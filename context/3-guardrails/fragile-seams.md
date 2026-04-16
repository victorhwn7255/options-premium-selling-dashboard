---
last_verified: 2026-04-16
verified_against: 2134cff
rot_risk: high
rot_triggers:
  - backend/calculator.py
  - backend/marketdata_client.py
  - backend/main.py
  - backend/csv_store.py
  - frontend/src/lib/api.ts
audience: both
---

# Fragile Seams

## Purpose

This file answers: **"What will break if I'm not careful?"** It documents known fragile areas — places where the code, data, or external dependencies have sharp edges that aren't obvious from reading the source alone. Several of these have caused production issues before.

This is not a bug tracker or tech-debt list. Each entry here describes a **hazard that a reasonable contributor could trigger** by touching nearby code without understanding the hidden constraint. If something is a deliberate design choice that *looks* like a bug, it belongs in [`3-guardrails/decisions/`](decisions/) instead.

## Scope

**This file covers:**
- Data quality seams (API convention instability, thin chains, measurement noise)
- API integration seams (expiration alignment, earnings source conflicts)
- Persistence seams (file I/O races, in-memory state loss, query limits)
- Timezone seams (host vs. trading timezone)
- Frontend seams (silent failures, polling assumptions)

**This file does NOT cover:**
- Deliberate design choices — see `3-guardrails/decisions/`
- Scoring formula details — see `1-domain/scoring-and-strategy.md`
- Deployment configuration — see `2-system/deployment.md`

---

## Data Quality Seams

### Vega convention instability

**Where:** `calculator.py:_normalize_vega()` (lines 320–329)

MarketData.app intermittently switches between two vega conventions: **per-1%-IV** (standard display convention, values typically 0.01–5.0 for US equities) and **raw BSM** (per-1.0 change in sigma, values ~100× larger). The switch is not announced and has been observed to flip between consecutive API calls on the same day (confirmed 2026-04-15).

The fix is a magnitude-based heuristic: if `|vega| > 5`, divide by 100. This works because per-1% vega for any US equity option is physically bounded below ~5 (it would require an implausibly high-gamma, deep-ITM, long-dated contract to exceed this).

**Hazard:** If you change the ATM contract selection (e.g., widening the strike range), you might select contracts where per-1% vega legitimately approaches the threshold. The heuristic has no way to distinguish "unusually large per-1% vega" from "raw BSM vega." Test with a range of tickers before modifying `find_atm_greeks()` or the 3% ATM range.

**Theta is NOT normalized** — it uses a consistent per-day convention from the API.

### Skew = 0 for illiquid tickers

**Where:** `calculator.py:compute_skew()` (lines 472–578)

5+ tickers regularly return `skew_25d = 0.0` because they lack sufficient liquid contracts in the 20–30 delta range at the nearest-to-30-DTE expiration. When no 25-delta puts pass the filter, `put_25d_iv` is `None` and the skew defaults to 0.

**Impact:** Understates the composite score by up to 10 points (the full skew component). These tickers appear less attractive than they actually are. No simple fix — the data genuinely isn't there. Widening the delta bucket would introduce contracts that don't represent the 25-delta risk premium.

### RV10 window sensitivity

**Where:** `calculator.py:compute_realized_vol()` (lines 152–181)

RV10 uses only the last 10 daily log-returns. A single outlier close (e.g., a late-day algo spike or a stock-split day that wasn't perfectly adjusted) can shift RV10 by 2–5 vol points, which cascades into RV acceleration (rv10/rv30) crossing the 1.10 or 1.20 sizing thresholds. A ticker can flip between Full and Half sizing on a single noisy closing print.

**Hazard:** Any change to the bar data source (e.g., switching from close-to-close to intraday OHLC) would alter RV10 materially and require recalibrating the sizing thresholds.

### EEM historical IV anomaly

Historical data for EEM contains a 289.88% ATM IV entry. Verified in the database: **2026-03-18 in SQLite** (`daily_iv` table) and **2026-03-17 in CSV** (`data/daily/EEM.csv`). The one-day date discrepancy is a remnant of the CSV date bug (CSVs used to write the last bar's date rather than the ET trading date; fixed in `1e896e5`). This is a garbage data point from the API that was stored before the 200% IV cap was added to `compute_atm_iv()`. It inflates IV Rank for EEM when it falls within the 252-day lookback window. Harmless once it ages out (~2027-03), but not cleaned from the database.

---

## API Integration Seams

### Skew expiration alignment

**Where:** `marketdata_client.py:get_options_chain()` (lines 233–255)

The options chain is fetched in two calls: a narrow chain (all expirations, 12 strikes) for ATM IV and term structure, and a wide chain (60 strikes, one expiration) for skew. The wide chain **must** target the exact expiration date that `compute_skew()` will select (nearest to 30 DTE).

**History:** This broke twice, both fixes visible in git:

1. **`6f1b338` (2026-03-21):** The original code hardcoded `dte=30` for the wide chain. The API interpreted this differently than `compute_skew()`'s expiration selection, causing most tickers to have zero skew. Fix: derive the actual DTE from the narrow chain's expiration data and pass `dte=skew_dte`.
2. **`1e896e5` (v1.08):** The DTE-based fix still didn't match — the API's DTE→expiration mapping differed from ours by a day in some cases. Fix: switched from passing `dte=` to `expiration=YYYY-MM-DD` (the actual date string derived from the narrow chain), eliminating the interpretation gap entirely.

**Hazard:** If you change `compute_skew()`'s expiration selection logic (e.g., switching from nearest-to-30-DTE to a specific tenor), you must also update the wide chain's expiration selection in `get_options_chain()` to match. These two pieces of code are in different files (`calculator.py` vs. `marketdata_client.py`) with no compile-time coupling.

### FMP earnings date drift

**Where:** `fmp_client.py`, `main.py` (post-scan verification, lines 518–553)

FMP (Financial Modeling Prep) earnings dates can shift by multiple weeks day-over-day for the same ticker. A date reported as April 28 on Monday might become May 12 on Tuesday with no explanation. This is an upstream data quality issue.

**Mitigation:** Post-scan, the system fetches Yahoo Finance earnings dates and compares. If the FMP and Yahoo dates differ by more than 5 days, the Yahoo date overrides FMP in the cached scan result (`update_latest_scan_earnings()`). If FMP returns nothing but Yahoo has a date, it backfills. This happens automatically after every scan. The Yahoo verification feature was added in `5479b53` (v1.03).

**Current state (verified 2026-04-16):** The last 5 scans each show 3–4 tickers with FMP/Yahoo discrepancies >5 days (MCD, SBUX, HOOD, WMT — diffs of 6–15 days). This is an ongoing upstream data quality issue, not a one-time incident.

**Hazard:** The earnings gate (DTE ≤ 14 → SKIP) operates on whatever date is in the scan result. If both FMP and Yahoo are wrong, a ticker could be incorrectly gated or incorrectly cleared. There is no third source to arbitrate. The user should verify earnings dates for any ticker they're about to trade — the dashboard date is a best-effort estimate, not a guarantee.

---

## Persistence Seams

### CSV daily file rewrite

**Where:** `csv_store.py:append_daily_csv()` (lines 84–122)

To maintain date-descending order, `append_daily_csv()` reads the entire CSV into memory, appends the new row, sorts, and rewrites the file. This is not atomic — if the process crashes mid-write (or another process reads the file between the open-for-read and open-for-write), data can be lost or corrupted.

In practice this hasn't caused issues because scans run sequentially (semaphore=1) and no other process writes to these files. But it would break if concurrent writes were introduced (e.g., parallel scan processing or an external CSV updater).

### In-memory earnings refresh counter

**Where:** `main.py:_earnings_refresh_tracker` (line 870)

The daily limit for `POST /api/earnings/refresh` is tracked in a Python dict (`{"date": None, "count": 0}`). This resets to zero on every container restart, Docker rebuild, or uvicorn reload. There is no persistent backing store.

**Impact:** After a restart, the user can refresh earnings again even if they already used their daily quota. Minor — the limit exists to conserve FMP API calls, not as a security boundary.

### Scan gate checks ET date, not hour-of-day

**Where:** `main.py:_is_scanned_today()` (lines 611–616)

The "already scanned today" check compares ET calendar dates. If a scan runs at 11:30 PM ET on Tuesday, the gate prevents all rescans until midnight ET Wednesday. There is no way to trigger a second scan on the same calendar day, even if data conditions changed (e.g., a late-evening corporate action).

### Day-over-day comparison has a 50-scan horizon

**Where:** `database.py:get_previous_day_scan()` (lines 264–288)

To find the previous day's scan, the function walks the last 50 rows of `scan_results` looking for one whose ET date is before the current scan's ET date. If there's been a gap longer than 50 scans without a qualifying previous-day entry (unlikely but possible after bulk rescans or testing), the comparison returns nothing and the UI shows "First scan — no prior day comparison available."

---

## Timezone Seams

### Host timezone vs. trading timezone

The production host runs in SGT (UTC+8). All trading logic uses ET (America/New_York) via `zoneinfo.ZoneInfo`. This works correctly because every time-sensitive operation explicitly converts:

- Cron target: `datetime.now(tz=et)` in `_cron_loop()`
- Scan gate: `datetime.now(tz=et)` in `trigger_scan()`
- CSV dates: `datetime.now(tz=ZoneInfo("America/New_York")).date()` in `scan_single_ticker()`
- `_is_scanned_today()`: converts UTC timestamp to ET before comparing

**Hazard:** Any new time-sensitive code that uses `datetime.now()` without an explicit timezone will get SGT, which is 12–13 hours ahead of ET. This would cause date-boundary bugs — a scan at 7 AM SGT Wednesday would see "Tuesday" in ET but "Wednesday" in naive local time. Always pass `tz=ZoneInfo("America/New_York")` when the result feeds into trading-day logic.

The frontend duplicates this concern: `Navbar.tsx` computes market hours and trading-day status using `toLocaleDateString('en-US', { timeZone: 'America/New_York' })`. If the user's browser timezone is unusual, the browser's `Date` object handles the conversion correctly via the `timeZone` option — but this only works for display, not for gating.

---

## Frontend Seams

### Silent API error handling

**Where:** `frontend/src/lib/api.ts` (all functions), `frontend/src/app/page.tsx` (all useEffect hooks)

Every API call is wrapped in try/catch with empty catch blocks. When the backend is down, slow, or returning errors, the user sees no feedback — just a loading spinner that never resolves, or stale data that doesn't update. There is no toast, no error banner, no retry prompt.

**Impact:** During backend restarts (e.g., after `docker compose up --build`), the frontend silently fails to load data. The user has to manually refresh the browser and hope the backend is back up. This is the most user-visible seam in the system.

### Scan polling cadence

**Where:** `page.tsx` (lines 91–102, scan progress polling), `api.ts:pollForScanResults()` (lines 29–41)

During a scan, the frontend polls `/api/scan/status` every 3 seconds for progress updates, and `pollForScanResults()` polls every 5 seconds (up to 200 attempts, ~16 minutes) waiting for completion. With 33 tickers at 10 API calls/min, scans typically take 8–13 minutes. This produces ~250 progress polls and ~150 completion polls per scan — harmless for a single-user dashboard but would need rethinking for multiple concurrent users.

### Stale methodology footer in page.tsx

**Where:** `frontend/src/app/page.tsx` (line 216)

The methodology footer displays: *"VRP magnitude (0-40) + Term structure (0-25) + IV percentile (0-20) − RV acceleration penalty (0-15)"*. This is the **Phase-1 frontend scoring formula**. The actual backend scoring is VRP 0-30, IV Pct 0-25, Term 0-20, RV 0-15, Skew 0-10 — all additive, no penalties. The footer omits the Skew component entirely and describes a penalty model that was replaced in v1.08 (see [ADR-011](decisions/011-additive-scoring-replaces-penalty-based.md)).

**Hazard:** A user reading the footer and then examining the leaderboard would expect scores based on different weights and a different model. A contributor reading it before the code would have a wrong mental model of the scoring engine.

### Verification polling after scan

**Where:** `page.tsx:handleRefresh()` (lines 113–130)

After a scan completes, `page.tsx` starts a separate polling loop: 12 attempts × 10 seconds = 2 minutes, checking `/api/verify/latest` and `/api/verify/earnings/latest` for results matching the new scan's `scanned_at` timestamp. If the Yahoo verification takes longer than 2 minutes (network issues, yfinance rate limits), the verification badges show stale data from the previous scan with no visual indication that they're outdated.

---

## Historical Incidents

| Commit | Date | Seam | What happened | Fix |
|--------|------|------|---------------|-----|
| `6f1b338` | 2026-03-21 | Skew expiration alignment | Wide chain hardcoded `dte=30`. API picked different expiration than `compute_skew()`. Most tickers had zero skew. | Derive DTE from narrow chain's expiration data, pass `dte=skew_dte`. |
| `1e896e5` | v1.08 | Skew expiration alignment (recurrence) | DTE-based parameter still caused API to pick a different expiration in some cases (off-by-one day). | Switch from `dte=` to `expiration=YYYY-MM-DD` (exact date string). |
| — | 2026-04-15 | Vega convention | MarketData.app returned raw BSM vega for several tickers mid-scan. θ/ν ratio displayed as ~0.01 instead of ~1.0. | `_normalize_vega()` heuristic added (divide by 100 if \|v\| > 5). |
| `1e896e5` | v1.08 | CSV date bug | `append_daily_csv()` used `bars[-1].date` (last bar's date, stale or UTC-shifted) instead of current ET trading date. CSVs silently skipped writes when the stale date already existed. | Changed to `datetime.now(tz=ET).date().isoformat()`. |
| `5479b53` | v1.03 | FMP earnings drift | FMP dates diverged from Yahoo by 5–15 days for multiple tickers. Ongoing: as of 2026-04-16, 3–4 tickers per scan show >5-day FMP/Yahoo discrepancy. | Added Yahoo Finance cross-check with automatic override on >5-day discrepancy. |
