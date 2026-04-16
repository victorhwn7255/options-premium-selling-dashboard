# Theta Harvest — Codebase Phase 3 Summary

> **Version:** v1.08 | **Date:** April 2026 | **Branch:** `v1.08`
> **Purpose:** Complete reference guide for team collaboration and future development.

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Architecture](#2-architecture)
3. [Backend Deep Dive](#3-backend-deep-dive)
4. [Scoring & Strategy](#4-scoring--strategy)
5. [Frontend Architecture](#5-frontend-architecture)
6. [Database Schema](#6-database-schema)
7. [API Reference](#7-api-reference)
8. [Data Pipeline](#8-data-pipeline)
9. [Configuration](#9-configuration)
10. [File Inventory](#10-file-inventory)
11. [Known Issues & Tech Debt](#11-known-issues--tech-debt)
12. [Development Guide](#12-development-guide)
13. [Changelog (Phase 2 → Phase 3)](#13-changelog-phase-2--phase-3)

---

## 1. Project Overview

**What it is:** A volatility premium scanner for options sellers. Scans 33 tickers daily after market close, computes volatility metrics, scores each on a 0–100 scale for premium selling edge, classifies market regimes, and presents actionable trade construction on a single-page dashboard.

**Core thesis:** Implied volatility systematically overestimates realized volatility. The gap (VRP) is the edge we harvest by selling options.

**Who it's for:** Options sellers looking for high-IV-percentile, positive-VRP tickers in contango with stable RV — the sweet spot for short premium strategies.

**Live at:** theta.thevixguy.com (via Cloudflare tunnel)

### Tech Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| Backend | Python, FastAPI, async/await, NumPy | 3.12, 0.115.6 |
| Frontend | Next.js (App Router), React, TypeScript, Tailwind CSS, Recharts | 14.2, 18.3, 5.4, 3.4, 2.12 |
| Database | SQLite with WAL mode | 3 |
| HTTP Client | httpx (async) with token-bucket rate limiting | 0.28.1 |
| Data Sources | MarketData.app (options/stocks), FMP (earnings), Yahoo Finance (verification) | Starter plan $12/mo |
| Deployment | Docker Compose (3 services: backend, frontend, cloudflared) | |
| Design System | "Anthropic Warm Humanist" — terracotta/sage/purple, dark/light mode | |

### Ticker Universe (33 tickers, 7+ sectors)

| Sector | Tickers |
|--------|---------|
| Index ETFs | SPY, QQQ, IWM, EEM |
| Sector ETFs | XLE, XLF, XLV, XLI, XLB, GLD, TLT |
| Tech | AAPL, MSFT, GOOG, META, NVDA, PLTR, UBER |
| Consumer | AMZN, TSLA, NFLX, WMT, MCD, KO, NKE, SBUX, HD |
| Financials | JPM, GS, HOOD |
| Energy | XOM |
| Healthcare | JNJ |
| Industrials | CAT |

---

## 2. Architecture

### Three-Service Stack

```
[MarketData.app API] ──→ [FastAPI Backend :8000] ──→ [SQLite WAL + CSVs]
[FMP API (earnings)]        ↕ /api/*                     ↕
[Yahoo Finance (verify)]  [Next.js Frontend :3000] ←── [API proxy via rewrites]
                            ↕
                        [Cloudflare Tunnel] ──→ theta.thevixguy.com
```

**Docker ports:** backend → host :8030, frontend → :3000. Frontend proxies `/api/*` to backend via Next.js rewrites in `next.config.js`.

### Data Flow

```
1. Cron fires at 6:30 PM ET (Mon-Fri, trading days only)
2. For each of 33 tickers (sequential, semaphore=1):
   a. Fetch stock snapshot (current price)
   b. Fetch 180 calendar days of daily bars
   c. Fetch options chain (2 API calls: narrow + wide)
   d. Fetch earnings date (FMP → cache → MarketData.app fallback)
   e. Extract ATM Greeks (theta, vega) + compute ATR14
   f. Get historical IVs from SQLite (for IV Rank/Percentile)
   g. build_vol_surface() → liquidity filter → ATM IV → IV rank → term structure → skew → VRP
   h. score_opportunity() → composite score + regime + recommendation + position construction
   i. Store daily_iv to SQLite, append to CSVs
3. Sort all results by score descending
4. Compute market-wide regime summary (avg VRP, avg term slope, danger/caution counts)
5. Persist full scan to scan_results table
6. Fire-and-forget: post-scan metrics verification against Yahoo Finance
7. Fire-and-forget: earnings verification against Yahoo Finance (override FMP if >5d discrepancy)
```

---

## 3. Backend Deep Dive

### Module Map

```
main.py (969 lines)
├── Ticker UNIVERSE dict (33 tickers)
├── FastAPI app + 12 API endpoints
├── Cron scheduler (6:30 PM ET, asyncio loop)
├── scan_single_ticker() — per-ticker orchestration
├── run_full_scan() — full universe scan
├── run_post_scan_verification() — Yahoo cross-check
├── _us_market_holidays() — pure datetime holiday calendar
├── _is_trading_day() — weekend + holiday check
└── _compute_deltas() — day-over-day comparison

calculator.py (638 lines)
├── filter_liquid_contracts() — reject illiquid options
├── compute_realized_vol() → RV10/20/30/60, acceleration
├── compute_atm_iv() → 30-day ATM IV (interpolated)
├── compute_iv_rank() → IV Rank + IV Percentile
├── compute_term_structure() → 8-tenor curve + slope
├── compute_skew() → 25Δ put skew
├── find_atm_greeks() → theta, vega
├── compute_atr14() → average true range
└── build_vol_surface() — main entry, orchestrates all

scorer.py (295 lines)
├── ScoringParams dataclass (thresholds)
├── ScoredOpportunity dataclass (full result)
└── score_opportunity() — 0-100 score + regime + recommendation

database.py (455 lines)
├── 7 SQLite tables (init_db)
├── daily_iv: store/get historical IV
├── scan_results: store/get/prune scan snapshots
├── earnings_cache: store/get/clear cached dates
├── verification_results: store/get verification reports
└── get_previous_day_scan() — for day-over-day comparison

marketdata_client.py (321 lines)
├── RateLimiter (token bucket, configurable calls/min)
├── OptionContract, DailyBar, StockSnapshot dataclasses
└── MarketDataClient
    ├── get_stock_snapshot()
    ├── get_daily_bars()
    ├── get_options_chain() — 2-call strategy (narrow + wide)
    └── get_earnings()

models.py (118 lines) — Pydantic v2 response models
fmp_client.py (59 lines) — FMP earnings with SQLite cache
csv_store.py (123 lines) — CSV persistence (daily metrics + quotes)
backfill.py (~400 lines) — Historical IV backfill with BSM solver
repair_rv.py (~180 lines) — Stock-split data repair
test_calculator.py — 5 unit tests
test_liquidity_filter.py — 6 unit tests
```

### Key Constants

| Constant | Value | Location | Purpose |
|----------|-------|----------|---------|
| Rate limit | 10 calls/min | main.py (lifespan) | MarketData.app API throttle |
| Scan concurrency | semaphore=1 | main.py (run_full_scan) | Sequential ticker processing |
| Cron time | 6:30 PM ET | main.py (_cron_loop) | Daily scan trigger |
| ATM range | ±3% of spot | calculator.py | Near-ATM strike filter |
| Max spread ratio | 50% | calculator.py | Liquidity filter threshold |
| Max IV | 200% | calculator.py | Garbage data ceiling |
| Min ATM contracts | 3 | calculator.py | Minimum for reliable IV |
| IV history lookback | 252 days | database.py | 1-year IV Rank calibration |
| Scan results retention | 50 rows | database.py | Pruning threshold |
| Earnings refresh limit | 1/day | main.py | FMP API conservation |
| Scan gate | 1/day, after 6:30 PM ET | main.py | Prevent redundant scans |
| CSV date timezone | America/New_York | main.py | ET-aware date for CSV persistence |

### Liquidity Filter Pipeline

```
Raw contracts from API
  ↓ reject: bid == 0
  ↓ reject: (ask - bid) / mid > 50%
  ↓ reject: IV > 200%
  ↓ reject: no bid/ask AND IV > 100%
  ↓ count ATM contracts (within 3% of spot, near 30 DTE)
  ↓ if < 3 liquid ATM contracts → iv_current = None → NO DATA
  ↓ else → compute ATM IV from filtered contracts
Filtered contracts used for term structure and skew
```

---

## 4. Scoring & Strategy

### Composite Score (0–100)

| Component | Max Pts | Formula | Purpose |
|-----------|---------|---------|---------|
| **VRP Quality** | 30 | `(IV/RV ratio - 1.15) × 66.67`, capped at 30. Dead zone below 1.15. | Is there premium edge? |
| **IV Percentile** | 25 | `(percentile - 30) × 0.357`. Floor at 30th pctl. | Are options expensive? |
| **Term Structure** | 20 | Piecewise: 0.85→20, 1.0→5, 1.15→0 | Is the structure favorable? |
| **RV Stability** | 15 | Piecewise: accel 0.85→15, 1.0→10, 1.15→0 | Is it safe? |
| **Skew** | 10 | Trapezoid: 0→0, 7→10, 12→10, 20→0 | Is there put demand to harvest? |

### Gates

| Gate | Condition | Effect | Location |
|------|-----------|--------|----------|
| Negative VRP | VRP < 0 | Caps score at 44 | Backend (scorer.py) |
| Earnings | DTE ≤ 14 days | Forces score to 0, action = SKIP | Frontend (scoring.ts) |
| No Data | IV = None | Score = 0, rec = NO DATA | Backend (scorer.py) |

### Per-Ticker Regime Detection

| Regime | Trigger | Recommendation Override |
|--------|---------|------------------------|
| DANGER | Term slope > 1.15 | → AVOID (always) |
| CAUTION | Term slope > 1.05, or IV Rank > 90 + RV Accel > 1.1 | Score ≥ 55 → REDUCE SIZE, else NO EDGE |
| NORMAL | Default | Score determines: ≥65 SELL, ≥45 CONDITIONAL, <45 NO EDGE |

### Market Regime (Dashboard-Level)

| Regime | Trigger | Posture |
|--------|---------|---------|
| OFF SEASON | >40% DANGER tickers | No trading |
| REGULAR SEASON | >25% stressed (DANGER+CAUTION) | Defined-risk only, reduced sizing |
| THE FINALS | Avg VRP >8 AND avg term slope <0.90 | Widest edge, be aggressive |
| THE PLAYOFFS | Default | Normal, execute playbook |

### Position Sizing (Frontend)

| RV Acceleration | Sizing |
|-----------------|--------|
| ≤ 1.10 | Full |
| 1.10–1.20 | Half |
| > 1.20 | Quarter |

### Position Construction (Backend)

| Condition | Delta | Structure | DTE | Notional |
|-----------|-------|-----------|-----|----------|
| DANGER | N/A | No position | N/A | 0% |
| CAUTION | 10–15Δ | Iron condor / wide put spread | 21–30 | 1–2% |
| IV Rank ≥ 80, VRP > 8 | 16–20Δ | Short strangle / jade lizard | 30–45 | 2–5% |
| IV Rank ≥ 80, VRP 4–8 | 16–20Δ | Iron condor / put credit spread | 30–45 | 2–5% |
| IV Rank ≥ 80, VRP ≤ 4 | 16–20Δ | Put credit spread | 30–45 | 2–5% |
| Default | 20–30Δ | Narrow put spread | 45–60 | 2–3% |

---

## 5. Frontend Architecture

### Single-Page Client App

All state lives in `page.tsx` via `useState`. No routing, no state management library.

```
page.tsx (root)
├── Navbar — scan controls, theme toggle, verification badges, modals
├── RegimeBanner — market regime + aggregate metrics
├── Leaderboard — sortable table with expandable detail rows
│   ├── VRPBar — horizontal progress bar per ticker
│   ├── ScorePill — colored score circle
│   ├── ActionChip — recommendation badge
│   ├── SizingChip — sizing indicator (Half/Quarter)
│   ├── DeltaChip — day-over-day change indicator
│   └── ExpandableDetail → DetailPanel
│       ├── Metrics grid (2×4)
│       ├── Position construction hints
│       ├── Flags / warnings
│       ├── IV vs RV chart (Recharts ComposedChart)
│       ├── Term Structure chart (Recharts AreaChart)
│       └── Day-over-Day comparison grid
├── RegimeGuideModal — educational: 4 regime deep-dives
└── ExplainMetricsModal — educational: 11 metric cards with formulas
```

### Component Props Flow

```
page.tsx
  apiData (ScanResponse) → buildScoredData() → DashboardTicker[]
    → RegimeBanner(data)
    → Leaderboard(data, selected, onSelect, selectedData, deltaMap)
        → DetailPanel(ticker, delta)
  deltaMap (Record<string, TickerDelta>) → fetched from /api/scan/comparison
  verification (VerificationResult) → Navbar badge
  earningsVerification (EarningsVerificationResult) → Navbar tooltip
```

### Frontend Scoring Pipeline (`scoring.ts`)

```
Backend TickerResult
  → mapRecommendation() — SELL PREMIUM→SELL, REDUCE SIZE→AVOID, etc.
  → Earnings gate — if DTE ≤ 14: score=0, action=SKIP, preGateScore preserved
  → Position sizing — RV accel > 1.20→Quarter, >1.10→Half, else→Full
  → θ/ν ratio — |theta/vega| for display
  → DashboardTicker (ready for rendering)
```

### Theme System

- Light/dark toggle via `data-theme` attribute on `<html>`
- CSS custom properties in `globals.css` (`:root` + `[data-theme="dark"]`)
- `useTheme` hook: localStorage persistence, system preference fallback
- `useCssColors` hook: reads CSS variables for Recharts (MutationObserver on theme change)
- Default theme: **dark**
- Inline `<script>` in layout.tsx prevents flash of wrong theme

### Design System

- **Colors:** terracotta primary (#C47B5A), sage secondary (#7D8C6E), dusty purple accent (#8B8FC7), warm neutrals
- **Warning color:** #E08A5E (light) / #D4A574 (dark)
- **Fonts:** General Sans (UI), Source Serif 4 (headings), JetBrains Mono (data)
- **Texture:** Risograph-style grain overlay via SVG noise filter
- **Dark mode:** Full dark theme via CSS custom properties

---

## 6. Database Schema

### SQLite Tables (7 total)

```sql
-- Historical IV for rank/percentile computation
daily_iv (
  ticker TEXT, date TEXT,
  atm_iv REAL, rv30 REAL, vrp REAL, term_slope REAL,
  PRIMARY KEY (ticker, date)
)

-- Scan run metadata
scan_log (
  id INTEGER PRIMARY KEY,
  timestamp TEXT, tickers_scanned INTEGER,
  duration_seconds REAL, errors TEXT (JSON)
)

-- Full scan result snapshots
scan_results (
  id INTEGER PRIMARY KEY,
  scanned_at TEXT, regime TEXT (JSON),
  tickers TEXT (JSON), historical TEXT (JSON)
)  -- Pruned to 50 rows

-- Cached earnings dates
earnings_cache (
  ticker TEXT PRIMARY KEY,
  earnings_date TEXT, fetched_at TEXT
)

-- Metrics verification (vs Yahoo Finance)
verification_results (
  id INTEGER PRIMARY KEY,
  scanned_at TEXT, verified_at TEXT,
  total_checks INTEGER, pass_count INTEGER,
  warn_count INTEGER, fail_count INTEGER,
  failures TEXT (JSON), warnings TEXT (JSON),
  full_report TEXT (JSON)
)  -- Pruned to 50 rows

-- Earnings verification (FMP vs Yahoo)
earnings_verification_results (
  id INTEGER PRIMARY KEY,
  scanned_at TEXT, verified_at TEXT,
  total_checks INTEGER, pass_count INTEGER,
  fail_count INTEGER, skip_count INTEGER,
  checks TEXT (JSON)
)  -- Pruned to 50 rows
```

### CSV Files

| Path | Content | Format |
|------|---------|--------|
| `data/daily/{TICKER}.csv` | Daily spot, ATM IV, RV30, VRP, term slope | Date-descending, one row per trading day |
| `data/quotes/{TICKER}.csv` | Full option quotes per scan | Date-appended, all contracts per day |

---

## 7. API Reference

| Method | Path | Description | Rate Limit |
|--------|------|-------------|------------|
| GET | `/api/health` | System status (DB, API connection, data count) | None |
| GET | `/api/scan/latest` | Most recent cached scan result | None |
| POST | `/api/scan` | Trigger scan (trading day, after 6:30 PM ET, once/day) | 1/day |
| GET | `/api/scan/status` | Poll scan progress (status, current/total, ticker) | None |
| GET | `/api/scan/history?limit=10` | Scan metadata for recent scans | None |
| GET | `/api/scan/comparison` | Day-over-day deltas for all tickers | None |
| GET | `/api/ticker/{ticker}/history?days=120` | Historical IV/RV/VRP/term_slope series | None |
| GET | `/api/universe` | Configured ticker universe | None |
| GET | `/api/earnings/remaining` | Earnings refresh count remaining today | None |
| POST | `/api/earnings/refresh` | Clear cache + re-fetch from FMP | 1/day |
| GET | `/api/verify/latest` | Latest metrics verification result | None |
| GET | `/api/verify/earnings/latest` | Latest earnings verification result | None |

### Response Models

- `ScanResponse`: timestamp, regime (RegimeSummary), tickers (TickerResult[]), historical, scanned_at, cached, message
- `TickerResult`: 30+ fields — all metrics, score, regime, recommendation, position construction, term structure points, skew points
- `ComparisonResponse`: current_scanned_at, previous_scanned_at, tickers (TickerComparison[] with deltas)
- `HealthResponse`: status, marketdata_connected, db_initialized, tickers_configured, historical_data_points

---

## 8. Data Pipeline

### Scan Timing & Gates

- **Cron:** 6:30 PM ET, Mon-Fri (trading days only, skips US market holidays)
- **Manual trigger:** POST `/api/scan` — gated to once per day (ET timezone), only after 6:30 PM ET, only on trading days
- **Background execution:** Scan runs as asyncio task, progress pollable via `/api/scan/status`
- **Retry:** Cron retries once after 5 minutes on failure

### Post-Scan Verification

After each scan, two verification tasks fire (non-blocking):

1. **Metrics verification** (`verify_metrics.py`):
   - Fetches Yahoo Finance bars for all scanned tickers
   - Compares RV30, spot price against independent computation
   - Stores pass/warn/fail counts in `verification_results`

2. **Earnings verification**:
   - Fetches Yahoo Finance earnings dates for non-ETF tickers
   - Compares against FMP dates
   - If Yahoo provides a date and FMP is missing → backfills from Yahoo
   - If FMP and Yahoo disagree by >5 days → overrides with Yahoo

### Earnings Date Pipeline

```
FMP API ──→ earnings_cache (SQLite)
  ↓ (if missing)
MarketData.app earnings ──→ fallback
  ↓ (post-scan)
Yahoo Finance ──→ verification
  ↓ (if >5d diff or FMP missing)
Override in scan_results + earnings_cache
```

### Historical IV Backfill

For IV Rank/Percentile to be meaningful, the system needs ~252 trading days of history. The `backfill.py` script populates this:

```
backfill.py --days 252 --verbose
  1. Fetch daily bars (adjusted) for all tickers
  2. For each trading day:
     a. Fetch historical options chain metadata
     b. Pick ~12 ATM contract symbols
     c. Fetch historical quotes (bid/ask)
     d. Compute IV via BSM bisection solver
     e. Compute RV30, term slope from bars
     f. Store to daily_iv + daily CSV
```

---

## 9. Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `MARKETDATA_TOKEN` | Yes | Bearer token for MarketData.app API |
| `FMP_API_KEY` | No | API key for Financial Modeling Prep (earnings) |
| `CLOUDFLARE_TUNNEL_TOKEN` | No | Cloudflare tunnel token for public access |
| `CORS_ORIGINS` | No | Extra CORS origins, comma-separated |
| `RISK_FREE_RATE` | No | For BSM IV solver in backfill (default 0.043) |

### Docker Compose

```yaml
services:
  backend:    # port 8030:8000, bind mount ./backend/data + ./utils
  frontend:   # port 3000:3000, build arg BACKEND_URL=http://backend:8000
  cloudflared: # Cloudflare tunnel, depends_on frontend
```

### Key Config Locations

| Setting | Location | Value |
|---------|----------|-------|
| Ticker universe | `backend/main.py` UNIVERSE dict | 33 tickers |
| Scoring thresholds | `backend/scorer.py` ScoringParams | min_iv_rank=60, min_vrp=3.0, etc. |
| CORS origins | `backend/main.py` | localhost:3000/8000/8030, 127.0.0.1:3000, + CORS_ORIGINS env |
| API proxy | `frontend/next.config.js` | `/api/*` → BACKEND_URL |
| Default theme | `frontend/src/hooks/useTheme.ts` | dark |

---

## 10. File Inventory

### Backend (10 source files + 2 test files)

| File | Lines | Purpose |
|------|-------|---------|
| `main.py` | ~969 | FastAPI app, endpoints, cron, scan orchestration |
| `calculator.py` | ~638 | Pure vol computation functions |
| `scorer.py` | ~295 | Scoring engine, regime detection |
| `database.py` | ~455 | SQLite operations (7 tables) |
| `marketdata_client.py` | ~321 | Async API client with rate limiting |
| `models.py` | ~118 | Pydantic v2 response models |
| `fmp_client.py` | ~59 | FMP earnings client with caching |
| `csv_store.py` | ~123 | CSV persistence (daily + quotes) |
| `backfill.py` | ~400 | Historical IV backfill with BSM solver |
| `repair_rv.py` | ~180 | Stock-split data repair |
| `test_calculator.py` | ~212 | 5 unit tests for vol computations |
| `test_liquidity_filter.py` | ~166 | 6 tests for liquidity filter |

### Frontend (16 source files)

| File | Lines | Purpose |
|------|-------|---------|
| `src/app/page.tsx` | ~232 | Root page, all state management |
| `src/app/layout.tsx` | ~30 | Root layout, fonts, theme script |
| `src/app/globals.css` | ~357 | CSS variables, design system, textures |
| `src/components/Navbar.tsx` | ~463 | Nav bar, controls, tooltips |
| `src/components/Leaderboard.tsx` | ~483 | Data table, mobile cards, sub-components |
| `src/components/DetailPanel.tsx` | ~499 | Detail view, charts, metrics grid |
| `src/components/RegimeBanner.tsx` | ~130 | Market regime banner |
| `src/components/ExplainMetricsModal.tsx` | ~182 | Educational metrics modal |
| `src/components/RegimeGuideModal.tsx` | ~349 | Regime guide modal |
| `src/components/RegimeSection.tsx` | ~167 | Regime card component |
| `src/components/ThemeToggle.tsx` | ~42 | Theme toggle button |
| `src/hooks/useTheme.ts` | ~55 | Theme management hook |
| `src/hooks/useCssColors.ts` | ~99 | CSS variable reader for Recharts |
| `src/lib/api.ts` | ~95 | API client (fetch wrappers) |
| `src/lib/types.ts` | ~201 | TypeScript interfaces |
| `src/lib/scoring.ts` | ~85 | Frontend scoring (earnings gate, sizing) |
| `src/lib/metrics-content.ts` | ~280 | Metric definitions for educational modal |
| `src/lib/simulated-data.ts` | ~115 | Fallback simulated data (unused) |

### Configuration Files

| File | Purpose |
|------|---------|
| `docker-compose.yml` | 3-service stack definition |
| `.env` | Environment variables (gitignored) |
| `CLAUDE.md` | AI assistant instructions |
| `README.md` | Project documentation |
| `frontend/tailwind.config.js` | Tailwind theme configuration |
| `frontend/next.config.js` | Next.js config (API proxy) |
| `frontend/tsconfig.json` | TypeScript configuration |
| `frontend/package.json` | Frontend dependencies |
| `backend/requirements.txt` | Python dependencies |
| `backend/Dockerfile` | Backend container image |
| `frontend/Dockerfile` | Frontend container image |

### Reference Documents

| File | Purpose |
|------|---------|
| `references/strategy.md` | Complete premium selling strategy documentation |
| `references/metrics_report.md` | Metrics & scoring reference (formulas, thresholds) |
| `references/checkpoints/codebase_phase_1_summary.md` | Phase 1 codebase snapshot |
| `references/checkpoints/codebase_phase_2_summary.md` | Phase 2 codebase snapshot |
| `references/checkpoints/codebase_phase_3_summary.md` | This document |
| `tasks/lessons.md` | Lessons learned from debugging sessions |
| `tasks/todo.md` | Task tracking |

### Approximate Code Stats

| Category | Files | Lines |
|----------|-------|-------|
| Backend Python | 12 | ~3,900 |
| Frontend TS/TSX | 18 | ~3,600 |
| CSS | 1 | ~360 |
| Config (JS/JSON/YAML) | 6 | ~350 |
| **Total** | **37** | **~8,200** |

---

## 11. Known Issues & Tech Debt

### Data Quality
- **Skew computation gaps:** 5+ tickers regularly show `skew_25d = 0.0` due to insufficient liquid 25Δ puts. Understates scores by up to 10 points.
- **RV10 sensitivity:** 10-day window is noisy. Single outlier close can shift RV acceleration by 0.1-0.2, crossing sizing thresholds.
- **EEM garbage IV:** Historical anomaly (289.88% IV) exists in both SQLite and CSV on different dates (3/17 and 3/18). Harmless now but not cleaned up.

### Architecture
- **ActionChip/SizingChip duplicated** in Leaderboard.tsx and DetailPanel.tsx. Should be shared components.
- **simulated-data.ts** is unused dead code. Can be deleted.
- **In-memory earnings refresh counter** resets on container restart. Should persist to SQLite.
- **CSV append_daily_csv** rewrites the entire file on each insert. Race condition possible with concurrent reads.
- **Silent API error handling** on frontend — no user-facing error states for failed API calls.

### Scoring
- **IV Rank computed but not used in scoring.** Only IV Percentile contributes to the score. IV Rank is used only for regime detection and position construction.
- **Methodology footer** in page.tsx shows outdated scoring formula text (doesn't match backend).

### Operations
- **Rate limit set to 10 calls/min** but API supports 50. Scans take ~13 minutes. Could be ~3 minutes at 50/min.
- **No CI/CD pipeline.** Only 11 manual tests (5 in test_calculator.py, 6 in test_liquidity_filter.py).
- **Holiday calendar duplicated** in backend (main.py) and frontend (Navbar.tsx). Should be a shared source.
- **.env committed to git** in earlier versions with real API keys. Gitignored now but history contains them.

---

## 12. Development Guide

### Local Development

```bash
# Backend
cd backend
pip install -r requirements.txt
export MARKETDATA_TOKEN=your_token
export FMP_API_KEY=your_key  # optional
python main.py  # starts on :8000

# Frontend
cd frontend
npm install
npm run dev  # starts on :3000, proxies /api/* to :8030
```

### Docker (Production)

```bash
# Start
docker compose up --build -d

# Rebuild after code changes
docker compose down && docker compose up --build -d

# View logs
docker logs options-premium-selling-dashboard-backend-1 -f

# Check health
curl http://localhost:8030/api/health
```

### Backfill Historical Data

```bash
cd backend
export MARKETDATA_TOKEN=your_token
python backfill.py --days 252 --verbose  # full year
python backfill.py --days 1              # fill yesterday
python backfill.py --days 5 --tickers SPY --dry-run  # preview
```

### Repair Stock Split Data

```bash
cd backend
export MARKETDATA_TOKEN=your_token
python repair_rv.py --tickers NFLX --dry-run  # preview
python repair_rv.py --all                      # fix all
```

### Running Tests

```bash
cd backend
python test_calculator.py       # 5 tests
python test_liquidity_filter.py # 6 tests (requires pytest)
```

### Key Development Patterns

1. **Backend scoring is authoritative.** Frontend passes through backend scores. Never compute scores on the frontend.
2. **ET timezone for all trading dates.** Use `datetime.now(tz=ZoneInfo("America/New_York"))` for any date that represents a trading day.
3. **CSS variables for theming.** All colors go through CSS custom properties. Components use Tailwind utility classes that reference variables.
4. **Earnings gate is frontend-only.** Backend doesn't know about the 14-day gate. Frontend applies it in `scoring.ts`.
5. **Plan before implementing.** CLAUDE.md requires plan mode for any task with 3+ steps.

---

## 13. Changelog (Phase 2 → Phase 3)

### v1.07 → v1.08+ Changes (this session)

**New Features:**
- Day-over-day comparison API (`/api/scan/comparison`) with deltas for score, IV, VRP, term slope, RV accel, skew, regime
- Delta chips in leaderboard table (VRP, term slope, score columns)
- Full day-over-day comparison grid in detail panel (moved below charts)
- Regime change labels ("was CAUTION") in leaderboard rows

**Bug Fixes:**
- CSV persistence date bug: `bars[-1].date` → `datetime.now(tz=ET).date().isoformat()`. CSVs were using stale bar dates, causing silent write skips.
- Options chain skew fix: wide chain now passes exact expiration date (`expiration=YYYY-MM-DD`) instead of DTE number, preventing API misalignment that caused 19/33 tickers to have zero skew.
- Earnings date corrections: 8 tickers had FMP dates off by 5-14 days. Manually corrected in SQLite cache.

**Documentation:**
- Scoring formula in "Explain Metrics" modal corrected to match backend (was showing old frontend formula).
- README scoring thresholds reference updated to point to `backend/scorer.py`.
- `references/metrics_report.md` fully rewritten to match actual code implementation.
- `references/strategy.md` created — complete premium selling strategy documentation.

**UI Changes:**
- Default theme changed to dark
- Warning color updated from yellowish #C49A5A to warm orange #E08A5E (light) / #D4A574 (dark)
- Regime banner redesigned: metrics inline with regime name, description in bottom strip, left border accent removed
- Day-over-day section repositioned below charts in detail panel
- "Metric" column header removed from day-over-day grid

**Data:**
- 2026-03-23 gap backfilled (all 33 tickers)
- XLV 2026-03-20 daily CSV gap patched
- 278+ days of historical IV data per ticker (backfill completed)
