"""Prompt templates for the headless Claude briefing + CPS Notable.

The prompts are fully self-contained (no tools needed): they carry the verified numbers,
today's rendered tables, and the recent entries as few-shot voice/continuity examples.
Claude returns ONLY the prose; Python validates and inserts it.
"""
from __future__ import annotations

BRIEFING_PROMPT = """You are writing the daily briefing entry for "Theta Harvest", an options \
premium-selling dashboard. Write the entry for {date} ({weekday}).

OUTPUT RULES (strict):
- Output ONLY the entry body. No `## {date}` heading, no preamble, no explanation, no code fences.
- Start with the `**Regime:**` line and end with the `**Position:** ...` line.
- Match the exact format, density, and opinionated voice of YOUR RECENT BRIEFINGS shown below.

AUTHORITATIVE NUMBERS — these are pre-computed. Copy them VERBATIM; never recompute or alter them.
Your first line MUST be exactly:
**Regime:** {regime_label} (<your short qualifier here>) | **Tradeable:** {tradeable_str} | **Avg VRP:** {avg_vrp_str}

VERIFIED STATS (use these; the day-over-day deltas are the truth — build the narrative around them):
{statpack_json}

TODAY'S NAKED PUTS TABLE:
{np_table}

TODAY'S CREDIT PUT SPREADS SNAPSHOT:
{cps_block}

YOUR LAST {n} BRIEFINGS (newest first — match this voice and structure, and CARRY FORWARD the running
theses, active positions, and watchpoints; reference what changed since yesterday):
{recent_briefings}

Now write {date}'s entry body: a regime headline line, 1 dense analysis paragraph naming specific \
tickers/scores/deltas and signal changes, and a final `**Position:** ...` line with concrete calls \
(sizing is the trader's decision — frame it as guidance, not orders). Be specific and decisive."""


CPS_NOTABLE_PROMPT = """You are writing the "Notable" analysis paragraph for the Credit Put Spreads \
(CPS) tab of "Theta Harvest", for {date} ({weekday}).

OUTPUT RULES (strict):
- Output ONLY the analysis prose (one dense paragraph). NO "**Notable:**" prefix, no heading, no \
table, no code fences, no preamble.
- Match the voice of YOUR RECENT CPS NOTABLES below.

TODAY'S CPS SNAPSHOT (already logged immediately above this Notable):
{cps_block}

TODAY'S REGIME CONTEXT (verified stats):
{statpack_json}

YOUR LAST {n} CPS NOTABLES (newest first — carry forward the Days streaks, c/w patterns, VIX trend, \
and the standing "what triggers the first SELL_CPS" thesis):
{recent_cps}

Now write {date}'s Notable paragraph — specific about Days streaks, credit/width levels, VIX/VVIX, \
base-gate passes, and what it all means for whether/when a SELL_CPS can fire."""
