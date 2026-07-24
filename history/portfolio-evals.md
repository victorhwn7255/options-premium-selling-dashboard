# Portfolio Evaluations — Open-Book Behavioural Review (Claude-written)

A daily, model-written **behavioural** evaluation of the OPEN options journal book (naked puts / put spreads sold for premium). Sister log to `daily-briefings.md` (market narrative) — this one is oriented at the trader's own positions and habits: is each name tracking its entry thesis, how close is it to a strategy exit rule, and what patterns recur across the book over time. Over time these entries become a corpus for learning the trader's trading habits (the roadmap's J3 "AI retro" layer). One entry per trading day with an open book, descending order (newest first).

Written automatically by headless Claude in `automation/` — **advisory and read-only**. It touches no CONFIG / eligibility / scoring and changes no live decision. The deterministic numbers it reads (marks, unrealized P&L, capture %, DTE, delta, flags) come straight from the prod-DB snapshot the automation already pulls (`positions` + `position_marks`, marked by the 18:30 ET scan) — Claude fetches nothing and recomputes nothing.

---

## Update Protocol

**Trigger:** After the 18:30 ET scan has marked the open positions, the automation assembles a deterministic book header (capture-before-Claude — written FIRST), then headless Claude appends the prose evaluation (best-effort — a failure here never blocks the v1 history; it self-heals on a later run).

**Empty book → no entry** (the file stays signal-dense — a day with no open positions is skipped entirely).

**Entry format:**
```
## YYYY-MM-DD (Day of week)

**Book summary:** N open · credit at risk $X · notional $Y · top concentration TICKER Z%

| # | Ticker | Structure | Strikes | Expiry | Qty | Credit | Mark | uPnL | Capture | DTE | Δ | Regime | v1 Action | v2 Gate | FVRP | Flags |
| ...one row per open position (mark = option_mid; flags cite the strategy's own exit rules)... |

**Closed YYYY-MM-DD:** (only when a trade closed today — a short thesis-vs-outcome + realized P&L note)
- TICKER structure strikes ×qty — thesis "..." → realized +$X (capture Z%, exit reason)

**Assessment:** [Claude prose — per-position tracking-vs-thesis + exit-signal proximity + IV-vs-delta
driver; portfolio-level credit-at-risk / concentration / regime alignment; management calls citing the
strategy's OWN exit rules (75% profit target, 21-DTE, danger-underwater, tested); behavioural
observations across the corpus]
```

**Analysis should cover:**
- Per position: is it tracking its entry thesis, how near an exit signal (flag), and IV- vs delta-driven
- Portfolio: credit at risk, single-name concentration, alignment with today's regime
- Management calls that cite the strategy's own exit rules — never invented ones
- Behavioural observations across the recent corpus (holding past target, sizing drift, checklist deviations)
- Closed-today trades: a brief thesis-vs-outcome + realized P&L post-mortem

**Tone:** Concise, data-driven, opinionated, advisory. Reference specific tickers and numbers. The deterministic header is GIVEN — never recompute or alter its numbers.

**Corrigenda:** when a later verification finds a factual error in an already-written entry, append a dated `> **Corrigendum (YYYY-MM-DD):** ...` blockquote to that entry rather than rewriting its prose.

---

> **IMPORTANT:** Entries are in **descending order** (newest first). New entries go immediately below this line.

---

## 2026-07-22 (Wednesday)

**Book summary:** 1 open · credit at risk $849 · notional $103,500 · top concentration GLD 100%

| # | Ticker | Structure | Strikes | Expiry | Qty | Credit | Mark | uPnL | Capture | DTE | Δ | Regime | v1 Action | v2 Gate | FVRP | Flags |
|---|--------|-----------|---------|--------|-----|--------|------|------|---------|-----|---|--------|-----------|---------|------|-------|
| 1 | GLD | naked_put | 345P | 2026-09-18 | 3 | $2.83 | $3.67 | -$254 | -30% | 58 | -0.17 | NORMAL | WATCHLIST | NORMAL | 1.03 | — |

**Assessment:** GLD 345P ×3 (Sep 18, 58 DTE) is the entire book, opened today at $2.83 and already marked $3.675 for -$254, a capture of -30% on day one. Read that number for what it is before reacting to it: the mark source is `quote_fallback`, not a live two-sided quote, on a position that has existed for hours. A -30% same-day capture on a strike sitting 34 points below a 379.12 close, with short delta at just -0.17, is not the market telling you the thesis broke — it is a fallback mid plus entry slippage. Do not treat this as information until a clean mark confirms it.

The move, to the extent it is real, is IV-driven rather than delta-driven. Forward vol went the wrong way on you — sigma_fwd 0.2028 at entry to 0.2092 on today's scan — while rv_acceleration climbed 0.738 → 0.855. Delta is doing almost nothing: -0.17 with spot nine handles of buffer above the strike, no TESTED condition anywhere near firing. What did deteriorate is the edge itself. FVRP has compressed 1.1156 → 1.035 with fvrp_z sliding -0.264 → -0.833, and vrp_ratio is 0.796 — you are still selling vol *below* realized, the same negative-VRP condition that was true at entry and has since gotten marginally worse. Signal score 49 → 45, recommendation still WATCHLIST, v2_eligible still false. The scan re-ran and did not vindicate the entry.

Against its own thesis — gold consolidates, $4000 as the floor, comfortable owning GLD at 345 into September — the position is tracking fine. Nothing in the mark contradicts a consolidation view, and 345 is well below where the stated floor sits in GLD terms. That is precisely the problem worth naming: the thesis is directional and the structure is a premium-selling instrument. The strategy's edge is VRP, and VRP here is negative (-5.66 vol points at entry). You are not being paid for vol; you are being paid a small option premium to express a long-gold opinion.

Portfolio level: $849 credit at risk against $103,500 notional. Concentration reads GLD 100%, which is structurally trivial at n=1 but substantively real — the book is one bet, that gold does not break 345 by September, and the assignment obligation behind $849 of premium is a six-figure line. Regime is NORMAL and the position is aligned with it; there is no regime conflict to manage. There is a *signal* conflict, which is different and which the deviation log already captures.

Management calls: **no exit rule fires today, explicitly.** Capture is -30%, nowhere near the PROFIT_TARGET threshold (75% in this NORMAL regime — roughly a quarter of the $2.83 credit left to buy back). DTE 58, so TIME_EXIT at 21 is over a month out — call it late August as the first mechanical checkpoint. Earnings is null on an ETF, so EARNINGS_WALL is inapplicable for the life of the trade. Regime is NORMAL, not DANGER, so DANGER_UNDERWATER does not apply no matter how ugly the day-one mark looks — being underwater alone is not an exit condition outside DANGER. And |Δ| 0.17 with spot far above strike means TESTED is not in play. Hold, and watch two things: whether rv_acceleration keeps climbing (if it flips the regime read, the PROFIT_TARGET flag will drop the target from 75% to 50% and the exit comes much sooner than you're planning for), and whether delta drifts toward -0.30, which is the only thing that turns this from a watch into a defend/roll decision.

Behavioural: this is deviation #1 in the corpus, and it is a clean specimen — three of five entry checks failed (score 49 vs 65, vrp_ratio 0.80 vs 1.15, recommendation WATCHLIST not actionable), overridden by a support-level conviction. One override is not a pattern, and the deviation_reason was written down honestly rather than rationalised after the fact, which is the right habit. What I will be tracking forward: whether directional overrides cluster in *gold specifically* (a macro view leaking into a vol book), and whether the negative-VRP entries get held longer than the positive-VRP ones — deviation trades tend to attract narrative defence at exit time, because the trader is managing the opinion rather than the flag. One process improvement worth making now, before it matters: write down the explicit GLD-equivalent of the $4000 gold floor so the invalidation level is a number the book can check, not a view you re-argue when the mark moves. The trader decides; nothing here requires action today.

---
