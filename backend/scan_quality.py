"""
Scan quality detection — flags degraded scans before they produce misleading recommendations.

Two triggers (per references/dashboard-behavior-qa-report.md §5.6, §7.3):

  1. NO DATA count > NO_DATA_THRESHOLD
     Too many tickers without reliable IV — aggregate metrics become meaningless
     and the regime banner reads from a degraded base.

  2. >SLOPE_WALL_THRESHOLD of tickers at term_slope ≈ 1.00
     Indicates degenerate term structure (the "1.00 wall" pattern from the
     2026-04-16 incident: 13/33 NO DATA + 16/20 of remaining at slope=1.00).

When DEGRADED, callers are expected to call `suppress_actionable()` to downgrade
SELL / CONDITIONAL / WATCHLIST recommendations to NO EDGE so the dashboard
doesn't surface tradeable signals computed from unreliable inputs.
"""

from typing import Optional, Sequence


SLOPE_WALL_TOLERANCE = 0.001   # term_slope within ±0.001 of 1.00 counts as "wall"
SLOPE_WALL_THRESHOLD = 0.25    # >25% of tickers at the wall → degraded
NO_DATA_THRESHOLD = 4          # > this many NO DATA rows → degraded


def compute_scan_quality(results: Sequence) -> tuple[str, Optional[str]]:
    """
    Return ('OK', None) or ('DEGRADED', reason).

    Each `result` must expose `.recommendation: str` and `.term_slope: float | None`.
    """
    total = len(results)
    if total == 0:
        return "OK", None

    # NO DATA is counted from `recommendation == "NO DATA"`, not from raw
    # `iv is None`. This relies on scorer.py's early-return path, which sets
    # recommendation = "NO DATA" whenever iv_current is None. Counting from the
    # normalized scoring output keeps fresh and cached responses consistent and
    # avoids miscounting earnings-gated rows whose underlying IV is also None.
    no_data_count = sum(1 for r in results if r.recommendation == "NO DATA")
    if no_data_count > NO_DATA_THRESHOLD:
        return (
            "DEGRADED",
            f"{no_data_count} of {total} tickers returned NO DATA",
        )

    slope_wall_count = sum(
        1
        for r in results
        if r.term_slope is not None
        and abs(r.term_slope - 1.0) < SLOPE_WALL_TOLERANCE
    )
    slope_wall_pct = slope_wall_count / total
    if slope_wall_pct > SLOPE_WALL_THRESHOLD:
        return (
            "DEGRADED",
            f"{slope_wall_count} of {total} tickers show term slope ≈ 1.00 "
            f"({slope_wall_pct:.0%}) — likely degenerate term structure",
        )

    return "OK", None


def suppress_actionable(results, reason: str) -> int:
    """
    Mutate results in-place: any ticker with SELL PREMIUM / CONDITIONAL / WATCHLIST
    is downgraded to NO EDGE for trading safety, but its pre-suppression
    diagnostic context is preserved on the row so the audit trail survives:

        suppressed_by_scan_quality       True for downgraded rows
        pre_suppression_recommendation   Original "SELL PREMIUM" / "CONDITIONAL" / "WATCHLIST"
        pre_suppression_score            Copy of signal_score (which is itself unchanged)
        scan_quality_suppression_reason  The reason string from compute_scan_quality()

    Preserved (NOT mutated):
        signal_score                     Raw scoring formula output
        regime                           NORMAL / CAUTION / DANGER classification
        vrp / vrp_ratio / iv_*           All input metrics

    Untouched action states:
        AVOID                            Already non-tradeable
        NO DATA                          Already non-tradeable
        NO EDGE                          Genuinely below threshold; not a suppression
        SKIP (frontend-only)             Frontend earnings-gate state, never reaches backend

    Returns number of rows suppressed.
    """
    actionable = {"SELL PREMIUM", "CONDITIONAL", "WATCHLIST"}
    suppressed = 0
    for r in results:
        if r.recommendation in actionable:
            # Capture diagnostic context BEFORE downgrade.
            r.pre_suppression_recommendation = r.recommendation
            r.pre_suppression_score = r.signal_score
            r.suppressed_by_scan_quality = True
            r.scan_quality_suppression_reason = reason

            # Downgrade displayed recommendation + zero Position Construction.
            # signal_score, regime, and all metric fields are intentionally untouched.
            r.recommendation = "NO EDGE"
            r.flags.append(f"Scan quality degraded — {reason}")
            r.suggested_delta = "N/A"
            r.suggested_structure = "Scan quality degraded — no recommendations"
            r.suggested_dte = "N/A"
            r.suggested_max_notional = "0%"
            suppressed += 1
    return suppressed
