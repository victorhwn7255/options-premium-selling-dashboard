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


_CAPTURE_PREFILTER_DAYS = 29   # mirrors backend/capture.py — rows dated <= D-29 are resolved by D


def _capture_summary_by_date(conn, iso_date: str, window: int = 60) -> dict:
    """Backfill counterpart of backend/database.py:get_capture_summary for a past date D: the
    last `window` resolved dates <= D-29 (a deterministic as-of rule — the columns are filled
    later, so `capture_resolved_at` cannot be used). Returns {} when the snapshot predates WS2a
    (no capture_30d column) or nothing is resolved, so the summary segment is simply omitted."""
    import math
    from datetime import date as _date, timedelta as _td
    cols = {r[1] for r in conn.execute("PRAGMA table_info(daily_iv)")}
    if "capture_30d" not in cols:
        return {}
    cutoff = (_date.fromisoformat(iso_date) - _td(days=_CAPTURE_PREFILTER_DAYS)).isoformat()
    dates = [r[0] for r in conn.execute(
        "SELECT DISTINCT date FROM daily_iv WHERE capture_30d IS NOT NULL AND date <= ? "
        "ORDER BY date DESC LIMIT ?", (cutoff, int(window)))]
    if not dates:
        return {}
    ph = ",".join("?" * len(dates))
    names = ("cap", "rvcc", "rvgk", "sf", "rv30", "rec", "elig", "warm")
    rows = [dict(zip(names, r)) for r in conn.execute(
        f"SELECT capture_30d, rv_fwd_21_cc, rv_fwd_21, sigma_fwd, rv30, legacy_recommendation, "
        f"v2_eligible, v2_warm FROM daily_iv WHERE date IN ({ph}) AND capture_30d IS NOT NULL", dates)]

    def mean(xs):
        xs = [x for x in xs if x is not None]
        return (sum(xs) / len(xs)) if xs else None

    def neg_rate(xs):
        xs = [x for x in xs if x is not None]
        return (sum(1 for x in xs if x < 0) / len(xs)) if xs else None

    def log_mae(pairs):
        v = [abs(math.log(a / b)) for a, b in pairs if a and b and a > 0 and b > 0]
        return (sum(v) / len(v)) if v else None

    actionable = ("SELL PREMIUM", "CONDITIONAL")
    v1 = [r for r in rows if r["rec"] is not None]
    v2 = [r for r in rows if r["elig"] is not None]
    v2w = [r for r in v2 if r["warm"]]
    return {
        "capture_n_resolved": len(rows), "capture_window_resolved": int(window),
        "capture_window_dates": dates,
        "capture_mean_all": mean(r["cap"] for r in rows),
        "capture_mean_v1_actionable": mean(r["cap"] for r in v1 if r["rec"] in actionable),
        "capture_mean_v2_eligible": mean(r["cap"] for r in v2 if r["elig"]),
        "capture_mean_v2_eligible_warm": mean(r["cap"] for r in v2w if r["elig"]),
        "capture_neg_rate_v1_gated": neg_rate(r["cap"] for r in v1 if r["rec"] not in actionable),
        "capture_neg_rate_v1_cleared": neg_rate(r["cap"] for r in v1 if r["rec"] in actionable),
        "capture_neg_rate_v2_vetoed": neg_rate(r["cap"] for r in v2 if not r["elig"]),
        "capture_neg_rate_v2_cleared": neg_rate(r["cap"] for r in v2 if r["elig"]),
        "capture_neg_rate_v2_vetoed_warm": neg_rate(r["cap"] for r in v2w if not r["elig"]),
        "capture_neg_rate_v2_cleared_warm": neg_rate(r["cap"] for r in v2w if r["elig"]),
        "sigma_fwd_log_mae": log_mae((r["sf"], r["rvcc"]) for r in rows),
        "rv30_log_mae": log_mae(((r["rv30"] / 100.0) if r["rv30"] else None, r["rvcc"]) for r in rows),
        "sigma_fwd_log_mae_gk": log_mae((r["sf"], r["rvgk"]) for r in rows),
    }


def read_shadow_by_date(snap: Path, iso_date: str) -> dict | None:
    """Return {"rows": [...], "summary": {...per-day counts...}} for the given ET date, or None.

    Mirrors the API's /api/shadow/diff join against the read-only snapshot; the summary is the
    day's own counts (not a rolling window) so the shadow-diffs backfill entry is self-contained.
    Since WS2a it also carries the forward-capture aggregates as of that date (additive)."""
    conn = _ro_conn(snap)
    try:
        rows = [dict(zip(_SHADOW_COLS, r)) for r in conn.execute(_SHADOW_QUERY, (iso_date,))]
        capture = _capture_summary_by_date(conn, iso_date) if rows else {}
        veto = _veto_summary_by_date(conn, iso_date) if rows else {}
    finally:
        conn.close()
    if not rows:
        return None
    summary = _day_summary(rows)
    summary.update(capture)
    summary.update(veto)
    return {"rows": rows, "summary": summary}


def _veto_summary_by_date(conn, iso_date: str) -> dict:
    """WS4 backfill counterpart of backend/database.py:get_veto_summary for one date (the day's
    own rows, like _day_summary). {} when the snapshot predates WS4 or nothing is populated."""
    cols = {r[1] for r in conn.execute("PRAGMA table_info(daily_iv)")}
    if "veto_disagree" not in cols:
        return {}
    n, k = conn.execute("SELECT COUNT(veto_disagree), COALESCE(SUM(veto_disagree), 0) FROM daily_iv "
                        "WHERE date = ? AND veto_disagree IS NOT NULL", (iso_date,)).fetchone()
    if not n:
        return {}
    return {"veto_disagree_rate": k / n, "veto_disagree_n": int(n)}


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
