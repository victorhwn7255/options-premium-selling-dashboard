---
last_verified: 2026-04-16
verified_against: 2134cff
status: active
---

# ADR-001: Single-Source Scoring (Backend Only)

## Context

The composite score (0–100) could be computed in the backend, the frontend, or both. Early versions had a frontend `computeScore()` function in `scoring.ts` that independently calculated scores using a different formula (VRP magnitude 0–40, term structure 0–25, IV percentile 0–20, minus RV accel penalty 0–15). The backend had its own scorer. The two formulas diverged silently — a ticker could show different scores depending on which path was read.

## Decision

The backend is the single source of truth for the composite score. `scorer.py:score_opportunity()` computes it. The frontend passes through `signal_score` unchanged (except for the earnings gate override, which is a display-layer concern — see ADR-003). The frontend's `computeScore()` was removed and replaced with `convertApiTicker()`, which maps backend fields to display types without recomputing.

## Alternatives Considered

**Dual computation with reconciliation.** Compute in both, flag discrepancies. Rejected: adds complexity without benefit — if the two disagree, you still have to pick one.

**Frontend-only scoring.** Move all scoring to the client. Rejected: scoring depends on IV Rank from 252-day SQLite history, which is not sent to the frontend. Sending the full history would bloat the API response.

## Consequences

**Makes easy:** Score interpretation is unambiguous. One formula, one number, one code path to audit.

**Makes hard:** Frontend can't adjust scoring logic without a backend deploy. Acceptable — scoring changes should be deliberate and version-controlled, not hot-patchable.

## Revisit If

- Frontend needs to score hypothetical scenarios (e.g., "what if VRP were 2 points higher?") — would require sending the scoring function or its parameters to the client.
