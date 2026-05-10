# Theta Harvest Phase 1 Code Review Report

**Reviewer date:** 2026-05-10
**Scope:** Implementation review of QA Phase 1 fixes (VRP gate, WATCHLIST, Thin Premium, scan-quality detection, suppression).
**Disclaimer:** This review validates dashboard implementation quality and behavior alignment with the documented specs. It does not validate trading strategy profitability.

---

## 1. Executive Summary

### Overall verdict: **Ready for production**

All Phase 1 acceptance criteria pass. 35 backend tests pass (5 calculator + 13 functional + 17 regression). Historical replay across 28 scan days shows the expected 8 false positives caught (plus 5 latent ones the QA report didn't sample) with zero unexpected downgrades. Frontend typechecks cleanly. Scan-quality wiring covers every API path that returns ticker data.

### Top 3 things implemented well

1. **Score-formula isolation.** The VRP-ratio gate runs *after* the additive score is finalized and clamped (`scorer.py:215`); it changes only the `recommendation` string. `signal_score` is never mutated by the gate or by suppression. Verified by `test_raw_score_unchanged_when_watchlist` and `test_raw_score_unchanged_after_degraded_suppression`.
2. **Diagnostic preservation through suppression.** `suppress_actionable()` captures `pre_suppression_recommendation`, `pre_suppression_score`, and `scan_quality_suppression_reason` *before* downgrading the row, so the audit trail survives. The DetailPanel surfaces this as a clear red diagnostic block. AVOID / NO DATA / true-NO EDGE rows are correctly excluded from suppression.
3. **Defense-in-depth + cached-path uniformity.** `_apply_scan_quality()` is called on fresh scans AND on every cached return path (5 paths in main.py). Old SQLite rows missing the new diagnostic fields deserialize cleanly via Pydantic defaults; no DB migration required.

### Top 3 risks or issues (none blocking production)

1. **[Low / Nit]** `scripts/phase1_historical_replay.py` duplicates the threshold constants (`SLOPE_WALL_TOLERANCE = 0.001`, `NO_DATA_THRESHOLD = 4`, `VRP_GATE = 1.15`) instead of importing them from `backend/scan_quality.py`. If production thresholds change, the replay would silently drift. The replay-report reproducibility section already mentions this implicitly but the script could `from scan_quality import ...`.
2. **[Low]** Backend `scan_quality.py` is *forgiving* about how a row signals NO DATA — it counts `r.recommendation == "NO DATA"`. But the historical replay counts `iv is None OR "NO DATA" in regime_col` (broader). This led the replay to count 10 NO DATA rows for Apr 16 while pure backend logic (post-deserialization) would also count those same 10 (since `iv_current` is None for all of them and recommendation gets set to NO DATA in the early-return path of `score_opportunity`). The two definitions converge in practice. Minor: a one-line consistency note in `scan_quality.py` would future-proof it.
3. **[Nit]** `globals.css` has a comment `/* color-mix utility classes (opacity modifier workaround) */` that's stale relative to recent additions. Pure documentation drift, not a behavior issue.

---

## 2. Scope

### Files reviewed

**Backend:**
- `backend/scan_quality.py`
- `backend/scorer.py`
- `backend/models.py`
- `backend/main.py`
- `backend/test_qa_phase1.py`
- `backend/test_qa_phase1_regression.py` (added in earlier task)

**Frontend:**
- `frontend/src/lib/types.ts`
- `frontend/src/lib/scoring.ts`
- `frontend/src/components/Leaderboard.tsx`
- `frontend/src/components/DetailPanel.tsx`
- `frontend/src/app/page.tsx`
- `frontend/src/app/globals.css`

**Replay & docs:**
- `scripts/phase1_historical_replay.py`
- `docs/qa/phase1-historical-replay-report.md`
- `docs/qa/phase1-manual-ui-checklist.md`
- `references/dashboard-behavior-qa-report.md`

### Commands run

| Command | Result |
|---|---|
| `python backend/test_qa_phase1.py` | 13 passed, 0 failed |
| `python backend/test_qa_phase1_regression.py` | 17 passed, 0 failed |
| `python backend/test_calculator.py` | 5 passed, 0 failed |
| `python scripts/phase1_historical_replay.py` | All 28 days replayed; "Section G: (none — all SELL/CONDITIONAL with vrp_ratio≥1.15 preserved)" |
| `cd frontend && npx tsc --noEmit` | No errors |

### Commands not run

| Command | Reason |
|---|---|
| `cd frontend && npm run build` | Production build wasn't requested; typecheck is sufficient for behavior validation |
| `cd frontend && npm test` | No frontend test framework installed (verified — `package.json` has no `test` script and no Jest/RTL dev-deps); manual checklist at `docs/qa/phase1-manual-ui-checklist.md` is the substitute |
| `pytest` | The repo uses plain Python `python test_*.py` runners (no pytest config found); the `if __name__ == "__main__"` runners produce equivalent output |

---

## 3. Review Findings

### 3.1 VRP-Ratio Gate

**Status: PASS**

Implementation in `scorer.py:209-217`:

```python
if (
    rec in ("SELL PREMIUM", "CONDITIONAL")
    and surface.vrp_ratio is not None
    and surface.vrp_ratio < 1.15
):
    rec = "WATCHLIST"
    flags.append("Structure clean, but premium too thin (VRP ratio < 1.15)")
```

Evidence the gate is correctly placed and bounded:

- ✅ Runs AFTER the score is computed and clamped (`scorer.py:215` `score = max(0, min(100, int(score)))`).
- ✅ Score is never reassigned from this point on — `signal_score` is whatever the formula produced.
- ✅ Only triggers for `rec ∈ {"SELL PREMIUM", "CONDITIONAL"}` — DANGER's `AVOID`, CAUTION's `REDUCE SIZE`/`NO EDGE`, and the negative-VRP-cap's `NO EDGE` all fall through.
- ✅ Defensive `vrp_ratio is not None` guard handles edge cases (though in practice it's never None when the early-return-NO-DATA path doesn't fire).
- ✅ Strict `< 1.15` boundary verified by `test_vrp_gate_boundary_conditions` (1.1499 → WATCHLIST, 1.15 exact → CONDITIONAL preserved).
- ✅ Frontend uses backend's `vrp_ratio` field directly (`scoring.ts: const vrpRatio = t.vrp_ratio ?? null`) — no double-rounding from IV/RV30.

Spec examples verified end-to-end via `test_qa_phase1.py`:
- QQQ May 8 → WATCHLIST (score 45, ratio 1.026) ✓
- XLF May 8 → WATCHLIST (score 45, ratio 1.083) ✓
- JNJ May 8 → CONDITIONAL (score 58, ratio 1.333) ✓
- WMT May 4 → SELL (score 65, ratio 1.343) ✓
- WMT May 8 → SKIP via earnings gate (frontend, preGateScore preserved) ✓

**No issues found.**

### 3.2 WATCHLIST Behavior

**Status: PASS**

- ✅ TypeScript union: `DashboardTicker['action']` includes `'WATCHLIST'` (`types.ts:26`).
- ✅ Action chip distinct: `bg-accent-subtle border-accent-30` with `var(--color-accent)` (dusty purple) — visually separated from CONDITIONAL (yellow), NO EDGE (gray), AVOID (red), SELL (green).
- ✅ Position Construction hidden: `DetailPanel.tsx:298` guard `!isSkipped && !isAvoided && !isNoData && !isWatchlist && !isSuppressed && ticker.action !== 'NO EDGE'`. The explicit `!isWatchlist` guard documents intent even though `WATCHLIST` action wouldn't fall into the NO-EDGE-only check.
- ✅ Tradeable counts exclude WATCHLIST: `Leaderboard.tsx:248-249` filters `d.action === 'SELL'` and `d.action === 'CONDITIONAL'` only. `RegimeBanner.tsx:23` filters `d.action === 'SELL' || d.action === 'CONDITIONAL'` for `tradeable`. Verified by `test_watchlist_not_counted_as_tradeable`.
- ✅ Mobile card still dims only `SKIP` (`Leaderboard.tsx:156`) — WATCHLIST stays informational at full opacity (correct intent: it's a watchlist, not a refusal).
- ✅ DetailPanel explanation block renders accent-purple prose: "Watchlist — structure clean, but premium too thin." Includes the actual VRP ratio.
- ✅ NO EDGE behavior unchanged: tests `test_qa_phase1` cases 3 (NORMAL+score<45) and 7 (clean OK scan) confirm.

Looked specifically for:
- ❌ No accidental `default` fallthrough that treats WATCHLIST as CONDITIONAL — `mapRecommendation` has explicit `case 'WATCHLIST'` (`scoring.ts:13`).
- ❌ No counter, banner, or CTA that includes WATCHLIST as tradeable.

**No issues found.**

### 3.3 Thin Premium Badge

**Status: PASS**

Logic in `scoring.ts:71-77`:
```ts
const thinPremium = (
  action === 'CONDITIONAL' &&
  vrpRatio !== null &&
  vrpRatio >= 1.15 &&
  vrpRatio < 1.25
);
```

- ✅ Only fires when action is CONDITIONAL — narrowly scoped via `action === 'CONDITIONAL'` (the action AFTER `mapRecommendation`).
- ✅ Range `[1.15, 1.25)` matches spec exactly. Strict `< 1.25` upper bound.
- ✅ Backend-supplied `vrp_ratio` (no recomputation from rounded IV/RV).
- ✅ Cannot fire on WATCHLIST: action would be `'WATCHLIST'`, not `'CONDITIONAL'`. Verified in `test_vrp_gate_boundary_conditions`.
- ✅ Cannot fire on SELL, NO EDGE, AVOID, SKIP, NO DATA — same reason.
- ✅ Rendered consistently in:
  - Desktop table action chip (`Leaderboard.tsx:485` next to `<ActionChip>`)
  - Mobile card action chip (`Leaderboard.tsx:194`)
  - DetailPanel header (`DetailPanel.tsx:235`)
- ✅ Wording is cautionary, not panic: "Thin Premium" with hover tooltip "VRP ratio just above 1.15 dead zone — premium is thin".

**No issues found.**

### 3.4 Degraded-Scan Detection

**Status: PASS**

Implementation in `scan_quality.py:compute_scan_quality()`:

- ✅ Empty-set safety: explicit `if total == 0: return "OK", None` at line 36.
- ✅ NO DATA count: `sum(1 for r in results if r.recommendation == "NO DATA")` — only counts the explicit NO DATA recommendation, not earnings-gated SKIP. ETFs with `iv_current = None` would already have `recommendation = "NO DATA"` from `scorer.py:84` early-return, so they're correctly counted.
- ✅ Slope-wall count: `r.term_slope is not None and abs(r.term_slope - 1.0) < 0.001`. The `is not None` guard means missing slopes don't accidentally count as 1.00.
- ✅ Tolerance is tight (`0.001`) — verified by `test_slope_wall_tolerance_is_tight` that 1.02 doesn't count and 1.0005 does.
- ✅ Threshold comparisons use strict `>`:
  - `if no_data_count > NO_DATA_THRESHOLD` (4)
  - `if slope_wall_pct > SLOPE_WALL_THRESHOLD` (0.25)
  - Verified that exactly 25% does NOT trigger by `test_slope_wall_degraded`.
- ✅ Reason strings are user-readable: `"13 of 33 tickers returned NO DATA"` and `"14 of 29 tickers show term slope ≈ 1.00 (48%) — likely degenerate term structure"`.
- ✅ Clean scans don't trigger: verified by `test_clean_scan_is_ok` and `test_cached_ok_scan_unchanged`. The historical replay also confirmed only Apr 16 fires DEGRADED across 28 days.

Looked specifically for the listed bugs:
- ❌ Earnings-gated rows are NOT incorrectly counted as NO DATA — the check is `recommendation == "NO DATA"`, not `iv is None`.
- ❌ Missing `term_slope` doesn't count as 1.00 — explicit `is not None` guard.
- ❌ Denominator is `total = len(results)` (full universe) — consistent with the slope-wall reason ("of 33 tickers"). Documented.
- ❌ Tolerance is `0.001`, not `±0.02` — proven by FP edge-case test.

**No issues found.**

### 3.5 Degraded-Scan Suppression

**Status: PASS**

Implementation in `scan_quality.py:suppress_actionable()`:

- ✅ Only `{"SELL PREMIUM", "CONDITIONAL", "WATCHLIST"}` are downgraded to `NO EDGE`. AVOID, NO DATA, NO EDGE, REDUCE SIZE, and SKIP are not in the actionable set.
- ✅ Preserves `signal_score` (only `recommendation` and `suggested_*` fields are mutated). Verified by `test_raw_score_unchanged_after_degraded_suppression`.
- ✅ Preserves `regime` (not touched). Verified by `test_degraded_suppression_preserves_raw_recommendation`.
- ✅ Captures `pre_suppression_recommendation`, `pre_suppression_score`, `scan_quality_suppression_reason` BEFORE downgrade.
- ✅ Sets `suppressed_by_scan_quality = True` only on suppressed rows.
- ✅ Does NOT mutate persisted DB rows: `main.py` constructs fresh `TickerResult(**t)` from the cached JSON dict per request; `_apply_scan_quality()` mutates those Pydantic instances, not the underlying dict. The DB rows remain intact (no UPDATE).
- ✅ Idempotent re-application: a second call to `suppress_actionable()` on already-suppressed rows is a no-op (the `recommendation` is now `NO EDGE`, not in the actionable set).
- ✅ Cached and fresh scans behave the same: `_apply_scan_quality()` is called in the fresh scan path and in all 4 cached paths in main.py (lines 484, 627, 729, 755, 779).

Looked specifically for the listed bugs:
- ❌ No in-place mutation of cached DB objects (Pydantic models per request).
- ❌ Double-application is safe (idempotent).
- ❌ AVOID is preserved — explicitly excluded from actionable set.
- ❌ NO DATA is preserved — explicitly excluded.

**No issues found.**

### 3.6 Backend/API Path Consistency

**Status: PASS**

`scan_quality` and `scan_quality_reason` are wired into every `ScanResponse` construction that returns ticker data:

| Path | main.py line | scan_quality wired? |
|---|---|---|
| Empty cache (no scans yet) | 610 | Defaults to "OK" via Pydantic default; no tickers to suppress |
| `/api/scan/latest` cached | 627 | ✓ explicit |
| Fresh scan response | 484 | ✓ explicit |
| `/api/scan` market-closed cached | 729 | ✓ explicit |
| `/api/scan` pre-6:30PM cached | 755 | ✓ explicit |
| `/api/scan` already-scanned-today cached | 779 | ✓ explicit |

- ✅ Defaults are safe: `ScanResponse.scan_quality: str = "OK"` and `scan_quality_reason: Optional[str] = None`. Old responses (or responses with no tickers) deserialize without error.
- ✅ `_apply_scan_quality()` helper centralizes the logic; all paths use it.
- ✅ Old cached SQLite rows missing the new diagnostic fields (`suppressed_by_scan_quality`, `pre_suppression_*`, `scan_quality_suppression_reason`) deserialize cleanly via Pydantic defaults (False / None). Verified by `test_scan_quality_applied_to_historical_scan`.
- ✅ Frontend gracefully handles missing `scan_quality`: `apiData?.scan_quality === 'DEGRADED'` is false on undefined; banner doesn't render. Verified by typecheck (the field is optional `string | undefined`).

`/api/scan/history` returns metadata only (no tickers) — no scan_quality needed.
`/api/scan/comparison` uses `ComparisonResponse` (different model wrapping `TickerComparison`) — no full scan rendering, suppression isn't applicable.

**No issues found.**

### 3.7 Frontend/UI Behavior

**Status: PASS**

Banner in `page.tsx:208-225`:

- ✅ Renders when `apiData?.scan_quality === 'DEGRADED'`.
- ✅ Positioned above the regime banner (`mb-5` gap).
- ✅ Shows `scan_quality_reason` with a fallback "Scan returned unreliable data." for null reason.
- ✅ Visually prominent: red border (`border-error-30`), red-tinted background (`bg-error-subtle`), bold "DEGRADED SCAN" label, explicit prose: "Actionable recommendations have been suppressed for this scan — no SELL or CONDITIONAL signals will display."
- ✅ Does NOT render when `scan_quality === 'OK'` (or undefined).
- ✅ Banner appears on cached/historical degraded scans: `_apply_scan_quality()` runs on every cached read in main.py, populating `scan_quality` so the banner renders for cached DEGRADED days too.

Looked specifically for:
- ❌ Banner is NOT below-the-fold or subtle — it's a full-width red block with a top-row position.
- ❌ Suppressed signals do NOT appear visually encouraged — they collapse to NO EDGE chips with no Position Construction.

**No issues found.**

### 3.8 Historical Replay

**Status: PASS**

`scripts/phase1_historical_replay.py`:

- ✅ Non-invasive: read-only on `history/metrics-logs.md`. No production data modified.
- ✅ Parses safely with regex; gracefully skips malformed rows via try/except in `parse_table()`.
- ✅ Path is computed via `Path(__file__).parent.parent / "history" / "metrics-logs.md"` — works regardless of CWD when invoked.
- ✅ Idempotent (no state, no side effects).
- ✅ Catches all 8 QA-listed false positives (Section A) plus 5 additional latent ones — 13 total transitions identified, matching `docs/qa/phase1-historical-replay-report.md`.
- ✅ Identifies 2026-04-16 as the only DEGRADED day across 28 scans.
- ✅ Section G "Unexpected SELL/CONDITIONAL downgrades" is empty — no rows with `vrp_ratio ≥ 1.15` get accidentally downgraded.

**Issue (Low / Nit):** Threshold constants are duplicated rather than imported from `backend/scan_quality.py`:
```python
SLOPE_WALL_TOLERANCE = 0.001
SLOPE_WALL_THRESHOLD = 0.25
NO_DATA_THRESHOLD = 4
VRP_GATE = 1.15
THIN_LO, THIN_HI = 1.15, 1.25
```

If production thresholds change, the replay would silently drift. Recommended fix (non-blocking): replace the local definitions with `from scan_quality import ...` after adding `backend/` to `sys.path` (or move the script to `backend/scripts/`).

### 3.9 Tests

**Status: PASS**

Test inventory:

| File | Count | Coverage |
|---|---|---|
| `test_qa_phase1.py` | 13 | Phase 1 functional + suppression diagnostics |
| `test_qa_phase1_regression.py` | 17 | Action precedence, edge cases, ETF stress, FP-tight slope wall |
| `test_calculator.py` | 5 | Pre-existing — score formula, RV, DB round-trip |
| **Total** | **35** | All passing |

Spec coverage check:
- ✅ Boundary tests at 1.1499 / 1.15 / 1.2499 / 1.25 (`test_vrp_gate_boundary_conditions`).
- ✅ QQQ / XLF / JNJ / WMT May 8 fixtures (`test_qa_phase1.py` cases 1-4, plus regression `test_vrp_gate_preserves_score`).
- ✅ Both DEGRADED triggers tested (`test_apr16_style_scan_degraded_no_data`, `test_apr16_style_scan_degraded_slope_wall`).
- ✅ Suppression behavior (`test_degraded_suppression_zeros_actionable`, `test_degraded_suppression_preserves_raw_recommendation`).
- ✅ Raw score preservation (`test_raw_score_unchanged_when_watchlist`, `test_raw_score_unchanged_after_degraded_suppression`).
- ✅ WATCHLIST position-construction zeroed (`test_watchlist_position_construction_is_zeroed`).
- ✅ Existing calculator + score tests still pass.
- ✅ ETF earnings-gate stress test (`test_etf_never_earnings_gated`) — revealed and fixed a latent gap during prior task.
- ✅ FP-aware slope-wall tolerance test.

**Suggestion (non-blocking, Phase 2 if needed):** A FastAPI `TestClient`-based integration test for `/api/scan/latest` that verifies the full HTTP response shape. Currently the cached-path is unit-tested via `test_scan_quality_applied_to_cached_latest_scan` against `_apply_scan_quality_helper` directly (mirror of main.py logic), not the actual HTTP route. Marginal value vs. existing coverage; not necessary for production.

**No issues found.**

---

## 4. Issues Found

| Severity | File | Issue | Why It Matters | Recommended Fix | Blocking? |
|---|---|---|---|---|---|
| Low | `scripts/phase1_historical_replay.py` | Threshold constants duplicated rather than imported from `backend/scan_quality.py` (`SLOPE_WALL_TOLERANCE`, `SLOPE_WALL_THRESHOLD`, `NO_DATA_THRESHOLD`, `VRP_GATE`) | If production thresholds change, replay silently drifts and historical regression checks become invalid | Add `sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))` then `from scan_quality import ...` | Non-blocking |
| Nit | `backend/scan_quality.py` | Comment could clarify that NO DATA detection relies on `recommendation == "NO DATA"` (set by `scorer.py:84`), not on raw `iv is None` | Future maintainer might add an alternate-path NO DATA case (e.g. quick-fail in main.py) and not realize the count requires the `scorer.py` early-return path | One-line clarifying comment in `compute_scan_quality()` | Non-blocking |
| Nit | `frontend/src/app/globals.css:341` | Stale comment: "color-mix utility classes (opacity modifier workaround)" — accurate but predates several new entries | Documentation drift only | Optional comment refresh | Non-blocking |
| Nit | `frontend/src/app/page.tsx:217` | The pre-existing `Methodology Footer` displays Phase-1 prose: "VRP magnitude (0-40) + Term structure (0-25) + IV percentile (0-20) − RV acceleration penalty (0-15)" — known stale per `references/dashboard-behavior-qa-report.md` (§5.7) and `fragile-seams.md` | A trader reading the footer has a wrong mental model of the actual additive scoring; predates Phase 1 fixes but worth flagging | Update prose to match current scorer (VRP 0-30, IV pct 0-25, Term 0-20, RV 0-15, Skew 0-10, additive); already on the existing fragile-seams list | Phase 2 backlog |

**No High, Medium, or Critical issues.**

---

## 5. Acceptance Criteria Checklist

| Criteria | Pass/Fail | Evidence |
|---|---|---|
| Score formula unchanged | **PASS** | `scorer.py:122-215` is identical to pre-Phase-1; tests `test_calculator.py::test_score_opportunity` (Normal score 87, Danger score 63 — unchanged from prior run) |
| SELL/CONDITIONAL thresholds unchanged | **PASS** | `scorer.py:222,224` `if score >= 65: rec = "SELL PREMIUM"; elif score >= 45: rec = "CONDITIONAL"` |
| VRP gate works | **PASS** | `scorer.py:209-217`; tests `test_qa_phase1.py` cases 1-3, regression A1-A3 |
| WATCHLIST not tradeable | **PASS** | `Leaderboard.tsx:248-249` filters `'SELL'`/`'CONDITIONAL'` only; `RegimeBanner.tsx:23` same; `test_watchlist_not_counted_as_tradeable` |
| Thin Premium badge correct | **PASS** | `scoring.ts:71-77` range `[1.15, 1.25)` AND `action === 'CONDITIONAL'` only; `test_vrp_gate_boundary_conditions` |
| Degraded scan detection works | **PASS** | `scan_quality.py:compute_scan_quality`; tests E11/E12/E13; replay confirms Apr 16 only |
| Degraded scan suppression safe | **PASS** | `scan_quality.py:suppress_actionable` — actionable set is `{SELL PREMIUM, CONDITIONAL, WATCHLIST}`; AVOID/NO DATA/SKIP/NO EDGE preserved; `test_degraded_scan_preserves_avoid_no_data_skip` |
| Earnings gate unchanged | **PASS** | `scoring.ts:35-43`; the only change since Phase 1 prep was adding the `&& !t.is_etf` defense-in-depth guard (revealed by `test_etf_never_earnings_gated`); core gate logic identical |
| DANGER/CAUTION unchanged | **PASS** | `scorer.py:196-206` (regime detection) and `scorer.py:218-227` (recommendation) — pre-Phase-1 paths untouched; `test_caution_behavior_unchanged`, `test_danger_overrides_watchlist` |
| Position sizing unchanged | **PASS** | `scoring.ts:50-52` `Full / Half / Quarter` based on `rvAccel` thresholds 1.10 / 1.20 — bytes-identical to pre-Phase-1 |
| Historical replay passes | **PASS** | All 28 days replay; 13 transitions caught (8 expected + 5 latent); 0 unexpected downgrades; Apr 16 only DEGRADED day |
| Tests pass | **PASS** | 35/35 across 3 suites; frontend typechecks clean |

---

## 6. Recommended Next Steps

### Must fix before production
- **None.** All acceptance criteria pass.

### Nice to fix before production
1. Replace duplicated threshold constants in `scripts/phase1_historical_replay.py` with imports from `backend/scan_quality.py`. Prevents silent drift if thresholds are tuned in future. ~5 lines of code.
2. Add the one-line clarifying comment in `scan_quality.py:compute_scan_quality()` documenting the NO DATA convention.

### Phase 2 backlog
1. Update the stale Methodology Footer prose in `page.tsx:217-225` (already noted in `fragile-seams.md`; not a Phase 1 regression).
2. Add a FastAPI `TestClient` integration test for `/api/scan/latest` to validate the full HTTP response shape (currently we test `_apply_scan_quality()` against an in-process mirror).
3. Consider a per-ticker score grid (the multi-ticker option from the prior frontier discussion) — separate user request, not blocking Phase 1.

---

## 7. Final Verdict

**Phase 1 is production-ready.**

The implementation is conservative, well-tested, and faithful to the specs. The VRP-ratio gate cleanly captures the structure-only false-positive class without distorting the score formula. The WATCHLIST tier is correctly excluded from every tradeable count and CTA. Scan-quality detection covers both documented triggers with strict comparison semantics and tight FP tolerances. Suppression preserves the audit trail (`pre_suppression_*` fields) so degraded-scan rows remain interpretable for post-hoc review. Cached responses re-evaluate scan-quality on every read, so historical scans get the new behavior without DB migration.

The three Low/Nit issues identified are all polish — none affects correctness, safety, or trading behavior. They can land in a follow-up commit or be deferred indefinitely without risk.

**This review validates implementation quality only. It does not validate that the underlying premium-selling strategy is profitable, or that the score thresholds (45, 65) are correctly calibrated for trading P&L. Those are separate concerns outside Phase 1's scope.**

The system safely handles the cases the QA report identified as failure modes (8 historical false positives + the Apr 16 degraded scan). Trading on the dashboard's output post-Phase-1 carries strictly less framework-induced risk than pre-Phase-1.

---

*End of report.*
