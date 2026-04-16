---
last_verified: 2026-04-16
verified_against: dc030c3
status: active
---

# ADR-005: Rate Limit 10 Calls/Min (API Supports 50)

## Context

MarketData.app's Starter plan allows 50 API calls per minute. The scanner makes ~4–5 calls per ticker (snapshot + bars + 2 chain calls + sometimes earnings). At 50/min, a 33-ticker scan would take ~3 minutes. At 10/min, it takes ~13 minutes.

## Decision

Set the token bucket to 10 calls/min (`MarketDataClient(rate_limit=10)` in `main.py:153`). Sequential ticker processing (Semaphore=1) rather than concurrent.

## Alternatives Considered

**50/min with concurrent tickers.** Fastest possible scan but risks burst rate-limit errors (429s). The API's 50/min is a sustained average; burst tolerance is undocumented. A 429 retry loop at 50/min can cascade into a minutes-long stall that's slower than steady 10/min.

**25/min as a middle ground.** Would cut scan time to ~6 minutes. Reasonable but untested — the 10/min rate has been reliable across months of daily scans with zero 429 errors.

## Consequences

**Makes easy:** Zero rate-limit errors in production. Simple mental model: one ticker at a time, steady throughput.

**Makes hard:** 13-minute scan time. Users see progress ticking slowly. The frontend polls every 3s during a scan (~250 polls). Acceptable for a once-daily scan triggered after market close.

## Revisit If

- Scan time becomes a user pain point (e.g., needing intraday rescans).
- MarketData.app documents burst tolerance and confirms 50/min sustained is safe.
- The ticker universe grows significantly (50+ tickers would mean 25+ minute scans).
