# Option Harvest — Codebase Summary

> A volatility premium scanner for options sellers. Identifies high-probability premium-selling opportunities using IV rank, volatility risk premium (VRP), term structure analysis, and regime detection.

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Architecture](#2-architecture)
3. [Backend Deep Dive](#3-backend-deep-dive)
4. [Key Metrics & Formulas](#4-key-metrics--formulas)
5. [Scoring System](#5-scoring-system)
6. [Regime Detection](#6-regime-detection)
7. [Frontend Architecture](#7-frontend-architecture)
8. [Database Schema](#8-database-schema)
9. [API Reference](#9-api-reference)
10. [Configuration](#10-configuration)
11. [Development Guide](#11-development-guide)

---

## 1. Project Overview

**Who it's for:** Options sellers looking for high-IV-rank, positive-VRP tickers in contango — the "sweet spot" for short premium strategies.

**What it does:**
- Scans 15 tickers across 6 sectors every day at 4:30 PM ET
- Computes realized vol, implied vol, VRP, term structure, skew, and ATR for each
- Scores each opportunity 0–100 and classifies the vol regime (NORMAL / CAUTION / DANGER)
- Provides position construction hints (delta, structure, DTE, sizing)
- Persists historical IV/RV data for trend analysis and charting

**Tech Stack:**

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.12, FastAPI, async/await, NumPy |
| Frontend | Next.js 14 (App Router), React 18, TypeScript, Tailwind CSS, Recharts |
| Database | SQLite with WAL mode (no external DB) |
| HTTP Client | httpx (async) with token-bucket rate limiting |
| Data Source | [MarketData.app](https://api.marketdata.app) API |
| Deployment | Docker Compose (two services) |
| Design System | "Anthropic Warm Humanist" — terracotta/sage/purple palette, risograph grain texture |

---

## 2. Architecture

### Two-Service Stack

```
┌─────────────────────┐      ┌─────────────────────┐
│   Next.js Frontend  │      │   FastAPI Backend    │
│   (port 3000)       │─────▶│   (port 8000/8030)  │
│                     │ /api │                     │
│  • Dashboard UI     │proxy │  • Scan engine       │
│  • Client scoring   │      │  • MarketData client │
│  • Theme system     │      │  • SQLite storage    │
│  • Recharts viz     │      │  • Cron scheduler    │
└─────────────────────┘      └─────────────────────┘
                                      │
                                      ▼
                             ┌─────────────────┐
                             │  MarketData.app  │
                             │  REST API        │
                             └─────────────────┘
```

### Data Flow (Scan)

```
Cron (4:30 PM ET) or Manual POST /api/scan
  │
  ▼
For each ticker (semaphore=2):
  ├─ get_stock_snapshot()    → current price
  ├─ get_daily_bars(180d)    → OHLCV history
  ├─ get_options_chain()     → all strikes/expirations
  ├─ get_earnings()          → next earnings date
  └─ get_historical_ivs()    → 252-day IV from SQLite
        │
        ▼
  calculator.build_vol_surface()
  ├─ compute_realized_vol()      → RV10/20/30/60
  ├─ compute_atm_iv()            → 30-day ATM IV
  ├─ compute_iv_rank()           → IV rank + percentile
  ├─ compute_term_structure()    → 8-tenor curve
  ├─ compute_skew()              → 25Δ put skew
  ├─ compute_atr14()             → ATR-14
  └─ find_atm_greeks()           → theta, vega
        │
        ▼
  scorer.score_opportunity()
  ├─ Composite score (0-100)
  ├─ Regime detection
  ├─ Recommendation
  └─ Position construction hints
        │
        ▼
  Store to SQLite (daily_iv + scan_results)
  Return ScanResponse to frontend
```

---

## 3. Backend Deep Dive

### Module Map

```
backend/
├── main.py                 # FastAPI app, endpoints, UNIVERSE, cron, scan orchestration
├── marketdata_client.py    # Async HTTP client for MarketData.app API
├── calculator.py           # Pure functions: all volatility metrics
├── scorer.py               # Composite scoring, regime detection, recommendations
├── database.py             # SQLite schema, CRUD operations
├── models.py               # Pydantic v2 response models
├── backfill.py             # Historical IV backfill script (CLI)
├── test_calculator.py      # Unit tests
├── requirements.txt        # Python dependencies
├── Dockerfile              # Container build
└── data/
    └── vol_history.db      # SQLite database (auto-created)
```

### main.py — Application Core

**UNIVERSE** — 15 tickers across 6 sectors:

| Ticker | Name | Sector |
|--------|------|--------|
| SPY | S&P 500 ETF | Index |
| QQQ | Nasdaq 100 ETF | Index |
| GLD | SPDR Gold Trust | Commodities |
| XLE | Energy Select SPDR | Sector ETF |
| XLF | Financial Select SPDR | Sector ETF |
| TLT | 20+ Year Treasury ETF | Fixed Income |
| NVDA | NVIDIA | Tech |
| PLTR | Palantir | Tech |
| HOOD | Robinhood Markets | Financials |
| AAPL | Apple | Tech |
| GS | Goldman Sachs | Financials |
| JPM | JPMorgan Chase | Financials |
| TSLA | Tesla | Consumer |
| META | Meta Platforms | Tech |
| AMZN | Amazon | Consumer |

**Scan orchestration:**
- `asyncio.Semaphore(2)` limits concurrent ticker scans
- `asyncio.gather()` with `return_exceptions=True` for fault tolerance
- Individual ticker failures logged, don't abort the scan
- Results sorted by `signal_score` descending
- Stored to SQLite via `store_scan_result()` (auto-prunes to last 50)

**Cron scheduler:**
- Runs at 4:30 PM ET, Monday–Friday
- Simple asyncio sleep loop (no external scheduler library)
- On failure: retries once after 5 minutes

**RegimeSummary computation** (in `run_full_scan()`):
- Averages IV rank and RV acceleration across all scanned tickers
- Counts DANGER and CAUTION regime tickers
- Uses SPY's term slope as `vix_term_slope` proxy
- Overall regime: DANGER if danger ≥ 2, ELEVATED RISK if VIX backwardation, OPPORTUNITY if avg IV rank > 80, else NORMAL

### marketdata_client.py — API Client

**Base URL:** `https://api.marketdata.app`

**Rate limiting:** Token bucket at 15 calls/min (configurable), 30s timeout per request.

**Retry logic:** Up to 5 retries with exponential backoff. Short-circuits on 402 (premium required) and 403 (forbidden).

**Columnar response format:** MarketData.app returns arrays indexed by position (e.g., `data["c"]` = close array, `data["iv"]` = IV array). The client unpacks these into dataclass instances.

**Data classes:**

| Class | Fields |
|-------|--------|
| `StockSnapshot` | price, change, change_pct, volume, prev_close |
| `DailyBar` | date, open, high, low, close, volume |
| `OptionContract` | ticker, strike, expiration, contract_type, implied_volatility, delta, gamma, theta, vega, open_interest, volume, last, bid, ask |

**Endpoints called:**

| Method | MarketData.app Endpoint | Purpose |
|--------|------------------------|---------|
| `get_stock_snapshot()` | `/v1/stocks/quotes/{ticker}/` | Current price |
| `get_daily_bars()` | `/v1/stocks/candles/D/{ticker}/` | 180-day OHLCV |
| `get_options_chain()` | `/v1/options/chain/{underlying}/` | Full options chain |
| `get_earnings()` | `/v1/stocks/earnings/{ticker}/` | Next earnings date |

### backfill.py — Historical IV Backfill

CLI tool for populating SQLite with historical ATM IV (up to 252 trading days).

**Key features:**
- Black-Scholes IV solver via bisection (100 iterations, $0.001 convergence)
- Risk-free rate: 4.3%
- Two-step interpolation: strike bracketing + expiry interpolation to 30-day tenor
- `--resume` flag skips dates already in database
- API credit tracking via `x-api-ratelimit-remaining` header
- Outputs CSV files to `data/quotes/` and `data/daily/`

**Usage:**
```bash
python backfill.py --days 252 --verbose
python backfill.py --days 5 --tickers SPY --dry-run
python backfill.py --resume --verbose
```

---

## 4. Key Metrics & Formulas

### Realized Volatility (RV)

**File:** `calculator.py:82-111`

```
log_returns = ln(close[i] / close[i-1])
RV_N = std(last N log_returns, ddof=1) × √252 × 100
```

| Window | Min Bars Required | Fallback |
|--------|-------------------|----------|
| RV10 | 11 | — |
| RV20 | 21 | = RV10 |
| RV30 | 31 | = RV20 |
| RV60 | 61 | = RV30 |

**RV Acceleration:**
```
rv_acceleration = RV10 / RV30
```
- `> 1.0` = rising vol (short-term > long-term)
- `< 1.0` = declining vol

### ATM Implied Volatility

**File:** `calculator.py:115-195`

1. Group options by expiration, calculate DTE
2. Find two expirations closest to 30 DTE
3. For each expiration, find contracts within 3% of spot price
4. Average call + put IV at nearest-to-ATM strike
5. Linear interpolate between expirations to exact 30-day point
6. Clamp interpolation weight to [0, 1]

**Output:** Percentage (e.g., 22.5 = 22.5%)

### IV Rank & Percentile

**File:** `calculator.py:265-289`

```
IV Rank = (current − min) / (max − min) × 100
IV Percentile = (# days where IV < current) / total_days × 100
```

- Lookback: 252 trading days (1 year)
- Minimum history: 20 data points (returns 50/50 if less)
- Flat period (range < 0.1): returns 50
- Both clamped to [0, 100], rounded to 1 decimal

### Volatility Risk Premium (VRP)

**File:** `calculator.py:506-546`

```
VRP = IV_current − RV30
VRP Ratio = IV_current / RV30
```

- Positive VRP = IV overpricing realized movement (premium seller's edge)
- VRP Ratio > 1.0 = favorable for selling

### Term Structure

**File:** `calculator.py:293-379`

**8 target tenors:** 1W (7d), 2W (14d), 1M (30d), 2M (60d), 3M (90d), 4M (120d), 6M (180d), 1Y (365d)

**Process:**
1. For each expiration, compute ATM IV via strike-bracketing interpolation
2. Collect (DTE, IV) pairs sorted by DTE
3. Use `np.interp()` to interpolate to each target tenor

**Slope:**
```
slope = front_iv / back_iv
```
- `< 1.0` = **contango** (normal, front month cheaper — favorable for premium sellers)
- `> 1.0` = **backwardation** (front month expensive — fear/event pricing)

### 25-Delta Skew

**File:** `calculator.py:383-502`

```
skew_25d = IV(25Δ put) − IV(ATM)
```

- Target expiration: nearest to 30 DTE
- Put range: −0.9 < delta < −0.05
- Call range: 0.05 < delta < 0.9
- Slope via `np.polyfit(deltas, ivs, 1)` (linear regression)
- Higher skew = more demand for downside protection

### ATR-14 (Average True Range)

**File:** `calculator.py:249-261`

```
True Range = max(high − low, |high − prev_close|, |low − prev_close|)
ATR14 = mean(last 14 true ranges)
```

Minimum 15 bars required. Measures average daily price range.

### ATM Greeks

**File:** `calculator.py:199-245`

Returns theta (daily decay) and vega (sensitivity to 1% IV change) from the ATM option at nearest-to-30-DTE expiration.

---

## 5. Scoring System

### Backend Scoring (scorer.py)

**File:** `scorer.py:64-239`

**Total possible range:** 0–100 (clamped)

#### Component Breakdown

| Component | Points | Formula |
|-----------|--------|---------|
| **VRP Score** | 0–25 | `min(25, max(0, (vrp_ratio − 1.0) × 30))` |
| **IV Rank Score** | 0–25 | `min(25, iv_rank × 0.3)` |
| **Term Structure** | −5 to +18 | See table below |
| **RV Acceleration** | −15 to 0 | See table below |
| **Skew Assessment** | 3–8 | See table below |
| **Regime Penalty** | −35 to 0 | Deep backwardation = −35, mild = −20 |

**Term Structure scoring:**

| Slope | Points | Meaning |
|-------|--------|---------|
| < 0.85 | +18 | Strong contango |
| 0.85–0.95 | +12 | Mild contango |
| 0.95–1.0 | +6 | Slight contango |
| ≥ 1.0 | −5 | Backwardation |

**RV Acceleration penalties:**

| RV Accel | Points |
|----------|--------|
| > 1.15 | −15 |
| 1.05–1.15 | −8 |
| ≤ 1.05 | 0 |

**Skew scoring:**

| 25Δ Skew | Points |
|----------|--------|
| > 10 | 5 |
| 7–10 | 8 |
| 4–7 | 6 |
| ≤ 4 | 3 |

**VRP penalties (additional):**
- VRP < 0: −10 points + flag "Negative VRP — no premium edge"
- VRP < min_vrp (default 3.0): −10 points + flag "VRP below minimum threshold"

**IV Rank penalty:**
- IV Rank < min_iv_rank (default 60): −10 points

#### Recommendation Logic

| Condition | Recommendation |
|-----------|---------------|
| Score ≥ 70 AND regime = NORMAL | **SELL PREMIUM** |
| Score ≥ 55 AND regime = NORMAL | **CONDITIONAL** |
| Regime = DANGER | **AVOID** |
| Regime = CAUTION | **REDUCE SIZE** |
| Otherwise | **NO EDGE** |

#### Position Construction Hints

| Regime / IV Rank | Delta | Structure | DTE | Sizing |
|-----------------|-------|-----------|-----|--------|
| DANGER | N/A | No position | N/A | 0% |
| CAUTION | 10–15Δ | Iron condor / wide put spread | 21–30 | 1–2% |
| IV Rank ≥ 80, VRP > 8 | 16–20Δ | Short strangle / jade lizard | 30–45 | 2–5% |
| IV Rank ≥ 80, VRP > 4 | 16–20Δ | Iron condor / put credit spread | 30–45 | 2–5% |
| IV Rank ≥ 80, VRP ≤ 4 | 16–20Δ | Put credit spread (strict width) | 30–45 | 2–5% |
| IV Rank < 80 | 20–30Δ | Put credit spread, narrow width | 45–60 | 2–3% |

### Frontend Scoring (scoring.ts)

**File:** `frontend/src/lib/scoring.ts`

The frontend reproduces the scoring formula client-side via `computeScore()`:

| Component | Points | Formula |
|-----------|--------|---------|
| **Earnings Gate** | — | If earnings ≤ 14d: score=0, action=SKIP |
| **VRP Magnitude** | 0–40 | `min(40, vrp × 2.5)` |
| **Term Structure** | 5–25 | slope < 0.85 → 25, 0.85–0.90 → 18, 0.90–0.95 → 12, ≥ 0.95 → 5 |
| **IV Percentile** | 3–20 | ≥ 80 → 20, 60–80 → 14, 40–60 → 8, < 40 → 3 |
| **RV Accel Penalty** | −15 to 0 | > 1.15 → −15, 1.05–1.15 → −6, ≤ 1.05 → 0 |

**Action mapping:** ≥ 70 = SELL, ≥ 50 = CONDITIONAL, > 0 = NO EDGE

**Sizing logic:**
```
rvAccel > 1.20 → 'Quarter'
rvAccel > 1.10 → 'Half'
otherwise     → 'Full'
```

> Note: The frontend formula differs slightly from the backend (different weights, VRP uses absolute not ratio, includes earnings gate). The frontend version is used for display; the backend version is the source of truth for `signal_score`.

---

## 6. Regime Detection

### Backend Regime (scorer.py)

Per-ticker regime, based on term structure slope:

| Condition | Regime | Score Penalty |
|-----------|--------|--------------|
| term_slope > 1.05 | **DANGER** | −35 |
| 1.0 < term_slope ≤ 1.05 | **CAUTION** | −20 |
| iv_rank > 90 AND rv_accel > 1.1 | **CAUTION** (upgrade) | (included above) |
| Otherwise | **NORMAL** | 0 |

### Backend Overall Regime (main.py — RegimeSummary)

Aggregated across all tickers:

| Condition | Overall Regime | Color |
|-----------|---------------|-------|
| danger_count ≥ 2 OR vix_term_slope > 1.05 | **ELEVATED RISK** | error (red) |
| avg_iv_rank > 80 | **OPPORTUNITY** | accent (purple) |
| Otherwise | **NORMAL** | secondary (sage) |

### Frontend Regime (RegimeBanner.tsx)

Client-side computation from displayed data:

| Condition | Regime | Color | Message |
|-----------|--------|-------|---------|
| backwardation ≥ 3 OR avgTermSlope > 1.02 | **HOSTILE** | Error (red) | "Multiple tickers in backwardation — no premium selling today" |
| avgRVAccel > 1.12 OR backwardation ≥ 1 | **CAUTION** | Warning (yellow) | "Realized vol accelerating — reduce sizing, defined risk only" |
| avgVRP > 8 AND avgTermSlope < 0.90 | **FAVORABLE** | Secondary (sage) | "Wide VRP spread in contango — strong premium selling environment" |
| Otherwise | **NORMAL** | Secondary (sage) | "Contango, moderate VRP — standard conditions" |

**Displayed metrics:** Avg VRP, Avg Term Slope, RV Accel, Tradeable count

---

## 7. Frontend Architecture

### Directory Structure

```
frontend/src/
├── app/
│   ├── page.tsx              # Main dashboard (client component, all state)
│   ├── layout.tsx            # Root layout, fonts, metadata, theme flash prevention
│   └── globals.css           # CSS custom properties, color-mix utilities, grain
├── components/
│   ├── Navbar.tsx            # Top bar: logo, refresh, date, theme toggle
│   ├── RegimeBanner.tsx      # Market regime indicator with metrics
│   ├── Leaderboard.tsx       # Main data table (sortable, selectable rows)
│   ├── DetailPanel.tsx       # Trade construction panel with charts
│   └── ThemeToggle.tsx       # Light/dark mode button
├── hooks/
│   ├── useTheme.ts           # Theme state + localStorage + system preference
│   └── useCssColors.ts       # Resolves CSS vars → hex for Recharts SVGs
└── lib/
    ├── api.ts                # Fetch wrapper for backend API
    ├── types.ts              # TypeScript interfaces + DEFAULT_FILTERS
    ├── scoring.ts            # Client-side scoring reproduction
    └── simulated-data.ts     # Deterministic test data (seeded PRNG)
```

### State Management

No state library — everything is `useState` in `page.tsx`:

- `scanData: ScanResponse | null` — raw API response
- `selected: string | null` — currently selected ticker symbol
- `refreshing: boolean` — scan in progress
- `theme: Theme` — from `useTheme()` hook

Data flow: API → `buildScoredData(scanData)` → `DashboardTicker[]` → components

### Key Components

**Leaderboard.tsx** — Main table with:
- VRP bar visualization (colored by magnitude)
- Score pill (green/yellow/gray/red)
- Action chip (SELL PREMIUM / CONDITIONAL / NO EDGE / SKIP)
- Sizing chip (Full/Half/Quarter)
- Click to select → populates DetailPanel
- Responsive: hides columns on mobile/tablet

**DetailPanel.tsx** — Selected ticker details:
- 2×4 metrics grid (VRP, Term Slope, RV Accel, IV Percentile, Skew, θ/ν, ATR14, Earnings)
- Position construction hints (delta, structure, DTE, sizing)
- Flags display (warning badges)
- Two charts: IV vs RV 120-day history, Term Structure curve

**RegimeBanner.tsx** — Market regime indicator:
- Left-border colored by regime severity
- Regime name in large serif font
- Four metric indicators with good/bad thresholds
- Red alert overlay in HOSTILE mode

### Theming

**Dark mode:** `data-theme="dark"` attribute on `<html>`

**Flash prevention:** Inline `<script>` in `layout.tsx` reads `localStorage('oh-theme')` or system preference before React hydrates, preventing flash of wrong theme.

**CSS custom properties** (globals.css):
- `:root` = light mode values
- `[data-theme="dark"]` = dark mode overrides
- All Tailwind colors reference `var(--color-*)` — one change propagates everywhere

**Recharts color issue:** SVG attributes can't resolve `var()`. Solved with `useCssColors()` hook:
- Uses `getComputedStyle()` to read resolved CSS variable values
- `MutationObserver` watches `data-theme` changes on `<html>` to re-resolve on theme toggle
- Returns hex values suitable for Recharts `stroke`, `fill`, etc.

**color-mix utilities** (globals.css):
- Classes like `.bg-primary-subtle`, `.border-success-30`
- Uses `color-mix(in srgb, var(--color-*) X%, transparent)` instead of Tailwind's `/opacity` modifier (which breaks with CSS variables)

### Design System

"Anthropic Warm Humanist" — full specification in `utils/anthropic_theme.json`

| Element | Value |
|---------|-------|
| Primary color | Terracotta #C47B5A |
| Secondary color | Sage #7D8C6E |
| Accent color | Dusty Purple #8B8FC7 |
| Background (light) | #FAF7F4 |
| Background (dark) | #1E1B18 |
| UI font | General Sans |
| Heading font | Source Serif 4 |
| Data font | JetBrains Mono |
| Texture | Risograph grain via SVG feTurbulence filter |
| Shadows | Warm brown base rgba(45, 40, 36, *) |

---

## 8. Database Schema

**File:** `backend/database.py`

**Engine:** SQLite with WAL mode (Write-Ahead Logging for concurrent reads)

### Tables

#### daily_iv
Stores 252-day IV history per ticker. Used for IV rank/percentile computation and historical charts.

```sql
CREATE TABLE daily_iv (
    ticker     TEXT NOT NULL,
    date       TEXT NOT NULL,          -- YYYY-MM-DD
    atm_iv     REAL NOT NULL,          -- percentage (e.g., 20.5)
    rv30       REAL,                   -- 30-day realized vol
    vrp        REAL,                   -- iv_current - rv30
    term_slope REAL,                   -- front_iv / back_iv
    PRIMARY KEY (ticker, date)
);
CREATE INDEX idx_daily_iv_ticker ON daily_iv(ticker, date DESC);
```

#### scan_log
Audit log of scan runs.

```sql
CREATE TABLE scan_log (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp         TEXT NOT NULL,    -- ISO format
    tickers_scanned   INTEGER,
    duration_seconds  REAL,
    errors            TEXT              -- JSON array of error strings
);
```

#### scan_results
Caches full scan results (auto-pruned to last 50).

```sql
CREATE TABLE scan_results (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    scanned_at  TEXT NOT NULL,         -- ISO format
    regime      TEXT NOT NULL,         -- JSON: RegimeSummary
    tickers     TEXT NOT NULL,         -- JSON: list[TickerResult]
    historical  TEXT NOT NULL          -- JSON: dict[ticker -> HistoricalPoint[]]
);
```

### Key Functions

| Function | Purpose |
|----------|---------|
| `init_db()` | Creates tables + indexes, enables WAL + foreign keys |
| `store_daily_iv()` | Upsert daily IV record (ON CONFLICT DO UPDATE) |
| `get_historical_ivs(ticker, lookback_days)` | ATM IV values for IV rank calculation |
| `get_historical_series(ticker, lookback_days=120)` | Full series (date, iv, rv, vrp, term_slope) for charting |
| `log_scan(tickers, duration, errors)` | Record scan metadata |
| `store_scan_result(scanned_at, regime, tickers, historical)` | Cache full scan as JSON, auto-prune to 50 |
| `get_latest_scan()` | Retrieve most recent cached scan |
| `get_scan_history(limit=10)` | Metadata for recent scans |

---

## 9. API Reference

### GET /api/health

System status check.

**Response:** `HealthResponse`
```json
{
  "status": "ok",
  "marketdata_connected": true,
  "db_initialized": true,
  "tickers_configured": 15,
  "historical_data_points": 1842
}
```

### GET /api/scan/latest

Returns most recent cached scan result.

**Response:** `ScanResponse`
```json
{
  "timestamp": "2026-02-13T16:35:00",
  "regime": { "overall_regime": "NORMAL", "regime_color": "#7D8C6E", ... },
  "tickers": [ { "ticker": "SPY", "signal_score": 78, ... } ],
  "historical": { "SPY": [ { "date": "2025-10-15", "iv": 18.5, ... } ] },
  "scanned_at": "2026-02-13T16:35:00",
  "cached": true
}
```

Returns `message` field if no scans exist yet.

### POST /api/scan

Triggers a fresh full scan. May take 30–60 seconds.

**Response:** `ScanResponse` (same shape as above, `cached: false`)

### GET /api/scan/history?limit=10

Returns metadata for recent scans.

**Query params:** `limit` (int, max 50, default 10)

**Response:**
```json
{
  "scans": [
    { "id": 1, "scanned_at": "...", "tickers_scanned": 15, "best_ticker": "NVDA" }
  ]
}
```

### GET /api/ticker/{ticker}/history?days=120

Historical IV/RV series for a specific ticker.

**Path params:** `ticker` (string, must be in UNIVERSE)

**Query params:** `days` (int, max 365, default 120)

**Response:**
```json
{
  "ticker": "SPY",
  "history": [
    { "date": "2025-10-15", "iv": 18.5, "rv": 14.2, "vrp": 4.3, "term_slope": 0.92 }
  ]
}
```

### GET /api/universe

Returns the configured ticker universe.

**Response:**
```json
{
  "tickers": [
    { "ticker": "SPY", "name": "S&P 500 ETF", "sector": "Index" }
  ]
}
```

---

## 10. Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `MARKETDATA_TOKEN` | Yes | — | Bearer token for MarketData.app API |
| `NEXT_PUBLIC_API_URL` | No | `""` (same-origin proxy) | Backend URL for frontend |

### Docker Configuration

**docker-compose.yml:**
```yaml
services:
  backend:
    build: ./backend
    ports: ["8030:8000"]
    environment: [MARKETDATA_TOKEN]
    volumes: ["./backend/data:/app/data"]   # Bind mount for SQLite
    healthcheck: python httpx GET localhost:8000/api/health
    restart: unless-stopped

  frontend:
    build: ./frontend
    ports: ["3000:3000"]
    environment: [NEXT_PUBLIC_API_URL=http://backend:8000]
    depends_on: [backend]
```

**Port mapping:**
- Backend: container 8000 → host 8030
- Frontend: container 3000 → host 3000

**Data persistence:** SQLite at `./backend/data/vol_history.db` via bind mount

### CORS Origins

Configured in `main.py`:
- `http://localhost:3000`
- `http://localhost:8000`
- `http://127.0.0.1:3000`

### API Proxy

`next.config.js` rewrites `/api/*` → backend:
```javascript
source: '/api/:path*'
destination: `${NEXT_PUBLIC_API_URL || 'http://localhost:8030'}/api/:path*`
```

### Scoring Defaults (ScoringParams)

| Parameter | Default | Description |
|-----------|---------|-------------|
| min_iv_rank | 60 | Minimum IV rank to consider |
| min_vrp | 3.0 | Minimum VRP (absolute points) |
| max_rv_accel | 1.15 | Max RV acceleration before penalty |
| max_skew | 15.0 | Max skew before flagging |
| only_contango | true | Only trade contango structures |

### Frontend Filter Defaults (types.ts)

```typescript
DEFAULT_FILTERS = {
  minIVRank: 60,
  minVRP: 3.0,
  maxRVAccel: 1.15,
  contangoOnly: true
}
```

### Rate Limits

| Setting | Value |
|---------|-------|
| MarketData.app rate limit | 15 calls/min (token bucket) |
| Request timeout | 30 seconds |
| Scan concurrency | 2 tickers simultaneously |
| Retry attempts | 5 (exponential backoff) |

---

## 11. Development Guide

### Prerequisites

- Python 3.12+
- Node.js 20+
- Docker & Docker Compose (for containerized dev)
- MarketData.app API token (Starter tier minimum)

### Docker (Recommended)

```bash
# Start full stack
docker compose up --build

# Backend at http://localhost:8030
# Frontend at http://localhost:3000
# API docs at http://localhost:8030/docs

# Stop
docker compose down
```

### Local Development

**Backend:**
```bash
cd backend
pip install -r requirements.txt
export MARKETDATA_TOKEN=your_token_here
python main.py                   # Starts uvicorn on :8000 with hot reload
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev                      # Next.js dev server on :3000
npm run build                    # Production build
npm run lint                     # ESLint
```

### Historical Backfill

```bash
cd backend
python backfill.py --days 252 --verbose        # Full backfill (uses API credits)
python backfill.py --days 5 --tickers SPY       # Quick test
python backfill.py --resume --verbose            # Skip existing dates
python backfill.py --days 10 --dry-run           # Preview without API calls
```

### Running Tests

```bash
cd backend
python test_calculator.py
```

Tests cover: RV computation, ATM IV extraction, IV rank/percentile, scoring (normal + danger scenarios), database round-trip.

### Key Dependencies

**Backend:**
| Package | Version | Purpose |
|---------|---------|---------|
| fastapi | 0.115.6 | Web framework |
| uvicorn | 0.34.0 | ASGI server |
| httpx | 0.28.1 | Async HTTP client |
| numpy | 2.2.1 | Numerical computations |
| pydantic | 2.10.4 | Data validation |

**Frontend:**
| Package | Version | Purpose |
|---------|---------|---------|
| next | 14.2.x | React framework |
| react | 18.3.x | UI library |
| recharts | 2.12.7 | Charting |
| tailwindcss | 3.4.x | Utility CSS |
| clsx | 2.1.x | Conditional classNames |
| typescript | 5.4.x | Type checking |

---

*Generated from source code analysis. Cross-referenced all formulas against `calculator.py`, `scorer.py`, and `scoring.ts`.*
