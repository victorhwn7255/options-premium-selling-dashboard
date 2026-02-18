"""
Repair script for stock-split-corrupted RV30/VRP values.

Stock splits (e.g. NFLX 10-for-1 on Nov 17 2025) can leave stale
unadjusted close prices in the daily_iv table, producing absurd RV30
spikes (e.g. 657 instead of ~30). The scan pipeline now fetches
adjusted bars, so new data is fine — this script fixes the historical
rows that were computed from unadjusted bars.

What it does:
  1. Fetches fresh adjusted daily bars from MarketData.app
  2. For each date in daily_iv, recomputes rv30 from the adjusted bars
  3. Recomputes vrp = atm_iv - rv30 (atm_iv is OCC-adjusted, so it's fine)
  4. Updates daily_iv rows in-place
  5. Rewrites the daily CSV with corrected spot/rv30/vrp values

Usage:
    python repair_rv.py --tickers NFLX              # Fix one ticker
    python repair_rv.py --tickers NFLX,AMZN         # Fix multiple
    python repair_rv.py --all                        # Fix entire universe
    python repair_rv.py --tickers NFLX --dry-run    # Preview without writing
"""

import os
import sys
import csv
import math
import argparse
import asyncio
import logging
from datetime import date, timedelta
from pathlib import Path

import numpy as np

from backfill import BackfillClient, compute_rv30_from_bars
from database import get_connection, init_db
from csv_store import DATA_DIR, DAILY_HEADER
from main import UNIVERSE
from marketdata_client import DailyBar

logger = logging.getLogger("repair_rv")

# How many extra calendar days to fetch before the earliest daily_iv date
# so we have enough bars for RV30 computation (need 31 bars prior).
LOOKBACK_BUFFER_DAYS = 80

# A single-day |log_return| above this threshold signals a stock split.
# ln(1.5) ~ 0.405. We use 0.5 (~65% move) to catch 2:1 splits where the
# API's adjusted prices aren't perfectly 2.0x (e.g. XLE: 90.35 -> 45.77).
SPLIT_LOG_RETURN_THRESHOLD = 0.5


def detect_and_adjust_splits(bars: list[DailyBar]) -> list[DailyBar]:
    """
    Detect stock splits in bar data and adjust prices to the most recent scale.

    The MarketData.app API sometimes returns unadjusted bars despite
    adjusted=true. This function finds single-day price jumps that look
    like splits (e.g. 10:1 → close drops from $1100 to $110) and adjusts
    all bars before the split so the entire series is in the post-split scale.

    Works for forward splits (10:1, 4:1, etc.) and reverse splits.
    """
    if len(bars) < 2:
        return bars

    sorted_bars = sorted(bars, key=lambda b: b.date)
    closes = [b.close for b in sorted_bars]

    # Scan for split-like discontinuities (newest to oldest so we can
    # chain-adjust multiple splits if needed, though that's rare).
    split_points: list[tuple[int, float]] = []  # (index, ratio)
    for i in range(len(closes) - 1, 0, -1):
        if closes[i - 1] <= 0 or closes[i] <= 0:
            continue
        log_ret = math.log(closes[i] / closes[i - 1])
        if abs(log_ret) > SPLIT_LOG_RETURN_THRESHOLD:
            # Estimate the split ratio: round to nearest common split
            raw_ratio = closes[i - 1] / closes[i]
            # Common ratios: 2, 3, 4, 5, 7, 8, 10, 15, 20, 1/2, 1/3, etc.
            best_ratio = round(raw_ratio)
            if best_ratio < 1:
                best_ratio = round(1.0 / raw_ratio)
                best_ratio = 1.0 / best_ratio
            split_points.append((i, raw_ratio))
            logger.info(
                f"    Split detected at {sorted_bars[i].date}: "
                f"ratio ~{raw_ratio:.2f} ({sorted_bars[i-1].close:.2f} -> {sorted_bars[i].close:.2f})"
            )

    if not split_points:
        return bars

    # Apply adjustments: for each split point, divide all bars before it
    # by the split ratio so everything is in the post-split price scale.
    adjusted = []
    for bar in sorted_bars:
        adj_close = bar.close
        adj_open = bar.open
        adj_high = bar.high
        adj_low = bar.low
        for split_idx, ratio in split_points:
            split_date = sorted_bars[split_idx].date
            if bar.date < split_date:
                adj_close /= ratio
                adj_open /= ratio
                adj_high /= ratio
                adj_low /= ratio
        adjusted.append(DailyBar(
            date=bar.date,
            open=round(adj_open, 4),
            high=round(adj_high, 4),
            low=round(adj_low, 4),
            close=round(adj_close, 4),
            volume=bar.volume,
        ))

    return adjusted


async def repair_ticker(
    client: BackfillClient,
    ticker: str,
    dry_run: bool = False,
) -> dict:
    """
    Repair rv30 and vrp for a single ticker.
    Returns stats dict: {dates_checked, dates_updated, sample_changes}.
    """
    conn = get_connection()
    rows = conn.execute(
        "SELECT date, atm_iv, rv30, vrp FROM daily_iv WHERE ticker = ? ORDER BY date ASC",
        (ticker,),
    ).fetchall()
    conn.close()

    if not rows:
        logger.info(f"  {ticker}: No daily_iv rows found, skipping")
        return {"dates_checked": 0, "dates_updated": 0, "sample_changes": []}

    earliest_date = rows[0][0]
    latest_date = rows[-1][0]

    # Fetch adjusted bars covering the full range + buffer for RV30
    from_date = date.fromisoformat(earliest_date) - timedelta(days=LOOKBACK_BUFFER_DAYS)
    to_date = date.fromisoformat(latest_date)

    logger.info(f"  {ticker}: Fetching adjusted bars {from_date} -> {to_date}")
    bars = await client.fetch_daily_bars(ticker, from_date, to_date)

    if not bars:
        logger.warning(f"  {ticker}: No bars returned from API, skipping")
        return {"dates_checked": len(rows), "dates_updated": 0, "sample_changes": []}

    # Detect and correct splits (API may return unadjusted data)
    bars = detect_and_adjust_splits(bars)

    # Build a date->bar lookup and sorted bar list
    bar_by_date: dict[str, DailyBar] = {b.date: b for b in bars}
    sorted_bars = sorted(bars, key=lambda b: b.date)

    stats = {"dates_checked": len(rows), "dates_updated": 0, "sample_changes": []}
    updates: list[tuple] = []  # (rv30, vrp, spot, ticker, date)

    for row_date, atm_iv, old_rv30, old_vrp in rows:
        # Get bars up to this date for RV30 computation
        bars_up_to = [b for b in sorted_bars if b.date <= row_date]
        new_rv30 = compute_rv30_from_bars(bars_up_to)

        if new_rv30 is None:
            continue

        new_vrp = round(atm_iv - new_rv30, 2)

        # Get the adjusted spot price for this date
        bar = bar_by_date.get(row_date)
        new_spot = bar.close if bar else None

        # Check if values actually changed (tolerance for float comparison)
        rv30_changed = old_rv30 is None or abs(new_rv30 - old_rv30) > 0.1
        vrp_changed = old_vrp is None or abs(new_vrp - old_vrp) > 0.1

        if rv30_changed or vrp_changed:
            updates.append((new_rv30, new_vrp, new_spot, ticker, row_date))
            stats["dates_updated"] += 1

            # Keep a few samples for dry-run display
            if len(stats["sample_changes"]) < 5:
                stats["sample_changes"].append({
                    "date": row_date,
                    "rv30": f"{old_rv30} -> {new_rv30}" if old_rv30 else f"None -> {new_rv30}",
                    "vrp": f"{old_vrp} -> {new_vrp}" if old_vrp else f"None -> {new_vrp}",
                    "spot": f"-> {new_spot}" if new_spot else "N/A",
                })

    if dry_run:
        return stats

    # Apply DB updates
    if updates:
        conn = get_connection()
        conn.executemany(
            "UPDATE daily_iv SET rv30 = ?, vrp = ? WHERE ticker = ? AND date = ?",
            [(rv30, vrp, tk, dt) for rv30, vrp, spot, tk, dt in updates],
        )
        conn.commit()
        conn.close()
        logger.info(f"  {ticker}: Updated {len(updates)} rows in daily_iv")

    # Rewrite daily CSV with corrected values
    _rewrite_daily_csv(ticker, bar_by_date, updates)

    return stats


def _rewrite_daily_csv(
    ticker: str,
    bar_by_date: dict[str, DailyBar],
    updates: list[tuple],
):
    """Rewrite the daily CSV with corrected spot, rv30, vrp values."""
    csv_path = DATA_DIR / "daily" / f"{ticker}.csv"
    if not csv_path.exists():
        logger.debug(f"  {ticker}: No daily CSV to rewrite")
        return

    # Build lookup of corrections: date → (rv30, vrp, spot)
    corrections: dict[str, tuple] = {}
    for rv30, vrp, spot, tk, dt in updates:
        corrections[dt] = (rv30, vrp, spot)

    # Read existing CSV
    with open(csv_path, "r", newline="") as f:
        reader = csv.reader(f)
        header = next(reader)
        rows = list(reader)

    # Find column indices (defensive against header variations)
    try:
        date_idx = header.index("date")
        spot_idx = header.index("spot")
        rv30_idx = header.index("rv30")
        vrp_idx = header.index("vrp")
    except ValueError as e:
        logger.warning(f"  {ticker}: CSV header mismatch ({e}), skipping CSV rewrite")
        return

    updated_count = 0
    for row in rows:
        if not row:
            continue
        row_date = row[date_idx]
        if row_date in corrections:
            rv30, vrp, spot = corrections[row_date]
            row[rv30_idx] = str(round(rv30, 2))
            row[vrp_idx] = str(round(vrp, 2))
            if spot is not None:
                row[spot_idx] = str(round(spot, 2))
            updated_count += 1

    # Write back
    with open(csv_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)

    logger.info(f"  {ticker}: Rewrote {updated_count} rows in {csv_path.name}")


async def main_async(args: argparse.Namespace):
    api_key = os.environ.get("MARKETDATA_TOKEN")
    if not api_key:
        print("Error: MARKETDATA_TOKEN environment variable not set.")
        sys.exit(1)

    # Resolve tickers
    if args.all:
        tickers = list(UNIVERSE.keys())
    elif args.tickers:
        tickers = [t.strip().upper() for t in args.tickers.split(",")]
        invalid = [t for t in tickers if t not in UNIVERSE]
        if invalid:
            print(f"Error: Unknown tickers: {', '.join(invalid)}")
            print(f"Available: {', '.join(sorted(UNIVERSE.keys()))}")
            sys.exit(1)
    else:
        print("Error: Specify --tickers NFLX or --all")
        sys.exit(1)

    init_db()

    mode = "DRY RUN" if args.dry_run else "LIVE"
    print(f"Theta Harvest — RV Repair ({mode})")
    print(f"  Tickers: {', '.join(tickers)}")
    print()

    client = BackfillClient(api_key=api_key, rate_limit=15)

    try:
        for ticker in tickers:
            print(f"Processing {ticker}...")
            stats = await repair_ticker(client, ticker, dry_run=args.dry_run)

            print(f"  Checked: {stats['dates_checked']} dates")
            print(f"  Updated: {stats['dates_updated']} dates")

            if stats["sample_changes"]:
                print("  Sample changes:")
                for change in stats["sample_changes"]:
                    print(f"    {change['date']}: rv30 {change['rv30']}, vrp {change['vrp']}, spot {change['spot']}")

            if stats["dates_updated"] == 0:
                print("  No corrections needed.")
            print()

    finally:
        await client.close()

    print("Done.")


def main():
    parser = argparse.ArgumentParser(
        description="Repair stock-split-corrupted RV30/VRP values in daily_iv.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python repair_rv.py --tickers NFLX --dry-run   # Preview changes
  python repair_rv.py --tickers NFLX             # Apply fix
  python repair_rv.py --tickers NFLX,AMZN        # Fix multiple
  python repair_rv.py --all                       # Fix entire universe
        """,
    )
    parser.add_argument(
        "--tickers", type=str, default=None,
        help="Comma-separated tickers to repair (e.g. NFLX,AMZN)",
    )
    parser.add_argument(
        "--all", action="store_true",
        help="Repair all tickers in UNIVERSE",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Preview changes without writing to DB or CSV",
    )
    parser.add_argument(
        "--verbose", action="store_true",
        help="Show debug logging",
    )

    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    else:
        logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)

    asyncio.run(main_async(args))


if __name__ == "__main__":
    main()
