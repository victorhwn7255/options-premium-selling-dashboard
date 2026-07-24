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
import re
import subprocess
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

from . import config
from .history import parser, writer
from .render.cps_snapshot import render_cps_snapshot
from .render.np_table import render_np_table
from .render.portfolio_eval import build_book_context, render_portfolio_header
from .render.shadow_table import compute_day_flips, render_shadow_snapshot, shadow_summary_line
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


def _portfolio_eval_pass(*, portfolio_evals_path, api_date, read_book_fn, scan_rows_fn,
                         eval_fn, summary, dry_run, claude_on, claude_ok, verbose) -> bool:
    """Capture + write the daily portfolio-eval entry(ies). Returns the (possibly flipped-off)
    claude_ok. Two phases, both idempotent + best-effort:

      1. CAPTURE — for every new trading day up to api_date not yet logged, read the book from
         the snapshot; empty book -> SKIP (no entry); else write the deterministic header.
      2. PROSE  — for every recent entry that has a header but no `**Assessment:**` (today's just-
         captured one, or a prior day whose Claude call failed), reconstruct the inputs from the
         snapshot and append the Claude prose. Oldest-first so append-in-place keeps order.

    A snapshot miss (read_book_fn -> None) skips the day this run; it self-heals next run.
    """
    from .claude.runner import ClaudeAuthError

    # -- phase 1: capture the deterministic header for new trading days --
    last_eval = parser.last_logged_date(portfolio_evals_path)
    if last_eval is None:
        new_days = [api_date]
    else:
        new_days = trading_days_between(last_eval, api_date)  # (last_eval, api_date]
    for d in new_days:
        iso = d.isoformat()
        if parser.has_entry(portfolio_evals_path, iso):
            continue  # idempotent
        book = read_book_fn(iso)
        if book is None:
            _log(f"portfolio-eval {iso}: no book snapshot — skipped this run (self-heals next run)",
                 verbose=verbose)
            continue
        if not book.get("open"):
            summary["portfolio_eval_skipped"].append(iso)
            _log(f"portfolio-eval {iso}: empty book — no entry (skip)", verbose=verbose)
            continue
        header = render_portfolio_header(book, scan_rows_fn(iso) or {}, iso)
        if not dry_run:
            writer.insert_entry(portfolio_evals_path, iso, _heading(d) + "\n\n" + header)
        summary["portfolio_eval_captured"].append(iso)
        _log(f"{'(dry) ' if dry_run else ''}wrote portfolio-evals {iso} (header capture)",
             verbose=verbose)

    # -- phase 2: append Claude prose to any recent header-only entry --
    if not (claude_on and claude_ok) or dry_run:
        return claude_ok
    try:
        recent = re.findall(r"^##\s+(\d{4}-\d{2}-\d{2})\b",
                            Path(portfolio_evals_path).read_text(), re.M)[:5]
    except OSError:
        recent = []
    for iso in reversed(recent):  # oldest -> newest
        et = parser.entry_text(portfolio_evals_path, iso) or ""
        if "**Assessment:**" in et:
            continue
        book = read_book_fn(iso)
        if not book or not book.get("open"):
            continue
        scan_by_ticker = scan_rows_fn(iso) or {}
        header = render_portfolio_header(book, scan_by_ticker, iso)
        book_ctx = build_book_context(book, scan_by_ticker, iso)
        try:
            d2 = date.fromisoformat(iso)
            prose = eval_fn(d2, header, book_ctx,
                            parser.latest_entries(portfolio_evals_path, 5))
            writer.append_to_entry(portfolio_evals_path, iso, f"**Assessment:** {prose}")
            summary["portfolio_eval_written"].append(iso)
            _log(f"wrote portfolio-eval prose {iso}", verbose=verbose)
        except ClaudeAuthError as e:
            claude_ok = False
            _log(f"⚠️ Claude re-login needed — portfolio-eval {iso} pending: {e}", verbose=verbose)
            break
        except Exception as e:  # noqa: BLE001 — prose failure never blocks; header already captured
            _log(f"portfolio-eval prose {iso} failed ({e}) — header captured, prose pending",
                 verbose=verbose)
    return claude_ok


# ------------------------------------------------------------------------------ core
def run(
    *,
    metrics_path,
    cps_path,
    briefings_path,
    api_date: date,
    np_latest: dict,
    cps_latest: dict | None,
    load_backfill,                 # (date) -> (np_raw|None, cps_raw|None[, shadow_raw|None])
    dry_run: bool = False,
    no_claude: bool = False,
    verbose: bool = True,
    briefing_fn=None,              # (d, statpack, np_table, cps_block, recent) -> body  (injectable)
    notable_fn=None,              # (d, statpack, cps_block, recent) -> notable        (injectable)
    shadow_diffs_path=None,        # v2 deterministic sister log (additive, best-effort)
    v2_briefings_path=None,        # v2 Claude sister log (additive, best-effort)
    shadow_latest: dict | None = None,  # {"rows": [...], "summary": {...}} for api_date, or None
    v2_briefing_fn=None,           # (d, summary_line, shadow_table, summary_json, recent) -> body
    prev_shadow_rows_fn=None,      # (iso_date) -> rows|None — prior-day rows for day-flips (best-effort)
    portfolio_evals_path=None,     # portfolio-eval Claude sister log (additive, best-effort)
    read_book_fn=None,             # (iso_date) -> book dict|None (open+closed_today from the DB snapshot)
    scan_rows_fn=None,             # (iso_date) -> {ticker: scan_row} — the day's "what the system thinks now"
    portfolio_eval_fn=None,        # (d, header, book_ctx, recent) -> prose  (injectable)
) -> dict:
    """Process every trading day from the most-behind file up to api_date. Returns a summary."""
    from .claude.runner import ClaudeAuthError
    if briefing_fn is None or notable_fn is None:
        from .claude import runner as _r
        briefing_fn = briefing_fn or _r.run_briefing
        notable_fn = notable_fn or _r.run_cps_notable
    if v2_briefing_fn is None:
        from .claude import runner as _r2
        v2_briefing_fn = _r2.run_v2_briefing
    if portfolio_eval_fn is None:
        from .claude import runner as _r3
        portfolio_eval_fn = _r3.run_portfolio_eval

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
               "shadow_written": [], "v2_briefing_written": [],
               "portfolio_eval_captured": [], "portfolio_eval_written": [],
               "portfolio_eval_skipped": [], "skipped": []}
    claude_on = not (no_claude or dry_run)
    claude_ok = True  # flipped off on an auth failure so we stop retrying mid-run

    # --- v2-BRIEFING SELF-HEAL (best-effort; runs even on nothing-to-do days) ---
    # A v2-only Claude failure leaves the day "done" (the done-gate is metrics +
    # v1-briefing), so the main loop never revisits it (2026-07-21 timeout). Any
    # recent shadow-diffs entry missing its v2-briefings twin is regenerated here,
    # reconstructing the inputs from the logged deterministic entry itself.
    # Oldest-first + newer-than-current-top so insert_entry (always splices at the
    # top) preserves descending order; an older mid-file gap is logged, not forced.
    if (claude_on and claude_ok and shadow_diffs_path is not None
            and v2_briefings_path is not None):
        try:
            shadow_dates = re.findall(r"^##\s+(\d{4}-\d{2}-\d{2})\b",
                                      Path(shadow_diffs_path).read_text(), re.M)[:5]
        except OSError:
            shadow_dates = []
        v2_top = parser.last_logged_date(v2_briefings_path)
        for iso in reversed(shadow_dates):  # oldest -> newest
            if parser.has_entry(v2_briefings_path, iso):
                continue
            if v2_top and date.fromisoformat(iso) < v2_top:
                _log(f"v2-briefing {iso} missing below the newest entry — manual backfill needed",
                     verbose=verbose)
                continue
            try:
                et = parser.entry_text(shadow_diffs_path, iso) or ""
                body = et.split("\n", 1)[1].strip() if "\n" in et else ""
                line = next((ln for ln in body.splitlines()
                             if ln.startswith("**Shadow summary:**")), None)
                if not line:
                    continue
                d2 = date.fromisoformat(iso)
                out = v2_briefing_fn(d2, line, body,
                                     "(unavailable — self-healed from the logged shadow table)",
                                     parser.latest_entries(v2_briefings_path, 5))
                writer.insert_entry(v2_briefings_path, iso, _heading(d2) + "\n\n" + out)
                summary["v2_briefing_written"].append(iso)
                v2_top = d2
                _log(f"wrote v2-briefings {iso} (self-heal)", verbose=verbose)
            except ClaudeAuthError as e:
                claude_ok = False
                _log(f"⚠️ Claude re-login needed — v2-briefing self-heal {iso} pending: {e}",
                     verbose=verbose)
                break
            except Exception as e:  # noqa: BLE001 — self-heal never blocks the run
                _log(f"v2-briefing self-heal {iso} failed ({e}) — still pending", verbose=verbose)

    # --- PORTFOLIO EVAL (best-effort sister log; NEVER gates v1) ---
    # A daily behavioural review of the OPEN journal book, read from the prod-DB snapshot
    # (positions + position_marks the 18:30 scan wrote). Runs every day (even nothing-to-do
    # days — the book state moves daily), before the v1 todo gate. Capture-before-Claude:
    # the deterministic header is written first, prose appended second; empty book -> no entry.
    # Fully isolated: any failure here never touches the v1 history.
    if portfolio_evals_path is not None and read_book_fn is not None:
        try:
            claude_ok = _portfolio_eval_pass(
                portfolio_evals_path=portfolio_evals_path, api_date=api_date,
                read_book_fn=read_book_fn, scan_rows_fn=scan_rows_fn or (lambda _iso: {}),
                eval_fn=portfolio_eval_fn, summary=summary, dry_run=dry_run,
                claude_on=claude_on, claude_ok=claude_ok, verbose=verbose)
        except Exception as e:  # noqa: BLE001 — the whole pass is best-effort; v1 unaffected
            _log(f"portfolio-eval pass failed ({e}) — v1 history unaffected", verbose=verbose)

    if not todo:
        _log("up to date — nothing to do", verbose=verbose)
        return summary

    _log(f"anchor={anchor} api_date={api_date} todo={[d.isoformat() for d in todo]}", verbose=verbose)

    for d in todo:  # oldest -> newest (continuity for day-over-day + briefing context)
        iso = d.isoformat()
        if d == api_date:
            np_raw, cps_raw = np_latest, cps_latest
            shadow_raw = shadow_latest
        elif d < api_date:
            bf = load_backfill(d)
            np_raw, cps_raw = bf[0], bf[1]
            shadow_raw = bf[2] if len(bf) > 2 else None  # tolerate legacy 2-tuple backfills
        else:
            np_raw, cps_raw, shadow_raw = None, None, None

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

        # --- SHADOW CAPTURE (deterministic v2 sister log; best-effort — NEVER gates v1) ---
        shadow_block_md = None
        shadow_flips = None
        if shadow_diffs_path is not None and shadow_raw:
            try:
                # Earnings DTE rides in from the same day's NP payload (shadow_diff rows lack it) —
                # the v1-UI reality check for the earnings window (added 2026-07-15).
                earn_map = {t.get("ticker"): t.get("earnings_dte")
                            for t in np_raw.get("tickers", [])}
                if prev_shadow_rows_fn is not None:
                    try:  # day-flips: true day-over-day churn vs the prior trading day
                        shadow_flips = compute_day_flips(
                            shadow_raw.get("rows") or [],
                            prev_shadow_rows_fn(_prev_trading_day(d).isoformat()))
                    except Exception:  # noqa: BLE001 — churn segment is optional, never blocks
                        shadow_flips = None
                shadow_block_md = render_shadow_snapshot(
                    shadow_raw.get("rows") or [], shadow_raw.get("summary"),
                    earnings_by_ticker=earn_map, flips=shadow_flips)
            except Exception as e:  # noqa: BLE001 — a render failure must not touch v1 history
                _log(f"shadow-diffs render {iso} failed ({e}) — v1 history unaffected", verbose=verbose)
            if shadow_block_md and not parser.has_entry(shadow_diffs_path, iso):
                try:
                    if not dry_run:
                        writer.insert_entry(shadow_diffs_path, iso, _heading(d) + "\n\n" + shadow_block_md)
                    _log(f"{'(dry) ' if dry_run else ''}wrote shadow-diffs {iso}", verbose=verbose)
                    summary["shadow_written"].append(iso)
                except Exception as e:  # noqa: BLE001
                    _log(f"shadow-diffs write {iso} failed ({e}) — v1 history unaffected", verbose=verbose)

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

        # --- v2 SHADOW BRIEFING (Claude) — best-effort sister log; NEVER gates v1 ---
        if (claude_on and claude_ok and v2_briefings_path is not None and shadow_block_md
                and not parser.has_entry(v2_briefings_path, iso)):
            try:
                # Same (summary, flips) inputs as the logged table -> byte-identical line, so the
                # briefing's verbatim-first-line contract holds.
                summary_line = shadow_summary_line(shadow_raw.get("summary"), shadow_flips)
                body = v2_briefing_fn(d, summary_line, shadow_block_md,
                                      shadow_raw.get("summary") or {},
                                      parser.latest_entries(v2_briefings_path, 5))
                writer.insert_entry(v2_briefings_path, iso, _heading(d) + "\n\n" + body)
                summary["v2_briefing_written"].append(iso)
                _log(f"wrote v2-briefings {iso}", verbose=verbose)
            except ClaudeAuthError as e:
                claude_ok = False
                _log(f"⚠️ Claude re-login needed — v2-briefing {iso} pending: {e}", verbose=verbose)
            except Exception as e:  # noqa: BLE001 — prose failure never crashes the run
                _log(f"v2-briefing {iso} failed ({e}) — shadow table written, briefing pending", verbose=verbose)

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
        for src in (config.METRICS_FILE, config.CPS_FILE, config.BRIEFINGS_FILE,
                    config.SHADOW_DIFFS_FILE, config.V2_BRIEFINGS_FILE, config.PORTFOLIO_EVALS_FILE):
            __import__("shutil").copy(src, config.SHADOW_DIR / src.name)  # re-seed from real each run
        metrics_file = config.SHADOW_DIR / config.METRICS_FILE.name
        cps_file = config.SHADOW_DIR / config.CPS_FILE.name
        briefings_file = config.SHADOW_DIR / config.BRIEFINGS_FILE.name
        shadow_diffs_file = config.SHADOW_DIR / config.SHADOW_DIFFS_FILE.name
        v2_briefings_file = config.SHADOW_DIR / config.V2_BRIEFINGS_FILE.name
        portfolio_evals_file = config.SHADOW_DIR / config.PORTFOLIO_EVALS_FILE.name
        _log("SHADOW mode — writing to staging/shadow/ (real history untouched)", verbose=verbose)
    else:
        metrics_file, cps_file, briefings_file = (
            config.METRICS_FILE, config.CPS_FILE, config.BRIEFINGS_FILE)
        shadow_diffs_file, v2_briefings_file = config.SHADOW_DIFFS_FILE, config.V2_BRIEFINGS_FILE
        portfolio_evals_file = config.PORTFOLIO_EVALS_FILE

    np_latest = api_source.fetch_latest_np()
    cps_latest = api_source.fetch_latest_cps()
    api_date = api_source.et_date(np_latest["scanned_at"])

    # v2 shadow surface (additive, best-effort): a fetch failure must not block the v1 history.
    try:
        shadow_latest = api_source.fetch_latest_shadow(api_date.isoformat())
    except Exception as e:  # noqa: BLE001
        shadow_latest = None
        _log(f"shadow fetch failed ({e}) — continuing without v2 shadow log", verbose=verbose)

    # Snapshot the prod DB. Needed for (a) past-day backfill AND (b) the portfolio-eval book,
    # which reads positions + position_marks from the snapshot EVERY run (not just backfill days)
    # — so the snapshot is now taken every run rather than gated on need_backfill.
    # Guarded: by here today's NP/CPS/shadow data is already in hand — an scp blip (the same
    # wake-race the API fetches retry) must not crash the run and discard today's capture; it
    # degrades to snap=None (past days + the book eval SKIP and self-heal next run). Mirrors the
    # shadow-fetch guard above. (simplify-2026-07-22 snapshot-db-unguarded)
    snap = None
    try:
        snap = db_source.snapshot_db()
    except Exception as e:  # noqa: BLE001
        _log(f"prod DB snapshot failed ({e}) — today's capture proceeds; past-day backfill + "
             f"portfolio-eval skip this run, self-heal next run", verbose=verbose)

    def load_backfill(d: date):
        if snap is None:
            return None, None, None
        return (db_source.read_np_by_date(snap, d.isoformat()),
                db_source.read_cps_by_date(snap, d.isoformat()),
                db_source.read_shadow_by_date(snap, d.isoformat()))

    def read_book(iso: str):
        return db_source.read_book_by_date(snap, iso) if snap is not None else None

    def scan_rows(iso: str) -> dict:
        """{ticker: scan_row} for the eval date — today's rows come from the live API payload
        already in hand; past days read the snapshot's stored scan."""
        if iso == api_date.isoformat():
            return {t.get("ticker"): t for t in (np_latest.get("tickers") or [])}
        if snap is None:
            return {}
        npd = db_source.read_np_by_date(snap, iso)
        return {t.get("ticker"): t for t in (npd.get("tickers") or [])} if npd else {}

    def prev_shadow_rows(iso: str):
        """Prior-day shadow rows for the day-flips segment (best-effort: API, then snapshot)."""
        try:
            return api_source.fetch_shadow_rows(iso)
        except Exception:  # noqa: BLE001
            if snap is not None:
                sh = db_source.read_shadow_by_date(snap, iso)
                return sh["rows"] if sh else None
            return None

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
        shadow_diffs_path=shadow_diffs_file,
        v2_briefings_path=v2_briefings_file,
        shadow_latest=shadow_latest,
        prev_shadow_rows_fn=prev_shadow_rows,
        portfolio_evals_path=portfolio_evals_file,
        read_book_fn=read_book,
        scan_rows_fn=scan_rows,
    )
    _log(f"done: {json.dumps(summary)}", verbose=verbose)
    return 0


if __name__ == "__main__":
    sys.exit(main())
