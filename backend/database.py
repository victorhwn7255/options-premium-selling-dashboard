"""
SQLite storage for historical IV values.

IV Rank and IV Percentile require a trailing 252-day history of daily ATM IV.
Polygon doesn't provide this pre-computed, so we store it ourselves.

On first run, historical IV will be empty — the scanner will use fallback
values and build history over time. After ~20 trading days of data
collection, IV Rank becomes meaningful. After ~252 days, it's fully
calibrated.
"""

import sqlite3
import json
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Optional


DB_PATH = Path(__file__).parent / "data" / "vol_history.db"


def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    """Create tables if they don't exist."""
    conn = get_connection()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS daily_iv (
            ticker TEXT NOT NULL,
            date TEXT NOT NULL,
            atm_iv REAL NOT NULL,
            rv30 REAL,
            vrp REAL,
            term_slope REAL,
            PRIMARY KEY (ticker, date)
        );

        CREATE INDEX IF NOT EXISTS idx_daily_iv_ticker
            ON daily_iv(ticker, date DESC);

        CREATE TABLE IF NOT EXISTS scan_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            tickers_scanned INTEGER,
            duration_seconds REAL,
            errors TEXT
        );

        CREATE TABLE IF NOT EXISTS scan_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            scanned_at TEXT NOT NULL,
            regime TEXT NOT NULL,
            tickers TEXT NOT NULL,
            historical TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS earnings_cache (
            ticker TEXT PRIMARY KEY,
            earnings_date TEXT NOT NULL,
            fetched_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS verification_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            scanned_at TEXT NOT NULL,
            verified_at TEXT NOT NULL,
            total_checks INTEGER NOT NULL,
            pass_count INTEGER NOT NULL,
            warn_count INTEGER NOT NULL,
            fail_count INTEGER NOT NULL,
            failures TEXT NOT NULL,
            warnings TEXT NOT NULL,
            full_report TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS earnings_verification_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            scanned_at TEXT NOT NULL,
            verified_at TEXT NOT NULL,
            total_checks INTEGER NOT NULL,
            pass_count INTEGER NOT NULL,
            fail_count INTEGER NOT NULL,
            skip_count INTEGER NOT NULL,
            checks TEXT NOT NULL
        );
    """)
    conn.commit()
    conn.close()


def store_daily_iv(
    ticker: str,
    atm_iv: float,
    rv30: Optional[float] = None,
    vrp: Optional[float] = None,
    term_slope: Optional[float] = None,
    as_of: Optional[date] = None,
):
    """Store today's ATM IV for a ticker."""
    d = (as_of or date.today()).isoformat()
    conn = get_connection()
    conn.execute(
        """
        INSERT INTO daily_iv (ticker, date, atm_iv, rv30, vrp, term_slope)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT (ticker, date) DO UPDATE SET
            atm_iv = excluded.atm_iv,
            rv30 = excluded.rv30,
            vrp = excluded.vrp,
            term_slope = excluded.term_slope
        """,
        (ticker, d, atm_iv, rv30, vrp, term_slope),
    )
    conn.commit()
    conn.close()


def get_historical_ivs(
    ticker: str,
    lookback_days: Optional[int] = None,
) -> list[float]:
    """
    Retrieve historical ATM IV values for IV Rank/Percentile computation.
    Returns all available values by default (most recent first).
    If lookback_days is set, limits to that many trading days.
    """
    conn = get_connection()
    if lookback_days:
        cutoff = (date.today() - timedelta(days=int(lookback_days * 1.5))).isoformat()
        cursor = conn.execute(
            """
            SELECT atm_iv FROM daily_iv
            WHERE ticker = ? AND date >= ?
            ORDER BY date DESC
            LIMIT ?
            """,
            (ticker, cutoff, lookback_days),
        )
    else:
        cursor = conn.execute(
            """
            SELECT atm_iv FROM daily_iv
            WHERE ticker = ?
            ORDER BY date DESC
            """,
            (ticker,),
        )
    ivs = [row[0] for row in cursor.fetchall()]
    conn.close()
    return ivs


def get_historical_series(
    ticker: str,
    lookback_days: int = 120,
) -> list[dict]:
    """
    Get full historical series for charting (IV, RV, VRP over time).
    """
    cutoff = (date.today() - timedelta(days=int(lookback_days * 1.5))).isoformat()
    conn = get_connection()
    cursor = conn.execute(
        """
        SELECT date, atm_iv, rv30, vrp, term_slope FROM daily_iv
        WHERE ticker = ? AND date >= ?
        ORDER BY date ASC
        LIMIT ?
        """,
        (ticker, cutoff, lookback_days),
    )
    rows = [
        {
            "date": row[0],
            "iv": row[1],
            "rv": row[2],
            "vrp": row[3],
            "term_slope": row[4],
        }
        for row in cursor.fetchall()
    ]
    conn.close()
    return rows


def log_scan(tickers_scanned: int, duration: float, errors: list[str] = None):
    """Log a scan run for debugging."""
    conn = get_connection()
    conn.execute(
        "INSERT INTO scan_log (timestamp, tickers_scanned, duration_seconds, errors) VALUES (?, ?, ?, ?)",
        (datetime.now().isoformat(), tickers_scanned, duration, json.dumps(errors or [])),
    )
    conn.commit()
    conn.close()


def store_scan_result(
    scanned_at: str,
    regime: dict,
    tickers: list[dict],
    historical: dict,
) -> int:
    """Store a complete scan result. Prunes to most recent 50 rows."""
    conn = get_connection()
    cursor = conn.execute(
        "INSERT INTO scan_results (scanned_at, regime, tickers, historical) VALUES (?, ?, ?, ?)",
        (scanned_at, json.dumps(regime), json.dumps(tickers), json.dumps(historical)),
    )
    row_id = cursor.lastrowid
    # Prune old rows, keep latest 50
    conn.execute(
        "DELETE FROM scan_results WHERE id NOT IN (SELECT id FROM scan_results ORDER BY id DESC LIMIT 50)"
    )
    conn.commit()
    conn.close()
    return row_id


def get_latest_scan() -> Optional[dict]:
    """Get the most recent scan result, or None if no scans exist."""
    conn = get_connection()
    row = conn.execute(
        "SELECT id, scanned_at, regime, tickers, historical FROM scan_results ORDER BY id DESC LIMIT 1"
    ).fetchone()
    conn.close()
    if not row:
        return None
    return {
        "id": row[0],
        "scanned_at": row[1],
        "regime": json.loads(row[2]),
        "tickers": json.loads(row[3]),
        "historical": json.loads(row[4]),
    }


def update_latest_scan_earnings(earnings: dict[str, int | None]) -> None:
    """Patch earnings_dte in the most recent cached scan result."""
    conn = get_connection()
    row = conn.execute(
        "SELECT id, tickers FROM scan_results ORDER BY id DESC LIMIT 1"
    ).fetchone()
    if not row:
        conn.close()
        return
    scan_id, tickers_json = row[0], json.loads(row[1])
    for t in tickers_json:
        if t["ticker"] in earnings:
            t["earnings_dte"] = earnings[t["ticker"]]
    conn.execute(
        "UPDATE scan_results SET tickers = ? WHERE id = ?",
        (json.dumps(tickers_json), scan_id),
    )
    conn.commit()
    conn.close()


def get_scan_history(limit: int = 10) -> list[dict]:
    """Return metadata for recent scans (no full payloads)."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT id, scanned_at, tickers FROM scan_results ORDER BY id DESC LIMIT ?",
        (limit,),
    ).fetchall()
    conn.close()
    results = []
    for row in rows:
        tickers = json.loads(row[2])
        best = max(tickers, key=lambda t: t.get("signal_score", 0)) if tickers else None
        results.append({
            "id": row[0],
            "scanned_at": row[1],
            "ticker_count": len(tickers),
            "best_score": best["signal_score"] if best else None,
            "best_ticker": best["ticker"] if best else None,
        })
    return results


def get_cached_earnings(ticker: str) -> Optional[str]:
    """Return cached earnings_date if it's still in the future, else None."""
    conn = get_connection()
    row = conn.execute(
        "SELECT earnings_date FROM earnings_cache WHERE ticker = ?",
        (ticker,),
    ).fetchone()
    conn.close()
    if row and row[0] >= date.today().isoformat():
        return row[0]
    return None


def clear_earnings_cache():
    """Delete all cached earnings rows, forcing re-fetch from FMP."""
    conn = get_connection()
    conn.execute("DELETE FROM earnings_cache")
    conn.commit()
    conn.close()


def store_cached_earnings(ticker: str, earnings_date: str):
    """Upsert earnings date for a ticker."""
    conn = get_connection()
    conn.execute(
        """
        INSERT INTO earnings_cache (ticker, earnings_date, fetched_at)
        VALUES (?, ?, ?)
        ON CONFLICT (ticker) DO UPDATE SET
            earnings_date = excluded.earnings_date,
            fetched_at = excluded.fetched_at
        """,
        (ticker, earnings_date, datetime.now().isoformat()),
    )
    conn.commit()
    conn.close()


def store_verification_result(report_dict: dict):
    """Store a verification report. Prunes to most recent 50 rows."""
    conn = get_connection()
    conn.execute(
        """
        INSERT INTO verification_results
            (scanned_at, verified_at, total_checks, pass_count, warn_count, fail_count,
             failures, warnings, full_report)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            report_dict["scan_timestamp"],
            datetime.now().isoformat(),
            report_dict["total_checks"],
            report_dict["pass_count"],
            report_dict["warn_count"],
            report_dict["fail_count"],
            json.dumps(report_dict["failures"]),
            json.dumps(report_dict["warnings"]),
            json.dumps(report_dict),
        ),
    )
    conn.execute(
        "DELETE FROM verification_results WHERE id NOT IN "
        "(SELECT id FROM verification_results ORDER BY id DESC LIMIT 50)"
    )
    conn.commit()
    conn.close()


def get_latest_verification() -> Optional[dict]:
    """Fetch the most recent verification result, or None."""
    conn = get_connection()
    row = conn.execute(
        "SELECT id, scanned_at, verified_at, total_checks, pass_count, warn_count, "
        "fail_count, failures, warnings FROM verification_results ORDER BY id DESC LIMIT 1"
    ).fetchone()
    conn.close()
    if not row:
        return None
    return {
        "id": row[0],
        "scanned_at": row[1],
        "verified_at": row[2],
        "total_checks": row[3],
        "pass_count": row[4],
        "warn_count": row[5],
        "fail_count": row[6],
        "failures": json.loads(row[7]),
        "warnings": json.loads(row[8]),
    }


def store_earnings_verification(report_dict: dict):
    """Store an earnings verification report. Prunes to most recent 50 rows."""
    conn = get_connection()
    conn.execute(
        """
        INSERT INTO earnings_verification_results
            (scanned_at, verified_at, total_checks, pass_count, fail_count, skip_count, checks)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            report_dict["scan_timestamp"],
            datetime.now().isoformat(),
            report_dict["total_checks"],
            report_dict["pass_count"],
            report_dict["fail_count"],
            report_dict["skip_count"],
            json.dumps(report_dict["checks"]),
        ),
    )
    conn.execute(
        "DELETE FROM earnings_verification_results WHERE id NOT IN "
        "(SELECT id FROM earnings_verification_results ORDER BY id DESC LIMIT 50)"
    )
    conn.commit()
    conn.close()


def get_latest_earnings_verification() -> Optional[dict]:
    """Fetch the most recent earnings verification result, or None."""
    conn = get_connection()
    row = conn.execute(
        "SELECT id, scanned_at, verified_at, total_checks, pass_count, fail_count, "
        "skip_count, checks FROM earnings_verification_results ORDER BY id DESC LIMIT 1"
    ).fetchone()
    conn.close()
    if not row:
        return None
    return {
        "id": row[0],
        "scanned_at": row[1],
        "verified_at": row[2],
        "total_checks": row[3],
        "pass_count": row[4],
        "fail_count": row[5],
        "skip_count": row[6],
        "checks": json.loads(row[7]),
    }


# Initialize on import
init_db()
