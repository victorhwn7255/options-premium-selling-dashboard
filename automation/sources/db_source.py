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
