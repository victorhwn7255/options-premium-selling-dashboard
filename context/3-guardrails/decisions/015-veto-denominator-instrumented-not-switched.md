---
last_verified: 2026-09-03
verified_against: Signal-Quality WS4 (working tree)
status: active
---

# ADR-015: The VRP Veto Denominator Is Instrumented, Not Switched — Test T1 Owns the Flip

## Context

v2 gates entries on the forward VRP ratio `IV30 / σ_fwd` (G4 negative-FVRP + the dead zone). The 2026-09-02 evaluation
proposed vetoing on the *richer* realized estimate, `IV30 / max(σ_fwd, RV30_trailing)`, on asymmetric-loss grounds: a
false clear costs tail, a false veto costs opportunity. Two facts argued against adopting that directly:

1. It would veto the **post-spike window** — trailing RV30 stays elevated for weeks while σ_fwd collapses — which is
   exactly the window the forward denominator exists to admit and the literature calls the richest selling state.
2. The only forward test so far (2026-08-24 audit, n = 645) had **σ_fwd losing to RV30 on MAE** (10.26 vs 9.43), so
   neither side has earned the veto by evidence.

Spec Module F already assigns this question to **Test T1** (population = ticker-days where the two denominators disagree on
eligibility; adopt the forecast denominator iff net expectancy ≥ 0 and post-spike false-blocks fall).

## Decision

Compute and persist **both** ratios every night (`daily_iv.fvrp_ratio` on σ_fwd; `daily_iv.fvrp_ratio_trail` on
`max(σ_fwd, RV30/100)` via `theta_core.fvrp_veto_ratio`), mark the rows where they disagree (`veto_disagree`), expose the
disagreement rate on `/api/shadow/summary` and the shadow line, and put the choice behind
`CONFIG["veto_denominator"] ∈ {"sigma_fwd", "max"}` **defaulted to `"sigma_fwd"`** — i.e. no behaviour change. The
z-score, O-dial and sizing always use σ_fwd regardless of the switch. The switch is flipped only by T1's registered
result plus the user's sign-off in `change-logs.md`.

## Alternatives Considered

**Switch to `max` now.** Rejected — pre-judges T1 and blocks the post-spike window on a hunch.

**Leave σ_fwd-only and wait for T1.** Rejected — T1's population would not accrue as a persisted, nightly series and the
trailing ratio would have to be reconstructed later from `rv30`; instrumenting costs two columns.

**Blend (e.g. geometric mean).** Rejected — a third, untested denominator with no owning test.

## Consequences

**Makes easy:** T1's population is a `WHERE veto_disagree = 1` query; the reason string names the active denominator
(`FVRP(max)`) so a flipped switch is visible on the badge.

**Makes hard:** Nothing today. If T1 selects `max`, the post-spike re-entry ramp (`reentry_ramp`) becomes the
mechanism for participating in that window and must be evaluated alongside.

## Revisit If

- T1 runs and records a result (`trial_registry.jsonl`, id `T1-2026-09-fvrp-denominator`).
- A third denominator (e.g. YZ21 or a HARQ-style measurement-error-aware estimate) is proposed — it needs its own
  registered test, not a CONFIG edit.
