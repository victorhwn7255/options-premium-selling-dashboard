"""
Import per-ticker scan metrics from history/metrics-logs.md into daily_iv.

Use case: production runs on Lightsail; the local DB lacks recent dates.
The markdown log is the human-maintained record. This script parses it
and upserts the missing rows so the activity grid (and any other historical
aggregate) is complete locally.

Parses columns: Ticker, IV, RV30, VRP, Term Slope.
Skips NO DATA rows (IV = "N/A").
By default only writes dates strictly newer than the latest date already
in daily_iv — this avoids regressing precision on overlapping dates
(markdown values are rounded to 1 decimal place; live scans are full precision).

Usage:
    python import_metrics_log.py                 # newer-dates-only, dry run
    python import_metrics_log.py --apply         # newer-dates-only, write
    python import_metrics_log.py --apply --all   # write all dates (overwrites)
"""

import argparse
import re
import sys
from datetime import date
from pathlib import Path

from database import get_connection, store_daily_iv


REPO_ROOT = Path(__file__).resolve().parent.parent
LOG_PATH = REPO_ROOT / "history" / "metrics-logs.md"

DATE_HEADING = re.compile(r"^##\s+(\d{4}-\d{2}-\d{2})\b")
ROW = re.compile(r"^\|\s*([A-Z]{1,5})\s*\|")


def parse_float(cell: str):
    s = cell.strip()
    if s in ("N/A", "—", "-", ""):
        return None
    try:
        return float(s)
    except ValueError:
        return None


def parse_log(path: Path) -> dict[str, list[dict]]:
    """Return {iso_date: [{ticker, atm_iv, rv30, vrp, term_slope}, ...]}"""
    by_date: dict[str, list[dict]] = {}
    current_date: str | None = None

    for line in path.read_text().splitlines():
        m = DATE_HEADING.match(line)
        if m:
            current_date = m.group(1)
            by_date.setdefault(current_date, [])
            continue
        if current_date is None:
            continue
        if not ROW.match(line):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        # Skip header + separator rows (header has "Ticker", separator has "---")
        if not cells or cells[0] in ("Ticker",) or set(cells[0]) <= set("- "):
            continue
        # Expected columns: Ticker | Score | IV | IV Pct | RV30 | VRP | Term Slope | RV Accel | 25Δ Skew | θ/V | Earnings | Regime
        if len(cells) < 7:
            continue
        ticker = cells[0]
        iv = parse_float(cells[2])
        rv30 = parse_float(cells[4])
        vrp = parse_float(cells[5])
        term_slope = parse_float(cells[6])
        if iv is None:
            # NO DATA row — skip; we'd rather have the date absent than a fake row
            continue
        by_date[current_date].append({
            "ticker": ticker,
            "atm_iv": iv,
            "rv30": rv30,
            "vrp": vrp,
            "term_slope": term_slope,
        })

    return by_date


def latest_db_date() -> str | None:
    conn = get_connection()
    cur = conn.execute("SELECT MAX(date) FROM daily_iv")
    row = cur.fetchone()
    conn.close()
    return row[0] if row and row[0] else None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="Write to DB (default: dry run)")
    parser.add_argument("--all", action="store_true",
                        help="Write all dates from the log, not just newer-than-latest-DB")
    parser.add_argument("--log", type=Path, default=LOG_PATH, help=f"Path to metrics log (default: {LOG_PATH})")
    args = parser.parse_args()

    if not args.log.exists():
        print(f"ERROR: log not found at {args.log}", file=sys.stderr)
        return 1

    parsed = parse_log(args.log)
    if not parsed:
        print("No date sections parsed — check the log format.")
        return 1

    cutoff = None if args.all else latest_db_date()
    targets = sorted(d for d in parsed if (args.all or (cutoff is None) or d > cutoff))

    print(f"Log dates parsed: {len(parsed)}")
    print(f"Latest date in daily_iv: {cutoff or '(empty)'}")
    print(f"Dates to import: {len(targets)} → {targets}")

    total_rows = 0
    for d in targets:
        rows = parsed[d]
        print(f"  {d}: {len(rows)} ticker rows")
        total_rows += len(rows)
        if args.apply:
            for row in rows:
                store_daily_iv(
                    ticker=row["ticker"],
                    atm_iv=row["atm_iv"],
                    rv30=row["rv30"],
                    vrp=row["vrp"],
                    term_slope=row["term_slope"],
                    as_of=date.fromisoformat(d),
                )

    print(f"\nTotal rows: {total_rows}")
    print("Mode: APPLIED" if args.apply else "Mode: DRY RUN (re-run with --apply to write)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
