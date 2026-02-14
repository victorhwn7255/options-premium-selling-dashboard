# Investigate & Fix: Earnings-Gated Tickers Contaminating Market Regime Aggregation

## Problem

Tickers that are gated out by the earnings proximity filter (score=0, action=SKIP/Earnings) still contribute their term_slope to the regime-level AVG TERM SLOPE metric displayed in the RegimeBanner. For example, WMT has earnings in 5 days and shows extreme backwardation (term_slope=1.71) purely from event-driven IV elevation — but this 1.71 gets averaged into the market regime calculation, inflating avgTermSlope and potentially triggering HOSTILE when the broader market may actually be NORMAL or CAUTION.

The regime should reflect the *tradeable* universe, not the full scan universe.

## Tasks

### 1. Trace the regime aggregation pipeline end-to-end

Start from `RegimeBanner.tsx` — find where `avgTermSlope`, `avgVRP`, `rvAccel`, and the backwardation count are computed. Then check the backend in `main.py` where `RegimeSummary` is built in `run_full_scan()`. Identify whether both paths (frontend client-side and backend) have this same contamination issue.

### 2. Check if earnings-gated tickers are excluded from any of these aggregations

Specifically: when the frontend `computeScore()` in `scoring.ts` sets score=0 for earnings ≤14d, does the regime calculation in `RegimeBanner.tsx` still include that ticker's term_slope, VRP, and RV accel in the averages?

### 3. Propose and implement a fix

Exclude earnings-gated tickers (earnings ≤14 days) from the regime aggregation metrics:

- `avgTermSlope`
- `avgVRP`
- `avgRVAccel`
- `backwardation count`
- `TRADEABLE` denominator

Show me the specific code changes needed in both frontend and backend.

### 4. Handle edge cases

What happens if ALL tickers are earnings-gated? The regime should fall back to NORMAL or show "insufficient data" rather than dividing by zero. Guard against this in both frontend and backend.
