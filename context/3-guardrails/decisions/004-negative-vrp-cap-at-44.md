---
last_verified: 2026-04-16
verified_against: dc030c3
status: active
---

# ADR-004: Negative VRP Cap at 44 (Not 45)

## Context

When VRP is negative (realized vol exceeds implied), there is no premium edge — the core thesis doesn't hold. The score must be capped below a tradeable threshold. The CONDITIONAL recommendation requires score ≥ 45.

## Decision

Cap at 44: `score = min(score, 44)` (`scorer.py`, line 212). This is one point below the CONDITIONAL threshold (45), ensuring a negative-VRP ticker can never reach a tradeable recommendation through other strong components alone.

## Alternatives Considered

**Cap at 0.** Too aggressive — destroys information. A negative-VRP ticker with strong contango, high IV percentile, and stable RV is genuinely closer to tradeable than one with weak metrics across the board. The 44-point cap preserves this ranking for monitoring purposes.

**Cap at 45 (exactly at threshold).** Off-by-one risk: if the CONDITIONAL threshold is ever lowered by 1 point during tuning, negative-VRP tickers would slip into CONDITIONAL territory without anyone noticing the gate was breached.

## Consequences

**Makes easy:** Clear semantic gap — negative VRP always means NO EDGE. The 1-point buffer is intentional safety margin against threshold tuning drift.

**Makes hard:** Nothing significant. The score range 0–44 is still useful for relative ranking of non-tradeable tickers.

## Revisit If

- The CONDITIONAL threshold changes from 45 to something else — the cap should remain at `threshold - 1`.
