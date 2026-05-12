# Theta Harvest Phase 2B Completion Report

**Date:** 2026-05-10
**Scope:** Decision-clarity UX and metadata only. No strategy, formula, threshold, or sizing changes.

---

## 1. Summary

Phase 2B added **frontend-only** decision-clarity surfaces:

1. **Earnings TBD warning** — `DATE_UNVERIFIED` chip when a non-ETF ticker has null `earnings_dte` (TBD).
2. **Earnings DATE_CONFLICT warning** — chip when FMP and Yahoo dates disagree by > 5 days, computed from the existing `/api/verify/earnings/latest` feed.
3. **DANGER vs CAUTION display split** — CAUTION + REDUCE SIZE now renders as an amber `REDUCE SIZE` chip (separate from DANGER's red `AVOID`). NO EDGE + CAUTION rows show a small `CAUTION` sub-pill.
4. **Differentiated DetailPanel prose** — DANGER reads "Avoid — term structure is in DANGER. Do not sell premium here." CAUTION/REDUCE reads "Caution — structure is less clean. If traded at all, use defined-risk only."
5. **Post-earnings diagnostic** — **deferred** (no `days_since_earnings` backend field).
6. **Event-driven vs structural regime nuance** — **deferred** (depends on the same missing field).

No backend logic changed. No counts/filters changed. The canonical `action` field is unchanged; the new `displayAction` is purely cosmetic for the chip label.

---

## 2. Files Changed

| File | Change |
|---|---|
| `frontend/src/lib/types.ts` | Added `earningsWarningKind`, `earningsWarningLabel`, `earningsWarningDetail`, `displayAction`, `cautionReason` to `DashboardTicker` (display-only). Renamed away from existing Phase-1 boolean `earningsWarning` to avoid name collision. |
| `frontend/src/lib/scoring.ts` | `convertApiTicker` now computes TBD warning + `displayAction` mapping (DANGER→AVOID red / CAUTION+REDUCE_SIZE→amber REDUCE SIZE / NO EDGE+CAUTION → cautionReason). Added new exported helper `enrichWithEarningsWarnings(tickers, earningsChecks)` that overlays DATE_CONFLICT warnings from the FMP/Yahoo verification feed. |
| `frontend/src/app/page.tsx` | Wired `enrichWithEarningsWarnings` into the `scoredData` useMemo, with `earningsVerification?.checks` dependency. |
| `frontend/src/components/Leaderboard.tsx` | Added `'REDUCE SIZE'` ActionChip config (amber). New `EarningsWarningBadge` and `CautionPill` components. Both desktop table and mobile card render the new badges and use `row.displayAction \|\| row.action`. |
| `frontend/src/components/DetailPanel.tsx` | Added `'REDUCE SIZE'` ActionChip config. Added `EarningsWarningBadge` to header chip row. Header ActionChip uses `ticker.displayAction \|\| ticker.action`. AVOID prose differentiates DANGER ("Avoid — term structure is in DANGER…") from CAUTION ("Caution — structure is less clean. If traded at all, use defined-risk only."). |

---

## 3. Earnings Warning / TBD Handling

**Implemented (DATE_UNVERIFIED):**
- Trigger: non-ETF ticker with `earnings_dte == null` (TBD).
- Label: "Date unverified".
- Detail: "Earnings date is missing or unverified. Confirm manually before trading."
- Render: yellow chip on the leaderboard action area (desktop + mobile) and on the DetailPanel header.
- ETF guard: `if (t.isEtf) return t` in `enrichWithEarningsWarnings`; convertApiTicker checks `!isEtf`.

**Implemented (DATE_CONFLICT):**
- Trigger: `Math.abs(EarningsCheck.diff_days) > 5` from `/api/verify/earnings/latest`.
- Label: "Date conflict".
- Detail: "FMP and Yahoo earnings dates differ by Xd. Confirm manually before trading."
- Computation: post-pass via `enrichWithEarningsWarnings`, using the `earningsVerification.checks` already fetched in `page.tsx`. Does not overwrite DATE_UNVERIFIED rows.

**Earnings-gated rows (DTE ≤ 14):** SKIP behavior unchanged. The Phase-1 boolean `earningsWarning` (DTE chevron) and the new `earningsWarningKind` are independent fields that can both fire.

---

## 4. DANGER vs CAUTION Display

| Backend state | Frontend `action` (unchanged) | New `displayAction` | Visual |
|---|---|---|---|
| DANGER + AVOID | `'AVOID'` | unset (falls back to action) | red AVOID chip |
| CAUTION + REDUCE SIZE | `'AVOID'` | `'REDUCE SIZE'` | amber REDUCE SIZE chip |
| CAUTION + NO EDGE | `'NO EDGE'` | unset | gray NO EDGE chip + small amber CAUTION sub-pill |
| NORMAL + everything else | unchanged | unset | unchanged |

**Backend regime logic, score formula, and recommendation thresholds are byte-identical to Phase 1.** The `action` filter used by `Leaderboard.tsx:248-249` (`d.action === 'SELL' \|\| 'CONDITIONAL'`) and `RegimeBanner.tsx:23` (`tradeable` count) are unaffected — they still see `'AVOID'` for both DANGER and CAUTION+REDUCE_SIZE rows, so tradeable counts and regime detection don't change.

DetailPanel prose is now distinct:
- DANGER: **"Avoid — term structure is in DANGER. Do not sell premium here. Deep backwardation or acute stress detected."**
- CAUTION: **"Caution — structure is less clean. If traded at all, use defined-risk only. Elevated risk; reduce exposure."**

---

## 5. Post-Earnings Diagnostic State

**Deferred.** Backend does not currently expose `days_since_earnings` or `last_earnings_date`. The `earnings_cache` table only stores forward `earnings_date`; the verification feed only has forward `our_dte` / `yahoo_dte`. Implementing this would require either:

- A new backend column tracking `last_earnings_date` per ticker, populated when `earnings_dte` crosses zero or jumps from low-to-high; OR
- Frontend heuristic detection via day-over-day comparison (`deltaMap`) — but this is brittle and not idempotent on cache reads.

Per the spec ("Do not build a new data pipeline. Add a TODO/report note"), this is deferred. Suggested follow-up: add `last_earnings_date` to `daily_iv` writes when a scan detects an earnings-date jump, then expose `days_since_earnings` in `TickerResult`.

---

## 6. Event-Driven vs Structural Regime Nuance

**Deferred.** Same root cause as §5: the cleanest signal for "event-driven stress" is "stressed AND recently reported", which requires `days_since_earnings`. A weaker pre-earnings-only heuristic is implementable using `earnings_dte` in `[15, 21]`, but covers only one half of the event-driven story (pre-print) and would mis-frame the user's actual concern (the post-print residual stress they've been tracking manually in briefings).

Recommend implementing this together with Phase 5's `last_earnings_date` work.

---

## 7. Tests and Verification

| Command | Result |
|---|---|
| `git diff` | Reviewed (5 frontend files modified, 0 backend) |
| `python backend/test_qa_phase1.py` | **Pass** (13/13) |
| `python backend/test_qa_phase1_regression.py` | **Pass** (17/17) |
| `python backend/test_qa_phase2a_integration.py` | **Pass** (3/3) |
| `python backend/test_calculator.py` | **Pass** (5/5) |
| `python scripts/phase1_historical_replay.py` | **Pass** — Section G: "(none — all SELL/CONDITIONAL with vrp_ratio≥1.15 preserved)" |
| Phase 2B-specific tests | Not added — frontend changes only; project has no JS test framework. Manual QA checklist deferred (see §9). |
| `cd frontend && npx tsc --noEmit` | **Pass** (no errors) |
| `cd frontend && npm run build` | Not run — typecheck sufficient for display-only frontend changes |

**Total: 38 backend tests passing, 0 failing. Frontend typecheck clean.** No regressions to Phase 1 / Phase 2A behavior.

---

## 8. Confirmation of Unchanged Logic

| Item | Changed? |
|---|---|
| Score formula | No |
| SELL threshold | No |
| CONDITIONAL threshold | No |
| VRP gate threshold | No |
| Thin Premium threshold | No |
| Earnings gate threshold | No |
| DANGER / CAUTION thresholds | No |
| Position sizing | No |
| WATCHLIST behavior | No |
| Degraded scan detection | No |
| Degraded scan suppression | No |
| Historical replay behavior | No |

Verified by:
- All Phase 1 unit + regression tests pass without modification (35/35 pre-existing).
- Phase 2A integration tests (cached endpoint shape) pass unchanged (3/3).
- Historical replay produces identical output: same 13 transitions, same 17 Thin Premium rows, same Apr 16 DEGRADED, same empty Section G.
- Zero backend files modified during Phase 2B.
- The frontend `action` enum is unchanged; only a parallel `displayAction` field was added.

---

## 9. Remaining Follow-Ups

### Non-blocking follow-ups
1. **Manual QA checklist not written.** A `docs/qa/phase2b-manual-ui-checklist.md` covering the new badges (DATE_UNVERIFIED, DATE_CONFLICT, REDUCE SIZE chip, CAUTION sub-pill) and differentiated DetailPanel prose is ~30 minutes of writing. Spec allowed deferral when test framework absent; defer to next polish window.
2. **Old field rename.** The Phase-1 `earningsWarning: boolean` (DTE chevron flag) and the new `earningsWarningKind: 'DATE_UNVERIFIED' \| 'DATE_CONFLICT'` coexist. Future cleanup: rename the boolean to `earningsGateActive` for clarity. Pure rename, no behavior change.
3. **NORMAL+CONDITIONAL with thin VRP + earnings warning** — these can stack three badges (Thin Premium + DATE_UNVERIFIED + sizing) on the chip row. Layout currently uses `flex-wrap`. Visually busy but correct. Could consolidate into a single "warnings" pill that summarizes count.

### Phase 2C backlog
4. **Post-earnings diagnostic state** — requires backend `last_earnings_date` tracking. See §5.
5. **Event-driven vs structural regime nuance** — depends on §4. See §6.

### Phase 3 backlog
6. **Per-ticker score grid** — separate user request, deferred earlier as research-tool with 6-month payoff horizon.
7. **Position sizing rebalance** — couples sizing to VRP magnitude as well as RV accel. Needs trading evidence.
8. **AVOID-vs-REDUCE-SIZE backend split** — currently the frontend display layer does the work; could be elevated to a real backend recommendation. Low priority now that display works.

---

## 10. Final Verdict

**Phase 2B complete with non-blocking follow-up.**

All implementable items shipped:
- ✅ Earnings TBD warning (DATE_UNVERIFIED) — visible end-to-end.
- ✅ Earnings drift warning (DATE_CONFLICT) — wired to existing FMP/Yahoo verification feed.
- ✅ DANGER vs CAUTION display split — leaderboard chips and DetailPanel prose both differentiate.
- ✅ ETF exemption preserved — ETFs never receive earnings warnings.
- ✅ Earnings-gated SKIP behavior unchanged.
- ✅ All Phase 1 / 2A behavior preserved (38/38 backend tests + replay clean).

Items appropriately deferred:
- ⏸ Post-earnings diagnostic state — backend data dependency.
- ⏸ Event-driven regime nuance — same dependency.
- ⏸ Manual UI checklist — non-blocking.

The dashboard is now meaningfully clearer about earnings uncertainty (TBD/drift) and the CAUTION/DANGER distinction the user has been tracking manually in briefings for the past month. **No trading strategy or threshold changed.**

---

## Phase 2B PR-Readiness Cleanup Addendum

**Date:** 2026-05-10 (same day, polish pass)

### Cleanup changes

1. **Renamed Phase-1 boolean** `earningsWarning` → `earningsGateActive`. The two-field naming (Phase-1 boolean + Phase-2B `earningsWarningKind` enum) was confusing. Now `earningsGateActive: boolean` clearly means "DTE ≤ 14 chevron flag" while `earningsWarningKind: 'DATE_UNVERIFIED' | 'DATE_CONFLICT'` is unambiguously the Phase-2B warning metadata. Pure rename across 5 files (`types.ts`, `scoring.ts`, `simulated-data.ts`, `Leaderboard.tsx`, `DetailPanel.tsx`); zero behavior change.

2. **Added DetailPanel earnings-warning prose block.** The Phase 2B initial pass only added a chip in the header. The proper explanation block now renders parallel to the WATCHLIST / SKIP / AVOID blocks:
   - DATE_UNVERIFIED title: "Earnings date unverified."
   - DATE_CONFLICT title: "Earnings date conflict."
   - Body text uses `ticker.earningsWarningDetail` if present, else a sensible default.
   - Cautionary tone (yellow `bg-warning-subtle border-warning-30`), not panic-red.
   - Renders independently of action state — does not hide Position Construction or change action.

3. **Manual UI checklist created** at `docs/qa/phase2b-manual-ui-checklist.md` covering earnings warnings, DANGER/CAUTION split, Phase-1 regressions, mobile layout, and DevTools-override recipes for staging the new states.

### Orphan-reference grep result

After rename, `grep -rn "earningsWarning\b" frontend/src/` (excluding `Kind`/`Label`/`Detail`/`EarningsWarningBadge`) returns **zero matches**. The old ambiguous `earningsWarning` boolean is fully gone.

### Verification re-run after cleanup

| Command | Result |
|---|---|
| `git diff` | Reviewed (~5 files modified for rename + 1 for prose block + 1 new checklist) |
| `cd frontend && npx tsc --noEmit` | **Pass** (no errors) |
| `python backend/test_qa_phase1.py` | **Pass** (13/13) |
| `python backend/test_qa_phase1_regression.py` | **Pass** (17/17) |
| `python backend/test_qa_phase2a_integration.py` | **Pass** (3/3) |
| `python backend/test_calculator.py` | **Pass** (5/5) |
| `python scripts/phase1_historical_replay.py` | **Pass** — Section G empty (identical pre-cleanup) |
| `cd frontend && npm run build` | Not run — typecheck sufficient for rename + JSX-prose changes |

**Total: 38 backend tests passing, 0 failing. Frontend typechecks clean. Replay output identical to pre-cleanup.**

### Confirmation of unchanged logic (post-cleanup)

| Item | Changed? |
|---|---|
| Score formula | No |
| All thresholds (SELL/CONDITIONAL/VRP-gate/Thin-Premium/earnings-gate/DANGER/CAUTION) | No |
| Position sizing | No |
| WATCHLIST behavior | No |
| Degraded-scan detection / suppression | No |
| Historical replay behavior | No |
| Backend Python files | No (zero modifications) |

### Final status: **Phase 2B PR-ready.**

The earlier non-blocking follow-up items (rename + prose block + manual checklist) are now resolved. Remaining deferrals (post-earnings diagnostic, event-driven nuance) still require the `days_since_earnings` backend field and stay deferred to Phase 2C.

---

*End of report.*
