---
last_verified: 2026-04-16
verified_against: 2134cff
status: active
---

# ADR-009: Sequential Scan (Semaphore=1)

## Context

The scan iterates 33 tickers. Each ticker requires 4–5 API calls. With `asyncio.gather()`, tickers could run concurrently. However, the rate limiter is set to 10 calls/min (see ADR-005), and each call must acquire a token before executing.

## Decision

`asyncio.Semaphore(1)` in `run_full_scan()` (`main.py:320`). Despite using `asyncio.gather()` for the task structure, only one ticker scans at a time. This is effectively sequential execution with async I/O.

## Alternatives Considered

**Semaphore(2–3) for modest concurrency.** Would allow 2–3 tickers to have API calls in-flight simultaneously. Rejected because the token-bucket rate limiter serializes the actual HTTP calls anyway — the semaphore just determines how many tickers are *waiting* at the rate limiter. With 4–5 calls per ticker and a 6-second interval between calls, a second concurrent ticker would just queue behind the first at the limiter, adding complexity without speed improvement.

**No semaphore, rely on rate limiter alone.** Would work but produces bursty behavior — all 33 tickers would immediately try to make their first call, creating a queue of 33 pending rate-limiter acquisitions. Sequential processing creates a steady, predictable flow.

## Consequences

**Makes easy:** Deterministic scan order, simple progress tracking (`_scan_progress` shows one ticker at a time), predictable timing (~13 min for 33 tickers).

**Makes hard:** No speedup possible without also increasing the rate limit. The semaphore and rate limit are coupled decisions.

## Revisit If

- Rate limit is increased (see ADR-005) — at 50/min, Semaphore(3–4) with concurrent ticker processing would cut scan time significantly.
