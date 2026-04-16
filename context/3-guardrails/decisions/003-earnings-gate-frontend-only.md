---
last_verified: 2026-04-16
verified_against: 2134cff
status: active
---

# ADR-003: Earnings Gate Is Frontend-Only

## Context

The 14-day earnings gate (DTE ≤ 14 → score forced to 0, action = SKIP) could live in the backend scorer or the frontend transform layer. The backend computes the score; the frontend displays it. The gate needs earnings_dte, which the backend already has.

## Decision

The earnings gate lives in the frontend (`scoring.ts:convertApiTicker()`, lines 33–39). The backend sends the full computed score and recommendation without any earnings adjustment. The frontend overrides: `score = 0`, `action = "SKIP"`, and preserves the original score as `preGateScore` for display.

## Alternatives Considered

**Backend gate.** Apply the gate in `scorer.py` before returning the recommendation. Rejected because:
1. The `preGateScore` display pattern (showing the underlying quality so users can monitor for post-earnings opportunities) requires both the gated and ungated scores. Backend would need to return both fields.
2. Earnings dates shift frequently (FMP drift, Yahoo overrides). Frontend gating means a date correction in the cached scan result takes effect on the next page load without re-running the scorer.
3. ETF exclusion from the gate is a display concern — ETFs don't have earnings. The backend shouldn't need to know display logic.

**Both.** Gate in backend AND frontend. Rejected: redundant, and the backend gate would mask the preGateScore information.

## Consequences

**Makes easy:** Backend scoring is pure edge measurement. The earnings gate is a separate safety layer with its own UX (SKIP badge, preGateScore display). Earnings date corrections take effect immediately.

**Makes hard:** A consumer of the raw API (`/api/scan/latest`) sees ungated scores — a ticker with score 80 and earnings_dte = 5 would appear as SELL PREMIUM. Any API consumer must implement their own earnings gate. Acceptable for a single-user dashboard with no external API consumers.

## Revisit If

- The API is exposed to third-party consumers who expect gated scores.
- The preGateScore display pattern is dropped (no longer need both values).
