"""US market trading-day calendar. Copied verbatim from backend/main.py:835-894
(`_us_market_holidays` / `_is_trading_day`) to avoid importing the backend. Pure datetime
math, no dependencies. Keep in sync if the backend's NYSE holiday rules ever change (rare).
"""
from __future__ import annotations

from datetime import date, timedelta


def us_market_holidays(year: int) -> set[date]:
    def _observe(d: date) -> date:
        if d.weekday() == 5:
            return d - timedelta(days=1)
        if d.weekday() == 6:
            return d + timedelta(days=1)
        return d

    def _nth_weekday(year: int, month: int, weekday: int, n: int) -> date:
        first = date(year, month, 1)
        offset = (weekday - first.weekday()) % 7
        return first + timedelta(days=offset + 7 * (n - 1))

    def _last_weekday(year: int, month: int, weekday: int) -> date:
        if month == 12:
            last_day = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            last_day = date(year, month + 1, 1) - timedelta(days=1)
        offset = (last_day.weekday() - weekday) % 7
        return last_day - timedelta(days=offset)

    def _easter(year: int) -> date:
        a = year % 19
        b, c = divmod(year, 100)
        d, e = divmod(b, 4)
        f = (b + 8) // 25
        g = (b - f + 1) // 3
        h = (19 * a + b - d - g + 15) % 30
        i, k = divmod(c, 4)
        ll = (32 + 2 * e + 2 * i - h - k) % 7
        m = (a + 11 * h + 22 * ll) // 451
        month = (h + ll - 7 * m + 114) // 31
        day = ((h + ll - 7 * m + 114) % 31) + 1
        return date(year, month, day)

    holidays = set()
    holidays.add(_observe(date(year, 1, 1)))        # New Year's Day
    holidays.add(_nth_weekday(year, 1, 0, 3))       # MLK Day
    holidays.add(_nth_weekday(year, 2, 0, 3))       # Presidents' Day
    holidays.add(_easter(year) - timedelta(days=2))  # Good Friday
    holidays.add(_last_weekday(year, 5, 0))         # Memorial Day
    holidays.add(_observe(date(year, 6, 19)))       # Juneteenth
    holidays.add(_observe(date(year, 7, 4)))        # Independence Day
    holidays.add(_nth_weekday(year, 9, 0, 1))       # Labor Day
    holidays.add(_nth_weekday(year, 11, 3, 4))      # Thanksgiving
    holidays.add(_observe(date(year, 12, 25)))      # Christmas
    return holidays


def is_trading_day(d: date) -> bool:
    if d.weekday() >= 5:
        return False
    return d not in us_market_holidays(d.year)


def trading_days_between(start: date, end: date) -> list[date]:
    """Trading days in (start, end] — exclusive of start, inclusive of end."""
    out = []
    cur = start + timedelta(days=1)
    while cur <= end:
        if is_trading_day(cur):
            out.append(cur)
        cur += timedelta(days=1)
    return out
