---
last_verified: 2026-04-16
verified_against: 2134cff
rot_risk: low
rot_triggers:
  - backend/calculator.py
  - backend/scorer.py
audience: both
---

# Methodology

## Purpose

Why the math is shaped the way it is. This file explains the academic basis, the approximations we accept, and the limitations we live with. A quant-literate reader should leave with a clear understanding of what the model captures, what it doesn't, and where the known gaps are.

For the actual scoring formula and breakpoints, see [`1-domain/scoring-and-strategy.md`](scoring-and-strategy.md). For domain term definitions, see [`1-domain/glossary.md`](glossary.md). For the trading strategy built on top of this methodology, see [`references/strategy.md`](../../references/strategy.md).

## Scope

**This file covers:** Academic basis for VRP harvesting, IV approximation choices, RV computation choices, scoring shape rationale, liquidity filter design, known limitations.

**This file does NOT cover:**
- Scoring formula and breakpoints — see `1-domain/scoring-and-strategy.md`
- Metric computation details — see `references/metrics_report.md`
- Trading strategy and position management — see `references/strategy.md`

---

## The Variance Risk Premium — Foundation

The core thesis rests on the empirically documented variance risk premium: the market price of variance (implied) systematically exceeds realized variance. This has been studied extensively:

- **Carr & Wu (2009):** Formally decomposed the variance risk premium across equity indexes and individual stocks, showing it is negative (sellers of variance earn a premium) and time-varying.
- **Bollerslev, Tauchen & Zhou (2009):** Linked the variance risk premium to macroeconomic uncertainty, showing it predicts future equity returns.
- **Guo & Loeper (2013):** Extended the analysis to individual equity options, confirming the premium exists at the single-stock level with sufficient liquidity.

The practical implication: selling options (which are priced from implied variance) and hedging with realized movement (delta-hedging or simply holding through expiration) captures a positive expected return — as long as implied vol genuinely exceeds realized vol, which it does roughly 80% of the time empirically.

The scanner doesn't attempt to predict *when* the premium will fail. It measures *how wide* the premium is right now and flags conditions where historical patterns suggest it might not hold (backwardation, accelerating RV, extreme skew).

---

## ATM Implied Volatility: Black-Scholes as Practical Proxy

The theoretically correct measure of the market's implied variance is the **model-free implied variance** (MFIV) derived from the full options chain via the VIX-style strip methodology. This integrates IV across all strikes, weighting by 1/K², and captures the entire risk-neutral return distribution.

We use **30-day ATM Black-Scholes IV** instead. This is a significant simplification:

**Why it works in practice:**
- For near-the-money options, BSM IV and MFIV are closely correlated (typically R² > 0.95 for liquid names). The divergence grows in the wings, which we don't use for the core VRP measurement.
- ATM IV is available from a single strike (or a small interpolation), while MFIV requires the full chain with sufficient OTM strike coverage. Many of our 33 tickers lack deep OTM liquidity.
- ATM IV is directly observable and familiar to traders — it maps to a concrete contract they can execute.

**What we lose:**
- Sensitivity to tail risk pricing. MFIV captures the "crash premium" embedded in deep OTM puts; ATM IV does not. Our skew component partially compensates by measuring the 25-delta put premium separately.
- Consistency across vol regimes. ATM BSM IV has well-known smile effects — the ATM point moves along the smile as spot changes. MFIV is by construction smile-invariant.

**Accepted tradeoff:** The signal-to-noise ratio of ATM IV is sufficient for a daily scanner. The MFIV approach would require substantially more API calls (full-chain per ticker per tenor), more complex computation, and would still require the same liquidity filter that currently rejects the wing data we'd need.

---

## Realized Volatility: Close-to-Close Log Returns

We compute RV as the standard deviation of close-to-close log returns, annualized:

```
RV_n = std(ln(close[i] / close[i-1]), ddof=1) × √252 × 100
```

**Alternatives considered:**

- **Parkinson (1980):** Uses high-low range, more efficient estimator (captures intraday movement). Not used because our bar data occasionally has stale high/low values from after-hours or pre-market trades that distort the range.
- **Yang-Zhang (2000):** Combines open-close and high-low information. More complex, requires reliable open prices. Same data quality concern with opens.
- **Realized variance from intraday data:** Theoretically superior but requires tick/minute data that MarketData.app doesn't provide on the Starter plan.

Close-to-close is the least efficient estimator but the most robust to the data quality issues we face. Given that we're computing RV as one input to a multi-component score (not as a standalone risk measure), the efficiency loss is acceptable.

---

## IV Percentile Over IV Rank in Scoring

Both IV Rank and IV Percentile are computed from 252 trading days of history. Only IV Percentile feeds into the composite score. IV Rank is used for regime detection (>90 triggers CAUTION when combined with high RV accel) and position construction (≥80 changes delta and structure suggestions).

**Why Percentile for scoring:** IV Rank uses min-max normalization: `(current - min) / (max - min)`. A single outlier spike (e.g., the EEM 289.88% anomaly) compresses the entire scale — every subsequent day scores low because the max is extreme. Percentile is rank-based (`count of days below current / total`), so one outlier affects only its own position in the sorted list, not every other data point's score.

**Why Rank still matters:** IV Rank answers a different question — "where am I relative to the absolute range?" An IV Rank of 80 means IV is 80% of the way from its annual low to its annual high, which is useful for position construction (the absolute premium is fat enough for wider strikes). Percentile doesn't capture this magnitude information as directly.

---

## Scoring Shape Rationale

The five components use three distinct shapes, each chosen for the behavior it produces:

**Linear with dead zone** (VRP Quality, IV Percentile): Below a threshold, the component is zero — there is no partial credit for marginal conditions. Above the threshold, value scales linearly. This models a fixed-cost floor (transaction costs for VRP, minimum premium for IV percentile) below which no edge exists.

**Piecewise linear with hinge** (Term Structure, RV Stability): A two-segment line with different slopes above and below a transition point (1.0 for both — the boundary between favorable and unfavorable). The asymmetry (steeper on the favorable side for Term, steeper on the unfavorable side for RV) encodes the different information content: deep contango is strongly informative, while mild backwardation is ambiguous (could be a transient expiration-cycle effect).

**Trapezoid** (Skew): Ramps up, plateaus, then ramps down. Models a "sweet spot" phenomenon — moderate put demand (7–12 points of 25-delta skew) represents healthy hedging flow that premium sellers can harvest. Below the sweet spot, insufficient demand. Above it, the demand may be informed (institutions buying protection because they know something), making the premium appropriately priced rather than overpriced.

---

## Liquidity Filter Design

Before any metric is computed, the options chain passes through `filter_liquid_contracts()`:

| Filter | Threshold | Rationale |
|--------|-----------|-----------|
| IV > 200% | Reject | Physically implausible for listed equity options; indicates API data error |
| No bid/ask + IV > 100% | Reject | Stale theoretical value with no live market validation |
| bid = 0 | Reject | No buyer exists — price is meaningless |
| (ask - bid) / mid > 50% | Reject | Spread too wide for reliable mid-price IV extraction |

After filtering, `_count_atm_contracts()` checks whether ≥ 3 liquid contracts exist in the ATM bucket (within 3% of spot, near 30 DTE). If not, `iv_current` is set to `None` and the ticker receives NO DATA — see [ADR-002](../3-guardrails/decisions/002-no-data-over-computed-from-rejected.md).

The 3-contract minimum was determined empirically: with 1–2 contracts, ATM IV is dominated by a single strike's bid-ask midpoint noise. At 3+, the average of put+call IV at the nearest strike provides enough signal for the daily scanner's purposes.

---

## Known Limitations

**No dividend adjustment.** ATM IV from BSM doesn't account for discrete dividends. For high-dividend stocks near ex-date, the put-call parity relationship shifts, and our put+call average may be biased. The effect is small for most of our universe (tech-heavy, low or no dividends) but could matter for KO, JNJ, or MCD near their ex-dates.

**Single-tenor VRP.** We measure VRP at 30 days only. The term structure of VRP — whether the premium is wider or narrower at different tenors — is ignored. The term structure *score component* partially compensates by rewarding contango (which implies the VRP widens at longer tenors), but it's an indirect proxy.

**No intraday data.** All metrics are computed from daily closes and end-of-day option snapshots. Intraday vol spikes or reversals are invisible until the next scan. The 6:30 PM ET scan time provides settled data but cannot capture mid-day regime changes.

**Skew measurement gaps.** 5+ tickers regularly lack sufficient liquid 25-delta puts, producing `skew_25d = 0`. This is a data availability problem, not a model error — but it means the skew component contributes nothing for those names, understating their score by up to 10 points.

**RV10 noise.** A 10-day window is sensitive to individual outlier closes. The sizing system (Full/Half/Quarter) uses thresholds on `rv10/rv30`, which means a single noisy print can change the sizing recommendation. See [fragile-seams.md § RV10 window sensitivity](../3-guardrails/fragile-seams.md#rv10-window-sensitivity).
