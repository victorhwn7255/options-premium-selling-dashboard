# Daily Briefings — Analysis Summaries

Trading analysis and recommendations based on each day's scan data.

---

## Update Protocol

**Trigger:** After updating `metrics-logs.md` with the day's raw data.

**Steps:**
1. Analyse the metrics — compare against previous day(s) for trends
2. Present analysis and trade recommendations to the user in chat
3. After user discussion, write the briefing entry here
4. Insert new entry **at the top** of the log (immediately below the `---` after this protocol section)

**Entry format:**
```
## YYYY-MM-DD (Day of week)

**Regime:** [NBA regime] ([phase/qualifier]) | **Tradeable:** [X]S / [Y]C | **Avg VRP:** [value]

[1-2 paragraph narrative analysis covering: regime shifts, top signals, key movements from
previous day, earnings impacts, sector themes, data quality notes if any]

**Position: [specific recommendations with RV Accel Status / environment cleanliness; contract count is the trader's call, recorded in the trade journal]**
```

**Analysis should cover:**
- Regime status and any shifts from previous day
- Top SELL and CONDITIONAL signals with scores
- Day-over-day changes for key tickers (score, VRP, slope, regime changes)
- Earnings gate impacts (newly gated/ungated tickers)
- Aggregate stats (avg VRP, % negative VRP, RV accel trends)
- Any data quality issues observed
- Actionable position recommendations referencing **RV Accel Status** (Excellent / Good / Acceptable / Caution / Avoid · Wait). Position size is a trader-controlled decision recorded in the trade journal — not prescribed by the dashboard or this briefing.

**Tone:** Concise, data-driven, opinionated. Reference specific numbers. Flag uncertainty.

---

> **IMPORTANT:** Entries are in **descending order** (newest first). New entries go immediately below this line.

---

## 2026-05-13 (Wednesday)

**Regime:** THE PLAYOFFS (Index Strength Reasserts) | **Tradeable:** 0S / 3C | **Avg VRP:** −0.4

**Stress halved 16.7% → 6.7% in one session — May 12's slope drift fully reversed.** JNJ cleared CAUTION (1.07 → 1.00), JPM cleared (1.06 → 1.04), XLE cleared (1.10 → 1.01), EEM downgraded DANGER → CAUTION (1.15 → 1.09). Only XOM (1.11) and EEM (1.09) remain stressed. The non-earnings-driven slope deterioration that worried me yesterday was a one-day repricing, not a building trend — the structural-stress thesis was wrong on directional read, right on noting the broadening. **XLF series-high at 64 (+14 in one session) — 1 point from SELL.** Every component strengthened simultaneously: VRP 3.8 → 5.0, IV pct 49 → 55, IV +0.5 vol pts, slope 0.83 stable, accel 0.59 → 0.74 (still RV Accel Status: **Excellent**). XLF is now the strongest non-earnings setup since JNJ on May 11, and the cleanest financial-sector setup in the entire series. **SPY +5 to 60 — three sessions of confirmed expansion.** Slope **0.67** is series-deepest contango of the cycle. VRP 2.8 → 4.0, vrp_ratio 14.8/10.9 = **1.36** (clean past 1.15 gate). Tuesday's SPY entry call is locked in. **QQQ −2 to 56 (signal intact, first yellow light).** VRP widened 5.3 → 5.6 BUT accel crossed 1.0 (0.93 → **1.04** = RV Accel Status: **Acceptable**). Three-session expansion is still working, but the structural concern axis just lit up. Manage to 50% profit, no add. **JNJ −35 to 26 — confirmation that Tuesday's CLOSE call was right for the structural reason, not just the slope reason.** Slope cleared back to 1.00 (regime NORMAL again), but underneath: RV30 16.0 → 18.1 (+2.1 vol pts of realized arriving), IV crushed 23.6 → 21.9, VRP 7.6 → 3.7. The slope rebuilt back to NORMAL, but realized vol ate the premium structurally. The May 12 SELL → AVOID downgrade was catching incoming realized vol via the slope-stress proxy, not just sentiment noise. **Single-stock cohort uniformly deteriorating:** MSFT 44 → 42 stable but no thaw, AMZN 38 → 35 (IV pct 33 → 28, drifting wrong), AAPL 34 stable (IV pct 31 → 26, also wrong direction), META 28 → 22 (VRP −8.9 widening negative, RV30 climbing 40.0 now), TSLA 28 → 24, GS 31 → 34 marginal. **Index ETFs are the only game.** **Earnings cluster pre-print backwardation building hard:** WMT slope 1.31 → **1.35** (8d to print, deepest so far), HD slope 1.32 → 1.33 stable (6d, IV pct **98** universe-top), NVDA slope **0.97 → 1.11** (newly backwardated 7d pre-print, VRP **12.6** universe-widest, accel 1.23 → 1.30). NVDA's transition from contango to backwardation pre-print is the classic pre-event template firing. **MSFT VRP cross-zero watch advancing slowly:** −2.3 → −1.7 (closer), accel 0.86 → 0.88 stable. 1-2 sessions from positive on current trajectory. **First real CPS-aware production scan ran today** — the 11-ETF universe, threshold-loosened, thin-premium-warning code's first live test. Tab should show ~6-8 candidates (SPY/QQQ/IWM/XLF/GLD/XLI/XLB/TLT all clear the VRP gate; EEM/XLE/XLV fail). With current low VIX, expect most to carry the 🟡 thin-premium warning chip. **Day-over-day:** XLF 50 → 64 (+14); SPY 55 → 60 (+5); JNJ 61 → 26 (−35); SBUX 4 → 31 (+27, accel 1.39 → 0.53 collapse); HOOD 8 → 22 (+14); KO 25 → 32 (+7); TLT 24 → 32 (+8, slope deepened 0.95 → 0.76); META 28 → 22 (−6); XLI flat 29 but accel 1.07 → **1.15** (Caution); XOM 26 → 30 (slope 1.30 → 1.11 = exited DANGER).

**Position: XLF — TOP NEW ENTRY of the cycle. RV Accel Status: Excellent (0.74). 30-45 DTE put credit spread or wide strangle/iron condor. Score 64 + ETF (no earnings) + 3-session VRP confirmation + universe-cleanest financial setup = highest-conviction non-earnings signal since Apr 14. Contract count is your call (record in journal); cleanliness justifies normal-discipline sizing, not size-up. SPY — HOLD if entered Tue. Three-session confirmation locks the thesis. No add; already at full normal discipline. QQQ — HOLD, no add, manage to 50% profit. Accel crossed 1.0 = first structural caution; if accel ≥ 1.10 next scan, exit at 25%. JNJ — confirmed CLOSE (Tue's call was right). Don't re-enter; the IV/RV reset is structural and the slope-cleared signal is noisy. MSFT — WATCHLIST, 1-2 sessions from VRP-positive. NVDA — WATCHLIST gated; pre-print backwardation just turned on, this is the entry signal building for the ~May 23 post-print window. WMT/HD — gated, pre-print IV ramp dominates. CPS tab — first real production day: expect 6-8 candidates, most with thin-premium warning given low VIX; NO SELL_CPS today (Day-1 of 2-day confirmation streak; earliest SELL_CPS = Thursday morning SGT IF candidates persist). Forward watchpoints: (1) Wed AMC = WMT print (per scanner; may also be later in week per FMP drift — verify before close). (2) Thu May 14 AM SGT = second CPS scan; if SPY/QQQ/IWM/XLF all re-qualify, Thursday delivers the first possible SELL_CPS. (3) QQQ accel persistence — if next print stays ≥ 1.05, the second-axis caution becomes a structural exit signal. (4) JNJ post-collapse template — JNJ collapsed by RV30 spike not slope, which is the cleaner "post-spike structural reset" template (compare against KO/SBUX Day-2 crush, MCD broken-Day-1). Honest framing: XLF is the day's clean setup, but the universe is bifurcating sharply (ETFs strengthening, single stocks rotting). Don't reach down the score table looking for diversification — there isn't any to be had today.**

---

## 2026-05-12 (Tuesday)

**Regime:** THE PLAYOFFS (Stress Trickling Back via Slope) | **Tradeable:** 0S / 3C | **Avg VRP:** −0.5

**JNJ broke slope discipline exactly as flagged.** Score 68 → 61 (−7); slope 0.87 → **1.07** crossed the CAUTION threshold, regime flipped NORMAL → CAUTION, recommendation downgraded SELL → REDUCE SIZE (displayed as AVOID). VRP/IV pct actually strengthened (6.7 → 7.6, 82 → 87) — pure slope-axis collapse. This is the post-rally drift risk I called out on Fri ("one slope worse-print puts this in CAUTION territory"). **Tradeable count narrowed to 0S / 3C / 0W** as JNJ exited, XLI fully reverted (45 → 29 in one session, IV crushed −8 vol pts, VRP +7.3 → −0.1 — Mon's surprise was a one-day pop), and the three remaining CONDITIONALs (QQQ 58, SPY 55, XLF 50) re-ranked around index VRP expansion. **The macro story shifted in a good way.** SPY cleanly cleared the 1.15 VRP gate for the first time this cycle: vrp_ratio 15.8/12.9 = **1.22** (Mon was 1.12 WATCHLIST). Slope 0.72 series-deepest. RV Accel 0.74 (Excellent). All five components simultaneously clean — cleanest non-earnings setup since Apr 14. QQQ continued widening (IV 21.1 → 22.4, VRP 4.0 → 5.3, IV pct 64 → 73) — three sessions of confirmed expansion now. **Counter-pressure: slope drift broadening across the universe.** Stress 3.3% → 16.7% (2 DANGER + 3 CAUTION out of 30): JNJ CAUTION (1.07), JPM new CAUTION (1.06), XLE CAUTION (1.10), EEM DANGER (1.15 boundary), XOM DANGER (1.30 deepening). Non-earnings-driven slope deterioration — likely macro vol-structure repricing into next week's WMT/HD/NVDA cluster. **Pre-print backwardation building hard:** WMT slope 1.00 → **1.31** (9 DTE, prints Wed AMC), HD slope 1.11 → **1.32** (7 DTE), NVDA slope 0.80 → 0.97 + VRP 8.2 → **10.5** (universe-widest, 8 DTE). **MSFT VRP cross-zero watch advancing:** −2.8 → −2.3, accel 0.90 → 0.86 stable. 2-3 sessions from positive. **Production CPS deploy completed today** — Phase 1-5 merged via PR #17 and live on theta.thevixguy.com. Tonight's 6:30 PM ET cron is the first CPS-aware production scan. All three CPS-universe tickers (SPY/QQQ/IWM) clear the 1.15 VRP base gate today, so tomorrow's CPS tab should show 3 WATCH_CPS candidates (Day-1 of confirmation streak; earliest SELL_CPS = Thursday morning SGT). **Day-over-day:** XLI 45 → 29 (full IV crush, the asymmetry didn't pay); WMT 0 → 0 (slope spike confirms pre-print IV ramp); JPM 36 → 26 (slope drift into CAUTION); EEM 39 → 27 (new DANGER); HOOD 11 → 8 (continued bleed).

**Position: JNJ — CLOSE at open Wed if entered Mon at 68 SELL. Framework correctly downgrading; don't fight the regime. Take whatever theta you accrued — don't wait for slope to worsen to DANGER. SPY — NEW ENTRY, cleanest non-earnings setup since Apr 14. RV Accel Status: Excellent (0.74). Slope 0.72 series-deepest. vrp_ratio just crossed 1.15 (this is the bullish signal — first SPY CONDITIONAL of the cycle). Iron condor or short strangle 30-45 DTE; ETF = no earnings risk. Contract count is your call (record in journal). QQQ — HOLD if entered Thu; optional add to half size if margin available. Three sessions of confirmed widening. XLF — HOLD (slipped 55 → 50 but still cleanly CONDITIONAL; no add). XLI — CLOSE if entered Mon (full IV crush). MSFT — WATCHLIST; 2-3 sessions from VRP-positive trigger. NVDA — WATCHLIST gated; post-print ~May 23 is the window. WMT — gated, prints Wed AMC. Forward watchpoints: (1) Wed May 13 AMC = WMT print; first real-world test of post-print template since May 7-8 batch. (2) Thu May 14 AM SGT = second CPS-eligible scan; first possible SELL_CPS if SPY/QQQ/IWM stay eligible both days. (3) JNJ slope persistence — if Wed close > 1.15 → DANGER; if back below 1.05 → CAUTION clears. (4) XOM/EEM energy stress — 5+ sessions now; watch for sector rotation. Honest framing: SPY entry is the day's clean setup, but don't size up beyond normal discipline — universe-wide slope drift means two-day confirmation discipline applies even on Naked Puts when structure is this twitchy.**

---

## 2026-05-11 (Monday)

**Regime:** THE PLAYOFFS (Tradeable Pool Peak of Cycle) | **Tradeable:** 1S / 3C / 1W | **Avg VRP:** −1.8

**Cleanest scan of the cycle — first SELL signal since WMT was gated.** JNJ pushed through to **SELL at 68 (+10 from Fri's 58)** with all five inputs simultaneously clean: VRP 5.3 → 6.7, IV pct 76 → 82, slope deepened 0.89 → 0.87, accel 0.88 stable, skew still 0.0 (the only weak component — but additive scorer correctly nets the other four past 65). Fri's "one skew uptick from SELL" forecast was right on direction, wrong on axis — VRP and IV pct moves alone did the work. **Tradeable count rebuilt 0S/3C → 1S/3C/1W** with three CONDITIONALs (XLF 55, QQQ 52, XLI 45) and one new WATCHLIST (SPY 45). **XLF series-best** at 55 (+10): RV30 compressed 15.7 → 13.5, VRP 1.3 → 4.3, slope 0.82 stable. **QQQ Thu IV-expansion held and widened** (+7 to 52): the spike-buy-Mon-revert risk I flagged Fri did NOT materialize — IV 19.4 → 21.1 (+1.7 more), VRP 0.5 → 4.0, slope at series-deepest 0.77. The macro pivot was real and sustained. **XLI surprise CONDITIONAL** (+14, biggest single-day jump): IV +8.5 vol pts (21.9 → 30.4), VRP −1.6 → +7.3, IV pct **97** (universe-top). Caveat: slope at exactly 1.00 (one print from CAUTION trigger), accel 1.06 (RV Accel Status: Acceptable, edging Caution) — riskiest of the four actionable signals. **SPY new WATCHLIST** (Phase-1 VRP-gate at work): vrp_ratio = 14.6/13.0 = 1.12 < 1.15, so the otherwise-CONDITIONAL score is correctly demoted. Slope 0.63 = series-deepest contango, structure clean, premium too thin. **Macro story shifted decisively:** SPY VRP turned positive for the first time in weeks (−0.5 → +1.6), QQQ VRP +0.5 → +4.0. Index VRP positive + stress 3.3% (XOM alone in DANGER, slope 1.24) + 4 tradeable signals = first time this cycle the framework has produced this combination. The May 1 forecast ("fattest opportunity Jun 5-15") arrived early. **Stress structure:** XLE exited CAUTION cleanly (slope 1.11 → 0.90); XOM re-entered DANGER alone (1.04 → 1.24, non-earnings-driven, possible energy-sector flicker). Negative VRP count narrowed 17/30 → 15/30. **MCD Day-2 crush template confirmed N=3:** May 7 slope 1.59 DANGER → today 0.87 NO EDGE NORMAL (score 16 → 37). SBUX / MCD now both confirmed Day-2-crush sub-pattern names. **Earnings-gated trio:** WMT 13d → 10d (slope loosened 0.82 → 1.00 — standard pre-print IV expansion ramp; prints Wed May 13 AMC), HD 11d → 8d (prints ~May 19), NVDA 12d → 9d (prints May 21; pre-gate VRP 8.2 + slope 0.80 + IV pct 59 is the strongest pre-print underlying in cycle). **MSFT VRP cross-zero watch on track:** −3.5 → −2.8 (closer), accel 0.90 stable, IV pct 62 — still needs ~3 RV30 vol pts to roll off, ETA ~May 22-28 unchanged. **Day-over-day:** HOOD 20 → 11 (RV held while IV crushed harder), TSLA 27 → 35 (slope deepened 0.93 → 0.84), TLT 28 → 26 stable, XLB 5 → 8 still worst.

**Position: JNJ — NEW SELL entry. RV Accel Status: Good (0.88). 30-45 DTE put credit spread or naked short put. 65d to next earnings = clean event runway, deepest contango of the cycle, IV pct 82. Strongest non-earnings setup since Apr 14. Contract count is your call — record in trade journal. XLF — ADD if entered Mon May 4 (signal accelerated past noise, RV Accel Status: Excellent at 0.49); HOLD as-is if not entered. QQQ — HOLD if entered Thu (IV expansion validated). Iron condor remains the right structure. XLI — OPTIONAL Quarter-notional entry only; the riskiest of the four signals (slope at 1.00 boundary, RV Accel Status: Acceptable edging Caution at 1.06). Iron condor 21-30 DTE if entered; hard exit if slope drifts above 1.05 next session. Skip if you don't want sector concentration alongside XLF. SPY — WATCHLIST only, no entry (vrp_ratio 1.12 < 1.15 dead zone). Re-evaluate when ratio crosses 1.20. WMT / HD / NVDA — gated (10d/8d/9d); NVDA pre-gate signal is strong, watchlist for post-print ~May 22-28 once 14d window clears. Forward: Wed May 13 AMC = WMT prints (slope 0.82 → 1.00 today is pre-print IV ramp); MSFT VRP cross-zero watch ~May 22-28; XOM slope persistence diagnostic next 1-2 sessions (DANGER alone non-earnings-driven). Honest framing: today is the day to act on JNJ. All five components simultaneously clean for the first time in this cycle. The macro story changed — index VRP positive + stress series-low + 4 tradeable signals — but don't size up beyond your normal discipline just because the dashboard finally lit up. Record contract counts in your journal.**

---

## 2026-05-08 (Friday)

**Regime:** THE PLAYOFFS (Stress Series-Low) | **Tradeable:** 0S / 3C | **Avg VRP:** -3.3

**Stress hit a series-low 3.3% (1/30 — XLE alone in CAUTION, ZERO DANGER).** XOM and MCD both exited DANGER in one session: XOM slope 1.18 → 1.04, MCD 1.59 → **1.00** (textbook SBUX-template Day-2 crush, second confirmation of that pattern). The structural cleanup that started Mon is now complete. **JNJ pushed toward SELL** (45 → **58, +13** points; +42 over two sessions). All five inputs now structurally clean: slope back to 0.89 (CAUTION-boundary risk gone), accel **0.90** (below 1.0, structural concern resolved), IV pct 76, VRP 5.3. **One skew uptick from SELL** — skew dropped to 0.3 today (the only weak component); if it recovers to 4-5 next session, score crosses 65. Cleanest CONDITIONAL setup of the week. **QQQ IV expansion partially reverted** (Thu 21.3 → today 19.4, −1.9 vol pts; VRP +1.1 → +0.5). The spike-buy-Mon-revert risk I flagged Thu materialized — not catastrophic (still CONDITIONAL at 45, VRP still positive), but Thu's entry got partial give-back. SPY tells the same partial-revert story (IV 15.5 → 14.1, VRP −0.4 → −0.5). The macro pivot was a partial pivot, not sustained. **MSFT replaces AMZN/AAPL as leading early-re-entry candidate:** IV pct 63 (already above >50 trigger), VRP −3.5 closing on zero, accel 0.87 (improving). The block is just RV30 needing to drop ~4 vol points to push VRP positive — likely arrives ~May 22-28 if trajectory holds. **AMZN drifted further from trigger** (IV pct 32 → 26), AAPL drifting wrong direction (IV pct 22 → 18, VRP −1.8 → −2.5). Both deferred to Jun 10-15 mechanical RV30 unwind window. **MCD anomaly fully resolved on Day-2** (slope 1.59 → 1.00, IV −3.0 vol pts, IV pct 88 → 60). The SBUX-template now has N=2 confirmations. **Lesson logged:** when a Day-1 reads "broken" (slope deepens post-print), give Day-2 one session before assuming structural failure — the broken-Day-1 is in the noisy sub-pattern, not necessarily a thesis kill. **UBER Day-2** continued normalizing (slope 0.96, VRP −0.1 closing on zero). PLTR Day-4 deepening contango (0.95 → 0.89). **Day-over-day:** WMT held at 0 SKIP (13d to print, slope still 0.82 deepening); MSFT 39 → 41 accel improvement; HOOD score climbing 15 → 20 as IV continues to crush (VRP −18.3 still deep but slope back to 0.90).

**Position: JNJ — STRONGEST signal of the week. If entered Thu: ADD to Half-or-Full notional given the structural cleanup (slope 0.89 + accel 0.90 + IV pct 76). If not entered: initiate Half-to-Full notional CONDITIONAL, 30-45 DTE put credit spread or wide strangle/jade lizard. Watch for skew recovery — one skew uptick puts this in SELL territory. QQQ — hold to break-even, don't add. Spike-buy from Thu got partial give-back; if Mon shows further IV revert below 19.0 with VRP turning negative, exit. XLF — hold to 50% profit/break-even (signal margin gone but structure intact). MSFT — NEW top mega-cap watchlist candidate (replaces AMZN/AAPL). Trigger: VRP crosses positive (~May 22-28 if RV30 trajectory holds); when it triggers, expect 55-65 score with deep contango + high IV pct = clean Half-to-Full CONDITIONAL or even SELL. AMZN/AAPL — off the early-re-entry watchlist for now (drifting wrong direction); wait for Jun 10-15 window. WMT — plan May 19-22 re-entry window, Jun 19 expiry target if score 65+ post-print. TLT — should be closed (Tue's entry decisively done, score 28 NO EDGE). MCD — should be closed (lesson: exiting into broken Day-1 likely cost the option-mark recovery from today's slope crush; future SBUX-anomaly broken Day-1s, give Day-2 one session). NVDA — gated (12d), off the table; post-print cycle is the next time NVDA matters. Forward: Mon May 11 = QQQ-revert diagnostic + JNJ-skew-recovery watch; May 14 WMT prints; May 19-22 first re-entry window; May 22-28 MSFT VRP-positive trigger watch; Jun 10-15 mega-cap RV30 unwind peak.**

---

## 2026-05-07 (Thursday)

**Regime:** THE PLAYOFFS (Tradeable Pool Refilling) | **Tradeable:** 0S / 3C | **Avg VRP:** -3.6

**Tradeable count rebuilt to 3 with new composition.** WMT formally gated as expected (63 → 0 SKIP, 14d threshold met) — verified-earnings discipline now reflected in framework's own output. Three new/recovered CONDITIONALs replaced it: **QQQ NEW (50)**, XLF recovered (43 → 47), JNJ rebounded (16 → **45**, +29 in one session). Stress held at 10% (3 DANGER: XOM, MCD, XLE; 0 CAUTION). **Owe two corrections from yesterday:** (1) JNJ "off the table, IV reset to baseline" framing was premature pattern-matching — five inputs improved simultaneously today: IV 18.9 → 20.5, IV pct 53 → 69, VRP 2.0 → 4.7, accel 1.11 → **0.96** (below 1.0, structural concern resolved), skew 0.0 → 4.2. JNJ at 45 today is structurally cleaner than JNJ at 53 was on May 4 (when accel was 1.24 borderline). (2) UBER Day-1 cleanly crushed (slope 1.77 → 1.01, IV −6.5 vol pts) — this confirms a two-sub-pattern model, not a single Day-2-crush universal: **Day-1-crush** names (GOOG, CAT, META, HOOD-D3, UBER) likely had bigger one-day realized moves; **Day-2-crush** names (MSFT, AMZN, AAPL, PLTR-D2, KO-D2, SBUX-D2) had more measured moves and need a session for the IV crush to arrive. **MCD is the new SBUX-anomaly:** Day-1 broken, slope 1.58 → **1.59** deepened post-print, DANGER regime active. SBUX eventually crushed Day-2; MCD's diagnostic is Mon. **The big macro story: index IV expanded sharply in one session.** SPY IV 13.9 → 15.5 (+1.6), QQQ IV 19.1 → 21.3 (+2.2). **QQQ VRP crossed positive (−0.9 → +1.1)** for the first time in weeks, SPY VRP −1.8 → −0.4 (highest since Apr 13). RV30 stable on both — this is exactly the IV-widening-while-RV-holds mechanic the framework needs to produce signals. **Important caveat: this is one session.** Diagnostic is whether IV expansion holds Mon. Could be sustained macro pivot (Fed/geopolitical/sector rotation → tradeable signals proliferate next week) OR single-day IV bid that reverts (today's QQQ entry would be buying the spike). **Day-over-day:** WMT 63 → 0 (formal gate, slope still deepening 0.89 → 0.85); MSFT 30 → 39 (accel 1.09 → 0.90, below 1.0); UBER post-print Day-1 crushed; PLTR Day-3 deepening contango (1.04 → 0.95, VRP −9.3); TLT continued deterioration 38 → **26** (Tue's entry now decisively underwater on signal terms).

**Position: WMT — formal gate fired (verified-earnings discipline now reflected in dashboard). Re-entry plan: May 19-22 if score 65+ post-print, Jun 19 expiry. JNJ — REAL entry candidate (best of the three). Quarter-to-Half notional CONDITIONAL, 30-45 DTE put credit spread or iron condor. Accel 0.96 below 1.0 means the structural concern is resolved; slope 1.02 close to CAUTION boundary is the residual risk. QQQ — IV expansion play, Quarter notional iron condor 30-45 DTE. Caveat: signal built on +2.2 vol pts of single-session IV expansion; if IV reverts Mon, this disappears. Don't size up. XLF — hold (no add); recovered to 47 CONDITIONAL but signal can degrade fast as Wed showed. Manage to 50% profit or break-even. TLT — close today; score 26 NO EDGE, two-session deterioration from 46 entry, thesis finished. MCD — close today if still held (DANGER regime, slope 1.59 deepened post-print, position now in worst configuration: post-binary + DANGER override + slope persisting). AMZN/AAPL — not yet re-entry (IV pct 32/22 too low for the "VRP positive + IV pct >50" trigger); wait. NVDA — gated (13d), off the table. Forward: today (Fri May 8) close is the QQQ-IV-expansion diagnostic; Mon May 11 = MCD Day-2 verdict + WMT 3d to print; May 14 WMT prints; May 19-22 first re-entry window; Jun 10-15 mega-cap RV30 unwind peak.**

---

## 2026-05-06 (Wednesday)

**Regime:** THE PLAYOFFS (Signals Degrading) | **Tradeable:** 0S / 1C | **Avg VRP:** -3.7

**Tradeable count collapsed 3 → 1** as XLF lost CONDITIONAL (48 → 43, VRP/IV pct compression) and TLT lost CONDITIONAL hard (46 → 38, accel jumped 0.78 → 0.93). Only WMT held — and verified-gated at 7d to May 14. Stress dropped further to 6.9% (2 DANGER, 0 CAUTION) but the signal pool emptied alongside it. **Mon's signal high (4 tradeable) was the peak, not an uptrend.** The XLF entry from Mon and the TLT entry from Tue are now both sub-threshold. **Owe a correction on TLT:** yesterday's "reasonable second tradeable" framing oversold a borderline score-46 signal with no margin; honest call should have been "borderline, only if you specifically want bond diversification, expect fast degradation." Today's −8 score drop in one session is the receipt. Both should manage to exit at break-even or first 25% profit, not be defended. **Day-over-day:** WMT 60 → 63 slope deepening 0.93 → 0.89 (structurally great but verified-gated); JNJ collapsed 39 → **16 (-23!)** as IV crushed 22.2 → 18.9 and IV pct dropped 81 → 53 (post-earnings-cycle baseline reset, not a tradeable signal); NVDA gated at 14d (slope 0.81 still deep contango but accel 1.28 worsening); IWM/EEM both +8 score on slope improvement but still NO EDGE. **UBER Day-1 stuck-slope** (1.71 pre → 1.77 post-print) — identical to MSFT/AMZN template; tomorrow's Day-2 read tells us whether crush arrives or UBER is SBUX-anomaly redux. **PLTR Day-2 IV crush arrived** (60.4 → 50.7, −9.7 vol pts) — confirms the Day-1-stuck/Day-2-crush template generalizes beyond mega-caps. **Mega-cap cohort state evolving:** AMZN VRP −0.8 + slope 0.81 + IV pct 31, AAPL VRP −1.3 + slope 0.91 — both nearing zero VRP. If either crosses VRP positive + IV pct >50, that's a potential earlier re-entry candidate than Jun 10-15. **Macro:** SPY slope 0.63 (series-deepest contango) but VRP −1.0 → −1.8 because IV is compressing in tandem with RV (SPY IV 14.7 → 13.9, RV30 stable). The "fear draining" mechanic is still working but no longer widening edge — both sides draining together = flat-VRP regime, not a wide-VRP one. The framework needs *expanding* VRP to produce signals; calm-market macro doesn't deliver that on indexes. **Energy DANGER persists:** XOM (slope 1.20) and XLE (1.21, accel jumped 0.66 → 1.07 — RV picking up). 4-5 sessions of energy stress now, non-earnings driven; treat as a sector to avoid this week regardless of score.

**Position: WMT — close if still held (verified May 14 = 7d, well inside formal gate; pre-print IV expansion will dominate). XLF — hold to 50% profit or break-even, don't add (slope 0.86 + accel 0.55 still clean, theta still accruing, but score below CONDITIONAL means thesis flipped off). TLT — hold to break-even or small profit, acknowledge entry was a stretch and degraded fast (don't churn but don't defend either). JNJ — off the table (score 16, IV reset to baseline). MCD existing — past the rational close window; reports today AMC, sit through the binary then close at open Fri regardless of direction (don't try to close into closing-bell IV peak — liquidity will be terrible). NVDA — gated, watchlist only; post-NVDA-print (~May 21+) is the next time NVDA matters. **No new entries today.** Universe below CONDITIONAL except WMT. The waiting period through May 13 is now mostly mechanical. Watchpoints: UBER Day-2 tomorrow (does crush arrive?), AMZN/AAPL VRP recovery (could move Jun re-entry forward to ~May 22-28 if either crosses VRP positive + IV pct >50). The structural picture is improving (stress 6.9%, deepest SPY contango of series) but macro mechanic is "both sides draining" not "IV draining while RV holds" — wait for that mechanic to reassert before expecting fresh signals.**

---

## 2026-05-05 (Tuesday)

**Regime:** THE PLAYOFFS (Signals Compressing) | **Tradeable:** 0S / 3C | **Avg VRP:** -2.6

**Tradeable count narrowed 4 → 3** despite stress holding at 10%. WMT lost SELL (65 → 60) on slope drift 0.82 → 0.93 (VRP actually widened 8.1 → 8.8 and accel improved — score loss is purely the noisy-axis); JNJ collapsed 53 → 39 on slope worsening 0.89 → 1.04 (paradoxically accel improved 1.24 → 1.10); IWM lost CONDITIONAL 45 → 36 on slope 0.82 → 0.96. **TLT joined CONDITIONAL** 42 → 46 (slope 0.89, VRP 2.9, IV pct 23 → 32, very stable accel 0.78) — modest second tradeable that diversifies XLF's equity-beta exposure. **XLF held cleanly at 48** — every input stable, yesterday's recommended entry remains intact. **DANGER count ticked 1 → 2: XOM joined XLE** (slope 1.07 → **1.27**, deepening backwardation 4 days post-print which is unusual). XLE simultaneously deepened 1.06 → 1.23, EEM re-entered CAUTION 0.97 → 1.13. **Energy sector is the new stress point** — non-earnings, non-residual; possible oil tape move, geopolitics, or sector rotation. Don't trade energy in any direction this week. **Mega-cap slope drift-back:** AMZN/MSFT/GOOG/META all mean-reverted from sub-0.85 Day-2 deep-contango readings back to 0.84-0.93 by Day 4-5. Normal post-print noise unwinding — slopes still good for re-entry purposes, just not as dramatic as Mon's snapshot. **Recalibrate Jun 10-15 expectations:** slopes will be 0.85-0.95 not sub-0.85 when RV30 unwinds. **PLTR Day-1 different mechanic:** slope cleanly crushed 1.45 → 1.05 (unlike mega-cap delayed pattern), but VRP barely moved 1.4 → 1.3 because pre-print VRP was already thin — the "RV30 unwind recovery" thesis only applies to fat-pre-print-VRP names like the mega-caps. **MCD pre-print IV peaked TODAY, not Mon as I claimed yesterday:** slope spiked 1.32 → 1.56 in one session, IV 23.3 → 24.4 — final-day vol-of-vol uptick. Tomorrow Wed AMC = the binary. **Macro slightly worse:** SPY VRP -0.5 → -1.0, QQQ -0.4 → -1.1, both slopes loosened (SPY 0.65 → 0.70, QQQ 0.70 → 0.80). The fear-draining thesis still works but pace slowed. NVDA 15d to earnings, gates next scan; HD now gated at 14d.

**Position: WMT — close if still held (verified May 14 = 8d today, formally gated; slope drift 0.82 → 0.93 confirms structure loosening into pre-print). XLF — hold existing entry; signal stable on every input, no action needed. TLT — reasonable second tradeable entry, Quarter notional, wide put credit spread or iron condor 30-45 DTE, diversifies away from equity-beta XLF (caveat: low absolute IV 11.4 means thin premium per spread). JNJ — stay out; slope at 1.04 is one print from CAUTION trigger; asymmetry hasn't changed. MCD — IF still held, **close at open today** (correcting yesterday's "IV plateaued" call which was wrong — slope spike 1.32 → 1.56 is the final-day IV ramp; today's elevated mark is being inflated by vega that crushes tomorrow regardless of direction; selling into today's IV vs tomorrow's post-event liquidity tightening is a meaningful exit advantage). NVDA — off the table (15d to earnings). UBER reports tomorrow AMC, watch for D1/D2 read on the post-earnings template. Hold powder for May 19-22 (WMT post-print) and Jun 10-15 (mega-cap RV30 unwind). The cycle remains in mechanical waiting mode for ~3 weeks; today's actionable: TLT new entry candidate, MCD final close, otherwise hold XLF and powder.**

---

## 2026-05-04 (Monday)

**Regime:** THE PLAYOFFS (Stress Bottoming) | **Tradeable:** 1S / 3C | **Avg VRP:** -3.2

**Major shift — tradeable count quadrupled overnight (1 → 4).** WMT crossed into SELL (63 → 65), JNJ recovered to CONDITIONAL (44 → 53), XLF and IWM both crossed the 45 threshold to new CONDITIONAL. Stress collapsed further to 10% (3/30 eligible — **zero DANGER**, three CAUTION: HD, XLE, XOM). **AAPL completed the mega-cap pattern in textbook fashion:** Day-1 slope 1.54 (DANGER) → **Day-2 slope 0.81** (clean contango), IV pct crushed 68 → 24, score 23 NO EDGE NORMAL. The KO Day-2 delayed-crush template is now confirmed across **all three** mega-cap reporters that initially looked like thesis failures (MSFT 2.00→1.91→1.02, AMZN 1.74→1.90→0.91, AAPL 1.40→1.54→0.81). My Apr 30 "cycle is dead" call was wrong — Day-1 is noise, Day-2 is the real signal. This pattern goes into the standing playbook. **Index VRP finally recovering:** SPY VRP -2.0 → -0.5 (highest reading since Apr 13), QQQ -2.3 → -0.4. SPY slope 0.65 and QQQ 0.70 are series-deepest contango. Mechanism: IV ticked up modestly while RV30 dropped (both indexes). The fear-draining macro thesis is still working — slower than originally forecast but real. If trajectory holds 3-5 more sessions, SPY VRP crosses positive (macro green-light). **Post-earnings cohort uniformly clean-slope-but-VRP-pinned:** AMZN 0.71, META 0.74, GOOG 0.79, AAPL 0.81, MSFT 0.84, KO 0.94 — six names sub-0.85 (deep contango zone, 18-20 of 20 term-structure points). VRP across the cohort ranges -0.9 (AAPL) to -22.7 (HOOD) — pure RV30 roll-off problem now. **Day-over-day key moves:** WMT slope 0.89 → 0.82 (deepest of series), VRP 8.1 stable, accel back to 1.00 — **strongest non-earnings signal in 2 weeks BUT verified May 14 earnings = 9 days today, formally gated**; JNJ accel 1.27 → 1.24 (sitting at exact 1.25 hard-exit boundary, one bad scan from triggering); NVDA slope 0.88 → 0.75 (deepest NVDA contango of series) but accel 1.18 still warn + 16d to earnings; XOM Day-3 partial crush only (1.24 → 1.07, still CAUTION) — energy slower than mega-caps to normalize. **Re-entry calendar locked:** May 14 (WMT prints), May 19-22 (WMT post-print re-entry window, Jun 19 expiry target), ~May 25-30 (early reporters' RV30 begins rolling off), **Jun 10-15 (peak re-entry window for mega-caps when RV30 fully unwinds)**. After this week's UBER/MCD/PLTR prints, the universe is in pure mechanical waiting for ~3 weeks.

**Position: WMT — UNTRADEABLE despite SELL signal. Verified May 14 = 9 days today, formally gated. The signal at peak just as the gate fires is exactly the trap the verified-earnings discipline is designed to catch. Existing position: close at today's open if not already done. Re-entry plan: May 19-22 if score 65+ post-print, Jun 19 expiry. JNJ — PASS. Recovery to 53 looks tempting but accel 1.24 at the 1.25 hard-exit boundary means likely 1-2 sessions to stop-out. Asymmetry doesn't pay: maybe 5d theta if it works vs. immediate stop on one accel print. XLF — Quarter-to-Half notional CONDITIONAL entry. Iron condor or wide put credit spread, 30-45 DTE. Cleanest of the three new tradeables (slope 0.82, VRP 2.0, IV pct 56, accel 0.53 very stable, ETF = no earnings risk). The ONLY actionable signal from this scan. IWM — Pass. Score 45 right at threshold, every input borderline. NVDA — Watch but don't touch (16d to earnings, accel 1.18 warn). MCD existing — last clean exit window before tomorrow's pre-print IV peak; P&L direction has been pending all week, this is the binary day. AMZN/MSFT/META/GOOG — calendar reminder for Jun 10-15 re-entry when RV30 unwinds. The cycle has turned but the actionable opportunity from today is thin; hold powder for May 19-22 (WMT) and Jun 10-15 (mega-caps).**

---

## 2026-05-01 (Friday)

**Regime:** THE PLAYOFFS (Stress Cleared) | **Tradeable:** 0S / 1C | **Avg VRP:** -3.0

Major regime shift back to THE PLAYOFFS — stress collapsed from 28.6% (Apr 30) to **10.3%** (3/29 eligible: AAPL DANGER, HD + XLE CAUTION). EEM, TLT, META, GOOG, SBUX, KO all exited CAUTION as slopes normalized. Yesterday's REGULAR SEASON reading is confirmed event-driven and gone in one session. **Thesis update: I owe a correction from yesterday's "MSFT/AMZN cycle is dead" call — both crushed massively on Day 2.** MSFT slope **2.00 → 1.91 → 1.02** with IV −11.4 vol points, AMZN **1.74 → 1.90 → 0.91** with IV −13.7. The KO Day-2 delayed-crush template applies to mega-caps too — Day-1 readings are noisy/idiosyncratic, Day-2 reveals the real crush. The "loaded spring" thesis was right on direction; we had the timing wrong by one session. **Post-earnings cohort state:** GOOG, META, CAT, KO, SBUX, HOOD, MSFT, AMZN all show clean slopes (≤1.02) but **VRP deeply negative on all of them** because RV30 absorbed the earnings-day move and won't roll off for ~30 trading days. Negative VRP count reached 18/29 = 62% (vs 54% yesterday) — entirely driven by post-earnings reporters. **AAPL D1 shows DANGER (slope 1.40 → 1.54 deepened)** — expect Day-2 crush Mon following MSFT/AMZN template. **Day-over-day:** WMT 58 → 63 (slope back to 0.89, accel back below 1.0, VRP 8.1) — strongest signal in 8 sessions but verified May 14 earnings = **13d today, gates Monday**; JNJ 46 → 44 (lost CONDITIONAL by 1pt as score moved on slope-noise axis); NVDA 26 → 32 (slope back to contango 0.88, cluster radiation fully unwound, but accel 1.13 still warn); TLT exited CAUTION (slope 1.06 → 0.86, possible rate-policy noise resolving); XLE exited DANGER (1.29 → 1.11) post-XOM print absorbed. **Macro structurally constructive:** SPY slope **0.68** (deepest contango in series), QQQ 0.74, SPY IV pct 54 → 45, fear continuing to drain. Only thing missing is VRP and that's a mechanical roll-off issue, not a structural one. **Re-entry timeline now bracketed:** WMT post-print May 15-16 (first non-event candidate), early RV30 unwind (KO, MCD) ~May 25-30, **peak re-entry window ~Jun 5-15** when mega-cap RV30 fully unwinds with slope clean + VRP wide combo. The "fattest opportunity day" forecast carried since Apr 14 finally has a credible target.

**Position: WMT — last tradeable day of this cycle. Take 50% profit if it hits today, otherwise close at Mon open. Verified May 14 earnings = 13d means Mon's scan dashboards SKIP/0; pre-earnings IV expansion next week is the actual cost. Re-entry plan: Jun 19 expiry, May 19-22 window if score 65+ post-print. JNJ — no change, off the table since Tue (accel 1.27 still hard-exit). NVDA — watchable not actionable; cluster radiation done, but 19d to earnings limits the window. Don't pre-position. MCD — 6d to earnings, slope 1.40 plateau, accel improving 1.30 → 1.22. P&L direction still pending; close before Tue pre-print IV peak rather than rolling. AAPL — wait for D2 crush confirmation Mon, then add to post-earnings watchlist. AMZN/MSFT — calendar reminder for ~Jun 5-15 re-entry window when RV30 unwinds. The next 3 weeks are mechanical waiting.**

---

## 2026-04-30 (Thursday)

**Regime:** REGULAR SEASON (Event-Driven Stress) | **Tradeable:** 0S / 2C | **Avg VRP:** -1.3

Stress climbed to 28.6% (3 DANGER + 5 CAUTION = 8/28 eligible) but **the regime label is misleading** — 3 of 8 stressed names are post-earnings reporters (MSFT, AMZN in DANGER; META in CAUTION). Strip them and structural stress = 5/25 = 20% (THE PLAYOFFS). Read this as residual post-event stress, not market deterioration. **Post-earnings forensics from the Wed AMC quad split into two camps:** GOOG, CAT (+ SBUX D2, HOOD D3) crushed cleanly — slopes normalized to ≤1.07 — but **VRP turned deeply negative on all four** because RV30 caught up to crushed IV (GOOG -3.0, SBUX -9.2, HOOD -17.9, CAT -4.9). MSFT and AMZN broke the model: **MSFT slope 2.00 → 1.91, AMZN slope 1.74 → 1.90 (deepened)** — the IV crush thesis failed for the mega-caps that mattered most. AMZN scored 51 today but DANGER override forced AVOID — first time in this series the regime override has bitten an otherwise-tradeable score (textbook ADR-011 in action). The "fattest opportunity Friday" forecast carried since Apr 14 is now formally downgraded: **realistic re-entry window pushed from "next Tue–Wed" to ~May 12–14**, contingent on (a) MSFT/AMZN slopes normalizing below 1.15 by Mon, and (b) RV30 rolling off the earnings-spike day to widen post-print VRP. **Day-over-day key moves:** WMT 64 → 58, accel crossed 1.0 (0.84 → 1.01), pre-earnings IV building, **verified May 14 earnings = exactly 14d today, gate fires tomorrow's scan**; JNJ 48 → 46, accel still 1.27 (hard exit zone unchanged); **NVDA 38 → 26 (-12)** — cluster IV reversion fully unwound, slope broke contango (0.95 → 1.01), accel 0.97 → 1.14; XLE re-entered DANGER deeper (1.09 → 1.29) into Fri's XOM print; TLT new CAUTION (slope 0.90 → 1.06, possible rate-policy expectation shift); 54% of eligible names now have negative VRP (vs 40% yesterday), driven by post-earnings reporters. SPY VRP -1.6 → -1.5 — fear-draining macro thesis officially stalled. Tomorrow watch: AAPL Day 1 read (does it follow GOOG-clean-crush or MSFT-slope-persists), XOM print into XLE 1.29 DANGER, MSFT/AMZN Day 2 slope normalization or stuck.

**Position: WMT — close at open Fri at the latest. Verified May 14 earnings = 14d today, gates tomorrow's scan; pre-earnings IV expansion already showing (accel crossed 1.0). Re-entry plan unchanged: target Jun 19 expiry, May 18-21 window if score 65+ post-print. JNJ — no change. Score-up via slope-noise; accel 1.27 stays in hard-exit zone. NVDA off watchlist entirely (slope broke contango, score collapsed). MCD existing — slope 1.34 → 1.39, accel 1.19 → 1.30 (Quarter zone), 7d to earnings; bleed accelerating, P&L direction still pending. AMZN/MSFT framework test — score 51 with AVOID (DANGER) is exactly what ADR-011 prevents from misleading you; do NOT enter into 1.90 slope. Watch as re-entry candidates if slopes normalize sub-1.15 by Mon-Tue. Otherwise cycle is dead and we shift to "wait for May 12-14 RV30 roll-off + AAPL/XOM cycle clean" posture.**

---

## 2026-04-29 (Wednesday)

**Regime:** REGULAR SEASON (Stress Crossed Threshold) | **Tradeable:** 0S / 2C | **Avg VRP:** -0.4

First regime shift out of THE PLAYOFFS in weeks — stress crossed 25% on the eligible base (1 DANGER + 5 CAUTION = 6/23 = 26.1%). SBUX moved to DANGER alone (slope deepened post-print 1.90 → **2.06**, an anomaly breaking the IV-crush template), with EEM/HD/XLE/KO/HOOD in CAUTION. HD and XLE both backed off DANGER (1.19 → 1.11, 1.21 → 1.09). Tradeable count doubled to 2C as **WMT rebounded 58 → 64** (slope 0.97 → 0.92, skew 0.9 → 2.0, VRP 8.5 → 8.1) and **JNJ recovered 39 → 48** (slope 1.14 → 1.02, exited CAUTION). Both signals compromised: WMT verified May 14 earnings means gate fires Friday's scan (15d → 13d crosses threshold); JNJ score-up came via the noisy axis (slope) while the structural axis deteriorated (**accel 1.18 → 1.27**, hard exit zone). **Post-earnings reads from Tue AMC reporters revised yesterday's thesis:** META clean crush (slope 1.70 → **1.09**, VRP -6.9, RV30 +4.3 — classic NFLX template), **KO delayed Day-2 crush** (slope 1.47 → 1.11, VRP 1.4 → -0.8 — yesterday's "no IV crush" reading was misleading; the crush comes one day later), HOOD continued bleed (VRP -2.2 → -4.6), SBUX broken model. Three of four reporters cleanly crushing is the realistic base case for tonight's MSFT/AMZN/GOOG quad. **Pre-print slopes hit series-high peaks:** MSFT 2.00 (highest pre-earnings reading in the entire briefing record, IV pct 99, VRP 9.7), AMZN 1.74, GOOG 1.64. NVDA cluster-IV radiation reversed exactly as forecast yesterday — IV 45.8 → 43.6, IV pct 65 → 55, score 42 → 38. Borrowed IV being returned. SPY VRP went the wrong way -0.9 → -1.6, puncturing Mon's "fear draining" macro thesis. NKE θ/V dropped to 0.01 — possible vega-convention flip not caught by the >5 normalization heuristic; sanity-check tomorrow. **Implication for next week's entry window:** the IV crush is a Day 4-5 event, not Day 1 (KO confirmed this). Real tradeable signals from the quad-print won't show up cleanly until Tue-Wed (May 5-6). Friday's scan is diagnostic, not entry.

**Position: WMT existing — close before Friday's gate fires (Thu open at latest if 50% profit doesn't hit today/tomorrow); no new entry despite 64 score given 15d to verified May 14 earnings. JNJ — stay out if exited per Apr 27 trigger. Score-up is slope-noise; accel 1.27 is the structural exit signal firing today on the second axis. MCD existing — pre-earnings IV expansion grinding harder (slope 1.26 → 1.34); decision still pending P&L direction. Cash otherwise. Re-entry window: post-MSFT/AMZN/GOOG Day 4-5 (May 5-6) IF slopes normalize sub-0.95 AND IV crushes deliver wide VRP. Watch SPY VRP for cross-back-to-zero, JNJ accel for 1.30 escalation, SBUX for whether the 2.06 anomaly mean-reverts or signals broader regime stress.**

---

## 2026-04-28 (Tuesday)

**Regime:** THE PLAYOFFS (Pre-Earnings Apex) | **Tradeable:** 0S / 1C | **Avg VRP:** -0.1

The "1.00 flat wall" reasserted itself one session after Monday's clean break. Tradeable count collapsed 1S/2C → 0S/1C as JNJ broke its slope discipline (0.94 → 1.14, entered CAUTION — Apr 27 exit trigger fired) and IWM lost contango (0.86 → 0.94, dropped CONDITIONAL). WMT held but downgraded to CONDITIONAL at 58 (-9): VRP intact (8.5), score loss came from slope loosening (0.89 → 0.97) and skew compression (1.7 → 0.9). **Earnings verification override:** scanner shows WMT 23d, but actual earnings is May 14 (16d) — FMP drift confirmed; gate fires Friday, so WMT is effectively untradeable in this scan even at CONDITIONAL. Re-entry plan: target Jun 19 expiry in May 18–21 window if WMT scores 65+ post-print. **Pre-earnings backwardation hit series-peak day:** MSFT 1.93 (highest pre-earnings slope in the entire briefing record), SBUX 1.90, AMZN 1.72, META 1.70, GOOG 1.57, CAT 1.54, KO 1.47, XOM 1.36, AAPL 1.35. **Tonight's three reporters (KO/SBUX/HOOD) revised the post-earnings thesis:** none showed clean IV crush. KO IV barely moved (21.4 → 20.9), RV30 expanded, slope *deepened* 1.33 → 1.47. SBUX same pattern, slope to 1.90. Only HOOD followed the NFLX/TSLA template (VRP collapse via RV30 expansion +9.4 pts, slope normalized 1.27 → 1.07). Two divergent post-earnings mechanics observed in one night — Wednesday's MSFT/AMZN/META/GOOG quad-print is no longer assumed to produce a "wide VRP + contango" Friday bonanza. The "loaded spring" forecast is now soft. NVDA edge is cluster-IV radiation, not structural — IV +4.7 in one session with no NVDA catalyst, slope drifted 0.84 → 0.99; score flat at 42 because additive model correctly nets contango erosion against IV expansion. HD entered DANGER (slope 1.08 → 1.19, IV Pct 98 universe-high) — story unverified, possible FMP earnings drift like WMT or sector stress. XLE re-entered DANGER (1.15 → 1.21). Stress 4/20 = 20% (below REGULAR SEASON threshold). Constructive macro signal: SPY VRP -1.5 → -0.9 (highest of the period), driven by IV compression with RV holding — fear draining, not edge widening yet.

**Position: WMT Hold CONDITIONAL Full (existing only — no new entry; verify May 14 earnings, plan Jun 19 expiry re-entry post-print). JNJ EXIT (CAUTION + slope 1.14 + accel 1.18 sustained 4 sessions = Apr 27 exit rule fires). MCD existing position: pre-earnings IV expansion (slope 1.13 → 1.26) bleeding mark-to-market faster than theta accrues; decide tonight (close at open Wed if loss, defensive Jul $260 roll if break-even, close-and-walk if small gain) — KO post-earnings tells us not to count on a clean IV-crush bailout. NVDA off watchlist until cluster clears. Friday's scan is the diagnostic, not the assumed payoff.**

---

## 2026-04-27 (Monday)

**Regime:** THE PLAYOFFS (Stress Creeping, Inflection Loaded) | **Tradeable:** 1S / 2C | **Avg VRP:** -0.4

The "1.00 flat wall" broke. Index ETFs and financials all pushed off slope=1.00 into healthy contango — IWM 1.02→0.86 (+12 to 48, NEW CONDITIONAL), XLF 1.00→0.81 (+13 to 44), JPM 1.00→0.85 (+9), GS 1.00→0.91 (+7), TLT 0.99→0.87 (+10). SPY hit series-deepest 0.76, QQQ stable 0.82 — index structure is the cleanest of the month. WMT held SELL at 67 with VRP slightly narrowed to 8.3 but slope (0.89) and skew (-2.0→+1.7) compensating. JNJ ticked up to 53 on slope improvement (1.04→0.94), but **accel stuck at 1.20 for the third consecutive scan** — Half size cap holds, exit if accel >1.25 or slope back above 1.0. IWM is slope-driven only (VRP just 1.0); Quarter sizing, defined-risk only. Stress climbed back to 23.8% (5/21 eligible) — XLE re-entered CAUTION (slope 0.97→1.15), CAT slipped to AVOID (DANGER, slope 1.34) after FMP/Yahoo pushed earnings to TBD. Three tickers (CAT, HD, MCD) had earnings dates drift to TBD — verify before action. Mega-cap pre-earnings slopes compressing but not unwound: MSFT 1.77→1.64, AMZN 1.68→1.55, META 1.60→1.48, SBUX 1.74→1.69. **This is the inflection week** — KO/HOOD/SBUX report Tue, AMZN/META/MSFT/GOOG Wed, AAPL Thu. Slopes 1.5+ today should collapse to <0.95 by Friday. Post-earnings ungate window opens ~May 14.

**Position: WMT Hold SELL Full (best signal, VRP 8.3, slope 0.89). JNJ Hold Half (accel-constrained at 1.20). IWM NEW Quarter (defined-risk only, thin VRP). NVDA watchlist (42, slope 0.84, 23d to earnings). Pre-position nothing into Wed/Thu earnings — wait for IV crush print before evaluating fresh signals on Friday's scan.**

---

## 2026-04-24 (Friday)

**Regime:** THE PLAYOFFS (Pre-Earnings Lockdown) | **Tradeable:** 1S / 1C | **Avg VRP:** -0.4

WMT pulled back 77→66 (-11) as slope loosened 0.87→0.94 and skew flipped negative (-2.0), but core thesis intact — VRP 9.8, IV pct 93, accel 0.84 (Full). Still the sole SELL. NVDA's edge evaporated: VRP compressed 9.5→5.8 as IV continued dropping (pct 49→43), score fell 55→42 (NO EDGE). JNJ staged a surprise +11 bounce (39→50, CONDITIONAL) on IV pct spike 78→92 and VRP widening 5.5→8.5, but RV accel at 1.20 (and rising) disqualifies it — likely a dead-cat bounce. TSLA post-earnings crush arrived: IV 56.2→41.6, IV pct 60→2, VRP flipped to -2.8. Textbook. MCD and CAT both newly earnings-gated (13d and 6d respectively) after TBD dates finally resolved — tradeable universe shrunk from 3 to 2 signals. XLE recovered (slope 1.15→0.97, exited DANGER). Net stress at 10% (2/20) — cleanest reading in over a week, but partially an artifact of 13 tickers being gated. Pre-earnings backwardation hit new extremes: MSFT slope 1.77 (series high), AMZN 1.68, META 1.60, SBUX 1.74, AAPL 1.27 (joining the extreme club). Mega-caps report in 4-6d.

**Position: WMT Hold SELL (Full — slope pullback, not structural breakdown). JNJ pass (accel 1.20 = dead-cat bounce). NVDA exit (VRP dried up). Cash otherwise. Mega-cap earnings next week (MSFT/AMZN/META/GOOG Apr 29-30, AAPL Apr 30) — slope compression from 1.60-1.77 to sub-0.90 will create the fattest VRP + contango combo of the year. The spring has never been this coiled.**

---

## 2026-04-23 (Thursday)

**Regime:** THE PLAYOFFS (Stabilizing) | **Tradeable:** 1S / 2C | **Avg VRP:** +0.5

WMT earned SELL at 77 (+14, second consecutive double-digit gain) — first SELL signal since JNJ on Apr 17 and highest non-gated score since MSFT's 83 on Apr 14. Every component strengthened: VRP 8.8→10.3, IV pct 90→93, slope 0.94→0.87 (contango deepening), skew 0.6→1.8. NVDA pulled back slightly (57→55) but thesis intact — VRP 9.5, slope 0.85, accel 0.81 (Full). JNJ collapse complete: 59→39 (-20) on VRP drop to 5.5 and RV accel spike to 1.17. Six-session decline 70→39 confirms exit was correct. TSLA post-earnings anomaly: IV *rose* 46.7→56.2 (unusual — no crush), VRP 10.8 (fattest in universe), slope 0.84 (contango). But score 42 (NO EDGE), accel 1.12 (Half). Monitor for accel drop. CAT ungated (TBD) but slope 1.38 = DANGER. Slope stress partially resolved: JNJ, GLD, GS all exited CAUTION. New CAUTION: EEM (1.12), XLF (1.06). Net stress 5/21 = 24%, below REGULAR SEASON. Pre-earnings backwardation extreme: SBUX 1.64, MSFT 1.62, AMZN 1.43. Mega-cap reports in 5-6d. MCD earnings TBD persists (4th session). XLB NO DATA again.

**Position: WMT Full SELL (hold/add — confirming strongly). NVDA Full CONDITIONAL (hold). TSLA watch (if accel <1.10 and score >45). Post-earnings mega-cap setup coiling — MSFT slope 1.62 will compress to sub-0.90, creating massive term structure + VRP opportunity.**

---

## 2026-04-22 (Wednesday)

**Regime:** THE PLAYOFFS (Stress Rising — 25% threshold) | **Tradeable:** 0S / 3C | **Avg VRP:** +0.3

WMT breakout: +17 to 63 (biggest single-day move of the series) as RV accel collapsed 1.17→0.87 (Full sizing), VRP widened 7.0→8.8, IV pct climbed to 90. NVDA continued strengthening (+6 to 57, third straight gain). But backwardation is spreading beyond earnings names — JNJ slope 0.98→1.15 (entered CAUTION, recommendation AVOID despite score 59), HD 1.10→1.17 (entered DANGER), GLD 0.94→1.10 (entered CAUTION), GS 1.02→1.09 (CAUTION), IWM 0.90→1.04 (lost CONDITIONAL). Stress count reached 5/20 (25%) — right at REGULAR SEASON threshold. Tradeable narrowed from 6C to 3C despite WMT breakout: JNJ regime-blocked, UBER earnings-gated (hit 14d), IWM slope-killed. RV deceleration wave (SPY 0.77→0.57, WMT 1.17→0.87, JNJ 1.15→0.97) offset by broad slope deterioration. MCD slope crossed 1.01 (backwardation) at 15d to earnings — one session from gate. TSLA reported today (0d). 13 tickers earnings-gated. Post-earnings thesis needs caveat: non-earnings slope deterioration may indicate broader market structure stress, not just pre-earnings anomaly. SPY slope 0.78→0.84 — watch closely.

**Position: WMT Full (VRP 8.8, IV pct 90, accel 0.87, slope 0.94, 29d to earnings). NVDA Full (VRP 9.5, slope 0.78, accel 0.70, 28d to earnings). JNJ exit — CAUTION regime, slope trend broken. Close both at 50% profit.**

---

## 2026-04-21 (Tuesday)

**Regime:** THE PLAYOFFS (Phase Transition — IV Expanding) | **Tradeable:** 0S / 6C | **Avg VRP:** +0.2

Potential inflection point. IV expanded across the entire universe for the first time in weeks — SPY +1.3, IWM +1.7, NVDA +2.5, UBER +3.2. Aggregate VRP turned positive (+0.2, was -0.9) for the first time since Apr 13. Negative VRP count dropped from 52% to 43%. Three new CONDITIONAL signals (NVDA, IWM, WMT) brought the tradeable count to 6 — most since Apr 13. NVDA was the breakout (+9 to 51) on VRP widening 5.7→8.8 with slope 0.78 and RV accel 0.70. JNJ continued its four-session slide (70→55) as RV accel hit 1.15 (zero RV Stability points) and slope reached 0.98. MCD took the #1 spot (56) but earnings TBD persists. Contango loosened broadly — SPY 0.67→0.78, QQQ 0.71→0.81, IWM 0.74→0.90. The "deepest contango of the series" is fading. Earnings names showed violent backwardation: AMZN 0.76→1.55 (extreme), CAT 1.04→1.24, KO 1.03→1.21, MSFT 0.85→1.03. Market pricing significant binary risk for next week's mega-cap reports. EEM and HD entered CAUTION; XLB recovered from NO DATA (22). TSLA reports tomorrow. Clean scan, all 33 tickers returned data.

**Position: NVDA Full (best risk-reward: VRP 8.8, slope 0.78, accel 0.70, 29d to earnings). JNJ exit/reduce — trend broken. MCD pass until earnings verified. Everything else cash. Post-earnings mega-cap thesis intact — AMZN's 1.55 slope will collapse post-report, creating massive VRP.**

---

## 2026-04-20 (Monday)

**Regime:** THE PLAYOFFS (Deep Complacency — Phase 4) | **Tradeable:** 0S / 3C | **Avg VRP:** -0.9

Zero SELL signals for the first time since Apr 14. JNJ dropped 9 points (70→61) over the weekend — VRP narrowed 8.8→7.8, slope worsened 0.91→0.94, IV pct declined 86→83. Edge eroding across all five components simultaneously. MCD (-6 to 58) and UBER (-6 to 50) also weakened. 11/21 eligible tickers (52%) have negative VRP; avg VRP -0.9. Index ETFs improved slightly (SPY VRP -4.0→-2.8, IWM -3.0→-0.8) but still negative. Contango remains the strongest signal — SPY 0.67 (deepest of the series), QQQ 0.71. Structure perfect, premium absent. NFLX post-earnings distortion fully resolved (slope 2.51→0.86, IV 60→29.9) but VRP deeply negative (-10.2). XLV exited DANGER (slope 1.16→1.00), XLI exited CAUTION (slope 1.10→1.00), XLE entered CAUTION (slope 1.04→1.08). PLTR newly earnings-gated (17d→14d). CAT ungated (13d→TBD, FMP drift). MCD earnings TBD — verify before trading. 11 tickers earnings-gated with mega-cap reports in 8-10d (MSFT, AMZN, META, GOOG, AAPL). TSLA reports in 2d. XLB NO DATA again. Clean scan otherwise (32/33 tickers).

**Position: JNJ Half (weakening trend, close at 50% profit). MCD pass until earnings date verified. UBER pass (score 50, too thin). Cash otherwise. Wait for post-earnings mega-cap IV crush (Apr 30–May 2) — MSFT pre-gate profile (IV pct 95, VRP 8.6, slope 0.85) suggests 75+ post-earnings. The spring is coiled.**

---

## 2026-04-17 (Friday)

**Regime:** THE PLAYOFFS (Complacency Phase) | **Tradeable:** 1S / 2C | **Avg VRP:** 0.2

**First clean scan from Lightsail** — all 33 tickers returned data, NO DATA issue fully resolved (was 10 tickers yesterday due to late scan timing). Term slopes now varied and realistic (0.68–2.51 vs yesterday's suspect 1.00 wall). Data verified against external sources (earnings dates, VIX, NFLX post-earnings). Contango deepened across the board: SPY 0.68, QQQ 0.73, NVDA 0.72 — deepest of the series. Index VRP still negative (SPY -4.0, QQQ -3.2, IWM -3.0) — IV crashing faster than RV, classic complacency. Strait of Hormuz reopened, Dow +1000, oil crashed 11.5% — risk-off fear draining rapidly.

**JNJ (68→70 SELL)** — strengthening. VRP stable at 8.8, slope 1.00→0.91 (contango restored). RV accel crossed 1.0 to 1.05 — minor flag but not disqualifying. Full size, 89d to earnings. **MCD (gated→64 CONDITIONAL)** — back in play after earnings refresh corrected date to 20d. VRP narrowed 7.2→5.8 but slope fixed to genuine 0.86 contango. **UBER (47→56 CONDITIONAL)** — biggest mover, +9 pts from slope normalizing (1.00→0.85). Approaching SELL threshold. **NFLX (49 AVOID/DANGER)** — post-earnings distortion: reported Apr 16 after close, stock -9.7%. Slope 2.51 (extreme backwardation), skew -30.0, IV 60 at 99th pctl. Pure noise, untradeable. 2 DANGER (NFLX, XLV), 1 CAUTION (XLI). 11 tickers earnings-gated (mega-caps report next week). 9/22 non-gated tickers have negative VRP.

**Position: JNJ Full. MCD Half (VRP narrowing, monitor). UBER watch — upgrade if it crosses 60 next scan. Cash otherwise.** Real opportunity comes post-earnings next week when mega-cap IV crushes widen VRP into this deep contango.

---

## 2026-04-16 (Thursday)

**Regime:** DEGRADED DATA | **Tradeable:** 1S / 1C | **Avg VRP:** N/A (unreliable)

**Data quality issue: 13 of 33 tickers returned NO DATA** — SPY, QQQ, IWM, GLD, XLI, XLB, META, TSLA, NFLX, GS all missing IV/VRP entirely. Additionally, 16 of the 20 remaining tickers show term slope of exactly 1.00 (yesterday: varied 0.72–1.48). MarketData.app options chain endpoint likely degraded during scan window. Term structure and skew unreliable across the board.

Of the valid data: **JNJ (68)** sole SELL — VRP widened 7.1→9.0 as IV rose 21.9→24.4, 90d to earnings, RV accel 0.96 (Full size eligible). **UBER (47)** upgraded to CONDITIONAL — VRP 9.7, improving, but term slope 1.00 vs yesterday's 1.09 makes the signal suspect. **MCD** newly gated (21d→7d, crossed 14d threshold). SBUX entered DANGER (slope 1.15, only ticker showing non-1.00 backwardation). NKE surged 15→39 as RV accel collapsed 1.67→0.62 (massive deceleration) but VRP still deeply negative (-21.4). XLE exited DANGER (slope 1.17→0.96, backwardation resolved).

**Position: Cash. Do not trade this scan.** The NO DATA issue across major index ETFs and mega-caps makes aggregate metrics meaningless. JNJ's fundamentals look fine but confirm with tomorrow's scan before acting. Investigate API errors — check if the new MarketData token has different endpoint permissions, or if this is a transient API outage.

---

## 2026-04-15 (Wednesday)

**Regime:** THE PLAYOFFS (Complacency Phase) | **Tradeable:** 2S / 0C | **Avg VRP:** -0.6

Earnings tsunami wiped out the top of the leaderboard. 11 tickers gated (MSFT, AAPL, GOOG, META, AMZN, NFLX, TSLA, KO, SBUX, HOOD, CAT) — all mega-caps out. Yesterday's entire top 3 gone: MSFT → gated, UBER → CAUTION (slope jumped 0.92→1.09), AAPL → gated. Zero CONDITIONAL signals (a first in the series). Only 2 SELL: **JNJ (68)** post-earnings IV crush (23.8→21.9, slope 1.48→0.96, 90d to next report) and **MCD (65)** — but MCD's earnings date jumped 9d→21d overnight, verify before trading. Avg VRP -0.6 (10/22 eligibles negative). Index ETFs in negative VRP (SPY -3.7, QQQ -3.8, IWM -2.1) — IV crashed faster than RV, classic Phase 4 Complacency. RV broadly decelerating (17+ below 1.0). NFLX reports today (slope 1.71, extreme pre-event). XLE lone DANGER. NKE still a post-earnings wreck (VRP -22.9). Backend regime shifted to ELEVATED RISK. **Position: JNJ Full + verified MCD Full; otherwise cash.** Wait for mega-cap IV crush to fatten VRP next week.

**Data note:** MarketData.app API flipped vega convention to raw BSM (100x scale) — patched in code (`_normalize_vega`) and DB. θ/V values below reflect corrected scale.

---

## 2026-04-14 (Tuesday)

**Regime:** THE PLAYOFFS (VRP Turned Negative) | **Tradeable:** 3S / 2C | **Avg VRP:** -0.2

VRP crossed zero — avg collapsed from 1.1 to -0.2 as RV caught up to IV. 15 of 25 eligibles now negative VRP (vs 12 yesterday). MSFT (83) stretches its lead — 7th straight day as leader with IV pctl 99 and VRP 14.3 still widening. UBER (70) and AAPL (65) both upgraded to SELL as earnings windows approach (15-16d). MCD dropped 70→0 on earnings gate (9d). XLE flipped back to DANGER (slope 1.31) — energy backwardation resurfacing. Peak earnings day: JNJ and JPM report today, NFLX Thursday (slope 1.76, acute pre-event fear). Contango relaxed slightly (avg slope 0.86→0.91). NKE still a post-earnings wreck (VRP -24.1, accel 1.71). XLB reported NO DATA — data quality issue to investigate. Top picks: MSFT Full, UBER Full (accel 0.74, fastest decel), AAPL Half. The "loaded spring" thesis held yesterday — now IV is crumbling instead. Wait for post-earnings IV reset or stick with the top 3.

---

## 2026-04-13 (Monday)

**Regime:** THE PLAYOFFS (Structure Perfect, Edge Thin) | **Tradeable:** 3S / 5C | **Avg VRP:** 1.1

Zero DANGER tickers — first time ever. Backwardation crisis fully resolved. Deepest contango on record (avg slope 0.86; SPY 0.66, NVDA 0.65). But VRP still thin at 1.1 avg, 12 tickers negative. "Loaded spring" — structure is set, waiting for IV to tick up. MSFT (76) 6th straight day as leader, UBER (73) holding, MCD (70) back to SELL. RV acceleration wave over — 17 tickers below 1.0. Peak earnings week: JNJ/JPM tomorrow, NFLX Thursday. KO just hit 14d gate. Post-earnings (Wed-Fri) may be the catalyst for VRP widening into this perfect contango.

---

## 2026-04-10 (Friday)

**Regime:** THE PLAYOFFS (Stabilizing) | **Tradeable:** 2S / 5C | **Avg VRP:** 2.3

Stabilizing. DANGER dropped to 1 (EEM only). XLE and XOM exited DANGER — energy backwardation finally resolving. UBER breakout: 63→78 SELL, RV accel dropped to 0.74 (fastest deceleration in universe). MSFT upgraded to Full size (accel 1.08, crossed below 1.10 threshold). VRP still widening to 15.9. Contango deepening broadly (SPY 0.77, QQQ 0.75, NVDA 0.66). But 12 tickers still negative VRP. Top picks: MSFT Full, UBER Full, MCD Full. Bank earnings Monday/Tuesday — JNJ, JPM, GS reporting.

---

## 2026-04-09 (Thursday)

**Regime:** THE PLAYOFFS (Deteriorating) | **Tradeable:** 2S / 5C | **Avg VRP:** 1.7

VRP collapsed to 1.7 — lowest of the period. 15/28 tickers now have negative VRP (half the universe). SPY and QQQ both negative VRP. RV catching up to IV across the board. XLB crashed 71→17 (IV pctl 91→25, VRP 14.6→-0.2). Only 2 SELL: MSFT (78, VRP still widening to 15.1) and MCD (65). UBER (63) flagged as sleeper — stable RV 0.89 with fat VRP 13.4. 13 tickers at Quarter sizing.

---

## 2026-04-07 (Tuesday)

**Regime:** THE PLAYOFFS (Earnings Season) | **Tradeable:** 5S / 4C | **Avg VRP:** 5.2

Earnings season hitting hard — 5 tickers gated (JNJ, JPM, GS, NFLX, TSLA). AAPL and MSFT tied at 73 SELL. XLB (71) best ETF play with fat VRP 14.6 and decelerating RV 0.86. AMZN (65) SELL but Quarter size (accel 1.21). Only 2 DANGER (XLE, XOM — energy sector). 14 tickers at Half/Quarter sizing. Top picks: AAPL Full, XLB Full, MSFT Half.

---

## 2026-04-01 (Wednesday)

**Regime:** THE PLAYOFFS | **Tradeable:** 3S / 5C | **Avg VRP:** 5.7

Regime shifted to THE PLAYOFFS. VRP compressed significantly (10.9→5.7) as IV mean-reverted. XLV collapsed 70→26 (IV dropped 26.4→17.8 in two days — premium evaporated). XLI 67→40. KO new leader at 79. AAPL 77, MSFT 71. 16 tickers at Quarter sizing from RV acceleration. NKE post-earnings: RV accel 1.66, VRP -0.0, slope 2.19 — not tradeable. JNJ/GS/JPM all earnings-gated.

---

## 2026-03-30 (Monday)

**Regime:** REGULAR SEASON (VRP Exploding) | **Tradeable:** 7S / 6C | **Avg VRP:** 10.9

VRP blew wide open — highest of the period. 7 SELL signals. MSFT hit 93 (near-max score). IV spiked across the board (25/31 tickers at 90+ IV percentile) while RV hadn't caught up. Best week yet for premium selling edge. JNJ at 15d earnings — one day above gate. SPY still CAUTION, IWM DANGER. The stress concentrated at index level while individual names found equilibrium. NKE earnings next day.

---

## 2026-03-26 (Wednesday)

**Regime:** REGULAR SEASON (Improving) | **Tradeable:** 2S / 8C | **Avg VRP:** 6.7

Normalizing. 6 tickers exited stress. First SELL signals of the week: JNJ (71) and MSFT (70). Term structures flattening — backwardation resolving. JNJ's slope collapsed 1.16→1.01 overnight. SPY flipped to DANGER (slope 1.18) while individual names normalized — unusual divergence. 10 tickers at Half/Quarter sizing from rising RV accel.

---

## 2026-03-25 (Tuesday)

**Regime:** REGULAR SEASON (Deteriorating) | **Tradeable:** 0S / 4C | **Avg VRP:** 5.9

Market got worse. DANGER count nearly doubled (5→9). Stress ratio jumped to 59%. RV acceleration rising (0.85→0.93) — vol re-accelerating. XLF, GS, XOM, SBUX all flipped to DANGER. SPY moved to CAUTION. Zero SELL signals. Only tradeable: GOOG (62), MSFT (52), AMZN (48), KO (45). The "post-shock recovery" thesis from Monday was premature.

---

## 2026-03-24 (Monday)

**Regime:** REGULAR SEASON | **Tradeable:** 1S / 5C | **Avg VRP:** 4.6

Post-shock environment. 20/32 tickers in backwardation. IV percentiles sky-high (19 tickers at 85+). RV acceleration low (avg 0.85) — the shock is fading. XLB sole SELL signal at 74 but IV of 46.3% on a materials ETF raised data quality concerns. 7 high-scoring tickers trapped by CAUTION/DANGER regimes. HOOD at -16.9 VRP — extreme negative. Best structure: GOOG (58) with deep contango 0.85.

---
