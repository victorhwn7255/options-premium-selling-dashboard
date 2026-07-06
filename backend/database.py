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
# Trial registry (spec Module E2): append-only JSONL of every backtest run.
# Created empty in Phase A so the path is stable across phases (used in D/F).
TRIAL_REGISTRY_PATH = DB_PATH.parent / "trial_registry.jsonl"


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
            skew_25d REAL,
            rv10 REAL,
            iv_percentile REAL,
            spot REAL,
            earnings_dte INTEGER,
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

        /* ── Credit Put Spreads (Phase 3) ────────────────────────────
         * Per-ticker, per-scan outcome rows. Used for:
         *   1. Ticker-level consecutive_sell_days lookup (SELL_CPS gate)
         *   2. Exact-spread consecutive_days (display-only context)
         *   3. /api/credit-put-spreads/latest reconstruction
         *
         * Additive: existing tables and queries unaffected.
         */
        CREATE TABLE IF NOT EXISTS cps_candidate_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            scan_date TEXT NOT NULL,            -- YYYY-MM-DD
            ticker TEXT NOT NULL,
            action TEXT NOT NULL,                -- SELL_CPS / WATCH_CPS / WAIT / AVOID / NO_EDGE / NO_DATA
            expiration TEXT,                     -- nullable when no candidate constructed
            short_strike REAL,
            long_strike REAL,
            credit_to_width REAL,
            base_score REAL,
            regime TEXT,
            passed_filters INTEGER NOT NULL DEFAULT 0,   -- 1 if all hard+exec filters cleared
            sell_eligible INTEGER NOT NULL DEFAULT 0,    -- 1 if eligible for SELL_CPS today (pre-confirmation)
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(scan_date, ticker, expiration, short_strike, long_strike)
        );

        CREATE INDEX IF NOT EXISTS idx_cps_history_ticker_date
            ON cps_candidate_history(ticker, scan_date DESC);

        /* Cache of the full /api/credit-put-spreads/latest response per scan.
         * Allows the endpoint to serve the exact response we built during
         * the scan without re-fetching chains or re-running the builder. */
        CREATE TABLE IF NOT EXISTS cps_scan_responses (
            scan_date TEXT PRIMARY KEY,
            response_json TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        /* ══ Theta Harvest v2 — silent data substrate (Phase A) ═══════════
         * All additive. v1 tables/queries untouched; nothing here changes
         * live behavior until Phase E (spec Module G, master plan §A).
         */

        /* Daily OHLC bars — the v2 estimator/forecaster input (GK+overnight,
         * Yang-Zhang, downside semivariance). `source` flags the historical
         * yfinance seed vs the live MarketData series (one seam at "now",
         * absorbed by the vbar demean). `quarantine`=1 marks a bar that
         * failed an integrity check — never silently corrected. */
        CREATE TABLE IF NOT EXISTS daily_bars (
            ticker TEXT NOT NULL,
            date TEXT NOT NULL,               -- YYYY-MM-DD
            o REAL, h REAL, l REAL, c REAL, v REAL,
            source TEXT,                      -- 'yfinance' | 'marketdata'
            adj_flag INTEGER DEFAULT 1,       -- 1 = split-adjusted
            quarantine INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY (ticker, date)
        );
        CREATE INDEX IF NOT EXISTS idx_daily_bars_ticker
            ON daily_bars(ticker, date DESC);

        /* VIX family daily closes (^VIX, ^VIX3M, ^VVIX) from yfinance.
         * PUT (Cboe PutWrite) benchmark is deferred to Phase D (Cboe CSV). */
        CREATE TABLE IF NOT EXISTS index_daily (
            symbol TEXT NOT NULL,
            date TEXT NOT NULL,
            o REAL, h REAL, l REAL, c REAL,
            PRIMARY KEY (symbol, date)
        );
        CREATE INDEX IF NOT EXISTS idx_index_daily_symbol
            ON index_daily(symbol, date DESC);

        /* Per-ticker-per-date gate state (spec Module B). Phase A writes the
         * SHADOW replay; Phase B extends this (additively) with the live
         * transition machine. `pending`/`blackout` reserved for Phase B. */
        CREATE TABLE IF NOT EXISTS gate_state (
            ticker TEXT NOT NULL,
            date TEXT NOT NULL,
            state TEXT NOT NULL,              -- NORMAL | CAUTION | DANGER
            transient INTEGER NOT NULL DEFAULT 0,
            pending TEXT,
            pending_days INTEGER NOT NULL DEFAULT 0,
            blackout INTEGER NOT NULL DEFAULT 0,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (ticker, date)
        );

        /* Shadow-diff: one row per ticker per scan (master plan §A3). Thin —
         * decisions + classification only; drivers join from daily_iv. */
        CREATE TABLE IF NOT EXISTS shadow_diff (
            date TEXT NOT NULL,
            ticker TEXT NOT NULL,
            is_etf INTEGER NOT NULL DEFAULT 0,
            v1_action TEXT,                   -- SELL PREMIUM / CONDITIONAL / WATCHLIST / NO EDGE / AVOID / SKIP / NO DATA
            v1_regime TEXT,                   -- NORMAL / CAUTION / DANGER
            v2_eligible INTEGER,              -- v2 seven-condition eligibility
            v2_gate_state TEXT,
            v2_transient INTEGER,
            divergence_class TEXT,            -- AGREE / V2_STRICTER / V2_LOOSER / STATE_MISMATCH / NODATA_SKEW
            divergence_reason TEXT,
            v2_warm INTEGER NOT NULL DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (date, ticker)
        );
        CREATE INDEX IF NOT EXISTS idx_shadow_diff_date
            ON shadow_diff(date DESC);

        /* Positions ledger (spec Module G / master plan §C1). Created empty in
         * Phase A; populated by the manual journal in Phase C. The entry
         * sizing snapshot is the audit trail of recommended-vs-entered. */
        CREATE TABLE IF NOT EXISTS positions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT NOT NULL,
            structure TEXT NOT NULL,          -- naked_put | put_spread
            status TEXT NOT NULL DEFAULT 'open',   -- open | closed
            short_strike REAL,
            long_strike REAL,                 -- null for naked
            expiry TEXT,
            contracts INTEGER,
            entry_date TEXT,
            entry_credit REAL,                -- per share
            entry_fills TEXT,                 -- json, per leg
            entry_commissions REAL,
            close_date TEXT,
            close_debit REAL,
            close_fills TEXT,                 -- json
            close_commissions REAL,
            realized_pnl REAL,
            entry_spot REAL,
            entry_iv REAL,
            entry_sigma_fwd REAL,
            entry_fvrp REAL,
            rec_contracts INTEGER,
            f_star REAL,
            dial_R REAL,
            dial_O REAL,
            margin_per_contract REAL,
            binding_cap TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        /* Per-closed-trade telemetry (spec Module G). Empty in A; Phase C/D. */
        CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            position_id INTEGER,
            ticker TEXT,
            margin_per_contract REAL,
            margin_util_at_entry REAL,
            fill_vs_mid_entry REAL,
            fill_vs_mid_exit REAL,
            quoted_spread_entry REAL,
            quoted_spread_exit REAL,
            iv_entry REAL,
            sigma_fwd_entry REAL,
            rv_realized_hold REAL,
            capture REAL,
            dial_R REAL,
            dial_O REAL,
            f_star_at_entry REAL,
            stressed_loss_at_entry REAL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        /* Daily portfolio NAV + risk/measurement series (spec Module G).
         * Empty in A; populated by Phase D measurement. */
        CREATE TABLE IF NOT EXISTS portfolio_daily (
            date TEXT PRIMARY KEY,
            nav REAL,
            notional_short_put REAL,
            margin_total REAL,
            stress_pnl_20_2x REAL,
            stress_pnl_10_15x REAL,
            psr0 REAL,
            psr05 REAL,
            mintrl REAL,
            monitor_e4 REAL,
            skew60 REAL,
            kurt60 REAL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # Additive daily_iv migration for DBs created before 2026-07: the scan computes
    # skew/rv10/iv_percentile/spot/earnings_dte every day but only 4 fields were
    # persisted, which forces imputation in any historical research (see
    # docs/strategy-backtest-2026-07.md). Existing rows keep NULLs.
    existing = {row[1] for row in conn.execute("PRAGMA table_info(daily_iv)")}
    for col, typ in (("skew_25d", "REAL"), ("rv10", "REAL"), ("iv_percentile", "REAL"),
                     ("spot", "REAL"), ("earnings_dte", "INTEGER")):
        if col not in existing:
            conn.execute(f"ALTER TABLE daily_iv ADD COLUMN {col} {typ}")

    # v2 (Phase A, silent) — additive Module-G columns on daily_iv: the v2
    # estimator/forecaster/gate outputs stored beside v1, plus the legacy_*
    # snapshot the shadow-diff compares against. All nullable; existing rows
    # keep NULLs and v1 never reads these. (master plan §A3, spec Module G)
    v2_cols = (
        ("v_gk", "REAL"), ("s_neg", "REAL"), ("s_pos", "REAL"),
        ("ewma_v_1", "REAL"), ("ewma_v_5", "REAL"), ("ewma_v_25", "REAL"), ("ewma_v_125", "REAL"),
        ("ewma_sneg_5", "REAL"), ("ewma_sneg_25", "REAL"), ("vbar", "REAL"),
        ("sigma_fwd", "REAL"), ("sigma_fwd_dn", "REAL"),
        ("fvrp_ratio", "REAL"), ("fvrp_z", "REAL"), ("slope_1m3m", "REAL"), ("accel_dn", "REAL"),
        ("global_factor", "REAL"), ("transient_tag", "INTEGER"),
        ("v2_gate_state", "TEXT"), ("v2_eligible", "INTEGER"),
        ("v2_warm", "INTEGER"), ("low_coverage", "INTEGER"),
        ("legacy_signal_score", "INTEGER"), ("legacy_recommendation", "TEXT"),
        ("legacy_regime", "TEXT"), ("legacy_vrp_ratio", "REAL"),
        ("legacy_term_slope", "REAL"), ("legacy_rv_accel", "REAL"),
    )
    for col, typ in v2_cols:
        if col not in existing:
            conn.execute(f"ALTER TABLE daily_iv ADD COLUMN {col} {typ}")

    conn.commit()
    conn.close()

    # Trial registry file (spec Module E2) — created empty; never truncated.
    TRIAL_REGISTRY_PATH.touch(exist_ok=True)


def store_daily_iv(
    ticker: str,
    atm_iv: float,
    rv30: Optional[float] = None,
    vrp: Optional[float] = None,
    term_slope: Optional[float] = None,
    as_of: Optional[date] = None,
    skew_25d: Optional[float] = None,
    rv10: Optional[float] = None,
    iv_percentile: Optional[float] = None,
    spot: Optional[float] = None,
    earnings_dte: Optional[int] = None,
):
    """Store today's per-ticker metrics snapshot (ATM IV + research fields)."""
    d = (as_of or date.today()).isoformat()
    conn = get_connection()
    conn.execute(
        """
        INSERT INTO daily_iv (ticker, date, atm_iv, rv30, vrp, term_slope,
                              skew_25d, rv10, iv_percentile, spot, earnings_dte)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT (ticker, date) DO UPDATE SET
            atm_iv = excluded.atm_iv,
            rv30 = excluded.rv30,
            vrp = excluded.vrp,
            term_slope = excluded.term_slope,
            skew_25d = excluded.skew_25d,
            rv10 = excluded.rv10,
            iv_percentile = excluded.iv_percentile,
            spot = excluded.spot,
            earnings_dte = excluded.earnings_dte
        """,
        (ticker, d, atm_iv, rv30, vrp, term_slope,
         skew_25d, rv10, iv_percentile, spot, earnings_dte),
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


def get_vrp_history_by_date(start: str, end: str, min_tickers: int = 30) -> list[dict]:
    """
    Aggregate avg VRP across all tickers per date for a date range (inclusive).
    Used by the activity grid in the regime banner.

    Dates with fewer than `min_tickers` ticker rows are omitted — partial scans
    (e.g. an interrupted run) would otherwise produce a "33-ticker mean" that
    isn't actually computed over 33 tickers and silently disagree with the
    component caption.
    """
    conn = get_connection()
    cursor = conn.execute(
        """
        SELECT date, AVG(vrp) AS avg_vrp, COUNT(*) AS n
        FROM daily_iv
        WHERE date >= ? AND date <= ? AND vrp IS NOT NULL
        GROUP BY date
        HAVING n >= ?
        ORDER BY date ASC
        """,
        (start, end, min_tickers),
    )
    rows = [
        {"date": row[0], "avg_vrp": float(row[1]), "ticker_count": int(row[2])}
        for row in cursor.fetchall()
    ]
    conn.close()
    return rows


# ────────────────────────────────────────────────────────────────────────
# Credit Put Spreads — Phase 3 helpers
# ────────────────────────────────────────────────────────────────────────

def get_vrp_history(ticker: str, days: int = 60) -> list[float]:
    """Return the last `days` non-null VRP values for `ticker`, oldest first.

    Used by the spread builder for the 60-day VRP z-score floor. Empty list
    or short history is returned as-is — the consumer decides how to handle
    insufficient data (we never crash, never silently fabricate a value).
    """
    conn = get_connection()
    # Pull the most recent `days` rows, then reverse to oldest→newest order
    cursor = conn.execute(
        """
        SELECT vrp FROM daily_iv
        WHERE ticker = ? AND vrp IS NOT NULL
        ORDER BY date DESC
        LIMIT ?
        """,
        (ticker, days),
    )
    rows = [float(r[0]) for r in cursor.fetchall()]
    conn.close()
    rows.reverse()  # oldest → newest, matching downstream consumer convention
    return rows


def record_cps_candidate(
    scan_date: str,
    ticker: str,
    action: str,
    expiration: Optional[str] = None,
    short_strike: Optional[float] = None,
    long_strike: Optional[float] = None,
    credit_to_width: Optional[float] = None,
    base_score: Optional[float] = None,
    regime: Optional[str] = None,
    passed_filters: bool = False,
    sell_eligible: bool = False,
) -> int:
    """Insert (or replace) a CPS candidate-history row for one scan.

    `sell_eligible` is what the next day's `get_consecutive_sell_days()` reads
    — it means "all SELL_CPS construction + execution + base gates passed
    today, ignoring confirmation/overlay." Persistence is idempotent on
    `(scan_date, ticker, expiration, short_strike, long_strike)`.
    """
    conn = get_connection()
    cursor = conn.execute(
        """
        INSERT INTO cps_candidate_history (
            scan_date, ticker, action, expiration, short_strike, long_strike,
            credit_to_width, base_score, regime, passed_filters, sell_eligible
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT (scan_date, ticker, expiration, short_strike, long_strike)
        DO UPDATE SET
            action = excluded.action,
            credit_to_width = excluded.credit_to_width,
            base_score = excluded.base_score,
            regime = excluded.regime,
            passed_filters = excluded.passed_filters,
            sell_eligible = excluded.sell_eligible
        """,
        (
            scan_date, ticker, action,
            expiration, short_strike, long_strike,
            credit_to_width, base_score, regime,
            1 if passed_filters else 0,
            1 if sell_eligible else 0,
        ),
    )
    row_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return row_id


def get_consecutive_sell_days(
    ticker: str,
    asof: Optional[date] = None,
) -> int:
    """Count consecutive trailing scan dates where `ticker` was SELL-eligible.

    Walks backwards from `asof` (or today). For each prior scan date we have
    a row for this ticker, increment the streak if ANY candidate on that
    date had `sell_eligible=1`. Stops at the first gap or non-eligible day.

    Streaks are based on calendar dates *we have data for* — not strict
    consecutive calendar days — so weekends don't break the streak.

    Note on `scan_date <= ?`: this is `<=` (inclusive), not `<`. In the
    production flow, `_build_cps_response()` calls this function BEFORE it
    calls `record_cps_candidate()` for today, so today's row doesn't exist
    yet and the bound is functionally equivalent to a strict `<`. Tests
    pre-populate the asof-day row to verify "today eligible + N prior days
    eligible → streak = N+1" — that contract requires the inclusive bound.
    """
    asof = asof or date.today()
    conn = get_connection()
    cursor = conn.execute(
        """
        SELECT scan_date, MAX(sell_eligible) AS any_eligible
        FROM cps_candidate_history
        WHERE ticker = ? AND scan_date <= ?
        GROUP BY scan_date
        ORDER BY scan_date DESC
        """,
        (ticker, asof.isoformat()),
    )
    streak = 0
    for _scan_date, any_eligible in cursor.fetchall():
        if any_eligible:
            streak += 1
        else:
            break
    conn.close()
    return streak


def get_consecutive_exact_spread_days(
    ticker: str,
    expiration: str,
    short_strike: float,
    long_strike: float,
    asof: Optional[date] = None,
) -> int:
    """Same as `get_consecutive_sell_days` but for the exact spread identity.

    Display-only context — never the SELL_CPS gate. Strikes shift day-to-day
    with the chain, so this almost always lags the ticker-level streak.
    """
    asof = asof or date.today()
    conn = get_connection()
    cursor = conn.execute(
        """
        SELECT scan_date, sell_eligible
        FROM cps_candidate_history
        WHERE ticker = ? AND expiration = ?
          AND short_strike = ? AND long_strike = ?
          AND scan_date <= ?
        ORDER BY scan_date DESC
        """,
        (ticker, expiration, short_strike, long_strike, asof.isoformat()),
    )
    streak = 0
    for _scan_date, sell_eligible in cursor.fetchall():
        if sell_eligible:
            streak += 1
        else:
            break
    conn.close()
    return streak


def save_cps_scan_response(scan_date: str, response_dict: dict) -> None:
    """Cache the full /api/credit-put-spreads/latest response JSON."""
    conn = get_connection()
    conn.execute(
        """
        INSERT INTO cps_scan_responses (scan_date, response_json)
        VALUES (?, ?)
        ON CONFLICT (scan_date) DO UPDATE SET
            response_json = excluded.response_json,
            created_at = CURRENT_TIMESTAMP
        """,
        (scan_date, json.dumps(response_dict)),
    )
    # Prune to last 14 responses (~2 weeks of scans)
    conn.execute(
        "DELETE FROM cps_scan_responses WHERE scan_date NOT IN "
        "(SELECT scan_date FROM cps_scan_responses ORDER BY scan_date DESC LIMIT 14)"
    )
    conn.commit()
    conn.close()


def get_latest_cps_scan_response() -> Optional[dict]:
    """Load the most-recent cached response, or None if none cached."""
    conn = get_connection()
    row = conn.execute(
        "SELECT scan_date, response_json FROM cps_scan_responses "
        "ORDER BY scan_date DESC LIMIT 1"
    ).fetchone()
    conn.close()
    if not row:
        return None
    try:
        return json.loads(row[1])
    except (json.JSONDecodeError, TypeError):
        return None


# ────────────────────────────────────────────────────────────────────────


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


def get_previous_day_scan(current_scanned_at: str) -> Optional[dict]:
    """Get the most recent scan from a calendar day (ET) before the given scan timestamp."""
    from zoneinfo import ZoneInfo
    et = ZoneInfo("America/New_York")
    current_dt = datetime.fromisoformat(current_scanned_at.replace("Z", "+00:00"))
    current_date = current_dt.astimezone(et).date()

    conn = get_connection()
    rows = conn.execute(
        "SELECT id, scanned_at, regime, tickers, historical FROM scan_results ORDER BY id DESC LIMIT 50"
    ).fetchall()
    conn.close()

    for row in rows:
        scan_dt = datetime.fromisoformat(row[1].replace("Z", "+00:00"))
        scan_date = scan_dt.astimezone(et).date()
        if scan_date < current_date:
            return {
                "id": row[0],
                "scanned_at": row[1],
                "regime": json.loads(row[2]),
                "tickers": json.loads(row[3]),
                "historical": json.loads(row[4]),
            }
    return None


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


# ════════════════════════════════════════════════════════════════════════
# Theta Harvest v2 — silent data-layer writers/readers (Phase A)
# All additive. None of these are read by v1 or by the history automation.
# ════════════════════════════════════════════════════════════════════════

def store_daily_bars(rows) -> int:
    """Bulk upsert OHLCV bars. `rows`: iterable of
    (ticker, date, o, h, l, c, v, source, adj_flag, quarantine). Idempotent
    on (ticker, date) — safe to re-run backfills or re-persist a scan window."""
    rows = list(rows)
    if not rows:
        return 0
    conn = get_connection()
    conn.executemany(
        """
        INSERT INTO daily_bars (ticker, date, o, h, l, c, v, source, adj_flag, quarantine)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT (ticker, date) DO UPDATE SET
            o = excluded.o, h = excluded.h, l = excluded.l, c = excluded.c,
            v = excluded.v, source = excluded.source, adj_flag = excluded.adj_flag,
            quarantine = excluded.quarantine
        """,
        rows,
    )
    conn.commit()
    conn.close()
    return len(rows)


def get_bars(ticker: str, exclude_quarantined: bool = True) -> list[dict]:
    """Return a ticker's bars oldest→newest (chronological, for EWMA replay)."""
    conn = get_connection()
    q = "SELECT date, o, h, l, c, v FROM daily_bars WHERE ticker = ?"
    if exclude_quarantined:
        q += " AND quarantine = 0"
    q += " ORDER BY date ASC"
    rows = [
        {"date": r[0], "o": r[1], "h": r[2], "l": r[3], "c": r[4], "v": r[5]}
        for r in conn.execute(q, (ticker,))
    ]
    conn.close()
    return rows


def get_bars_coverage() -> dict:
    """Per-ticker bar coverage for the A1 backfill report."""
    conn = get_connection()
    rows = conn.execute(
        """
        SELECT ticker, MIN(date), MAX(date), COUNT(*),
               SUM(CASE WHEN quarantine = 1 THEN 1 ELSE 0 END)
        FROM daily_bars GROUP BY ticker ORDER BY ticker
        """
    ).fetchall()
    conn.close()
    return {
        r[0]: {"min": r[1], "max": r[2], "count": r[3], "quarantined": r[4] or 0}
        for r in rows
    }


def store_index_bars(rows) -> int:
    """Bulk upsert VIX-family index bars. `rows`: (symbol, date, o, h, l, c)."""
    rows = list(rows)
    if not rows:
        return 0
    conn = get_connection()
    conn.executemany(
        """
        INSERT INTO index_daily (symbol, date, o, h, l, c)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT (symbol, date) DO UPDATE SET
            o = excluded.o, h = excluded.h, l = excluded.l, c = excluded.c
        """,
        rows,
    )
    conn.commit()
    conn.close()
    return len(rows)


def get_index_bars(symbol: str) -> list[dict]:
    """Return an index symbol's bars oldest→newest."""
    conn = get_connection()
    rows = [
        {"date": r[0], "o": r[1], "h": r[2], "l": r[3], "c": r[4]}
        for r in conn.execute(
            "SELECT date, o, h, l, c FROM index_daily WHERE symbol = ? ORDER BY date ASC",
            (symbol,),
        )
    ]
    conn.close()
    return rows


# Whitelist of daily_iv columns the v2 writer may touch (prevents SQL injection
# via dynamic column names, and catches typos at the call site).
_V2_IV_COLS = frozenset({
    "v_gk", "s_neg", "s_pos", "ewma_v_1", "ewma_v_5", "ewma_v_25", "ewma_v_125",
    "ewma_sneg_5", "ewma_sneg_25", "vbar", "sigma_fwd", "sigma_fwd_dn",
    "fvrp_ratio", "fvrp_z", "slope_1m3m", "accel_dn", "global_factor",
    "transient_tag", "v2_gate_state", "v2_eligible", "v2_warm", "low_coverage",
    "legacy_signal_score", "legacy_recommendation", "legacy_regime",
    "legacy_vrp_ratio", "legacy_term_slope", "legacy_rv_accel",
})


def store_daily_iv_v2(ticker: str, as_of=None, **fields) -> int:
    """UPDATE v2/legacy columns on an existing daily_iv row.

    v1's store_daily_iv writes the row first (atm_iv NOT NULL), so this only
    UPDATEs — the two-phase live write (sign-local fields, then fvrp_z after
    the cross-ticker G_t) both land on the same (ticker, date) row. Returns
    rows affected (0 ⇒ no v1 row exists yet). Unknown keys raise."""
    d = (as_of or date.today())
    d = d.isoformat() if hasattr(d, "isoformat") else str(d)
    bad = [k for k in fields if k not in _V2_IV_COLS]
    if bad:
        raise ValueError(f"unknown daily_iv v2 columns: {bad}")
    cols = [k for k in fields if k in _V2_IV_COLS]
    if not cols:
        return 0
    set_clause = ", ".join(f"{c} = ?" for c in cols)
    vals = [fields[c] for c in cols] + [ticker, d]
    conn = get_connection()
    cur = conn.execute(
        f"UPDATE daily_iv SET {set_clause} WHERE ticker = ? AND date = ?", vals
    )
    conn.commit()
    n = cur.rowcount
    conn.close()
    return n


def get_fvrp_history(ticker: str, days: int = 252) -> list[float]:
    """Return the last `days` non-null FVRP ratios, oldest→newest — the trailing
    window for the FVRP z-score (theta_core.fvrp logs these internally)."""
    conn = get_connection()
    rows = [
        float(r[0])
        for r in conn.execute(
            """
            SELECT fvrp_ratio FROM daily_iv
            WHERE ticker = ? AND fvrp_ratio IS NOT NULL
            ORDER BY date DESC LIMIT ?
            """,
            (ticker, days),
        )
    ]
    conn.close()
    rows.reverse()
    return rows


def get_last_good_global_factor() -> Optional[float]:
    """Most recent global factor G_t from a NON-low-coverage day. Used to carry
    G_t forward on a thin-panel scan so a partial cross-section can't move the
    whole book (panel-coverage guard, spec A2 / master plan §A3)."""
    conn = get_connection()
    row = conn.execute(
        "SELECT global_factor FROM daily_iv "
        "WHERE global_factor IS NOT NULL AND (low_coverage IS NULL OR low_coverage = 0) "
        "ORDER BY date DESC LIMIT 1"
    ).fetchone()
    conn.close()
    return float(row[0]) if row and row[0] is not None else None


def store_gate_state(ticker: str, as_of, state: str, transient: bool = False,
                     pending: Optional[str] = None, pending_days: int = 0,
                     blackout: int = 0) -> None:
    """Upsert a per-ticker-per-date gate-state row (shadow replay in Phase A;
    the live transition machine extends this in Phase B)."""
    d = as_of.isoformat() if hasattr(as_of, "isoformat") else str(as_of)
    conn = get_connection()
    conn.execute(
        """
        INSERT INTO gate_state
            (ticker, date, state, transient, pending, pending_days, blackout, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT (ticker, date) DO UPDATE SET
            state = excluded.state, transient = excluded.transient,
            pending = excluded.pending, pending_days = excluded.pending_days,
            blackout = excluded.blackout, updated_at = excluded.updated_at
        """,
        (ticker, d, state, int(transient), pending, int(pending_days),
         int(blackout), datetime.now().isoformat()),
    )
    conn.commit()
    conn.close()


def get_latest_gate_state(ticker: str, before=None) -> Optional[dict]:
    """Most recent gate_state row for a ticker (optionally strictly before a
    date) — seeds the next state-machine transition."""
    conn = get_connection()
    if before is not None:
        b = before.isoformat() if hasattr(before, "isoformat") else str(before)
        row = conn.execute(
            "SELECT state, transient, pending, pending_days, blackout FROM gate_state "
            "WHERE ticker = ? AND date < ? ORDER BY date DESC LIMIT 1",
            (ticker, b),
        ).fetchone()
    else:
        row = conn.execute(
            "SELECT state, transient, pending, pending_days, blackout FROM gate_state "
            "WHERE ticker = ? ORDER BY date DESC LIMIT 1",
            (ticker,),
        ).fetchone()
    conn.close()
    if not row:
        return None
    return {"state": row[0], "transient": bool(row[1]), "pending": row[2],
            "pending_days": row[3], "blackout": row[4]}


def store_shadow_diff(rows) -> int:
    """Bulk upsert shadow-diff rows. Each row a dict with keys: date, ticker,
    is_etf, v1_action, v1_regime, v2_eligible, v2_gate_state, v2_transient,
    divergence_class, divergence_reason, v2_warm."""
    rows = list(rows)
    if not rows:
        return 0
    conn = get_connection()
    conn.executemany(
        """
        INSERT INTO shadow_diff
            (date, ticker, is_etf, v1_action, v1_regime, v2_eligible, v2_gate_state,
             v2_transient, divergence_class, divergence_reason, v2_warm)
        VALUES (:date, :ticker, :is_etf, :v1_action, :v1_regime, :v2_eligible,
                :v2_gate_state, :v2_transient, :divergence_class, :divergence_reason, :v2_warm)
        ON CONFLICT (date, ticker) DO UPDATE SET
            is_etf = excluded.is_etf, v1_action = excluded.v1_action,
            v1_regime = excluded.v1_regime, v2_eligible = excluded.v2_eligible,
            v2_gate_state = excluded.v2_gate_state, v2_transient = excluded.v2_transient,
            divergence_class = excluded.divergence_class,
            divergence_reason = excluded.divergence_reason, v2_warm = excluded.v2_warm
        """,
        rows,
    )
    conn.commit()
    conn.close()
    return len(rows)


def get_shadow_diffs(scan_date: Optional[str] = None,
                     divergence_class: Optional[str] = None,
                     sleeve: Optional[str] = None, warm_only: bool = False,
                     limit: int = 500) -> list[dict]:
    """Filtered shadow-diff rows joined to their daily_iv drivers (v1 vs v2),
    decision-changing classes first. Powers GET /api/shadow/diff."""
    q = """
        SELECT s.date, s.ticker, s.is_etf, s.v1_action, s.v1_regime, s.v2_eligible,
               s.v2_gate_state, s.v2_transient, s.divergence_class, s.divergence_reason,
               s.v2_warm, d.legacy_vrp_ratio, d.legacy_term_slope, d.legacy_rv_accel,
               d.fvrp_ratio, d.fvrp_z, d.slope_1m3m, d.accel_dn, d.sigma_fwd
        FROM shadow_diff s
        LEFT JOIN daily_iv d ON d.ticker = s.ticker AND d.date = s.date
        WHERE 1 = 1
    """
    params: list = []
    if scan_date:
        q += " AND s.date = ?"; params.append(scan_date)
    if divergence_class:
        q += " AND s.divergence_class = ?"; params.append(divergence_class)
    if sleeve == "index":
        q += " AND s.is_etf = 1"
    elif sleeve == "single":
        q += " AND s.is_etf = 0"
    if warm_only:
        q += " AND s.v2_warm = 1"
    q += (" ORDER BY s.date DESC, CASE s.divergence_class "
          "WHEN 'V2_STRICTER' THEN 0 WHEN 'V2_LOOSER' THEN 1 ELSE 2 END, "
          "s.v2_warm DESC, s.ticker LIMIT ?")
    params.append(limit)
    cols = ["date", "ticker", "is_etf", "v1_action", "v1_regime", "v2_eligible",
            "v2_gate_state", "v2_transient", "divergence_class", "divergence_reason",
            "v2_warm", "v1_vrp_ratio", "v1_term_slope", "v1_rv_accel",
            "fvrp_ratio", "fvrp_z", "slope_1m3m", "accel_dn", "sigma_fwd"]
    conn = get_connection()
    rows = [dict(zip(cols, r)) for r in conn.execute(q, params)]
    conn.close()
    return rows


def get_shadow_summary(window_days: int = 10) -> dict:
    """Aggregate shadow diffs over the last `window_days` distinct scan dates:
    agreement rate, divergence counts, the index-sleeve gating rate (v1 vs v2 —
    the G2 canary), gate-oscillation (v1 vs v2), and warm coverage. Powers
    GET /api/shadow/summary."""
    from collections import Counter
    conn = get_connection()
    dates = [r[0] for r in conn.execute(
        "SELECT DISTINCT date FROM shadow_diff ORDER BY date DESC LIMIT ?", (window_days,))]
    if not dates:
        conn.close()
        return {"n_ticker_days": 0, "n_warm": 0, "dates": [],
                "agreement_rate": None, "divergence_counts": {},
                "index_gating_rate_v1": None, "index_gating_rate_v2": None,
                "oscillation_v1": None, "oscillation_v2": None, "warm_coverage": None}
    ph = ",".join("?" * len(dates))
    diffs = conn.execute(
        f"SELECT is_etf, divergence_class, v2_eligible, v1_action, v2_warm "
        f"FROM shadow_diff WHERE date IN ({ph})", dates).fetchall()
    # Oscillation: mean per-ticker gate-state transitions over the window
    # (v1 = legacy_regime, v2 = v2_gate_state), read from daily_iv.
    seq = conn.execute(
        f"SELECT ticker, date, legacy_regime, v2_gate_state FROM daily_iv "
        f"WHERE date IN ({ph}) ORDER BY ticker, date ASC", dates).fetchall()
    conn.close()

    n = len(diffs)
    cls = Counter(r[1] for r in diffs)
    warm = sum(1 for r in diffs if r[4])
    idx = [r for r in diffs if r[0]]

    def _nonactionable_v1(a):
        return a not in ("SELL PREMIUM", "CONDITIONAL")

    idx_gate_v1 = (sum(1 for r in idx if _nonactionable_v1(r[3])) / len(idx)) if idx else None
    idx_gate_v2 = (sum(1 for r in idx if not r[2]) / len(idx)) if idx else None

    def _oscillation(col_idx):
        trans, tickers = 0, 0
        cur_ticker, prev = None, None
        counted = False
        for tkr, _d, v1r, v2r in seq:
            val = (v1r if col_idx == 2 else v2r)
            if tkr != cur_ticker:
                cur_ticker, prev, counted = tkr, val, False
                continue
            if val is not None and prev is not None and val != prev:
                trans += 1
            if not counted:
                tickers += 1
                counted = True
            prev = val
        return (trans / tickers) if tickers else None

    return {
        "n_ticker_days": n, "n_warm": warm, "dates": dates,
        "agreement_rate": (cls.get("AGREE", 0) / n) if n else None,
        "divergence_counts": dict(cls),
        "index_gating_rate_v1": idx_gate_v1,
        "index_gating_rate_v2": idx_gate_v2,
        "oscillation_v1": _oscillation(2),
        "oscillation_v2": _oscillation(3),
        "warm_coverage": (warm / n) if n else None,
    }


# Initialize on import
init_db()
