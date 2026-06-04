"""Tests for stat-pack, parser, writer, and trading calendar.

Run from repo root:  python3 automation/tests/test_core.py
"""
from __future__ import annotations

import json
import shutil
import sys
import tempfile
from datetime import date
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from automation.render.statpack import compute_statpack  # noqa: E402
from automation.history import parser, writer  # noqa: E402
from automation.sources import trading_calendar as cal  # noqa: E402

FIX = REPO / "automation" / "fixtures"
METRICS = REPO / "history" / "metrics-logs.md"
BRIEF = REPO / "history" / "daily-briefings.md"


def _eq(label, got, exp):
    assert got == exp, f"{label}: got {got!r}, expected {exp!r}"
    print(f"  PASS  {label} = {got!r}")


def test_statpack():
    raw = json.loads((FIX / "np_2026-06-03.json").read_text())["tickers"]
    prior = parser.parse_np_table(METRICS, "2026-06-02")
    sp = compute_statpack(raw, prior)
    _eq("statpack.regime_label", sp["regime_label"], "THE PLAYOFFS")
    _eq("statpack.tradeable_str", sp["tradeable_str"], "3S / 3C + 1W")
    _eq("statpack.avg_vrp_str", sp["avg_vrp_str"], "+2.7")
    _eq("statpack.aggregates.sell/cond/watch",
        (sp["aggregates"]["sell"], sp["aggregates"]["conditional"], sp["aggregates"]["watchlist"]),
        (3, 3, 1))
    qqq = next(d for d in sp["day_over_day"] if d["ticker"] == "QQQ")
    _eq("statpack.dod.QQQ", (qqq["prev"], qqq["today"], qqq["delta"]), (62, 71, 9))


def test_parser():
    _eq("parser.last_logged_date", parser.last_logged_date(METRICS), date(2026, 6, 3))
    _eq("parser.has_entry(6/3)", parser.has_entry(METRICS, "2026-06-03"), True)
    _eq("parser.has_entry(9999)", parser.has_entry(METRICS, "9999-01-01"), False)
    np62 = parser.parse_np_table(METRICS, "2026-06-02")
    _eq("parser.parse_np_table QQQ score", np62["QQQ"]["score"], 62)
    np63 = parser.parse_np_table(METRICS, "2026-06-03")
    _eq("parser.parse_np_table XLB iv (N/A->None, 6/3)", np63["XLB"]["iv"], None)
    headings = parser.latest_entries(METRICS, 7).count("\n## ") + 1
    _eq("parser.latest_entries top-7 heading count", headings, 7)


def test_writer():
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td) / "metrics-logs.md"
        shutil.copy(METRICS, tmp)
        block = "## 2026-06-04 (Thursday)\n\n| Ticker | Score |\n|---|---|\n| TST | 99 |"
        writer.insert_entry(tmp, "2026-06-04", block)
        text = tmp.read_text()
        # New entry is now the top dated entry, directly above 6/3, separators intact.
        assert parser.last_logged_date(tmp) == date(2026, 6, 4), "new entry not at top"
        assert "## 2026-06-04 (Thursday)\n\n| Ticker | Score |\n|---|---|\n| TST | 99 |\n\n---\n\n## 2026-06-03" in text, "splice/separator wrong"
        print("  PASS  writer.insert_entry top placement + separators")
        # Idempotent
        try:
            writer.insert_entry(tmp, "2026-06-04", block)
            raise AssertionError("expected AlreadyLogged")
        except writer.AlreadyLogged:
            print("  PASS  writer idempotency (AlreadyLogged)")
        # No temp leftovers
        leftovers = [p for p in Path(td).iterdir() if p.name.startswith(".metrics-logs.md.")]
        assert not leftovers, f"temp files left: {leftovers}"
        print("  PASS  writer atomic (no temp leftover)")


def test_calendar():
    _eq("cal.is_trading_day(2026-06-03 Wed)", cal.is_trading_day(date(2026, 6, 3)), True)
    _eq("cal.is_trading_day(2026-05-25 Memorial Day)", cal.is_trading_day(date(2026, 5, 25)), False)
    _eq("cal.is_trading_day(2026-06-06 Sat)", cal.is_trading_day(date(2026, 6, 6)), False)
    # 6/1..6/3 inclusive of end, exclusive of start (5/29) -> Mon/Tue/Wed
    days = cal.trading_days_between(date(2026, 5, 29), date(2026, 6, 3))
    _eq("cal.trading_days_between(5/29,6/3)", [d.isoformat() for d in days],
        ["2026-06-01", "2026-06-02", "2026-06-03"])


if __name__ == "__main__":
    print("Core module tests:")
    test_statpack()
    test_parser()
    test_writer()
    test_calendar()
    print("All core tests passed.")
