# Bug: Stock Split Creates Fake RV Spike in Historical Charts

## The Problem

NFLX did a 10-for-1 stock split on Nov 17, 2025. Pre-split price: ~$1,100. Post-split price: ~$110.

Our price history database has **unadjusted** pre-split prices sitting next to **post-split** prices. When the RV calculator hits the split boundary, it sees:

```
log_return = ln(110 / 1100) = ln(0.1) = -2.302
```

That looks like a -230% single-day crash. Annualized, it produces RV values of ~657 — which is what we see in the NFLX "IV vs RV — 120 Day" chart as a massive orange spike around Nov 6-17.

**This is not a real market event.** IV stayed flat at ~30.5 through the spike, which proves the options data was properly OCC-adjusted but the stock price data was not.

## Why It Matters

- Historical RV chart is wildly wrong for any ticker that has split within the lookback window
- If a split happened within the last 30 trading days, RV30 would be corrupted and VRP/scoring would break
- NFLX split was ~3 months ago so current RV10/RV30 are clean, but the chart is misleading

## What To Fix

1. **Find where historical close prices are stored** — check `daily_iv` table, `data/quotes/`, and `data/daily/` CSVs
2. **Find where prices are fetched** — check `backfill.py` and the daily scan pipeline for how they call MarketData.app
3. **Determine if the API supports split-adjusted prices** — look for an `adjusted=true` parameter or similar
4. **Fix the data source** to always use split-adjusted closes
5. **Backfill corrected data** for any affected tickers (at minimum NFLX, but check the full universe for other recent splits)
6. **Verify the fix** by confirming the NFLX RV chart no longer shows the ~657 spike around Nov 17

## Scope

This is a **data pipeline fix**, not a calculator fix. The RV formula in `calculator.py` is correct — it's being fed bad prices. Don't change the math, fix the input data.
