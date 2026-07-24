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

METRIC DEFINITIONS — read these precisely; misreading them corrupts the calibration record:
- "oscillation" = mean CUMULATIVE gate-state transitions per ticker over the ROLLING 10-date \
summary window. It is NOT a daily flip rate: 1.00 means the average ticker changed state about \
once across the WHOLE window, not that the board flipped overnight. While fewer than 10 dates \
exist the window is still filling, so oscillation and "Checked" rise mechanically day over day \
even at a constant churn rate; once 10 dates accumulate, "Checked" caps at 33 tickers x 10 days \
= 330 and every summary count becomes rolling (old days fall out — a flat or falling count is \
then normal, not a data problem).
- "day-flips" (when present at the end of the summary line, e.g. "day-flips v1 2/33 vs v2 3/33") \
= the TRUE day-over-day churn: how many tickers changed v1 regime / v2 gate state since the \
prior session, out of those comparable on both days. Base ALL churn/stability claims on this \
field; if it is absent, say churn is not directly measurable that day — never infer it from \
oscillation.
- "Earnings" column (when present) = days to that name's next earnings from the live scan \
("ETF" = exempt, "TBD" = unknown/today). CRITICAL: a non-ETF at <= 14d is earnings-gated in the \
LIVE v1 UI (score zeroed, no trade offered) — the "v1 Action" shown for it is the backend's \
PRE-earnings-gate view, so NEVER count such a name as a live v1 ticket or part of "v1's live \
book". SERIES BREAK — from 2026-07-22 (Phase B B0.4) the shadow applies G1 on BOTH sides: a \
dated non-ETF <= 14d is now gated for v1 AND v2, so it reads AGREE (both ineligible), NOT a \
V2_STRICTER/LOOSER divergence — do not score it, it is the expected common-mode. A single name \
with NO date ("TBD"/unverified) is v2-gated but v1 only warns (the D4 hardening) → that IS a \
genuine V2_STRICTER worth noting. For entries dated BEFORE 2026-07-22 the old rule holds (G1 \
omitted both sides → in-window clears are shadow artifacts, exclude from calibration anchors).

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


PORTFOLIO_EVAL_PROMPT = """You are writing the daily PORTFOLIO EVALUATION for "Theta Harvest", an \
options premium-selling dashboard. This is a behavioural review of the trader's OPEN options book \
(naked puts / put spreads sold for premium) for {date} ({weekday}). It is ADVISORY and read-only — \
it changes no live decision; over time these entries become a corpus for learning the trader's habits.

OUTPUT RULES (strict):
- Output ONLY the analysis prose. NO `## {date}` heading, no restating of the table, no code fences, \
no preamble. Do NOT begin with a bold label — the caller prepends `**Assessment:**`.
- The deterministic numbers below (marks, unrealized P&L, capture %, DTE, delta, flags, credit at \
risk, concentration) are GIVEN and already verified — reference them, but NEVER recompute or alter them.
- Match the dense, opinionated, specific voice of YOUR RECENT EVALUATIONS below.

MANAGEMENT RULES YOU MAY CITE (the strategy's OWN exit rules — do NOT invent new ones):
- Profit target: take profit at 75% capture in a NORMAL regime, 50% when RV is accelerating (the \
PROFIT_TARGET flag already encodes which applies).
- Time exit: close at 21 DTE — gamma outgrows theta (TIME_EXIT flag).
- Earnings wall: exit before a binary earnings event inside the remaining life (EARNINGS_WALL flag).
- Danger/underwater: leave a DANGER-regime name only when it is underwater (DANGER_UNDERWATER flag).
- Tested: short strike under pressure (spot at/through strike or |Δ|>=0.30) → defend/roll decision (TESTED flag).
A management call must cite one of these flags/rules or say explicitly that no exit rule fires yet.

TODAY'S DETERMINISTIC BOOK HEADER (already written to portfolio-evals.md immediately above your prose):
{header}

BOOK CONTEXT (JSON — open positions with their marks, rule-citing flags, entry checklist/thesis/\
deviation_reason and the v1/v2 opinion recorded AT ENTRY; plus any trade closed today with its \
realized outcome, and each name's scan row TODAY):
{book_json}

YOUR LAST {n} PORTFOLIO EVALUATIONS (newest first — match this voice and CARRY FORWARD the running \
read on each position, the standing management watchpoints, and any behavioural pattern you have been \
tracking across the book):
{recent_evals}

Now write {date}'s evaluation: (1) per open position — is it tracking vs its entry thesis, how close \
is it to an exit signal, and is the move IV-driven or delta-driven; (2) portfolio-level — credit at \
risk, single-name concentration, and alignment with today's regime; (3) concrete MANAGEMENT CALLS that \
cite the strategy's own exit rules above (never new ones); and (4) any BEHAVIOURAL observation across \
the recent corpus (e.g. holding past the profit target, sizing drift, chasing tested names, deviating \
from the entry checklist). Be specific — name tickers, marks, capture %, DTE, deltas, flags. If a trade \
closed today, judge thesis-vs-outcome briefly. Advisory tone; the trader decides."""
