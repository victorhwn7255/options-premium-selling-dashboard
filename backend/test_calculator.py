"""
Unit tests for the vol scanner backend.

Run: cd backend && python test_calculator.py
"""

import sys
import os
import math
import random
import tempfile
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(__file__))

from marketdata_client import DailyBar, OptionContract
from calculator import (
    compute_realized_vol, compute_atm_iv, compute_iv_rank,
    VolSurface, RealizedVol, ImpliedVolMetrics,
    TermStructure, VolSkew, TermStructurePoint, SkewPoint,
)
from scorer import score_opportunity, ScoringParams


# ── Test compute_realized_vol ────────────────────────────
def test_compute_realized_vol():
    price = 100.0
    bars = []
    for i in range(60):
        daily_return = 0.0095 if i % 2 == 0 else -0.0095
        price *= (1 + daily_return)
        bars.append(DailyBar(
            date=f"2025-01-{i+1:02d}",
            open=price * 0.999,
            high=price * 1.005,
            low=price * 0.995,
            close=price,
            volume=1000000,
        ))

    rv = compute_realized_vol(bars)
    assert rv.rv10 > 0, f"RV10 must be positive, got {rv.rv10}"
    assert rv.rv20 > 0, f"RV20 must be positive, got {rv.rv20}"
    assert rv.rv30 > 0, f"RV30 must be positive, got {rv.rv30}"
    assert rv.rv60 > 0, f"RV60 must be positive, got {rv.rv60}"
    assert 0.5 < rv.rv_acceleration < 2.0, f"RV accel {rv.rv_acceleration} out of range"
    print(f"  RV10={rv.rv10:.2f}, RV20={rv.rv20:.2f}, RV30={rv.rv30:.2f}, RV60={rv.rv60:.2f}")
    print(f"  RV Acceleration={rv.rv_acceleration:.3f}")
    print("  PASS: compute_realized_vol")


# ── Test compute_atm_iv ──────────────────────────────────
def test_compute_atm_iv():
    today = date.today()
    exp_30d = (today + timedelta(days=30)).strftime("%Y-%m-%d")
    exp_60d = (today + timedelta(days=60)).strftime("%Y-%m-%d")

    contracts = []
    spot = 500.0
    for strike in range(480, 521, 5):
        for exp in [exp_30d, exp_60d]:
            for ct in ["call", "put"]:
                iv = 0.20 + (abs(strike - spot) / spot) * 0.5
                contracts.append(OptionContract(
                    ticker="SPY",
                    strike=float(strike),
                    expiration=exp,
                    contract_type=ct,
                    implied_volatility=iv,
                    delta=0.5 if strike == spot else 0.3,
                ))

    atm_iv = compute_atm_iv(contracts, spot_price=spot, target_dte=30)
    assert atm_iv is not None, "ATM IV should not be None"
    assert 15 < atm_iv < 30, f"ATM IV {atm_iv} out of expected range"
    print(f"  ATM IV (30 DTE): {atm_iv}")
    print("  PASS: compute_atm_iv")


# ── Test compute_iv_rank ─────────────────────────────────
def test_compute_iv_rank():
    random.seed(42)
    historical = [random.uniform(15, 35) for _ in range(252)]

    current = sorted(historical)[int(252 * 0.75)]
    rank, percentile = compute_iv_rank(current, historical)
    assert 50 < rank < 100, f"Rank {rank} unexpected for 75th percentile value"
    assert 60 < percentile < 90, f"Percentile {percentile} unexpected"
    print(f"  IV Rank={rank:.1f}, Percentile={percentile:.1f}")

    # Edge case: empty history
    rank, pct = compute_iv_rank(20.0, [])
    assert rank == 50.0 and pct == 50.0, "Empty history should return 50/50"

    # Edge case: all same values
    rank, pct = compute_iv_rank(20.0, [20.0] * 100)
    assert rank == 50.0, f"Flat history should return 50 rank, got {rank}"
    print("  PASS: compute_iv_rank")


# ── Test score_opportunity ───────────────────────────────
def test_score_opportunity():
    # Perfect premium-selling scenario
    surface = VolSurface(
        ticker="TEST",
        price=100.0,
        rv=RealizedVol(rv10=12.0, rv20=13.0, rv30=14.0, rv60=15.0, rv_acceleration=0.857),
        iv=ImpliedVolMetrics(iv_current=22.0, iv_rank=85.0, iv_percentile=80.0),
        term_structure=TermStructure(
            points=[
                TermStructurePoint(7, "1W", 24.0),
                TermStructurePoint(30, "1M", 22.0),
                TermStructurePoint(90, "3M", 20.0),
            ],
            slope=0.80, is_contango=True, front_iv=24.0, back_iv=20.0,
        ),
        skew=VolSkew(
            points=[SkewPoint(25, 26.0, "put"), SkewPoint(50, 22.0, "call")],
            skew_25d=5.0, put_skew_slope=-0.2, call_skew_slope=0.1,
        ),
        vrp=8.0,
        vrp_ratio=1.57,
    )

    scored = score_opportunity(surface, name="Test Corp", sector="Tech", params=ScoringParams())
    print(f"  Normal: Score={scored.signal_score}, Regime={scored.regime}, Rec={scored.recommendation}")
    assert scored.signal_score >= 60, f"Perfect scenario should score high, got {scored.signal_score}"
    assert scored.regime == "NORMAL", f"Expected NORMAL regime, got {scored.regime}"
    assert scored.recommendation in ("SELL PREMIUM", "CONDITIONAL"), f"Unexpected rec: {scored.recommendation}"

    # Danger scenario (deep backwardation + high RV)
    danger_surface = VolSurface(
        ticker="DANGER",
        price=100.0,
        rv=RealizedVol(rv10=30.0, rv20=25.0, rv30=20.0, rv60=18.0, rv_acceleration=1.5),
        iv=ImpliedVolMetrics(iv_current=35.0, iv_rank=95.0, iv_percentile=95.0),
        term_structure=TermStructure(
            points=[], slope=1.15, is_contango=False, front_iv=35.0, back_iv=30.0,
        ),
        skew=VolSkew(
            points=[], skew_25d=12.0, put_skew_slope=-0.5, call_skew_slope=0.2,
        ),
        vrp=15.0,
        vrp_ratio=1.75,
    )

    danger_scored = score_opportunity(danger_surface, name="Danger Corp", sector="Index", params=ScoringParams())
    print(f"  Danger: Score={danger_scored.signal_score}, Regime={danger_scored.regime}, Rec={danger_scored.recommendation}")
    assert danger_scored.regime == "DANGER", f"Expected DANGER, got {danger_scored.regime}"
    assert danger_scored.recommendation == "AVOID", f"Expected AVOID, got {danger_scored.recommendation}"
    print("  PASS: score_opportunity")


# ── Test database round-trip ─────────────────────────────
def test_database():
    # Use a temp database to avoid corrupting real data
    tmp_db = tempfile.mktemp(suffix='.db')
    import database
    database.DB_PATH = type(database.DB_PATH)(tmp_db)
    database.init_db()

    from database import store_daily_iv, get_historical_ivs, get_historical_series

    for i in range(30):
        d = date.today() - timedelta(days=30 - i)
        store_daily_iv("TEST", atm_iv=20.0 + i * 0.1, rv30=15.0, vrp=5.0 + i * 0.1, term_slope=0.95, as_of=d)

    ivs = get_historical_ivs("TEST", lookback_days=30)
    assert len(ivs) == 30, f"Expected 30 IVs, got {len(ivs)}"

    series = get_historical_series("TEST", lookback_days=30)
    assert len(series) == 30, f"Expected 30 series points, got {len(series)}"
    assert "term_slope" in series[0], "Series should include term_slope"
    print(f"  Retrieved {len(ivs)} historical IVs, {len(series)} series points")

    # Clean up
    os.unlink(tmp_db)
    print("  PASS: database round-trip")


# ── Run all tests ────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 60)
    print("Backend Unit Tests")
    print("=" * 60)

    tests = [
        ("compute_realized_vol", test_compute_realized_vol),
        ("compute_atm_iv", test_compute_atm_iv),
        ("compute_iv_rank", test_compute_iv_rank),
        ("score_opportunity", test_score_opportunity),
        ("database round-trip", test_database),
    ]

    passed = 0
    failed = 0
    for name, fn in tests:
        print(f"\nTest: {name}")
        try:
            fn()
            passed += 1
        except Exception as e:
            print(f"  FAIL: {e}")
            failed += 1

    print(f"\n{'=' * 60}")
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)

    if failed > 0:
        sys.exit(1)
