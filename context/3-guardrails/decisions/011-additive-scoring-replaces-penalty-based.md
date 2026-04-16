---
last_verified: 2026-04-16
verified_against: dc030c3
status: active
---

# ADR-011: Additive Scoring Replaces Penalty-Based

## Context

The Phase-1 scorer (`scorer.py` prior to v1.08) used a penalty-based model: it started with positive contributions from VRP and IV Rank, then subtracted penalties for backwardation (-5 to -35), high RV acceleration (-8 to -15), low VRP (-10), and low IV Rank (-10). Regime detection was entangled with scoring — a DANGER regime subtracted 35 points directly from the composite score.

This caused two problems:

1. **Score conflated edge measurement with risk adjustment.** A ticker with excellent VRP and IV conditions but mild backwardation (slope 1.02) lost 20 points, making it impossible to distinguish "good edge in cautious conditions" from "mediocre edge in normal conditions." Both showed the same score.

2. **Cliff effects from penalties.** The boundary between 0 and -8 for RV acceleration happened at exactly 1.05. A ticker at accel 1.049 scored 8 points higher than one at 1.051 — a difference invisible in the underlying data but dramatic in the output. This turned measurement noise into score instability.

## Decision

Replace penalty-based scoring with a purely additive model. Five components (VRP Quality, IV Percentile, Term Structure, RV Stability, Skew) each contribute 0 to their maximum, never negative. Regime detection is separated entirely from the score — it drives recommendation and sizing overrides but does not modify the numeric score. All component functions are continuous and piecewise-linear with no cliffs.

## Alternatives Considered

**Keep penalties but smooth them.** Would fix cliff effects but not the conflation problem. A score of 55 would still be ambiguous between "great edge minus regime penalty" and "moderate edge with no penalty."

**Multiplicative model** (score = VRP_factor × IV_factor × ...). Appealing mathematically but creates a different problem: a single zero factor (e.g., VRP ratio below threshold) zeros the entire score, losing information about the other components. The additive model degrades gracefully — zero VRP points still allows other components to signal partial edge.

**Weighted ensemble with regime as a separate dimension.** This is conceptually what we arrived at, but formalized as a simple sum rather than a weighted average, because equal-scale components (each 0 to max) make the weights implicit in the max-point allocation (VRP gets 30 out of 100 = 30% weight).

## Consequences

**Makes easy:** Reading the score. A score of 72 means "72 points of edge present." Comparing two tickers is straightforward. Diagnosing why a ticker scored low is a matter of checking which component is near zero.

**Makes hard:** Expressing "this ticker has great metrics but the environment is dangerous." The score shows the edge; the regime shows the risk. Users must read both. The UI addresses this with regime badges, flags, and recommendation overrides (DANGER → AVOID regardless of score).

**Locks in:** The 0-100 scale and the 30/25/20/15/10 weight allocation. Changing max points per component requires recalibrating all recommendation thresholds (65 for SELL, 45 for CONDITIONAL).

## Revisit If

- Users consistently report that a high score in DANGER regime is confusing (suggests the two-axis model isn't working as a UX pattern).
- A new scoring component is added that interacts non-additively with existing ones (e.g., a correlation penalty that should reduce the total when two tickers are highly correlated).
