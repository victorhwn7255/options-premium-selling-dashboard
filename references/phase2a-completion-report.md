# Theta Harvest Phase 2A Completion Report

**Date:** 2026-05-10
**Scope:** Polish-only cleanup of low-risk items identified in `phase1-code-review-report.md` §4. No strategy logic changed.

---

## 1. Summary

Phase 2A landed four cleanup changes:

1. **Methodology footer** in `frontend/src/app/page.tsx` updated to reflect the current additive scoring model (replacing the stale Phase-1 penalty-model prose).
2. **Replay script thresholds** in `scripts/phase1_historical_replay.py` now imported from `backend/scan_quality.py` so the historical-replay tool can no longer drift silently from production detection rules.
3. **NO DATA convention comment** added to `backend/scan_quality.py:compute_scan_quality()` documenting that the count comes from `recommendation == "NO DATA"` (set by scorer.py's early-return path), not from raw `iv is None`.
4. **Lightweight FastAPI integration test** at `backend/test_qa_phase2a_integration.py` exercises `/api/scan/latest` for empty / OK-cached / DEGRADED-cached scenarios via TestClient with mocked DB read. Three new tests pass.

**No production trading logic changed.** All thresholds, gates, scoring rules, and action mappings are byte-identical to pre-Phase-2A. All Phase 1 unit tests (35) and the new integration tests (3) pass; historical replay continues to flag the same 13 transitions and the single Apr 16 DEGRADED day.

---

## 2. Files Changed

| File | Change |
|---|---|
| `frontend/src/app/page.tsx` | Methodology footer prose updated to current additive model + Phase 1 gates |
| `scripts/phase1_historical_replay.py` | Imports `SLOPE_WALL_TOLERANCE`, `SLOPE_WALL_THRESHOLD`, `NO_DATA_THRESHOLD` from `backend/scan_quality.py`; `VRP_GATE` / `THIN_LO` / `THIN_HI` left local with TODO comment (production hardcodes them in scorer.py / scoring.ts) |
| `backend/scan_quality.py` | NO DATA convention inline comment added inside `compute_scan_quality()` (doc-only, no behavior change) |
| `backend/test_qa_phase2a_integration.py` | **NEW** — 3 FastAPI TestClient integration tests for `/api/scan/latest` |
| `references/phase2a-completion-report.md` | **NEW** — this report |

---

## 3. Footer Update

### Old (stale Phase-1 penalty model)

> Scoring: VRP magnitude (0-40) + Term structure (0-25) + IV percentile (0-20) − RV acceleration penalty (0-15). Gated by earnings proximity and backwardation.

### New (current additive model + Phase 1 gates)

> Scoring: VRP Quality (30) + IV Percentile (25) + Term Structure (20) + RV Stability (15) + 25Δ Put Skew (10). Negative VRP caps scores at 44. Earnings within 14 days forces SKIP for non-ETF tickers. DANGER regimes override to AVOID. Otherwise-actionable signals with VRP ratio below 1.15 are shown as WATCHLIST, not tradeable. Sizing: Full if RV Accel < 1.10, Half if < 1.20, Quarter above. Live data — not financial advice.

Concise, single block, same UI styling. No extra layout. Reflects:
- Five additive components with correct max points (matches `scorer.py` and `references/metrics.md`).
- Negative-VRP cap at 44 (ADR-004).
- Earnings gate at 14d for non-ETFs (frontend, ADR-003 + the Phase 2A `!is_etf` defense-in-depth fix).
- DANGER regime override (ADR-011).
- VRP-ratio gate → WATCHLIST (Phase 1).
- Position sizing chip rules unchanged.

---

## 4. Replay Threshold Import

`scan_quality` thresholds (3 of 5 phase-1-relevant constants) are now imported from production:

```python
sys.path.insert(0, str(BACKEND))
from scan_quality import (
    SLOPE_WALL_TOLERANCE,
    SLOPE_WALL_THRESHOLD,
    NO_DATA_THRESHOLD,
)
```

`VRP_GATE = 1.15` and `THIN_LO / THIN_HI = 1.15 / 1.25` remain local constants because they aren't currently exposed as named constants in production code (hardcoded literals in `backend/scorer.py:212` and `frontend/src/lib/scoring.ts:75-77`). A `TODO` comment notes this:

```python
# VRP gate (1.15) is hardcoded in backend/scorer.py and Thin Premium bounds
# (1.15, 1.25) in frontend/src/lib/scoring.ts. They aren't exposed as named
# constants in production today.
# TODO: promote these to shared backend constants if thresholds become configurable.
```

Per the spec ("Do not refactor broadly… Do not create a new shared config module unless it is tiny and clearly safe."), these stay local for now.

**Replay behavior unchanged.** The script produces the same 13 transitions, 17 Thin Premium rows, 1 DEGRADED day, and zero unexpected downgrades as before. Output verified identical to `docs/qa/phase1-historical-replay-report.md`.

---

## 5. NO DATA Comment

Comment added inside `compute_scan_quality()` directly above the count:

```python
# NO DATA is counted from `recommendation == "NO DATA"`, not from raw
# `iv is None`. This relies on scorer.py's early-return path, which sets
# recommendation = "NO DATA" whenever iv_current is None. Counting from the
# normalized scoring output keeps fresh and cached responses consistent and
# avoids miscounting earnings-gated rows whose underlying IV is also None.
no_data_count = sum(1 for r in results if r.recommendation == "NO DATA")
```

**Behavior unchanged** — same expression as before, only the inline comment is new.

---

## 6. Integration Test

**Added.** `backend/test_qa_phase2a_integration.py` covers three scenarios via `fastapi.testclient.TestClient` with `unittest.mock.patch("main.get_latest_scan", …)`:

| Test | Validates |
|---|---|
| `test_latest_scan_empty_cache_returns_default_scan_quality` | When no cached scan exists, response includes `scan_quality` (defaults to `"OK"`) and `scan_quality_reason` (null) — no crash on missing data |
| `test_latest_scan_cached_ok_response_has_scan_quality` | Healthy cached scan reads back as `OK`; SELL / CONDITIONAL / WATCHLIST / NO EDGE recommendations are NOT mutated |
| `test_latest_scan_cached_degraded_response_suppresses_actionable` | Cached scan with 5 NO DATA rows triggers `DEGRADED`; SELL / CONDITIONAL / WATCHLIST → NO EDGE on the wire with full `pre_suppression_*` audit metadata; AVOID and NO DATA preserved |

The test was lightweight: `httpx` and `fastapi` are already in `backend/requirements.txt`, only `unittest.mock` was needed (stdlib). Setup overhead is one `os.environ.setdefault("MARKETDATA_TOKEN", "test-stub-for-integration")` call before importing `main`. No DB or API mocking beyond `get_latest_scan`.

This validates the full HTTP-response shape (the existing unit tests cover the helpers that the route calls; the integration test confirms the wire format and that none of the wiring layers drop the new fields).

---

## 7. Test Results

| Command | Result |
|---|---|
| `git diff` | Reviewed (5 file changes, all in scope) |
| `python backend/test_qa_phase1.py` | **Pass** (13/13) |
| `python backend/test_qa_phase1_regression.py` | **Pass** (17/17) |
| `python backend/test_calculator.py` | **Pass** (5/5) |
| `python backend/test_qa_phase2a_integration.py` | **Pass** (3/3, NEW) |
| `python scripts/phase1_historical_replay.py` | **Pass** (28 days, same output as pre-Phase-2A; Section G empty) |
| `cd frontend && npx tsc --noEmit` | **Pass** (no errors) |
| `cd frontend && npm run build` | Not run — typecheck is sufficient for the doc-only frontend change; production-build cost not justified for a footer prose edit |

**Total: 38 tests passing, 0 failing.** No regressions.

---

## 8. Confirmation of Unchanged Logic

| Item | Changed? |
|---|---|
| Score formula | No |
| SELL threshold | No |
| CONDITIONAL threshold | No |
| VRP gate threshold | No |
| Thin Premium threshold | No |
| Earnings gate | No |
| DANGER / CAUTION logic | No |
| Position sizing | No |
| WATCHLIST behavior | No |
| Degraded scan detection | No |
| Degraded scan suppression | No |

Verified by:
- All Phase 1 unit + regression tests pass without modification (35/35).
- Historical replay output is byte-identical to pre-Phase-2A (same 13 transitions, same 17 Thin Premium rows, same Apr 16 DEGRADED, same Section G "(none)").
- The only Python file edited under `backend/` is `scan_quality.py`, and the only change is the inline NO DATA comment (no expression changed).
- The only frontend file edited under `src/` is `app/page.tsx`, and the only change is JSX prose inside the methodology footer (no logic, hooks, or state).
- The replay script now imports thresholds (production single-source-of-truth strengthened, behavior identical).

---

## 9. Remaining Follow-Ups

Non-blocking, deferred:

1. **`VRP_GATE = 1.15` and `THIN_LO / THIN_HI = 1.15 / 1.25` are not yet exposed as named constants in production.** The replay script keeps local copies with a TODO. A future small refactor could promote these — e.g., add `VRP_RATIO_GATE = 1.15` to `scorer.py` (or a new `thresholds.py`) and a `THIN_PREMIUM_RANGE = (1.15, 1.25)` exposure usable by both scoring.ts (via copy/sync) and the replay script. Out of scope for Phase 2A.
2. **`npm run build`** wasn't run; only `tsc --noEmit`. The footer change is JSX prose with no new imports or types, so the production build risk is negligible. If production deploy includes a build step, it will exercise this.
3. The integration test patches `main.get_latest_scan` directly. A more thorough end-to-end test could exercise `/api/scan` (POST) too, but that path involves cron / scan-trigger logic and requires more mocking. Defer to Phase 2B if needed.

None of these block production. None affect trading behavior.

---

## 10. Final Verdict

**Phase 2A complete.**

All four cleanup items landed cleanly. No production behavior changed. Test coverage strengthened (3 new integration tests on the wire format). Diff is small and reviewable. Acceptance criteria from the task spec are all met:

- ✅ Footer reflects the current scoring model.
- ✅ Replay script imports scan-quality thresholds from production.
- ✅ NO DATA convention comment added.
- ✅ Lightweight integration test added (FastAPI TestClient).
- ✅ All existing backend tests pass.
- ✅ Historical replay still passes.
- ✅ Frontend typecheck passes.
- ✅ No strategy behavior changed.
- ✅ This report exists at `references/phase2a-completion-report.md`.

---

*End of report.*
