"""Backfill source: snapshot the production Lightsail SQLite over SSH and read past scans.

Used only when the Mac has missed days (the public API serves only the latest scan). The
prod DB is host-bind-mounted, so a plain `scp` of the file is sufficient — historical rows
are long-committed, and the only ever-uncommitted (WAL) data is the latest scan, which we
get from the API anyway, not from here. The local copy is opened read-only.
"""
from __future__ import annotations

import json
import sqlite3
import subprocess
from pathlib import Path

from .. import config
from .api_source import et_date


def snapshot_db() -> Path:
    """scp the prod DB to staging/snap.db and return its path. Raises on failure."""
    config.STAGING_DIR.mkdir(parents=True, exist_ok=True)
    dest = config.STAGING_DIR / "snap.db"
    rc = subprocess.run(
        ["scp", "-q", f"{config.SSH_ALIAS}:{config.REMOTE_DB}", str(dest)],
        capture_output=True, text=True, timeout=config.SSH_TIMEOUT,
    )
    if rc.returncode != 0:
        raise RuntimeError(f"scp of prod DB failed: {rc.stderr.strip()}")
    return dest


def _ro_conn(snap: Path) -> sqlite3.Connection:
    return sqlite3.connect(f"file:{snap}?mode=ro", uri=True)


def read_np_by_date(snap: Path, iso_date: str) -> dict | None:
    """Return the latest scan for the given ET date as {scanned_at, regime, tickers}, or None."""
    conn = _ro_conn(snap)
    try:
        rows = conn.execute(
            "SELECT scanned_at, regime, tickers FROM scan_results ORDER BY id DESC"
        ).fetchall()
    finally:
        conn.close()
    for scanned_at, regime, tickers in rows:  # DESC => first match is the latest scan that date
        if et_date(scanned_at).isoformat() == iso_date:
            return {"scanned_at": scanned_at, "regime": json.loads(regime), "tickers": json.loads(tickers)}
    return None


def read_cps_by_date(snap: Path, iso_date: str) -> dict | None:
    """Return the cached CPS response for the given scan_date (YYYY-MM-DD), or None."""
    conn = _ro_conn(snap)
    try:
        row = conn.execute(
            "SELECT response_json FROM cps_scan_responses WHERE scan_date = ?", (iso_date,)
        ).fetchone()
    finally:
        conn.close()
    return json.loads(row[0]) if row else None


# --- v2-shadow backfill (additive) ---------------------------------------------------
_SHADOW_COLS = ["date", "ticker", "is_etf", "v1_action", "v1_regime", "v2_eligible",
                "v2_gate_state", "v2_transient", "divergence_class", "divergence_reason",
                "v2_warm", "v1_vrp_ratio", "v1_term_slope", "v1_rv_accel",
                "fvrp_ratio", "fvrp_z", "slope_1m3m", "accel_dn", "sigma_fwd"]

# Replicates backend/database.py:get_shadow_diffs (same join + alias set), filtered to one date.
_SHADOW_QUERY = """
    SELECT s.date, s.ticker, s.is_etf, s.v1_action, s.v1_regime, s.v2_eligible,
           s.v2_gate_state, s.v2_transient, s.divergence_class, s.divergence_reason,
           s.v2_warm, d.legacy_vrp_ratio, d.legacy_term_slope, d.legacy_rv_accel,
           d.fvrp_ratio, d.fvrp_z, d.slope_1m3m, d.accel_dn, d.sigma_fwd
    FROM shadow_diff s
    LEFT JOIN daily_iv d ON d.ticker = s.ticker AND d.date = s.date
    WHERE s.date = ?
    ORDER BY CASE s.divergence_class
             WHEN 'V2_STRICTER' THEN 0 WHEN 'V2_LOOSER' THEN 1 ELSE 2 END,
             s.v2_warm DESC, s.ticker
"""


def _day_summary(rows: list[dict]) -> dict:
    """Per-day counterpart of backend/database.py:get_shadow_summary, computed from a single
    date's rows (oscillation needs a multi-day window, so it stays None on backfill)."""
    from collections import Counter
    n = len(rows)
    cls = Counter(r["divergence_class"] for r in rows)
    warm = sum(1 for r in rows if r["v2_warm"])
    idx = [r for r in rows if r["is_etf"]]

    def _nonactionable_v1(a):
        return a not in ("SELL PREMIUM", "CONDITIONAL")

    idx_v1 = (sum(1 for r in idx if _nonactionable_v1(r["v1_action"])) / len(idx)) if idx else None
    idx_v2 = (sum(1 for r in idx if not r["v2_eligible"]) / len(idx)) if idx else None
    return {
        "n_ticker_days": n, "n_warm": warm, "dates": [rows[0]["date"]] if rows else [],
        "agreement_rate": (cls.get("AGREE", 0) / n) if n else None,
        "divergence_counts": dict(cls),
        "index_gating_rate_v1": idx_v1, "index_gating_rate_v2": idx_v2,
        "oscillation_v1": None, "oscillation_v2": None,
        "warm_coverage": (warm / n) if n else None,
    }


def read_shadow_by_date(snap: Path, iso_date: str) -> dict | None:
    """Return {"rows": [...], "summary": {...per-day counts...}} for the given ET date, or None.

    Mirrors the API's /api/shadow/diff join against the read-only snapshot; the summary is the
    day's own counts (not a rolling window) so the shadow-diffs backfill entry is self-contained."""
    conn = _ro_conn(snap)
    try:
        rows = [dict(zip(_SHADOW_COLS, r)) for r in conn.execute(_SHADOW_QUERY, (iso_date,))]
    finally:
        conn.close()
    if not rows:
        return None
    return {"rows": rows, "summary": _day_summary(rows)}


# --- portfolio-eval book snapshot (additive) -----------------------------------------
def _mark_as_of(conn: sqlite3.Connection, position_id: int, iso_date: str) -> dict | None:
    """The latest position_marks row on or before iso_date (the mark the day's scan wrote,
    or a carried mark if that scan didn't reach the position). None if never marked."""
    row = conn.execute(
        "SELECT * FROM position_marks WHERE position_id = ? AND date <= ? "
        "ORDER BY date DESC LIMIT 1", (position_id, iso_date)).fetchone()
    if not row:
        return None
    cols = [c[1] for c in conn.execute("PRAGMA table_info(position_marks)")]
    return dict(zip(cols, row))


def read_book_by_date(snap: Path, iso_date: str) -> dict | None:
    """Read the journal book AS OF a given ET date from the read-only snapshot.

    Mirrors positions_api's open-book shape without the API/token: for every position that was
    live on iso_date (entry_date <= date < close, or never closed), attach its latest mark
    (on-or-before iso_date) and its parsed entry checklist. Positions CLOSED on iso_date are
    returned separately for the closed-trade post-mortem note.

    Returns {"date", "open": [...], "closed_today": [...]}, or None when the snapshot has no
    `positions` table (a pre-journal DB). An EMPTY open book is a valid non-None result — the
    orchestrator decides to SKIP the entry; this reader never guesses.
    """
    conn = _ro_conn(snap)
    try:
        tables = {r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'")}
        if "positions" not in tables:
            return None
        pcols = [c[1] for c in conn.execute("PRAGMA table_info(positions)")]
        prows = [dict(zip(pcols, r)) for r in conn.execute("SELECT * FROM positions")]

        open_book, closed_today = [], []
        for p in prows:
            entry_d = p.get("entry_date")
            close_d = p.get("close_date")
            if entry_d and entry_d > iso_date:
                continue  # not entered yet on this date
            try:
                p["checklist"] = json.loads(p.get("checklist_json") or "{}")
            except (ValueError, TypeError):
                p["checklist"] = {}
            if close_d and close_d == iso_date:
                closed_today.append(p)
            elif close_d is None or close_d > iso_date:
                p["mark"] = _mark_as_of(conn, p["id"], iso_date)
                open_book.append(p)
    finally:
        conn.close()
    open_book.sort(key=lambda p: p.get("ticker") or "")
    return {"date": iso_date, "open": open_book, "closed_today": closed_today}
