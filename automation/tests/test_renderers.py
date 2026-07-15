"""Golden-fixture byte-match tests for the deterministic renderers.

Run from repo root:  python3 automation/tests/test_renderers.py
(also works under pytest)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from automation.render.np_table import render_np_table  # noqa: E402
from automation.render.cps_snapshot import render_cps_snapshot  # noqa: E402
from automation.render.shadow_table import (  # noqa: E402
    compute_day_flips, render_shadow_snapshot, shadow_summary_line)

FIX = REPO / "automation" / "fixtures"


def _load(p: Path) -> str:
    return p.read_text().rstrip("\n")


def check_np(date: str) -> None:
    raw = json.loads((FIX / f"np_{date}.json").read_text())
    expected = _load(FIX / "expected" / f"np_{date}.md")
    got = render_np_table(raw["tickers"])
    _assert_equal(f"NP {date}", expected, got)


def check_cps(date: str) -> None:
    raw = json.loads((FIX / f"cps_{date}.json").read_text())
    expected = _load(FIX / "expected" / f"cps_{date}.md")
    got = render_cps_snapshot(raw)
    _assert_equal(f"CPS {date}", expected, got)


def check_shadow(date: str) -> None:
    # Fixture is {"rows": [...], "summary": {...}, "earnings": {...}, "prev_rows": [...]};
    # a representative slice of a day's rows + the rolling 10-day summary (the live shape:
    # window summary above the day's divergences), plus the earnings map (from the same
    # day's NP payload) and the prior day's rows (for the day-flips churn segment).
    raw = json.loads((FIX / f"shadow_{date}.json").read_text())
    expected = _load(FIX / "expected" / f"shadow_{date}.md")
    got = render_shadow_snapshot(raw["rows"], raw["summary"],
                                 earnings_by_ticker=raw.get("earnings"),
                                 flips=compute_day_flips(raw["rows"], raw.get("prev_rows")))
    _assert_equal(f"SHADOW {date}", expected, got)


def check_shadow_edges() -> None:
    """day-flips omission + earnings fallbacks: no prior day -> no segment (pre-2026-07-15
    format); no earnings map -> ETF/TBD cells; the summary line stays otherwise identical."""
    raw = json.loads((FIX / "shadow_2026-06-03.json").read_text())
    assert compute_day_flips(raw["rows"], None) is None, "no prev day must yield None"
    assert compute_day_flips(raw["rows"], []) is None, "empty prev day must yield None"
    line = shadow_summary_line(raw["summary"], None)
    assert "day-flips" not in line, "flips=None must omit the segment"
    assert line == shadow_summary_line(raw["summary"], compute_day_flips(raw["rows"], None)), \
        "line must be stable through the None path"
    no_map = render_shadow_snapshot(raw["rows"], raw["summary"])
    assert "| NKE | NO EDGE | NORMAL | TBD |" in no_map, "missing earnings map must render TBD"
    assert "| QQQ | SELL PREMIUM | NORMAL | ETF |" in no_map, "ETF rows must render ETF"
    print("  PASS  SHADOW edges (day-flips omission, earnings fallbacks)")


def _assert_equal(label: str, expected: str, got: str) -> None:
    if expected == got:
        print(f"  PASS  {label}")
        return
    print(f"  FAIL  {label}")
    exp_lines, got_lines = expected.splitlines(), got.splitlines()
    for i in range(max(len(exp_lines), len(got_lines))):
        e = exp_lines[i] if i < len(exp_lines) else "<missing>"
        g = got_lines[i] if i < len(got_lines) else "<missing>"
        if e != g:
            print(f"    line {i}:")
            print(f"      expected: {e!r}")
            print(f"      got:      {g!r}")
    raise AssertionError(label)


def test_renderers_golden():
    for date in ["2026-05-27", "2026-05-28", "2026-05-29", "2026-06-01", "2026-06-02", "2026-06-03"]:
        check_np(date)
        check_cps(date)
    check_shadow("2026-06-03")
    check_shadow_edges()


if __name__ == "__main__":
    print("Golden-fixture renderer tests:")
    test_renderers_golden()
    print("All renderer golden tests passed.")
