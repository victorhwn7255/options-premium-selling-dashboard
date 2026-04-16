---
last_verified: 2026-04-16
verified_against: 2134cff
rot_risk: medium
rot_triggers:
  - backend/database.py
  - backend/csv_store.py
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
- Backfill script internals — see `context/deployment.md`
- How metrics are computed from this data — see `references/metrics_report.md`

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

**PK:** `(ticker, date)`. **Index:** `idx_daily_iv_ticker(ticker, date DESC)`.  
**Write pattern:** Upsert via `ON CONFLICT DO UPDATE` — safe to re-run scans.  
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

**Write behavior:** `append_daily_csv()` reads the entire file, appends the new row, sorts by date descending, and rewrites. Deduplicates by date. See [fragile-seams.md § CSV daily file rewrite](fragile-seams.md#csv-daily-file-rewrite) for the race condition risk.

### `data/quotes/{TICKER}.csv`

Full option chain quotes per scan day. **Append-only** (no rewrite).

```
date,option_symbol,underlying,strike,expiration,side,bid,ask,mid,last,underlying_price,dte,computed_iv,volume,open_interest
```

Option symbol format: `{TICKER}{YYYYMMDD}{C|P}{strike×1000 zero-padded to 8 digits}` (e.g., `SPY20260516C00550000`). Skipped if the date already exists in the file.

---

## Data Lifecycle

**Daily accumulation:** Each scan stores one row per ticker in `daily_iv` and appends to both CSV files. Over time, `daily_iv` builds the 252-day history needed for IV Rank and IV Percentile.

**Historical backfill:** `backfill.py` populates `daily_iv` retroactively using a two-step historical chain→quote fetch with BSM IV solving. See `context/deployment.md` for usage.

**Earnings pipeline:** FMP → SQLite cache → MarketData.app fallback → Yahoo Finance post-scan verification (backfill missing, override >5-day discrepancies). See [fragile-seams.md § FMP earnings date drift](fragile-seams.md#fmp-earnings-date-drift).

**Pruning:** `scan_results`, `verification_results`, and `earnings_verification_results` auto-prune to 50 rows on each insert. `daily_iv` and `scan_log` are never pruned.
