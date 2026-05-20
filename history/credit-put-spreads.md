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
