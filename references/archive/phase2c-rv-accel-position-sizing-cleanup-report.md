# Theta Harvest Phase 2C RV Acceleration / Position Sizing Cleanup Report

## 1. Summary

This was an **interpretation, copy, and display-layer cleanup**. The dashboard no longer prescribes Full / Half / Quarter position sizes from RV Acceleration. Instead, the frontend renders an **RV Accel Status** chip (Excellent / Good / Acceptable / Caution / Avoid · Wait) that classifies the **cleanliness of the volatility environment**. Actual position size is now framed as a trader-controlled decision recorded in the trade journal — not something the scanner prescribes.

**No scoring logic, weight, gate, or threshold was changed.** RV Acceleration's contribution to the RV Stability score (0–15 pts) is unchanged. The composite formula, recommendation thresholds, regime triggers, earnings gate, negative VRP cap, VRP-ratio gate, Thin Premium threshold, and degraded-scan suppression all behave identically to Phase 2B.

The change is documentation + frontend display copy + one frontend rename (`sizing` → `rvAccelStatus`) + one backend description string. No backend logic, scoring code, or API field shape changed.

## 2. Files Changed

| File | Change |
|---|---|
| `references/metrics.md` | RV Acceleration §2: replaced "Sizing impact (frontend)" with the 5-tier Status table + "not used to prescribe size" note. ATR-14 §10: "Position sizing reference" → "Strike-width / stop reference". §Position Sizing (frontend) subsection rewritten as "RV Acceleration Status (frontend display)". REGULAR SEASON market-regime row: "reduced sizing" → "demand cleaner setups". |
| `references/strategy.md` | RV Stability §4: removed the "drives position sizing" Full/Half/Quarter list, replaced with RV Acceleration Status chip pointer. Position Construction's old "Position Sizing" subsection replaced with "RV Acceleration Interpretation" + 5-tier table + trade-journal note. Daily Workflow item 4 rewritten — "Check sizing… Don't override" → "Check RV Acceleration status… record actual size in the trade journal". |
| `context/1-domain/scoring-and-strategy.md` | Scope bullet "Position construction and sizing logic" → "Position construction and the RV Acceleration Status display". Design-principles paragraph updated to reference trader-controlled sizing in trade journal. "Position Sizing" §H replaced with "RV Acceleration Status (display)" §H + audit paragraph explaining the Phase-2C removal. Backend-vs-Frontend table row "Position sizing (Full/Half/Quarter)" → "RV Acceleration Status (5-tier display label)". |
| `context/1-domain/glossary.md` | Threshold table rows "Sizing: Half" / "Sizing: Quarter" relabeled to "RV Accel Status: Caution" / "RV Accel Status: Avoid / Wait" (same RV-Accel thresholds). |
| `context/2-system/architecture.md` | Transform-pipeline ASCII diagram: replaced Sizing line with "RV Accel Status — 5-tier label — display only". Ownership-boundary table row "Position sizing (Full/Half/Quarter)" → "RV Accel Status (5-tier display label)". |
| `frontend/src/lib/types.ts` | New `RvAccelStatusLabel` union + `RvAccelStatus` interface. `DashboardTicker.sizing?: string` → `DashboardTicker.rvAccelStatus?: RvAccelStatus` with explanatory comment. |
| `frontend/src/lib/scoring.ts` | New exported `getRvAccelStatus(accel)` helper returning the 5-tier status. Replaced the in-line `let sizing = 'Full' / 'Half' / 'Quarter'` block with a single `getRvAccelStatus(rvAccel)` call. Renamed return field. |
| `frontend/src/components/Leaderboard.tsx` | Replaced `SizingChip` with `RvAccelStatusChip`. Chip surfaces only on Caution / Avoid · Wait (mirrors prior Half/Quarter visibility). Tooltip + label "RV Caution" / "RV Avoid / Wait". Code comment "RV Accel + sizing" → "RV Accel". |
| `frontend/src/components/DetailPanel.tsx` | Replaced `SizingChip` with `RvAccelStatusChip` in the header chip row. Position Construction "Sizing" tile (½ / ¼ / Standard) → "RV Accel Status" tile showing the label + description. Added tile-row footer note "Position size is a trader-controlled decision — record it in your trade journal." |
| `frontend/src/components/RegimeGuideModal.tsx` | REGULAR SEASON do/don'ts rewritten ("Cut position size to Half or Quarter" removed; "Demand a clean RV Accel status" + "Ignore the RV Accel status — if it says Caution or Avoid / Wait, wait" added). REGULAR SEASON example tile "Sizing: Half" → "RV Accel: Caution"; THE PLAYOFFS example tile "Sizing: Full" → "RV Accel: Good"; THE FINALS example tile "Sizing: Full" → "RV Accel: Excellent"; narrative prose updated correspondingly. THE PLAYOFFS dos/donts: "Use Full or Half sizing as indicated by the sizing chip" → "Confirm the RV Accel status is Acceptable or better"; "Size up beyond what the system recommends" → "Override your own position-sizing discipline because conditions are calm — record every entry's contract count in the trade journal". THE FINALS dos: "Use Full sizing on tickers scoring ≥ 50" → "Trade tickers scoring ≥ 50 when RV Accel status confirms a clean environment". |
| `frontend/src/components/RegimeBanner.tsx` | REGULAR SEASON detail string: "reduced sizing" → "demand cleaner setups before entering". |
| `frontend/src/lib/metrics-content.ts` | RV Acceleration card: tag "Speed gauge" → "Environment cleanliness". Explain text rewritten to drop the "drives position sizing" phrasing. Readings replaced with the 5-tier status labels. Position Sizing card (id `position-sizing`) repurposed as `vol-environment-status` ("RV Accel Status" / "Volatility environment"); explain prose, formulas, and readings rewritten to reflect the cleanliness framing. |
| `frontend/src/app/page.tsx` | Methodology footer line "Sizing: Full if RV Accel < 1.10, Half if < 1.20, Quarter above" → "RV Accel Status: informational only — Excellent / Good / Acceptable / Caution / Avoid·Wait classifies environment cleanliness, never prescribes position size." |
| `backend/main.py` | CAUTION market-regime description string: "Rising realized vol — tighten position sizing, favor defined-risk structures" → "Rising realized vol — environment less clean, favor defined-risk structures and require strong confirmation". (Display-only string; not used in any logic path.) |
| `tasks/todo.md` | Replaced stale daily-grid plan with Phase 2C plan + acceptance criteria. |

## 3. Documentation Updates

### `references/metrics.md`
- §2 RV Acceleration: removed "Sizing impact (frontend)" line; added the 5-tier Status table; added the "RV Acceleration is not used to prescribe position size" callout. Formula and 0–15-point scoring impact preserved verbatim.
- §10 ATR-14: clarified usage as "strike-width / stop-loss reference" rather than "position sizing reference". Scoring impact unchanged (still display-only).
- §"Position Sizing (frontend, based on RV Acceleration)" subsection rewritten as "RV Acceleration Status (frontend display)" with the same 5 tiers and an explicit closing line: *"Actual position size is a trader-controlled decision recorded in the trade journal."*
- Market-regime row REGULAR SEASON: "reduced sizing" → "demand cleaner setups".

### `references/strategy.md`
- §"4. RV Stability": kept the 0–15 scoring table; removed the "This metric also drives **position sizing**" Full/Half/Quarter list; replaced with a pointer to the new "RV Acceleration Interpretation" section.
- New §RV Acceleration Interpretation (replaces the old Position Sizing section under Position Construction). Contains the 5-tier action-bias table verbatim from the spec, plus the trade-journal note.
- Daily Workflow item 4 rewritten in the new framing.
- The pre-existing line *"The scoring system identifies opportunities. Position sizing, stop losses, and portfolio Greeks management are the trader's responsibility."* (§Edge Decay) was already aligned with Phase 2C and was kept verbatim.

### `context/1-domain/scoring-and-strategy.md`
- Scope bullet, design-principles paragraph, Position-Sizing section, and Backend-vs-Frontend table updated as listed above. Audit note explains *why* the Full/Half/Quarter prescription was removed.

### `context/1-domain/glossary.md`
- Threshold table relabeled (same RV-Accel thresholds, new "RV Accel Status: Caution / Avoid · Wait" labels).

### `context/2-system/architecture.md`
- Transform-pipeline diagram + ownership-boundary table updated to reflect the rename.

## 4. Frontend Updates

### Old sizing chip removed
- `Leaderboard.tsx` and `DetailPanel.tsx` no longer reference `Full` / `Half` / `Quarter`. Both components now use a single shared visual treatment (`RvAccelStatusChip`) that shows only on Caution / Avoid · Wait.

### New labels / fields / hidden fields
- `DashboardTicker.sizing?: string` removed; `DashboardTicker.rvAccelStatus?: RvAccelStatus` added.
- `getRvAccelStatus(accel)` is exported from `scoring.ts` and used by both the Leaderboard chip and the DetailPanel Position-Construction tile.
- DetailPanel Position Construction grid still has 4 tiles (Target Delta, Structure, DTE, **RV Accel Status**); the old "Sizing" tile (½ / ¼ / Standard) is gone.
- Backend fields `suggested_max_notional` and the `notional` string ("0%", "1–2% portfolio", "2–5% portfolio", "2–3% portfolio") are **left in place** per the spec ("do not remove backend fields if doing so causes broad API churn"). They are produced by `backend/scorer.py` and consumed by Pydantic `TickerResult`. The frontend currently does not surface these strings as a position-size prescription on the dashboard. They remain available for downstream consumers (CSV export, scan-history, future trade-journal export, etc.).

### Chip / label inventory
- `RvAccelStatusChip` (new) — Leaderboard.tsx + DetailPanel.tsx.
- "RV Accel Status" tile inside Position Construction grid — DetailPanel.tsx.
- Methodology-footer copy and metrics modal copy now describe the status framing.

## 5. Trade Journal

There is **no trade-journal module** in this repository. `grep -ri 'trade journal'` matched only documentation references that were just added in this phase.

Phase 2C therefore did **not** add or modify a trade-journal module. The new copy in `references/strategy.md`, `references/metrics.md`, `frontend/src/components/DetailPanel.tsx` (the new "Position size is a trader-controlled decision — record it in your trade journal" footnote), and `RegimeGuideModal.tsx` reframes position sizing as a trader-controlled, journal-recorded decision so the language is correct when a trade journal is eventually added.

Trade-journal **build was deliberately deferred** — out of Phase-2C scope.

## 6. Grep Results

| Pattern | Match count | Allowed remainders |
|---|---|---|
| `Full size` | 3 | All in `history/daily-briefings.md` (Apr-09 through Apr-15 entries — immutable historical scan logs that describe the dashboard's prior behavior on those days). |
| `Half size` | 1 | `history/daily-briefings.md` (Apr-13 entry, same reason). |
| `Quarter size` | 1 | `history/daily-briefings.md` (Mar-25 entry, same reason). |
| `Sizing impact` | 0 | — clean. |
| `Position Sizing` | 11 | All in historical Phase-1 / Phase-2A / Phase-2B / QA-report / dashboard-behavior-qa-report files (audit trail), and the **new** Phase-2C `references/strategy.md:260` line ("The scoring system identifies opportunities. Position sizing… is the trader's responsibility") which is the *correct* framing for Phase-2C. The `context/1-domain/scoring-and-strategy.md` match is the new "trader-controlled position sizing (recorded in the trade journal)" line. |
| `Accel ≤ 1.10` / `Accel <= 1.10` | 1 | `frontend/src/lib/scoring.ts:13` — the new `getRvAccelStatus()` helper boundary (Acceptable bin). Expected. |
| `Accel 1.10` | 0 | — clean. |
| `Accel > 1.20` | 4 | `references/dashboard-behavior-qa-report.md` (×3 — historical P2 audit findings, immutable) and `context/2-system/architecture.md` reference within the historical narrative — but the live diagram now reads "RV Accel Status" (the QA-report match describes the prior P2 issue exactly). |

**Bottom line:** every active dashboard-facing surface and every live documentation surface is on the new framing. Remaining matches are either (a) immutable history-of-record files, (b) the new helper function's threshold boundary, (c) the 2026 QA reports that describe the prior state, or (d) the new Phase-2C-aligned framing of "position sizing is the trader's responsibility".

## 7. Test Results

| Command | Result |
|---|---|
| `cd frontend && npx tsc --noEmit` | **Pass** (zero errors) |
| `python backend/test_qa_phase1.py` | **Pass** — 13 / 13 |
| `python backend/test_qa_phase1_regression.py` | **Pass** — 17 / 17 |
| `python backend/test_qa_phase2a_integration.py` | **Pass** — 3 / 3 |
| `python backend/test_calculator.py` | **Pass** — 5 / 5 |
| `python scripts/phase1_historical_replay.py` | **Pass** — Section G empty (zero unexpected SELL/CONDITIONAL downgrades across 28 scan days) |

Total: **38 backend tests pass, frontend typecheck clean, replay byte-stable.**

## 8. Confirmation of Unchanged Logic

| Item | Changed? |
|---|---|
| RV Acceleration formula | No |
| RV Stability scoring formula | No |
| Composite score weights (30 / 25 / 20 / 15 / 10) | No |
| SELL threshold (≥ 65) | No |
| CONDITIONAL threshold (≥ 45) | No |
| VRP-ratio WATCHLIST gate (< 1.15) | No |
| Thin Premium threshold (1.15 ≤ ratio < 1.25) | No |
| Earnings gate (DTE ≤ 14, frontend-only, ETF-exempt) | No |
| Negative VRP cap (44) | No |
| DANGER / CAUTION term-structure logic | No |
| Skew scoring (trapezoid 0/7/12/20) | No |
| WATCHLIST behavior | No |
| Degraded-scan detection + suppression | No |
| `suggested_max_notional` API field | No (kept; not displayed as a sizing prescription) |
| Trade-journal capability | n/a (no trade-journal module exists; deferred) |

## 9. Final Verdict

**Phase 2C complete.**

- Dashboard no longer prescribes Full / Half / Quarter sizing.
- RV Acceleration is described as environment cleanliness across `metrics.md`, `strategy.md`, `scoring-and-strategy.md`, `glossary.md`, `architecture.md`, and the dashboard UI (Leaderboard chip, DetailPanel chip + tile, Regime Guide examples, page footer, metrics modal).
- All scoring logic, weights, gates, thresholds, and regime rules are byte-identical to Phase 2B.
- All 38 backend tests pass, frontend typechecks, historical replay produces identical Section G (empty).
- No trade-journal module exists, so no trade-journal changes were attempted; new copy is written so the framing is correct when one is eventually added.
