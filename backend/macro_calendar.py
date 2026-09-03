"""Scheduled macro-event calendar — the data behind gate G6 (index sleeve) and the X1/X3 replay.

FOMC decision days, CPI and NFP release dates are PUBLISHED schedules, not calendar arithmetic
(unlike `main._us_market_holidays`), so they live as static data in `macro_calendar.json` with a
source URL per block and get extended yearly. This module is pure (no DB, no network):

    next_event(as_of)            -> (kind, date, calendar_days_until) or None
    in_window(as_of, pre, post)  -> (gated, kind, days_until)   # G6's question
    is_stale(as_of, horizon)     -> True when no event lies within `horizon` days ahead — the
                                    maintainer alarm. G6 FAILS OPEN on a stale calendar (ADR-014):
                                    a stale file must never silently gate the whole index sleeve.

Windows are in CALENDAR days, like G1's `earnings_dte`.
"""
from __future__ import annotations

import json
from datetime import date, timedelta
from functools import lru_cache
from pathlib import Path

DEFAULT_PATH = Path(__file__).parent / "macro_calendar.json"
KINDS = ("FOMC", "CPI", "NFP")


@lru_cache(maxsize=4)
def _load_cached(path_str: str) -> dict:
    raw = json.loads(Path(path_str).read_text())
    out: dict[str, list[tuple[date, str]]] = {}
    for kind in KINDS:
        rows = raw.get(kind) or []
        out[kind] = sorted((date.fromisoformat(r["date"]), r.get("note", "")) for r in rows)
    out["meta"] = raw.get("meta", {})
    return out


def load(path: Path | str | None = None) -> dict:
    """{kind: sorted [(date, note), ...], "meta": {...}}."""
    return _load_cached(str(path or DEFAULT_PATH))


def events(kinds=None, path=None) -> list[tuple[date, str, str]]:
    """All events as (date, kind, note), sorted by date."""
    cal = load(path)
    kinds = tuple(kinds) if kinds else KINDS
    out = [(d, k, n) for k in kinds for d, n in cal.get(k, [])]
    return sorted(out)


def coverage(kinds=None, path=None) -> dict[str, tuple[date | None, date | None, int]]:
    cal = load(path)
    kinds = tuple(kinds) if kinds else KINDS
    return {k: ((cal[k][0][0], cal[k][-1][0], len(cal[k])) if cal.get(k) else (None, None, 0))
            for k in kinds}


def next_event(as_of: date, kinds=None, path=None) -> tuple[str, date, int] | None:
    """The first event on or after `as_of`: (kind, date, calendar days until) — or None."""
    for d, k, _ in events(kinds, path):
        if d >= as_of:
            return k, d, (d - as_of).days
    return None


def in_window(as_of: date, pre_days: int, post_days: int = 0, kinds=None,
              path=None) -> tuple[bool, str | None, int | None]:
    """G6: is `as_of` inside [event - pre_days, event + post_days] for any event?
    Returns (gated, kind, days_until) with days_until negative after the event."""
    for d, k, _ in events(kinds, path):
        delta = (d - as_of).days
        if -post_days <= delta <= pre_days:
            return True, k, delta
    return False, None, None


def is_stale(as_of: date, horizon_days: int = 60, kinds=None, path=None) -> bool:
    """True when the calendar has NO event within the next `horizon_days` — i.e. it needs
    extending. Per kind: any kind with no forward coverage makes the calendar stale."""
    cal = load(path)
    kinds = tuple(kinds) if kinds else KINDS
    limit = as_of + timedelta(days=horizon_days)
    for k in kinds:
        if not any(as_of <= d <= limit for d, _ in cal.get(k, [])):
            return True
    return False
