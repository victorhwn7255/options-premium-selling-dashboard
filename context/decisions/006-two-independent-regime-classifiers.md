---
last_verified: 2026-04-16
verified_against: 2134cff
status: active
---

# ADR-006: Two Independent Regime Classifiers

## Context

The backend computes a market-wide regime (`RegimeSummary` in `main.py`): ELEVATED RISK / CAUTION / OPPORTUNITY / NORMAL. The frontend computes its own regime (`computeRegime()` in `RegimeBanner.tsx`): OFF SEASON / REGULAR SEASON / THE PLAYOFFS / THE FINALS. These use different thresholds, different input aggregations, and different names. The frontend ignores the backend's `overall_regime` field.

## Decision

Keep both. The backend regime uses Phase-1 logic (avg IV rank, danger count ≥ 2, SPY slope as VIX proxy) and serves as a stored historical record in `scan_results`. The frontend regime uses per-ticker regime percentages and aggregate VRP, designed for display and trader decision-making.

## Alternatives Considered

**Unify into backend only.** The frontend would display the backend's regime. Rejected because the frontend regime uses a fundamentally different aggregation (percentage of tickers in DANGER vs. absolute count ≥ 2) that better reflects the market-wide picture for a 33-ticker universe. The backend's "danger ≥ 2" threshold was tuned for a 15-ticker universe and hasn't been updated.

**Unify into frontend only.** Remove backend regime computation. Rejected because the backend regime is stored in `scan_results` JSON and provides historical regime tracking that predates the frontend rewrite.

**Update backend to match frontend logic.** Would require migrating the frontend's NBA-themed names and percentage thresholds into Python, and updating all historical `scan_results` for consistency. High effort, low payoff — the stored backend regime is never displayed to the user.

## Consequences

**Makes easy:** Each classifier can evolve independently. The frontend regime can be tuned for UX without touching the backend.

**Makes hard:** A new contributor reading the API response sees `regime.overall_regime = "NORMAL"` while the dashboard shows "THE PLAYOFFS" — confusing until they understand the two are independent. This ADR exists to prevent someone from "fixing" the mismatch.

## Revisit If

- The backend regime is exposed to external consumers who expect it to match the dashboard.
- The historical regime data in `scan_results` is needed for backtesting — at that point, unifying and backfilling may be worth the cost.
