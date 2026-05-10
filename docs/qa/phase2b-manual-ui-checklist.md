# Phase 2B Manual UI Checklist

Run after any change to `scoring.ts`, `types.ts`, `Leaderboard.tsx`, `DetailPanel.tsx`, `page.tsx`.

## Earnings warnings

- [ ] **Non-ETF with TBD earnings** (e.g. WMT/MCD/CAT showing "TBD" historically) renders a yellow `Date unverified` chip on the leaderboard action area (desktop and mobile).
- [ ] DetailPanel for a TBD ticker shows the cautionary prose block: **"Earnings date unverified."** + detail prose, between metrics grid and IV/RV chart.
- [ ] **FMP/Yahoo drift > 5d** (override `earningsVerification.checks` in DevTools to inject a `diff_days: 7` row): chip reads `Date conflict`; DetailPanel block reads **"Earnings date conflict."** with the absolute day-count.
- [ ] **ETF row** (SPY/QQQ/etc.) never shows either chip or block, regardless of injected `earnings_dte`.
- [ ] **Earnings-gated row** (DTE ≤ 14, non-ETF) still shows red SKIP chip as primary state. The Phase-1 ⚠ DTE chevron in the earnings cell still appears (driven by `earningsGateActive`).

## DANGER vs CAUTION display split

- [ ] **DANGER + AVOID** row (slope > 1.15): leaderboard chip is red **AVOID**.
- [ ] **CAUTION + score ≥ 55** row: leaderboard chip is amber **REDUCE SIZE** (not red AVOID).
- [ ] **CAUTION + score < 55** row: chip is gray **NO EDGE** plus a small amber **CAUTION** sub-pill next to it.
- [ ] DetailPanel header AVOID prose differentiates: DANGER reads "Avoid — term structure is in DANGER…"; CAUTION reads "Caution — structure is less clean. If traded at all, use defined-risk only."

## Phase-1 regression

- [ ] **WATCHLIST** chip still purple/accent; DetailPanel still hides Position Construction.
- [ ] **Thin Premium** badge still appears on CONDITIONAL with `1.15 ≤ vrp_ratio < 1.25`.
- [ ] **DEGRADED scan banner** still shows above regime banner when `scan_quality === "DEGRADED"`; SELL/CONDITIONAL/WATCHLIST rows still display as NO EDGE on a degraded scan.
- [ ] Suppressed rows still expose the audit-trail block in DetailPanel ("Raw signal suppressed because scan data is degraded…").

## Layout

- [ ] Mobile card chip row uses `flex-wrap` and never horizontally overflows. With max chip stack (Earnings warning + Caution + Thin Premium + Sizing + ActionChip), the row wraps cleanly to a second line on narrow viewports.
- [ ] Desktop table action cell uses `flex-wrap` and tooltips on hover.
- [ ] Both light and dark themes render the new yellow chips/blocks legibly.

## Producing test scans

To force any of the new states without waiting for live data, use DevTools → Network → "Override response" on `/api/scan/latest`:
- TBD: set a row's `earnings_dte: null`, `is_etf: false`.
- Conflict: keep `earningsVerification.checks` mocked with `diff_days: 7` for a target ticker.
- DEGRADED: set `scan_quality: "DEGRADED"`, `scan_quality_reason: "test"`.
