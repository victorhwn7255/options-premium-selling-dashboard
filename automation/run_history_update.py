"""Orchestrator: append missing daily entries to the three history files.

Capture-before-Claude: the deterministic data (metrics table + CPS snapshot) is written
first; the briefing prose (Claude) comes after, so a Claude failure never loses data.
Self-healing: backfills every missing trading day since the most-behind file.

CLI (run from repo root):
    python3 -m automation.run_history_update [--dry-run] [--no-claude] [--verbose]
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import date, datetime, timedelta

from . import config
from .history import parser, writer
from .render.cps_snapshot import render_cps_snapshot
from .render.np_table import render_np_table
from .render.statpack import compute_statpack
from .sources import api_source, db_source
from .sources.trading_calendar import is_trading_day, trading_days_between


# --------------------------------------------------------------------------- helpers
def _stamp() -> str:
    return datetime.now(config.ET).strftime("%Y-%m-%d %H:%M:%S ET")


def _log(msg: str, *, verbose: bool = True) -> None:
    line = f"[{_stamp()}] {msg}"
    if verbose:
        print(line)
    try:
        config.LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with config.LOG_FILE.open("a") as f:
            f.write(line + "\n")
    except OSError:
        pass


def _notify(title: str, message: str) -> None:
    """Best-effort macOS notification (used for auth-failure alerts)."""
    try:
        subprocess.run(
            ["osascript", "-e", f'display notification {json.dumps(message)} with title {json.dumps(title)}'],
            capture_output=True, timeout=10,
        )
    except Exception:  # noqa: BLE001
        pass


def _heading(d: date) -> str:
    return f"## {d.isoformat()} ({d.strftime('%A')})"


def _prev_trading_day(d: date) -> date:
    cur = d - timedelta(days=1)
    while not is_trading_day(cur):
        cur -= timedelta(days=1)
    return cur


def _write_staging(iso: str, np_raw: dict, cps_raw: dict | None, statpack: dict) -> None:
    config.STAGING_DIR.mkdir(parents=True, exist_ok=True)
    (config.STAGING_DIR / f"{iso}.json").write_text(
        json.dumps({"np": np_raw, "cps": cps_raw, "statpack": statpack})
    )


# ------------------------------------------------------------------------------ core
def run(
    *,
    metrics_path,
    cps_path,
    briefings_path,
    api_date: date,
    np_latest: dict,
    cps_latest: dict | None,
    load_backfill,                 # (date) -> (np_raw|None, cps_raw|None)
    dry_run: bool = False,
    no_claude: bool = False,
    verbose: bool = True,
    briefing_fn=None,              # (d, statpack, np_table, cps_block, recent) -> body  (injectable)
    notable_fn=None,              # (d, statpack, cps_block, recent) -> notable        (injectable)
) -> dict:
    """Process every trading day from the most-behind file up to api_date. Returns a summary."""
    from .claude.runner import ClaudeAuthError
    if briefing_fn is None or notable_fn is None:
        from .claude import runner as _r
        briefing_fn = briefing_fn or _r.run_briefing
        notable_fn = notable_fn or _r.run_cps_notable

    last_dates = [parser.last_logged_date(p) for p in (metrics_path, cps_path, briefings_path)]
    present = [d for d in last_dates if d is not None]
    if not present:
        raise RuntimeError("no existing history entries to anchor from")
    anchor = min(present)

    # A day is "done" once metrics + briefing exist (CPS is best-effort, never blocks).
    candidates = trading_days_between(anchor, api_date)
    todo = [
        d for d in candidates
        if not (parser.has_entry(metrics_path, d.isoformat())
                and parser.has_entry(briefings_path, d.isoformat()))
    ]
    summary = {"anchor": anchor.isoformat(), "api_date": api_date.isoformat(),
               "todo": [d.isoformat() for d in todo], "metrics_written": [], "cps_written": [],
               "briefings_written": [], "notables_written": [], "briefings_pending": [],
               "skipped": []}
    claude_on = not (no_claude or dry_run)
    claude_ok = True  # flipped off on an auth failure so we stop retrying mid-run

    if not todo:
        _log("up to date — nothing to do", verbose=verbose)
        return summary

    _log(f"anchor={anchor} api_date={api_date} todo={[d.isoformat() for d in todo]}", verbose=verbose)

    for d in todo:  # oldest -> newest (continuity for day-over-day + briefing context)
        iso = d.isoformat()
        if d == api_date:
            np_raw, cps_raw = np_latest, cps_latest
        elif d < api_date:
            np_raw, cps_raw = load_backfill(d)
        else:
            np_raw, cps_raw = None, None

        if not np_raw or len(np_raw.get("tickers", [])) < config.MIN_TICKERS:
            n = 0 if not np_raw else len(np_raw.get("tickers", []))
            _log(f"SKIP {iso}: no/partial NP data ({n} tickers)", verbose=verbose)
            summary["skipped"].append(iso)
            continue

        np_table_md = render_np_table(np_raw["tickers"])
        cps_block_md = render_cps_snapshot(cps_raw) if cps_raw else None

        # --- CAPTURE (deterministic, before Claude) ---
        if not parser.has_entry(metrics_path, iso):
            if not dry_run:
                writer.insert_entry(metrics_path, iso, _heading(d) + "\n\n" + np_table_md)
            _log(f"{'(dry) ' if dry_run else ''}wrote metrics-logs {iso}", verbose=verbose)
            summary["metrics_written"].append(iso)

        if cps_block_md and not parser.has_entry(cps_path, iso):
            if not dry_run:
                writer.insert_entry(cps_path, iso, _heading(d) + "\n\n" + cps_block_md)
            _log(f"{'(dry) ' if dry_run else ''}wrote credit-put-spreads {iso}", verbose=verbose)
            summary["cps_written"].append(iso)
        elif not cps_raw:
            _log(f"NOTE {iso}: no CPS data (>{config.CPS_BACKFILL_LIMIT}d window) — CPS skipped",
                 verbose=verbose)

        # --- stat-pack (verified numbers for the briefing) ---
        prior = parser.parse_np_table(metrics_path, _prev_trading_day(d).isoformat())
        statpack = compute_statpack(np_raw["tickers"], prior)
        if not dry_run:
            _write_staging(iso, np_raw, cps_raw, statpack)

        # --- ANALYZE (Claude, Max subscription) — capture above already guarantees no data loss ---
        if not parser.has_entry(briefings_path, iso):
            if claude_on and claude_ok:
                try:
                    body = briefing_fn(d, statpack, np_table_md, cps_block_md or "",
                                       parser.latest_entries(briefings_path, 7))
                    writer.insert_entry(briefings_path, iso, _heading(d) + "\n\n" + body)
                    summary["briefings_written"].append(iso)
                    _log(f"wrote daily-briefings {iso}", verbose=verbose)
                except ClaudeAuthError as e:
                    claude_ok = False
                    summary["briefings_pending"].append(iso)
                    _log(f"⚠️ Claude re-login needed — briefing {iso} pending: {e}", verbose=verbose)
                    _notify("Theta Harvest: Claude re-login needed",
                            "Run `claude` to re-auth; briefings will backfill next run.")
                except Exception as e:  # noqa: BLE001 — never let prose failure crash the run
                    summary["briefings_pending"].append(iso)
                    _log(f"briefing {iso} failed ({e}) — data captured, briefing pending", verbose=verbose)
            else:
                summary["briefings_pending"].append(iso)
                _log(f"briefing {iso} pending ({'dry-run' if dry_run else '--no-claude' if no_claude else 'claude-disabled'})",
                     verbose=verbose)

        # --- CPS Notable (Claude) — appended to the already-written CPS entry ---
        if claude_on and claude_ok and cps_block_md and parser.has_entry(cps_path, iso):
            et = parser.entry_text(cps_path, iso) or ""
            if "**Notable:**" not in et:
                try:
                    notable = notable_fn(d, statpack, cps_block_md, parser.latest_entries(cps_path, 5))
                    writer.append_to_entry(cps_path, iso, f"**Notable:** {notable}")
                    summary["notables_written"].append(iso)
                    _log(f"wrote CPS Notable {iso}", verbose=verbose)
                except ClaudeAuthError as e:
                    claude_ok = False
                    _log(f"⚠️ Claude re-login needed — CPS Notable {iso} pending: {e}", verbose=verbose)
                except Exception as e:  # noqa: BLE001
                    _log(f"CPS Notable {iso} failed ({e}) — table written, notable pending", verbose=verbose)

    return summary


# ------------------------------------------------------------------------------ main
def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Append missing daily entries to history files.")
    ap.add_argument("--dry-run", action="store_true", help="render + validate, write nothing")
    ap.add_argument("--no-claude", action="store_true", help="skip the briefing (deterministic only)")
    ap.add_argument("--shadow", action="store_true",
                    help="write to a scratch copy (staging/shadow/) re-seeded from real history, "
                         "for Phase-6 validation — never touches the real history files")
    ap.add_argument("--quiet", action="store_true", help="log to file only, not stdout")
    args = ap.parse_args(argv)
    verbose = not args.quiet

    if args.shadow:
        config.SHADOW_DIR.mkdir(parents=True, exist_ok=True)
        for src in (config.METRICS_FILE, config.CPS_FILE, config.BRIEFINGS_FILE):
            __import__("shutil").copy(src, config.SHADOW_DIR / src.name)  # re-seed from real each run
        metrics_file = config.SHADOW_DIR / config.METRICS_FILE.name
        cps_file = config.SHADOW_DIR / config.CPS_FILE.name
        briefings_file = config.SHADOW_DIR / config.BRIEFINGS_FILE.name
        _log("SHADOW mode — writing to staging/shadow/ (real history untouched)", verbose=verbose)
    else:
        metrics_file, cps_file, briefings_file = (
            config.METRICS_FILE, config.CPS_FILE, config.BRIEFINGS_FILE)

    np_latest = api_source.fetch_latest_np()
    cps_latest = api_source.fetch_latest_cps()
    api_date = api_source.et_date(np_latest["scanned_at"])

    # Snapshot the prod DB only if backfill is actually needed.
    last_dates = [parser.last_logged_date(p) for p in (metrics_file, cps_file, briefings_file)]
    anchor = min(d for d in last_dates if d is not None)
    need_backfill = any(d < api_date for d in trading_days_between(anchor, api_date)
                        if not (parser.has_entry(metrics_file, d.isoformat())
                                and parser.has_entry(briefings_file, d.isoformat())))
    snap = db_source.snapshot_db() if need_backfill else None

    def load_backfill(d: date):
        if snap is None:
            return None, None
        return (db_source.read_np_by_date(snap, d.isoformat()),
                db_source.read_cps_by_date(snap, d.isoformat()))

    summary = run(
        metrics_path=metrics_file,
        cps_path=cps_file,
        briefings_path=briefings_file,
        api_date=api_date,
        np_latest=np_latest,
        cps_latest=cps_latest,
        load_backfill=load_backfill,
        dry_run=args.dry_run,
        no_claude=args.no_claude,
        verbose=verbose,
    )
    _log(f"done: {json.dumps(summary)}", verbose=verbose)
    return 0


if __name__ == "__main__":
    sys.exit(main())
