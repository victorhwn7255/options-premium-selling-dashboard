---
last_verified: 2026-04-16
verified_against: 2134cff
rot_risk: medium
rot_triggers:
  - docker-compose.yml
  - backend/main.py
  - frontend/src/app/page.tsx
  - frontend/src/lib/api.ts
  - frontend/src/lib/scoring.ts
  - frontend/src/components/RegimeBanner.tsx
audience: both
---

# Architecture

## Purpose

How the pieces fit together — service boundaries, data flow between them, and the ownership boundary that determines which code is authoritative for what. Read this before touching cross-service behavior.

## Scope

**This file covers:** Service topology, API proxy, scan lifecycle, frontend data flow, backend/frontend ownership, regime disconnect, external dependencies, module dependency graph.

**This file does NOT cover:**
- Scoring formula — see `1-domain/scoring-and-strategy.md`
- SQLite schema and CSV formats — see `2-system/data-model.md`
- Deployment commands and env vars — see `2-system/deployment.md`
- Domain terminology — see `1-domain/glossary.md`

---

## Service Topology

Three Docker services, no auth, no external database:

```
                                    ┌──────────────────────┐
                                    │   MarketData.app     │
                                    │   (options, stocks)  │
                                    └──────────┬───────────┘
                                               │
┌─────────────┐     /api/* rewrite    ┌────────┴───────────┐     ┌──────────────┐
│  Browser     ├────────────────────→ │  FastAPI Backend    │────→│  SQLite WAL  │
│  :3000       │                      │  :8000 (:8030 host) │     │  + CSVs      │
└──────┬──────┘                      └────────┬───────────┘     └──────────────┘
       │                                       │
┌──────┴──────┐                      ┌────────┴───────────┐
│  Next.js     │                      │  FMP (earnings)     │
│  Frontend    │                      │  Yahoo (verify)     │
│  :3000       │                      └────────────────────┘
└──────┬──────┘
       │
┌──────┴──────┐
│  Cloudflared │─── tunnel ──→ theta.thevixguy.com
└─────────────┘
```

The frontend never calls external APIs directly. All data flows through the backend. The Next.js server proxies `/api/*` requests to the backend via `next.config.js` rewrites (build-time `BACKEND_URL`, defaults to `http://localhost:8030` locally, `http://backend:8000` in Docker).

---

## Scan Lifecycle

A scan can be triggered by cron (6:30 PM ET, trading days) or manually (`POST /api/scan`). Both paths converge on `run_full_scan()`.

**Gate cascade** (manual trigger only — cron bypasses):

```
Is it a trading day?       → No: return cached + "Market closed"
Is it after 6:30 PM ET?   → No: return cached + "After 6:30 PM ET"
Already scanned today (ET)?→ Yes: return cached
Scan already running?      → Yes: return progress status
Otherwise                  → Launch background scan
```

**Per-ticker pipeline** (33 tickers, sequential via Semaphore(1)):

```
Stock snapshot → 180-day bars → Options chain (2 API calls) → Earnings date
    │                               │
    └──→ build_vol_surface() ───────┘
         ├── Liquidity filter
         ├── ATM IV (30-day interpolated)
         ├── IV Rank + Percentile (252-day history from SQLite)
         ├── Term structure (8 tenors)
         ├── Skew (25-delta)
         └── VRP = IV − RV30
                │
                └──→ score_opportunity()
                     ├── Composite score (0-100)
                     ├── Regime (NORMAL/CAUTION/DANGER)
                     ├── Recommendation
                     └── Position construction hints
```

**Post-scan** (fire-and-forget, non-blocking):
1. Yahoo Finance metrics verification (compares RV30, spot against independent computation)
2. Yahoo Finance earnings verification (overrides FMP if >5-day discrepancy, backfills missing dates)

---

## Frontend Data Flow

All state lives in `page.tsx` via `useState`. No state management library, no routing.

**On mount:**

```
fetchLatestScan()                  → GET /api/scan/latest → setApiData
fetchEarningsRemaining()           → GET /api/earnings/remaining
fetchVerificationLatest()          → GET /api/verify/latest
fetchEarningsVerificationLatest()  → GET /api/verify/earnings/latest
  (after apiData loads)
fetchComparison()                  → GET /api/scan/comparison → setDeltaMap
```

**Transform pipeline** (`scoring.ts`):

```
Backend TickerResult (snake_case)
  → convertApiTicker()
    ├── mapRecommendation()     "SELL PREMIUM" → "SELL", "REDUCE SIZE" → "AVOID"
    ├── Earnings gate           DTE ≤ 14 → score=0, action=SKIP, preGateScore saved
    ├── Sizing                  RV accel > 1.20 → Quarter, > 1.10 → Half, else Full
    └── θ/ν ratio               |theta / vega|
  → buildScoredData()          sort by score descending
  → DashboardTicker[]          → components
```

**Regime computation** (`RegimeBanner.tsx:computeRegime()`): runs on the transformed `DashboardTicker[]`, excludes SKIP and NO DATA tickers, produces the NBA-themed market regime. See [scoring-and-strategy.md § Dashboard-Level Market Regime](../1-domain/scoring-and-strategy.md#dashboard-level-market-regime).

---

## Ownership Boundary

The most important architectural invariant: **backend scoring is authoritative.**

| Responsibility | Owner | Why it's there |
|---|---|---|
| All metric computation | Backend | Single source of truth, pure functions, testable |
| Composite score (0-100) | Backend | Avoids formula drift between two codebases |
| Per-ticker regime | Backend | Requires term structure + IV rank + RV accel |
| Recommendation | Backend | Combines score + regime — one decision point |
| Position construction | Backend | Requires IV rank and VRP magnitude |
| Earnings gate (DTE ≤ 14 → SKIP) | **Frontend** | See [ADR-003](../3-guardrails/decisions/003-earnings-gate-frontend-only.md) |
| Position sizing (Full/Half/Quarter) | **Frontend** | Display concern driven by RV accel threshold |
| Dashboard market regime (NBA-themed) | **Frontend** | Independent classifier from aggregate ticker data |

See [ADR-001](../3-guardrails/decisions/001-single-source-scoring.md) for why the frontend doesn't recompute scores.

---

## Regime Disconnect

Two independent regime classifiers exist. This is deliberate — see [ADR-006](../3-guardrails/decisions/006-two-independent-regime-classifiers.md).

**Backend** (`main.py`, `RegimeSummary`): ELEVATED RISK / CAUTION / OPPORTUNITY / NORMAL. Uses aggregate averages (avg IV rank, avg RV accel, danger count) and SPY's term slope as VIX proxy.

**Frontend** (`RegimeBanner.tsx`): OFF SEASON / REGULAR SEASON / THE PLAYOFFS / THE FINALS. Uses per-ticker regime counts (danger%, stress%) and aggregate VRP + term slope.

The frontend **ignores** the backend's `overall_regime` field entirely. The backend regime is still computed and stored in `scan_results` but serves no display purpose.

---

## External Dependencies

| Service | Tier | Endpoints used | Rate | Purpose |
|---------|------|----------------|------|---------|
| MarketData.app | Starter $12/mo | `/v1/stocks/quotes/`, `/v1/stocks/candles/D/`, `/v1/options/chain/` (×2), `/v1/stocks/earnings/` | 10 calls/min (token bucket) | Primary data: spot, bars, options, earnings fallback |
| FMP | Free/paid | `/stable/earnings` | Uncapped (SQLite-cached) | Earnings dates (primary source) |
| Yahoo Finance | Free (yfinance) | Bars, VIX close, earnings dates | Post-scan only (blocking I/O in executor) | Verification + earnings override |

MarketData.app is the only required external dependency. FMP and Yahoo are optional (FMP for better earnings, Yahoo for verification).

---

## Module Dependency Graph

**Backend** (runtime imports only):

```
main.py
  ├── marketdata_client  (MarketDataClient, data classes)
  ├── fmp_client          (get_next_earnings)
  ├── calculator          (build_vol_surface, find_atm_greeks, compute_atr14)
  ├── scorer              (score_opportunity, ScoringParams)
  ├── database            (all CRUD functions)
  ├── csv_store           (append_daily_csv, append_quotes_csv)
  ├── models              (all Pydantic response models)
  └── [runtime] utils.verify_metrics  (optional, sys.path hack for Docker)

calculator  → marketdata_client (DailyBar, OptionContract)
scorer      → calculator (VolSurface)
csv_store   → marketdata_client (OptionContract)
fmp_client  → database (get_cached_earnings, store_cached_earnings)
```

**Frontend** (component tree):

```
page.tsx
  ├── Navbar → ThemeToggle, ExplainMetricsModal
  ├── RegimeBanner (exports computeRegime)
  ├── Leaderboard → DetailPanel
  └── RegimeGuideModal → RegimeSection

Hooks: useTheme (localStorage + DOM), useCssColors (getComputedStyle + MutationObserver)
Lib:   api.ts (fetch wrappers), scoring.ts (transform), types.ts, metrics-content.ts
```
