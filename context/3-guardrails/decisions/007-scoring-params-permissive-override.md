---
last_verified: 2026-04-16
verified_against: 2134cff
status: active
---

# ADR-007: ScoringParams Permissive Override

## Context

`ScoringParams` is a dataclass in `scorer.py` with defaults: `min_iv_rank=60`, `min_vrp=3.0`, `max_rv_accel=1.15`, `max_skew=15.0`, `only_contango=True`. These were designed as pre-filters — tickers failing them would be excluded before scoring.

In `run_full_scan()` (`main.py:309–313`), the params are overridden with permissive values: `min_iv_rank=0`, `min_vrp=-999`, `max_rv_accel=999`, `max_skew=999`, `only_contango=False`. This effectively disables all filters.

## Decision

Keep the permissive override. All tickers pass through to scoring. The composite score and regime system handle differentiation — there is no pre-filter stage.

## Alternatives Considered

**Remove ScoringParams entirely.** Clean but would break the function signature and any future use of per-scan filter customization (e.g., a future UI filter panel).

**Use the defaults.** Would exclude tickers with IV Rank < 60 or VRP < 3 from the leaderboard entirely. Rejected because users want to see all tickers — the NO EDGE / low-score tickers serve as context (watching a ticker with score 30 today that might be 65 tomorrow).

## Consequences

**Makes easy:** Every ticker in UNIVERSE appears on the dashboard. No hidden exclusions.

**Makes hard:** The `ScoringParams` dataclass is dead weight in the runtime path — it's carried through but has no effect. A contributor might waste time tuning its defaults without realizing they're overridden.

## Revisit If

- A filter UI is added that lets users narrow the leaderboard by IV rank, VRP, etc. The params infrastructure is already there — just wire it to user input instead of hardcoded permissive values.
