# Theta Harvest — Metrics & Scoring Reference

A complete reference of every metric, scoring component, and chart on the dashboard, how each is calculated, and what data feeds into it. All formulas match the actual code implementation as of April 2026.

---

## Raw Data Sources

All metrics derive from three API data feeds fetched per ticker during each scan:

| Source | API | Raw Fields Used |
|--------|-----|-----------------|
| **Stock Snapshot** | MarketData.app `/v1/stocks/quotes/` | `price` (spot) |
| **Daily Bars** (180 calendar days) | MarketData.app `/v1/stocks/candles/` | `open`, `high`, `low`, `close`, `volume` per day |
| **Options Chain** (2 calls: narrow + wide) | MarketData.app `/v1/options/chain/` | `strike`, `expiration`, `side`, `iv`, `delta`, `gamma`, `theta`, `vega`, `bid`, `ask`, `openInterest`, `volume` |
| **Historical IV** (252 trading days) | Internal SQLite `daily_iv` table | `atm_iv` stored after each scan — builds over time |
| **Earnings Date** | FMP `/stable/earnings` (primary), MarketData.app fallback, Yahoo Finance cross-check | Next earnings date where date >= today |

---

## 1. Realized Volatility (RV)

**Calculated in:** `backend/calculator.py` → `compute_realized_vol()`

**Raw data:** Daily closing prices from 180-day bar history.

**Method:** Close-to-close log returns, annualized.

```
log_returns = diff(ln(closes))
RV_n = std(last n log_returns, ddof=1) × √252 × 100
```

| Metric | Window | Description |
|--------|--------|-------------|
| **RV10** | 10 trading days | Short-term realized vol |
| **RV20** | 20 trading days | Medium-term realized vol |
| **RV30** | 30 trading days | Primary benchmark (used for VRP) |
| **RV60** | 60 trading days | Long-term context |

**Displayed in:** DetailPanel metrics grid (RV10 and RV30 shown in sub-text under RV Accel cell). IV vs RV chart (dashed line).

---

## 2. RV Acceleration

**Calculated in:** `backend/calculator.py` → `compute_realized_vol()`

**Formula:**

```
RV Acceleration = RV10 / RV30
```

**Interpretation:**
- `< 0.85` — vol decelerating strongly (favorable)
- `0.85–1.0` — vol stable to declining (good)
- `1.0–1.10` — vol rising slightly (neutral)
- `1.10–1.20` — vol accelerating (caution, reduce size)
- `> 1.20` — vol spiking (danger, quarter size)

**Scoring impact (backend):** Additive component, 0–15 points:

```
if accel ≤ 0.85:   15 pts
elif accel ≥ 1.15:  0 pts
elif accel ≤ 1.0:   10 + (1.0 - accel) / 0.15 × 5    (linear 10→15)
else:               10 × (1.15 - accel) / 0.15        (linear 10→0)
```

**Sizing impact (frontend):** `> 1.10` = Half size, `> 1.20` = Quarter size.

---

## 3. ATM Implied Volatility (IV Current)

**Calculated in:** `backend/calculator.py` → `compute_atm_iv()`

**Raw data:** Options chain filtered through liquidity filter.

**Liquidity filter** (`filter_liquid_contracts()`):
- Reject if `bid == 0`
- Reject if `(ask - bid) / mid > 50%` spread ratio
- Reject if `IV > 200%` (garbage data)
- Reject if no bid/ask and `IV > 100%` (stale theoretical)
- Require ≥ 3 liquid contracts in ATM bucket, else `IV = None` → NO DATA

**Method:**
1. Group contracts by expiration, compute DTE for each.
2. Find two expirations closest to 30 DTE (within ±10 day tolerance).
3. At each expiration, filter to near-ATM contracts (strike within 3% of spot).
4. Average put + call IV at the strike nearest to spot (requires both sides).
5. Linearly interpolate between the two expirations to hit exactly 30 DTE.
6. Cap result at 200%.

```
weight = (30 - dte_near) / (dte_far - dte_near)
IV_30d = IV_near × (1 - weight) + IV_far × weight
```

Result is in percentage terms (e.g., 25.4 = 25.4% annualized IV).

If IV cannot be computed (insufficient liquid contracts), `iv_current = None` and the ticker receives score 0 with recommendation "NO DATA".

---

## 4. IV Rank

**Calculated in:** `backend/calculator.py` → `compute_iv_rank()`

**Formula:**

```
IV Rank = (IV_current - IV_52wk_low) / (IV_52wk_high - IV_52wk_low) × 100
```

**Range:** 0–100. Returns 50.0 if fewer than 20 historical data points.

**Usage:** IV Rank is **not used in scoring**. It is used for:
- Regime detection: IV Rank > 90 AND RV Accel > 1.1 → CAUTION regime
- Position construction: determines delta selection and DTE recommendations

---

## 5. IV Percentile

**Calculated in:** `backend/calculator.py` → `compute_iv_rank()` (same function, second return value)

**Formula:**

```
IV Percentile = (count of days where historical_iv < current_iv) / total_days × 100
```

**Interpretation:** "Current IV is higher than X% of the past year's readings."

**Scoring impact (backend):** Additive component, 0–25 points:

```
if percentile < 30:   0 pts   (no edge selling cheap premium)
else:                 (percentile - 30) × (25 / 70)   (linear 0→25)
```

Floor at 30th percentile. At 100th percentile: `(100 - 30) × 0.357 = 25 pts`.

---

## 6. Volatility Risk Premium (VRP)

**Calculated in:** `backend/calculator.py` → `build_vol_surface()`

**Formula:**

```
VRP = IV_current - RV30       (absolute spread, in vol points)
VRP Ratio = IV_current / RV30  (relative multiplier)
```

**Interpretation:**
- **VRP > 0** — implied vol exceeds realized vol; options are "expensive" relative to actual movement. This is the core edge for premium sellers.
- **VRP < 0** — realized vol exceeds implied; no premium selling edge.

**Scoring impact (backend):** VRP Quality component, 0–30 points (largest single component):

```
Dead zone below ratio 1.15 → 0 pts (marginal after costs)
Linear: (vrp_ratio - 1.15) × (30 / 0.45)
Capped at 30 pts (reached at ratio 1.60)
```

**Negative VRP gate:** If VRP < 0, total score is capped at 44 regardless of other components.

---

## 7. Term Structure

**Calculated in:** `backend/calculator.py` → `compute_term_structure()`

**Method:**
1. For each expiration in the chain, compute ATM IV (3% of spot, requires both put + call).
2. Skip expirations with ATM IV > 200% (implausible).
3. Sort by DTE, interpolate to 8 standard tenors: **1W** (7d), **2W** (14d), **1M** (30d), **2M** (60d), **3M** (90d), **4M** (120d), **6M** (180d), **1Y** (365d).
4. Compute slope:

```
Slope = Front IV (shortest tenor) / Back IV (longest tenor)
```

| Value | Meaning |
|-------|---------|
| `< 1.0` | Contango — normal, favorable for premium selling |
| `> 1.0` | Backwardation — stressed, near-term fear exceeds long-term |

**Scoring impact (backend):** Additive component, 0–20 points:

```
if slope ≤ 0.85:   20 pts   (deep contango)
elif slope ≥ 1.15:  0 pts   (deep backwardation)
elif slope ≤ 1.0:   5 + (1.0 - slope) / 0.15 × 15   (linear 20→5)
else:               5 × (1.15 - slope) / 0.15         (linear 5→0)
```

**Regime impact:**
- Slope > 1.15 → **DANGER** regime (per-ticker)
- Slope > 1.05 → **CAUTION** regime (per-ticker)

---

## 8. Volatility Skew (25-Delta Put Skew)

**Calculated in:** `backend/calculator.py` → `compute_skew()`

**Method:**
1. Pick the expiration closest to 30 DTE.
2. Compute delta for each contract (from API Greeks, or BSM fallback if missing).
3. Filter: puts with delta between -0.90 and -0.05, calls between 0.05 and 0.90.
4. ATM IV = average of contracts with delta 40–60.
5. 25Δ put IV = average of put contracts with delta 20–30.

```
25Δ Put Skew = IV(25Δ put) - IV(ATM)
Clamped to ±30 (physically plausible range)
```

**Scoring impact (backend):** Additive component, 0–10 points (trapezoid):

```
if skew < 0:       0 pts   (inverted skew, abnormal)
elif skew ≤ 7:     skew / 7 × 10           (linear 0→10)
elif skew ≤ 12:    10 pts                   (sweet spot plateau)
elif skew ≤ 20:    10 × (20 - skew) / 8    (linear taper 10→0)
else:              0 pts                    (extreme skew)
```

---

## 9. ATM Greeks (Theta & Vega)

**Calculated in:** `backend/calculator.py` → `find_atm_greeks()`

**Method:**
1. Find the expiration closest to 30 DTE (within 25-day tolerance).
2. Filter to contracts within 3% of spot with valid IV.
3. Pick the single contract nearest to spot.
4. Return its `theta` and `vega` from the API.

**Derived metric (frontend-computed):**

```
θ/ν Ratio = |theta| / |vega|
```

Higher ratio means faster time decay per unit of vol exposure — favorable for premium sellers.

**Scoring impact:** None. Display only.

---

## 10. ATR 14 (Average True Range)

**Calculated in:** `backend/calculator.py` → `compute_atr14()`

**Formula:**

```
True Range = max(High - Low, |High - Prev Close|, |Low - Prev Close|)
ATR 14 = mean(last 14 True Range values)
```

**Usage:** Position sizing reference — helps determine stop-loss width and strike spacing for credit spreads.

**Scoring impact:** None. Display only.

---

## 11. Earnings Date & DTE

**Sources (in priority order):**
1. FMP API `/stable/earnings` — primary, SQLite-cached
2. MarketData.app `/v1/stocks/earnings/` — fallback if no FMP key
3. Yahoo Finance — post-scan verification cross-check; overrides FMP when >5 day discrepancy

**Formula:**

```
Earnings DTE = (next_earnings_date - today).days
```

**Earnings gate (frontend-only):**
- If `Earnings DTE ≤ 14` → score forced to 0, action = SKIP
- `preGateScore` preserved for display so traders can see underlying quality
- ETFs are excluded from earnings checks

---

## Composite Scoring System

The backend computes a single **0–100 composite score** per ticker. The frontend passes through the backend score and applies the earnings gate. There is only **one scoring engine** (backend).

### Scoring Components (`backend/scorer.py`)

| Component | Max Points | Breakpoints | Purpose |
|-----------|-----------|-------------|---------|
| **VRP Quality** | 30 | Ratio 1.15→0, 1.60→30 (continuous) | Is there premium edge? |
| **IV Percentile** | 25 | 30th pctl→0, 100th→25 (continuous, floor at 30) | Are options expensive? |
| **Term Structure** | 20 | Slope 0.85→20, 1.0→5, 1.15→0 (piecewise linear) | Is the structure favorable? |
| **RV Stability** | 15 | Accel 0.85→15, 1.0→10, 1.15→0 (piecewise linear) | Is it safe? |
| **Skew** | 10 | 25Δ skew 0→0, 7→10, 12→10, 20→0 (trapezoid) | Is there put demand to harvest? |
| **Total** | **100** | | |

### Gates

| Gate | Condition | Effect |
|------|-----------|--------|
| **Negative VRP** | VRP < 0 | Caps total score at 44 (backend) |
| **Earnings** | DTE ≤ 14 days | Forces score to 0, action = SKIP (frontend) |
| **No Data** | IV = None (insufficient liquid contracts) | Score = 0, recommendation = NO DATA (backend) |

### Per-Ticker Regime Detection (`backend/scorer.py`)

| Regime | Trigger | Effect on Recommendation |
|--------|---------|--------------------------|
| **DANGER** | Term slope > 1.15 | Always → AVOID |
| **CAUTION** | Term slope > 1.05, OR (IV Rank > 90 AND RV Accel > 1.1) | Score ≥ 55 → REDUCE SIZE, else → NO EDGE |
| **NORMAL** | Default | Score ≥ 65 → SELL PREMIUM, ≥ 45 → CONDITIONAL, < 45 → NO EDGE |

### Recommendation → Frontend Action Mapping

| Backend Recommendation | Frontend Action |
|-----------------------|-----------------|
| SELL PREMIUM | SELL |
| CONDITIONAL | CONDITIONAL |
| REDUCE SIZE | AVOID |
| AVOID | AVOID |
| NO EDGE | NO EDGE |
| NO DATA | NO DATA |

### Position Sizing (frontend, based on RV Acceleration)

| RV Accel | Sizing |
|----------|--------|
| ≤ 1.10 | **Full** (standard allocation) |
| 1.10–1.20 | **Half** (50% of standard) |
| > 1.20 | **Quarter** (25% of standard) |

---

## Market Regime Detection (Dashboard-Level)

**Calculated in:** `frontend/src/components/RegimeBanner.tsx` → `computeRegime()`

Computed from all eligible tickers (excluding earnings-gated and NO DATA tickers).

| Regime | Trigger | Dashboard Behavior |
|--------|---------|-------------------|
| **OFF SEASON** | > 40% of tickers in DANGER | Hostile — no premium selling |
| **REGULAR SEASON** | > 25% of tickers in DANGER or CAUTION | Caution — defined-risk only, reduced sizing |
| **THE FINALS** | Avg VRP > 8 AND avg term slope < 0.90 | Favorable — widest statistical edge |
| **THE PLAYOFFS** | Default (none of above) | Normal — execute standard playbook |

**Banner metrics displayed:**
1. Avg VRP — warning if ≤ 5
2. Avg Term Slope — warning if ≥ 0.95
3. RV Accel — warning if ≥ 1.08
4. Tradeable count (SELL + CONDITIONAL) / eligible — warning if ≤ 3

---

## Position Construction (`backend/scorer.py`)

When a ticker's action is SELL or CONDITIONAL, the DetailPanel shows position construction hints:

| Regime | Delta | Structure | DTE | Notional |
|--------|-------|-----------|-----|----------|
| **DANGER** | N/A | No position | N/A | 0% |
| **CAUTION** | 10–15Δ | Iron condor or wide put spread (defined risk) | 21–30 DTE | 1–2% |
| **NORMAL, IV Rank ≥ 80** | 16–20Δ | Strangle if VRP > 8, condor if VRP > 4, put spread if VRP ≤ 4 | 30–45 DTE | 2–5% |
| **NORMAL, default** | 20–30Δ | Narrow put spread | 45–60 DTE | 2–3% |

---

## Charts

### 1. IV vs RV — 120 Day (ComposedChart)

**Data source:** `/api/ticker/{sym}/history?days=120` → SQLite `daily_iv` table.

| Series | Style | Differentiation |
|--------|-------|-----------------|
| **IV** (implied vol) | Solid line, 2px width | Primary metric |
| **RV30** (realized vol) | Dashed line, 1.5px width | Comparison baseline |
| **VRP area** | Gradient fill between IV and RV | Visual gap = premium |

**What it tells you:** When IV sits above RV, there's a persistent risk premium to harvest. The gap between the lines is the VRP.

### 2. Term Structure (AreaChart)

**Data source:** `term_structure_points` array from scan response.

| Series | Style |
|--------|-------|
| **IV by tenor** | Area chart with dots at each tenor point |

**X-axis:** Tenor labels — 1W, 2W, 1M, 2M, 3M, 4M, 6M, 1Y.
**Badge:** "Contango" or "Backwardation" indicator.

**What it tells you:** An upward-sloping curve (contango) is normal and favorable. An inverted curve (backwardation) signals acute fear.

### 3. Day-over-Day Comparison

**Data source:** `/api/scan/comparison` — compares latest scan to previous day's scan.

Shows change in: Score, VRP, Term Slope, RV Accel, IV, IV Percentile, Skew, and Regime. Color-coded: favorable changes in green (or bold for unfavorable, inverted for term slope and RV accel where lower is better).

---

## Data Persistence

| SQLite Table | Contents | Retention |
|-------------|----------|-----------|
| `daily_iv` | Per-ticker daily ATM IV, RV30, VRP, term slope | Indefinite (builds 252-day history for IV Rank/Percentile) |
| `scan_results` | Full scan snapshots (regime, all tickers, historical) | Last 50 scans |
| `scan_log` | Scan metadata (timestamp, ticker count, duration, errors) | Indefinite |
| `earnings_cache` | Per-ticker next earnings date + fetch timestamp | Until earnings date passes |
| `verification_results` | Post-scan metrics verification vs Yahoo Finance | Last 50 |
| `earnings_verification_results` | Earnings date cross-check vs Yahoo Finance | Last 50 |

| CSV Store | Contents | Location |
|-----------|----------|----------|
| `data/daily/{TICKER}.csv` | Daily spot, ATM IV, RV30, VRP, term slope | Date-descending |
| `data/quotes/{TICKER}.csv` | Full option quotes per scan (bid, ask, mid, IV, volume, OI) | Date-appended |

---

## Scan Pipeline

```
1. Cron fires at 6:30 PM ET (Mon-Fri, trading days only)
2. For each of 33 tickers (sequential, semaphore=1):
   a. Fetch stock snapshot (current price)
   b. Fetch 180 calendar days of daily bars
   c. Fetch options chain (2 API calls: narrow for ATM+term, wide for skew)
   d. Fetch earnings date (FMP → cache → or MarketData.app fallback)
   e. Extract ATM Greeks (theta, vega) + compute ATR14
   f. Get historical IVs from SQLite (for IV Rank/Percentile)
   g. build_vol_surface() → liquidity filter → ATM IV → IV rank → term structure → skew → VRP
   h. score_opportunity() → composite score + regime + recommendation + position construction
   i. Store daily_iv to SQLite, append to CSVs
3. Sort all results by score descending
4. Compute market-wide regime summary
5. Persist full scan to scan_results table
6. Fire-and-forget: post-scan verification against Yahoo Finance
7. Fire-and-forget: earnings verification against Yahoo Finance
```
