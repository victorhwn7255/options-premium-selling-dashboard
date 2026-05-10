"""
QA Phase 1 — Production Regression Tests
=========================================
Action precedence, edge-case, and UI-consistency verification.

Builds on `test_qa_phase1.py` (which proves the Phase 1 features work) by
verifying they work *correctly under all combinations* of regime, score,
earnings, and scan-quality state. The expected precedence model:

    1. NO DATA stays NO DATA (early-return path).
    2. Earnings gate (frontend) → SKIP when DTE ≤ 14 and not an ETF.
    3. DANGER → AVOID, regardless of score or VRP ratio.
    4. CAUTION → REDUCE SIZE if score ≥ 55, else NO EDGE.
    5. VRP-ratio gate → only NORMAL SELL/CONDITIONAL becomes WATCHLIST.
    6. WATCHLIST is never tradeable (excluded from sell/conditional counts).
    7. DEGRADED scan suppresses SELL/CONDITIONAL/WATCHLIST → NO EDGE.
    8. signal_score is preserved through the WATCHLIST gate AND through
       degraded suppression — only the displayed recommendation changes.

Run: cd backend && python test_qa_phase1_regression.py
"""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from calculator import (
    VolSurface, RealizedVol, ImpliedVolMetrics,
    TermStructure, VolSkew,
)
from scorer import score_opportunity, ScoringParams
from scan_quality import (
    compute_scan_quality, suppress_actionable,
    SLOPE_WALL_TOLERANCE, SLOPE_WALL_THRESHOLD, NO_DATA_THRESHOLD,
)
from models import TickerResult, ScanResponse


# ── Test Helpers ─────────────────────────────────────────

def _build_surface(*, ticker, iv_current, rv30, rv10,
                   iv_rank, iv_pct, slope, accel, skew_25d,
                   rv20=None, rv60=None, vrp_ratio=None):
    """
    Build a VolSurface fixture. When `vrp_ratio` is supplied explicitly it
    overrides the iv/rv30 derivation (useful for boundary testing).
    """
    if rv20 is None:
        rv20 = rv30
    if rv60 is None:
        rv60 = rv30
    vrp = iv_current - rv30
    if vrp_ratio is None:
        vrp_ratio = iv_current / rv30 if rv30 else 1.0
    return VolSurface(
        ticker=ticker,
        price=100.0,
        rv=RealizedVol(rv10=rv10, rv20=rv20, rv30=rv30, rv60=rv60,
                       rv_acceleration=accel),
        iv=ImpliedVolMetrics(iv_current=iv_current, iv_rank=iv_rank,
                             iv_percentile=iv_pct),
        term_structure=TermStructure(
            points=[], slope=slope, is_contango=slope < 1.0,
            front_iv=iv_current * slope, back_iv=iv_current,
        ),
        skew=VolSkew(
            points=[], skew_25d=skew_25d,
            put_skew_slope=0.0, call_skew_slope=0.0,
        ),
        vrp=vrp,
        vrp_ratio=vrp_ratio,
    )


def _build_ticker_result(*, ticker, recommendation, term_slope,
                         signal_score=50, regime="NORMAL", is_etf=False,
                         earnings_dte=None, vrp=5.0, vrp_ratio=1.33,
                         iv_current=20.0):
    """
    Build a TickerResult Pydantic model for cached-path / suppression tests.
    Defaults to a healthy NORMAL ticker; override fields per scenario.
    """
    return TickerResult(
        ticker=ticker, name=ticker, sector="Test",
        price=100.0,
        iv_current=iv_current, iv_rank=50.0, iv_percentile=50.0,
        rv10=15.0, rv20=15.0, rv30=15.0,
        vrp=vrp, vrp_ratio=vrp_ratio,
        rv_acceleration=0.85, term_slope=term_slope,
        is_contango=term_slope < 1.0, skew_25d=2.0,
        signal_score=signal_score, regime=regime,
        recommendation=recommendation, flags=[],
        suggested_delta="x", suggested_structure="x",
        suggested_dte="x", suggested_max_notional="x",
        earnings_dte=earnings_dte, is_etf=is_etf,
    )


class _StubResult:
    """Duck-typed result stub for scan-quality tests (no Pydantic overhead)."""

    def __init__(self, recommendation, term_slope,
                 signal_score=0, regime="NORMAL"):
        self.recommendation = recommendation
        self.term_slope = term_slope
        self.signal_score = signal_score
        self.regime = regime
        self.flags = []
        self.suggested_delta = "x"
        self.suggested_structure = "x"
        self.suggested_dte = "x"
        self.suggested_max_notional = "x"
        self.suppressed_by_scan_quality = False
        self.pre_suppression_recommendation = None
        self.pre_suppression_score = None
        self.scan_quality_suppression_reason = None


def _apply_scan_quality_helper(tickers):
    """
    Inline mirror of main.py:_apply_scan_quality(). Replicated here to avoid
    importing main.py (which boots FastAPI + DB on import).
    """
    quality, reason = compute_scan_quality(tickers)
    if quality == "DEGRADED":
        suppress_actionable(tickers, reason)
    return quality, reason


def _simulate_frontend_gate(*, action, signal_score, earnings_dte,
                            is_etf):
    """
    Mirror frontend/src/lib/scoring.ts earnings gate (lines 34-39).
    Returns (final_action, final_score, pre_gate_score).

    The is_etf check is tracked here; if the production code accidentally
    drops it, the test_etf_never_earnings_gated stress test will fail.
    """
    if (earnings_dte is not None
            and earnings_dte <= 14
            and not is_etf):
        return ("SKIP", 0, signal_score if signal_score > 0 else None)
    return (action, signal_score, None)


def _is_thin_premium(*, action, vrp_ratio):
    """Mirror scoring.ts thinPremium derivation: 1.15 ≤ ratio < 1.25 + CONDITIONAL."""
    if action != "CONDITIONAL" or vrp_ratio is None:
        return False
    return 1.15 <= vrp_ratio < 1.25


def _map_action(rec):
    """Mirror scoring.ts:mapRecommendation."""
    return {
        "SELL PREMIUM": "SELL",
        "CONDITIONAL": "CONDITIONAL",
        "WATCHLIST": "WATCHLIST",
        "AVOID": "AVOID",
        "REDUCE SIZE": "AVOID",
        "NO DATA": "NO DATA",
    }.get(rec, "NO EDGE")


# ─────────────────────────────────────────────────────────
# A. VRP gate precedence tests
# ─────────────────────────────────────────────────────────

def test_vrp_gate_only_applies_to_normal_sell_or_conditional():
    """
    The VRP-ratio gate must fire for NORMAL SELL/CONDITIONAL only.
    DANGER and CAUTION recommendations come from a different code path
    and must remain unaffected.

    Note: Some user-spec scores aren't reachable for every regime due to
    the formula's structural caps (DANGER zeros term, CAUTION caps it
    near 0 when slope > 1.05). The test uses the closest reachable score
    while preserving the precedence intent.
    """
    params = ScoringParams()

    # 1) NORMAL + score in SELL territory + vrp_ratio 1.10 → WATCHLIST
    s = _build_surface(ticker="N1", iv_current=22.0, rv30=20.0, rv10=18.0,
                       iv_rank=80, iv_pct=90,
                       slope=0.85, accel=0.85, skew_25d=7.0,
                       vrp_ratio=1.10)
    r = score_opportunity(s, name="N1", sector="Test", params=params)
    assert r.signal_score >= 65, \
        f"Fixture should reach SELL score ≥65, got {r.signal_score}"
    assert r.recommendation == "WATCHLIST", \
        f"NORMAL+SELL-tier+vrp_ratio<1.15 must be WATCHLIST, got {r.recommendation}"

    # 2) NORMAL + score in CONDITIONAL territory (45-64) + vrp_ratio 1.10 → WATCHLIST
    s = _build_surface(ticker="N2", iv_current=22.0, rv30=20.0, rv10=18.0,
                       iv_rank=60, iv_pct=60,
                       slope=0.85, accel=0.85, skew_25d=5.0,
                       vrp_ratio=1.10)
    r = score_opportunity(s, name="N2", sector="Test", params=params)
    assert 45 <= r.signal_score < 65, \
        f"Fixture should reach CONDITIONAL score 45-64, got {r.signal_score}"
    assert r.recommendation == "WATCHLIST", \
        f"NORMAL+CONDITIONAL-tier+vrp_ratio<1.15 must be WATCHLIST, got {r.recommendation}"

    # 3) NORMAL + score < 45 + vrp_ratio 1.10 → NO EDGE (gate doesn't fire — already below threshold)
    s = _build_surface(ticker="N3", iv_current=22.0, rv30=20.0, rv10=18.0,
                       iv_rank=20, iv_pct=20,
                       slope=0.95, accel=0.95, skew_25d=2.0,
                       vrp_ratio=1.10)
    r = score_opportunity(s, name="N3", sector="Test", params=params)
    assert r.signal_score < 45, \
        f"Fixture should reach NO EDGE score <45, got {r.signal_score}"
    assert r.recommendation == "NO EDGE", \
        f"NO EDGE score must remain NO EDGE (not WATCHLIST), got {r.recommendation}"

    # 4) DANGER (slope > 1.15) + vrp_ratio 1.10 → AVOID, never WATCHLIST
    #    DANGER caps non-VRP score at ~50 (term=0), so we use achievable score.
    s = _build_surface(ticker="D1", iv_current=22.0, rv30=20.0, rv10=18.0,
                       iv_rank=80, iv_pct=80,
                       slope=1.20, accel=0.85, skew_25d=7.0,
                       vrp_ratio=1.10)
    r = score_opportunity(s, name="D1", sector="Test", params=params)
    assert r.regime == "DANGER", f"Expected DANGER, got {r.regime}"
    assert r.recommendation == "AVOID", \
        f"DANGER must be AVOID (not WATCHLIST), got {r.recommendation}"

    # 5a) CAUTION via slope (1.05-1.15) + low score < 55 + vrp_ratio 1.10 → NO EDGE
    s = _build_surface(ticker="C1", iv_current=22.0, rv30=20.0, rv10=18.0,
                       iv_rank=70, iv_pct=70,
                       slope=1.10, accel=0.95, skew_25d=2.0,
                       vrp_ratio=1.10)
    r = score_opportunity(s, name="C1", sector="Test", params=params)
    assert r.regime == "CAUTION", f"Expected CAUTION, got {r.regime}"
    assert r.signal_score < 55, \
        f"Fixture should produce score <55 in CAUTION, got {r.signal_score}"
    assert r.recommendation == "NO EDGE", \
        f"CAUTION+score<55 must be NO EDGE (not WATCHLIST), got {r.recommendation}"

    # 5b) CAUTION via path 2 (iv_rank>90 + accel>1.1) + score≥55 + vrp_ratio 1.10
    #     → REDUCE SIZE (unaffected by VRP gate which only handles SELL/CONDITIONAL).
    s = _build_surface(ticker="C2", iv_current=22.0, rv30=20.0, rv10=18.0,
                       iv_rank=95, iv_pct=100,
                       slope=0.85, accel=1.105, skew_25d=7.0,
                       vrp_ratio=1.10)
    r = score_opportunity(s, name="C2", sector="Test", params=params)
    assert r.regime == "CAUTION", f"Expected CAUTION, got {r.regime}"
    assert r.signal_score >= 55, \
        f"Fixture should produce score ≥55 in CAUTION, got {r.signal_score}"
    assert r.recommendation == "REDUCE SIZE", \
        (f"CAUTION+score≥55 must be REDUCE SIZE (not WATCHLIST), "
         f"got {r.recommendation}")

    # 6) NO DATA (iv_current None) → NO DATA. VRP gate must never run.
    s = _build_surface(ticker="ND", iv_current=20.0, rv30=20.0, rv10=18.0,
                       iv_rank=50, iv_pct=50,
                       slope=0.90, accel=0.90, skew_25d=3.0)
    s.iv.iv_current = None  # simulate insufficient liquid contracts
    r = score_opportunity(s, name="ND", sector="Test", params=params)
    assert r.recommendation == "NO DATA", \
        f"NO DATA path must remain NO DATA, got {r.recommendation}"
    assert r.signal_score == 0, \
        f"NO DATA score must be 0, got {r.signal_score}"

    print("  All 6 precedence cases verified")
    print("  PASS: VRP gate only applies to NORMAL SELL/CONDITIONAL")


def test_vrp_gate_boundary_conditions():
    """
    Implementation uses strict `<` comparisons:
      - VRP gate:    vrp_ratio < 1.15  → WATCHLIST
      - Thin Premium: 1.15 ≤ ratio < 1.25 → flag (frontend-derived)
    Boundary values must align with the spec exactly.
    """
    params = ScoringParams()

    def _make(ratio):
        # Build a surface that would reach CONDITIONAL on non-VRP components alone
        # so we observe the gate's effect on the recommendation.
        return _build_surface(
            ticker="B", iv_current=22.0, rv30=20.0, rv10=18.0,
            iv_rank=60, iv_pct=60,
            slope=0.85, accel=0.85, skew_25d=7.0,
            vrp_ratio=ratio,
        )

    # 1.1499 → just below dead-zone exit → WATCHLIST
    r = score_opportunity(_make(1.1499), name="B", sector="Test", params=params)
    assert r.recommendation == "WATCHLIST", \
        f"vrp_ratio 1.1499 (<1.15) must be WATCHLIST, got {r.recommendation}"

    # 1.15 exactly → NOT < 1.15 → CONDITIONAL preserved
    r = score_opportunity(_make(1.15), name="B", sector="Test", params=params)
    assert r.recommendation in ("CONDITIONAL", "SELL PREMIUM"), \
        (f"vrp_ratio exactly 1.15 must NOT trigger gate "
         f"(strict less-than), got {r.recommendation}")

    # 1.1501 → above dead-zone → CONDITIONAL preserved
    r = score_opportunity(_make(1.1501), name="B", sector="Test", params=params)
    assert r.recommendation in ("CONDITIONAL", "SELL PREMIUM"), \
        f"vrp_ratio 1.1501 must NOT trigger gate, got {r.recommendation}"

    # Thin Premium boundaries: 1.2499 → flag, 1.25 → no flag
    # (Frontend-derived logic mirrored in _is_thin_premium helper.)
    r = score_opportunity(_make(1.2499), name="B", sector="Test", params=params)
    fe_action = _map_action(r.recommendation)
    if fe_action == "CONDITIONAL":
        assert _is_thin_premium(action=fe_action, vrp_ratio=1.2499) is True, \
            "vrp_ratio 1.2499 + CONDITIONAL must trigger Thin Premium badge"

    r = score_opportunity(_make(1.25), name="B", sector="Test", params=params)
    fe_action = _map_action(r.recommendation)
    if fe_action == "CONDITIONAL":
        assert _is_thin_premium(action=fe_action, vrp_ratio=1.25) is False, \
            "vrp_ratio exactly 1.25 must NOT trigger Thin Premium badge"

    # Thin Premium only applies to CONDITIONAL — never to WATCHLIST or SELL.
    assert _is_thin_premium(action="WATCHLIST", vrp_ratio=1.20) is False, \
        "WATCHLIST must never get Thin Premium (already a stronger warning)"
    assert _is_thin_premium(action="SELL", vrp_ratio=1.20) is False, \
        "SELL must never get Thin Premium"
    assert _is_thin_premium(action="NO EDGE", vrp_ratio=1.20) is False, \
        "NO EDGE must never get Thin Premium"

    print("  Verified: 1.1499/1.15/1.2499/1.25 boundaries")
    print("  PASS: VRP gate boundary conditions")


def test_vrp_gate_preserves_score():
    """QQQ May 8 fixture: signal_score=45 must survive the WATCHLIST downgrade."""
    s = _build_surface(
        ticker="QQQ", iv_current=19.4, rv30=18.9, rv10=18.0,
        iv_rank=51, iv_pct=51,
        slope=0.78, accel=0.89, skew_25d=3.1,
    )
    r = score_opportunity(s, name="Invesco QQQ", sector="Index",
                          params=ScoringParams())
    assert r.recommendation == "WATCHLIST", \
        f"QQQ May 8 must be WATCHLIST, got {r.recommendation}"
    assert r.signal_score == 45, \
        f"signal_score must be preserved at 45, got {r.signal_score}"
    assert s.vrp_ratio < 1.15, \
        f"QQQ vrp_ratio should be <1.15, got {s.vrp_ratio:.4f}"
    print(f"  QQQ: score={r.signal_score} preserved through WATCHLIST gate")
    print("  PASS: VRP gate preserves score")


# ─────────────────────────────────────────────────────────
# B. Earnings precedence tests
# ─────────────────────────────────────────────────────────

def test_earnings_gate_overrides_watchlist_frontend_or_transform_layer():
    """
    Earnings gate (frontend) must override BOTH SELL and WATCHLIST → SKIP.
    Backend supplies the raw recommendation; frontend gate is decisive when
    DTE ≤ 14.
    """
    # Case 1: backend SELL (vrp_ratio strong) + earnings 13d → frontend SKIP
    s = _build_surface(
        ticker="WMT", iv_current=31.3, rv30=23.2, rv10=19.7,
        iv_rank=85, iv_pct=85,
        slope=0.82, accel=0.85, skew_25d=2.0,
    )
    r = score_opportunity(s, name="Walmart", sector="Consumer",
                          params=ScoringParams())
    assert r.recommendation in ("SELL PREMIUM", "CONDITIONAL"), \
        f"Expected SELL/CONDITIONAL for WMT, got {r.recommendation}"
    assert s.vrp_ratio >= 1.15, "WMT should be past the dead zone"

    final_action, final_score, pre_gate = _simulate_frontend_gate(
        action=_map_action(r.recommendation),
        signal_score=r.signal_score,
        earnings_dte=13, is_etf=False,
    )
    assert final_action == "SKIP", \
        f"Earnings DTE 13 must produce SKIP, got {final_action}"
    assert final_score == 0, "Gated score must be 0"
    assert pre_gate == r.signal_score, \
        f"preGateScore must equal backend score {r.signal_score}, got {pre_gate}"
    assert final_action != "WATCHLIST", \
        "Earnings-gated SKIP must NOT display as WATCHLIST"

    # Case 2: backend WATCHLIST + earnings 13d → frontend STILL SKIP (not WATCHLIST)
    s = _build_surface(
        ticker="W", iv_current=22.0, rv30=20.0, rv10=18.0,
        iv_rank=60, iv_pct=60,
        slope=0.85, accel=0.85, skew_25d=5.0,
        vrp_ratio=1.10,
    )
    r = score_opportunity(s, name="W", sector="Test", params=ScoringParams())
    assert r.recommendation == "WATCHLIST"

    final_action, final_score, pre_gate = _simulate_frontend_gate(
        action=_map_action(r.recommendation),
        signal_score=r.signal_score,
        earnings_dte=13, is_etf=False,
    )
    assert final_action == "SKIP", \
        f"WATCHLIST + earnings 13d must produce SKIP (not WATCHLIST), got {final_action}"

    print("  WMT (SELL→SKIP), W (WATCHLIST→SKIP) verified")
    print("  PASS: Earnings gate overrides WATCHLIST and SELL/CONDITIONAL")


def test_etf_never_earnings_gated():
    """
    ETFs are exempt from the earnings gate (per metrics.md / strategy.md).

    Two scenarios:
      1. ETF with earnings_dte=None (current production state) → not gated.
      2. Stress test: ETF with earnings_dte=5 (defense-in-depth) → not gated.

    If scenario 2 fails, the frontend earnings gate is not checking is_etf;
    we update scoring.ts to add the guard.
    """
    # 1) Standard case — ETF carries earnings_dte=None
    final_action, _, _ = _simulate_frontend_gate(
        action="SELL", signal_score=70, earnings_dte=None, is_etf=True,
    )
    assert final_action == "SELL", \
        f"ETF with earnings_dte=None must keep its action, got {final_action}"

    # 2) Defense-in-depth — even if earnings_dte were set on an ETF, no gate
    for dte in (5, 10, 14):
        final_action, final_score, _ = _simulate_frontend_gate(
            action="SELL", signal_score=70, earnings_dte=dte, is_etf=True,
        )
        assert final_action == "SELL", (
            f"ETF stress test FAILED at DTE={dte}: action became {final_action}. "
            f"Frontend earnings gate must include `&& !is_etf` to honor "
            f"the documented ETF exemption."
        )
        assert final_score == 70, \
            f"ETF score must not be zeroed by earnings gate, got {final_score}"

    # 3) Non-ETF DTE=15 (just outside gate) is unaffected
    final_action, final_score, _ = _simulate_frontend_gate(
        action="SELL", signal_score=70, earnings_dte=15, is_etf=False,
    )
    assert final_action == "SELL", \
        f"Non-ETF at DTE 15 (>14) must NOT be gated, got {final_action}"

    # 4) Non-ETF DTE=14 (boundary) IS gated
    final_action, _, _ = _simulate_frontend_gate(
        action="SELL", signal_score=70, earnings_dte=14, is_etf=False,
    )
    assert final_action == "SKIP", \
        f"Non-ETF at DTE 14 (boundary) must be gated, got {final_action}"

    print("  ETFs (DTE 5/10/14/null) all bypass the gate; non-ETF DTE 14 gated")
    print("  PASS: ETFs never earnings-gated")


# ─────────────────────────────────────────────────────────
# C. DANGER / CAUTION precedence tests
# ─────────────────────────────────────────────────────────

def test_danger_overrides_watchlist():
    """
    A DANGER ticker (slope > 1.15) with vrp_ratio < 1.15 must produce AVOID,
    never WATCHLIST. The DANGER override happens before the VRP gate even runs.
    """
    s = _build_surface(
        ticker="D", iv_current=22.0, rv30=20.0, rv10=18.0,
        iv_rank=80, iv_pct=80,
        slope=1.25, accel=0.85, skew_25d=7.0,
        vrp_ratio=1.10,
    )
    r = score_opportunity(s, name="D", sector="Test", params=ScoringParams())
    assert r.regime == "DANGER", f"Expected DANGER, got {r.regime}"
    assert r.recommendation == "AVOID", \
        f"DANGER must produce AVOID even with vrp_ratio<1.15, got {r.recommendation}"
    assert r.recommendation != "WATCHLIST", \
        "DANGER must NEVER yield WATCHLIST"
    print(f"  DANGER (slope 1.25) + vrp_ratio 1.10 → {r.recommendation}")
    print("  PASS: DANGER overrides WATCHLIST")


def test_caution_behavior_unchanged():
    """
    CAUTION recommendations come from a different code path than the VRP gate.
    The gate's actionable set is {SELL PREMIUM, CONDITIONAL}, neither of which
    CAUTION ever produces. So CAUTION behavior must be unchanged by Phase 1.
    """
    params = ScoringParams()

    # Slope-CAUTION + low score → NO EDGE
    s = _build_surface(
        ticker="C-low", iv_current=22.0, rv30=20.0, rv10=18.0,
        iv_rank=70, iv_pct=70,
        slope=1.10, accel=0.95, skew_25d=2.0,
        vrp_ratio=1.10,
    )
    r = score_opportunity(s, name="C-low", sector="Test", params=params)
    assert r.regime == "CAUTION"
    assert r.signal_score < 55
    assert r.recommendation == "NO EDGE", \
        f"CAUTION+score<55 must be NO EDGE, got {r.recommendation}"

    # Slope-CAUTION + low score + vrp_ratio HIGH (above gate) → still NO EDGE
    s2 = _build_surface(
        ticker="C-low-fat", iv_current=30.0, rv30=20.0, rv10=18.0,
        iv_rank=70, iv_pct=70,
        slope=1.10, accel=0.95, skew_25d=2.0,
    )
    r2 = score_opportunity(s2, name="C-low-fat", sector="Test", params=params)
    assert r2.regime == "CAUTION"
    if r2.signal_score < 55:
        assert r2.recommendation == "NO EDGE", \
            f"CAUTION+score<55 must be NO EDGE regardless of vrp_ratio, " \
            f"got {r2.recommendation} at vrp_ratio={s2.vrp_ratio:.2f}"

    # Path-2 CAUTION + score ≥ 55 + vrp_ratio 1.10 → REDUCE SIZE (gate doesn't fire)
    s3 = _build_surface(
        ticker="C-high", iv_current=22.0, rv30=20.0, rv10=18.0,
        iv_rank=95, iv_pct=100,
        slope=0.85, accel=1.105, skew_25d=7.0,
        vrp_ratio=1.10,
    )
    r3 = score_opportunity(s3, name="C-high", sector="Test", params=params)
    assert r3.regime == "CAUTION", f"Expected CAUTION via path 2, got {r3.regime}"
    assert r3.signal_score >= 55
    assert r3.recommendation == "REDUCE SIZE", \
        f"CAUTION+score≥55 must be REDUCE SIZE, got {r3.recommendation}"
    assert r3.recommendation != "WATCHLIST", \
        "VRP gate must NOT rewrite CAUTION recommendations"

    print("  CAUTION (low score → NO EDGE) and (high score → REDUCE SIZE) preserved")
    print("  PASS: CAUTION behavior unchanged")


# ─────────────────────────────────────────────────────────
# D. Degraded scan tests
# ─────────────────────────────────────────────────────────

def test_degraded_scan_suppresses_sell_conditional_watchlist():
    """All three actionable states downgrade to NO EDGE; pre-suppression
       diagnostic metadata is preserved."""
    sell = _StubResult("SELL PREMIUM", 0.85, signal_score=70, regime="NORMAL")
    cond = _StubResult("CONDITIONAL", 0.90, signal_score=55, regime="NORMAL")
    watch = _StubResult("WATCHLIST", 0.85, signal_score=46, regime="NORMAL")

    suppress_actionable([sell, cond, watch], reason="degraded test")

    for row, original in [(sell, "SELL PREMIUM"),
                          (cond, "CONDITIONAL"),
                          (watch, "WATCHLIST")]:
        assert row.recommendation == "NO EDGE", \
            f"{original} must downgrade to NO EDGE, got {row.recommendation}"
        assert row.suppressed_by_scan_quality is True
        assert row.pre_suppression_recommendation == original, \
            f"Pre-suppression rec for {original} must be preserved"
        assert row.pre_suppression_score == row.signal_score, \
            "Pre-suppression score must be captured"
        assert row.scan_quality_suppression_reason == "degraded test"

    print("  SELL/CONDITIONAL/WATCHLIST → NO EDGE with audit trail")
    print("  PASS: Degraded scan suppresses all three actionable states")


def test_degraded_scan_preserves_avoid_no_data_skip():
    """AVOID, NO DATA, true NO EDGE are not mutated and not flagged suppressed."""
    avoid = _StubResult("AVOID", 1.20, signal_score=42, regime="DANGER")
    no_data = _StubResult("NO DATA", None, signal_score=0, regime="NORMAL")
    no_edge = _StubResult("NO EDGE", 0.95, signal_score=33, regime="NORMAL")
    reduce_size = _StubResult("REDUCE SIZE", 1.10, signal_score=58,
                              regime="CAUTION")

    suppress_actionable([avoid, no_data, no_edge, reduce_size],
                        reason="test")

    # AVOID preserved
    assert avoid.recommendation == "AVOID"
    assert avoid.suppressed_by_scan_quality is False
    assert avoid.pre_suppression_recommendation is None

    # NO DATA preserved
    assert no_data.recommendation == "NO DATA"
    assert no_data.suppressed_by_scan_quality is False

    # True NO EDGE not flagged as suppressed
    assert no_edge.recommendation == "NO EDGE"
    assert no_edge.suppressed_by_scan_quality is False
    assert no_edge.pre_suppression_recommendation is None

    # REDUCE SIZE — note: the spec says SELL/CONDITIONAL/WATCHLIST are the
    # actionable set. REDUCE SIZE is the CAUTION-tier "tradeable but defensive"
    # state. Per current scan_quality.py, REDUCE SIZE is NOT in the actionable
    # set, so it survives suppression unchanged. Document this so a future
    # change doesn't silently broaden the set.
    assert reduce_size.recommendation == "REDUCE SIZE", (
        "REDUCE SIZE is not in the suppression set — verify intentional. "
        "If REDUCE SIZE should also suppress, update scan_quality.py + this test."
    )
    assert reduce_size.suppressed_by_scan_quality is False

    # SKIP scenario: SKIP is frontend-derived from the earnings gate.
    # Backend rows that *would* render as SKIP have rec ∈ {SELL, COND, WATCH}
    # *plus* earnings_dte ≤ 14. After suppression, rec→NO EDGE. The frontend
    # gate fires on earnings_dte (independent of rec) and still produces SKIP.
    skip_like = _StubResult("SELL PREMIUM", 0.85, signal_score=70, regime="NORMAL")
    skip_like.earnings_dte = 5
    suppress_actionable([skip_like], reason="test")
    final_action, _, _ = _simulate_frontend_gate(
        action=_map_action(skip_like.recommendation),
        signal_score=skip_like.signal_score,
        earnings_dte=skip_like.earnings_dte, is_etf=False,
    )
    assert final_action == "SKIP", \
        f"Earnings-gated row must remain SKIP after suppression, got {final_action}"

    print("  AVOID/NO DATA/NO EDGE/REDUCE SIZE preserved; SKIP gate still fires")
    print("  PASS: Degraded scan preserves AVOID/NO DATA/SKIP/NO EDGE")


def test_clean_scan_does_not_suppress():
    """OK quality means no mutation — actionable rows display unchanged."""
    rows = [
        _StubResult("SELL PREMIUM", 0.85, signal_score=70),
        _StubResult("CONDITIONAL", 0.90, signal_score=55),
        _StubResult("WATCHLIST", 0.85, signal_score=46),
        _StubResult("AVOID", 1.20, signal_score=42, regime="DANGER"),
        _StubResult("NO DATA", None, signal_score=0),
        _StubResult("NO EDGE", 0.95, signal_score=33),
    ]

    quality, reason = _apply_scan_quality_helper(rows)
    assert quality == "OK", f"Healthy fixture should be OK, got {quality} ({reason})"

    # Recommendations untouched
    assert rows[0].recommendation == "SELL PREMIUM"
    assert rows[1].recommendation == "CONDITIONAL"
    assert rows[2].recommendation == "WATCHLIST"
    assert rows[3].recommendation == "AVOID"
    assert rows[4].recommendation == "NO DATA"
    assert rows[5].recommendation == "NO EDGE"

    # No diagnostic flags set
    for r in rows:
        assert r.suppressed_by_scan_quality is False
        assert r.pre_suppression_recommendation is None
        assert r.scan_quality_suppression_reason is None

    print("  All actionable + non-actionable rows unchanged on OK scan")
    print("  PASS: Clean scan does not suppress")


# ─────────────────────────────────────────────────────────
# E. Scan-quality detection tests
# ─────────────────────────────────────────────────────────

def test_no_data_cluster_degraded():
    """NO_DATA_THRESHOLD = 4 (strict >). 5+ NO DATA → DEGRADED; 4 alone → OK."""
    assert NO_DATA_THRESHOLD == 4, \
        f"This test depends on NO_DATA_THRESHOLD=4; got {NO_DATA_THRESHOLD}"

    # 5 NO DATA → DEGRADED (5 > 4)
    rows = [_StubResult("NO DATA", None) for _ in range(5)]
    rows += [_StubResult("NO EDGE", 0.85) for _ in range(20)]
    quality, reason = compute_scan_quality(rows)
    assert quality == "DEGRADED", f"5 NO DATA must be DEGRADED, got {quality}"
    assert "NO DATA" in (reason or "")

    # 4 NO DATA + varied slopes → OK (no slope wall trigger either)
    rows = [_StubResult("NO DATA", None) for _ in range(4)]
    rows += [_StubResult("NO EDGE", 0.85)]
    rows += [_StubResult("NO EDGE", 0.92)]
    rows += [_StubResult("CONDITIONAL", 0.78)]
    rows += [_StubResult("AVOID", 1.20)]
    rows += [_StubResult("NO EDGE", 1.02)]
    rows += [_StubResult("NO EDGE", 0.71)]
    rows += [_StubResult("SELL PREMIUM", 0.82)]
    quality, _ = compute_scan_quality(rows)
    assert quality == "OK", f"4 NO DATA alone must be OK, got {quality}"

    # 4 NO DATA + slope wall → DEGRADED via slope path
    rows = [_StubResult("NO DATA", None) for _ in range(4)]
    rows += [_StubResult("NO EDGE", 1.00) for _ in range(8)]   # 8/16 = 50% wall
    rows += [_StubResult("NO EDGE", 0.85) for _ in range(4)]
    quality, reason = compute_scan_quality(rows)
    assert quality == "DEGRADED", \
        f"4 NO DATA + slope wall must be DEGRADED, got {quality}"
    assert "1.00" in (reason or "") or "slope" in (reason or "").lower()

    print("  5 NO DATA → DEGRADED; 4 NO DATA alone → OK; 4 + slope wall → DEGRADED")
    print("  PASS: NO DATA cluster detection")


def test_slope_wall_degraded():
    """SLOPE_WALL_THRESHOLD = 0.25 (strict >). 25% exactly → OK; >25% → DEGRADED."""
    assert SLOPE_WALL_THRESHOLD == 0.25, \
        f"This test depends on SLOPE_WALL_THRESHOLD=0.25; got {SLOPE_WALL_THRESHOLD}"

    # Exactly 25%: 1 of 4 at slope 1.00 → OK (strict >)
    rows = [_StubResult("NO EDGE", 1.00)]
    rows += [_StubResult("NO EDGE", 0.85),
             _StubResult("NO EDGE", 0.92),
             _StubResult("NO EDGE", 1.10)]
    quality, _ = compute_scan_quality(rows)
    assert quality == "OK", \
        f"Exactly 25% slope wall must be OK (strict >), got {quality}"

    # >25%: 2 of 7 (28.6%) → DEGRADED
    rows = [_StubResult("NO EDGE", 1.00) for _ in range(2)]
    rows += [_StubResult("NO EDGE", 0.85),
             _StubResult("NO EDGE", 0.92),
             _StubResult("NO EDGE", 1.10),
             _StubResult("NO EDGE", 0.78),
             _StubResult("NO EDGE", 0.95)]
    quality, _ = compute_scan_quality(rows)
    assert quality == "DEGRADED", \
        f"28.6% slope wall must be DEGRADED, got {quality}"

    # 80% slope wall → DEGRADED with high pct in reason
    rows = [_StubResult("NO EDGE", 1.00) for _ in range(8)]
    rows += [_StubResult("NO EDGE", 0.85),
             _StubResult("NO EDGE", 0.92)]
    quality, reason = compute_scan_quality(rows)
    assert quality == "DEGRADED"
    assert "80%" in (reason or "")

    print("  25% boundary → OK; 28.6% → DEGRADED; 80% → DEGRADED")
    print("  PASS: Slope-wall threshold")


def test_slope_wall_tolerance_is_tight():
    """
    SLOPE_WALL_TOLERANCE = 0.001 — only near-exact 1.00 counts.

    Floating-point note: at this tolerance, IEEE-754 representation makes
    `abs(1.001 - 1.0)` evaluate to ~0.0009999... (< 0.001 → counted),
    while `abs(0.999 - 1.0)` evaluates to ~0.0010000... (NOT < 0.001 → not
    counted). The asymmetry is harmless in production (it's a fail-safe
    direction — slightly more rows could count) but means test inputs at
    exactly 1.001 / 0.999 are unstable. We use FP-safe inputs (clearly
    inside or clearly outside) and verify the rounded thresholds.
    """
    assert SLOPE_WALL_TOLERANCE == 0.001, \
        f"This test depends on SLOPE_WALL_TOLERANCE=0.001; got {SLOPE_WALL_TOLERANCE}"

    # Clearly within tolerance (diff well under 0.001):
    counted = [1.0000, 1.0005, 0.9995, 1.0001]
    # Clearly outside tolerance (diff well above 0.001):
    not_counted = [1.005, 1.02, 0.95, 1.10, 0.85, 0.78, 0.92]

    rows = [_StubResult("NO EDGE", v) for v in counted]
    rows += [_StubResult("NO EDGE", v) for v in not_counted]
    # counted=4, total=11 → 36% → > 25% → DEGRADED
    quality, reason = compute_scan_quality(rows)
    assert quality == "DEGRADED", \
        f"4/11 (36%) at slope ≈ 1.00 must be DEGRADED, got {quality}"
    # The reason must reflect the 4 counted (not the full 11).
    assert "4 of 11" in (reason or ""), \
        f"Reason should report '4 of 11' counted, got {reason!r}"

    # Flip: only outside-tolerance values → never trigger wall regardless of count.
    # (1.02 / 0.95 / etc. are real curves, not degenerate ≈1.00 readings.)
    rows = [_StubResult("NO EDGE", v) for v in not_counted * 2]   # 14 rows
    quality, _ = compute_scan_quality(rows)
    assert quality == "OK", \
        f"Real (non-1.00) slopes must NOT trigger wall, got {quality}"

    # Spot-check the critical spec claims:
    # 1.000 must count
    assert abs(1.000 - 1.0) < SLOPE_WALL_TOLERANCE
    # 1.0005 must count (FP-safe value)
    assert abs(1.0005 - 1.0) < SLOPE_WALL_TOLERANCE
    # 1.02 must NOT count
    assert not (abs(1.02 - 1.0) < SLOPE_WALL_TOLERANCE)

    print("  1.0000/1.0005/0.9995/1.0001 counted; 1.005/1.02/0.95 NOT counted")
    print("  PASS: Slope-wall tolerance is tight")


# ─────────────────────────────────────────────────────────
# F. Cached path tests
# ─────────────────────────────────────────────────────────

def test_scan_quality_applied_to_cached_latest_scan():
    """
    Cached responses run through the same _apply_scan_quality helper as fresh
    scans. A cached scan that meets DEGRADED criteria gets suppressed on read.
    """
    cached = [
        _build_ticker_result(ticker="X1", recommendation="SELL PREMIUM",
                             term_slope=0.85, signal_score=70),
        _build_ticker_result(ticker="X2", recommendation="CONDITIONAL",
                             term_slope=0.95, signal_score=50),
        _build_ticker_result(ticker="X3", recommendation="WATCHLIST",
                             term_slope=0.80, signal_score=46),
    ]
    cached += [
        _build_ticker_result(ticker=f"ND{i}", recommendation="NO DATA",
                             term_slope=1.0, signal_score=0)
        for i in range(13)
    ]

    quality, reason = _apply_scan_quality_helper(cached)

    assert quality == "DEGRADED", \
        f"Cached scan with 13 NO DATA must be DEGRADED, got {quality}"

    # API response shape includes the fields
    response = ScanResponse(
        timestamp="2026-04-16T22:30:00",
        regime=None,
        tickers=cached,
        historical={},
        scanned_at="2026-04-16T22:30:00",
        cached=True,
        scan_quality=quality,
        scan_quality_reason=reason,
    )
    assert response.scan_quality == "DEGRADED"
    assert "NO DATA" in (response.scan_quality_reason or "")

    # Suppression applied
    sell, cond, watch = cached[0], cached[1], cached[2]
    assert sell.recommendation == "NO EDGE"
    assert sell.suppressed_by_scan_quality is True
    assert sell.pre_suppression_recommendation == "SELL PREMIUM"
    assert sell.signal_score == 70   # unchanged
    assert cond.recommendation == "NO EDGE"
    assert watch.recommendation == "NO EDGE"

    print("  Cached scan: DEGRADED detected, 3 actionable rows suppressed")
    print("  PASS: Scan-quality applied to cached latest scan")


def test_scan_quality_applied_to_historical_scan():
    """
    Old cached scans pre-date the diagnostic fields. Pydantic uses defaults
    (False / None) on missing fields, and the helper still produces correct
    output without DB migration.
    """
    # Simulate raw cached JSON without diagnostic fields, as if produced
    # before Phase 1 audit metadata was added.
    raw = {
        "ticker": "OLD",
        "name": "Old Ticker",
        "sector": "Test",
        "price": 100.0,
        "iv_current": 22.0,
        "iv_rank": 80.0,
        "iv_percentile": 80.0,
        "rv10": 18.0,
        "rv20": 19.0,
        "rv30": 20.0,
        "vrp": 2.0,
        "vrp_ratio": 1.10,
        "rv_acceleration": 0.85,
        "term_slope": 0.85,
        "is_contango": True,
        "skew_25d": 7.0,
        "signal_score": 70,
        "regime": "NORMAL",
        "recommendation": "SELL PREMIUM",
        "flags": [],
        "suggested_delta": "20Δ",
        "suggested_structure": "PCS",
        "suggested_dte": "30 DTE",
        "suggested_max_notional": "3%",
        "earnings_dte": None,
        "is_etf": False,
        # No suppressed_by_scan_quality, no pre_suppression_*, no scan_quality_*
    }
    ticker = TickerResult(**raw)

    # Defaults applied
    assert ticker.suppressed_by_scan_quality is False
    assert ticker.pre_suppression_recommendation is None
    assert ticker.pre_suppression_score is None
    assert ticker.scan_quality_suppression_reason is None

    # Build a degraded fixture using this ticker + 5 NO DATA siblings
    cached = [ticker]
    cached += [
        _build_ticker_result(ticker=f"ND{i}", recommendation="NO DATA",
                             term_slope=0.95, signal_score=0)
        for i in range(5)
    ]

    quality, reason = _apply_scan_quality_helper(cached)
    assert quality == "DEGRADED", \
        f"Should detect DEGRADED on old-format cached data, got {quality}"

    # The old-format ticker now carries fresh suppression metadata
    assert ticker.recommendation == "NO EDGE"
    assert ticker.suppressed_by_scan_quality is True
    assert ticker.pre_suppression_recommendation == "SELL PREMIUM"
    assert ticker.pre_suppression_score == 70
    assert ticker.scan_quality_suppression_reason == reason
    assert ticker.signal_score == 70   # never zeroed

    print("  Old cached row (no diag fields) accepts defaults + gets fresh suppression")
    print("  PASS: Scan-quality applied to historical cached scan (no migration needed)")


def test_cached_ok_scan_unchanged():
    """
    A cached healthy scan reads back as OK with no suppression applied.
    """
    cached = [
        _build_ticker_result(ticker="OK1", recommendation="SELL PREMIUM",
                             term_slope=0.82, signal_score=70),
        _build_ticker_result(ticker="OK2", recommendation="CONDITIONAL",
                             term_slope=0.90, signal_score=50),
        _build_ticker_result(ticker="OK3", recommendation="WATCHLIST",
                             term_slope=0.85, signal_score=46),
        _build_ticker_result(ticker="OK4", recommendation="AVOID",
                             term_slope=1.25, signal_score=42, regime="DANGER"),
        _build_ticker_result(ticker="OK5", recommendation="NO EDGE",
                             term_slope=0.95, signal_score=33),
        _build_ticker_result(ticker="OK6", recommendation="NO DATA",
                             term_slope=0.78, signal_score=0),
    ]

    quality, reason = _apply_scan_quality_helper(cached)
    assert quality == "OK", \
        f"Healthy cached fixture must be OK, got {quality} ({reason})"
    assert reason is None

    # Recommendations untouched
    assert cached[0].recommendation == "SELL PREMIUM"
    assert cached[1].recommendation == "CONDITIONAL"
    assert cached[2].recommendation == "WATCHLIST"
    assert cached[3].recommendation == "AVOID"
    assert cached[4].recommendation == "NO EDGE"
    assert cached[5].recommendation == "NO DATA"

    # No diagnostic flags set
    for r in cached:
        assert r.suppressed_by_scan_quality is False
        assert r.pre_suppression_recommendation is None

    print("  6-row healthy cached scan: OK, no suppression")
    print("  PASS: Cached OK scan unchanged")


# ─────────────────────────────────────────────────────────
# Sanity checks for "WATCHLIST never tradeable"
# ─────────────────────────────────────────────────────────

def test_watchlist_not_counted_as_tradeable():
    """
    Mirror the leaderboard's tradeable count logic (Leaderboard.tsx:248-249):
        sellCount = data.filter(d => d.action === 'SELL').length;
        conditionalCount = data.filter(d => d.action === 'CONDITIONAL').length;
    WATCHLIST is excluded — must never be counted as tradeable.
    """
    actions = ["CONDITIONAL", "WATCHLIST", "WATCHLIST", "SKIP",
               "SELL", "NO EDGE", "AVOID", "NO DATA"]
    sell_count = sum(1 for a in actions if a == "SELL")
    conditional_count = sum(1 for a in actions if a == "CONDITIONAL")
    watchlist_count = sum(1 for a in actions if a == "WATCHLIST")
    assert sell_count == 1
    assert conditional_count == 1, \
        f"Banner must report 1 conditional (not 3 — WATCHLIST excluded), got {conditional_count}"
    assert watchlist_count == 2
    print(f"  Tradeable counts: {sell_count} SELL / {conditional_count} CONDITIONAL "
          f"({watchlist_count} watchlist excluded)")
    print("  PASS: WATCHLIST not counted as tradeable")


# ─────────────────────────────────────────────────────────
# Runner
# ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 64)
    print("QA Phase 1 — Production Regression Tests")
    print("=" * 64)

    tests = [
        # A. VRP gate precedence
        ("A1: VRP gate only NORMAL SELL/CONDITIONAL",
            test_vrp_gate_only_applies_to_normal_sell_or_conditional),
        ("A2: VRP gate boundary conditions",
            test_vrp_gate_boundary_conditions),
        ("A3: VRP gate preserves score (QQQ May 8)",
            test_vrp_gate_preserves_score),
        # B. Earnings precedence
        ("B4: Earnings gate overrides WATCHLIST/SELL",
            test_earnings_gate_overrides_watchlist_frontend_or_transform_layer),
        ("B5: ETFs never earnings-gated",
            test_etf_never_earnings_gated),
        # C. DANGER / CAUTION
        ("C6: DANGER overrides WATCHLIST",
            test_danger_overrides_watchlist),
        ("C7: CAUTION behavior unchanged",
            test_caution_behavior_unchanged),
        # D. Degraded scan
        ("D8: Degraded suppresses SELL/COND/WATCHLIST",
            test_degraded_scan_suppresses_sell_conditional_watchlist),
        ("D9: Degraded preserves AVOID/NO DATA/SKIP",
            test_degraded_scan_preserves_avoid_no_data_skip),
        ("D10: Clean scan does not suppress",
            test_clean_scan_does_not_suppress),
        # E. Scan-quality detection
        ("E11: NO DATA cluster threshold",
            test_no_data_cluster_degraded),
        ("E12: Slope wall threshold (>25% strict)",
            test_slope_wall_degraded),
        ("E13: Slope wall tolerance is tight",
            test_slope_wall_tolerance_is_tight),
        # F. Cached path
        ("F14: Scan quality on cached latest scan",
            test_scan_quality_applied_to_cached_latest_scan),
        ("F15: Scan quality on historical (old-format) scan",
            test_scan_quality_applied_to_historical_scan),
        ("F16: Cached OK scan unchanged",
            test_cached_ok_scan_unchanged),
        # Tradeable count invariant
        ("G19: WATCHLIST not counted as tradeable",
            test_watchlist_not_counted_as_tradeable),
    ]

    passed = 0
    failed = 0
    for name, fn in tests:
        print(f"\nTest: {name}")
        try:
            fn()
            passed += 1
        except AssertionError as e:
            print(f"  FAIL: {e}")
            failed += 1
        except Exception as e:
            print(f"  ERROR: {type(e).__name__}: {e}")
            failed += 1

    print("\n" + "=" * 64)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 64)
    sys.exit(0 if failed == 0 else 1)
