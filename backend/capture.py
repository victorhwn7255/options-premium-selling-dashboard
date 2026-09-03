"""Forward realized capture — spec E3 per ticker-day, the standing signal-quality metric (WS2a).

For every ticker-day t with an IV30 print, once 21 further sessions of bars exist:

    rv_fwd_21_cc   = close-to-close realized vol over t -> t+21 (annualized decimal, ddof=1;
                     the same convention as positions_api._hold_rv / trades.capture)
    rv_fwd_21      = GK+overnight realized vol over t+1 .. t+21 — the pooled forecaster's own
                     target (forecast.ForecastEngine.build_panel), so sigma_fwd can be graded
                     against what it was trained to predict
    capture_30d    = tc.realized_capture(IV30, rv_fwd_21_cc)["var_points"]
                     = (IV30^2 - RV^2) * 1e4   (spec E3; Module G names the column capture_30d)
    capture_30d_log

Advisory only: nothing here feeds a recommendation. Runs nightly after the v2 shadow step in
its own try/except (a failure never touches the v1 scan) and is idempotent — only rows with
capture_30d IS NULL are considered, and a row for date t is filled only when bars through t+21
exist (the exact gate; the calendar-day cutoff is just a cheap prefilter). Bounded per run.

CLI (on the box, one-off history backfill ~11k rows):
    python capture.py --backfill [--limit N] [--as-of YYYY-MM-DD] [--dry-run]
"""
from __future__ import annotations

import argparse
import logging
import math
from collections import defaultdict
from datetime import date, timedelta

import theta_core as tc
from database import get_bars, get_capture_candidates, store_daily_iv_v2

HOLD = tc.HOLD_SESSIONS                 # 21 sessions
PREFILTER_CALENDAR_DAYS = 29            # >= 21 sessions; bars availability is the real gate
DEFAULT_LIMIT = 2000                    # nightly bound (a normal night resolves ~33 rows)

log = logging.getLogger(__name__)


def forward_rv_cc(closes: list[float]) -> float | None:
    """Annualized close-to-close vol from HOLD+1 closes (t .. t+HOLD), ddof=1."""
    if len(closes) != HOLD + 1 or any((c is None or c <= 0) for c in closes):
        return None
    rets = [math.log(closes[i] / closes[i - 1]) for i in range(1, len(closes))]
    mean = sum(rets) / len(rets)
    var = sum((r - mean) ** 2 for r in rets) / (len(rets) - 1)
    return math.sqrt(var * tc.ANN)


def forward_rv_gk(window: list[dict], prev_close: float) -> float | None:
    """Annualized GK+overnight vol from the HOLD bars t+1 .. t+HOLD (prev_close = close at t)."""
    if len(window) != HOLD or not prev_close or prev_close <= 0:
        return None
    v_sum, prev = 0.0, prev_close
    for b in window:
        o, h, l, c = b.get("o"), b.get("h"), b.get("l"), b.get("c")
        if not all(x and x > 0 for x in (o, h, l, c)):
            return None
        v_sum += tc.daily_inputs(o, h, l, c, prev)["v"]
        prev = c
    return math.sqrt(max((tc.ANN / HOLD) * v_sum, 0.0))


def resolve_row(iv_pct: float, bars: list[dict], idx: int) -> dict | None:
    """Capture fields for the bar at `idx` (date t) if bars through t+HOLD exist, else None."""
    if iv_pct is None or iv_pct <= 0 or idx < 0 or idx + HOLD >= len(bars):
        return None
    closes = [bars[i].get("c") for i in range(idx, idx + HOLD + 1)]
    rv_cc = forward_rv_cc(closes)
    if rv_cc is None or rv_cc <= 0:
        return None
    rv_gk = forward_rv_gk(bars[idx + 1: idx + HOLD + 1], bars[idx].get("c"))
    cap = tc.realized_capture(iv_pct / 100.0, rv_cc)
    return {"rv_fwd_21_cc": round(rv_cc, 6), "rv_fwd_21": round(rv_gk, 6) if rv_gk is not None else None,
            "capture_30d": round(cap["var_points"], 4), "capture_30d_log": round(cap["log"], 6)}


def fill_resolved(as_of: date | None = None, limit: int = DEFAULT_LIMIT, dry_run: bool = False) -> dict:
    """Fill capture columns for every resolvable ticker-day (bounded). Returns counts."""
    as_of = as_of or date.today()
    cutoff = (as_of - timedelta(days=PREFILTER_CALENDAR_DAYS)).isoformat()
    cands = get_capture_candidates(cutoff, limit)
    by_ticker: dict[str, list[tuple]] = defaultdict(list)
    for tkr, d, iv in cands:
        by_ticker[tkr].append((d, iv))
    stats = {"as_of": as_of.isoformat(), "candidates": len(cands), "resolved": 0,
             "unresolved": 0, "tickers": len(by_ticker), "dry_run": dry_run}
    for tkr, rows in by_ticker.items():
        bars = get_bars(tkr)                       # chronological, quarantined bars excluded
        pos = {b["date"]: i for i, b in enumerate(bars)}
        for d, iv in rows:
            i = pos.get(d)
            out = resolve_row(iv, bars, i) if i is not None else None
            if out is None:
                stats["unresolved"] += 1
                continue
            if dry_run:
                stats["resolved"] += 1
                continue
            n = store_daily_iv_v2(tkr, as_of=d, capture_resolved_at=as_of.isoformat(), **out)
            stats["resolved"] += int(n)
    return stats


def _main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Forward realized capture (spec E3) fill.")
    ap.add_argument("--backfill", action="store_true", help="raise the per-run bound for a history backfill")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--as-of", type=str, default=None)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--verbose", action="store_true")
    a = ap.parse_args(argv)
    logging.basicConfig(level=logging.DEBUG if a.verbose else logging.INFO, format="%(message)s")
    limit = a.limit if a.limit is not None else (50_000 if a.backfill else DEFAULT_LIMIT)
    as_of = date.fromisoformat(a.as_of) if a.as_of else None
    stats = fill_resolved(as_of=as_of, limit=limit, dry_run=a.dry_run)
    print(stats)
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
