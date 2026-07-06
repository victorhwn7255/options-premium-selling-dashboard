"""Edge-case tests for paths the 6 days of real fixtures don't exercise.

Run from repo root:  python3 automation/tests/test_edges.py
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from automation.render.np_table import render_np_table  # noqa: E402
from automation.render.cps_snapshot import render_cps_snapshot  # noqa: E402
from automation.render.shadow_table import render_shadow_snapshot, shadow_summary_line  # noqa: E402
from automation.render.statpack import compute_statpack  # noqa: E402


def _t(ticker, score, rec, regime="NORMAL", vrp=1.0, slope=0.9, accel=0.9,
       earnings_dte=None, is_etf=True, iv=20.0, ivpct=50.0, rv30=15.0, skew=1.0,
       theta=-0.3, vega=0.5):
    return {
        "ticker": ticker, "signal_score": score, "recommendation": rec, "regime": regime,
        "iv_current": iv, "iv_percentile": ivpct, "rv30": rv30, "vrp": vrp,
        "term_slope": slope, "rv_acceleration": accel, "skew_25d": skew,
        "earnings_dte": earnings_dte, "is_etf": is_etf, "theta": theta, "vega": vega,
    }


def _ok(label, cond):
    assert cond, f"FAIL {label}"
    print(f"  PASS  {label}")


def test_earnings_gate_skip():
    tickers = [
        _t("AAA", 80, "SELL PREMIUM", is_etf=True),
        _t("BBB", 70, "SELL PREMIUM", is_etf=False, earnings_dte=5),  # gated
    ]
    out = render_np_table(tickers)
    lines = out.splitlines()
    # gated row sinks to bottom, score 0, Regime cell = reason, Earnings cell = "5d"
    _ok("skip row sorts to bottom", lines[-1].startswith("| BBB |"))
    _ok("skip score is 0", "| BBB | 0 |" in lines[-1])
    _ok("skip Earnings cell '5d'", "| 5d |" in lines[-1])
    _ok("skip Regime cell is reason", lines[-1].rstrip("|").rstrip().endswith("Earnings in 5d"))


def test_cps_empty_candidates():
    cps = {
        "rejection_summary": {"checked": 11, "actionable": 0, "rejected_by_base_gate": 8,
                              "rejected_by_construction": 3, "rejected_by_execution": 0,
                              "rejected_by_overlay": 0, "rejected_by_confirmation": 0},
        "regime_overlay": {"status": "NORMAL", "vix": 15.0, "vix3m": 18.0, "vvix": 90.0,
                           "vix_backwardation": False, "warnings": []},
        "candidates": [],
    }
    out = render_cps_snapshot(cps)
    _ok("empty CPS = 2 lines (no table)", len(out.splitlines()) == 2)
    _ok("empty CPS scan line", out.startswith("**Scan summary:** Checked 11 / 0 actionable"))
    _ok("empty CPS overlay contango", out.splitlines()[1].endswith("— NORMAL, Contango"))


def test_cps_unknown_overlay():
    cps = {
        "rejection_summary": None,
        "regime_overlay": {"status": "UNKNOWN", "vix": None, "vix3m": None, "vvix": None,
                           "vix_backwardation": None, "warnings": ["data unavailable"]},
        "candidates": [],
    }
    out = render_cps_snapshot(cps)
    _ok("unknown scan summary", out.splitlines()[0] == "**Scan summary:** (unavailable)")
    _ok("unknown overlay dashes + term —",
        out.splitlines()[1] == "**Overlay:** VIX — / VIX3M — / VVIX — — UNKNOWN, —")


def test_regime_precedence():
    # OFF SEASON: >40% DANGER
    off = [_t(f"D{i}", 30, "NO EDGE", regime="DANGER") for i in range(3)] + \
          [_t(f"N{i}", 30, "NO EDGE", regime="NORMAL") for i in range(2)]
    _ok("OFF SEASON (>40% danger)", compute_statpack(off)["regime_label"] == "OFF SEASON")
    # REGULAR SEASON: >25% stress (DANGER+CAUTION), <=40% danger
    reg = [_t("C1", 30, "NO EDGE", regime="CAUTION"), _t("C2", 30, "NO EDGE", regime="CAUTION"),
           _t("N1", 30, "NO EDGE"), _t("N2", 30, "NO EDGE")]
    _ok("REGULAR SEASON (>25% stress)", compute_statpack(reg)["regime_label"] == "REGULAR SEASON")
    # THE FINALS: avgVRP>8 AND avgSlope<0.90, low stress
    fin = [_t(f"F{i}", 30, "NO EDGE", vrp=10.0, slope=0.80) for i in range(4)]
    _ok("THE FINALS (vrp>8 & slope<0.90)", compute_statpack(fin)["regime_label"] == "THE FINALS")
    # THE PLAYOFFS default
    play = [_t(f"P{i}", 30, "NO EDGE", vrp=2.0, slope=0.95) for i in range(4)]
    _ok("THE PLAYOFFS (default)", compute_statpack(play)["regime_label"] == "THE PLAYOFFS")


def test_first_day_no_deltas():
    sp = compute_statpack([_t("AAA", 50, "CONDITIONAL")], prior_np=None)
    _ok("first-day day_over_day empty", sp["day_over_day"] == [])


def _srow(ticker, div="AGREE", elig=1, gate="WARM", **kw):
    r = {"ticker": ticker, "is_etf": 1, "v1_action": "NO EDGE", "v1_regime": "NORMAL",
         "v2_eligible": elig, "v2_gate_state": gate, "divergence_class": div, "v2_warm": 1,
         "sigma_fwd": 0.2, "fvrp_ratio": 1.1, "fvrp_z": 0.3, "slope_1m3m": 0.91, "accel_dn": 0.98}
    r.update(kw)
    return r


def test_shadow_empty_rows():
    # No divergence rows at all -> just the summary line, no table.
    out = render_shadow_snapshot([], {"n_ticker_days": 0, "divergence_counts": {},
                                      "index_gating_rate_v1": None, "index_gating_rate_v2": None,
                                      "oscillation_v1": None, "oscillation_v2": None,
                                      "warm_coverage": None})
    _ok("empty shadow = 1 line (no table)", len(out.splitlines()) == 1)
    _ok("empty shadow summary line", out.startswith("**Shadow summary:** Checked 0 / 0 agree"))
    _ok("None rates render as em dash",
        "index-gating v1 — vs v2 — | oscillation v1 — vs v2 — | warm —" in out)


def test_shadow_none_summary():
    _ok("None summary -> (unavailable)", shadow_summary_line(None) == "**Shadow summary:** (unavailable)")
    _ok("empty summary -> (unavailable)", shadow_summary_line({}) == "**Shadow summary:** (unavailable)")


def test_shadow_all_agree_and_sort():
    # all-AGREE (no decision-changing rows) still renders a table, sorted by ticker.
    rows = [_srow("SPY"), _srow("AAA"), _srow("QQQ")]
    out = render_shadow_snapshot(rows, {"n_ticker_days": 3, "divergence_counts": {"AGREE": 3},
                                        "index_gating_rate_v1": 0.0, "index_gating_rate_v2": 0.0,
                                        "oscillation_v1": 0.0, "oscillation_v2": 0.0,
                                        "warm_coverage": 1.0})
    body = out.splitlines()[4:]  # rows after summary(0) + blank(1) + header(2) + sep(3)
    _ok("all-AGREE sorted by ticker", [r.split("|")[1].strip() for r in body] == ["AAA", "QQQ", "SPY"])
    _ok("all-AGREE 3 agree line", "Checked 3 / 3 agree / 0 V2_STRICTER" in out)
    _ok("0% rates render", "index-gating v1 0% vs v2 0% | oscillation v1 0.00 vs v2 0.00 | warm 100%" in out)


def test_shadow_decision_changing_first():
    # V2_STRICTER, then V2_LOOSER, then everything else — regardless of ticker order.
    rows = [_srow("ZZZ", div="AGREE"), _srow("AAA", div="V2_LOOSER", elig=1),
            _srow("MMM", div="V2_STRICTER", elig=0), _srow("BBB", div="STATE_MISMATCH")]
    out = render_shadow_snapshot(rows, None)  # None summary -> (unavailable) header, table still renders
    order = [r.split("|")[1].strip() for r in out.splitlines()[4:]]
    _ok("V2_STRICTER first, then V2_LOOSER, then rest by ticker", order == ["MMM", "AAA", "BBB", "ZZZ"])
    _ok("None summary header still valid", out.startswith("**Shadow summary:** (unavailable)"))


def test_shadow_none_numeric_cells():
    # A NODATA_SKEW row with all-None drivers -> every numeric cell is an em dash.
    row = _srow("XLB", div="NODATA_SKEW", elig=0, gate="NODATA", v2_eligible=None,
                sigma_fwd=None, fvrp_ratio=None, fvrp_z=None, slope_1m3m=None, accel_dn=None)
    out = render_shadow_snapshot([row], None)
    last = out.splitlines()[-1]
    _ok("None eligible -> em dash", "| XLB | NO EDGE | NORMAL | — | NODATA | NODATA_SKEW |" in last)
    _ok("None drivers -> em dashes", last.endswith("| — | — | — | — | — |"))


def test_avg_vrp_js_rounding_tie():
    # eligible mean exactly 2.25 -> JS toFixed(1) = "2.3" (banker's would give 2.2)
    tied = [_t("A", 30, "NO EDGE", vrp=2.0), _t("B", 30, "NO EDGE", vrp=2.5)]
    _ok("avg_vrp tie rounds half-up (+2.3)", compute_statpack(tied)["avg_vrp_str"] == "+2.3")
    # negative mean keeps minus sign, no plus
    neg = [_t("A", 30, "NO EDGE", vrp=-3.7), _t("B", 30, "NO EDGE", vrp=-3.7)]
    _ok("avg_vrp negative (-3.7)", compute_statpack(neg)["avg_vrp_str"] == "-3.7")


if __name__ == "__main__":
    print("Edge-case tests:")
    for fn in [test_earnings_gate_skip, test_cps_empty_candidates, test_cps_unknown_overlay,
               test_regime_precedence, test_first_day_no_deltas, test_avg_vrp_js_rounding_tie,
               test_shadow_empty_rows, test_shadow_none_summary, test_shadow_all_agree_and_sort,
               test_shadow_decision_changing_first, test_shadow_none_numeric_cells]:
        fn()
    print("All edge-case tests passed.")
