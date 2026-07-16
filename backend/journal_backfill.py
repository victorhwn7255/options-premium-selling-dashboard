"""Retroactive position-marks backfill from the captured quotes CSVs.

For a position journaled after the fact (entry_date in the past), reconstruct its
daily P&L curve from `data/quotes/{ticker}.csv` — the per-scan chain capture that
has run since 2026-02-11. Trades older than that get economics + settlement only.

Marks are written with mark_source='csv_backfill'; delta stays NULL (the CSVs
don't carry greeks — see the J1 plan deviation note). earnings_dte joins from
daily_iv where available. Idempotent: (position_id, date) upserts.

Usage (from backend/):
    python3 journal_backfill.py <position_id> [--dry-run]
"""
from __future__ import annotations

import argparse
import csv
import sys
from datetime import date
from pathlib import Path

from database import get_connection, get_position, store_position_mark
from positions_api import capture_pct, net_close_debit, position_pnl

QUOTES_DIR = Path(__file__).parent / "data" / "quotes"


def _daily_quotes(ticker: str, expiry: str, strike: float,
                  start: str, end: str) -> dict[str, dict]:
    """{date: {bid, ask, mid, underlying_price}} for one contract over a window."""
    path = QUOTES_DIR / f"{ticker}.csv"
    out: dict[str, dict] = {}
    if not path.exists():
        return out
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            d = row.get("date") or ""
            if not (start <= d <= end):
                continue
            if row.get("expiration") != expiry or row.get("side") != "put":
                continue
            if abs(float(row.get("strike") or 0) - strike) >= 1e-6:
                continue

            def _num(key):
                v = row.get(key)
                return float(v) if v not in (None, "") else None
            out[d] = {"bid": _num("bid"), "ask": _num("ask"), "mid": _num("mid"),
                      "underlying_price": _num("underlying_price")}
    return out


def _earnings_by_date(ticker: str, start: str, end: str) -> dict[str, int]:
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT date, earnings_dte FROM daily_iv "
            "WHERE ticker = ? AND date BETWEEN ? AND ? AND earnings_dte IS NOT NULL",
            (ticker, start, end)).fetchall()
        return {r[0]: r[1] for r in rows}
    finally:
        conn.close()


def backfill_position_marks(position_id: int, dry_run: bool = False) -> int:
    pos = get_position(position_id)
    if not pos:
        raise SystemExit(f"position {position_id} not found")
    start = pos["entry_date"]
    end = pos.get("close_date") or min(pos.get("expiry") or date.today().isoformat(),
                                       date.today().isoformat())
    print(f"[backfill] #{position_id} {pos['ticker']} {pos['structure']} "
          f"{pos['short_strike']}/{pos.get('long_strike') or '—'} exp {pos['expiry']} "
          f"window {start} → {end}")

    short_q = _daily_quotes(pos["ticker"], pos["expiry"], pos["short_strike"], start, end)
    long_q = (_daily_quotes(pos["ticker"], pos["expiry"], pos["long_strike"], start, end)
              if pos.get("long_strike") else {})
    earn = _earnings_by_date(pos["ticker"], start, end)
    if not short_q:
        print("[backfill] no captured quotes in window — nothing to write "
              "(capture began 2026-02-11)")
        return 0

    written = 0
    for d in sorted(short_q):
        sq = short_q[d]
        lq = long_q.get(d) if pos.get("long_strike") else None
        net = net_close_debit(sq.get("mid"), (lq or {}).get("mid") if lq else None,
                              pos["structure"])
        if net is None:
            continue
        dte = (date.fromisoformat(pos["expiry"]) - date.fromisoformat(d)).days
        if dry_run:
            print(f"  (dry) {d}: mid {net} pnl "
                  f"{position_pnl(pos['entry_credit'], net, pos['contracts'])}")
        else:
            store_position_mark(
                position_id, d, underlying_close=sq.get("underlying_price"),
                option_bid=sq.get("bid"), option_ask=sq.get("ask"), option_mid=net,
                short_delta=None,
                unrealized_pnl=position_pnl(pos["entry_credit"], net, pos["contracts"]),
                capture_pct=capture_pct(pos["entry_credit"], net),
                dte=dte, earnings_dte=earn.get(d), mark_source="csv_backfill")
        written += 1
    print(f"[backfill] {'planned' if dry_run else 'wrote'} {written} marks")
    return written


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("position_id", type=int)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    sys.exit(0 if backfill_position_marks(args.position_id, args.dry_run) >= 0 else 1)
