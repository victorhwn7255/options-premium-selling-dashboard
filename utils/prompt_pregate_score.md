# Implement Pre-Gate Score Display for Earnings-Gated Tickers

## Problem

When the earnings gate fires (earnings ≤14 days), the scoring function sets the score to 0 and action to SKIP/Earnings. This is correct for safety, but it destroys useful information — the trader can't tell whether a gated ticker has strong underlying metrics worth watching post-earnings.

Example: NVDA currently shows score=0 with "Earnings in 11d", but its pre-gate metrics are strong (VRP 14.0, term slope 0.86 contango). A trader wants to know "Should I sell premium on NVDA the morning after earnings?" The dashboard can't answer that today.

## Before Writing Any Code

Read and understand these files first — the implementation must match the current codebase, not assumptions:

1. **Scoring logic:** Find the scoring function (likely in `frontend/src/lib/` somewhere). Read how the earnings gate works — where it short-circuits, what it returns, and the full return type/interface.
2. **Type definitions:** Find the TypeScript interfaces for scored ticker data. Understand the shape of the object that flows from scoring → components.
3. **Leaderboard component:** Find the component that renders the score pill and action chip for each ticker row. Read how it currently handles earnings-gated tickers vs normal tickers.
4. **Detail panel component:** Find the component that shows expanded info for a selected ticker. Read what score/action info it displays.
5. **Page-level data flow:** Find the main page component that calls the scoring function and passes data to the leaderboard/detail components. Understand how scored data flows through.

## What to Implement

### Scoring function changes

1. Restructure the earnings gate so the full score is computed first (VRP + term structure + IV percentile + RV accel penalty), THEN the earnings gate is applied afterward
2. When the earnings gate fires, keep the final score at 0 and action as SKIP/Earnings, but also return the pre-gate computed score as a new field (e.g., `preGateScore`)
3. Update the relevant TypeScript interface to include this optional field — it should only be present when the earnings gate fired

### Leaderboard display changes

For earnings-gated tickers (where `preGateScore` exists and is > 0):
- Keep the score pill showing 0 with current styling
- Add the pre-gate score next to it in muted/dimmed text, e.g., `0 (52)`
- Use the same color logic as normal scores (green ≥70, yellow ≥50, gray otherwise) but at reduced opacity to signal "hypothetical"

For non-earnings-gated tickers or where preGateScore is 0: no change.

### Detail panel changes

If the detail panel shows score info for the selected ticker, display the pre-gate score with context like "Score without earnings gate: 52 — monitor post-earnings"

## Design

Follow the existing design system tokens already in the codebase:
- Muted text: use the tertiary text color variable
- Font: same mono font used for other data values
- Keep it compact — supplementary info, not a primary metric

## Edge Cases

- If `preGateScore` is also 0 or negative, don't show the parenthetical — "0 (0)" adds no value
- `preGateScore` must NOT influence regime aggregation, sorting, TRADEABLE count, or any other computation — it is display-only
- The "Earnings in Xd" action chip should remain unchanged
- Verify the existing earnings gate threshold by reading the code — don't assume it's 14 days
