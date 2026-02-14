# Option Harvest — Metrics & Charts Reference

A complete reference of every metric, chart, and scoring component displayed on the dashboard, how each is calculated, and what raw data feeds into it.

---

## Raw Data Sources

All metrics derive from three API data feeds fetched per ticker during each scan:

| Source | API | Raw Fields Used |
|--------|-----|-----------------|
| **Stock Snapshot** | MarketData.app `/v1/stocks/quotes/` | `price` (spot) |
| **Daily Bars** (180 calendar days) | MarketData.app `/v1/stocks/candles/` | `open`, `high`, `low`, `close`, `volume` per day |
| **Options Chain** | MarketData.app `/v1/options/chain/` | `strike`, `expiration`, `contract_type`, `implied_volatility`, `delta`, `gamma`, `theta`, `vega` per contract |
| **Historical IV** (252 trading days) | Internal SQLite `daily_iv` table | `atm_iv` stored after each scan — builds over time |
| **Earnings Date** | FMP `/stable/earnings` (or MarketData.app fallback) | Next `date` field where date >= today |

---

## 1. Realized Volatility (RV)

**Calculated in:** `backend/calculator.py` -> `compute_realized_vol()`

**Raw data:** Daily closing prices from 180-day bar history.

**Method:** Close-to-close log returns, annualized.

```
log_returns = diff(ln(closes))
RV_n = std(last n log_returns, ddof=1) * sqrt(252) * 100
```

| Metric | Window | Description |
|--------|--------|-------------|
| **RV10** | 10 trading days | Short-term realized vol |
| **RV20** | 20 trading days | Medium-term realized vol |
| **RV30** | 30 trading days | Primary benchmark (used for VRP) |
| **RV60** | 60 trading days | Long-term context |

**Displayed in:** DetailPanel metrics grid (RV10 and RV30 shown in sub-text under VRP and RV Accel cells).

---

## 2. RV Acceleration

**Calculated in:** `backend/calculator.py` -> `compute_realized_vol()`

**Formula:**

```
RV Acceleration = RV10 / RV30
```

**Interpretation:**
- `< 1.0` — short-term vol is declining relative to the 30-day average (favorable)
- `1.0–1.05` — neutral
- `1.05–1.15` — rising, caution warranted
- `> 1.15` — rapid vol expansion, dangerous for premium sellers

**Displayed in:**
- **Leaderboard:** "RV Accel" column — red text if > 1.10
- **DetailPanel:** Metrics grid with sub-text showing `RV10 / RV30` breakdown — warning color if > 1.10
- **RegimeBanner:** Averaged across all tickers as "RV Accel" — warning if >= 1.08

**Scoring impact:** -6 pts if > 1.05, -15 pts if > 1.15 (frontend). -8 / -15 (backend).

**Sizing impact:** > 1.10 = Half size, > 1.20 = Quarter size.

---

## 3. ATM Implied Volatility (IV Current)

**Calculated in:** `backend/calculator.py` -> `compute_atm_iv()`

**Raw data:** Full options chain — all contracts with `implied_volatility > 0`.

**Method:**
1. Group contracts by expiration, compute DTE for each.
2. Find two expirations closest to 30 DTE (within +/-10 day tolerance).
3. At each expiration, filter to near-ATM contracts (strike within 3% of spot price).
4. Average put + call IV at the strike nearest to spot.
5. Linearly interpolate between the two expirations to hit exactly 30 DTE.

```
weight = (30 - dte_near) / (dte_far - dte_near)
IV_30d = IV_near * (1 - weight) + IV_far * weight
```

Result is in percentage terms (e.g., 25.4 = 25.4% annualized IV).

**Displayed in:** DetailPanel (sub-text under VRP: `IV {value}`), IV vs RV chart (primary line).

---

## 4. IV Rank

**Calculated in:** `backend/calculator.py` -> `compute_iv_rank()`

**Raw data:** Up to 252 daily ATM IV values from SQLite `daily_iv` table.

**Formula:**

```
IV Rank = (IV_current - IV_52wk_low) / (IV_52wk_high - IV_52wk_low) * 100
```

**Range:** 0–100. Returns 50.0 if fewer than 20 historical data points.

**Displayed in:** Used in backend scoring only (not directly shown on dashboard). Determines position construction suggestions (delta, DTE).

**Scoring impact (backend):** `min(25, iv_rank * 0.3)` = 0–25 points.

---

## 5. IV Percentile

**Calculated in:** `backend/calculator.py` -> `compute_iv_rank()`

**Raw data:** Same 252-day historical IV series as IV Rank.

**Formula:**

```
IV Percentile = (count of days where historical_iv < current_iv) / total_days * 100
```

**Interpretation:** "Current IV is higher than X% of the past year's readings."

**Displayed in:**
- **DetailPanel:** Metrics grid — "IV Percentile" cell with sub-text "252-day window"

**Scoring impact (frontend):** 20 pts if >= 80%, 14 pts if >= 60%, 8 pts if >= 40%, 3 pts otherwise.

---

## 6. Volatility Risk Premium (VRP)

**Calculated in:** `backend/calculator.py` -> `build_vol_surface()`

**Formula:**

```
VRP = IV Current - RV30       (absolute spread, in vol points)
VRP Ratio = IV Current / RV30  (relative multiplier)
```

**Interpretation:**
- **VRP > 0** — implied vol exceeds realized vol, meaning options are "expensive" relative to actual movement. This is the core edge for premium sellers.
- **VRP < 0** — realized vol exceeds implied, no premium selling edge.

**Displayed in:**
- **Leaderboard:** Horizontal bar chart (green >= 10, blue >= 5, gray < 5)
- **DetailPanel:** Metrics grid — highlighted green if >= 8, sub-text shows `IV {x} - RV {y}`
- **RegimeBanner:** "Avg VRP" across all tickers — warning if <= 5

**Scoring impact (frontend):** `min(40, VRP * 2.5)` = 0–40 points.
**Scoring impact (backend):** `min(25, (VRP_ratio - 1) * 30)` = 0–25 points.

---

## 7. Term Structure

**Calculated in:** `backend/calculator.py` -> `compute_term_structure()`

**Raw data:** Full options chain — ATM IV computed at each available expiration.

**Method:**
1. For each expiration in the chain, compute ATM IV (same 3%-of-spot filter as above).
2. Sort by DTE.
3. Interpolate to 8 standard tenors: **1W** (7d), **2W** (14d), **1M** (30d), **2M** (60d), **3M** (90d), **4M** (120d), **6M** (180d), **1Y** (365d).
4. Compute slope:

```
Slope = Front IV (shortest tenor) / Back IV (longest tenor)
```

| Metric | Formula | Meaning |
|--------|---------|---------|
| **Slope** | front_iv / back_iv | < 1.0 = contango (normal, good), > 1.0 = backwardation (stress) |
| **Is Contango** | slope < 1.0 | Boolean flag |
| **Front IV** | IV at shortest available tenor | Near-term implied vol |
| **Back IV** | IV at longest available tenor | Deferred implied vol |

**Displayed in:**
- **Leaderboard:** "Term" column — red if > 1.0
- **DetailPanel:** Metrics grid with "Contango" / "Backwardation" sub-text, warning color if > 1.0
- **DetailPanel:** Term Structure area chart (see Charts section)
- **RegimeBanner:** "Avg Term Slope" — warning if >= 0.95

**Scoring impact (frontend):** 25 pts if < 0.85, 18 if < 0.90, 12 if < 0.95, 5 if < 1.0.
**Scoring impact (backend):** 18 pts if < 0.85, 12 if < 0.95, 6 if < 1.0, -5 penalty if >= 1.0.

---

## 8. Volatility Skew (25-Delta Put Skew)

**Calculated in:** `backend/calculator.py` -> `compute_skew()`

**Raw data:** Options chain at the expiration nearest to 30 DTE — all puts and calls with valid IV.

**Method:**
1. Pick the expiration closest to 30 DTE.
2. If Greeks are available, plot IV by delta:
   - Puts: contracts with delta between -0.90 and -0.05
   - Calls: contracts with delta between 0.05 and 0.90
3. If no Greeks, fall back to moneyness-as-delta approximation.
4. Identify ATM IV (contracts near 50-delta) and 25-delta put IV (contracts near 25-delta).

```
25Δ Put Skew = IV(25Δ put) - IV(ATM)
```

**Additional metrics (computed but not charted):**
- **Put Skew Slope:** Linear regression slope of put IV vs delta
- **Call Skew Slope:** Linear regression slope of call IV vs delta

**Interpretation:** Higher skew = more expensive downside protection. May indicate informed hedging or tail fear.

**Displayed in:**
- **DetailPanel:** Metrics grid — "25Δ Put Skew" with sub-text "vol points above ATM"

**Scoring impact (backend):** 8 pts if > 7, 6 pts if > 4, 5 pts if > 10 (steep), 3 pts otherwise.

---

## 9. ATM Greeks (Theta & Vega)

**Calculated in:** `backend/calculator.py` -> `find_atm_greeks()`

**Raw data:** Options chain — `theta` and `vega` fields from the ATM contract nearest to 30 DTE.

**Method:**
1. Find the expiration closest to 30 DTE (within 25-day tolerance).
2. Filter to contracts within 3% of spot.
3. Pick the single contract nearest to spot.
4. Return its `theta` and `vega`.

**Derived metric:**

```
Theta/Vega Ratio = |theta| / |vega|
```

**Interpretation:** Higher ratio means the option decays faster per unit of vol exposure — favorable for premium sellers collecting time decay.

**Displayed in:**
- **DetailPanel:** Metrics grid — "Θ/V Ratio" with sub-text showing raw `θ {value} / ν {value}`

---

## 10. ATR 14 (Average True Range)

**Calculated in:** `backend/calculator.py` -> `compute_atr14()`

**Raw data:** Daily bars — `high`, `low`, `close` for 15+ consecutive days.

**Formula:**

```
True Range = max(High - Low, |High - Prev Close|, |Low - Prev Close|)
ATR 14 = mean(last 14 True Range values)
```

**Displayed in:**
- **DetailPanel:** Metrics grid — "$X.XX" with sub-text showing "X.XX% of spot"

**Usage:** Position sizing reference — helps determine stop-loss width and notional risk per contract.

---

## 11. Earnings Date & DTE

**Calculated in:** `backend/main.py` via `fmp_client.py` -> `get_next_earnings()`

**Raw data:** FMP API `/stable/earnings` endpoint — returns upcoming earnings dates per ticker. Cached in SQLite `earnings_cache` table to survive restarts.

**Formula:**

```
Earnings DTE = (next_earnings_date - today).days
```

**Rules:**
- ETFs have no earnings — displays "ETF"
- If Earnings DTE <= 14 days -> **earnings gate fires**, ticker is SKIP'd with score = 0

**Displayed in:**
- **Leaderboard:** "Earnings" column (hidden on tablet) — shows "Xd", warning icon if <= 14 days
- **DetailPanel:** Metrics grid — "Xd" or "ETF", warning sub-text "Within DTE window" if <= 14

---

## Composite Scoring System

Scores combine the individual metrics above into a single 0–100 signal. The frontend and backend compute scores independently with slightly different weights.

### Frontend Score (`frontend/src/lib/scoring.ts`)

Applied client-side for every displayed ticker.

| Component | Points | Formula |
|-----------|--------|---------|
| **VRP** | 0–40 | `min(40, VRP * 2.5)` |
| **Term Structure** | 5–25 | 25 if slope < 0.85, 18 if < 0.90, 12 if < 0.95, 5 otherwise |
| **IV Percentile** | 3–20 | 20 if >= 80%, 14 if >= 60%, 8 if >= 40%, 3 otherwise |
| **RV Accel Penalty** | -15 to 0 | -15 if > 1.15, -6 if > 1.05 |
| **Earnings Gate** | -> 0 | If DTE <= 14 days, score = 0, action = SKIP |

**Total range:** 0–100 (clamped).

### Backend Score (`backend/scorer.py`)

Computed during scan for persistence and position construction.

| Component | Points | Formula |
|-----------|--------|---------|
| **VRP** | 0–25 | `min(25, (VRP_ratio - 1) * 30)` |
| **IV Rank** | 0–25 | `min(25, iv_rank * 0.3)` |
| **Term Structure** | -5 to +18 | 18 if slope < 0.85, 12 if < 0.95, 6 if < 1.0, -5 if >= 1.0 |
| **RV Accel Penalty** | -15 to 0 | -15 if > 1.15, -8 if > 1.05 |
| **Skew** | 3–8 | 8 if > 7, 6 if > 4, 5 if > 10, 3 otherwise |
| **Regime Override** | -35 to 0 | -35 if DANGER, -20 if CAUTION |
| **Below-threshold penalties** | -10 each | If VRP < min_vrp or IV Rank < min_iv_rank |

### Action Mapping

| Frontend Score | Action |
|----------------|--------|
| >= 70 | **SELL PREMIUM** |
| >= 50 | **CONDITIONAL** |
| < 50 | **NO EDGE** |
| Earnings <= 14d | **SKIP** |

### Position Sizing

Determined by RV Acceleration:

| RV Accel | Sizing |
|----------|--------|
| <= 1.10 | **Full** (standard allocation) |
| 1.10–1.20 | **Half** (50% of standard) |
| > 1.20 | **Quarter** (25% of standard) |

---

## Market Regime Detection

### Frontend Regime (`RegimeBanner.tsx`)

Computed from the full array of scored tickers.

| Regime | Trigger | Dashboard Behavior |
|--------|---------|-------------------|
| **HOSTILE** | 3+ tickers in backwardation OR avg term slope > 1.02 | Red banner, read-only mode alert |
| **CAUTION** | Avg RV Accel > 1.12 OR 1+ tickers in backwardation | Orange banner |
| **FAVORABLE** | Avg VRP > 8 AND avg term slope < 0.90 | Green banner |
| **NORMAL** | Default | Sage banner |

**Banner aggregate metrics displayed:**
1. Avg VRP (warning if <= 5)
2. Avg Term Slope (warning if >= 0.95)
3. RV Accel (warning if >= 1.08)
4. Tradeable count (SELL + CONDITIONAL tickers, warning if <= 3)

### Backend Regime (`scorer.py` — per-ticker)

| Regime | Trigger |
|--------|---------|
| **DANGER** | Term slope > 1.05 |
| **CAUTION** | Term slope > 1.0, or IV Rank > 90 AND RV Accel > 1.1 |
| **NORMAL** | Default |

---

## Charts

### 1. IV vs RV — 120 Day (ComposedChart)

**Component:** `DetailPanel.tsx`
**Chart library:** Recharts `ComposedChart` with `Area` + two `Line` series.
**Data source:** `/api/ticker/{sym}/history?days=120` -> SQLite `daily_iv` table.

| Series | Data Key | Style | Color |
|--------|----------|-------|-------|
| **IV** (implied vol) | `iv` | Solid line (2px) + gradient area fill | Terracotta primary |
| **RV30** (realized vol) | `rv` | Dashed line (1.5px) | Sage secondary |

**X-axis:** Date labels (e.g., "Jan 15"), every 20th point shown.
**Y-axis:** Volatility % (auto-scaled).
**Tooltip:** Custom tooltip showing date, IV value, RV30 value.

**What it tells you:** When IV consistently sits above RV, there's a persistent risk premium to harvest. The gap between the lines is the VRP.

### 2. Term Structure (AreaChart)

**Component:** `DetailPanel.tsx`
**Chart library:** Recharts `AreaChart`.
**Data source:** `term_structure_points` array from the scan response (computed in `calculator.py`).

| Series | Data Key | Style | Color |
|--------|----------|-------|-------|
| **IV by tenor** | `iv` | Area with gradient fill + dots at each point | Purple accent |

**X-axis:** Tenor labels — 1W, 2W, 1M, 2M, 3M, 4M, 6M, 1Y (as available).
**Y-axis:** IV % (auto-scaled).
**Badge:** "Contango" (green) or "Backwardation" (red) pill above chart.

**What it tells you:** An upward-sloping curve (contango) is normal and favorable — short-dated options are cheaper than long-dated. An inverted curve (backwardation) signals acute fear and is dangerous for premium sellers.

### 3. VRP Bar (inline in Leaderboard)

**Component:** `Leaderboard.tsx` -> `VRPBar`
**Chart type:** Horizontal progress bar (CSS-based).

| VRP Range | Bar Color |
|-----------|-----------|
| >= 10 | Green (secondary) |
| >= 5 | Terracotta (primary) |
| < 5 | Gray (tertiary) |

**Scale:** 0–20 (values above 20 still show full bar).

### 4. Score Pill (inline in Leaderboard)

**Component:** `Leaderboard.tsx` -> `ScorePill`
**Visual:** Circular badge showing the integer score 0–100.

| Score Range | Color |
|-------------|-------|
| >= 70 | Green |
| >= 50 | Orange |
| > 0 | Gray |
| 0 | Red |

---

## Position Construction (DetailPanel)

When a ticker's action is SELL or CONDITIONAL, the DetailPanel shows a 4-cell position construction grid. These values come from `scorer.py` based on regime and IV rank:

| Field | Logic |
|-------|-------|
| **Target Delta** | 10–15Δ (CAUTION), 16–20Δ (IV Rank >= 80), 20–30Δ (default) |
| **Structure** | Short strangle / jade lizard (high VRP), iron condor / put spread (moderate VRP), narrow put spread (low VRP) |
| **DTE** | 21–30 DTE (CAUTION), 30–45 DTE (high IV Rank), 45–60 DTE (default) |
| **Sizing** | Standard / Half / Quarter (based on RV Acceleration) |

---

## Default Filter Thresholds

These are the default filter values applied in the frontend (`types.ts` -> `DEFAULT_FILTERS`):

| Filter | Default | Effect |
|--------|---------|--------|
| Min IV Rank | 60 | Only show tickers with IV in the upper 40% of their 1-year range |
| Min VRP | 3.0 | Require at least 3 vol points of implied-over-realized spread |
| Max RV Accel | 1.15 | Exclude tickers where short-term vol is expanding too fast |
| Max Skew | 15.0 | Cap on extreme tail pricing |
| Only Contango | true | Exclude any ticker in backwardation |

---

## Data Persistence

| SQLite Table | Contents | Retention |
|-------------|----------|-----------|
| `daily_iv` | Per-ticker daily ATM IV, RV30, VRP, term slope | Indefinite (builds 252-day history for IV Rank) |
| `scan_results` | Full scan snapshots (regime, all tickers, historical) | Last 50 scans |
| `scan_log` | Scan metadata (timestamp, ticker count, duration, errors) | Indefinite |
| `earnings_cache` | Per-ticker next earnings date + fetch timestamp | Until earnings date passes |
