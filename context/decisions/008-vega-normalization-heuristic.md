---
last_verified: 2026-04-16
verified_against: 2134cff
status: active
---

# ADR-008: Vega Normalization by Magnitude Threshold

## Context

MarketData.app intermittently returns vega in two conventions: **per-1%-IV** (values ~0.01–5.0 for US equities) and **raw BSM** (per-1.0 sigma change, values ~100× larger). The switch is undocumented and has been observed to flip between consecutive API calls on the same day (confirmed 2026-04-15). The θ/ν ratio and any future vega-dependent logic require a consistent convention.

## Decision

Autodetect by magnitude: if `|vega| > 5`, divide by 100. Implemented in `calculator.py:_normalize_vega()` (lines 320–329). The threshold of 5 is based on the physical constraint that per-1%-IV vega for any US equity option is bounded below ~5 (it would require an implausibly high-gamma, deep-ITM, long-dated contract to exceed this).

Theta is not normalized — it uses a consistent per-day convention from the API.

## Alternatives Considered

**Flag and skip.** If vega looks anomalous, set it to None. Rejected: this would make θ/ν ratio unavailable on the days the API flips, which might be most days for some tickers.

**Normalize based on contract characteristics.** Compute expected vega from BSM given the strike, DTE, and IV, then compare to the API value to determine the convention. More principled but adds complexity and a BSM dependency to what should be a simple data-cleaning step.

**Contact MarketData.app for a fix.** Ideal long-term but the issue is intermittent and hard to reproduce in a support ticket.

## Consequences

**Makes easy:** θ/ν ratio is always available and always in a consistent scale.

**Makes hard:** If the ATM contract selection changes (e.g., wider strike range or longer DTE), a legitimate per-1% vega could approach the threshold. See [fragile-seams.md § Vega convention instability](../fragile-seams.md#vega-convention-instability).

## Revisit If

- MarketData.app documents their vega convention or confirms they've fixed the inconsistency.
- A contract is found where per-1%-IV vega legitimately exceeds 5.
