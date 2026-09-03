"""Macro calendar (WS3 data / WS1 prerequisite) — coverage, window arithmetic, staleness.

Run:  cd backend && python -m pytest test_macro_calendar.py -v
"""
from __future__ import annotations

from datetime import date

import macro_calendar as mc


def test_coverage_and_known_dates():
    cov = mc.coverage()
    assert cov["FOMC"][0] == date(2016, 1, 27) and cov["FOMC"][1] == date(2027, 12, 8)
    # 8 scheduled meetings/yr × 12 yrs, except 2020 (7 scheduled — March was replaced by the
    # 03-15 emergency meeting) + 3 unscheduled (2019-10-04, 2020-03-02, 2020-03-15) = 98.
    assert cov["FOMC"][2] == 98
    assert cov["CPI"][0] == date(2024, 1, 15) and cov["NFP"][1] == date(2026, 12, 4)
    fomc = dict((d, n) for d, n in mc.load()["FOMC"])
    assert fomc[date(2020, 3, 15)] == "unscheduled" and fomc[date(2019, 10, 4)] == "unscheduled"
    assert date(2018, 2, 5) not in fomc                      # sanity: Volmageddon was not an FOMC day


def test_next_event_and_window():
    assert mc.next_event(date(2026, 9, 3)) == ("NFP", date(2026, 9, 4), 1)
    assert mc.next_event(date(2026, 9, 5), kinds=("FOMC",)) == ("FOMC", date(2026, 9, 16), 11)
    # G6 window: 3 calendar days before through the event day (post_days=0).
    assert mc.in_window(date(2026, 9, 13), 3, 0, kinds=("FOMC",)) == (True, "FOMC", 3)
    assert mc.in_window(date(2026, 9, 16), 3, 0, kinds=("FOMC",)) == (True, "FOMC", 0)
    assert mc.in_window(date(2026, 9, 17), 3, 0, kinds=("FOMC",)) == (False, None, None)
    assert mc.in_window(date(2026, 9, 12), 3, 0, kinds=("FOMC",)) == (False, None, None)
    assert mc.in_window(date(2026, 9, 17), 3, 1, kinds=("FOMC",)) == (True, "FOMC", -1)


def test_staleness_alarm():
    assert mc.is_stale(date(2026, 9, 3)) is False
    assert mc.is_stale(date(2027, 6, 1), kinds=("FOMC",)) is False          # FOMC covers 2027
    assert mc.is_stale(date(2026, 12, 20), kinds=("CPI",)) is True           # no 2027 CPI dates yet
    assert mc.is_stale(date(2030, 1, 1)) is True
