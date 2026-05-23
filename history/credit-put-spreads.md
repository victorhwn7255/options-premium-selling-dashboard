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
