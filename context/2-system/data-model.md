---
last_verified: 2026-07-15
verified_against: human-machine-toggle (v2 Phase A schema live)
rot_risk: medium
rot_triggers:
  - backend/database.py
  - backend/csv_store.py
  - backend/backfill_bars.py
  - backend/backfill_v2.py
audience: both
---

# Data Model

## Purpose

Where data lives, what shape it takes, and how it flows through persistence layers. Lookup reference for anyone touching the database or CSV files.

## Scope

**This file covers:** SQLite schema, CSV formats, data lifecycle, earnings cache pipeline.

**This file does NOT cover:**
- Database function signatures — read `backend/database.py`
- CSV helper implementation — read `backend/csv_store.py`
- Backfill script internals — see `2-system/deployment.md`
- How metrics are computed from this data — see `references/metrics_v1.md`

---

## SQLite Database

**Path:** `backend/data/vol_history.db` (auto-created on first import of `database.py` via `init_db()`).  
**Mode:** WAL (Write-Ahead Logging) for concurrent reads. Foreign keys enabled.  
**Bind mount:** `./backend/data:/app/data` in Docker — database survives container rebuilds.

### Table: `daily_iv`

Per-ticker per-day IV/RV history. Primary data store for IV Rank and IV Percentile computation (252-day lookback).

| Column | Type | Notes |
|--------|------|-------|
| `ticker` | TEXT NOT NULL | e.g., "SPY" |
| `date` | TEXT NOT NULL | YYYY-MM-DD (ET trading date) |
| `atm_iv` | REAL NOT NULL | 30-day ATM IV, percentage (e.g., 22.5) |
| `rv30` | REAL | 30-day realized vol, percentage |
| `vrp` | REAL | iv - rv30 |
| `term_slope` | REAL | front_iv / back_iv |
| *(2026-07-04)* `skew_25d`, `rv10`, `iv_percentile`, `spot`, `earnings_dte` | REAL/INT | Added so backtests are exact instead of imputed |
| *(v2, 2026-07)* 28 additive Module-G columns | REAL/INT/TEXT | Estimator/forecaster/gate outputs per ticker-day: `v_gk, s_neg, s_pos, ewma_v_1/5/25/125, ewma_sneg_5/25, vbar, sigma_fwd, sigma_fwd_dn, fvrp_ratio, fvrp_z, slope_1m3m, accel_dn, global_factor, transient_tag, v2_gate_state, v2_eligible, v2_warm, low_coverage` + a `legacy_*` shadow snapshot of v1's decision (`legacy_signal_score/recommendation/regime/vrp_ratio/term_slope/rv_accel`). Written by the live scan's shadow step and `backfill_v2.py` via `store_daily_iv_v2()` (column-whitelisted). All nullable — v1 code never reads them. |

**PK:** `(ticker, date)`. **Index:** `idx_daily_iv_ticker(ticker, date DESC)`.  
**Write pattern:** Upsert via `ON CONFLICT DO UPDATE` — safe to re-run scans. New columns arrive via a PRAGMA-guarded `ALTER TABLE` loop on startup (idempotent, additive-only).  
**No pruning** — rows accumulate indefinitely. ~280 rows per ticker after 1 year.

### Table: `scan_results`

Full scan JSON snapshots. The frontend's primary data source via `/api/scan/latest`.

| Column | Type | Notes |
|--------|------|-------|
| `id` | INTEGER PK | Auto-increment |
| `scanned_at` | TEXT | UTC ISO timestamp + "Z" |
| `regime` | TEXT | JSON: RegimeSummary object |
| `tickers` | TEXT | JSON: array of TickerResult objects (30+ fields each) |
| `historical` | TEXT | JSON: `{ticker: HistoricalPoint[]}` for SPY + QQQ |

**Pruned to 50 rows** on each insert. The `tickers` JSON is patched in-place by `update_latest_scan_earnings()` when Yahoo overrides FMP earnings dates.

### Table: `scan_log`

Audit log of scan runs. Not pruned.

| Column | Type | Notes |
|--------|------|-------|
| `id` | INTEGER PK | Auto-increment |
| `timestamp` | TEXT | ISO format |
| `tickers_scanned` | INTEGER | Count of successful tickers |
| `duration_seconds` | REAL | Wall-clock scan time |
| `errors` | TEXT | JSON array of error strings |

### Table: `earnings_cache`

Per-ticker FMP earnings date cache. Cleared entirely on `POST /api/earnings/refresh`.

| Column | Type | Notes |
|--------|------|-------|
| `ticker` | TEXT PK | |
| `earnings_date` | TEXT | YYYY-MM-DD |
| `fetched_at` | TEXT | ISO timestamp |

Cache validity: `get_cached_earnings()` returns the date only if `earnings_date >= today`. Past dates are treated as cache misses.

### CPS tables (2026-05)

| Table | Purpose |
|-------|---------|
| `cps_candidate_history` | One row per ticker per CPS scan day (action, strikes, credit/width economics) — powers the 2-day SELL_CPS confirmation lookback. UNIQUE `(scan_date, ticker)`. |
| `cps_scan_responses` | Full CPS response JSON per scan day — the `GET /api/credit-put-spreads/latest` cache. |

### v2 tables (Phase A, 2026-07) — the silent data substrate

Seven tables added by the v2 build (all `CREATE TABLE IF NOT EXISTS`, inert to v1 code). See `tasks/v2-build/` for the arc.

| Table | Purpose | Written by | Populated? |
|-------|---------|-----------|------------|
| `daily_bars` | Full OHLCV per ticker-day — the forecaster's training substrate. `source` column flags the seam: `yfinance` (one-time 10y multi-regime seed, 2016→2026) vs `marketdata` (live scan upsert, going forward). `quarantine=1` marks integrity failures (H≥max(O,C), L≤min(O,C), O>0, \|ln return\|<0.5) — stored, never silently corrected, excluded from estimator reads. PK `(ticker,date)`. | `backfill_bars.py` + each live scan | ✅ ~79.7k rows (33 tickers × 10y), seeded on prod 2026-07-07 |
| `index_daily` | VIX family (`^VIX`, `^VIX3M`, `^VVIX`) daily OHLC from yfinance. PUT (Cboe PutWrite) deferred to Phase D. | `backfill_bars.py` | ✅ ~7.5k rows |
| `gate_state` | v2 hysteretic gate per ticker-day: `state` (NORMAL/CAUTION/DANGER) + `transient` flag. Feeds the shadow oscillation metric. | live scan shadow step + `backfill_v2.py` | ✅ |
| `shadow_diff` | The daily v1↔v2 divergence log: v1 action/regime vs v2 eligibility/gate + `divergence_class` (AGREE / V2_STRICTER / V2_LOOSER / STATE_MISMATCH / NODATA_SKEW) + reason + `v2_warm`. Served by `GET /api/shadow/diff` and summarized by `/api/shadow/summary`; source of `history/v2-metrics-logs.md`. | live scan shadow step only (not backfills) | ✅ since 2026-07-06 |
| `positions` | Option positions (Phase-A1 columns + the 2026-07-16 journal columns: `scan_ref` FK to the entry-day `scan_results` row, `thesis`, plan-at-entry `target_capture`/`exit_dte_plan`/`max_loss_plan`, backend-evaluated `checklist_json`, `exit_reason`, `followed_plan`, `roll_group_id`, nullable `user_id`). Phase-C fields (`f_star`, dials, `binding_cap`) stay NULL until Phase C. | Journal API (`positions_api.py`) / Phase C | ✅ live (trade-journal J1) |
| `trades` | Per-closed-trade Module-G telemetry (fill_vs_mid, quoted spreads, capture, rv_realized_hold…) — written by the journal's close flow; feeds Phase D realized-capture/PSR and Phase F trials. NULLs never block a close. | Journal close flow / Phase C-D | ✅ accrues per close |
| `portfolio_daily` | Daily portfolio aggregates. Journal writes the partial row (nav from settings, `notional_short_put`, `margin_total`); PSR/stress columns stay NULL until Phase C. | Journal mark step / Phase C-D | ✅ partial |
| `position_marks` | Daily EOD state per open position: net option mark from the scan's in-memory chain, `short_delta`, unrealized P&L, `capture_pct`, DTE, `mark_source` (`scan_chain` / `quote_fallback` / `carried` / `csv_backfill` — carried = last mark reused on a data gap, flagged, never interpolated). PK `(position_id, date)`. | scan mark step + `journal_backfill.py` | ✅ live (J1) |
| `app_settings` | Single-user key/value (NAV, journal defaults) | Journal API | ✅ |

Also: **`trial_registry.jsonl`** (file, beside the DB) — append-only registry for Phase F's pre-registered trials T1–T3; the only mechanism allowed to change live behavior post-cutover (P2). Created empty.

> **Journal access:** every `positions`/`journal`/`settings` route requires owner credentials (`backend/auth.py:require_owner` — Cloudflare Access JWT / bearer / dev-open; fail-closed 403 on reads and writes). See `deployment.md § Trade-journal privacy`.

### Tables: `verification_results` + `earnings_verification_results`

Post-scan Yahoo Finance cross-check results. Both pruned to 50 rows.

| Column (verification_results) | Type | Notes |
|------|------|-------|
| `scanned_at`, `verified_at` | TEXT | Timestamps |
| `total_checks`, `pass_count`, `warn_count`, `fail_count` | INTEGER | Summary counts |
| `failures`, `warnings`, `full_report` | TEXT | JSON arrays/objects |

| Column (earnings_verification_results) | Type | Notes |
|------|------|-------|
| `scanned_at`, `verified_at` | TEXT | Timestamps |
| `total_checks`, `pass_count`, `fail_count`, `skip_count` | INTEGER | Summary counts |
| `checks` | TEXT | JSON array of per-ticker check results |

---

## CSV Files

Two CSV families, one file per ticker. Stored in `backend/data/`.

### `data/daily/{TICKER}.csv`

Daily metrics snapshot. **Date-descending order** (newest first).

```
date,spot,atm_iv,rv30,vrp,term_slope
2026-04-16,551.23,18.45,14.32,4.13,0.923
2026-04-15,548.90,18.12,14.28,3.84,0.931
```

**Write behavior:** `append_daily_csv()` reads the entire file, appends the new row, sorts by date descending, and rewrites. Deduplicates by date. See [fragile-seams.md § CSV daily file rewrite](../3-guardrails/fragile-seams.md#csv-daily-file-rewrite) for the race condition risk.

### `data/quotes/{TICKER}.csv`

Full option chain quotes per scan day. **Append-only** (no rewrite).

```
date,option_symbol,underlying,strike,expiration,side,bid,ask,mid,last,underlying_price,dte,computed_iv,volume,open_interest
```

Option symbol format: `{TICKER}{YYYYMMDD}{C|P}{strike×1000 zero-padded to 8 digits}` (e.g., `SPY20260516C00550000`). Skipped if the date already exists in the file.

---

## Data Lifecycle

**Daily accumulation:** Each scan stores one row per ticker in `daily_iv` and appends to both CSV files. Over time, `daily_iv` builds the 252-day history needed for IV Rank and IV Percentile.

**Historical backfill:** `backfill.py` populates `daily_iv` retroactively using a two-step historical chain→quote fetch with BSM IV solving (costs MarketData credits). See `2-system/deployment.md` for usage.

**v2 backfills (one-time, re-runnable, zero MarketData cost):** `backfill_bars.py --period 10y` seeds `daily_bars` + `index_daily` from yfinance; `backfill_v2.py` then trains the pooled forecaster from stored bars and writes the v2 columns onto existing `daily_iv` rows (in-sample seed for the FVRP z-window; the live scan refits forward-only every night). Both ran on prod 2026-07-07. **They must be run inside the prod container to affect prod** — local and prod DBs are fully independent files (bind mount).

**Earnings pipeline:** FMP → SQLite cache → MarketData.app fallback → Yahoo Finance post-scan verification (backfill missing, override >5-day discrepancies). See [fragile-seams.md § FMP earnings date drift](../3-guardrails/fragile-seams.md#fmp-earnings-date-drift).

**Pruning:** `scan_results`, `verification_results`, and `earnings_verification_results` auto-prune to 50 rows on each insert. `daily_iv` and `scan_log` are never pruned.
