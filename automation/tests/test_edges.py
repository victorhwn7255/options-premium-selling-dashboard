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
               test_regime_precedence, test_first_day_no_deltas, test_avg_vrp_js_rounding_tie]:
        fn()
    print("All edge-case tests passed.")
