# Credit Put Spreads — Daily Scan Log

Structured snapshot of the CPS tab per trading day. Sister log to `metrics-logs.md` (Naked Puts) and `daily-briefings.md` (narrative). One entry per scan, descending order.

Authoritative data lives in `cps_candidate_history` + `cps_scan_responses` tables; this file is the human-readable mirror for day-over-day pattern recognition (streak tracking, c/w drift, which tickers stay eligible).

---

## Update Protocol

**Trigger:** After updating `metrics-logs.md` with the day's Naked Puts data, paste the CPS tab into this file.

**Steps:**
1. Receive Credit Put Spreads tab screenshot or data from the user
2. Insert new entry **at the top** of the log (immediately below the `---` after this protocol section)
3. Use heading format: `## YYYY-MM-DD (Day of week)`
4. Capture three blocks per entry: **Scan summary**, **Overlay**, **Candidates table**

**Required fields:**
- **Scan summary** — `Checked X / N actionable / B base_gate / C construction / E execution / O overlay / F confirmation`
- **Overlay** — `VIX <v> / VIX3M <v3> / VVIX <vv> — <status>, <Contango|Backwardation>`
- **Candidates table** — # / Ticker / Action / Days / Score / C/W / Credit / Width / Max Loss / RV Status / Notes

**Optional fields:**
- `Notable:` one-liner ONLY when something is worth flagging (first long streak, first SELL_CPS, regime overlay change, etc.). Don't force it.

**Column order:**
```
| # | Ticker | Action | Days | Score | C/W | Credit | Width | Max Loss | RV Status | Notes |
```

**Action values:** `SELL` | `WATCH` (SELL_CPS / WATCH_CPS — the user-visible chip strings)
**RV Status values:** `Excellent` | `Good` | `Acceptable` | `Caution` | `Avoid / Wait`

---

> **IMPORTANT:** Entries are in **descending order** (newest first). New entries go immediately below this line.

---

## 2026-06-17 (Wednesday)

**Scan summary:** Checked 11 / 0 actionable / 11 base_gate / 0 construction / 0 execution / 0 overlay / 0 confirmation
**Overlay:** VIX 18.44 / VIX3M 20.62 / VVIX 94.5 — NORMAL, Contango

**Notable:** Fifth consecutive zero-name session — but the first printed against a vol tape that finally turned *up* off the floor with conviction, the catalyst direction the standing thesis has waited the entire cycle to see move the right way: **VIX 16.41 → 18.44 (+2.03), VIX3M 19.53 → 20.62 (+1.09), VVIX 87.7 → 94.5 (+6.8)** — spot vol up two full points off Tuesday's pause-at-the-floor, vol-of-vol leaping nearly seven back to within striking distance of 100 after sitting frozen flat yesterday, so the overshoot that bottomed Monday and merely paused Tuesday has now *reversed* into a genuine bounce, the floor confirmed in and the tape turning off it rather than resting on it. And it changed nothing on the board: **11 base_gate / 0 construction**, the eleven-of-eleven sweep re-welding for the fourth time in five sessions, chamber empty for a fifth straight day with not even Friday's lone construction flicker left in the magazine — because a two-point VIX pop, however directionally correct, is not the skew-steepening event the 25% c/w gate requires, and its *shape* underlines the gap: contango compressed for the first time in the cycle, **3.12 → 2.18 (VIX 18.44 vs VIX3M 20.62)**, the front catching a bid faster than the three-month so the curve flattened toward the right structure but kept positive carry by more than two points, still emphatically NORMAL/Contango with nothing underneath to gate. The Days inventory stays at absolute zero for a sixth straight session, and the arithmetic compounds the same way — nothing surfacing today slides the earliest theoretical 2d satisfaction yet another session out, a name appearing tomorrow at 0d unable to clear 2d before Friday, so the Days gate QQQ's spine once made trivial remains an active structural blocker stacked atop the unsolved skew problem. The score tape re-rated *up* almost universally for the third time in a week and once again it bound on nothing — **NFLX 72 → 77 (the lone score anywhere above the 65 gate, now pulling further clear), XLE +10 (22 → 32), HOOD +10 (13 → 23), GOOG +9, JNJ +5, SPY +5, GLD and UBER +3, even XLB resurrecting 0 → 5** against the few faders, **QQQ −8 (42 → 34), WMT −8, IWM −4, SBUX −3** — a near-wholesale green tape that moved the actionable board not one inch, the now-familiar proof that the score axis and the c/w axis are fully independent: scores can vault or crater and the empty board does not flinch, because the binding constraint was never the score, it's the construction/skew c/w test that even a directionally-correct vol move can't substitute for until it scales. The regime context held its darkened shape: label steady at **THE PLAYOFFS**, tradeable pinned **1S / 0C**, and carry stayed *below the zero line for a second straight session* — **avg VRP −1.4 → −1.35 (essentially pinned negative), neg-VRP 71% → 69%**, still better than two-thirds of the eligible pool bleeding negative carry — even as distress drained to a cycle low, **danger pinned at 0 and stress 3 → 1 (9.7% → 3.1%)**. **Still zero SELL_CPS at 23 sessions** — but today is the first entry in the firing case where the headline input finally drifted the *right* way: the vol floor is confirmed in and the tape is turning up, which is the necessary precondition the last fortnight of cycle-low VIX and cycle-wide contango actively denied. What's still missing is everything downstream — the bounce has to *extend* into an actual front-end skew event rather than a two-point pop under still-positive contango; a name has to be on the board at all to catch it (and the sweep is hermetically empty, so there's not even a c/w on screen to watch respond); the Days streak inventory has to climb off zero where it's sat six sessions; and carry, negative for a second straight print, has to refill the premium any future SELL would harvest. Loaded-but-unfired, chamber empty and re-welded shut, the CPS tab stays fully dark — zero names, zero streaks — but for the first time on record the one variable that had been drifting dead wrong is now drifting toward the trigger: still distant, the assembly still three stages from complete, but no longer moving away.

---

## 2026-06-16 (Tuesday)

**Scan summary:** Checked 11 / 0 actionable / 11 base_gate / 0 construction / 0 execution / 0 overlay / 0 confirmation
**Overlay:** VIX 16.41 / VIX3M 19.53 / VVIX 87.7 — NORMAL, Contango

**Notable:** Fourth consecutive zero-name session, and the board held its hermetic shape while the vol slide that emptied it finally stopped falling — barely: **11 base_gate / 0 construction**, the eleven-of-eleven sweep re-welded exactly as it was Monday and back on 06-11, not even the one-name construction flicker of Friday left in the magazine, chamber empty for a fourth straight day. And it printed against a vol tape that ticked *up* for the first time since the cycle-low descent began, though by amounts barely distinguishable from noise: **VIX 16.20 → 16.41 (+0.21), VIX3M 19.36 → 19.53, VVIX 87.6 → 87.7 (+0.1, effectively pinned)** — spot vol nudging a fifth of a point off Monday's cycle floor, vol-of-vol frozen flat well under 100, so the overshoot bottomed but didn't reverse: this is the tape pausing at the floor, not turning off it, and a quarter-point VIX uptick is nowhere near the skew-steepening event the gate requires. The Days inventory stays at absolute zero for a fifth straight session, and the arithmetic compounds the same way it has all week — with nothing surfacing today the earliest theoretical 2d satisfaction slides yet another session out, a name appearing tomorrow at 0d unable to clear 2d before Thursday, so the Days gate that QQQ's spine once made trivial remains an active structural blocker stacked atop the unsolved skew problem. The genuinely instructive cross-current is the mirror image of Monday's: where yesterday scores **re-rated up almost universally and it changed nothing**, today they **re-rated down almost universally and it *also* changed nothing** — **JNJ −26 (56 → 30, handing back Monday's entire +26 in one session), NKE collapsing −67 (67 → 0, the ex-lone-score-above-gate now obliterated), XLE −12, KO and HOOD −10, HD and AMZN −9, GOOG and MCD and CAT −7, PLTR −5, even NFLX fading 75 → 72** but still the lone score anywhere above the 65 gate — a near-wholesale red tape that emptied nothing further because there was nothing left to empty, the cleanest back-to-back proof yet that the score axis and the c/w axis are fully independent: scores can vault past 65 or crater beneath it and the actionable board does not move, because the binding constraint was never the score, it's the skew/construction c/w test that VIX level cannot substitute for. The overlay stays comfortable on a flat-vol day — **contango 3.16 → 3.12 (VIX 16.41 vs VIX3M 19.53)**, a hair off Monday's cycle-wide cushion but still emphatically NORMAL/Contango ON with nothing underneath to gate — yet the regime context darkened hard in the one column that matters for selling premium: the label held **THE PLAYOFFS** but the tradeable count downshifted **2S / 1C → 1S / 0C** (three tradeable to one), and carry didn't just rot, it crossed the zero line — **avg VRP +0.5 → −1.4, the first negative average of the cycle, smashing through the floor it set only yesterday, with neg-VRP 52% → 71%**, better than seven of ten eligible names now bleeding negative carry — even as distress kept draining, **danger pinned at 0 and stress 4 → 3 (12.1% → 9.7%)**. That is the worst possible backdrop for the first SELL: an average eligible name now carrying *negative* VRP means the pool is, on average, paying you not to sell vol, the precise opposite of the rich-premium condition the framework wants beneath a steep-skew trigger. **Still zero SELL_CPS at 22 sessions** — and today moves the catalyst *further* over the horizon, not closer: VIX bottomed but didn't turn, so skew stays flat under cycle-wide contango; scores cratered on the one axis the screen has already proven twice this week it doesn't bind on; the Days streak inventory sits at zero for a fifth session; and carry just went outright negative, draining the premium any future SELL would need to harvest. Loaded-but-unfired, chamber empty and re-welded shut, the CPS tab stays fully dark — zero names, zero streaks — with the vol floor, the steep term structure, and now negative average carry all aligned against the skew event the first SELL requires, the firing case as far from assembly as it has been at any point on record.

---

## 2026-06-15 (Monday)

**Scan summary:** Checked 11 / 0 actionable / 11 base_gate / 0 construction / 0 execution / 0 overlay / 0 confirmation
**Overlay:** VIX 16.20 / VIX3M 19.36 / VVIX 87.6 — NORMAL, Contango

**Notable:** Third consecutive zero-name session, and the board scrubbed itself back to a full sweep even as the vol cycle that emptied it kept draining beneath: **11 base_gate / 0 construction** — Friday's lone construction flicker is gone, the one round that briefly showed in the magazine reabsorbed, the gate stack back to the hermetic eleven-of-eleven of Thursday 06-11. And it printed against a vol tape carving fresh cycle lows in every column: **VIX 17.68 → 16.20 (−1.48), VIX3M 20.51 → 19.36, VVIX 93.8 → 87.6 (−6.2)** — spot vol now a clean point-and-a-half under Friday's already-cycle-low read, vol-of-vol sinking further beneath 100 to its lowest of the visible cycle, so the round-trip that *completed* Friday has now *overshot* to the downside: the entire 06-05 → 06-10 expansion (peak VIX 22.22, peak VVIX 108.2) isn't merely retraced but undercut, the tape quieter now than at any point the cycle has logged. The Days inventory stays at absolute zero for a fourth straight session, and with the board empty again the earliest theoretical 2d satisfaction slides yet another session out — a name surfacing tomorrow at 0d can't clear 2d before midweek, so the gate QQQ's 15-session spine once made trivial remains an active structural blocker stacked atop the skew problem. The genuinely instructive cross-current is that scores **re-rated up almost universally and it changed nothing**: **NFLX 62 → 75 (now the lone score anywhere above the 65 gate), JNJ +26 (30 → 56), PLTR +21, TSLA +16, QQQ clawing 27 → 40, MSFT +12, HD +13, IWM +9, even XLB resurrecting 0 → 10** — the prior week's de-rate reversing hard, a near-wholesale green tape — yet the actionable screen didn't take a single name, the cleanest proof yet that the score axis and the c/w axis are independent: NFLX vaulted clean past 65 and the board stayed empty, because the binding constraint was never the score, it's the skew/construction c/w test the last five sessions have shown VIX level can't substitute for. The overlay, predictably comfortable on a vol-down day, posted its widest cushion of the entire cycle — **contango 2.83 → 3.16 (VIX 16.20 vs VIX3M 19.36)**, NORMAL/Contango emphatically ON with nothing underneath to gate — and the regime context sharpened the divergence rather than softening it: the label **upgraded back to THE PLAYOFFS, 2S / 1C**, the model now flagging two outright sells (3 tradeable) at the exact moment the CPS screen carries zero, the starkest gap yet between the macro read and this tab, while the surface/tail inversion intensified to its extreme — **danger fully drained 2 → 0, stress 9 → 4 (28.1% → 12.1%)**, distress essentially gone, even as carry rotted to a cycle worst: **avg VRP +0.8 → +0.5 (cycle low) and neg-VRP 44% → 52%**, crossing into outright majority for the first time, more than half the eligible pool now bleeding negative carry as outright distress evaporates. **Still zero SELL_CPS at 21 sessions** — and today moves the framework *further* from a fire, not closer: the thesis needs skew steepening or a higher-delta build to lift c/w past 25% on a name simultaneously holding score ≥ 65 and ≥ 2d, and every input drifted the wrong way at once — VIX at a cycle low and contango at a cycle wide is the vol regime actively *flattening* skew, the precise opposite of the catalyst the gate requires; the board emptied back to a clean sweep; streaks held at zero; and the one thing that did improve, scores, is the single axis the screen has already proven it doesn't bind on. Loaded-but-unfired, chamber empty again after a one-session glimpse of a round, gate shut and re-welded; CPS tab stays fully dark — zero names, zero streaks — and with vol at the floor and the term structure at its steepest of the cycle, the catalyst the first SELL needs sits further over the horizon than at any prior point on record.

---

## 2026-06-12 (Friday)

**Scan summary:** Checked 11 / 0 actionable / 10 base_gate / 1 construction / 0 execution / 0 overlay / 0 confirmation
**Overlay:** VIX 17.68 / VIX3M 20.51 / VVIX 93.8 — NORMAL, Contango

**Notable:** Second consecutive zero-name session, and the vol cycle that emptied the board has now fully unwound beneath it: **VIX 19.44 → 17.68 (−1.76), VIX3M 21.42 → 20.51, VVIX 100.6 → 93.8 (−6.8, back under 100)** — ending vol-of-vol's two-session stand above the line, its one genuinely new wrinkle of the week, and putting spot vol *below* every print since the 06-05 spike era began (under even 06-08's 18.92 revert), so the Wednesday cycle-high of 22.22 has round-tripped completely in two sessions and the third spike-revert of the cycle is now archived in full. The gate stack shifted by exactly one notch: **10 base_gate / 1 construction** versus Thursday's clean sweep of eleven, meaning one name clawed back over the base gate only to die at the construction check — still **0 actionable**, but the first sign since Wednesday that anything can even reach the c/w test, which is where the standing thesis says the fight actually is. The streak inventory stays at absolute zero for a third straight session, and the Days arithmetic keeps compounding: with nothing surfacing today, the earliest theoretical 2d satisfaction slips yet another session out — a name appearing Monday at 0d can't clear 2d before midweek — so the gate that QQQ's 15-session spine once made trivial remains an active structural blocker stacked *on top of* the skew problem. The overlay, predictably comfortable on a revert day, posted its widest cushion of the visible cycle: **contango 1.98 → 2.83 (VIX 17.68 vs VIX3M 20.51)**, NORMAL/Contango emphatically ON with nothing underneath to gate. And the regime context executed a perfect inversion of Thursday's split — where yesterday the surface healed while the tail rotted, today the tail healed while the surface rotted: **danger collapsed 7 → 2 names (21.2% → 6.2%) and stress 14 → 9 (42.4% → 28.1%)**, both retreating hard off cycle highs, while **avg VRP sagged +1.4 → +0.8 and neg-VRP jumped 33% → 44%** — a fresh cycle high, nearly half the eligible pool now carrying negative carry even as outright distress drains away, the label easing to **REGULAR SEASON, 1S / 1C**. The score tape tells the same two-track story: the de-rate stays parked exactly where this tab lives — **SPY 32 → 28, QQQ 33 → 27, IWM −9 to 20, GLD 26 → 18** (the ex-lone-name now eight points further from ever returning), **SBUX −8, XLB collapsing to zero for the second time in a week (20 → 0)** — while the bid rotates into mega-cap singles the actionable board doesn't carry: **MSFT +9 to 32, META +7, MCD and UBER and NVDA +6, AAPL and PLTR +5**, with **NKE fading 73 → 68 but still the only score anywhere above the 65 gate**. **Still zero SELL_CPS at 20 sessions** — and the firing case now reads as a three-stage assembly problem with stage one barely flickering: one name reached construction today (proof the base gate isn't hermetically sealed), but it would need to surface as actionable at all, survive two further sessions for the Days gate, and then catch the skew event or higher-delta build that four straight tests have shown VIX level cannot substitute for — and with VIX now at 17.68 and contango at its widest, the vol regime is actively moving *away* from the kind of skew-steepening event the 25% c/w gate requires. The framework remains loaded-but-unfired with an empty chamber, though for the first time in two sessions there's a round visible in the magazine; CPS tab stays dark, zero names, zero streaks, the gate shut but no longer welded.

---

## 2026-06-11 (Thursday)

**Scan summary:** Checked 11 / 0 actionable / 11 base_gate / 0 construction / 0 execution / 0 overlay / 0 confirmation
**Overlay:** VIX 19.44 / VIX3M 21.42 / VVIX 100.6 — NORMAL, Contango

**Notable:** The board finally went all the way to empty — **0 actionable of 11 checked, all eleven names failing the base gate**, the first zero-name session of the cycle — and it did so on a *revert* day, not a spike day: **VIX 22.22 → 19.44 (−2.78), VIX3M 22.89 → 21.42, VVIX 108.2 → 100.6 (−7.6)**, so Wednesday's "this is no longer a one-session spike-and-revert" read survived exactly one session before the tape filed it with 06-05 and 06-08 — the third spike-revert of the cycle, just launched from a higher base — with one genuinely new wrinkle: **VVIX held above 100 for a second consecutive session for the first time**, vol-of-vol refusing to fully stand down even as spot vol round-tripped nearly three points. GLD's tenure as the lone name lasted exactly one day: **score 30 → 26**, off the board before its Days counter ever ticked past 0d, meaning the streak that reset the whole inventory to zero on Wednesday died without ever starting — the board now carries **no streaks anywhere for a second straight session**, and with nothing eligible today the earliest theoretical 2d-gate satisfaction slips another session out (a name surfacing tomorrow at 0d can't reach 2d until three sessions from now), so the Days gate, once trivially satisfied by QQQ's 15-session spine, has become an active blocker in its own right. The overlay repeated its now-familiar rhythm — knife-edge on spike days, comfortable on revert days — **contango re-widening 0.67 → 1.98 (VIX 19.44 vs VIX3M 21.42)**, the term-structure threat receding for the second time, NORMAL/Contango comfortably ON with nothing underneath it to gate. The regime context split cleanly in two: the surface healed — **avg VRP +1.1 → +1.4, neg-VRP 38% → 33%**, label steady at **REGULAR SEASON, 1S / 1C** — while the tail kept rotting, **danger 5 → 7 names (21.2%) and stress 10 → 14 (42.4%), both fresh cycle highs**, nearly half the eligible pool now stressed two sessions after danger first went nonzero. And the score tape confirms why the CPS screen specifically is starving: the de-rate is concentrated exactly where this tab lives — **SPY −15 (47 → 32), CAT −14, QQQ 37 → 33, MSFT −6, META −4, GLD −4** — while the only strength is rotating into single names the actionable board doesn't carry: **NKE 67 → 73 (the lone score anywhere above the 65 gate), NFLX 54 → 60, JPM +10, JNJ +8, XLB resurrecting 0 → 20** after Tuesday's collapse to zero. **Still zero SELL_CPS at 19 sessions** — and today's entry in the firing case is the starkest yet: not a wrong variable moving, but *no variable visible at all*. The skew/construction thesis can't even be tested on an empty board — there is no c/w on the screen to watch ignore a vol move — so the path to the first SELL now requires three things to assemble from scratch in sequence: a name clearing the base gate at all, surviving two further sessions to satisfy 2d, and then the skew event or higher-delta build that four straight tests have shown VIX level cannot substitute for. With danger and stress at cycle highs beneath a nominally benign overlay, the framework declining to hold even a WATCH looks less like starvation and more like triage; the gate isn't stuck, it's shut on purpose. CPS tab goes fully dark for the first time — zero names, zero streaks, loaded-but-unfired now with nothing in the chamber.

---

## 2026-06-10 (Wednesday)

**Scan summary:** Checked 11 / 1 actionable / 9 base_gate / 1 construction / 0 execution / 0 overlay / 0 confirmation
**Overlay:** VIX 22.22 / VIX3M 22.89 / VVIX 108.2 — NORMAL, Contango

| # | Ticker | Action | Days | Score | C/W | Credit | Width | Max Loss | RV Status | Notes |
|---|--------|--------|------|-------|------|--------|-------|----------|-----------|-------|
| 1 | GLD | WATCH | 0d | 30 | 12.7% | $1.27 | $10 | $8.73 | Caution | Thin premium |

**Notable:** The vol event came back — bigger than Friday's — and the board responded by getting *emptier*. **VIX 19.87 → 22.22 (+2.35, a new cycle high above 06-05's 21.51), VVIX 95.8 → 108.2 (+12.4, smashing through 100 for the second time and well past the 102.0 peak), VIX3M 21.31 → 22.89** — this is no longer a creep or a one-session spike-and-revert, it's a higher high in both vol and vol-of-vol — and the actionable board's answer was to swap its lone name for a worse one: **TLT fell off entirely** (score 38 → 35, slipping under the base gate as fails tick 9 → 9 with construction absorbing the churn), its 3-day streak dying at 3d, replaced by **GLD alone at 0d — score 30, c/w 12.7%, $1.27 credit on a $10 width, Caution RV**. That's the fourth and most emphatic proof of the 06-05 thesis: the cycle's highest VIX print produced the cycle's *lowest* lone-name c/w (12.7% vs TLT's thrice-pinned 14.0%), the gap to the 25% gate now 12.3 points — vol keeps going up and the credit lever keeps not moving, because it was never the lever. GLD does break one pattern worth noting: at ~$127 max gain per contract it's the first **economically real spread** to hold the board since the index names de-rated — no micro-spread asterisk — but it fails everything else: score 30 is 35 points under the 65 gate, **0d resets the Days clock to zero across the entire board for the first time this cycle** (no name anywhere carries a streak, so even a perfect tomorrow leaves the 2d gate two sessions away at minimum), and **Caution RV** is the first sub-Good reading to headline the table in the modern era of this board. Meanwhile the regime context turned genuinely darker under the nominally-ON overlay: the label rolled back to **REGULAR SEASON, 1S / 2C, avg VRP +1.0 → +1.1** roughly flat, but **danger jumped 0 → 5 names (15.6%) — the first nonzero danger reading of the cycle — and stress 7 → 10 (31.2%)**, nearly a third of the eligible pool now stressed, neg-VRP 36% → 38%; the de-rate broadened too (**XLB −19 to a score of zero, HD −15, XLI −10, NVDA and XLV −9, XLF and MCD −8**, gainers capped at IWM's +6). And the overlay is back on the knife's edge: **contango compressed 1.44 → 0.67 (VIX 22.22 vs VIX3M 22.89)**, the second-tightest reading of the cycle behind Friday's 0.31 — the same perverse tension as 06-05, where the next leg of the very vol expansion that might finally steepen skew would invert the term structure and flip the NORMAL/Contango gate OFF before c/w ever reached 25%. **Still zero SELL_CPS at 18 sessions** — and today's contribution to the firing case is purely subtractive: the skew/construction thesis got its fourth confirmation (VIX +2.35 to a cycle high, c/w fell), the Days streak inventory went to zero, the only name on the screen fails four of five gates including RV for the first time, and the tape beneath is re-stressing fast enough (danger 15.6%, stress 31.2%) that the framework declining to sell puts into it looks less like a stuck gate and more like the gate doing its job. The framework remains correctly loaded-but-unfired; CPS tab stays WATCH-only at a fully reset board.

---

## 2026-06-09 (Tuesday)

**Scan summary:** Checked 11 / 1 actionable / 9 base_gate / 1 construction / 0 execution / 0 overlay / 0 confirmation
**Overlay:** VIX 19.87 / VIX3M 21.31 / VVIX 95.8 — NORMAL, Contango

| # | Ticker | Action | Days | Score | C/W | Credit | Width | Max Loss | RV Status | Notes |
|---|--------|--------|------|-------|------|--------|-------|----------|-----------|-------|
| 1 | TLT | WATCH | 3d | 38 | 14.0% | $0.07 | $0.50 | $0.43 | Excellent | Thin premium |

**Notable:** A modest vol creep, and the board didn't blink. The day after Friday's spike round-tripped, Tuesday saw index vol tick back up a touch — **VIX 18.92 → 19.87 (+0.95), VVIX 92.4 → 95.8 (+3.4, still under 100), VIX3M 20.79 → 21.31** — but this was a creep, not a catalyst, and it produced exactly nothing on the actionable front: the board stays at its cycle-low single name, **TLT alone**, unchanged for the third straight session at **score 38 / c/w 14.0% / $0.07 credit on a $0.50 width** (~$7 max gain, retail-uneconomic), base-gate fails ticking **8 → 9** as the de-rate absorbs one more name. The one quietly useful data point is the cleanest reconfirmation yet of the 06-05 thesis: **vol firmed nearly a full VIX point and TLT's c/w didn't move a single tick** — pinned at 14.0% for the third consecutive session — exactly as a skew/construction-governed c/w should behave when index IV rises without skew steepening. The +0.95 move richened credit not at all, just as the +6.11 spike on 06-05 actually compressed it; the framework has now watched c/w ignore both a vol-down round-trip AND a vol-up creep, and the lever stays where 06-05 placed it — **skew steepness or higher-delta strike selection, not VIX level.** Days: **TLT logs its 3rd consecutive eligible session (2d → 3d)**, and the irony compounds — the only name carrying any streak on the board is the one that structurally *cannot* fire, a $7-max-gain micro-spread sitting at score 38 (27 below the 65 gate) and c/w 14.0% (11 points short of 25); with QQQ's 15-session spine broken Monday and the index names de-rated out of contention, there's no longer a single name on the screen even theoretically tracking toward the gate. Under the surface the tape cooled unevenly: the broad de-rate continued — **XLB collapsed −36 (55 → 19), XLF −16 (51 → 35), XLI −9, JNJ −9** — and regime thinned in step, **THE PLAYOFFS, 1S / 2C (down from 1S / 5C), avg VRP +1.3 → +1.0, neg-VRP 42% → 36%** — but the notable cross-current is **stress jumping 2 → 7 names (6.1% → 21.2%)** even as outright negative-VRP names *fell*, a quiet re-stressing of the rich tail that firmed vol without firming credit, danger still 0%. The overlay cushion compressed again — **contango 1.87 → 1.44 (VIX 19.87 vs VIX3M 21.31)** — narrower than yesterday but comfortably ON, no term-structure threat. **Still zero SELL_CPS at 17 sessions** — and today adds nothing to the firing case except a third proof that the wrong variable keeps moving: vol went down-and-up across three sessions, c/w never flinched, and the first SELL still requires what no recent session has supplied — a skew event or higher-delta build that lifts c/w past 25% on a name simultaneously holding score ≥ 65 and ≥ 2d, a combination that, with the index names now de-rated and only an uneconomic TLT streak left standing, isn't even visible on the current screen. The framework remains correctly loaded-but-unfired; CPS tab stays WATCH-only at its emptiest board of the cycle.

---

## 2026-06-08 (Monday)

**Scan summary:** Checked 11 / 1 actionable / 8 base_gate / 2 construction / 0 execution / 0 overlay / 0 confirmation
**Overlay:** VIX 18.92 / VIX3M 20.79 / VVIX 92.4 — NORMAL, Contango

| # | Ticker | Action | Days | Score | C/W | Credit | Width | Max Loss | RV Status | Notes |
|---|--------|--------|------|-------|------|--------|-------|----------|-----------|-------|
| 1 | TLT | WATCH | 2d | 38 | 14.0% | $0.07 | $0.50 | $0.43 | Excellent | Thin premium |

**Notable:** The Friday spike round-tripped in a single session — and took the entire actionable board with it. The vol event that landed Friday (VIX 21.51, VVIX cracking 100 for the first time this cycle) reverted almost as fast as it arrived: **VIX 21.51 → 18.92 (−2.59), VVIX 102.0 → 92.4 (−9.6, back under 100), VIX3M 21.82 → 20.79** — and with the vol went the signal-quality surge it produced. The record index scores from Friday collapsed in lockstep: **QQQ 81 → 32 (−49), SPY 79 → 51 (−28), IWM 50 → 23 (−27)** — all three dropped off the actionable board entirely, base-gate fails jumping **5 → 8** to absorb them, leaving a **one-name board for the first time this cycle: TLT alone.** This is the cleanest possible confirmation of Friday's hard-won thesis update — those all-time-high scores were **vol-borne and ephemeral, not durable construction edge**: the spike that produced them lasted exactly one session, an echo of the EEM 56.3% monster and QQQ's 20.4% c/w, each of which also vanished in 24 hours. The pattern is now unmistakable — this framework keeps generating **one-session artifacts that revert**, and Friday's VVIX-100 break + score surge was just the latest, gone in a single Monday. **The QQQ streak is broken.** After fifteen consecutive eligible sessions — the spine of the entire loaded-but-unfired era — QQQ falls off the board at score 32, ending the run that defined the 10d-through-15d count, and for the first time the zero-SELL session counter **decouples from QQQ's Days streak**: the streak ends at 15, but the framework stays unfired into its **16th session** — and the lone name still carrying a streak is, ironically, **TLT at 2d (1d → 2d), the perennial micro-spread trap** ($0.07 credit / $0.50 width, ~$7 max gain per contract, retail-uneconomic) now standing as the last actionable name on the entire board. The c/w gate is no closer — **TLT 14.0% vs the 25% requirement**, nothing within eleven points of it — and with the index names de-rated out of contention there's no longer even a *theoretical* path to the gate on the screen; Friday's spike never moved c/w in the first place (QQQ topped at 14.9% at VIX 21.5), and now the names that could conceivably build toward it have evaporated. The one consolation is the overlay backing off the knife's edge: Friday's contango had compressed to a razor **0.31 points**, one push from backwardation flipping the NORMAL/Contango gate OFF; today it **re-widened to 1.87 (VIX 18.92 vs VIX3M 20.79)**, so the term-structure threat receded and the overlay gate is comfortably ON again — cold comfort when nothing else qualifies. Regime cooled in step: **THE PLAYOFFS, 1S / 5C, avg VRP +1.8 → +1.3**, the SELL-grade pool thinning from **3 names to 1**, **neg-VRP 41% → 42%, stress 1 → 2 names (6.1%)**, danger 0%. **Still zero SELL_CPS at 16 sessions** — and the takeaway compounds Friday's: the catalyst didn't just prove it was the wrong variable, it proved it was a *transient* one — the vol came and went inside three sessions, the board emptied back to a single uneconomic micro-spread, and the first SELL still requires what no recent session has supplied: a skew event or a higher-delta build that lifts c/w on a name simultaneously holding score ≥ 65 and ≥ 2d. The framework remains correctly loaded-but-unfired; CPS tab stays WATCH-only, now at its emptiest board of the cycle.

---

## 2026-06-05 (Friday)

**Scan summary:** Checked 11 / 4 actionable / 5 base_gate / 2 construction / 0 execution / 0 overlay / 0 confirmation
**Overlay:** VIX 21.51 / VIX3M 21.82 / VVIX 102.0 — NORMAL, Contango

| # | Ticker | Action | Days | Score | C/W | Credit | Width | Max Loss | RV Status | Notes |
|---|--------|--------|------|-------|------|--------|-------|----------|-----------|-------|
| 1 | QQQ | WATCH | 15d | 81 | 14.9% | $1.19 | $8 | $6.81 | Excellent | Thin premium |
| 2 | SPY | WATCH | 0d | 79 | 13.0% | $0.65 | $5 | $4.35 | Excellent | Thin premium |
| 3 | IWM | WATCH | 0d | 50 | 15.6% | $0.63 | $4 | $3.37 | Good | Thin premium |
| 4 | TLT | WATCH | 1d | 38 | 14.0% | $0.07 | $0.50 | $0.43 | Excellent | Thin premium |

**Notable:** The vol event the tab waited fifteen sessions for finally arrived — and it falsified the standing thesis instead of firing it. After the 06-01 uptick rolled over and fourteen sessions concluded "c/w cannot reach 25% without a macro vol event," that event landed hard today: **VIX 15.40 → 21.51 (+6.11), VVIX 85.8 → 102.0 — cracking 100 for the first time this cycle (+16.2) — VIX3M 19.23 → 21.82**, the broad index-vol expansion the CPS tab has awaited since the streak began. And the result is the cleanest refutation the framework has produced: **QQQ's c/w went the WRONG way, 20.4% → 14.9%**, reverting precisely to its 06-03 reading ($1.19 credit / $8 width), so yesterday's record "construction-driven" 20.4% **vanished in exactly one session** — an echo of the EEM 56.3% monster — and the gap to the 25% SELL_CPS gate **re-widened from 4.6 points back to 10.1.** The catalyst came and the gate moved *further away*, forcing the thesis to be rewritten at the root: **the binding constraint was never VIX level.** A delta-targeted vertical's c/w tracks short-strike delta and put skew, not absolute IV, which is why a 6-point VIX spike lifted credit not at all on a held $8 width — the algo simply re-struck at the same delta. The prior twelve sessions' inference "need VIX low-to-mid 20s for 25% c/w" is now directly contradicted: **VIX printed 21.5 and c/w fell**; the real lever is skew steepness or more aggressive strike selection, neither of which a moderate one-session spike supplied. What the spike DID do is surge signal quality to all-time highs — **QQQ score 70 → 81 (+11, a new record), SPY 54 → 79 (+25), IWM 37 → 50 (+13)** — sharpening the SELL signal across every index ETF (all Excellent/Good RV); QQQ now clears **four of five gates by its widest margin yet (score 81 ≫ 65 ✓, 15d ✓, Excellent ✓, NORMAL/Contango ✓), only c/w blocks**, but the lone blocker just got *harder*, not closer. **Days: QQQ logs its 15th consecutive eligible session, still solo** — SPY, which dropped off the board entirely yesterday, is back today but at **0d, so the dual streak stays broken** — with IWM (0d, back on) and TLT (1d) rounding out a four-name actionable board (4 actionable / 5 base_gate / 2 construction). The overlay is now on a knife's edge worth flagging: **contango compressed to just 0.31 points (VIX 21.51 vs VIX3M 21.82) from 3.83 yesterday** — one more push inverts the term structure to backwardation and flips the currently-satisfied NORMAL/Contango gate OFF, the perverse tension being that **a further vol spike could make a SELL_CPS *harder*, not easier** (steepening skew to help c/w while threatening to knock out the overlay gate). Micro notes: **XLF cratered −22 (74 → 52) off yesterday's top score and fell off the actionable board entirely**; TLT is the usual micro-spread trap ($0.07 / $0.50, ~$7 max gain, retail-uneconomic); SPY (13.0%) and IWM sit near their structural floors. Regime stays benign despite the spike — **THE PLAYOFFS, 3S / 3C + 1W, avg VRP +1.8** (down from +2.4), **neg-VRP jumped 27% → 41%** as the spike compressed VRP broadly, stress 1 name (3.1%), danger 0%. **Still zero SELL_CPS at 15 sessions** — but for the first time the conclusion isn't "waiting for the catalyst," it's "the catalyst arrived and proved it was never the right variable": c/w is governed by skew/construction, not VIX, so the first SELL now requires a skew event or a higher-delta build, not the index-vol spike that just came and went. The framework remains correctly loaded-but-unfired; CPS tab stays WATCH-only.

---

## 2026-06-04 (Thursday)

**Scan summary:** Checked 11 / 3 actionable / 4 base_gate / 4 construction / 0 execution / 0 overlay / 0 confirmation
**Overlay:** VIX 15.40 / VIX3M 19.23 / VVIX 85.8 — NORMAL, Contango

| # | Ticker | Action | Days | Score | C/W | Credit | Width | Max Loss | RV Status | Notes |
|---|--------|--------|------|-------|------|--------|-------|----------|-----------|-------|
| 1 | XLF | WATCH | 1d | 74 | 15.0% | $0.08 | $0.50 | $0.42 | Good | Thin premium |
| 2 | QQQ | WATCH | 14d | 70 | 20.4% | $1.63 | $8 | $6.37 | Excellent | — |
| 3 | TLT | WATCH | 0d | 37 | 13.5% | $0.13 | $1 | $0.86 | Excellent | Thin premium |

**Notable:** **Days = 14d — QQQ's solo streak, and the closest the c/w gate has ever come.** QQQ logs its **14th consecutive eligible session**, but for the first time it carries the streak alone: **SPY dropped off the board entirely** (score 62 → 54, −8), ending the dual SPY/QQQ run that held unbroken from 10d through 13d — the 14d counter is now QQQ-only. The headline is QQQ's **c/w breaking into the 20s for the first time ever: 14.9% → 20.4%**, a new record that compresses the distance to the 25% SELL_CPS gate from yesterday's 10.1 points to just **4.6**. The gate structure is unchanged — **four of five satisfied (score 70 ≥ 65 ✓, 14d ✓, Excellent RV ✓, NORMAL/Contango ✓), only c/w still blocks** — but it has never been this close, and the *mechanism* of the jump partially complicates yesterday's "need VIX low-to-mid 20s for 25% c/w" conclusion: the c/w expansion came from **credit richening ($1.19 → $1.63 on a held $8 width) while VIX actually FELL (16.06 → 15.40)** — so skew/strike-construction supplied ~5.5 c/w points with zero help from index vol. That argues the first SELL may not require the full VIX-22 spike the prior twelve sessions implied; a few more points of construction-driven c/w on a confirmed name could close the gap. But temper it: this is a single-name, single-session move, **not** a regime event — **the 06-01 VIX uptick has now fully reversed** (16.06 → 15.40, **VVIX 89.8 → 85.8, back at the 05-29 cycle low of 86.1**), so the "first inflection worth tracking" lasted exactly two sessions and rolled over; the systemic catalyst is still absent and the CPS tab — the cleaner gauge of broad vol — confirms it. **XLF score surged 60 → 74 (+14), vaulting to the top CPS score**, but it's the textbook **micro-spread trap**: $0.08 credit / $0.50 width = ~$8 max gain per contract, retail-uneconomic, and only **1d confirmed (< 2d gate)** — highest score ≠ tradeable, tracking-only. **XLI collapsed −37 (69 → 32)**, finally resolving the multi-day construction-reject saga — the former NP SELL-grade name is out of contention entirely, no longer even base-relevant (NP score ≠ CPS buildability, now fully decayed). **TLT cleared back onto the board** (0d, Excellent RV, vrp_ratio recovered above the 1.15 boundary it failed yesterday) but at score 37 / c/w 13.5% it's nowhere near actionable. Base-gate fails 4 / construction 4 / actionable 3; regime is benign — **THE PLAYOFFS, 3S / 4C + 2W, avg VRP +2.4**, stress 6.1%, danger 0%, neg-VRP 27%. **Still zero SELL_CPS at 14 sessions** — but the binding constraint just demonstrably narrowed for the first time: c/w climbed toward the gate on construction alone, so the standing thesis updates from "c/w cannot move without a VIX event" to "c/w *can* inch up via skew, but needs either a couple more construction points or a modest vol uptick to clear 25% on a name that simultaneously holds score ≥ 65 and ≥ 2d." The framework remains correctly loaded-but-unfired; CPS tab stays WATCH-only.

---

## 2026-06-03 (Wednesday)

**Scan summary:** Checked 11 / 5 actionable / 3 base_gate / 3 construction / 0 execution / 0 overlay / 0 confirmation
**Overlay:** VIX 16.06 / VIX3M 19.76 / VVIX 89.8 — NORMAL, Contango

| # | Ticker | Action | Days | Score | C/W | Credit | Width | Max Loss | RV Status | Notes |
|---|--------|--------|------|-------|------|--------|-------|----------|-----------|-------|
| 1 | QQQ | WATCH | 13d | 71 | 14.9% | $1.19 | $8 | $6.81 | Excellent | Thin premium |
| 2 | SPY | WATCH | 13d | 62 | 12.6% | $0.63 | $5 | $4.37 | Excellent | Thin premium |
| 3 | XLF | WATCH | 0d | 60 | 14.0% | $0.07 | $0.50 | $0.43 | Acceptable | Thin premium |
| 4 | XLE | WATCH | 0d | 42 | 15.5% | $0.15 | $1 | $0.85 | Good | Thin premium |
| 5 | IWM | WATCH | 1d | 38 | 15.5% | $0.62 | $4 | $3.38 | Good | Thin premium |

**Notable:** **The "closest ever" milestone — and the definitive proof of the 13-session thesis.** For the first time in CPS history a candidate clears the **score gate**: QQQ score **71 ≥ 65**, with **13d** confirmation (≥2d ✓), **Excellent** RV, and a clean NORMAL/Contango overlay. **Four of the five SELL_CPS gates are satisfied — only c/w blocks it (14.9% vs the 25% requirement).** This concretely settles the hypothesis the prior 12 sessions could only infer: the binding constraint is the **low-vol c/w ceiling, not signal quality.** The best-case clean SELL signal finally arrived (QQQ 71 / 13d / Excellent / contango) and the spread STILL tops out at ~15% c/w because **VIX is flat at 16.06** — no expansion. The clean index SELL signals (QQQ/XLI in the NP tab) came from contango + RV deceleration + IV-percentile, NOT from rising absolute IV, so index c/w stays pinned (QQQ 14.9%, SPY 12.6% near its floor). To reach 25% c/w, QQQ IV would need to be materially higher (VIX low-to-mid 20s). **The EEM validation — within one session:** yesterday's record **56.3% c/w monster vanished entirely** — EEM's vrp_ratio fell to 1.08 (< 1.15), base-gate-failed, and dropped off the board. The "richest spread ever recorded" was a one-day stressed-premium artifact, exactly as the High-credit/width tail-risk warning implied. The framework's caution was vindicated in 24 hours: the spread you didn't take is already gone — textbook confirmation that high c/w on a CAUTION-regime name is fear, not edge. **XLI construction-rejected for the 2nd straight day** despite being an NP SELL (69) — flat-ish slope (0.97) still won't build a clean defined-risk spread. A SELL-grade index name producing no CPS candidate: NP score ≠ CPS buildability, now proven on a SELL. **Micro-spread traps:** XLF $0.07 credit / $0.50 width and XLE $0.15 / $1 width are retail-uneconomic ($7–15 max gain per contract) — tracking-only, ignore for execution (3 construction rejects = XLI + the thin-build names). **Base-gate fails (3):** GLD (ratio 1.04), EEM (ratio 1.08), TLT (ratio ~1.15 boundary). **Still zero SELL_CPS at 13 sessions** — but for the first time the only missing ingredient is the vol environment itself. Trade book: NKE EXITED today (Naked Puts, accel blew out to 1.37); CPS tab remains WATCH-only, awaiting a VIX move that hasn't come.

---

## 2026-06-02 (Tuesday)

**Scan summary:** Checked 11 / 5 actionable / 3 base_gate / 3 construction / 0 execution / 0 overlay / 0 confirmation
**Overlay:** VIX 15.77 / VIX3M 19.49 / VVIX 90.5 — NORMAL, Contango

| # | Ticker | Action | Days | Score | C/W | Credit | Width | Max Loss | RV Status | Notes |
|---|--------|--------|------|-------|------|--------|-------|----------|-----------|-------|
| 1 | QQQ | WATCH | 12d | 62 | 14.1% | $1.27 | $9 | $7.73 | Excellent | Thin premium |
| 2 | SPY | WATCH | 12d | 55 | 12.3% | $0.74 | $6 | $5.26 | Excellent | Thin premium |
| 3 | EEM | WATCH | 0d | 44 | 56.3% | $0.84 | $1.50 | $0.66 | Excellent | High credit/width |
| 4 | IWM | WATCH | 0d | 41 | 15.5% | $0.62 | $4 | $3.38 | Acceptable | Thin premium |
| 5 | TLT | WATCH | 0d | 35 | 14.0% | $0.07 | $0.50 | $0.43 | Excellent | Thin premium |

**Notable:** **5 actionable candidates — the pool roughly doubled** (only 3 base_gate fails left: XLF accel 1.23, GLD/XLE weak vrp_ratio), exactly as yesterday's NP base-gate analysis predicted. New Day-0 entrants EEM / IWM / TLT — IWM (accel 1.23→1.02) and TLT (1.25→0.84) cleared the RV-shock gate. **EEM c/w 56.3% — an all-time CPS record by ~3× (prior high was XLE 18.7% on 5/26)** — but it is the textbook **High-credit/width tail-risk warning, NOT a buy signal.** EEM sits in CAUTION regime (slope 1.08 backwardation), IVpct 92, score 44, Day-0. The fat c/w is fear premium — the market richly bidding EEM's near-strike puts because it's stressed. The framework correctly gates it (score < 65, Day-0 < 2d, explicit high-c/w warning). This is the cleanest live illustration yet of **why credit/width alone is never the gate** — the single highest c/w ever recorded appears on a CAUTION-regime, high-IVpct name, exactly where the spec says high c/w signals elevated tail risk. **The VIX divergence is the key reconciliation between the two tabs:** VIX actually FELL 16.05 → **15.77** (VVIX 91.6 → 90.5) while the Naked Puts tab showed avg-VRP expansion (+1.3 → +3.3) and stress 0 → 21%. So the catalyst (VIX 22+) did NOT arrive — the NP "fear-premium expansion" was **single-name IV ramps (NKE) + RV-collapses (NFLX) + term-slope pockets, not a systemic index-vol event.** Index c/w stayed pinned (SPY at the **12.3% structural floor again**, QQQ 14.1%). This tempers yesterday's "CPS catalyst forming" read — VIX went the wrong way; the CPS tab is the cleaner gauge of systemic vol and it says not yet. **Still zero SELL_CPS at 12 sessions:** QQQ/SPY at **12d** streak + RV Status upgraded to **Excellent** (accel cleared) + clean NORMAL/Contango overlay — everything aligned EXCEPT c/w (12–14% << 25% gate). EEM has the c/w but fails score/confirmation/regime. No single name clears all gates simultaneously — the book remains correctly loaded-but-unfired. **XLI base-passed but construction-rejected** despite being the NP near-SELL (64, IVpct 93) — flat slope (1.00) blocked a clean spread build. NP score ≠ CPS buildability, again (3 construction rejects = XLI, XLB, XLV). Trade book unchanged: NKE Full (Naked Puts, single-stock, not in CPS_UNIVERSE), CPS tab WATCH-only.

---

## 2026-06-01 (Monday)

**Scan summary:** Checked 11 / 2 actionable / 8 base_gate / 1 construction / 0 execution / 0 overlay / 0 confirmation
**Overlay:** VIX 16.05 / VIX3M 19.43 / VVIX 91.6 — NORMAL, Contango

| # | Ticker | Action | Days | Score | C/W | Credit | Width | Max Loss | RV Status | Notes |
|---|--------|--------|------|-------|------|--------|-------|----------|-----------|-------|
| 1 | QQQ | WATCH | 11d | 50 | 14.3% | $1.15 | $8 | $6.85 | Acceptable | Thin premium |
| 2 | SPY | WATCH | 11d | 39 | 12.3% | $0.74 | $6 | $5.26 | Acceptable | Thin premium |

**Notable:** **Days = 11d new cumulative high** for SPY/QQQ — eleven consecutive trading days of eligibility, still WATCH-only. **First VIX uptick of the entire cycle: 15.32 → 16.05 (+0.73)** after the relentless grind to cycle lows; VIX3M 18.66 → 19.43, **VVIX 86.1 → 91.6 (+5.5)** — the first directional turn in vol-of-vol. Still NORMAL/Contango (VIX < VIX3M) and far from the 22+ SELL_CPS catalyst, but it's the first inflection worth tracking, and it pairs with the Naked Puts tab's **financials/materials/bonds RV-accel pocket** (XLF 1.21, XLB 1.27, GS 1.26, TLT 1.25, IWM 1.23, WMT 1.33) building under an otherwise stress-zero surface. If this uptick extends 2-3 sessions, it's the early tell of the vol expansion the tab has waited 11 sessions for. **XLV base-gate-eligible but construction-rejected** (the 1 construction bucket) — its NEW Naked Puts CONDITIONAL (+33 to 51, IV pct 30 → 88) did NOT translate to a buildable CPS candidate: flat slope (1.00) + thin premium kept c/w below the 20% WATCH floor. Confirms the recurring pattern — NP score recoveries don't produce CPS-actionable spreads while broad premium is thin. **c/w still range-bound:** SPY pinned at the **12.3% structural floor** yet again (now its persistent minimum at VIX 16-17), QQQ 14.3% with width compressing $9 → $8 (credit $1.31 → $1.15). **IWM dropped out** (NP accel 1.23 breached the 1.20 base-gate). Eleven sessions of data now confirm the thesis cleanly: clean structure + persistent eligibility + clean overlay, but **c/w cannot reach 25% without a macro vol event.** The framework remains correctly loaded-but-unfired. Trade book unchanged: NKE Full (Naked Puts, single-stock, not in CPS_UNIVERSE), CPS tab WATCH-only.

---

## 2026-05-29 (Friday)

**Scan summary:** Checked 11 / 2 actionable / 8 base_gate / 1 construction / 0 execution / 0 overlay / 0 confirmation
**Overlay:** VIX 15.32 / VIX3M 18.66 / VVIX 86.1 — NORMAL, Contango

| # | Ticker | Action | Days | Score | C/W | Credit | Width | Max Loss | RV Status | Notes |
|---|--------|--------|------|-------|------|--------|-------|----------|-----------|-------|
| 1 | QQQ | WATCH | 10d | 51 | 14.6% | $1.31 | $9 | $7.69 | Acceptable | Thin premium |
| 2 | SPY | WATCH | 10d | 38 | 12.3% | $0.74 | $6 | $5.26 | Acceptable | Thin premium |

**Notable:** **Days = 10d double-digit milestone** for SPY/QQQ — ten consecutive trading days of eligibility. **XLI's Day-1 pop didn't hold** (yesterday at 0d c/w 10.0% boundary, today construction-rejected — predicted). **VIX continues lower (15.74 → 15.32 — third consecutive cycle low)** despite this week's major single-stock setups (NKE first SELL, JNJ +19 NEW CONDITIONAL, MSFT VRP cross-zero). **Critical signal-decoupling observation:** single-stock vol expansion does NOT propagate to broad-ETF c/w. SPY/QQQ c/w stayed range-bound 12-15% across all 10 sessions while the Naked Puts cohort fully reorganized around NKE/JNJ/MSFT. **The framework conclusion after 10 sessions of data:** for first SELL_CPS to fire, we need market-wide vol expansion (VIX 22+), not single-name surprises. Earnings cluster didn't trigger; today's single-stock breakthroughs didn't trigger. The catalyst remains elusive. **SPY decoupled from NP regime:** lost CONDITIONAL (-4 to 38) in NP but stayed in CPS WATCH (c/w 12.3% above 10% gate) — CPS Days counter persistence is independent of NP score band. Trade book: NKE Full + JNJ Quarter-Half (both Naked Puts, single stocks not in CPS_UNIVERSE). CPS tab continues WATCH-only.

---

## 2026-05-28 (Thursday)

**Scan summary:** Checked 11 / 3 actionable / 8 base_gate / 0 construction / 0 execution / 0 overlay / 0 confirmation
**Overlay:** VIX 15.74 / VIX3M 19.11 / VVIX 86.0 — NORMAL, Contango

| # | Ticker | Action | Days | Score | C/W | Credit | Width | Max Loss | RV Status | Notes |
|---|--------|--------|------|-------|------|--------|-------|----------|-----------|-------|
| 1 | QQQ | WATCH | 9d | 52 | 14.5% | $1.31 | $9 | $7.69 | Acceptable | Thin premium |
| 2 | XLI | WATCH | 0d | 48 | 10.0% | $0.20 | $2 | $1.80 | Excellent | Thin premium |
| 3 | SPY | WATCH | 9d | 42 | 12.8% | $0.77 | $6 | $5.23 | Acceptable | Thin premium |

**Notable:** **Days = 9d new cumulative high** for SPY/QQQ. **XLI NEW entry at Day-0** (predicted) — score 48 + RV Excellent (accel 0.84) but **c/w 10.0% exactly at the WATCH_CPS gate threshold**. Credit $0.20 on $2 width = $20 max gain/contract — below most retail decision thresholds. Tracking-only candidate (useful for confirming XLI's Naked Puts structural cleanup, not a standalone trade). **Zero construction rejections — first time ever** (8 base_gate fails consumed every non-actionable ticker; no chains built that failed at c/w/long-put-selection stage). Pattern worth watching — if 0-construction holds 2-3 sessions, base gates are doing more work. **VIX continues to new cycle low (16.29 → 15.74)** despite NKE's universe-record VRP 23.8. **The premium expansion catalyst showed up on NKE specifically, not on the indexes.** ETF c/w basically unchanged (SPY 12.7→12.8, QQQ 14.3→14.5). Eight sessions confirm: ETF c/w is range-bound 12-15% absent a macro vol event. NKE is the trade today (Naked Puts FULL notional, not CPS — NKE is single-stock, not in CPS_UNIVERSE).

---

## 2026-05-27 (Wednesday)

**Scan summary:** Checked 11 / 2 actionable / 7 base_gate / 2 construction / 0 execution / 0 overlay / 0 confirmation
**Overlay:** VIX 16.29 / VIX3M 19.45 / VVIX 87.5 — NORMAL, Contango

| # | Ticker | Action | Days | Score | C/W | Credit | Width | Max Loss | RV Status | Notes |
|---|--------|--------|------|-------|------|--------|-------|----------|-----------|-------|
| 1 | QQQ | WATCH | 8d | 54 | 14.3% | $1.29 | $9 | $7.71 | Acceptable | Thin premium |
| 2 | SPY | WATCH | 8d | 49 | 12.7% | $0.76 | $6 | $5.24 | Acceptable | Thin premium |

**Notable:** **Smallest scan since deploy** — just 2 candidates. **XLE's 18.7% c/w breakthrough from yesterday DIDN'T HOLD** — construction-rejected today despite base-gates passing. The single-day flash was a one-day artifact, not a sustainable signal. **New framework rule:** c/w "breakthroughs" need Day-2 confirmation before treating as real (same discipline as score confirmation streak). **Days = 8d milestone for SPY/QQQ** — new cumulative high. IWM streak BROKEN yesterday (accel 1.25 base-gate fail) — reduces core to two names. **VIX continues lower (17.01 → 16.29)** despite Naked Puts briefing's "stress spike" narrative (6 names CAUTION). The slope repricing on individual names is NOT translating to ETF premium expansion. **c/w fully range-bound:** SPY 12.7% (5th appearance at exactly this level — structural minimum for SPY at VIX 16-17 confirmed), QQQ 14.3%. Eight sessions of data confirm: **18% c/w hasn't been achieved on a sustained basis** despite varied regime conditions. The catalyst for first SELL_CPS-quality premium remains elusive — neither earnings cluster, NKE breakthrough, nor today's broad slope move produced expansion. Framework is correctly positioned: Day-8 streak past 2d gate + clean RV + persistent eligibility = ready to fire SELL_CPS the moment c/w expands.

---

## 2026-05-26 (Tuesday)

**Scan summary:** Checked 11 / 4 actionable / 5 base_gate / 2 construction / 0 execution / 0 overlay / 0 confirmation
**Overlay:** VIX 17.01 / VIX3M 19.89 / VVIX 89.6 — NORMAL, Contango

| # | Ticker | Action | Days | Score | C/W | Credit | Width | Max Loss | RV Status | Notes |
|---|--------|--------|------|-------|------|--------|-------|----------|-----------|-------|
| 1 | QQQ | WATCH | 7d | 52 | 14.4% | $1.29 | $9 | $7.71 | Good | Thin premium |
| 2 | SPY | WATCH | 7d | 47 | 12.7% | $0.76 | $6 | $5.24 | Acceptable | Thin premium |
| 3 | XLE | WATCH | 0d | 34 | 18.7% | $0.28 | $1.50 | $1.22 | Good | — |
| 4 | IWM | WATCH | 7d | 33 | 15.1% | $0.61 | $4 | $3.39 | Caution | Thin premium |

**Notable:** **XLE breakthrough — first candidate ever above the 18% thin-premium threshold (c/w 18.7%, no chip).** Best c/w in the entire CPS history. Driven by high IV (30.1) + IV pct 92 + slope 1.15 at DANGER boundary + VRP +4.3 widening. **STILL blocks SELL_CPS:** score 34 (gate ≥ 65), Day-0 confirmation (gate ≥ 2d), CAUTION regime one tick from AVOID override. The framework is correctly saying WATCH — discipline holds even on the cleanest math seen yet. **Days = 7d milestone for SPY/QQQ/IWM** — function correctly skipped Memorial Day holiday gap; seven consecutive trading days of eligibility for the core three. **QQQ RV Status Acceptable → Good** — confirms yesterday's cycle-pivot narrative; the three-week accel issue is fully resolved in CPS data too. **XLF dropped** despite tied-#1 NP score 52 yesterday — likely accel-boundary breach or tighter ATR construction. **EEM construction-rejected** (chain density issue persists despite base-gate eligibility from yesterday's forecast). 2 construction rejects = XLF + EEM. Trade calibration: XLE +5% EV math is genuinely positive at 18.7% c/w + 0.20-delta short, but sector concentration + DANGER-boundary slope + Day-0 confirmation = appropriate WAIT. Quarter-notional consideration ONLY from Day-2 IF slope holds.

---

## 2026-05-22 (Friday)

**Scan summary:** Checked 11 / 4 actionable / 6 base_gate / 1 construction / 0 execution / 0 overlay / 0 confirmation
**Overlay:** VIX 16.70 / VIX3M 20.03 / VVIX 91.2 — NORMAL, Contango

| # | Ticker | Action | Days | Score | C/W | Credit | Width | Max Loss | RV Status | Notes |
|---|--------|--------|------|-------|------|--------|-------|----------|-----------|-------|
| 1 | SPY | WATCH | 6d | 46 | 12.7% | $0.76 | $6 | $5.24 | Acceptable | Thin premium |
| 2 | QQQ | WATCH | 6d | 43 | 14.2% | $1.28 | $9 | $7.72 | Caution | Thin premium |
| 3 | XLF | WATCH | 0d | 43 | 11.0% | $0.06 | $0.50 | $0.44 | Caution | Thin premium |
| 4 | IWM | WATCH | 6d | 33 | 14.9% | $0.60 | $4 | $3.40 | Caution | Thin premium |

**Notable:** **Days = 6d** for SPY/QQQ/IWM — sixth consecutive day of eligibility (longest streak since deploy). XLF re-entered at Day-0 after yesterday's accel-fail break. XLI still construction-rejected (the 1 construction bucket). **NEW pattern: XLF $0.50-wide spread** — first time the system surfaced half-dollar-wide candidates ($48.50/$48.00). Credit $0.06 on $0.50 width = $6 max gain / $44 max loss with typical slippage 33-83% of max gain. **Worse than the $1-wide trap** for retail dollar-economics. Three of four candidates carrying RV Caution chip (SPY Acceptable, QQQ/IWM/XLF Caution) — accel-axis pressure on ETFs persists despite headline stress at series-low 6.7%. **c/w fully range-bound 12-15%** across six sessions despite VIX 17.44 → 16.70, despite WMT/NVDA/HD crushes, despite six days of streak. **The post-earnings-cluster premium-expansion thesis is decisively wrong** — the crushes normalized post-print RV but did not produce fatter ETF c/w. Premium-expansion catalyst now needs to come from elsewhere (Fed event, geopolitics, sustained vol regime shift) — not the earnings cluster. Jun 5-12 window (per yesterday's reverse-of-stuck-slope call) remains the realistic next SELL_CPS catalyst, contingent on NVDA/WMT/HD RV30 rolling off cleanly.

---

## 2026-05-21 (Thursday)

**Scan summary:** Checked 11 / 3 actionable / 6 base_gate / 2 construction / 0 execution / 0 overlay / 0 confirmation
**Overlay:** VIX 16.76 / VIX3M 20.00 / VVIX 91.9 — NORMAL, Contango

| # | Ticker | Action | Days | Score | C/W | Credit | Width | Max Loss | RV Status | Notes |
|---|--------|--------|------|-------|------|--------|-------|----------|-----------|-------|
| 1 | SPY | WATCH | 5d | 54 | 12.6% | $0.75 | $6 | $5.25 | Acceptable | Thin premium |
| 2 | QQQ | WATCH | 5d | 50 | 14.4% | $1.44 | $10 | $8.56 | Caution | Thin premium |
| 3 | IWM | WATCH | 5d | 35 | 14.1% | $0.56 | $4 | $3.44 | Caution | Thin premium |

**Notable:** **Days = 5d milestone** — third straight day of streak advancement (3d → 4d → 5d for SPY/QQQ/IWM). XLF correctly dropped out (accel 1.21 base-gate breach matched yesterday's forecast). XLI breakthrough (Naked Puts score 59 #1) did NOT materialize as a CPS candidate — construction-rejected (c/w < 10% gate; same "$1-wide trap" pattern as XLF/XLB). VIX dropped 17.44 → 16.76 despite the three "stuck-slope" earnings prints — post-NVDA reaction was a fade, not a spike. **ATR contracting on SPY ($10 → $6, -40%) and IWM ($6 → $4, -33%)** — width adjustment confirms realized vol is calming faster than the briefing's stress narrative suggested. c/w continues narrowing across the board (SPY −0.2, QQQ −0.3). Jun 10-15 (possibly Jun 17-24 per stuck-slope earnings pattern) remains the realistic next SELL_CPS catalyst window.

---

## 2026-05-20 (Wednesday)

**Scan summary:** Checked 11 / 4 actionable / 6 base_gate / 1 construction / 0 execution / 0 overlay / 0 confirmation
**Overlay:** VIX 17.44 / VIX3M 20.76 / VVIX 96.4 — NORMAL, Contango

| # | Ticker | Action | Days | Score | C/W | Credit | Width | Max Loss | RV Status | Notes |
|---|--------|--------|------|-------|------|--------|-------|----------|-----------|-------|
| 1 | SPY | WATCH | 4d | 49 | 12.8% | $1.28 | $10 | $8.72 | Acceptable | Thin premium |
| 2 | QQQ | WATCH | 4d | 43 | 14.7% | $1.47 | $10 | $8.53 | Caution | Thin premium |
| 3 | IWM | WATCH | 4d | 42 | 13.5% | $0.81 | $6 | $5.19 | Acceptable | Thin premium |
| 4 | XLF | WATCH | 0d | 41 | 13.0% | $0.07 | $1 | $0.43 | Good | Thin premium |

**Notable:** Days counter reaches **4d for the first time** on SPY/QQQ/IWM (Thu+Fri+Mon+Tue eligibility accumulated cleanly) — SELL_CPS confirmation gate fully exceeded; only c/w < 25% gates remain. XLF re-entered at Day-0 after two construction rejections — sector ETF still hitting the "$1-wide trap" ($0.07 credit / $43 max loss). **ATR-aware width expanded post-NVDA print:** SPY width $6 → **$10**, IWM width $4 → **$6**, QQQ width $9 → $10. Credit scaled proportionally so c/w held in the 12-15% range — same ratio, larger dollar exposure. IWM RV improved Caution → Acceptable (accel 1.13 → 1.00 boundary); SPY degraded Good → Acceptable (accel 0.99 → 1.00). Construction rejection = XLI (NO_DATA chain anomaly today). **VIX ticked DOWN 18.06 → 17.44 despite NVDA print** — the expected post-earnings ETF-premium expansion did not materialize. Jun 10-15 RV30 unwind window remains the realistic next SELL_CPS catalyst.

---

## 2026-05-19 (Tuesday)

**Scan summary:** Checked 11 / 3 actionable / 7 base_gate / 1 construction / 0 execution / 0 overlay / 0 confirmation
**Overlay:** VIX 18.06 / VIX3M 21.12 / VVIX 94.6 — NORMAL, Contango

| # | Ticker | Action | Days | Score | C/W | Credit | Width | Max Loss | RV Status | Notes |
|---|--------|--------|------|-------|------|--------|-------|----------|-----------|-------|
| 1 | SPY | WATCH | 3d | 60 | 12.8% | $0.77 | $6 | $5.23 | Good | Thin premium |
| 2 | QQQ | WATCH | 3d | 46 | 13.4% | $1.21 | $9 | $7.79 | Caution | Thin premium |
| 3 | IWM | WATCH | 3d | 39 | 15.6% | $0.63 | $4 | $3.38 | Caution | Thin premium |

**Notable:** **First Day-3 confirmation streak since deploy** — 2-day SELL_CPS gate procedurally exceeded for SPY/QQQ/IWM. c/w narrowed on all three despite VIX +0.24 (17.82 → 18.06): SPY 13.4 → 12.8, QQQ 14.5 → 13.4, IWM 16.2 → 15.6. Pre-NVDA-print IV expansion NOT translating to fatter ETF premium — the thin-premium regime is unusually sticky. SPY RV Status improved Acceptable → Good (accel 1.03 → 0.99); QQQ and IWM still Caution. XLF construction-rejected again (sector ETF at low VIX can't clear 10% c/w gate). Same 3 names persisting day-over-day.

---

## 2026-05-18 (Monday)

**Scan summary:** Checked 11 / 3 actionable / 7 base_gate / 1 construction / 0 execution / 0 overlay / 0 confirmation
**Overlay:** VIX 17.82 / VIX3M 20.92 / VVIX 91.2 — NORMAL, Contango

| # | Ticker | Action | Days | Score | C/W | Credit | Width | Max Loss | RV Status | Notes |
|---|--------|--------|------|-------|------|--------|-------|----------|-----------|-------|
| 1 | SPY | WATCH | 2d | 55 | 13.4% | $0.81 | $6 | $5.19 | Acceptable | Thin premium |
| 2 | QQQ | WATCH | 2d | 53 | 14.5% | $1.16 | $8 | $6.84 | Caution | Thin premium |
| 3 | IWM | WATCH | 2d | 35 | 16.2% | $0.65 | $4 | $3.35 | Caution | Thin premium |

**Notable:** First scan with Days counter = 2d — the 2-day confirmation gate is now mathematically reachable for SELL_CPS. None qualify (all c/w < 25%) so still WATCH-only. Universe shrunk 6 → 3 as 7 tickers failed base gates (GLD/XLV/XLI/XLE vrp_ratio < 1.15, TLT/XLB/EEM accel > 1.20). XLF built a spread but c/w < 10% (construction-rejected) — the $1-wide trap correctly self-filters at low VIX. RV Status degraded universally: SPY Excellent → Acceptable, QQQ Acceptable → Caution, IWM Good → Caution.

---

## 2026-05-14 (Thursday)

**Scan summary:** Checked 11 / 6 actionable / 3 base_gate / 2 construction / 0 execution / 0 overlay / 0 confirmation
**Overlay:** VIX 17.26 / VIX3M 20.85 / VVIX 94.3 — NORMAL, Contango

| # | Ticker | Action | Days | Score | C/W | Credit | Width | Max Loss | RV Status | Notes |
|---|--------|--------|------|-------|------|--------|-------|----------|-----------|-------|
| 1 | SPY | WATCH | 0d | 59 | 13.0% | $0.78 | $6 | $5.22 | Excellent | Thin premium |
| 2 | XLF | WATCH | 0d | 59 | 12.0% | $0.12 | $1 | $0.88 | Excellent | Thin premium |
| 3 | QQQ | WATCH | 0d | 57 | 16.1% | $1.28 | $8 | $6.72 | Acceptable | Thin premium |
| 4 | IWM | WATCH | 0d | 44 | 15.0% | $0.60 | $4 | $3.40 | Good | Thin premium |
| 5 | GLD | WATCH | 0d | 39 | 14.2% | $1.42 | $10 | $8.58 | Acceptable | Thin premium |
| 6 | XLB | WATCH | 0d | 8 | 11.5% | $0.11 | $1 | $0.89 | Caution | Thin premium |

**Notable:** First scan after CPS-fix deploy (expiration-selector + strikeLimit=120 + execution-filter removal + WATCH_CPS score-gate removal). All six candidates Day-0 of confirmation streak — no SELL_CPS possible until Monday May 18 at earliest if any of SPY/QQQ/IWM/XLF clear 25% c/w (unlikely at current VIX).

---
