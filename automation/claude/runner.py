"""Headless Claude invocation (Max subscription) for the briefing prose + CPS Notable.

Claude returns ONLY the prose to stdout; the orchestrator validates and inserts it. The job
env strips ANTHROPIC_API_KEY so Claude Code uses the Max subscription (zero API cost), never
the paid API. Auth failures are detected and reported (never silently produce a bad entry).
"""
from __future__ import annotations

import json
import os
import re
import subprocess
from datetime import date

from .. import config
from . import prompts

# Substrings that indicate the Max session needs re-login / the call wasn't authorized.
_AUTH_PATTERNS = re.compile(
    r"(invalid api key|authentication|please run|/login|not logged in|log ?in|oauth|"
    r"credit balance|unauthorized|401|forbidden)",
    re.I,
)


class ClaudeAuthError(Exception):
    pass


def _invoke(prompt: str, timeout: int = 300) -> str:
    """Run `claude -p` headless on the Max plan. Returns stdout text; raises ClaudeAuthError
    on an auth problem and RuntimeError on other failures/timeouts."""
    env = {k: v for k, v in os.environ.items() if k != "ANTHROPIC_API_KEY"}
    try:
        res = subprocess.run(
            [config.CLAUDE_BIN, "-p", prompt, "--output-format", "text"],
            env=env, cwd=os.path.expanduser("~"),  # neutral cwd: prompt is self-contained, and
            capture_output=True, text=True, timeout=timeout,  # also keeps node's cwd out of the (formerly TCC-gated) repo tree
        )
    except subprocess.TimeoutExpired:
        raise RuntimeError("claude -p timed out")
    out, err = (res.stdout or "").strip(), (res.stderr or "").strip()
    if res.returncode != 0:
        if _AUTH_PATTERNS.search(err) or _AUTH_PATTERNS.search(out):
            raise ClaudeAuthError(err or out)
        raise RuntimeError(f"claude -p failed (rc={res.returncode}): {err or out}")
    if not out:
        raise RuntimeError("claude -p returned empty output")
    return out


def _briefing_valid(text: str, sp: dict) -> bool:
    return (
        text.startswith(f"**Regime:** {sp['regime_label']}")
        and f"**Tradeable:** {sp['tradeable_str']}" in text
        and f"**Avg VRP:** {sp['avg_vrp_str']}" in text
        and "**Position:" in text
    )


def run_briefing(d: date, statpack: dict, np_table: str, cps_block: str,
                 recent_briefings: str, n: int = 7) -> str:
    """Return the daily-briefings entry body (regime line → narrative → Position line).
    Raises ClaudeAuthError on auth failure, RuntimeError if the output can't be validated.

    600s timeout: this is by far the largest prompt (7 recent briefings + both tables +
    statpack) and twice overran the 300s default (2026-07-09, 2026-07-15) — the run is a
    nightly batch job, so trading wall-clock for fewer briefing-pending days is free."""
    prompt = prompts.BRIEFING_PROMPT.format(
        date=d.isoformat(), weekday=d.strftime("%A"),
        regime_label=statpack["regime_label"], tradeable_str=statpack["tradeable_str"],
        avg_vrp_str=statpack["avg_vrp_str"], statpack_json=json.dumps(statpack, indent=2),
        np_table=np_table, cps_block=cps_block or "(no CPS data today)",
        recent_briefings=recent_briefings, n=n,
    )
    out = _invoke(prompt, timeout=600)
    if not _briefing_valid(out, statpack):
        # One stricter retry — most failures are a stray preamble or a tweaked number.
        strict = prompt + (
            "\n\nYOUR PREVIOUS ATTEMPT WAS REJECTED (altered a verified number or added text). "
            f"Output must START with exactly:\n**Regime:** {statpack['regime_label']} "
            f"(<qualifier>) | **Tradeable:** {statpack['tradeable_str']} | "
            f"**Avg VRP:** {statpack['avg_vrp_str']}\nand contain a **Position:** line. Nothing else."
        )
        out = _invoke(strict, timeout=600)
        if not _briefing_valid(out, statpack):
            raise RuntimeError("briefing output failed validation (numbers/format)")
    return out


def _clean_notable(text: str) -> str:
    """Strip an accidental leading `Notable:` / `**Notable:**` label without harming an
    intended opening bold like `**Days = 13d …**` (which the real Notables start with)."""
    return re.sub(r"^\*{0,2}Notable:\*{0,2}\s*", "", text.strip()).strip()


def run_cps_notable(d: date, statpack: dict, cps_block: str, recent_cps: str, n: int = 5) -> str:
    """Return the CPS Notable paragraph prose (no '**Notable:**' prefix)."""
    prompt = prompts.CPS_NOTABLE_PROMPT.format(
        date=d.isoformat(), weekday=d.strftime("%A"),
        cps_block=cps_block, statpack_json=json.dumps(statpack, indent=2),
        recent_cps=recent_cps, n=n,
    )
    return _clean_notable(_invoke(prompt))


def _v2_briefing_valid(text: str, summary_line: str) -> bool:
    return text.startswith(summary_line) and "**Calibration read:" in text


def run_v2_briefing(d: date, summary_line: str, shadow_table: str, summary_json,
                    recent_v2_briefings: str, n: int = 5) -> str:
    """Return the v2-briefings entry body (verbatim shadow-summary line -> analysis ->
    `**Calibration read:**` line). Raises ClaudeAuthError on auth failure, RuntimeError if the
    output can't be validated. Mirrors run_briefing (verbatim-header validation + one retry).

    600s timeout: the v2 prompt has grown dense (5 recent entries + corrigenda + the full
    divergence table) and overran the 300s default on 2026-07-21 — same latency profile as
    the v1 briefing, so same headroom. Nightly batch job; wall-clock is free."""
    sj = summary_json if isinstance(summary_json, str) else json.dumps(summary_json, indent=2)
    prompt = prompts.V2_BRIEFING_PROMPT.format(
        date=d.isoformat(), weekday=d.strftime("%A"), summary_line=summary_line,
        shadow_table=shadow_table, summary_json=sj, recent_v2_briefings=recent_v2_briefings, n=n,
    )
    out = _invoke(prompt, timeout=600)
    if not _v2_briefing_valid(out, summary_line):
        # One stricter retry — most failures are a stray preamble or a tweaked number.
        strict = prompt + (
            "\n\nYOUR PREVIOUS ATTEMPT WAS REJECTED (altered the summary line or dropped the "
            "calibration line). Your output must START with exactly this line, character-for-"
            f"character:\n{summary_line}\nand contain a `**Calibration read:**` line. Nothing else."
        )
        out = _invoke(strict, timeout=600)
        if not _v2_briefing_valid(out, summary_line):
            raise RuntimeError("v2-briefing output failed validation (summary line / calibration)")
    return out


def _clean_eval(text: str) -> str:
    """Strip an accidental leading `Assessment:` / `**Assessment:**` label (the caller prepends
    its own) and any stray opening code fence, without harming the prose."""
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else ""
        text = text.rsplit("```", 1)[0]
    return re.sub(r"^\*{0,2}Assessment:\*{0,2}\s*", "", text.strip()).strip()


def run_portfolio_eval(d: date, header: str, book_json, recent_evals: str, n: int = 5) -> str:
    """Return the portfolio-evaluation prose (no `**Assessment:**` prefix — the caller adds it).
    Raises ClaudeAuthError on auth failure, RuntimeError on other failures/empty output.

    Best-effort sister log to daily-briefings: the deterministic book header is captured to
    portfolio-evals.md BEFORE this runs, so a Claude failure never loses the day's book snapshot
    (the orchestrator appends the prose on a later self-heal). No `--model` flag: CLI default.

    600s timeout: matches the other briefing calls' latency profile (recent evals + the full book
    JSON + checklist context is a dense prompt); nightly batch job, so wall-clock is free."""
    bj = book_json if isinstance(book_json, str) else json.dumps(book_json, indent=2)
    prompt = prompts.PORTFOLIO_EVAL_PROMPT.format(
        date=d.isoformat(), weekday=d.strftime("%A"), header=header,
        book_json=bj, recent_evals=recent_evals or "(no prior evaluations — this is the first)", n=n,
    )
    out = _clean_eval(_invoke(prompt, timeout=600))
    if not out:
        raise RuntimeError("portfolio-eval returned empty output")
    return out
