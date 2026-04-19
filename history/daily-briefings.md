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

**Position: [specific recommendations with sizing]**
```

**Analysis should cover:**
- Regime status and any shifts from previous day
- Top SELL and CONDITIONAL signals with scores
- Day-over-day changes for key tickers (score, VRP, slope, regime changes)
- Earnings gate impacts (newly gated/ungated tickers)
- Aggregate stats (avg VRP, % negative VRP, RV accel trends)
- Any data quality issues observed
- Actionable position recommendations with sizing (Full/Half/Quarter)

**Tone:** Concise, data-driven, opinionated. Reference specific numbers. Flag uncertainty.

---

> **IMPORTANT:** Entries are in **descending order** (newest first). New entries go immediately below this line.

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
