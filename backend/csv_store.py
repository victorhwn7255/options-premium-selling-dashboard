"""Shared CSV helpers for daily metrics and option quotes persistence."""

import csv
from datetime import datetime
from pathlib import Path
from typing import Optional

from marketdata_client import OptionContract

DATA_DIR = Path(__file__).parent / "data"

QUOTES_HEADER = [
    "date", "option_symbol", "underlying", "strike", "expiration",
    "side", "bid", "ask", "mid", "last", "underlying_price",
    "dte", "computed_iv", "volume", "open_interest",
]

DAILY_HEADER = [
    "date", "spot", "atm_iv", "rv30", "vrp", "term_slope",
]


def _ensure_csv(path: Path, header: list[str]):
    """Create CSV with header if it doesn't exist."""
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", newline="") as f:
            csv.writer(f).writerow(header)


def _csv_has_date(path: Path, target_date: str, date_col: int = 0) -> bool:
    """Check if a date already exists in a CSV (avoids duplicate rows on re-run)."""
    if not path.exists():
        return False
    with open(path, "r") as f:
        reader = csv.reader(f)
        next(reader, None)  # skip header
        for row in reader:
            if row and row[date_col] == target_date:
                return True
    return False


def append_quotes_csv(
    ticker: str,
    as_of: str,
    contracts: list[OptionContract],
    spot_price: float,
):
    """Append option quote rows to data/quotes/{ticker}.csv"""
    path = DATA_DIR / "quotes" / f"{ticker}.csv"
    _ensure_csv(path, QUOTES_HEADER)

    if _csv_has_date(path, as_of):
        return

    with open(path, "a", newline="") as f:
        w = csv.writer(f)
        for c in contracts:
            exp_date = datetime.strptime(c.expiration, "%Y-%m-%d").date()
            as_of_date = datetime.strptime(as_of, "%Y-%m-%d").date()
            dte = (exp_date - as_of_date).days
            w.writerow([
                as_of,
                f"{ticker}{c.expiration.replace('-','')}"
                f"{'C' if c.contract_type == 'call' else 'P'}"
                f"{int(c.strike * 1000):08d}",
                ticker,
                c.strike,
                c.expiration,
                c.contract_type,
                c.bid if c.bid is not None else "",
                c.ask if c.ask is not None else "",
                round((c.bid + c.ask) / 2, 4) if c.bid and c.ask else "",
                c.last_price if c.last_price is not None else "",
                spot_price,
                dte,
                round(c.implied_volatility, 6) if c.implied_volatility else "",
                c.volume,
                c.open_interest,
            ])


def append_daily_csv(
    ticker: str,
    as_of: str,
    spot: float,
    atm_iv: float,
    rv30: Optional[float],
    vrp: Optional[float],
    term_slope: Optional[float],
):
    """Insert a daily metrics row into data/daily/{ticker}.csv in date-descending order."""
    path = DATA_DIR / "daily" / f"{ticker}.csv"
    _ensure_csv(path, DAILY_HEADER)

    new_row = [
        as_of,
        round(spot, 2),
        round(atm_iv, 2),
        round(rv30, 2) if rv30 is not None else "",
        round(vrp, 2) if vrp is not None else "",
        round(term_slope, 3) if term_slope is not None else "",
    ]

    # Read existing rows, insert new row in sorted position (newest first)
    with open(path, "r", newline="") as f:
        reader = csv.reader(f)
        header = next(reader)
        rows = list(reader)

    # Skip if date already exists
    if any(row and row[0] == as_of for row in rows):
        return

    rows.append(new_row)
    rows.sort(key=lambda r: r[0] if r else "", reverse=True)

    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)
