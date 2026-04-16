---
last_verified: 2026-04-16
verified_against: dc030c3
status: active
---

# ADR-010: Holiday Calendar Duplicated in Frontend and Backend

## Context

The US market holiday calendar (10 holidays, observation rules, Easter via Gregorian algorithm) exists in two independent implementations: Python in `main.py:_us_market_holidays()` (lines 619–671) and JavaScript in `Navbar.tsx` (lines 44–91). They compute the same holidays with the same rules.

## Decision

Keep both. The backend needs the calendar for scan gating (cron skip, manual scan rejection) and CSV date logic. The frontend needs it for display (non-trading-day badge, scan-window status, market-closed indicator) without an API round-trip.

## Alternatives Considered

**Backend-only via API endpoint** (e.g., `GET /api/is-trading-day`). Would eliminate the frontend copy. Rejected because:
1. The frontend checks trading-day status on every page load and on a timer — an API call per check adds latency to a display-only decision.
2. If the backend is down, the frontend would lose its ability to show "Market Closed" — a degradation in the exact situation where the information matters most.
3. The holiday calendar is stable (10 fixed holidays per year) with near-zero maintenance cost.

**Shared package.** Extract the calendar into a shared npm/pip package or a JSON config. Adds build-system complexity for 50 lines of pure datetime math that changes never.

## Consequences

**Makes easy:** Frontend shows trading-day status instantly, even when backend is unreachable. No API dependency for a display concern.

**Makes hard:** If a new holiday is added (unlikely — NYSE holiday calendar changes are rare and announced years in advance), both implementations must be updated. A contributor might update one and forget the other.

## Revisit If

- NYSE changes its holiday calendar (last change: Juneteenth added in 2022).
- The frontend needs more calendar intelligence (e.g., early-close days, which are not currently tracked in either implementation).
