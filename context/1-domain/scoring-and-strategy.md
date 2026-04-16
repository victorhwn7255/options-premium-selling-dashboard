---
last_verified: 2026-04-16
verified_against: dc030c3
rot_risk: high
rot_triggers:
  - backend/scorer.py
  - backend/calculator.py
  - frontend/src/lib/scoring.ts
  - frontend/src/components/RegimeBanner.tsx
audience: both
---

# Scoring and Strategy

## Purpose

This file answers: **"How does a ticker go from raw market data to a SELL / SKIP / AVOID decision?"** It documents the composite scoring formula, the gates that override it, the regime system that modifies recommendations, and where each piece lives in code. It is the single source of truth for the scoring engine's current behavior.

For the trading *strategy* behind these choices (when to trade, daily workflow, position management), see [`references/strategy.md`](../../references/strategy.md). For the *academic rationale* behind the formula's shape (why VRP ratio, why a dead zone at 1.15, why close-to-close RV), see [`1-domain/methodology.md`](methodology.md). For domain term definitions, see [`1-domain/glossary.md`](glossary.md).

## Scope

**This file covers:**
- The 5 scoring components with exact formulas and breakpoints
- The 3 gates that cap or zero-out the score
- Per-ticker regime detection and how it overrides recommendations
- Dashboard-level market regime (frontend-computed)
- Position construction and sizing logic
- Which code owns which piece (backend vs. frontend)

**This file does NOT cover:**
- Academic basis for VRP or why specific approximations were chosen — see `1-domain/methodology.md`
- Known fragile areas in the scoring pipeline — see `3-guardrails/fragile-seams.md`
- Strategy thesis, daily workflow, position management rules — see `references/strategy.md`
- Metric formulas (how ATM IV is interpolated, how RV is computed) — see `references/metrics_report.md`
- Deliberate design decisions (why earnings gate is frontend-only, why negative VRP cap is 44) — see `3-guardrails/decisions/`

---

## Composite Scoring Formula

The scoring engine lives in `backend/scorer.py` (`score_opportunity()`). It produces a single integer from 0 to 100 per ticker, representing **premium-selling edge quality** — not risk, not expected return, just how favorable the conditions are for selling options on this name right now.

### Design principles

The score is **purely additive**. There are no penalties that subtract from the total, no multipliers, no regime-based deductions. Every component contributes 0 to its maximum — a ticker with weak skew gets 0 skew points, not negative points. This replaced an earlier penalty-based scorer — see [ADR-011](../3-guardrails/decisions/011-additive-scoring-replaces-penalty-based.md) for the rationale. The additive design means the score has a clean interpretation: it answers "how much edge is present?" without conflating edge measurement with risk adjustment. Risk adjustment happens separately through the regime system and position sizing.

The score also has **no cliff effects**. Every component is continuous and piecewise-linear. A VRP ratio of 1.14 scores 0 and a ratio of 1.16 scores a small positive number — there is no jump where a 0.01 change in one input swings the score by 10 points. This matters because the underlying data has measurement noise (ATM IV interpolation, thin option chains, RV window sensitivity), and cliff effects would turn input noise into output instability.

### The five components

**VRP Quality (0–30 points)** — *"Is there premium edge?"*

The largest single component, because VRP is the core thesis: implied volatility systematically overstates realized volatility, and that gap is the edge. The input is the VRP ratio (`iv_current / rv30`), not the absolute VRP spread, because the ratio normalizes across vol regimes — a 5-point VRP spread means very different things when RV is 10% vs. 40%.

The dead zone below ratio 1.15 exists because a 15% markup over realized vol is marginal after transaction costs (bid-ask spread on entry and exit, assignment risk, margin costs). Below this threshold the component contributes nothing. From 1.15 to 1.60, points scale linearly to 30. Above 1.60, points cap at 30 — the additional edge from a 2.0 ratio vs. a 1.6 ratio is real but diminishing, and overfitting to extreme values adds no practical signal.

```
vrp_score = clamp(0, 30, (vrp_ratio - 1.15) × 66.67)
```

**IV Percentile (0–25 points)** — *"Are options expensive relative to their own history?"*

Measures where current 30-day ATM IV sits relative to the past 252 trading days. IV Percentile (count-based: "what fraction of days had lower IV?") is used instead of IV Rank (min-max normalization) because percentile is robust to outlier spikes — a single day of extreme IV doesn't distort the entire scale. IV Rank is still computed and used for regime detection and position construction, but not for scoring.

The floor at the 30th percentile means options that are cheaper than 70% of the past year get zero points. Selling cheap options is a losing proposition even if other metrics look favorable.

```
iv_pct_score = clamp(0, 25, (iv_percentile - 30) × 0.357)
```

**Term Structure (0–20 points)** — *"Is the market structure favorable?"*

Compares front-month IV to back-month IV. The normal state is contango (slope < 1.0): longer-dated options have higher IV because more time means more uncertainty. Backwardation (slope > 1.0) means near-term options are more expensive than longer-dated ones — the market is pricing an acute near-term event. Premium sellers get crushed in backwardation because the "overpriced" near-term options often turn out to be correctly priced or underpriced.

The scoring has three regimes, hinged at 0.85, 1.0, and 1.15:

- Deep contango (slope ≤ 0.85) → 20 points. Ideal conditions.
- Contango to flat (0.85 < slope ≤ 1.0) → 5 to 20, linear. Flat (1.0) earns 5 points, not zero — a flat term structure is neutral, not bearish for premium sellers.
- Backwardation (1.0 < slope < 1.15) → 0 to 5, tapering linearly. Mild backwardation still contributes something because transient inversions happen around expiration cycles without signaling systemic stress.
- Deep backwardation (slope ≥ 1.15) → 0 points.

```
if slope ≤ 0.85:       20
elif slope ≤ 1.0:      5 + (1.0 - slope) / 0.15 × 15
elif slope < 1.15:     5 × (1.15 - slope) / 0.15
else:                  0
```

**RV Stability (0–15 points)** — *"Is realized volatility stable or accelerating?"*

RV Acceleration is `rv10 / rv30` — the ratio of short-term to medium-term realized vol. Below 1.0, recent vol is lower than the 30-day average (decelerating — favorable). Above 1.0, vol is rising. The concern is that accelerating RV often leads IV higher, closing the VRP gap that the score just measured as attractive. Scoring a ticker highly on VRP while its RV is spiking is a recipe for entering just as the edge evaporates.

The structure mirrors term structure scoring: a two-segment piecewise linear with a hinge at 1.0.

- Accel ≤ 0.85 → 15 points (vol strongly decelerating)
- 0.85 < accel ≤ 1.0 → 10 to 15, linear
- 1.0 < accel < 1.15 → 0 to 10, linear
- Accel ≥ 1.15 → 0 points

```
if accel ≤ 0.85:       15
elif accel ≤ 1.0:      10 + (1.0 - accel) / 0.15 × 5
elif accel < 1.15:     10 × (1.15 - accel) / 0.15
else:                  0
```

**Skew (0–10 points)** — *"Is there put demand to harvest?"*

25-delta put skew is the IV of 25-delta puts minus ATM IV. Positive skew means downside protection is more expensive than ATM options — this is normal and represents the "insurance premium" that flows to premium sellers. The scoring is a trapezoid:

- Negative skew → 0. Inverted skew (puts cheaper than ATM) is abnormal and offers no put premium to harvest.
- 0 to 7 → linear ramp from 0 to 10. Moderate demand building.
- 7 to 12 → plateau at 10. The sweet spot: steady institutional hedging demand creates reliable premium without signaling informed directional flow.
- 12 to 20 → taper from 10 to 0. Extreme skew may reflect informed protection buying (someone knows something), making the "insurance" less likely to be overpriced.
- Above 20 → 0.

```
if skew < 0:           0
elif skew ≤ 7:         skew / 7 × 10
elif skew ≤ 12:        10
elif skew ≤ 20:        10 × (20 - skew) / 8
else:                  0
```

### Total

```
score = int(clamp(0, 100, vrp + iv_pct + term + rv + skew))
```

The theoretical maximum is 100 (30 + 25 + 20 + 15 + 10). Reaching 85+ requires near-maximum contributions from all five components simultaneously — wide VRP, high IV percentile, deep contango, decelerating RV, and moderate skew. Empirically, across 41 scans (1,317 ticker-scores as of 2026-04-16): scores above 85 occurred 3 times (0.2%), above 75 occurred 22 times (1.7%), and above 65 (SELL threshold) occurred 100 times (7.6%). The highest observed score is 93.

---

## Gates

Three gates can override the composite score. They are evaluated independently — a ticker can be affected by multiple gates, though in practice the first one that fires determines the outcome.

**Negative VRP gate** — backend, `scorer.py`

When VRP is negative (realized vol exceeds implied vol), the core thesis does not hold — there is no premium edge to harvest. The gate caps the composite score at 44, one point below the CONDITIONAL threshold of 45. This ensures that even if all other components are strong (deep contango, high IV percentile, moderate skew), a negative-VRP ticker cannot reach a tradeable recommendation. The cap is at 44 specifically, not 0, so the score still reflects the quality of other conditions — useful for monitoring tickers that might become attractive once VRP turns positive. See [ADR-004](../3-guardrails/decisions/004-negative-vrp-cap-at-44.md) for why 44 and not 45.

**No-data gate** — backend, `scorer.py`

If `iv_current` is `None` (the liquidity filter in `calculator.py` found fewer than 3 liquid ATM contracts near 30 DTE), the scorer returns immediately with `signal_score=0` and `recommendation="NO DATA"`. No components are evaluated. This is preferred over computing from rejected low-quality contracts — see [ADR-002](../3-guardrails/decisions/002-no-data-over-computed-from-rejected.md).

**Earnings gate** — frontend only, `scoring.ts`

If a non-ETF ticker has `earnings_dte ≤ 14`, the frontend overrides the backend score to 0 and sets `action="SKIP"`. The original backend score is preserved as `preGateScore` for display (so users can see the underlying quality for post-earnings monitoring). The backend has no knowledge of this gate — it sends the full computed score. See [ADR-003](../3-guardrails/decisions/003-earnings-gate-frontend-only.md) for why this lives in the frontend.

---

## Per-Ticker Regime Detection

Regime detection is **separate from scoring** — it does not modify the numeric score. Instead, it overrides the recommendation that maps from the score. This separation is the core design choice of [ADR-011](../3-guardrails/decisions/011-additive-scoring-replaces-penalty-based.md).

Detection runs in `scorer.py` after scoring, using term structure slope and the IV Rank + RV acceleration combination:

| Regime | Trigger | Effect on recommendation |
|--------|---------|--------------------------|
| **DANGER** | Term slope > 1.15 | Always → AVOID, regardless of score |
| **CAUTION** | Term slope > 1.05, OR (IV Rank > 90 AND RV accel > 1.1) | Score ≥ 55 → REDUCE SIZE; else → NO EDGE |
| **NORMAL** | Default (neither trigger fires) | Score determines recommendation normally |

The CAUTION trigger has two independent paths. The slope path catches structural backwardation. The IV Rank + RV acceleration path catches a different danger pattern: extreme IV coupled with rising realized vol, which signals a potential regime shift (not just elevated fear) even when the term structure hasn't inverted yet.

DANGER and CAUTION flags are inserted at position 0 in the flags array so they appear first in the UI.

---

## Recommendation Logic

The recommendation combines score and regime into a single action label. This is the **backend's final output** per ticker — the frontend maps these to display labels but does not alter the logic.

```
DANGER regime       → "AVOID"
CAUTION + score≥55  → "REDUCE SIZE"
CAUTION + score<55  → "NO EDGE"
NORMAL  + score≥65  → "SELL PREMIUM"
NORMAL  + score≥45  → "CONDITIONAL"
NORMAL  + score<45  → "NO EDGE"
iv_current is None  → "NO DATA"
```

The frontend maps these for display: "SELL PREMIUM" → "SELL", "REDUCE SIZE" → "AVOID" (same visual treatment as DANGER-triggered AVOID). The full mapping is in `scoring.ts:mapRecommendation()`.

---

## Position Construction

When a ticker qualifies (recommendation is SELL PREMIUM, CONDITIONAL, or REDUCE SIZE), the backend provides position construction hints. These are **suggestions, not orders** — the trader applies judgment and their own risk framework.

Construction is keyed on regime first, then IV Rank and VRP:

| Condition | Delta | Structure | DTE | Notional |
|-----------|-------|-----------|-----|----------|
| DANGER | N/A | No position | N/A | 0% |
| CAUTION | 10–15Δ | Iron condor or wide put spread (defined risk) | 21–30 DTE | 1–2% |
| NORMAL, IV Rank ≥ 80, VRP > 8 | 16–20Δ | Short strangle or jade lizard | 30–45 DTE | 2–5% |
| NORMAL, IV Rank ≥ 80, VRP > 4 | 16–20Δ | Iron condor or put credit spread | 30–45 DTE | 2–5% |
| NORMAL, IV Rank ≥ 80, VRP ≤ 4 | 16–20Δ | Put credit spread (strict width) | 30–45 DTE | 2–5% |
| NORMAL, IV Rank < 80 | 20–30Δ | Put credit spread, narrow | 45–60 DTE | 2–3% |

The logic lives in `scorer.py` (lines 229–254). Note that IV Rank drives position construction even though it's not used in scoring — it indicates *how fat* the premium is in absolute terms, which affects how aggressively you can structure the trade.

---

## Position Sizing

Sizing is **frontend-computed** in `scoring.ts`, based solely on RV Acceleration:

| RV Acceleration | Sizing | Rationale |
|-----------------|--------|-----------|
| ≤ 1.10 | Full | Vol stable or decelerating — standard allocation |
| 1.10–1.20 | Half | Vol rising — reduce exposure |
| > 1.20 | Quarter | Vol spiking — minimal exposure |

This is independent of the score and recommendation. A ticker with SELL PREMIUM and a score of 80 still gets Half sizing if RV accel is 1.15. The sizing chip appears next to the action chip in the leaderboard.

---

## Dashboard-Level Market Regime

The frontend computes an **overall market regime** from the per-ticker data. This is a separate classifier from the backend's `RegimeSummary` — see [ADR-006](../3-guardrails/decisions/006-two-independent-regime-classifiers.md).

Computation lives in `RegimeBanner.tsx:computeRegime()`. It first excludes earnings-gated (SKIP) and NO DATA tickers as they would contaminate aggregate metrics. From the eligible set:

| Regime | Trigger | Posture |
|--------|---------|---------|
| **OFF SEASON** | > 40% of eligible tickers in DANGER | No trading. Systemic stress. |
| **REGULAR SEASON** | > 25% of eligible tickers in DANGER or CAUTION | Defined-risk only, reduced sizing |
| **THE FINALS** | Avg VRP > 8 AND avg term slope < 0.90 | Widest statistical edge. Be aggressive. |
| **THE PLAYOFFS** | Default (none of above) | Normal. Execute standard playbook. |

Hierarchy: OFF SEASON > REGULAR SEASON > THE FINALS > THE PLAYOFFS. The regime banner displays four aggregate metrics (avg VRP, avg term slope, avg RV accel, tradeable count) with good/bad thresholds for quick visual assessment.

---

## Backend vs. Frontend Responsibility

| Responsibility | Owner | Location |
|----------------|-------|----------|
| All metric computation (RV, IV, VRP, term structure, skew) | Backend | `calculator.py` |
| Composite score (0–100) | Backend | `scorer.py` |
| Per-ticker regime (NORMAL/CAUTION/DANGER) | Backend | `scorer.py` |
| Recommendation (SELL PREMIUM, etc.) | Backend | `scorer.py` |
| Position construction hints | Backend | `scorer.py` |
| Negative VRP gate (cap at 44) | Backend | `scorer.py` |
| No-data gate (score 0) | Backend | `scorer.py` |
| Earnings gate (DTE ≤ 14 → SKIP) | **Frontend** | `scoring.ts` |
| Position sizing (Full/Half/Quarter) | **Frontend** | `scoring.ts` |
| θ/ν ratio (|theta/vega|) | **Frontend** | `scoring.ts` |
| Recommendation name mapping | **Frontend** | `scoring.ts` |
| Dashboard market regime (NBA-themed) | **Frontend** | `RegimeBanner.tsx` |

The key principle: **backend scoring is authoritative.** The frontend passes through the backend's `signal_score` and `recommendation` unchanged, except for the earnings gate override and the recommendation name mapping. The frontend never recomputes the composite score. See [ADR-001](../3-guardrails/decisions/001-single-source-scoring.md).

---

## Known Discrepancy

The methodology footer in `page.tsx` (line 216) displays a stale Phase-1 scoring formula that does not match the actual backend. See [fragile-seams.md § Stale methodology footer](../3-guardrails/fragile-seams.md#stale-methodology-footer-in-pagetsx) for details.
