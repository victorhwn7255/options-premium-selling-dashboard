# Context Folder — Phase 2: Source Map

> **Date:** 2026-04-16 | **Git:** `2134cff` | **Status:** Awaiting review before Phase 3

This document maps every approved `/context/` file to its source material, identifies what migrates from `tasks/notes.md`, flags stale content in `references/checkpoints/`, and lists the final ADR set.

---

## 1. `scoring-and-strategy.md` — Source Mapping

| Section | Primary source | Notes.md sections | References |
|---|---|---|---|
| 5 scoring components | `backend/scorer.py:64-295` (score_opportunity) | Notes §5 (full formula table) | `references/metrics_report.md` §Composite Scoring |
| Gates (neg VRP, earnings, no-data) | `scorer.py:209-215`, `frontend/src/lib/scoring.ts:33-39` | Notes §5 (gates table) | `references/strategy.md` §Three Safety Systems |
| Per-ticker regime detection | `scorer.py:196-206` | Notes §5 (regime detection) | — |
| Recommendation logic | `scorer.py:217-227` | Notes §5 (recommendation table) | — |
| Position construction | `scorer.py:229-254` | Notes §5 (position construction table) | `references/strategy.md` §Position Construction |
| Position sizing | `frontend/src/lib/scoring.ts:41-43` | Notes §27 step 2 | — |
| Dashboard regime | `frontend/src/components/RegimeBanner.tsx:9-70` | Notes §34 | `references/strategy.md` §Market Regime |
| Backend vs frontend responsibility | Cross-cutting | Notes §37 (integration summary) | — |
| Methodology footer discrepancy | `frontend/src/app/page.tsx:216-220` | Notes §39 item 5 | — |

**Rewrite needed:** Notes §5 is the best raw material, but it's formatted as implementation notes. Needs to be restructured as a "how scoring works" narrative with code location pointers (not line numbers).

---

## 2. `fragile-seams.md` — Source Mapping

| Seam | Primary source | Notes.md | Memory/references |
|---|---|---|---|
| Skew expiration alignment | `marketdata_client.py:234-254` (wide chain exact date) | Notes §19 item 10 | `memory/project_vega_convention_bug.md` mentions related |
| Vega convention instability | `calculator.py:320-329` (_normalize_vega) | Notes §19 item 4 | `memory/project_vega_convention_bug.md` |
| FMP earnings drift | `fmp_client.py`, `main.py:518-553` (Yahoo override) | Notes §19 item 11 | `memory/project_fmp_earnings_staleness.md` |
| CSV race condition | `csv_store.py:106-122` (append_daily_csv) | Notes §19 item 8 | — |
| In-memory earnings counter | `main.py:869-870` (_EARNINGS_REFRESH_LIMIT) | Notes §19 item — | `memory/project_known_issues.md` |
| EEM IV anomaly | Historical data in SQLite | Notes §19 — (from phase 3 summary) | — |
| RV10 sensitivity | `calculator.py:152-181` (10-day window) | Phase 3 summary §11 | — |
| Skew=0 for illiquid tickers | `calculator.py:472-578` (compute_skew) | Phase 3 summary §11 | `memory/project_known_issues.md` |
| UTC+8 host timezone | `main.py` ET timezone handling, Docker in SGT | Notes §19 item 9 | — |
| Silent frontend errors | `frontend/src/lib/api.ts` (empty catch blocks) | Notes §39 item 6 | — |
| Scan gate edge case | `main.py:611-616` (_is_scanned_today) | Notes §19 item 6 | — |
| get_previous_day_scan 50-row limit | `database.py:264-288` | Notes §19 item 7 | — |

**Rewrite needed:** Consolidate from notes §19 + §39 + phase 3 summary §11 + memory files. Add incident history where known (skew alignment broke twice, vega convention flip on 2026-04-15).

---

## 3. `architecture.md` — Source Mapping

| Section | Primary source | Notes.md |
|---|---|---|
| Service topology | `docker-compose.yml` | Notes §23 |
| API proxy | `frontend/next.config.js`, `frontend/src/lib/api.ts` | Notes §28 |
| Scan lifecycle | `main.py:212-477` | Notes §3 + §21 (E2E flow) |
| Frontend data flow | `frontend/src/app/page.tsx`, `scoring.ts` | Notes §27 |
| Ownership boundary | Cross-cutting | Notes §37 |
| Regime disconnect | `main.py:399-445` vs `RegimeBanner.tsx:9-70` | Notes §6 + §34 |
| External deps | `marketdata_client.py`, `fmp_client.py`, `utils/verify_metrics.py` | Notes §20 |
| Module dependency graph | Import statements across all backend + frontend files | Notes §22 |

**Rewrite needed:** Notes §21 has a good E2E flow diagram but is formatted as a code walkthrough. Architecture.md should be diagrams + prose, not a file-by-file tour. Module graph from Notes §22 is the right level (module-level, not function-level).

---

## 4. `data-model.md` — Source Mapping

| Section | Primary source | Notes.md |
|---|---|---|
| SQLite schema (6 tables) | `database.py:31-93` (init_db) | Notes §9 |
| Pruning behavior | `database.py:216-222`, `database.py:373-378`, `database.py:423-428` | Notes §9 |
| CSV formats | `csv_store.py:12-20` (headers), `csv_store.py:84-122` (append logic) | Notes §13 |
| Data lifecycle | `main.py:264-283` (persist per ticker), `backfill.py` (historical) | Notes §15 |
| Earnings pipeline | `fmp_client.py`, `main.py:518-553` (Yahoo fills/overrides) | Notes §8 + §11 |

**Rewrite needed:** Notes §9 has complete table definitions. Need to restructure as a data model reference (not implementation notes) with lifecycle narrative.

---

## 5. `deployment.md` — Source Mapping

| Section | Primary source | Notes.md |
|---|---|---|
| Docker stack | `docker-compose.yml` | Notes §23 |
| Env vars | `main.py:145-160`, `backfill.py:44` | Notes §23 (table) |
| Local dev | CLAUDE.md §Commands | — |
| Rebuild workflow | Docker behavior (source baked in) | Memory: `feedback_docker_rebuild.md` |
| Volumes | `docker-compose.yml` volumes section | Notes §23 |
| Cloudflare tunnel | `docker-compose.yml` cloudflared service | — |
| Backfill/repair scripts | `backfill.py`, `repair_rv.py` (CLI args) | Notes §15 + §16 |
| SGT timezone caveat | Runtime observation | Notes §19 item 9 |

**Rewrite needed:** Mostly new writing organized from scattered sources. CLAUDE.md §Commands is the closest existing reference. Memory file on docker rebuild is important context.

---

## 6. `methodology.md` — Source Mapping

| Section | Primary source | Notes.md |
|---|---|---|
| VRP academic basis | Domain knowledge + `references/strategy.md` §Core Thesis | — |
| ATM BSM as proxy | `calculator.py:185-267` (compute_atm_iv) | Notes §4 |
| Close-to-close RV | `calculator.py:152-181` (compute_realized_vol) | Notes §4 |
| IV Percentile vs Rank | `scorer.py:135-139` (scoring uses percentile, not rank) | Notes §5 |
| Scoring shape rationale | `scorer.py:64-82` (docstring), `references/strategy.md` §Five Signals | — |
| Liquidity filter design | `calculator.py:93-148` | Notes §4 |
| Known limitations | Domain knowledge | — |

**Rewrite needed:** This is mostly new writing. The academic rationale isn't documented anywhere in the repo currently — it needs to be authored from domain knowledge and the strategy doc, not migrated from existing notes.

---

## 7. `domain-glossary.md` — Source Mapping

| Section | Primary source | Notes.md |
|---|---|---|
| Volatility metrics | `references/metrics_report.md` §1-6 | — |
| Structure metrics | `references/metrics_report.md` §7-8 | — |
| Trade-level metrics | `references/metrics_report.md` §9-10 | — |
| Per-ticker regime | `scorer.py:196-206` | Notes §5 |
| Dashboard regime | `RegimeBanner.tsx:9-70` | Notes §34 |
| Recommendation labels | `scorer.py:217-227` | Notes §5 |
| Position terms | `references/strategy.md` §Position Construction | — |
| Thresholds | Scattered across scorer.py, calculator.py | Notes §18 |

**Rewrite needed:** Primarily a consolidation of `references/metrics_report.md` definitions (link, don't duplicate) plus regime/recommendation labels from notes. The threshold quick-reference table from Notes §18 is valuable — migrate as-is.

---

## 8. `decisions/` ADRs — Source Mapping

| ADR | Primary source | Notes.md | Status |
|---|---|---|---|
| 001: Single-source scoring | `scoring.ts` (passes through, doesn't recompute) | Notes §37 | Confirmed |
| 002: NO DATA over computed-from-rejected | `calculator.py:600-612` (MIN_ATM_CONTRACTS gate) | Notes §4 item 3 | Confirmed |
| 003: Earnings gate frontend-only | `scoring.ts:33-39` (not in scorer.py) | Notes §39 item 1 | Confirmed |
| 004: Negative VRP cap at 44 | `scorer.py:211-213` | Notes §5 | Confirmed |
| 005: Rate limit 10/min | `main.py:153` (MarketDataClient rate_limit=10) | Notes §19 item 3 | Confirmed |
| 006: Two regime classifiers | `main.py:399-445` vs `RegimeBanner.tsx:9-70` | Notes §37 | Confirmed |
| 007: ScoringParams permissive override | `main.py:309-313` | Notes §19 item 1 | Confirmed |
| 008: Vega normalization heuristic | `calculator.py:320-329` | Notes §19 item 4 | Confirmed |
| 009: Sequential scan (Semaphore=1) | `main.py:320` | Notes §19 item 3 | Confirmed |
| 010: Holiday calendar in both frontend and backend | `main.py:619-678` + `Navbar.tsx:44-91` | Notes §12 + §33 | **New** (per Phase 1 feedback) |

**XLB exclusion:** Dropped from candidates — XLB is in UNIVERSE, no exclusion exists in current code.

---

## 9. `README.md` — Source Mapping

Written last. Sources:
- File list and descriptions from all completed files
- Project summary from CLAUDE.md §Project Overview
- Reading order derived from the dependency between files

---

## Content Triage: `tasks/notes.md`

### Migrates to `/context/`

| Notes section | Destination | Treatment |
|---|---|---|
| §3 Per-Ticker Scan Flow | `architecture.md` §Scan Lifecycle | Restructure as narrative, drop line numbers |
| §4 build_vol_surface | `methodology.md` (rationale only) | Extract "why" decisions, drop implementation detail |
| §5 Scoring Engine | `scoring-and-strategy.md` | Primary source for scoring file |
| §6 Market-Wide Regime | `architecture.md` §Regime Disconnect | Merge with §34 |
| §8 FMP Earnings | `data-model.md` §Earnings Pipeline | Condense |
| §9 Database Layer | `data-model.md` | Table definitions + CRUD summary |
| §11 Post-Scan Verification | `architecture.md` §Scan Lifecycle | Brief mention, not full walkthrough |
| §12 Holiday Calendar | `decisions/010-holiday-duplication.md` | ADR |
| §13 CSV Storage | `data-model.md` §CSV Files | Schema + gotchas |
| §15 Backfill Script | `deployment.md` §Backfill Scripts + `data-model.md` §Data Lifecycle | Split: usage → deployment, purpose → data-model |
| §16 Repair Script | `deployment.md` §Backfill Scripts | Usage only |
| §18 Constants | `domain-glossary.md` §Thresholds | Migrate table |
| §19 Backend Gotchas | `fragile-seams.md` + `decisions/` | Split: hazards → seams, deliberate choices → ADRs |
| §20 External Deps | `architecture.md` §External Dependencies | Condense |
| §21 E2E Flow | `architecture.md` §Scan Lifecycle | Restructure as diagram |
| §22 Import Graph | `architecture.md` §Module Dependencies | Module-level only |
| §23 Deployment | `deployment.md` | Primary source |
| §27 Frontend Data Flow | `architecture.md` §Frontend Data Flow | Restructure |
| §28 API Client | `architecture.md` §API Proxy | Condense |
| §33 Navbar | `fragile-seams.md` (holiday dup) + `decisions/010` | Specific items only |
| §34 RegimeBanner | `scoring-and-strategy.md` §Dashboard Regime | Merge with §6 |
| §37 Integration Summary | `architecture.md` §Ownership Boundary | Key section |
| §39 Frontend Gotchas | `fragile-seams.md` + `decisions/` | Split same as §19 |

### Stays in `tasks/notes.md` (no natural home in `/context/`)

| Notes section | Reason to keep |
|---|---|
| §1 File Inventory (line counts) | Stale the moment any file changes. Code is the source of truth. |
| §2 Runtime Entry Point (startup sequence detail) | Implementation detail, not context. Read the code. |
| §7 Rate Limiting internals | Code walkthrough. Architecture.md covers the "what", not the retry loop. |
| §10 API Endpoints (full gate cascade) | CLAUDE.md has the endpoint table. Notes has implementation detail. |
| §14 Response Models (field lists) | Read `models.py`. |
| §17 Tests (test descriptions) | Read the test files. |
| §24 Things NOT in the backend | Negative-space observation, not actionable context. |
| §25-26 Frontend file inventory | Same as §1 — stale on any change. |
| §29-32 Theme, Design System, Component details | Implementation detail. Read the code. |
| §35-36 Educational Modals, Type System | Implementation detail. |
| §38 Deployment (frontend) | Merged into `deployment.md` already. |
| §40 Signal Delivery Chain | Good narrative but redundant with architecture.md scan lifecycle. |

`tasks/notes.md` remains as the raw study scratchpad — NOT deleted.

---

## Content Triage: `references/checkpoints/`

| File | Status | Action |
|---|---|---|
| `codebase_phase_1_summary.md` | **Stale** — v1.0.0, 15 tickers, old scoring formula, old regime names | Archive (rename parent to `references/archive/`) |
| `codebase_phase_2_summary.md` | **Stale** — v1.0.2, no day-over-day, no verification, old earnings limit | Archive |
| `codebase_phase_3_summary.md` | **Partially stale** — v1.08, mostly accurate but ticker count, some details outdated | Archive (context/ supersedes) |

**Recommendation:** Rename `references/checkpoints/` → `references/archive/` with a one-line `README.md` noting these are historical snapshots. Do NOT delete — they have value as a changelog.

---

## Phase 2 Complete — Awaiting Review

Questions for the reviewer:
1. Is the migration mapping correct? Any content I'm sending to the wrong file?
2. Is the "stays in notes" list right? Anything I'm leaving behind that should migrate?
3. Confirm the `references/checkpoints/` → `references/archive/` rename is acceptable.
4. Ready to proceed to Phase 3 (write `scoring-and-strategy.md` + `fragile-seams.md`)?
