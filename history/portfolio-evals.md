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

## 2026-07-27 (Monday)

**Book summary:** 1 open · credit at risk $849 · notional $103,500 · top concentration GLD 100%

| # | Ticker | Structure | Strikes | Expiry | Qty | Credit | Mark | uPnL | Capture | DTE | Δ | Regime | v1 Action | v2 Gate | FVRP | Flags |
|---|--------|-----------|---------|--------|-----|--------|------|------|---------|-----|---|--------|-----------|---------|------|-------|
| 1 | GLD | naked_put | 345P | 2026-09-18 | 3 | $2.83 | $3.83 | -$298 | -35% | 53 | -0.19 | NORMAL | NO EDGE | NORMAL | 1.03 | — |

**Assessment:** GLD 345P ×3 (Sep 18, 53 DTE) is still the entire book, and today it marks $3.825 for -$298, capture -35% — a $113 recovery off Friday's -$411 low. Same caveat as the last four sessions before anything else: `mark_source` is `quote_fallback` for the fourth consecutive day, so the level is still unverified. But the sequence is now $2.83 → $3.675 → $2.83 → $4.20 → $3.825, and today's print is coherent with its inputs in the same way Friday's was, just in the opposite direction. Worth noting the magnitude mismatch, though: spot rose 2.66 to 374.56 and sigma_fwd came off 0.2265 → 0.2131, and a -0.19 delta against that spot move alone accounts for roughly half a point of the option before vega does anything. The mark gave back only $0.375 of Friday's $1.37 markup. The most likely reading is that Friday's $4.20 overshot and today's $3.825 is closer to fair — meaning the true damage on this trade has probably sat somewhere between the two prints all along, and the P&L line has been noisier than the position.

Attribution today is favourable on both channels for the first time in the trade's life. Spot up 0.72%, forward vol down 1.3 vol points, delta retreating -0.196 → -0.1868 — the first session that has bought back distance from the -0.30 TESTED trigger rather than spending it. Buffer to the 345 strike widened from 26.9 to 29.56 points, about 7.9% of spot, the widest since Wednesday. And against the stated thesis — gold consolidates and bounces, $4000 as the floor — this is the first genuinely supportive tape: 371.53 → 371.90 → 374.56 is stabilise-then-lift, which is exactly the shape a consolidation view predicts. Credit that honestly. Also hold it at its true weight: one up day five sessions into a trade that has been offside every single one of them is a data point, not a confirmation, and it is precisely the kind of data point the narrative-defence pattern I have been watching for would seize on.

The edge picture ticked up and remains bad. Signal score printed 39 after 49 → 45 → 40 → 36, the first improvement in four sessions — and the recommendation is **NO EDGE** for a third consecutive day. vrp_ratio 0.824 → 0.884 is the largest one-day gain of the trade and is still below 1.0, still short vol under realized, still nowhere near the 1.15 entry check. FVRP recovered 1.0054 → 1.0291 with fvrp_z -1.053 → -0.872, off the floor and still negative. iv_percentile has bled 61.5 at entry to 54.7. v2_eligible false throughout. The one reading that got materially worse is the one that matters most structurally: **rv_acceleration crossed 1.0 today**, printing 1.02 after 0.738 → 0.855 → 0.859 → 0.914. That is the input I have flagged as the standing watchpoint every day since Wednesday, and it has now cleared the line. Realized vol is accelerating into a position that is short 53 days of it.

Portfolio shape is unchanged: $849 credit at risk against $103,500 notional — 0.82% of the assignment obligation — GLD 100% concentration, trivially so at n=1 and totally so in substance. Regime reads NORMAL and the position sits inside it, so no regime conflict. The signal conflict narrowed marginally today and is still wider than it was at entry. Regime alignment remains permission to hold, not evidence of edge.

Management calls — **no exit rule fires today, and the flags column is empty.** PROFIT_TARGET: capture -35% against the 75% NORMAL-regime threshold; you would need to buy back near $0.71, and you are $3.825 away from that conversation. But read the rule's second clause today, because rv_acceleration at 1.02 is the input behind it: if that reading flips the target to 50%, the buyback level moves to roughly $1.42 and the exit arrives far sooner than a 75% plan implies. The flag encodes which applies; it has not switched, and it is closer than it has ever been. TIME_EXIT: 53 DTE, the 21-DTE checkpoint is Aug 28, 32 days out. EARNINGS_WALL: earnings_dte null on an ETF, inapplicable for the trade's remaining life. TESTED: |Δ| 0.1868 versus the 0.30 trigger, spot 29.56 points clear — not fired, and for the first time moving away from the trigger rather than toward it. DANGER_UNDERWATER: regime is NORMAL, not DANGER, so it cannot fire; the underwater half is satisfied at -$298 and has been for four sessions, so this flag continues to sit armed on one leg with rv_acceleration as the trigger for the other. Hold. And the infrastructure item is now four days old: `quote_fallback` feeds the mark, the mark feeds capture %, capture % feeds PROFIT_TARGET, and today's print differs from Friday's by more than a third of the credit at risk. Fix the quote source. This is the second consecutive eval where I have called it urgent rather than hygienic.

Behavioural: the discipline held for a third straight session. Scan says NO EDGE, the position is offside, and the book is still 3 contracts — no adds, no averaging down, no re-entry contemplated. Three consecutive passes of the live test I set on Wednesday; that is now approaching a pattern in the good direction, and it is the strongest thing in this file. The specific risk today is different from the last four days and worth naming in advance: a favourable session in a losing deviation trade is where narrative defence starts. The correct read of today is "the mark was probably too pessimistic on Friday and spot cooperated once," not "the $4000 floor thesis is working." The open process item is unchanged and is now five days old — the GLD-level number that would say the thesis is wrong, plus the explicit acceptance that between here and there this position can bleed on vol alone. Friday's -$411 and today's $113 rebound with no rule change in between are both exhibits for why that second number needs writing down. Standing watches carry forward: directional overrides clustering in gold, and negative-VRP entries attracting narrative defence at exit time. The trader decides; nothing here requires action today.

> **Corrigendum (2026-07-28):** The "unverified mark / fix the quote source" thread running through the 07-22→07-27 evals was mistaken. The `quote_fallback` marks were verified against the DB snapshot as real, tight two-sided quotes (07-27: bid 3.70 / ask 3.95 / mid 3.825; Δ -0.187) — not stale, last-known, or model mids. `quote_fallback` is the *by-design* path for a held strike outside the scan's ATM window (GLD 345 is ~8% OTM, and Sep-18 isn't a scanned expiry), so the marker quotes that one contract directly; it is a live quote equal in quality to a scan-chain mark. The eval read it as suspect only because its input context surfaced the `mark_source` label while **omitting the bid/ask** — fixed 2026-07-28 (the context now carries the spread + an honest `mark_quality`). The marks, capture %, and flags in these entries are sound; there is no quote-source defect.

---

## 2026-07-24 (Friday)

**Book summary:** 1 open · credit at risk $849 · notional $103,500 · top concentration GLD 100%

| # | Ticker | Structure | Strikes | Expiry | Qty | Credit | Mark | uPnL | Capture | DTE | Δ | Regime | v1 Action | v2 Gate | FVRP | Flags |
|---|--------|-----------|---------|--------|-----|--------|------|------|---------|-----|---|--------|-----------|---------|------|-------|
| 1 | GLD | naked_put | 345P | 2026-09-18 | 3 | $2.83 | $4.20 | -$411 | -48% | 56 | -0.20 | NORMAL | NO EDGE | NORMAL | 1.01 | — |

**Assessment:** GLD 345P ×3 (Sep 18, 56 DTE) is still the entire book, and today it marks $4.20 for -$411, capture -48% — the worst print of the trade's three-day life. Before reacting, apply the same discipline as the last two days: `mark_source` is `quote_fallback` for the third consecutive session, so the level remains unverified. But this print is different in kind from yesterday's. Yesterday's $2.83 was the feed freezing at your fill — a mark that abstained. Today's $4.20 *moved*, and it moved exactly the way the vol inputs say it should: sigma_fwd jumped 0.2118 → 0.2265, the largest one-day rise since entry, and an OTM put repricing ~$1.37 higher on a flat tape is precisely what a vol markup looks like. Treat the level as approximate but the direction as probably real. The mark sequence is now $2.83 → $3.675 → $2.83 → $4.20 without a single clean two-sided quote behind any of it, and for the first time the fallback print and the surface inputs agree with each other.

Which settles the attribution question cleanly: this is IV-driven, not delta-driven. GLD closed 371.90, *up* 0.37 on the day — the underlying did nothing, mildly in your favor — and the put still marked against you. Delta went -0.1422 → -0.196 on an up-spot session, which is higher vol fattening an OTM put's delta; unlike Thursday's incoherent greeks, today's set squares internally (vol up, delta out, mark up), and skew_25d recovering 1.00 → 1.91 says yesterday's surface glitch resolved. Buffer to the strike is 26.9 points, ~7.2% of spot, essentially unchanged. The consequence worth staring at: delta closed roughly a third of its remaining distance to the -0.30 TESTED trigger *without spot moving at all*. There is now a live path to a TESTED flag that runs entirely through the vol surface.

The edge picture had one supportive datum left at entry — forward VRP at 1.1156 — and today it died: FVRP 1.0054, dead flat, with fvrp_z at -1.053, the worst of the trade. Signal score has printed 49 → 45 → 40 → 36, four straight lower, NO EDGE for a second consecutive day, vrp_ratio 0.824 still on the wrong side, v2_eligible still false. You are short forward vol that is rising — sigma_fwd up about 12% since entry — at a spot VRP below realized. Meanwhile rv_acceleration hit 0.914, up from 0.738 at entry, still grinding toward the level that flips the regime read. Against the thesis, today is the first session that doesn't contradict consolidation — spot stabilized after the -2% day. But be honest about where the money is going: the thesis is about the gold *price*, and the P&L is coming from the gold *vol surface*. The trade is losing in a channel the thesis doesn't address.

Portfolio level is unchanged in shape: $849 credit at risk against $103,500 notional, GLD 100%. Regime NORMAL, position aligned, no regime conflict — and the signal conflict is now the widest it has been. Regime alignment is permission to hold, not evidence of edge; that line gets truer every print.

Management calls — **no exit rule fires today, and the flags column is empty.** PROFIT_TARGET: capture -48% against the 75% NORMAL-regime threshold; not in the conversation. TIME_EXIT: 56 DTE, the 21-DTE checkpoint is 35 days out, Aug 28. EARNINGS_WALL: earnings_dte null on an ETF, inapplicable for the trade's life. TESTED: |Δ| 0.196 vs 0.30 — not fired, but the closest yet, and it closed distance on a flat spot day. DANGER_UNDERWATER deserves its own sentence today: the flag needs DANGER regime *and* underwater, and for the first time the underwater half is plausibly true. Regime is NORMAL so it cannot fire — but rv_acceleration at 0.914 is exactly the input that would flip the regime, and if it does, this flag arms with one leg already satisfied *and* PROFIT_TARGET simultaneously drops from 75% to 50%. Both standing watchpoints are hotter than yesterday, not cooler. Hold. And the infrastructure item has graduated from hygiene to urgency: three straight days of `quote_fallback`, and the marks now matter — capture feeds PROFIT_TARGET, delta feeds TESTED, and a fallback feed can miss a real exit or fire a false one. Fix the quote source.

Behavioural: the discipline held again. Day three offside, scan at NO EDGE, and the book is still 3 contracts — no averaging down, no re-entry contemplated in a name the scanner won't even watch. That is two consecutive passes of the live test I set on Wednesday, and it earns credit. The open process item gains a wrinkle today: I have been asking for the GLD-equivalent of the $4000 floor as a written invalidation number, and that is still missing — but today demonstrated that a spot floor, even written down, has no jurisdiction over how this trade actually loses. The honest fix is now two numbers: the GLD level where the thesis is wrong, and an explicit acceptance that between here and there the position can bleed on vol alone — with -$411 as the exhibit. Standing watches carry forward unchanged: directional overrides clustering in gold, and negative-VRP entries attracting narrative defence at exit time. The trader decides; nothing here requires action today.

---

## 2026-07-23 (Thursday)

**Book summary:** 1 open · credit at risk $849 · notional $103,500 · top concentration GLD 100%

| # | Ticker | Structure | Strikes | Expiry | Qty | Credit | Mark | uPnL | Capture | DTE | Δ | Regime | v1 Action | v2 Gate | FVRP | Flags |
|---|--------|-----------|---------|--------|-----|--------|------|------|---------|-----|---|--------|-----------|---------|------|-------|
| 1 | GLD | naked_put | 345P | 2026-09-18 | 3 | $2.83 | $2.83 | +$0 | 0% | 57 | -0.14 | NORMAL | NO EDGE | NORMAL | 1.05 | — |

**Assessment:** GLD 345P ×3 (Sep 18, 57 DTE) remains the whole book, and today it marks at exactly $2.83 — the entry credit to the cent, +$0 unrealized, 0% capture. Read that the same way I asked you to read yesterday's -$254: `mark_source` is still `quote_fallback`, and a mark that prints precisely at your fill is the pricing stack reverting to last-known, not the market agreeing with you. So the position has now gone $2.83 → $3.675 → $2.83 in two sessions without a single clean two-sided quote behind any of it. Yesterday I said don't treat the -30% as information until a clean mark confirms it. Today's mark does not confirm or deny — it abstains. Two consecutive days where the P&L line carries no signal.

What *is* real is the tape: GLD closed 371.53 against 379.12 yesterday, roughly -2% in a session. Buffer to the 345 strike compressed from 34.1 points to 26.5, about 7.1% of spot. That is the only genuinely new fact today, and it is delta-relevant — except the reported delta went the other way, -0.17 to -0.1422, with spot down 7.6 points. That combination does not square on its own; the surface input moved underneath it, with skew_25d collapsing 2.08 at entry to 1.00 on today's scan while sigma_fwd kept climbing 0.2028 → 0.2092 → 0.2118. Call this move underlying-driven with an unreliable vol overlay, not IV-driven and not cleanly delta-driven. The honest characterisation is that the greeks are being computed off a surface that is itself drifting, on a name whose option is not quoting.

The edge continues to decay in one direction. Signal score 49 → 45 → 40 across three prints, and the recommendation has now crossed from WATCHLIST to **NO EDGE** — the scanner has gone from "wouldn't sell this" to "wouldn't watch this." vrp_ratio ticked up to 0.814 and FVRP to 1.0542 with fvrp_z recovering to -0.695, both marginal and both still on the wrong side: you remain short vol *below* realized, which was true at entry and has not been fixed by anything since. v2_eligible false. rv_acceleration 0.859, still grinding up from 0.738 at entry. Against the stated thesis — gold consolidates and bounces, $4000 as the floor — one -2% session is not a refutation, but it is also not consolidation, and the thesis has now had two days and zero confirmation. The structure is still doing what a premium seller does; the payment for it is still not there.

Portfolio level is unchanged in shape: $849 credit at risk against $103,500 notional — you are collecting 0.82% of the assignment obligation. GLD reads 100% concentration, arithmetically trivial at n=1 and substantively total. Regime is NORMAL and the position sits inside it, so there is no regime conflict. There is a signal conflict, now wider than at entry, and the distinction matters: regime alignment is permission to hold, not evidence of edge.

Management calls — **no exit rule fires today, and the flags column is empty for a reason.** PROFIT_TARGET: capture 0% against the 75% NORMAL-regime threshold; you would need to buy this back near $0.71. TIME_EXIT: 57 DTE, so the 21-DTE mechanical checkpoint is 36 days out — Aug 28. EARNINGS_WALL: earnings_dte null on an ETF, inapplicable for the life of the trade. DANGER_UNDERWATER: regime is NORMAL, not DANGER, and the position is flat anyway — doubly inapplicable. TESTED: |Δ| 0.1422 against the 0.30 trigger, spot 26.5 points clear of the strike; not close. Hold. The two watchpoints carry forward unchanged: rv_acceleration climbing far enough to flip the regime read, which would drop PROFIT_TARGET from 75% to 50% and pull the exit forward much faster than you are planning for; and delta drifting toward -0.30, which is the only path that converts this from a watch into a defend/roll. I would add a third that is infrastructure, not markets — the PROFIT_TARGET flag is computed off capture %, capture % is computed off the mark, and the mark has been `quote_fallback` for two straight days. Fix the quote source before it matters, because a mechanical exit rule is only as good as the price feeding it.

Behavioural: the notable thing today is what did not happen. The underlying moved 2% against a directional entry and the book is still 3 contracts — no averaging down, no size added to improve the entry. That is the single most common failure mode after a conviction trade goes offside on day two, and it did not occur. One data point, credited. Deviation #1 remains the only specimen in the corpus, and the standing watches hold: whether directional overrides cluster in gold specifically, and whether negative-VRP entries get held past their exit rules because the trader is managing the opinion rather than the flag. That second one now has a live test in front of it — the scan says NO EDGE on GLD today, so if a re-entry or an add gets contemplated in this name, that is the pattern showing itself. And yesterday's process item is still open and got more urgent, not less: the GLD-equivalent of the $4000 gold floor is still not written down, and spot moved 7.6 points toward the strike before it was. The point of fixing an invalidation number in advance is to have it *before* the move. The trader decides; nothing here requires action today.

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
