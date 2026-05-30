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
