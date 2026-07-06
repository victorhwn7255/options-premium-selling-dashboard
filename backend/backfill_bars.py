"""
backfill_bars.py — one-time historical OHLC backfill for the v2 data substrate.

Phase A (silent). Populates `daily_bars` (33-ticker universe) and `index_daily`
(VIX family) from **yfinance**, which gives multi-year, multi-regime history for
free — a far less bull-biased seed for the forward-RV forecaster than the ~1yr
MarketData trial cap. Going-forward bars come from MarketData in the live scan
(source='marketdata'); this seeds source='yfinance'. The one seam at "now" is
absorbed by the per-ticker vbar demean in the forecaster.

Bars are stored with an integrity flag, never silently corrected: a bar failing
H≥max(O,C) / L≤min(O,C) / O>0 / |ln(C/prevC)|<0.5 is stored with quarantine=1 and
excluded from estimator reads.

Usage:
  python backfill_bars.py --dry-run                 # show plan, fetch nothing
  python backfill_bars.py --tickers SPY --period 3y # single-ticker test
  python backfill_bars.py --period 3y               # full backfill (default)
  python backfill_bars.py --resume                  # skip (ticker,date) already stored
"""

from __future__ import annotations

import argparse
import logging
import math
import sys
import time

import database as db
from config import NAKED_PUT_UNIVERSE

logger = logging.getLogger("backfill_bars")

# VIX family for index_daily. PUT (Cboe PutWrite) benchmark is deferred to
# Phase D (weekly Cboe CSV import) — MarketData indices are unentitled on the
# trial token and yfinance does not carry the PutWrite index cleanly.
INDEX_SYMBOLS = ["^VIX", "^VIX3M", "^VVIX"]

SOURCE = "yfinance"
MAX_ABS_LOG_RETURN = 0.5  # |ln(C/prevC)| ≥ this ⇒ integrity failure (split/data artifact)


def _bar_ok(o, h, l, c, prev_c) -> bool:
    """Bar-integrity check. Returns True if the bar is trustworthy."""
    if None in (o, h, l, c) or any(x != x for x in (o, h, l, c)):  # NaN-safe
        return False
    if not (o > 0 and h > 0 and l > 0 and c > 0):
        return False
    if h < max(o, c) - 1e-9 or l > min(o, c) + 1e-9:
        return False
    if prev_c and prev_c > 0 and abs(math.log(c / prev_c)) >= MAX_ABS_LOG_RETURN:
        return False
    return True


def _existing_dates(table: str, key_col: str, key: str) -> set[str]:
    conn = db.get_connection()
    rows = {r[0] for r in conn.execute(
        f"SELECT date FROM {table} WHERE {key_col} = ?", (key,))}
    conn.close()
    return rows


def _download(symbol: str, period: str):
    """yfinance download → list of (date, o, h, l, c, v) rows, oldest→newest."""
    import yfinance as yf
    df = yf.download(symbol, period=period, auto_adjust=True,
                     progress=False, threads=False)
    if df is None or df.empty:
        return []
    # yfinance returns MultiIndex (field, ticker) columns even for a single
    # symbol — flatten to plain field names so row lookups are scalars.
    if getattr(df.columns, "nlevels", 1) > 1:
        df.columns = df.columns.get_level_values(0)
    out = []
    for idx, row in df.iterrows():
        def _f(field):
            val = row.get(field)
            if val is None:
                return None
            try:
                f = float(val)
            except (TypeError, ValueError):
                return None
            return f if f == f else None  # NaN → None
        d = idx.date().isoformat()
        out.append((d, _f("Open"), _f("High"), _f("Low"), _f("Close"), _f("Volume")))
    return out


def backfill_ticker(ticker: str, period: str, resume: bool, dry_run: bool) -> dict:
    existing = _existing_dates("daily_bars", "ticker", ticker) if resume else set()
    if dry_run:
        return {"ticker": ticker, "planned": True, "already": len(existing)}
    raw = _download(ticker, period)
    rows, prev_c, quar = [], None, 0
    for d, o, h, l, c, v in raw:
        if resume and d in existing:
            prev_c = c if (c and c == c) else prev_c
            continue
        ok = _bar_ok(o, h, l, c, prev_c)
        if not ok:
            quar += 1
        rows.append((ticker, d, o, h, l, c, v, SOURCE, 1, 0 if ok else 1))
        if c and c == c:
            prev_c = c
    n = db.store_daily_bars(rows)
    return {"ticker": ticker, "stored": n, "quarantined": quar, "fetched": len(raw)}


def backfill_index(symbol: str, period: str, resume: bool, dry_run: bool) -> dict:
    existing = _existing_dates("index_daily", "symbol", symbol) if resume else set()
    if dry_run:
        return {"symbol": symbol, "planned": True, "already": len(existing)}
    raw = _download(symbol, period)
    rows = [(symbol, d, o, h, l, c) for d, o, h, l, c, _v in raw
            if not (resume and d in existing) and c is not None and c == c]
    n = db.store_index_bars(rows)
    return {"symbol": symbol, "stored": n, "fetched": len(raw)}


def main():
    parser = argparse.ArgumentParser(
        description="Backfill historical OHLC bars (yfinance) for the v2 data substrate.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--period", type=str, default="3y",
                        help="yfinance history period (default: 3y ≈ 750 trading days, multi-regime)")
    parser.add_argument("--tickers", type=str, default=None,
                        help="Comma-separated subset (default: all 33)")
    parser.add_argument("--resume", action="store_true",
                        help="Skip (ticker,date) rows already in daily_bars")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show the plan; fetch/write nothing")
    parser.add_argument("--no-index", action="store_true",
                        help="Skip the VIX-family index_daily backfill")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO,
                        format="%(message)s")

    if not args.dry_run:
        try:
            import yfinance  # noqa: F401
        except ImportError:
            print("ERROR: yfinance not installed. `pip install yfinance` (it is a "
                  "declared prod dependency; the dev env just needs it too).", file=sys.stderr)
            sys.exit(1)

    tickers = ([t.strip().upper() for t in args.tickers.split(",")]
               if args.tickers else list(NAKED_PUT_UNIVERSE.keys()))
    bad = [t for t in tickers if t not in NAKED_PUT_UNIVERSE]
    if bad:
        print(f"ERROR: unknown tickers {bad}", file=sys.stderr)
        sys.exit(1)

    print(f"Theta Harvest — v2 OHLC backfill (period={args.period}, "
          f"{len(tickers)} tickers{' +VIX' if not args.no_index else ''})"
          f"{' [DRY RUN]' if args.dry_run else ''}{' [RESUME]' if args.resume else ''}")

    for t in tickers:
        r = backfill_ticker(t, args.period, args.resume, args.dry_run)
        if args.dry_run:
            print(f"  {t:5s} plan (already stored: {r['already']})")
        else:
            print(f"  {t:5s} stored={r['stored']:4d} fetched={r['fetched']:4d} "
                  f"quarantined={r['quarantined']}")
            time.sleep(0.2)  # be polite to Yahoo

    if not args.no_index:
        for s in INDEX_SYMBOLS:
            r = backfill_index(s, args.period, args.resume, args.dry_run)
            if args.dry_run:
                print(f"  {s:7s} plan (already stored: {r['already']})")
            else:
                print(f"  {s:7s} stored={r['stored']:4d} fetched={r['fetched']:4d}")
                time.sleep(0.2)

    if not args.dry_run:
        print("\nCoverage report:")
        cov = db.get_bars_coverage()
        short = [t for t in tickers if cov.get(t, {}).get("count", 0) < 500]
        for t in tickers:
            c = cov.get(t, {})
            flag = "  ⚠ <500" if c.get("count", 0) < 500 else ""
            print(f"  {t:5s} {c.get('count', 0):4d} bars  {c.get('min','-')}→{c.get('max','-')}"
                  f"  quar={c.get('quarantined', 0)}{flag}")
        print(f"\n{'✅' if not short else '⚠'} {len(tickers)-len(short)}/{len(tickers)} "
              f"tickers ≥500 bars" + (f"; short: {short}" if short else ""))


if __name__ == "__main__":
    main()
