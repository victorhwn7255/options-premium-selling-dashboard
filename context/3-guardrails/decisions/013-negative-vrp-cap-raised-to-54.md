---
last_verified: 2026-07-04
verified_against: c203544 (working tree — ships with the 2026-07 scoring update)
status: active
supersedes: 004-negative-vrp-cap-at-44.md
---

# ADR-013: Negative VRP Cap Raised to 54 (Supersedes ADR-004)

## Context

ADR-004 capped negative-VRP scores at 44 — one point below CONDITIONAL (45) — so no negative-VRP
ticker could reach a tradeable recommendation through other strong components. Two things changed:

1. **The VRP-Ratio Actionability Gate now exists** (post-QA, `scorer.py`): any SELL/CONDITIONAL
   recommendation with vrp_ratio < 1.15 is demoted to WATCHLIST with no position construction.
   Negative VRP implies vrp_ratio < 1.0 < 1.15, so ADR-004's protection concern is structurally
   covered — twice.
2. **The 2026-07 backtest** (`docs/strategy-backtest-2026-07.md`) found that negative-VRP
   ticker-days whose other components summed to 45–64 traded at PF 2.62 (n=113) — better than the
   SELL cohort itself. The 44 cap was destroying ranking information that ADR-004 explicitly
   wanted to preserve "for monitoring purposes".

## Decision

`score = min(score, 54)` — one point below the CAUTION REDUCE-SIZE bar (55) and well below SELL
(65), mirroring ADR-004's threshold-minus-one pattern. Score visibility improves for monitoring;
the recommendation remains non-tradeable regardless (WATCHLIST via the VRP-ratio gate).

## Alternatives Considered

**Keep 44.** Ignores that the ratio gate now provides the actual protection, and keeps compressing
the 45–64 quality band into a bucket indistinguishable from genuinely weak names.

**Remove the cap entirely (let the ratio gate do everything).** The backtest cohort was one bull
year; a SELL-labeled negative-VRP name (even as WATCHLIST) misleads the leaderboard's visual
hierarchy. The cap still communicates "core thesis absent".

**Make negative-VRP names CONDITIONAL-tradeable.** Rejected as over-fitting a single regime —
selling insurance priced below realized risk is thesis-inverted, whatever one year of data says.

## Consequences

**Makes easy:** Post-vol-spike names (IV normalizing faster than stale RV30) surface with honest
scores for monitoring, exactly the ADR-004 goal. Semantics unchanged: negative VRP is never
tradeable.

**Makes hard:** Score continuity — negative-VRP names can display up to 10 points higher from
2026-07-04. Anyone comparing against pre-July history must account for it
(`references/change-logs.md`).

## Revisit If

- The REDUCE-SIZE threshold (55) or CONDITIONAL threshold (45) changes — keep cap = 55 − 1.
- The VRP-Ratio Actionability Gate is ever removed — the cap must then drop back below 45.
