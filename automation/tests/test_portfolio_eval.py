"""Portfolio-eval tests (no network/SSH/token — synthetic sqlite + injected book/Claude).

Covers: the deterministic header assembles from a synthetic positions+position_marks DB; the
orchestrator step captures a header then appends Claude prose; an empty book writes NO entry;
a raised exception in the eval step never breaks the rest of the run; the writer inserts
descending; and a re-run is idempotent. The `claude -p` call is always stubbed (hermetic).

Run from repo root:  python3 automation/tests/test_portfolio_eval.py
"""
from __future__ import annotations

import shutil
import sqlite3
import sys
import tempfile
from datetime import date
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from automation import run_history_update as orch  # noqa: E402
from automation.history import parser, writer  # noqa: E402
from automation.render.portfolio_eval import (  # noqa: E402
    build_book_context, compute_flags, render_portfolio_header)
from automation.sources import db_source  # noqa: E402

HIST = REPO / "history"


def _ok(label, cond):
    assert cond, f"FAIL {label}"
    print(f"  PASS  {label}")


# ── synthetic DB fixture (no SSH/token) ─────────────────────────────────────
def _make_snap(td: Path) -> Path:
    """A tiny prod-DB stand-in: positions + position_marks with one open naked put (GLD, at the
    50% profit target), one tested/danger spread (AMZN), and one trade closed on the eval date."""
    dbp = td / "snap.db"
    conn = sqlite3.connect(dbp)
    conn.executescript("""
        CREATE TABLE positions (id INTEGER PRIMARY KEY, ticker TEXT, structure TEXT, status TEXT,
          short_strike REAL, long_strike REAL, expiry TEXT, contracts INTEGER, entry_date TEXT,
          entry_credit REAL, entry_commissions REAL, close_date TEXT, close_debit REAL,
          realized_pnl REAL, thesis TEXT, checklist_json TEXT, scan_ref TEXT, exit_reason TEXT,
          target_capture REAL, exit_dte_plan INTEGER, followed_plan INTEGER);
        CREATE TABLE position_marks (position_id INTEGER, date TEXT, underlying_close REAL,
          option_bid REAL, option_ask REAL, option_mid REAL, short_delta REAL, unrealized_pnl REAL,
          capture_pct REAL, dte INTEGER, earnings_dte INTEGER, mark_source TEXT,
          PRIMARY KEY(position_id, date));
    """)
    chk = '{"checks":{"score_ge_65":true},"values":{"v2_gate_state":"COOL"},"deviation_reason":null}'
    conn.execute("INSERT INTO positions VALUES (1,'GLD','naked_put','open',305,NULL,'2026-08-15',2,"
                 "'2026-05-15',3.10,1.30,NULL,NULL,NULL,'IV rank high, fat vol premium',?,'x',NULL,"
                 "0.75,21,NULL)", (chk,))
    conn.execute("INSERT INTO position_marks VALUES "
                 "(1,'2026-06-03',330.0,1.50,1.60,1.55,-0.28,310.0,0.50,25,NULL,'scan_chain')")
    conn.execute("INSERT INTO positions VALUES (2,'AMZN','put_spread','open',210,205,'2026-08-01',1,"
                 "'2026-05-10',1.20,0.65,NULL,NULL,NULL,'post-earnings drift',?,'x',NULL,0.75,21,NULL)",
                 (chk,))
    conn.execute("INSERT INTO position_marks VALUES "
                 "(2,'2026-06-03',208.0,1.90,2.10,2.00,-0.42,-80.0,-0.6667,9,3,'scan_chain')")
    conn.execute("INSERT INTO positions VALUES (3,'KO','naked_put','closed',60,NULL,'2026-07-18',3,"
                 "'2026-05-01',0.80,1.0,'2026-06-03',0.20,171.0,'mean reversion','{}','x',"
                 "'profit_target',0.75,21,1)")
    conn.commit()
    conn.close()
    return dbp


_SCAN = {
    "GLD": {"regime": "NORMAL", "recommendation": "SELL PREMIUM", "v2_gate_state": "COOL",
            "fvrp_ratio": 1.02, "rv_acceleration": 0.70},
    "AMZN": {"regime": "DANGER", "recommendation": "AVOID", "v2_gate_state": "DANGER",
             "fvrp_ratio": 1.25, "rv_acceleration": 1.30},
}


# ── scratch v1 + evals files ────────────────────────────────────────────────
def _scratch_v1(td: Path):
    """Copy the three real v1 history files (fully) — v1 is up-to-date so the run's v1 side is a
    no-op and we exercise only the portfolio-eval pass."""
    out = []
    for name in ("metrics-logs.md", "credit-put-spreads.md", "daily-briefings.md"):
        p = td / name
        shutil.copy(HIST / name, p)
        out.append(p)
    return out


def _scratch_evals(td: Path, seed_dates=()) -> Path:
    """Copy the real (empty-log) portfolio-evals.md; optionally seed completed entries (with an
    Assessment) so descending-insert + idempotency can be exercised."""
    p = td / "portfolio-evals.md"
    shutil.copy(HIST / "portfolio-evals.md", p)
    for iso in seed_dates:  # oldest first so insert-at-top yields descending
        d = date.fromisoformat(iso)
        writer.insert_entry(p, iso, f"## {iso} ({d.strftime('%A')})\n\n"
                                    f"**Book summary:** 1 open\n\n**Assessment:** seeded.")
    return p


def _run(td: Path, evals_path, read_book_fn, *, eval_fn=None, no_claude=False):
    """Drive orch.run with an up-to-date v1 (empty todo) so only the eval pass does work."""
    m, c, b = _scratch_v1(td)
    return orch.run(
        metrics_path=m, cps_path=c, briefings_path=b, api_date=date(2026, 6, 3),
        np_latest={"tickers": []}, cps_latest=None,
        load_backfill=lambda d: (None, None, None), no_claude=no_claude, verbose=False,
        portfolio_evals_path=evals_path, read_book_fn=read_book_fn,
        scan_rows_fn=lambda iso: _SCAN,
        portfolio_eval_fn=eval_fn or (lambda d, header, ctx, recent: "Eval prose body."))


# ── tests ───────────────────────────────────────────────────────────────────
def test_flags_match_backend_logic():
    """compute_flags faithfully ports positions_api.compute_flags."""
    with tempfile.TemporaryDirectory() as td:
        book = db_source.read_book_by_date(_make_snap(Path(td)), "2026-06-03")
        by_tkr = {p["ticker"]: compute_flags(p, p.get("mark"), _SCAN.get(p["ticker"]), "2026-06-03")
                  for p in book["open"]}
        amzn = {f["code"] for f in by_tkr["AMZN"]}
        _ok("AMZN tested+time+earnings+danger flags",
            amzn == {"TIME_EXIT", "EARNINGS_WALL", "DANGER_UNDERWATER", "TESTED"})
        _ok("GLD at 50% target below 75% NORMAL target -> no flags", by_tkr["GLD"] == [])
        _ok("every flag cites a rule", all(f.get("rule") for fl in by_tkr.values() for f in fl))


def test_header_assembles_from_synthetic_db():
    with tempfile.TemporaryDirectory() as td:
        book = db_source.read_book_by_date(_make_snap(Path(td)), "2026-06-03")
        header = render_portfolio_header(book, _SCAN, "2026-06-03")
        _ok("book summary counts 2 open", "**Book summary:** 2 open" in header)
        _ok("credit at risk summed (3.10*100*2 + 1.20*100*1 = 740)", "credit at risk $740" in header)
        _ok("concentration names top single-name notional",
            "top concentration GLD 74%" in header)
        _ok("GLD row: mark=option_mid, +uPnL, capture, DTE, delta, context",
            "| 2 | GLD | naked_put | 305P | 2026-08-15 | 2 | $3.10 | $1.55 | +$310 | 50% | 25 | "
            "-0.28 | NORMAL | SELL PREMIUM | COOL | 1.02 | — |" in header)
        _ok("AMZN row carries the recomputed flag codes",
            "TIME_EXIT, EARNINGS_WALL, DANGER_UNDERWATER, TESTED |" in header)
        _ok("closed-today post-mortem line present",
            '- KO naked_put 60P ×3 — thesis "mean reversion" → realized +$171 '
            '(capture 75%, exit profit_target)' in header)
        ctx = build_book_context(book, _SCAN, "2026-06-03")
        _ok("book context carries thesis + at-entry checklist",
            ctx["positions"][0]["thesis"] and "entry_checklist" in ctx["positions"][0])
        _ok("book context carries the closed trade", ctx["closed_today"][0]["ticker"] == "KO")


def test_step_captures_header_then_appends_prose():
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        snap = _make_snap(tdp)
        evals = _scratch_evals(tdp)
        s = _run(tdp, evals, lambda iso: db_source.read_book_by_date(snap, iso))
        _ok("header captured for api_date", s["portfolio_eval_captured"] == ["2026-06-03"])
        _ok("prose written for api_date", s["portfolio_eval_written"] == ["2026-06-03"])
        et = parser.entry_text(evals, "2026-06-03")
        _ok("entry has the deterministic table", "**Book summary:** 2 open" in et)
        _ok("prose appended under **Assessment:**", "**Assessment:** Eval prose body." in et)
        _ok("header precedes prose", et.index("**Book summary:**") < et.index("**Assessment:**"))
        # idempotent re-run
        s2 = _run(tdp, evals, lambda iso: db_source.read_book_by_date(snap, iso))
        _ok("re-run captures nothing", s2["portfolio_eval_captured"] == [])
        _ok("re-run writes no prose", s2["portfolio_eval_written"] == [])


def test_empty_book_writes_no_entry():
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        evals = _scratch_evals(tdp)
        before = evals.read_text()
        s = _run(tdp, evals, lambda iso: {"date": iso, "open": [], "closed_today": []})
        _ok("empty book -> recorded as skipped", s["portfolio_eval_skipped"] == ["2026-06-03"])
        _ok("empty book -> nothing captured", s["portfolio_eval_captured"] == [])
        _ok("empty book -> no entry written", not parser.has_entry(evals, "2026-06-03"))
        _ok("file untouched", evals.read_text() == before)


def test_descending_insert_across_days():
    """A gap of trading days below the last eval backfills newest-on-top."""
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        snap = _make_snap(tdp)
        evals = _scratch_evals(tdp, seed_dates=["2026-05-29"])  # last eval = 5/29
        s = _run(tdp, evals, lambda iso: db_source.read_book_by_date(snap, iso))
        _ok("captured the 3 missing trading days",
            s["portfolio_eval_captured"] == ["2026-06-01", "2026-06-02", "2026-06-03"])
        text = evals.read_text()
        _ok("newest-on-top order",
            text.index("## 2026-06-03") < text.index("## 2026-06-02")
            < text.index("## 2026-06-01") < text.index("## 2026-05-29"))
        _ok("seeded 5/29 entry left intact (already has Assessment)",
            "**Assessment:** seeded." in parser.entry_text(evals, "2026-05-29"))


def test_isolation_eval_failure_never_breaks_run():
    """A raised exception in the eval step is swallowed; the v1 briefing for a pending day still
    gets written (the eval pass runs before the v1 loop and must never abort it)."""
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        # truncate v1 so there IS a v1 todo day (6/3) to prove the run continues past the failure
        for name in ("metrics-logs.md", "credit-put-spreads.md", "daily-briefings.md"):
            text = (HIST / name).read_text()
            import re as _re
            first = _re.search(r"^##\s+\d{4}-\d{2}-\d{2}\b", text, _re.M)
            keep = _re.search(r"^##\s+2026-06-02\b", text, _re.M)
            (tdp / name).write_text(text[: first.start()] + text[keep.start():])
        import json as _json
        m, c, b = (tdp / n for n in ("metrics-logs.md", "credit-put-spreads.md", "daily-briefings.md"))
        evals = _scratch_evals(tdp)
        np_latest = _json.loads((REPO / "automation" / "fixtures" / "np_2026-06-03.json").read_text())
        cps_latest = _json.loads((REPO / "automation" / "fixtures" / "cps_2026-06-03.json").read_text())

        def boom(iso):
            raise RuntimeError("book read exploded")

        s = orch.run(
            metrics_path=m, cps_path=c, briefings_path=b, api_date=date(2026, 6, 3),
            np_latest=np_latest, cps_latest=cps_latest,
            load_backfill=lambda d: (None, None, None), no_claude=False, verbose=False,
            briefing_fn=lambda *a, **k: ("**Regime:** X | **Tradeable:** Y | **Avg VRP:** Z\n\n"
                                         "n\n\n**Position:** hold."),
            notable_fn=lambda *a, **k: "note",
            portfolio_evals_path=evals, read_book_fn=boom, scan_rows_fn=lambda iso: _SCAN,
            portfolio_eval_fn=lambda *a, **k: "prose")
        _ok("run did not crash despite eval-step exception", True)
        _ok("no portfolio entry written", not parser.has_entry(evals, "2026-06-03"))
        _ok("v1 briefing STILL written despite eval failure", "2026-06-03" in s["briefings_written"])
        _ok("v1 metrics STILL written despite eval failure", "2026-06-03" in s["metrics_written"])


def test_capture_survives_claude_failure():
    """Capture-before-Claude: if the prose call raises, the deterministic header is still written
    and the day is left prose-pending (self-heals next run)."""
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        snap = _make_snap(tdp)
        evals = _scratch_evals(tdp)

        def failing_eval(*a, **k):
            raise RuntimeError("claude down")

        s = _run(tdp, evals, lambda iso: db_source.read_book_by_date(snap, iso), eval_fn=failing_eval)
        _ok("header captured despite Claude failure", s["portfolio_eval_captured"] == ["2026-06-03"])
        _ok("no prose written", s["portfolio_eval_written"] == [])
        et = parser.entry_text(evals, "2026-06-03")
        _ok("header present", "**Book summary:** 2 open" in et)
        _ok("no Assessment yet (pending)", "**Assessment:**" not in et)
        # next run self-heals the prose (Claude back up)
        s2 = _run(tdp, evals, lambda iso: db_source.read_book_by_date(snap, iso))
        _ok("no re-capture (header already there)", s2["portfolio_eval_captured"] == [])
        _ok("prose self-healed on the next run", s2["portfolio_eval_written"] == ["2026-06-03"])
        _ok("Assessment now present",
            "**Assessment:** Eval prose body." in parser.entry_text(evals, "2026-06-03"))


if __name__ == "__main__":
    print("Portfolio-eval tests:")
    test_flags_match_backend_logic()
    test_header_assembles_from_synthetic_db()
    test_step_captures_header_then_appends_prose()
    test_empty_book_writes_no_entry()
    test_descending_insert_across_days()
    test_isolation_eval_failure_never_breaks_run()
    test_capture_survives_claude_failure()
    print("All portfolio-eval tests passed.")
