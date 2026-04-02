# Theta Harvest — Options Premium Selling Strategy

## The Core Thesis

Options are systematically overpriced. Implied volatility (what the market expects) consistently exceeds realized volatility (what actually happens) because investors overpay for protection. This gap — the **Volatility Risk Premium (VRP)** — is the edge we harvest by selling options.

We don't predict direction. We sell inflated insurance premiums and collect theta (time decay) as the options expire worthless or are bought back cheaply.

---

## What We Sell and Why

**We sell options premium** — specifically short puts, put credit spreads, iron condors, and strangles on highly liquid US equities and ETFs. We collect upfront credit and profit when the underlying stays within our expected range.

**Why it works:**
- IV overstates future realized moves ~80% of the time historically
- Option buyers pay a fear premium (insurance markup) that decays daily as theta
- We systematically identify when this fear premium is fattest and the market structure supports harvesting it

**Why it can fail:**
- Realized vol can exceed implied during regime changes (market crashes, gap moves)
- Earnings announcements create binary risk that no premium compensates for
- Backwardation signals that near-term risk is underpriced, not overpriced

---

## The Five Signals We Measure

Every trading day after market close, we scan 33 tickers (22 stocks + 11 ETFs) across 7 sectors and score each on five dimensions:

### 1. VRP Quality (0–30 points) — "Is there edge?"

The single most important signal. Measures how much implied vol exceeds realized vol.

```
VRP Ratio = IV(30-day ATM) / RV(30-day close-to-close)
Score = (ratio - 1.15) × 66.67, clamped 0–30
```

- **Dead zone below 1.15**: A 15% markup is marginal after transaction costs. No points.
- **Sweet spot 1.30–1.60**: Options priced 30–60% above realized moves. Fat premium.
- **Above 1.60**: Plateaus at 30 points. Diminishing marginal value.

If VRP is negative (RV > IV), the total score is capped at 44 regardless of other signals. There is no edge selling underpriced insurance.

### 2. IV Percentile (0–25 points) — "Are options expensive?"

Measures where current IV sits relative to the past 252 trading days.

```
IV Percentile = (days where historical IV < current IV) / total days × 100
Score = (percentile - 30) × 0.357, clamped 0–25
```

- **Floor at 30th percentile**: Below this, options are too cheap to sell. Zero points.
- **80th+ percentile**: Options are historically expensive. Maximum edge.

We use IV Percentile (not IV Rank) because percentile is more robust to outlier spikes.

### 3. Term Structure (0–20 points) — "Is the market structure favorable?"

Compares near-term IV to far-term IV. Normal markets price longer-dated options higher (contango). Stressed markets invert this (backwardation).

```
Slope = Front-month IV / Back-month IV
```

| Slope | Structure | Points | Meaning |
|-------|-----------|--------|---------|
| ≤ 0.85 | Deep contango | 20 | Ideal — near-term calm, long-term uncertainty |
| 0.85–1.0 | Contango | 5–20 | Normal, favorable |
| 1.0 | Flat | 5 | Neutral |
| 1.0–1.15 | Mild backwardation | 0–5 | Caution |
| ≥ 1.15 | Deep backwardation | 0 | Danger — market expects imminent trouble |

Backwardation is the strongest danger signal. When near-term options cost more than long-term ones, the market is pricing an acute event. Premium sellers get crushed in backwardation because the "expensive" near-term options often turn out to be correctly priced.

### 4. RV Stability (0–15 points) — "Is it safe?"

Measures whether realized volatility is accelerating or decelerating.

```
RV Acceleration = RV10 / RV30
```

| Accel | Points | Meaning |
|-------|--------|---------|
| ≤ 0.85 | 15 | Vol decelerating — recent calm, favorable |
| 0.85–1.0 | 10–15 | Stable — safe |
| 1.0–1.15 | 0–10 | Rising — caution |
| ≥ 1.15 | 0 | Spiking — dangerous |

This metric also drives **position sizing** on the frontend:
- Accel ≤ 1.10 → Full size
- Accel 1.10–1.20 → Half size
- Accel > 1.20 → Quarter size

### 5. Skew (0–10 points) — "Is there put demand to harvest?"

Measures how much more expensive 25-delta puts are compared to ATM options.

```
25Δ Skew = IV(25-delta put) - IV(ATM)
```

| Skew | Points | Meaning |
|------|--------|---------|
| < 0 | 0 | Inverted — abnormal, no put premium |
| 0–7 | 0–10 | Normal demand, building premium |
| 7–12 | 10 | Sweet spot — steady hedging demand = premium to sell |
| 12–20 | 10→0 | Extreme — institutions may know something |
| > 20 | 0 | Too extreme — informed protection buying |

---

## The Scoring System

The five signals combine into a single **composite score (0–100)**:

```
Total = VRP Quality (30) + IV Percentile (25) + Term Structure (20)
      + RV Stability (15) + Skew (10)
```

All components are **continuous** (no cliff effects) and **additive** (no penalties that can go negative). The score represents pure edge quality.

### Score → Recommendation

| Score | Recommendation | Meaning |
|-------|---------------|---------|
| ≥ 65 | **SELL PREMIUM** | Strong edge — execute |
| 45–64 | **CONDITIONAL** | Decent edge — trade with discipline |
| < 45 | **NO EDGE** | Skip — not enough edge to justify risk |
| 0 (gated) | **SKIP** | Earnings within 14 days — no exceptions |

---

## The Three Safety Systems

### 1. Regime Detection (Per-Ticker)

Each ticker gets a regime classification based on term structure and IV conditions:

| Regime | Trigger | Effect |
|--------|---------|--------|
| **DANGER** | Term slope > 1.15 (deep backwardation) | Recommendation → AVOID, regardless of score |
| **CAUTION** | Term slope > 1.05, or IV Rank > 90 + RV Accel > 1.1 | Score ≥ 55 → REDUCE SIZE (defined-risk only), else NO EDGE |
| **NORMAL** | Default | Score determines recommendation normally |

A ticker can score 90 and still show AVOID if it's in DANGER regime. The regime system overrides the score because selling premium into backwardation is how accounts blow up.

### 2. Earnings Gate (Frontend)

If a ticker has earnings within 14 calendar days:
- Score is forced to **0**
- Action is **SKIP**
- No exceptions, no overrides

Earnings create binary gap risk (10%+ overnight moves) that no premium can compensate for. The pre-gate score is preserved for display so traders can identify post-earnings opportunities.

### 3. Negative VRP Cap (Backend)

If VRP < 0 (realized vol exceeds implied vol):
- Total score is capped at **44** (below CONDITIONAL threshold)
- This prevents other metrics from creating a false SELL signal when the core thesis doesn't hold

---

## Market Regime (Dashboard-Level)

The dashboard computes an overall market regime from all eligible tickers:

| Regime | Trigger | Posture |
|--------|---------|---------|
| **OFF SEASON** | > 40% of tickers in DANGER | No trading. Go to cash. Systemic stress. |
| **REGULAR SEASON** | > 25% stressed (DANGER + CAUTION) | Trade small. Defined-risk only. Reduced sizing. |
| **THE FINALS** | Avg VRP > 8 AND avg term slope < 0.90 | Best environment. Wide VRP + contango. Be aggressive. |
| **THE PLAYOFFS** | Default | Normal. Execute playbook on high-scoring names. |

The regime hierarchy: OFF SEASON overrides REGULAR SEASON overrides THE FINALS overrides THE PLAYOFFS.

---

## Position Construction

When a ticker qualifies (SELL or CONDITIONAL), the system suggests specific trade parameters:

### Delta Selection
- **CAUTION regime**: 10–15Δ (further OTM, more room for error)
- **IV Rank ≥ 80**: 16–20Δ (premium is fat enough to go closer)
- **Default**: 20–30Δ (standard positioning)

### Structure Selection
Based on VRP magnitude and regime:

| Condition | Structure |
|-----------|-----------|
| DANGER regime | No position |
| CAUTION regime | Iron condor or wide put spread (defined risk only) |
| VRP > 8, normal regime | Short strangle or jade lizard |
| VRP 4–8, normal regime | Iron condor or put credit spread |
| VRP ≤ 4, normal regime | Narrow put credit spread (defined risk) |

### DTE Selection
- **CAUTION**: 21–30 DTE (shorter to limit exposure)
- **IV Rank ≥ 80**: 30–45 DTE (optimal theta decay with fat premium)
- **Default**: 45–60 DTE (more time, narrower strikes)

### Position Sizing
Based on RV Acceleration (vol momentum):
- **Accel ≤ 1.10**: Full standard allocation (2–5% portfolio notional)
- **Accel 1.10–1.20**: Half (vol rising, reduce exposure)
- **Accel > 1.20**: Quarter (vol spiking, minimal exposure)

---

## The Ticker Universe

33 tickers across 7 sectors, selected for options liquidity:

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

ETFs are excluded from earnings checks. All tickers must have liquid options chains (≥3 ATM contracts passing liquidity filter).

---

## Daily Workflow

1. **6:30 PM ET**: Automated scan runs (cron, trading days only)
2. **Check regime**: If OFF SEASON → no action. If REGULAR SEASON → caution.
3. **Review SELL signals**: Highest-scoring tickers with NORMAL regime. Verify score components make sense.
4. **Check sizing**: Respect Half/Quarter sizing from RV acceleration. Don't override.
5. **Check earnings proximity**: Even if a ticker isn't gated (>14d), earnings within 21d warrant smaller size.
6. **Enter positions**: Use the suggested delta, structure, and DTE. Defined risk always in REGULAR SEASON.
7. **Manage at 50% profit**: Close winning positions at 50% of max profit. Don't wait for expiration.
8. **Monitor regime changes**: If a ticker flips to DANGER after entry, close the position. Don't hold through backwardation.

---

## What This Strategy Does NOT Do

- **Predict direction**: We are delta-neutral or slightly directional. We profit from time decay, not moves.
- **Trade through earnings**: The 14-day gate is absolute. No hero trades.
- **Fight backwardation**: If the term structure inverts, we step aside. The market is telling us something.
- **Guarantee profits**: This is a probabilistic edge. Individual trades can lose. The edge is in aggregate over many trades.
- **Replace risk management**: The scoring system identifies opportunities. Position sizing, stop losses, and portfolio Greeks management are the trader's responsibility.

---

## Edge Decay and Timing

The premium selling edge is not constant. It follows a cycle:

1. **Shock** (OFF SEASON): IV spikes, backwardation. No edge — the options are correctly priced or underpriced.
2. **Fear Overshoot** (transitioning to REGULAR SEASON → THE FINALS): IV stays elevated after RV drops. VRP widens. This is when the edge is fattest.
3. **Normalization** (THE PLAYOFFS): IV and RV converge. VRP returns to baseline. Moderate edge.
4. **Complacency**: IV drops to historical lows. Little premium to sell. No edge.

The system is designed to be most active during phase 2 (wide VRP, contango returning) and phase 3 (normal conditions). It forces inactivity during phases 1 and 4. Patience during OFF SEASON is what makes THE FINALS profitable.
