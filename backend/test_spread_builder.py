"""Unit tests for spread_builder.py — Credit Put Spreads candidate construction.

Runner: plain `python backend/test_spread_builder.py` (no pytest dependency,
matching the rest of the test suite).
"""

from __future__ import annotations

import sys
import os
import traceback
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config as cfg
import spread_builder as sb
from marketdata_client import OptionContract


# ── Helpers ───────────────────────────────────────────────────────────


@dataclass
class FakeTickerResult:
    """Stand-in for backend.models.TickerResult used in builder tests.

    Avoids Pydantic validation friction — `passes_base_hard_gates` reads
    fields via `getattr` so a dataclass is fine.
    """
    ticker: str = "SPY"
    iv_current: Optional[float] = 18.0
    iv_percentile: float = 65.0
    rv30: float = 15.0
    rv_acceleration: float = 0.9
    term_slope: float = 0.80
    skew_25d: float = 6.0
    vrp: float = 3.0
    vrp_ratio: float = 1.20
    signal_score: int = 70
    recommendation: str = "SELL PREMIUM"
    regime: str = "NORMAL"
    earnings_dte: Optional[int] = None
    is_etf: bool = True


def _exp_iso(days_out: int) -> str:
    return (date.today() + timedelta(days=days_out)).isoformat()


def _put(strike: float, exp: str, delta: float, *, bid=1.0, ask=1.05, oi=500, vol=100) -> OptionContract:
    """Build an OptionContract for a put with sane execution defaults."""
    return OptionContract(
        ticker="SPY",
        strike=strike,
        expiration=exp,
        contract_type="put",
        implied_volatility=18.0,
        delta=delta,
        gamma=0.01,
        theta=-0.05,
        vega=0.10,
        open_interest=oi,
        volume=vol,
        bid=bid,
        ask=ask,
    )


def make_clean_chain(exp_dte: int = 35) -> list[OptionContract]:
    """Synthetic SPY-like put chain, $1 strikes, designed so a 20-delta short
    paired with a 4-wide long (ATR=5 → target_width=3.75) produces
    credit/width ≈ 0.26 — comfortably above the 0.25 SELL_CPS threshold but
    below the 0.35 high-c/w warning. Ask = bid + 0.05 on every leg.
    """
    exp = _exp_iso(exp_dte)
    # (strike, delta, bid) anchors hand-tuned for the math, not BSM realism.
    anchors = [
        (470, -0.02, 0.10),
        (475, -0.05, 0.20),
        (480, -0.10, 0.50),
        (482, -0.12, 0.65),
        (484, -0.15, 0.95),  # long pick for ATR=5 (width 4)
        (485, -0.16, 1.10),
        (486, -0.17, 1.35),
        (487, -0.18, 1.55),
        (488, -0.20, 2.00),  # short pick (target delta 0.20)
        (490, -0.25, 2.50),
        (492, -0.30, 3.00),
        (495, -0.40, 4.00),
        (500, -0.50, 5.50),
        (505, -0.65, 8.00),
        (510, -0.80, 11.00),
    ]
    return [_put(s, exp, d, bid=b, ask=b + 0.05) for s, d, b in anchors]


# ── Test runner ───────────────────────────────────────────────────────


passed = 0
failed: list[tuple[str, str]] = []


def run(name: str, fn):
    global passed
    print(f"\nTest: {name}")
    try:
        fn()
        passed += 1
        print(f"  PASS: {name}")
    except AssertionError as e:
        failed.append((name, str(e)))
        print(f"  FAIL: {name}\n    {e}")
    except Exception as e:
        failed.append((name, f"{type(e).__name__}: {e}\n{traceback.format_exc()}"))
        print(f"  ERROR: {name}\n    {type(e).__name__}: {e}")


# ── Tests ─────────────────────────────────────────────────────────────


def test_universe_filter_excludes_non_cps_tickers():
    """A ticker outside CPS_UNIVERSE never produces a SELL/WATCH candidate."""
    tr = FakeTickerResult(ticker="JNJ", is_etf=False)
    out = sb.build_candidate_outcome_for_ticker(
        ticker="JNJ", ticker_result=tr, chain=make_clean_chain(),
        spot=150.0, atr14=2.5, consecutive_sell_days=5,
    )
    assert out.action == "NO_EDGE", f"expected NO_EDGE, got {out.action}"
    assert out.candidate is None
    assert any("not in CPS_UNIVERSE" in r for r in out.rejection_reasons)


def test_no_expiration_in_window_returns_no_data():
    """If chain has no DTE in [30,45], we get NO_DATA."""
    chain = [_put(500, _exp_iso(7), -0.20)]  # 7 DTE only
    tr = FakeTickerResult()
    out = sb.build_candidate_outcome_for_ticker(
        ticker="SPY", ticker_result=tr, chain=chain,
        spot=500.0, atr14=5.0, consecutive_sell_days=2,
    )
    assert out.action == "NO_DATA", f"expected NO_DATA, got {out.action}"


def test_short_delta_selection_targets_020():
    """Short put picked closest to 0.20 |delta| inside [0.15, 0.25]."""
    exp = _exp_iso(35)
    puts = [
        _put(480, exp, -0.10),  # outside band low
        _put(485, exp, -0.15),  # band edge low
        _put(488, exp, -0.20),  # target — closest to 0.20
        _put(490, exp, -0.25),  # band edge high
        _put(500, exp, -0.40),  # outside high
    ]
    pick = sb.select_short_put(puts)
    assert pick is not None and pick.strike == 488, f"expected 488, got {pick.strike if pick else None}"


def test_short_delta_no_match_returns_none():
    """All deltas outside band → no short."""
    exp = _exp_iso(35)
    puts = [_put(480, exp, -0.05), _put(500, exp, -0.50)]
    assert sb.select_short_put(puts) is None


def test_long_put_is_below_short_strike():
    """select_long_put never picks a strike at or above short."""
    chain = make_clean_chain()
    short = next(c for c in chain if c.strike == 488)
    long_pick = sb.select_long_put(chain, short, spot=500.0, atr14=5.0)
    assert long_pick is not None
    assert long_pick.strike < short.strike, f"long {long_pick.strike} >= short {short.strike}"


def test_atr_aware_width_rounds_to_strike_grid():
    """Target width = max(strike_step, 0.75×ATR). With ATR=10, target 7.5,
    band [7.5, 15]. Below short 488: 480 (w=8, in-band & closest)."""
    chain = make_clean_chain()
    short = next(c for c in chain if c.strike == 488)
    long_pick = sb.select_long_put(chain, short, spot=500.0, atr14=10.0)
    assert long_pick is not None
    assert long_pick.strike == 480, f"expected 480 (width 8 closest to 7.5), got {long_pick.strike}"


def test_economics_basic():
    """Net credit, width, max loss, credit/width, breakeven."""
    short = sb._make_leg(_put(500, _exp_iso(35), -0.20, bid=2.00, ask=2.10), 35)
    long_ = sb._make_leg(_put(495, _exp_iso(35), -0.10, bid=0.75, ask=0.85), 35)
    econ = sb.compute_spread_economics(short, long_)
    # short_mid = 2.05, long_mid = 0.80, net_credit = 1.25
    assert abs(econ["net_credit"] - 1.25) < 1e-6, econ
    assert econ["width"] == 5.0
    assert abs(econ["max_loss"] - 3.75) < 1e-6
    assert abs(econ["credit_to_width"] - 0.25) < 1e-6
    assert abs(econ["breakeven"] - 498.75) < 1e-6


def test_credit_to_width_below_watch_rejects():
    """credit/width < 0.20 → NO_EDGE."""
    exp = _exp_iso(35)
    # Strikes at 1-step grid; ATR=5 → target_width 3.75. Long pick goes to
    # strike 484 (width 4). Net credit by design = 0.525 - 0.475 = 0.05.
    chain = [
        _put(484, exp, -0.10, bid=0.45, ask=0.50),
        _put(485, exp, -0.12, bid=0.42, ask=0.47),
        _put(486, exp, -0.14, bid=0.40, ask=0.45),
        _put(488, exp, -0.20, bid=0.50, ask=0.55),  # short — anaemic premium
        _put(490, exp, -0.25, bid=0.80, ask=0.85),
    ]
    tr = FakeTickerResult()
    out = sb.build_candidate_outcome_for_ticker(
        ticker="SPY", ticker_result=tr, chain=chain,
        spot=510.0, atr14=5.0, consecutive_sell_days=2,
    )
    assert out.action == "NO_EDGE", f"expected NO_EDGE, got {out.action}"


def test_bid_ask_ratio_rejects_wide_quote():
    """Either leg with bid_ask_ratio > 20% → NO_DATA (rejected)."""
    chain = make_clean_chain()
    # Inject a wide quote on the short-pick strike (488): bid 1.00 / ask 1.50
    # → ratio = 0.50 / 1.25 = 0.40, well above the 0.20 cap.
    for c in chain:
        if c.strike == 488:
            c.bid = 1.0
            c.ask = 1.5
    tr = FakeTickerResult()
    out = sb.build_candidate_outcome_for_ticker(
        ticker="SPY", ticker_result=tr, chain=chain,
        spot=500.0, atr14=5.0, consecutive_sell_days=2,
    )
    assert out.action == "NO_DATA"
    assert any("bid_ask_ratio" in r for r in out.rejection_reasons)


def test_oi_too_low_rejects():
    """OI < 100 → reject."""
    chain = make_clean_chain()
    for c in chain:
        c.open_interest = 50  # Too low
    tr = FakeTickerResult()
    out = sb.build_candidate_outcome_for_ticker(
        ticker="SPY", ticker_result=tr, chain=chain,
        spot=500.0, atr14=5.0, consecutive_sell_days=2,
    )
    assert out.action == "NO_DATA"
    assert any("OI" in r for r in out.rejection_reasons)


def test_volume_too_low_rejects():
    """Volume < 25 → reject."""
    chain = make_clean_chain()
    for c in chain:
        c.volume = 10
    tr = FakeTickerResult()
    out = sb.build_candidate_outcome_for_ticker(
        ticker="SPY", ticker_result=tr, chain=chain,
        spot=500.0, atr14=5.0, consecutive_sell_days=2,
    )
    assert out.action == "NO_DATA"


def test_danger_regime_rejects():
    """ticker_result.regime == 'DANGER' → AVOID."""
    tr = FakeTickerResult(regime="DANGER", term_slope=1.20)
    out = sb.build_candidate_outcome_for_ticker(
        ticker="SPY", ticker_result=tr, chain=make_clean_chain(),
        spot=500.0, atr14=5.0, consecutive_sell_days=2,
    )
    assert out.action == "AVOID", f"expected AVOID, got {out.action}"


def test_term_slope_over_danger_threshold_rejects():
    """term_slope > 1.15 → AVOID."""
    tr = FakeTickerResult(regime="NORMAL", term_slope=1.18)
    out = sb.build_candidate_outcome_for_ticker(
        ticker="SPY", ticker_result=tr, chain=make_clean_chain(),
        spot=500.0, atr14=5.0, consecutive_sell_days=2,
    )
    assert out.action == "AVOID"


def test_vrp_ratio_below_threshold_rejects():
    """vrp_ratio < 1.15 → NO_EDGE."""
    tr = FakeTickerResult(vrp_ratio=1.10)
    out = sb.build_candidate_outcome_for_ticker(
        ticker="SPY", ticker_result=tr, chain=make_clean_chain(),
        spot=500.0, atr14=5.0, consecutive_sell_days=2,
    )
    assert out.action == "NO_EDGE"


def test_negative_vrp_rejects():
    """vrp < 0 → NO_EDGE."""
    tr = FakeTickerResult(vrp=-1.0)
    out = sb.build_candidate_outcome_for_ticker(
        ticker="SPY", ticker_result=tr, chain=make_clean_chain(),
        spot=500.0, atr14=5.0, consecutive_sell_days=2,
    )
    assert out.action == "NO_EDGE"


def test_rv_accel_shock_rejects():
    """rv_acceleration > 1.20 → WAIT."""
    tr = FakeTickerResult(rv_acceleration=1.25)
    out = sb.build_candidate_outcome_for_ticker(
        ticker="SPY", ticker_result=tr, chain=make_clean_chain(),
        spot=500.0, atr14=5.0, consecutive_sell_days=2,
    )
    assert out.action == "WAIT"


def test_extreme_skew_rejects():
    """skew_25d > 20 → AVOID."""
    tr = FakeTickerResult(skew_25d=22.0)
    out = sb.build_candidate_outcome_for_ticker(
        ticker="SPY", ticker_result=tr, chain=make_clean_chain(),
        spot=500.0, atr14=5.0, consecutive_sell_days=2,
    )
    assert out.action == "AVOID"


def test_sell_cps_requires_two_day_confirmation():
    """All filters pass but consecutive_sell_days=1 → WATCH_CPS, not SELL_CPS."""
    tr = FakeTickerResult()
    out = sb.build_candidate_outcome_for_ticker(
        ticker="SPY", ticker_result=tr, chain=make_clean_chain(),
        spot=500.0, atr14=5.0, consecutive_sell_days=1,
    )
    assert out.action == "WATCH_CPS", f"expected WATCH_CPS, got {out.action}"
    assert out.candidate is not None
    # Note should explain why we're not SELL_CPS
    assert any("consecutive_sell_days" in n for n in out.notes)


def test_sell_cps_promoted_with_two_day_confirmation():
    """All filters pass AND consecutive_sell_days >= 2 → SELL_CPS."""
    tr = FakeTickerResult()
    out = sb.build_candidate_outcome_for_ticker(
        ticker="SPY", ticker_result=tr, chain=make_clean_chain(),
        spot=500.0, atr14=5.0, consecutive_sell_days=2,
    )
    assert out.action == "SELL_CPS", f"expected SELL_CPS, got {out.action}"
    assert out.candidate is not None
    assert out.candidate.credit_to_width >= cfg.CPS_MIN_CREDIT_TO_WIDTH


def test_watch_cps_allowed_below_sell_credit_to_width():
    """20% ≤ c/w < 25%, base score adequate → WATCH_CPS only (not SELL_CPS).

    Built by hand: short at 488 (delta -0.20) mid 2.025, long at 484 (width 4)
    mid 1.205 → net 0.82, c/w ≈ 0.205 — sits in the WATCH band.
    """
    exp = _exp_iso(35)
    chain = [
        _put(484, exp, -0.15, bid=1.18, ask=1.23),  # long — eats more credit
        _put(485, exp, -0.16, bid=1.30, ask=1.35),
        _put(486, exp, -0.17, bid=1.55, ask=1.60),
        _put(487, exp, -0.18, bid=1.80, ask=1.85),
        _put(488, exp, -0.20, bid=2.00, ask=2.05),  # short
        _put(490, exp, -0.25, bid=2.50, ask=2.55),
    ]
    tr = FakeTickerResult()
    out = sb.build_candidate_outcome_for_ticker(
        ticker="SPY", ticker_result=tr, chain=chain,
        spot=510.0, atr14=5.0, consecutive_sell_days=2,
    )
    assert out.candidate is not None, out.rejection_reasons
    cw = out.candidate.credit_to_width
    assert cfg.CPS_WATCH_MIN_CREDIT_TO_WIDTH <= cw < cfg.CPS_MIN_CREDIT_TO_WIDTH, \
        f"c/w {cw} not in WATCH band [{cfg.CPS_WATCH_MIN_CREDIT_TO_WIDTH}, {cfg.CPS_MIN_CREDIT_TO_WIDTH})"
    assert out.action == "WATCH_CPS", f"expected WATCH_CPS, got {out.action}"


def test_high_credit_to_width_warning():
    """c/w > 35% attaches an explicit warning."""
    exp = _exp_iso(35)
    # Short 488 mid 2.55, long 484 mid 0.475 → net 2.075, c/w 0.519
    # Tight bid/ask everywhere so the execution filter passes.
    chain = [
        _put(484, exp, -0.10, bid=0.45, ask=0.50),  # long pick (bar 0.105)
        _put(485, exp, -0.12, bid=0.55, ask=0.60),
        _put(486, exp, -0.14, bid=0.65, ask=0.70),
        _put(487, exp, -0.17, bid=1.00, ask=1.05),
        _put(488, exp, -0.20, bid=2.50, ask=2.60),  # short
    ]
    tr = FakeTickerResult()
    out = sb.build_candidate_outcome_for_ticker(
        ticker="SPY", ticker_result=tr, chain=chain,
        spot=510.0, atr14=5.0, consecutive_sell_days=2,
    )
    assert out.candidate is not None, out.rejection_reasons
    assert out.candidate.credit_to_width > cfg.CPS_HIGH_CREDIT_TO_WIDTH_WARNING, \
        f"c/w {out.candidate.credit_to_width} not above warning threshold"
    assert any("credit/width" in w.lower() for w in out.warnings), out.warnings


def test_regime_overlay_danger_downgrades_sell_to_watch():
    """All filters pass, but regime overlay DANGER blocks SELL_CPS → WATCH_CPS.

    Construction: import the production overlay builder to keep status logic
    aligned with what spread_builder actually consumes.
    """
    from regime_overlay import build_overlay_from_values
    overlay = build_overlay_from_values(vix=22.0, vix3m=20.0, vvix=95.0)  # backwardation → DANGER
    assert overlay.status == "DANGER"
    tr = FakeTickerResult()
    out = sb.build_candidate_outcome_for_ticker(
        ticker="SPY", ticker_result=tr, chain=make_clean_chain(),
        spot=500.0, atr14=5.0, regime_overlay=overlay,
        consecutive_sell_days=2,
    )
    assert out.action == "WATCH_CPS", f"expected WATCH_CPS, got {out.action}"


def test_regime_overlay_unknown_does_not_block_sell():
    """UNKNOWN overlay must NOT block candidates — surfaces warning only."""
    from regime_overlay import build_overlay_from_values
    overlay = build_overlay_from_values(vix=None, vix3m=None, vvix=None)
    assert overlay.status == "UNKNOWN"
    tr = FakeTickerResult()
    out = sb.build_candidate_outcome_for_ticker(
        ticker="SPY", ticker_result=tr, chain=make_clean_chain(),
        spot=500.0, atr14=5.0, regime_overlay=overlay,
        consecutive_sell_days=2,
    )
    assert out.action == "SELL_CPS", f"expected SELL_CPS, got {out.action}"
    assert any("UNKNOWN" in w for w in out.warnings)


def test_vrp_zscore_below_floor_downgrades_to_watch():
    """60d VRP z-score below 0.5 with otherwise clean candidate → WATCH_CPS."""
    # 60 history points all = 5.0; current also 5.0 → z=0 < 0.5 floor
    history = [5.0] * 60
    tr = FakeTickerResult(vrp=5.0)
    out = sb.build_candidate_outcome_for_ticker(
        ticker="SPY", ticker_result=tr, chain=make_clean_chain(),
        spot=500.0, atr14=5.0, consecutive_sell_days=2,
        vrp_history_60d=history,
    )
    # z = (5 - 5) / std (std=0!) — std=0 should yield None → no floor enforced
    # Make history vary so std>0, then ensure current is at the mean
    history = [4.5, 5.5] * 30  # alternating, mean 5.0
    out = sb.build_candidate_outcome_for_ticker(
        ticker="SPY", ticker_result=tr, chain=make_clean_chain(),
        spot=500.0, atr14=5.0, consecutive_sell_days=2,
        vrp_history_60d=history,
    )
    assert out.candidate is not None
    assert out.candidate.vrp_zscore_60d is not None
    assert abs(out.candidate.vrp_zscore_60d) < 0.5
    assert out.action == "WATCH_CPS", f"expected WATCH_CPS, got {out.action}"


def test_vrp_zscore_unknown_does_not_block():
    """< 20 points of history → z-score None → warning, but does not block."""
    tr = FakeTickerResult()
    out = sb.build_candidate_outcome_for_ticker(
        ticker="SPY", ticker_result=tr, chain=make_clean_chain(),
        spot=500.0, atr14=5.0, consecutive_sell_days=2,
        vrp_history_60d=[3.0, 4.0, 5.0],  # only 3 points
    )
    assert out.action == "SELL_CPS"  # not blocked
    assert any("z-score UNKNOWN" in w for w in out.warnings)


def test_top_level_ranks_by_base_score():
    """build_credit_put_spread_candidates sorts SELL_CPS first, then by base score."""
    scan = {
        "SPY": FakeTickerResult(ticker="SPY", signal_score=70),
        "QQQ": FakeTickerResult(ticker="QQQ", signal_score=78),
        "IWM": FakeTickerResult(ticker="IWM", signal_score=66),
    }
    chains = {t: make_clean_chain() for t in ("SPY", "QQQ", "IWM")}
    spots = {"SPY": 500.0, "QQQ": 500.0, "IWM": 500.0}
    atrs = {"SPY": 5.0, "QQQ": 5.0, "IWM": 5.0}
    confs = {"SPY": 2, "QQQ": 2, "IWM": 2}
    candidates = sb.build_credit_put_spread_candidates(
        scan_results=scan,
        option_chains=chains,
        spot_prices=spots,
        atr_values=atrs,
        consecutive_sell_days=confs,
    )
    tickers_in_order = [c.ticker for c in candidates]
    # All three should be SELL_CPS at this point, ranked by base_score desc
    assert tickers_in_order == ["QQQ", "SPY", "IWM"], tickers_in_order


def test_non_cps_ticker_never_appears_in_top_level_output():
    """Top-level builder must not emit anything outside CPS_UNIVERSE."""
    scan = {
        "JNJ": FakeTickerResult(ticker="JNJ", signal_score=80, is_etf=False),
        "SPY": FakeTickerResult(ticker="SPY", signal_score=70),
    }
    chains = {"JNJ": make_clean_chain(), "SPY": make_clean_chain()}
    spots = {"JNJ": 150.0, "SPY": 500.0}
    candidates = sb.build_credit_put_spread_candidates(
        scan_results=scan,
        option_chains=chains,
        spot_prices=spots,
        atr_values={"JNJ": 2.5, "SPY": 5.0},
        consecutive_sell_days={"JNJ": 5, "SPY": 2},
    )
    assert all(c.ticker in cfg.CPS_UNIVERSE for c in candidates), \
        [c.ticker for c in candidates]


def test_bid_ask_ratio_field_name_consistency():
    """Built legs carry bid_ask_ratio (never spread_ratio)."""
    tr = FakeTickerResult()
    out = sb.build_candidate_outcome_for_ticker(
        ticker="SPY", ticker_result=tr, chain=make_clean_chain(),
        spot=500.0, atr14=5.0, consecutive_sell_days=2,
    )
    assert out.candidate is not None
    assert out.candidate.short_put.bid_ask_ratio is not None
    assert out.candidate.long_put.bid_ask_ratio is not None


# ── Runner ────────────────────────────────────────────────────────────


if __name__ == "__main__":
    print("Phase 2 — spread_builder.py unit tests")
    print("=" * 64)

    tests = [
        ("Universe filter excludes non-CPS tickers", test_universe_filter_excludes_non_cps_tickers),
        ("No expiration in window → NO_DATA", test_no_expiration_in_window_returns_no_data),
        ("Short delta selection targets 0.20", test_short_delta_selection_targets_020),
        ("Short delta no match → None", test_short_delta_no_match_returns_none),
        ("Long put below short strike", test_long_put_is_below_short_strike),
        ("ATR-aware width rounds to strike grid", test_atr_aware_width_rounds_to_strike_grid),
        ("Spread economics math", test_economics_basic),
        ("credit/width < 20% rejects", test_credit_to_width_below_watch_rejects),
        ("bid_ask_ratio > 20% rejects", test_bid_ask_ratio_rejects_wide_quote),
        ("OI < 100 rejects", test_oi_too_low_rejects),
        ("Volume < 25 rejects", test_volume_too_low_rejects),
        ("DANGER regime rejects", test_danger_regime_rejects),
        ("term_slope > 1.15 rejects", test_term_slope_over_danger_threshold_rejects),
        ("vrp_ratio < 1.15 rejects", test_vrp_ratio_below_threshold_rejects),
        ("Negative VRP rejects", test_negative_vrp_rejects),
        ("RV Accel shock rejects", test_rv_accel_shock_rejects),
        ("Extreme skew rejects", test_extreme_skew_rejects),
        ("SELL_CPS requires 2-day confirmation", test_sell_cps_requires_two_day_confirmation),
        ("SELL_CPS promoted with confirmation", test_sell_cps_promoted_with_two_day_confirmation),
        ("WATCH_CPS band (20% ≤ c/w < 25%)", test_watch_cps_allowed_below_sell_credit_to_width),
        ("High c/w (>35%) warning", test_high_credit_to_width_warning),
        ("Regime overlay DANGER downgrades", test_regime_overlay_danger_downgrades_sell_to_watch),
        ("Regime overlay UNKNOWN does not block", test_regime_overlay_unknown_does_not_block_sell),
        ("VRP z-score below floor downgrades", test_vrp_zscore_below_floor_downgrades_to_watch),
        ("VRP z-score UNKNOWN does not block", test_vrp_zscore_unknown_does_not_block),
        ("Top-level ranks by base score", test_top_level_ranks_by_base_score),
        ("Non-CPS ticker never appears", test_non_cps_ticker_never_appears_in_top_level_output),
        ("bid_ask_ratio field name", test_bid_ask_ratio_field_name_consistency),
    ]

    for name, fn in tests:
        run(name, fn)

    print("\n" + "=" * 64)
    print(f"Results: {passed} passed, {len(failed)} failed")
    print("=" * 64)
    if failed:
        sys.exit(1)
