"""Orchestrator tests (no network/SSH — fixtures + scratch files injected).

Run from repo root:  python3 automation/tests/test_orchestrator.py
"""
from __future__ import annotations

import json
import re
import shutil
import sys
import tempfile
from datetime import date
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from automation import run_history_update as orch  # noqa: E402
from automation.history import parser  # noqa: E402
from automation.render.np_table import render_np_table  # noqa: E402

FIX = REPO / "automation" / "fixtures"
HIST = REPO / "history"


def _load_np(d):
    return json.loads((FIX / f"np_{d}.json").read_text())


def _load_cps(d):
    return json.loads((FIX / f"cps_{d}.json").read_text())


def _scratch_truncated(dst_dir: Path, keep_from: str):
    """Copy the 3 history files into dst_dir, dropping every entry newer than keep_from."""
    out = {}
    for name in ("metrics-logs.md", "credit-put-spreads.md", "daily-briefings.md"):
        text = (HIST / name).read_text()
        first = re.search(r"^##\s+\d{4}-\d{2}-\d{2}\b", text, re.M)
        keep = re.search(rf"^##\s+{re.escape(keep_from)}\b", text, re.M)
        new = text[: first.start()] + text[keep.start():]
        p = dst_dir / name
        p.write_text(new)
        out[name] = p
    return out["metrics-logs.md"], out["credit-put-spreads.md"], out["daily-briefings.md"]


def _ok(label, cond):
    assert cond, f"FAIL {label}"
    print(f"  PASS  {label}")


def test_backfill_three_days_then_idempotent():
    with tempfile.TemporaryDirectory() as td:
        m, c, b = _scratch_truncated(Path(td), "2026-05-29")
        _ok("scratch anchor is 5/29", parser.last_logged_date(m) == date(2026, 5, 29))

        def load_backfill(d):
            return _load_np(d.isoformat()), _load_cps(d.isoformat())

        summary = orch.run(
            metrics_path=m, cps_path=c, briefings_path=b,
            api_date=date(2026, 6, 3),
            np_latest=_load_np("2026-06-03"), cps_latest=_load_cps("2026-06-03"),
            load_backfill=load_backfill, no_claude=True, verbose=False,
        )
        _ok("todo == 6/1,6/2,6/3", summary["todo"] == ["2026-06-01", "2026-06-02", "2026-06-03"])
        _ok("metrics written all 3", summary["metrics_written"] == ["2026-06-01", "2026-06-02", "2026-06-03"])
        _ok("cps written all 3", summary["cps_written"] == ["2026-06-01", "2026-06-02", "2026-06-03"])
        _ok("briefings pending all 3", summary["briefings_pending"] == ["2026-06-01", "2026-06-02", "2026-06-03"])
        _ok("metrics last-logged now 6/3", parser.last_logged_date(m) == date(2026, 6, 3))
        # content correctness: 6/3 metrics entry byte-matches the renderer
        expected = render_np_table(_load_np("2026-06-03")["tickers"])
        got = parser.parse_np_table  # sanity that parse round-trips
        _ok("6/3 metrics table present verbatim", expected in m.read_text())
        # ordering: 6/1 appears below 6/2 below 6/3 (newest on top)
        text = m.read_text()
        _ok("newest-on-top order", text.index("## 2026-06-03") < text.index("## 2026-06-02") < text.index("## 2026-06-01"))
        # briefings untouched (no Claude)
        _ok("briefings untouched at 5/29", parser.last_logged_date(b) == date(2026, 5, 29))

        # idempotent re-run -> nothing new written
        s2 = orch.run(
            metrics_path=m, cps_path=c, briefings_path=b, api_date=date(2026, 6, 3),
            np_latest=_load_np("2026-06-03"), cps_latest=_load_cps("2026-06-03"),
            load_backfill=load_backfill, no_claude=True, verbose=False,
        )
        _ok("re-run writes no metrics", s2["metrics_written"] == [])
        _ok("re-run writes no cps", s2["cps_written"] == [])


def test_capture_before_claude_on_auth_failure():
    """If Claude auth fails, the deterministic data must still be fully captured for every day,
    the run must not crash, and briefings are left pending. Proves zero-loss."""
    from automation.claude.runner import ClaudeAuthError

    with tempfile.TemporaryDirectory() as td:
        m, c, b = _scratch_truncated(Path(td), "2026-05-29")

        def load_backfill(d):
            return _load_np(d.isoformat()), _load_cps(d.isoformat())

        def failing_briefing(*a, **k):
            raise ClaudeAuthError("Please run /login")

        s = orch.run(metrics_path=m, cps_path=c, briefings_path=b, api_date=date(2026, 6, 3),
                     np_latest=_load_np("2026-06-03"), cps_latest=_load_cps("2026-06-03"),
                     load_backfill=load_backfill, no_claude=False, verbose=False,
                     briefing_fn=failing_briefing, notable_fn=lambda *a, **k: "x")
        _ok("run did not crash on auth failure", True)
        _ok("all 3 days' metrics captured despite auth failure",
            all(parser.has_entry(m, d) for d in ("2026-06-01", "2026-06-02", "2026-06-03")))
        _ok("all 3 days' cps captured despite auth failure",
            all(parser.has_entry(c, d) for d in ("2026-06-01", "2026-06-02", "2026-06-03")))
        _ok("no briefings written", s["briefings_written"] == [])
        _ok("briefings left pending", "2026-06-01" in s["briefings_pending"])
        _ok("briefings file untouched", parser.last_logged_date(b) == date(2026, 5, 29))


def test_injected_claude_success():
    """With a fake successful Claude, briefings + notables are written into the right place."""
    with tempfile.TemporaryDirectory() as td:
        m, c, b = _scratch_truncated(Path(td), "2026-06-02")  # only 6/3 missing

        def briefing_fn(d, sp, np_table, cps_block, recent):
            return (f"**Regime:** {sp['regime_label']} (test) | **Tradeable:** {sp['tradeable_str']} "
                    f"| **Avg VRP:** {sp['avg_vrp_str']}\n\nNarrative.\n\n**Position: hold.**")

        s = orch.run(metrics_path=m, cps_path=c, briefings_path=b, api_date=date(2026, 6, 3),
                     np_latest=_load_np("2026-06-03"), cps_latest=_load_cps("2026-06-03"),
                     load_backfill=lambda d: (None, None), no_claude=False, verbose=False,
                     briefing_fn=briefing_fn, notable_fn=lambda *a, **k: "Notable body.")
        _ok("briefing 6/3 written", s["briefings_written"] == ["2026-06-03"])
        _ok("notable 6/3 written", s["notables_written"] == ["2026-06-03"])
        bt = parser.entry_text(b, "2026-06-03")
        _ok("briefing has correct regime line", bt.startswith("## 2026-06-03 (Wednesday)\n\n**Regime:** THE PLAYOFFS (test) | **Tradeable:** 3S / 3C + 1W | **Avg VRP:** +2.7"))
        ct = parser.entry_text(c, "2026-06-03")
        _ok("CPS Notable appended after table, before separator",
            "\n\n**Notable:** Notable body.\n\n---" in ct)
        _ok("CPS table still intact before Notable",
            "| 1 | QQQ | WATCH | 13d |" in ct and ct.index("| 1 | QQQ") < ct.index("**Notable:**"))


def test_up_to_date_noop():
    with tempfile.TemporaryDirectory() as td:
        # keep everything (anchor = 6/3); api_date 6/3 -> no todo
        for name in ("metrics-logs.md", "credit-put-spreads.md", "daily-briefings.md"):
            shutil.copy(HIST / name, Path(td) / name)
        m, c, b = (Path(td) / n for n in ("metrics-logs.md", "credit-put-spreads.md", "daily-briefings.md"))
        s = orch.run(metrics_path=m, cps_path=c, briefings_path=b, api_date=date(2026, 6, 3),
                     np_latest=_load_np("2026-06-03"), cps_latest=_load_cps("2026-06-03"),
                     load_backfill=lambda d: (None, None), no_claude=True, verbose=False)
        _ok("up-to-date -> empty todo", s["todo"] == [])


def test_partial_scan_and_cps_window():
    with tempfile.TemporaryDirectory() as td:
        m, c, b = _scratch_truncated(Path(td), "2026-05-29")
        # 6/1 returns a partial NP (10 tickers) -> skipped; 6/2 returns NP but no CPS -> NP only
        def load_backfill(d):
            if d == date(2026, 6, 1):
                np = _load_np("2026-06-01"); np = {**np, "tickers": np["tickers"][:10]}
                return np, None
            if d == date(2026, 6, 2):
                return _load_np("2026-06-02"), None  # CPS beyond window
            return None, None
        s = orch.run(metrics_path=m, cps_path=c, briefings_path=b, api_date=date(2026, 6, 3),
                     np_latest=_load_np("2026-06-03"), cps_latest=_load_cps("2026-06-03"),
                     load_backfill=load_backfill, no_claude=True, verbose=False)
        _ok("partial 6/1 skipped", "2026-06-01" in s["skipped"] and "2026-06-01" not in s["metrics_written"])
        _ok("6/2 NP written despite no CPS", "2026-06-02" in s["metrics_written"])
        _ok("6/2 CPS not written (window)", "2026-06-02" not in s["cps_written"])
        _ok("6/3 NP+CPS written", "2026-06-03" in s["metrics_written"] and "2026-06-03" in s["cps_written"])


if __name__ == "__main__":
    print("Orchestrator tests:")
    test_backfill_three_days_then_idempotent()
    test_capture_before_claude_on_auth_failure()
    test_injected_claude_success()
    test_up_to_date_noop()
    test_partial_scan_and_cps_window()
    print("All orchestrator tests passed.")
