---
last_verified: 2026-07-15
verified_against: human-machine-toggle (v2 Phase A shadow live; MACHINE view added)
rot_risk: medium
rot_triggers:
  - docker-compose.yml
  - backend/main.py
  - backend/forecast.py
  - frontend/src/app/page.tsx
  - frontend/src/lib/api.ts
  - frontend/src/lib/scoring.ts
  - frontend/src/components/RegimeBanner.tsx
  - frontend/src/components/machine/
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

**v2 shadow step** (Phase A, 2026-07 — after the scoring loop, before `store_scan_result`):

```
per ticker (during loop):  persist live OHLCV → daily_bars · capture chain partials (iv30/iv90 → slope_1m3m)
post-loop (cross-ticker):  train pooled forecaster from stored daily_bars (~seconds)
                           → global factor G_t (panel-coverage guard: <90% valid → carry-forward + low_coverage)
                           → per-ticker sigma_fwd / sigma_fwd_dn → FVRP ratio → fvrp_z (trailing window, min 60 obs)
                           → hysteretic GateState (seeded from prior persisted state)
                           → shadow eligibility vs [PROVISIONAL] dead zones → divergence classification
                           → write daily_iv v2 columns + gate_state + shadow_diff rows
```

**Advisory only** — v1 stays authoritative until Phase E (`ELIGIBILITY_AUTHORITY` flag). The entire step is `try/except`-isolated exactly like the CPS branch: a v2 failure logs `"v2 shadow: 0 rows"` and can never break the v1 scan (confirmed live). v2 telemetry rides **additively** on `TickerResult` (10 optional fields) — served, cached, ignored by v1 frontend logic. Served by `GET /api/shadow/summary?window=N` and `GET /api/shadow/diff` (read-only; consumed by the automation's v2 logs and the MACHINE view).

**Post-scan** (fire-and-forget, non-blocking):
1. Yahoo Finance metrics verification (compares RV30, spot against independent computation)
2. Yahoo Finance earnings verification (overrides FMP if >5-day discrepancy, backfills missing dates — this is why the manual earnings-refresh button was removed from the UI in 2026-07: the pipeline self-heals nightly)

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
    ├── RV Accel Status         5-tier label (Excellent / Good / Acceptable / Caution / Avoid·Wait) — display only
    └── θ/ν ratio               |theta / vega|
  → buildScoredData()          sort by score descending
  → DashboardTicker[]          → components
```

**Credit Put Spreads branch** (added 2026-05-12):

```
Naked-Puts scoring loop produces TickerResult[]
    │
    ▼
For each ticker in CPS_UNIVERSE = ["SPY","QQQ","IWM"]:
  ├── hydrate raw chain + spot + atr14 (captured during scan)
  ├── fetch_regime_overlay()  → VIX/VIX3M/VVIX (yfinance) — ONCE per scan
  ├── get_vrp_history(60d) + get_consecutive_sell_days() from SQLite
  └── spread_builder.build_candidate_outcome_for_ticker(...)
       │
       ├── universe filter (cheapest)
       ├── inherited base hard gates (DANGER / earnings / negative VRP / etc.)
       ├── construction: 30–45 DTE, 0.15–0.25 short delta, ATR-aware width
       ├── execution: bid_ask_ratio / OI / volume — per leg
       ├── credit_to_width gates (WATCH 0.20 / SELL 0.25)
       ├── overlay (DANGER blocks SELL; UNKNOWN does NOT block)
       └── 2-day ticker-level confirmation (SELL_CPS gate only)
    ▼
record_cps_candidate(...) → cps_candidate_history table
    │
    ▼
save_cps_scan_response(...) → cps_scan_responses cache row
    │
    ▼
GET /api/credit-put-spreads/latest → CreditPutSpreadsTab
```

Engineered guarantee: the CPS branch is wrapped in `try/except` inside `run_full_scan()`. Any failure (yfinance outage, builder bug, DB write error) is logged but **cannot** affect the Naked Puts response. See [`backend/main.py:_build_cps_response`](../../backend/main.py).

**Regime computation** (`RegimeBanner.tsx:computeRegime()`): runs on the transformed `DashboardTicker[]`, excludes SKIP and NO DATA tickers, produces the NBA-themed market regime. See [scoring-and-strategy.md § Dashboard-Level Market Regime](../1-domain/scoring-and-strategy.md#dashboard-level-market-regime).

**[HUMAN | MACHINE] view mode** (added 2026-07-14): a navbar toggle (`useViewMode`, `localStorage('oh-view')`, `?view=machine` URL override) swaps the entire dashboard body for the **MACHINE view** — a monospace, full-precision, verbatim render of everything the API returns, including all v2 shadow telemetry and the otherwise-unrendered `/api/shadow/*` endpoints, plus a `[COPY_ALL]` export. Anti-drift core in `lib/machine-format.ts`: one `MachineSection[]` descriptor feeds both the React renderer and the clipboard serializer, so screen and paste can never diverge; a `TICKERS.OTHER` catch-all guarantees future API fields are never silently dropped. Display-only by construction (P1) — it renders API fields verbatim, computes nothing, and imports nothing from `scoring.ts`. Tables >50 rows render collapsed behind `[+]`. HUMAN mode is byte-identical to the pre-toggle UI. There are deliberately **no mutation controls** anywhere: scan triggering belongs to the 18:30 ET cron and earnings dates self-heal nightly.

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
| RV Accel Status (5-tier display label) | **Frontend** | Display-only environment classifier; does not prescribe size |
| Dashboard market regime (NBA-themed) | **Frontend** | Independent classifier from aggregate ticker data |
| **Credit Put Spreads** — universe filter, construction, execution filters, overlay, confirmation, ranking | **Backend** | Reuses Base Edge Score from `scorer.py`; no separate scoring engine |
| **CPS persistence** — `cps_candidate_history` + `cps_scan_responses` tables | **Backend** | Supports 2-day confirmation lookups + API response cache |
| **CPS exit rules** — pin-risk, defensive, time, profit-target, event-risk | **Backend** | Pure function in `spread_exit_evaluator.py`; Journal will call it once trade entry ships |
| **Tab routing** (Naked Puts / CPS / Journal) | **Frontend** | `page.tsx` useState; Regime Banner stays above the TabBar |

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
| Yahoo Finance | Free (yfinance) | Bars, VIX close, earnings dates | Post-scan only (blocking I/O in executor) + one-time v2 backfill | Verification + earnings override; 10y multi-regime `daily_bars`/`index_daily` seed (`backfill_bars.py`) |

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
  ├── theta_core          (v2: verbatim golden-master port — CONFIG home (P3), 1e-9 oracle)
  ├── estimators          (v2: bars → daily variance inputs → EWMA replay; recompute-from-bars, no persisted state)
  ├── forecast            (v2: pooled-ridge ForecastEngine — sigma_fwd/sigma_fwd_dn + global factor)
  └── [runtime] utils.verify_metrics  (optional, sys.path hack for Docker)

calculator  → marketdata_client (DailyBar, OptionContract)
scorer      → calculator (VolSurface)
csv_store   → marketdata_client (OptionContract)
fmp_client  → database (get_cached_earnings, store_cached_earnings)
forecast    → theta_core, estimators, database
(one-time scripts: backfill_bars.py — yfinance 10y OHLC seed; backfill_v2.py — train + backfill v2 columns)
```

**Frontend** (component tree):

```
page.tsx  ── mode ternary: HUMAN (below) | MACHINE (machine/MachineView)
  ├── Navbar → ThemeToggle, ViewModeToggle, ExplainMetricsModal
  ├── RegimeBanner (exports computeRegime) → VrpActivityGrid
  ├── TabBar → Leaderboard → DetailPanel | CreditPutSpreadsTab | JournalComingSoon
  ├── RegimeGuideModal → RegimeSection
  └── machine/MachineView → MachineSectionView   (self-fetches health + shadow + CPS raw)

Hooks: useTheme (localStorage + DOM), useViewMode ('oh-view' + ?view=), useCssColors (getComputedStyle + MutationObserver)
Lib:   api.ts (fetch wrappers), scoring.ts (transform — FROZEN at Phase B, P1), types.ts,
       metrics-content.ts (explainer cards incl. the v2 · shadow section), machine-format.ts (MACHINE descriptors + serializer)
```
