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


V2_BRIEFING_PROMPT = """You are writing the daily v2-shadow briefing for "Theta Harvest", an \
options premium-selling dashboard mid-way through a staged v1->v2 upgrade. v2 runs SILENTLY in \
the background (Phase A) — it changes NO live decision yet; this log measures how its eligibility \
view would diverge from the live v1 engine, so the eventual Phase-B calibration is data-driven. \
Write the entry for {date} ({weekday}).

OUTPUT RULES (strict):
- Output ONLY the entry body. No `## {date}` heading, no preamble, no explanation, no code fences.
- Your FIRST line MUST be exactly the deterministic shadow-summary line below, reproduced VERBATIM \
(copy it character-for-character; never recompute or alter any number):
{summary_line}
- End with a `**Calibration read:** ...` line (see below).
- Match the dense, opinionated voice of YOUR RECENT v2 BRIEFINGS shown below.

Vocabulary: V2_STRICTER = v1 would trade but v2 gates it (a potential veto — is v2 correctly \
saving you from a bad sell, or missing a good one?). V2_LOOSER = v2 would allow what v1 gates. \
STATE_MISMATCH = same eligibility, different gate state. NODATA_SKEW = v2 lacked the FVRP inputs. \
"warm" = v2 had enough history to judge. FVRP = forward volatility-risk-premium ratio; z = its \
z-score; the Phase-B plan gates on an FVRP "dead-zone" whose bounds are set by matching v1's \
historical eligibility quantiles.

TODAY'S DETERMINISTIC SHADOW TABLE (already logged in v2-metrics-logs.md; do not restate it as a table):
{shadow_table}

TODAY'S /api/shadow/summary JSON (rolling 10-day aggregate — the trend context):
{summary_json}

YOUR LAST {n} v2 BRIEFINGS (newest first — match this voice; carry forward the running read on \
whether v2 is vetoing correctly and where the FVRP dead-zone is trending):
{recent_v2_briefings}

Now write {date}'s entry body: the verbatim shadow-summary line, then ONE dense paragraph analyzing \
the divergence — which specific V2_STRICTER / V2_LOOSER tickers matter and why (name them with their \
FVRP/z/slope), whether v2 is correctly vetoing or is at risk of missing tradeable premium, and the \
FVRP / index-gating / oscillation TREND vs recent days — and finally a `**Calibration read:** ...` \
line stating, concretely, what this day implies for the Phase-B FVRP dead-zone quantile-match \
(e.g. whether the dead-zone bounds look too tight/too loose relative to v1's realized eligibility)."""
