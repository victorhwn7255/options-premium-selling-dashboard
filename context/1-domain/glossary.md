---
last_verified: 2026-04-16
verified_against: dc030c3
rot_risk: low
rot_triggers:
  - backend/scorer.py
  - frontend/src/components/RegimeBanner.tsx
audience: both
---

# Domain Glossary

## Purpose

Quick-reference definitions for every domain term used in the codebase. Look up a term, get the definition, formula, and relevant thresholds in one place.

## Scope

**This file covers:** Volatility metrics, structure metrics, trade-level metrics, regime labels, recommendation labels, position terms, key thresholds.

**This file does NOT cover:**
- Why formulas are shaped this way — see `1-domain/methodology.md`
- How terms combine into a score — see `1-domain/scoring-and-strategy.md`
- Full metric derivation with code paths — see `references/metrics_report.md`

---

## Volatility Metrics

| Term | Formula | Unit | Code location |
|------|---------|------|---------------|
| **RV (Realized Volatility)** | `std(log_returns, ddof=1) × √252 × 100` | % annualized | `calculator.py:compute_realized_vol()` |
| **RV10 / RV20 / RV30 / RV60** | RV over last 10/20/30/60 trading days | % | Same function, different windows |
| **IV (Implied Volatility)** | ATM 30-day IV, interpolated from 2 nearest expirations | % annualized | `calculator.py:compute_atm_iv()` |
| **VRP (Volatility Risk Premium)** | `IV − RV30` | vol points | `calculator.py:build_vol_surface()` |
| **VRP Ratio** | `IV / RV30` | dimensionless | Same |
| **IV Rank** | `(current − 52wk_low) / (52wk_high − 52wk_low) × 100` | 0–100 | `calculator.py:compute_iv_rank()` |
| **IV Percentile** | `count(days where IV < current) / total_days × 100` | 0–100 | Same function, second return |

---

## Structure Metrics

| Term | Formula | Unit | Code location |
|------|---------|------|---------------|
| **Term Structure** | ATM IV curve across 8 tenors: 1W, 2W, 1M, 2M, 3M, 4M, 6M, 1Y | % per tenor | `calculator.py:compute_term_structure()` |
| **Term Slope** | `front_iv / back_iv` (shortest / longest tenor) | ratio | Same |
| **Contango** | Slope < 1.0 — normal: far-dated options pricier | — | — |
| **Backwardation** | Slope > 1.0 — stressed: near-term options pricier | — | — |
| **RV Acceleration** | `RV10 / RV30` | ratio | `calculator.py:compute_realized_vol()` |
| **25-Delta Skew** | `IV(25Δ put) − IV(ATM)`, clamped ±30 | vol points | `calculator.py:compute_skew()` |

---

## Trade-Level Metrics

| Term | Formula | Unit | Code location |
|------|---------|------|---------------|
| **Theta (θ)** | Daily time decay of the ATM option | $/day | `calculator.py:find_atm_greeks()` |
| **Vega (ν)** | Price sensitivity per 1% IV change (normalized) | $/1%IV | Same, via `_normalize_vega()` |
| **θ/ν Ratio** | `\|theta\| / \|vega\|` | ratio | Frontend: `scoring.ts` |
| **ATR14** | `mean(last 14 True Ranges)` | $ | `calculator.py:compute_atr14()` |
| **DTE** | Days to expiration | days | — |

---

## Per-Ticker Regime Labels

Computed in `scorer.py`. Drives recommendation overrides but does **not** modify the composite score.

| Regime | Trigger | Effect |
|--------|---------|--------|
| **DANGER** | Term slope > 1.15 | Recommendation → AVOID regardless of score |
| **CAUTION** | Term slope > 1.05, OR (IV Rank > 90 AND RV accel > 1.1) | Score ≥ 55 → REDUCE SIZE, else → NO EDGE |
| **NORMAL** | Default | Score determines recommendation |

---

## Dashboard Regime Labels (NBA-Themed)

Computed in `RegimeBanner.tsx` from per-ticker regime data. Independent of backend's `RegimeSummary`.

| Regime | Trigger | Posture |
|--------|---------|---------|
| **OFF SEASON** | > 40% of eligible tickers in DANGER | No trading |
| **REGULAR SEASON** | > 25% in DANGER or CAUTION | Defined-risk only, reduced sizing |
| **THE FINALS** | Avg VRP > 8 AND avg term slope < 0.90 | Widest edge — be aggressive |
| **THE PLAYOFFS** | Default | Normal — execute playbook |

---

## Recommendation Labels

| Backend label | Frontend display | Meaning |
|---------------|------------------|---------|
| SELL PREMIUM | SELL | Score ≥ 65, NORMAL regime — strong edge |
| CONDITIONAL | CONDITIONAL | Score 45–64, NORMAL — decent edge, trade with discipline |
| REDUCE SIZE | AVOID | CAUTION regime + score ≥ 55 — edge exists but conditions risky |
| AVOID | AVOID | DANGER regime — do not sell premium |
| NO EDGE | NO EDGE | Score < 45 (NORMAL) or < 55 (CAUTION) — insufficient edge |
| NO DATA | NO DATA | Insufficient liquid contracts for IV computation |
| *(frontend only)* | SKIP | Earnings DTE ≤ 14 — hard gate, score forced to 0 |

---

## Position Terms

| Term | Meaning |
|------|---------|
| **Delta (Δ)** | Option's sensitivity to underlying price. 25Δ put ≈ 25% probability of finishing ITM. Lower delta = more OTM = more room for error. |
| **Iron Condor** | Short call spread + short put spread. Defined risk, profits if underlying stays in range. |
| **Strangle** | Short OTM call + short OTM put. Undefined risk, higher premium. |
| **Jade Lizard** | Short put + short call spread. Eliminates upside risk of a strangle. |
| **Put Credit Spread** | Short put + long put at lower strike. Defined risk, directionally neutral to bullish. |
| **Defined Risk** | Max loss known at entry (spreads, condors). Required in CAUTION regime. |

---

## Key Thresholds Quick Reference

| Threshold | Value | Where | Purpose |
|-----------|-------|-------|---------|
| VRP ratio dead zone | 1.15 | `scorer.py` | Below this, VRP Quality scores 0 |
| VRP ratio cap | 1.60 | `scorer.py` | Above this, VRP Quality maxes at 30 |
| IV Percentile floor | 30th | `scorer.py` | Below this, IV Pct scores 0 |
| SELL threshold | Score ≥ 65 | `scorer.py` | Recommendation: SELL PREMIUM |
| CONDITIONAL threshold | Score ≥ 45 | `scorer.py` | Recommendation: CONDITIONAL |
| Negative VRP cap | Score ≤ 44 | `scorer.py` | Below CONDITIONAL threshold |
| DANGER trigger | Slope > 1.15 | `scorer.py` | Per-ticker regime |
| CAUTION trigger | Slope > 1.05 | `scorer.py` | Per-ticker regime |
| Earnings gate | DTE ≤ 14 | `scoring.ts` (frontend) | Forces score to 0 |
| Sizing: Half | RV accel > 1.10 | `scoring.ts` (frontend) | Reduce position size |
| Sizing: Quarter | RV accel > 1.20 | `scoring.ts` (frontend) | Minimal exposure |
| ATM range | ±3% of spot | `calculator.py` | Strike filter for ATM IV |
| Min ATM contracts | 3 | `calculator.py` | Below this → NO DATA |
| Max spread ratio | 50% | `calculator.py` | Liquidity filter |
| Max IV | 200% | `calculator.py` | Garbage data rejection |
| Rate limit | 10 calls/min | `main.py` | MarketData.app throttle |
