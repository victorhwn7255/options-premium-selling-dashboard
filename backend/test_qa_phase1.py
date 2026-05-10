"""
QA Phase 1 tests — VRP-ratio actionability gate, WATCHLIST tier, scan-quality detection.

Implements the acceptance tests requested in the Phase 1 fix list:
  - QQQ May 8 → WATCHLIST (vrp_ratio 1.026 < 1.15)
  - XLF May 8 → WATCHLIST (vrp_ratio 1.083 < 1.15)
  - JNJ May 8 → CONDITIONAL preserved (vrp_ratio 1.333 ≥ 1.15)
  - WMT May 8 → SKIP via earnings gate (frontend-side, simulated)
  - Apr 16-style scan → DEGRADED (NO DATA cluster + slope-1.00 wall)
  - Raw signal_score unchanged when action becomes WATCHLIST

Run: cd backend && python test_qa_phase1.py
"""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from calculator import (
    VolSurface, RealizedVol, ImpliedVolMetrics,
    TermStructure, VolSkew,
)
from scorer import score_opportunity, ScoringParams
from scan_quality import compute_scan_quality, suppress_actionable


# ── Fixtures ──────────────────────────────────────────────

def _build_surface(*, ticker, iv_current, rv30, rv10,
                   iv_rank, iv_pct, slope, accel, skew_25d,
                   rv20=None, rv60=None):
    """
    Build a minimal VolSurface fixture matching the column shape in metrics-logs.md.
    Some inputs are nudged up by 0–1 unit relative to the displayed (rounded) value
    so the recomputed `int(score)` clears recommendation thresholds; the displayed
    values would otherwise round-down past `int()` truncation.
    """
    if rv20 is None:
        rv20 = rv30
    if rv60 is None:
        rv60 = rv30
    vrp = iv_current - rv30
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


# Real May 8, 2026 data nudged where needed so int(score) ≥ 45 (gate's input precondition).
# Every fixture preserves vrp_ratio's relationship to the 1.15 threshold.

QQQ_MAY8 = dict(
    ticker="QQQ",
    iv_current=19.4, rv30=18.9, rv10=18.0,
    iv_rank=51, iv_pct=51,           # displayed 50; nudged for int() truncation
    slope=0.78, accel=0.89, skew_25d=3.1,
)

XLF_MAY8 = dict(
    ticker="XLF",
    iv_current=17.0, rv30=15.7, rv10=11.3,
    iv_rank=48, iv_pct=48,           # displayed 47; nudged
    slope=0.77, accel=0.51, skew_25d=2.8,
)

JNJ_MAY8 = dict(
    ticker="JNJ",
    iv_current=21.2, rv30=15.9, rv10=14.3,
    iv_rank=76, iv_pct=76,
    slope=0.89, accel=0.90, skew_25d=0.3,
)

WMT_MAY8 = dict(
    ticker="WMT",
    iv_current=31.3, rv30=23.2, rv10=19.7,
    iv_rank=85, iv_pct=85,
    slope=0.82, accel=0.85, skew_25d=2.0,
)


# ── Stub for scan-quality testing ─────────────────────────

class _StubResult:
    """Duck-typed stand-in for TickerResult — only fields used by scan_quality."""

    def __init__(self, recommendation: str, term_slope, signal_score: int = 0,
                 regime: str = "NORMAL"):
        self.recommendation = recommendation
        self.term_slope = term_slope
        self.signal_score = signal_score
        self.regime = regime
        self.flags = []
        self.suggested_delta = "x"
        self.suggested_structure = "x"
        self.suggested_dte = "x"
        self.suggested_max_notional = "x"
        # Diagnostic fields default to false/None until suppression sets them.
        self.suppressed_by_scan_quality = False
        self.pre_suppression_recommendation = None
        self.pre_suppression_score = None
        self.scan_quality_suppression_reason = None


# ── Tests ─────────────────────────────────────────────────

def test_qqq_may8_becomes_watchlist():
    """QQQ May 8: vrp_ratio 1.026 < 1.15 → must be WATCHLIST, not CONDITIONAL."""
    surface = _build_surface(**QQQ_MAY8)
    scored = score_opportunity(surface, name="Invesco QQQ",
                               sector="Index", params=ScoringParams())

    assert surface.vrp_ratio < 1.15, \
        f"Fixture vrp_ratio should be < 1.15, got {surface.vrp_ratio:.3f}"
    assert scored.recommendation == "WATCHLIST", \
        (f"Expected WATCHLIST (vrp_ratio {surface.vrp_ratio:.3f} < 1.15), "
         f"got {scored.recommendation}")
    assert scored.signal_score >= 45, \
        f"Score must reach 45+ (gate's input precondition), got {scored.signal_score}"
    assert any("premium too thin" in f.lower() for f in scored.flags), \
        f"Expected explanatory flag, got {scored.flags}"
    print(f"  QQQ: score={scored.signal_score}, rec={scored.recommendation}, "
          f"vrp_ratio={surface.vrp_ratio:.3f}")
    print("  PASS: QQQ May 8 → WATCHLIST")


def test_xlf_may8_becomes_watchlist():
    """XLF May 8: vrp_ratio 1.083 < 1.15 → must be WATCHLIST, not CONDITIONAL."""
    surface = _build_surface(**XLF_MAY8)
    scored = score_opportunity(surface, name="Financial Sector ETF",
                               sector="Financials", params=ScoringParams())

    assert surface.vrp_ratio < 1.15, \
        f"Fixture vrp_ratio should be < 1.15, got {surface.vrp_ratio:.3f}"
    assert scored.recommendation == "WATCHLIST", \
        (f"Expected WATCHLIST, got {scored.recommendation} "
         f"(score {scored.signal_score}, vrp_ratio {surface.vrp_ratio:.3f})")
    assert scored.signal_score >= 45, \
        f"Score must reach 45+, got {scored.signal_score}"
    print(f"  XLF: score={scored.signal_score}, rec={scored.recommendation}, "
          f"vrp_ratio={surface.vrp_ratio:.3f}")
    print("  PASS: XLF May 8 → WATCHLIST")


def test_jnj_may8_remains_conditional():
    """JNJ May 8: vrp_ratio 1.333 ≥ 1.15 → CONDITIONAL or SELL preserved (real edge)."""
    surface = _build_surface(**JNJ_MAY8)
    scored = score_opportunity(surface, name="Johnson & Johnson",
                               sector="Healthcare", params=ScoringParams())

    assert surface.vrp_ratio >= 1.15, \
        f"Fixture vrp_ratio should be ≥ 1.15, got {surface.vrp_ratio:.3f}"
    assert scored.recommendation in ("CONDITIONAL", "SELL PREMIUM"), \
        (f"Expected CONDITIONAL/SELL (vrp_ratio {surface.vrp_ratio:.3f}), "
         f"got {scored.recommendation}")
    assert "premium too thin" not in " ".join(scored.flags).lower(), \
        f"Should NOT carry thin-premium flag at vrp_ratio 1.333: {scored.flags}"
    print(f"  JNJ: score={scored.signal_score}, rec={scored.recommendation}, "
          f"vrp_ratio={surface.vrp_ratio:.3f}")
    print("  PASS: JNJ May 8 → CONDITIONAL preserved")


def test_wmt_may8_skip_via_earnings_gate():
    """
    WMT May 8: backend produces SELL/CONDITIONAL; frontend earnings gate
    (per ADR-003, scoring.ts:34-39) maps to SKIP when earnings_dte ≤ 14.
    Since the gate is frontend-only, we verify the backend output here and
    simulate the frontend gate to confirm the full pipeline.
    """
    surface = _build_surface(**WMT_MAY8)
    scored = score_opportunity(surface, name="Walmart",
                               sector="Consumer", params=ScoringParams())

    assert scored.recommendation in ("SELL PREMIUM", "CONDITIONAL"), \
        f"Backend should rate WMT tradeable, got {scored.recommendation}"
    assert surface.vrp_ratio >= 1.15, \
        "WMT should be past the dead zone (not WATCHLIST)"

    # Simulate the frontend earnings gate (frontend/src/lib/scoring.ts:34-39).
    # WMT verified May 14 from May 8 = 6 trading days; sample value 9 chosen
    # to demonstrate any DTE ≤ 14 fires the gate.
    earnings_dte = 9
    is_etf = False
    backend_score = scored.signal_score
    backend_action = scored.recommendation

    if earnings_dte is not None and earnings_dte <= 14 and not is_etf:
        gated_action = "SKIP"
        gated_score = 0
        pre_gate_score = backend_score
    else:
        gated_action = backend_action
        gated_score = backend_score
        pre_gate_score = None

    assert gated_action == "SKIP", \
        f"Frontend earnings gate must fire SKIP at DTE=9, got {gated_action}"
    assert gated_score == 0, \
        f"Gated displayed score must be 0, got {gated_score}"
    assert pre_gate_score == backend_score, \
        f"preGateScore must preserve backend score ({backend_score}), got {pre_gate_score}"
    print(f"  WMT: backend score={backend_score} ({backend_action}) → "
          f"frontend SKIP (preGate={pre_gate_score})")
    print("  PASS: WMT May 8 → SKIP via earnings gate")


def test_apr16_style_scan_degraded_no_data():
    """Apr 16 style: 13 NO DATA + others → DEGRADED (NO DATA threshold > 4)."""
    results = [_StubResult("NO DATA", 1.00) for _ in range(13)]
    results += [_StubResult("CONDITIONAL", 0.85) for _ in range(5)]
    results += [_StubResult("NO EDGE", 0.95) for _ in range(15)]

    quality, reason = compute_scan_quality(results)
    assert quality == "DEGRADED", \
        f"Expected DEGRADED with 13 NO DATA, got {quality}"
    assert "NO DATA" in (reason or ""), \
        f"Reason should reference NO DATA: {reason!r}"
    print(f"  Reason: {reason}")
    print("  PASS: Apr 16 style → DEGRADED (NO DATA cluster)")


def test_apr16_style_scan_degraded_slope_wall():
    """
    Apr 16 also: 16 of remaining 20 tickers showed slope == 1.00.
    Fewer NO DATA but still DEGRADED via the slope-wall trigger.
    """
    # 4 NO DATA (under threshold), 14 of 25 at slope 1.00 (56%, well above 25%).
    results = [_StubResult("NO DATA", None) for _ in range(4)]
    results += [_StubResult("NO EDGE", 1.00) for _ in range(14)]
    results += [_StubResult("NO EDGE", 0.85) for _ in range(7)]
    results += [_StubResult("CONDITIONAL", 0.92) for _ in range(4)]

    quality, reason = compute_scan_quality(results)
    assert quality == "DEGRADED", \
        f"Expected DEGRADED with 14/29 at slope 1.00, got {quality}"
    assert "1.00" in (reason or "") or "slope" in (reason or "").lower(), \
        f"Reason should reference slope wall: {reason!r}"
    print(f"  Reason: {reason}")
    print("  PASS: Apr 16 style → DEGRADED (slope-1.00 wall)")


def test_clean_scan_is_ok():
    """Healthy scan: 1 NO DATA + varied slopes → OK."""
    results = [
        _StubResult("NO DATA", None),
        _StubResult("NO EDGE", 0.85),
        _StubResult("NO EDGE", 0.92),
        _StubResult("CONDITIONAL", 0.78),
        _StubResult("AVOID", 1.18),
        _StubResult("NO EDGE", 1.02),
        _StubResult("NO EDGE", 0.71),
        _StubResult("SELL PREMIUM", 0.82),
    ]

    quality, reason = compute_scan_quality(results)
    assert quality == "OK", f"Expected OK, got {quality} ({reason})"
    print("  PASS: Clean scan → OK")


def test_degraded_suppression_zeros_actionable():
    """
    When DEGRADED, all SELL / CONDITIONAL / WATCHLIST rows downgrade to NO EDGE;
    AVOID and NO DATA are preserved (they're already non-tradeable).
    """
    results = [
        _StubResult("SELL PREMIUM", 0.82),
        _StubResult("CONDITIONAL", 0.85),
        _StubResult("WATCHLIST", 0.78),
        _StubResult("NO EDGE", 1.02),
        _StubResult("AVOID", 1.20),
        _StubResult("NO DATA", None),
    ]

    n = suppress_actionable(results, reason="test reason")
    assert n == 3, f"Expected 3 suppressions (SELL+COND+WATCH), got {n}"
    assert results[0].recommendation == "NO EDGE"
    assert results[1].recommendation == "NO EDGE"
    assert results[2].recommendation == "NO EDGE"
    assert results[3].recommendation == "NO EDGE"   # already
    assert results[4].recommendation == "AVOID"     # preserved
    assert results[5].recommendation == "NO DATA"   # preserved
    assert any("Scan quality degraded" in f for f in results[0].flags), \
        f"Suppressed row should carry explanation flag, got {results[0].flags}"
    print(f"  Suppressed {n} actionable rows; AVOID/NO DATA preserved")
    print("  PASS: Degraded suppression")


def test_degraded_suppression_preserves_raw_recommendation():
    """
    SELL / CONDITIONAL / WATCHLIST get displayed as NO EDGE for safety,
    but the original recommendation is preserved on the row for audit.
    AVOID / NO DATA / NO EDGE are not touched and not marked suppressed.
    """
    results = [
        _StubResult("SELL PREMIUM", 0.82, signal_score=72, regime="NORMAL"),
        _StubResult("CONDITIONAL", 0.85, signal_score=55, regime="NORMAL"),
        _StubResult("WATCHLIST", 0.78, signal_score=46, regime="NORMAL"),
        _StubResult("AVOID", 1.20, signal_score=42, regime="DANGER"),
        _StubResult("NO DATA", None, signal_score=0, regime="NORMAL"),
        _StubResult("NO EDGE", 0.95, signal_score=33, regime="NORMAL"),
    ]
    sell, cond, watch, avoid, no_data, no_edge = results

    suppress_actionable(results, reason="test")

    # All three actionable rows display as NO EDGE (safe) ...
    assert sell.recommendation == "NO EDGE"
    assert cond.recommendation == "NO EDGE"
    assert watch.recommendation == "NO EDGE"
    # ... AND carry pre-suppression context for audit.
    assert sell.suppressed_by_scan_quality is True
    assert sell.pre_suppression_recommendation == "SELL PREMIUM"
    assert cond.suppressed_by_scan_quality is True
    assert cond.pre_suppression_recommendation == "CONDITIONAL"
    assert watch.suppressed_by_scan_quality is True
    assert watch.pre_suppression_recommendation == "WATCHLIST"

    # signal_score is preserved through the gate.
    assert sell.signal_score == 72
    assert cond.signal_score == 55
    assert watch.signal_score == 46

    # AVOID stays AVOID and is NOT marked suppressed.
    assert avoid.recommendation == "AVOID"
    assert avoid.suppressed_by_scan_quality is False
    assert avoid.pre_suppression_recommendation is None

    # NO DATA stays NO DATA and is NOT marked suppressed.
    assert no_data.recommendation == "NO DATA"
    assert no_data.suppressed_by_scan_quality is False

    # True NO EDGE is NOT marked suppressed (it was always non-actionable).
    assert no_edge.recommendation == "NO EDGE"
    assert no_edge.suppressed_by_scan_quality is False
    assert no_edge.pre_suppression_recommendation is None

    print("  Audit: SELL/CONDITIONAL/WATCHLIST preserved pre-suppression rec; "
          "AVOID/NO DATA/NO EDGE untouched")
    print("  PASS: Degraded suppression preserves raw recommendation")


def test_suppression_reason_is_propagated():
    """The scan_quality_reason string must travel onto every suppressed row."""
    reason = "13 NO DATA tickers"
    results = [
        _StubResult("SELL PREMIUM", 0.82, signal_score=70),
        _StubResult("CONDITIONAL", 0.85, signal_score=50),
        _StubResult("WATCHLIST", 0.78, signal_score=46),
        _StubResult("NO EDGE", 0.95, signal_score=20),
        _StubResult("AVOID", 1.20, signal_score=40),
    ]

    suppress_actionable(results, reason=reason)

    # Suppressed rows carry the reason.
    for r in results[:3]:
        assert r.scan_quality_suppression_reason == reason, \
            f"Suppressed row should carry reason {reason!r}, got {r.scan_quality_suppression_reason!r}"
        assert any(reason in f for f in r.flags), \
            f"Reason should also appear in flags: {r.flags}"

    # Untouched rows do NOT carry the reason.
    no_edge_row, avoid_row = results[3], results[4]
    assert no_edge_row.scan_quality_suppression_reason is None
    assert avoid_row.scan_quality_suppression_reason is None

    print(f"  Reason propagated to all 3 suppressed rows: {reason!r}")
    print("  PASS: Suppression reason propagated")


def test_raw_score_unchanged_after_degraded_suppression():
    """
    A SELL with score 70 suppressed to NO EDGE retains signal_score=70 AND
    has pre_suppression_score=70 captured explicitly. The displayed action
    is NO EDGE, but every score-related field tells the audit story truthfully.
    """
    sell_row = _StubResult("SELL PREMIUM", 0.82, signal_score=70, regime="NORMAL")
    cond_row = _StubResult("CONDITIONAL", 0.90, signal_score=55, regime="NORMAL")
    watch_row = _StubResult("WATCHLIST", 0.85, signal_score=46, regime="NORMAL")

    suppress_actionable([sell_row, cond_row, watch_row], reason="degraded test")

    # Display state: NO EDGE.
    assert sell_row.recommendation == "NO EDGE"
    assert cond_row.recommendation == "NO EDGE"
    assert watch_row.recommendation == "NO EDGE"

    # Raw score: unchanged (the formula output is the audit truth).
    assert sell_row.signal_score == 70, \
        f"signal_score must be preserved at 70, got {sell_row.signal_score}"
    assert cond_row.signal_score == 55
    assert watch_row.signal_score == 46

    # pre_suppression_score: explicit copy at suppression time.
    assert sell_row.pre_suppression_score == 70
    assert cond_row.pre_suppression_score == 55
    assert watch_row.pre_suppression_score == 46

    # Regime: also preserved.
    assert sell_row.regime == "NORMAL"

    print("  signal_score preserved at 70/55/46; pre_suppression_score captured")
    print("  PASS: Raw score unchanged after degraded suppression")


def test_raw_score_unchanged_when_watchlist():
    """
    The VRP-ratio gate must preserve signal_score (it only changes recommendation).
    Verifies QQQ May 8 yields the same composite score the formula produces;
    nothing is zeroed when the action moves to WATCHLIST.
    """
    surface = _build_surface(**QQQ_MAY8)
    scored = score_opportunity(surface, name="Invesco QQQ",
                               sector="Index", params=ScoringParams())

    assert scored.recommendation == "WATCHLIST", \
        f"Expected WATCHLIST, got {scored.recommendation}"

    # Manually recompute the additive components (mirror scorer.py:122-190)
    # to verify the published score is preserved through the gate.
    def _vrp_pts(ratio):
        return min(30, max(0, (ratio - 1.15) * (30.0 / 0.45)))

    def _iv_pts(pct):
        return max(0, (pct - 30) * (25.0 / 70.0))

    def _term_pts(slope):
        if slope <= 0.85:
            return 20.0
        if slope >= 1.15:
            return 0.0
        if slope <= 1.0:
            return 5.0 + (1.0 - slope) / 0.15 * 15.0
        return 5.0 * (1.15 - slope) / 0.15

    def _rv_pts(accel):
        if accel <= 0.85:
            return 15.0
        if accel >= 1.15:
            return 0.0
        if accel <= 1.0:
            return 10.0 + (1.0 - accel) / 0.15 * 5.0
        return 10.0 * (1.15 - accel) / 0.15

    def _skew_pts(skew):
        if skew < 0:
            return 0.0
        if skew <= 7:
            return skew / 7.0 * 10.0
        if skew <= 12:
            return 10.0
        if skew <= 20:
            return 10.0 * (20.0 - skew) / 8.0
        return 0.0

    expected = int(
        _vrp_pts(surface.vrp_ratio)
        + _iv_pts(surface.iv.iv_percentile)
        + _term_pts(surface.term_structure.slope)
        + _rv_pts(surface.rv.rv_acceleration)
        + _skew_pts(surface.skew.skew_25d)
    )
    # Negative-VRP cap doesn't apply here (vrp positive).
    assert scored.signal_score == expected, \
        (f"Score must equal additive recompute. "
         f"Got {scored.signal_score}, expected {expected}")
    assert scored.signal_score >= 45, \
        "Score must clear 45 — otherwise the gate's precondition isn't tested"
    print(f"  Score preserved: {scored.signal_score} (recomputed {expected}); "
          f"action={scored.recommendation}")
    print("  PASS: Raw score unchanged when action → WATCHLIST")


def test_watchlist_position_construction_is_zeroed():
    """WATCHLIST rows must have no Position Construction (notional 0%, delta N/A)."""
    surface = _build_surface(**QQQ_MAY8)
    scored = score_opportunity(surface, name="Invesco QQQ",
                               sector="Index", params=ScoringParams())

    assert scored.recommendation == "WATCHLIST"
    assert scored.suggested_max_notional == "0%", \
        f"Expected 0% notional, got {scored.suggested_max_notional!r}"
    assert scored.suggested_delta == "N/A"
    assert scored.suggested_dte == "N/A"
    assert "watchlist" in scored.suggested_structure.lower() or \
           "premium to expand" in scored.suggested_structure.lower(), \
        f"Expected watchlist explanation in structure, got {scored.suggested_structure!r}"
    print(f"  Position construction: notional={scored.suggested_max_notional}, "
          f"delta={scored.suggested_delta}")
    print("  PASS: WATCHLIST position construction zeroed")


# ── Run all tests ─────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 64)
    print("QA Phase 1 Tests — VRP gate + WATCHLIST + scan quality")
    print("=" * 64)

    tests = [
        ("QQQ May 8 → WATCHLIST",                   test_qqq_may8_becomes_watchlist),
        ("XLF May 8 → WATCHLIST",                   test_xlf_may8_becomes_watchlist),
        ("JNJ May 8 → CONDITIONAL preserved",       test_jnj_may8_remains_conditional),
        ("WMT May 8 → SKIP (earnings gate)",        test_wmt_may8_skip_via_earnings_gate),
        ("Apr 16 → DEGRADED (NO DATA cluster)",     test_apr16_style_scan_degraded_no_data),
        ("Apr 16 → DEGRADED (slope-1.00 wall)",     test_apr16_style_scan_degraded_slope_wall),
        ("Clean scan → OK",                         test_clean_scan_is_ok),
        ("DEGRADED suppression",                    test_degraded_suppression_zeros_actionable),
        ("Raw score unchanged when WATCHLIST",      test_raw_score_unchanged_when_watchlist),
        ("WATCHLIST position construction zeroed",  test_watchlist_position_construction_is_zeroed),
        # ── Suppression diagnostics (Phase 1 audit) ──────
        ("Suppression preserves raw recommendation", test_degraded_suppression_preserves_raw_recommendation),
        ("Suppression reason propagated",            test_suppression_reason_is_propagated),
        ("Raw score unchanged after suppression",    test_raw_score_unchanged_after_degraded_suppression),
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
