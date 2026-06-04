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


if __name__ == "__main__":
    print("Golden-fixture renderer tests:")
    test_renderers_golden()
    print("All renderer golden tests passed.")
