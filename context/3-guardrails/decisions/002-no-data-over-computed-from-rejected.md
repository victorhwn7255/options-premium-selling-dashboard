---
last_verified: 2026-04-16
verified_against: dc030c3
status: active
---

# ADR-002: NO DATA Over Computed-From-Rejected Contracts

## Context

When the liquidity filter leaves fewer than 3 contracts in the ATM bucket (within 3% of spot, near 30 DTE), we must decide: attempt to compute ATM IV from whatever remains (possibly 1–2 illiquid contracts), or refuse to produce a number.

## Decision

Refuse. Set `iv_current = None`, which propagates to `signal_score = 0` and `recommendation = "NO DATA"`. The ticker appears on the dashboard with a gray badge and no position suggestion.

The threshold is `MIN_ATM_CONTRACTS = 3` in `calculator.py`. If the filtered chain has ≥ 3 ATM contracts but `compute_atm_iv()` still fails (e.g., no matching put+call at the same strike), a fallback to the unfiltered chain is attempted with a low-confidence flag.

## Alternatives Considered

**Lower the threshold to 1.** A single ATM contract's mid-price IV is dominated by its bid-ask spread. For a contract with a 40% spread ratio (our filter allows up to 50%), the IV uncertainty is ±several vol points — enough to swing the VRP component by 10+ score points.

**Compute from unfiltered contracts always.** Tried during Phase 1. Produced garbage: bid=0 contracts with theoretical IV of 80%+ inflated ATM IV, creating false SELL signals on illiquid names.

## Consequences

**Makes easy:** Every displayed score is backed by a minimum data quality floor. Users can trust that a score > 0 means the underlying data passed a liquidity check.

**Makes hard:** 1–3 tickers per scan show NO DATA (typically EEM, less liquid sector ETFs, or small-caps near earnings). These tickers are invisible to the scoring leaderboard.

## Revisit If

- A more liquid data source becomes available (e.g., OPRA direct feed) that would eliminate the thin-chain problem.
- The MIN_ATM_CONTRACTS threshold needs per-ticker tuning (e.g., index ETFs could safely use 2).
