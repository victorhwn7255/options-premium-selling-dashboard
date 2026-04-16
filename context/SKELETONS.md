# Context Folder — Phase 1: Skeletons

> **Date:** 2026-04-16 | **Git:** `2134cff` (v1.12 merge) | **Status:** Awaiting review before Phase 2

---

## 1. `README.md`

**Purpose:** Entry point and reading-order guide — answers "where do I start?" for a new human or agent.

**Audience:** Both

**Scope includes:**
- Reading order (what to read first depending on your role)
- One-paragraph project summary
- Index of every file in `/context/` with one-line description
- Pointers to primary sources (`references/strategy.md`, `references/metrics_report.md`)
- How to keep context files updated (freshness protocol)

**Scope excludes:**
- Any technical content — see the individual files
- Session instructions — see `CLAUDE.md`
- Task tracking — see `tasks/`

**Rot risk:** Low — changes only when files are added/removed from `/context/`

**Section outline:**
1. What is Theta Harvest? (3 sentences)
2. Reading Order
3. File Index
4. Primary Sources (links to `/references/`)
5. Keeping Context Fresh

**Open questions:** None.

---

## 2. `architecture.md`

**Purpose:** Answers "how do the pieces fit together?" — service boundaries, data flow between services, and the high-level codebase map. NOT a module-by-module walkthrough.

**Audience:** Both

**Scope includes:**
- 3-service Docker topology (backend, frontend, cloudflared)
- Request flow: browser → Next.js → API proxy → FastAPI → MarketData.app / SQLite
- Scan lifecycle: cron trigger → per-ticker pipeline → scoring → persistence → verification
- Frontend data flow: fetch → scoring.ts transform → regime computation → render
- What backend owns vs. what frontend owns (authoritative boundary)
- The regime disconnect (backend Phase-1 names vs. frontend NBA-themed names)

**Scope excludes:**
- Individual function signatures or module internals — read the source
- Scoring formula details — see `scoring-and-strategy.md`
- SQLite schema / CSV format — see `data-model.md`
- Deployment config (env vars, Docker commands) — see `deployment.md`
- Domain definitions (VRP, IV percentile, etc.) — see `domain-glossary.md`

**Rot risk:** Medium — triggers: new endpoint added, new service added, frontend-backend contract change
- `backend/main.py` (endpoints, scan orchestration)
- `frontend/src/lib/api.ts` (API client)
- `frontend/src/lib/scoring.ts` (transform pipeline)
- `frontend/src/components/RegimeBanner.tsx` (regime computation)
- `docker-compose.yml`

**Section outline:**
1. Service Topology
2. API Proxy & Communication
3. Scan Lifecycle (end-to-end)
4. Frontend Data Flow (fetch → transform → render)
5. Ownership Boundary (what backend vs. frontend is authoritative for)
6. Regime Disconnect (two independent classifiers)
7. External Dependencies (MarketData.app, FMP, Yahoo Finance)

**Open questions:**
- Should this include the file import graph (which module imports what), or is that too close to code-mirroring? Leaning no — it's derivable from the code and changes frequently.

---

## 3. `domain-glossary.md`

**Purpose:** Answers "what does this term mean?" — options-selling domain vocabulary with formulas. A new engineer who doesn't trade options can look up any term they encounter in the codebase.

**Audience:** Both (especially humans new to options)

**Scope includes:**
- Every domain term used in the codebase: RV, IV, VRP, IV Rank, IV Percentile, term structure (contango/backwardation), slope, skew (25-delta), theta, vega, ATR, DTE, earnings gate
- Per-ticker regime labels (NORMAL, CAUTION, DANGER) — what triggers each
- Dashboard regime labels (OFF SEASON, REGULAR SEASON, THE PLAYOFFS, THE FINALS)
- Recommendation labels (SELL PREMIUM, CONDITIONAL, REDUCE SIZE, AVOID, NO EDGE, NO DATA)
- Position construction terms (delta, DTE, iron condor, strangle, jade lizard, credit spread)
- Key thresholds referenced in code (1.15 VRP ratio dead zone, 30th percentile floor, 3% ATM range, etc.)

**Scope excludes:**
- How terms combine into a score — see `scoring-and-strategy.md`
- Full metric derivation with code paths — see `references/metrics_report.md`
- Strategy thesis (why we sell premium) — see `references/strategy.md`

**Rot risk:** Low — these definitions are stable unless the scoring model is redesigned
- `backend/scorer.py` (regime thresholds, recommendation labels)
- `frontend/src/components/RegimeBanner.tsx` (dashboard regime thresholds)

**Section outline:**
1. Volatility Metrics (RV, IV, VRP, VRP Ratio, IV Rank, IV Percentile)
2. Structure Metrics (Term Structure, Slope, Contango/Backwardation, Skew)
3. Trade-Level Metrics (Theta, Vega, ATR, DTE)
4. Per-Ticker Regime (NORMAL / CAUTION / DANGER)
5. Dashboard Regime (OFF SEASON / REGULAR SEASON / THE PLAYOFFS / THE FINALS)
6. Recommendation Labels
7. Position Construction Terms
8. Key Thresholds Quick Reference

**Open questions:** None.

---

## 4. `methodology.md`

**Purpose:** Answers "why is the math shaped this way?" — the academic basis for the scoring model, the approximations we accept, and the known limitations. For a quant-literate reader who wants to evaluate whether the approach is sound.

**Audience:** Humans (quant-oriented)

**Scope includes:**
- Academic basis: variance risk premium literature (Bollerslev-Zhou, Carr-Wu, Guo-Loeper)
- Why ATM Black-Scholes IV is used as a proxy for model-free implied variance (practical tradeoff)
- Why close-to-close RV instead of Parkinson/Yang-Zhang (data availability + simplicity)
- Why IV Percentile over IV Rank in scoring (outlier robustness)
- Why the 1.15 VRP ratio dead zone exists (transaction cost floor)
- Why the skew scoring is a trapezoid (sweet spot vs. informed flow)
- Why the negative VRP cap is at 44 (below CONDITIONAL threshold)
- Liquidity filter rationale (MIN_ATM_CONTRACTS=3, 50% spread, 200% IV cap)
- Known model limitations (no dividend adjustment, single-tenor VRP, no intraday data)

**Scope excludes:**
- The actual scoring formula and breakpoints — see `scoring-and-strategy.md`
- Trading strategy and position construction — see `references/strategy.md`
- Metric definitions — see `domain-glossary.md`

**Rot risk:** Low — methodology rarely changes; when it does, it's a major version
- `backend/calculator.py` (computation methods)
- `backend/scorer.py` (scoring shape choices)
- `references/strategy.md` (thesis)

**Section outline:**
1. The Variance Risk Premium — Academic Foundation
2. IV Approximation: ATM Black-Scholes as Practical Proxy
3. Realized Volatility: Close-to-Close Log Returns
4. IV Percentile vs. IV Rank (scoring choice)
5. Scoring Shape Rationale (dead zones, plateaus, trapezoids)
6. Liquidity Filter Design
7. Known Limitations & Accepted Approximations

**Open questions:**
- Should this reference specific papers with citations, or keep it practitioner-level? Leaning practitioner with paper names for those who want to dig deeper.

---

## 5. `scoring-and-strategy.md`

**Purpose:** Answers "how does a ticker go from raw data to SELL/SKIP?" — the complete scoring pipeline, gates, regime overrides, and how strategy becomes code. The single source of truth for "what the scoring engine actually does."

**Audience:** Both

**Scope includes:**
- The 5 scoring components with exact formulas and breakpoints (VRP 0-30, IV Pct 0-25, Term 0-20, RV 0-15, Skew 0-10)
- Gates: negative VRP cap (44), earnings gate (14 DTE, frontend-only), no-data gate
- Per-ticker regime detection: DANGER (slope>1.15), CAUTION (slope>1.05 or IVR>90+accel>1.1)
- Recommendation logic: how score + regime → SELL/CONDITIONAL/REDUCE SIZE/AVOID/NO EDGE/NO DATA
- Position construction: delta, structure, DTE, notional — keyed on regime + IV rank + VRP
- Position sizing: RV accel → Full/Half/Quarter (frontend-applied)
- Dashboard regime: OFF SEASON / REGULAR SEASON / THE PLAYOFFS / THE FINALS (frontend-computed)
- Where each piece lives in code (file + function, not line numbers)
- What backend vs. frontend is responsible for

**Scope excludes:**
- Why the math is shaped this way — see `methodology.md`
- Domain term definitions — see `domain-glossary.md`
- Strategy thesis (when to trade, daily workflow) — see `references/strategy.md`
- Metric calculation internals (how ATM IV is interpolated) — see `references/metrics_report.md`

**Rot risk:** High — any change to `scorer.py` or `scoring.ts` invalidates this file
- `backend/scorer.py` (score_opportunity function)
- `frontend/src/lib/scoring.ts` (convertApiTicker, earnings gate, sizing)
- `frontend/src/components/RegimeBanner.tsx` (computeRegime)

**Section outline:**
1. Scoring Components (5 components, exact formulas)
2. Gates (negative VRP, earnings, no-data)
3. Per-Ticker Regime Detection
4. Recommendation Logic (score + regime → action)
5. Position Construction Hints
6. Position Sizing (RV acceleration)
7. Dashboard-Level Market Regime (frontend)
8. Backend vs. Frontend Responsibility
9. Methodology Footer Discrepancy (known stale text in page.tsx)

**Open questions:** None.

---

## 6. `data-model.md`

**Purpose:** Answers "where does data live and what shape is it?" — SQLite schema, CSV formats, persistence patterns, data lifecycle.

**Audience:** Both

**Scope includes:**
- SQLite schema: 6 tables with column types, primary keys, indexes
- Which tables are pruned and to what limit (scan_results, verification tables → 50 rows)
- CSV file formats: daily/{TICKER}.csv (date-desc), quotes/{TICKER}.csv (append-only)
- Data lifecycle: how daily_iv accumulates over time for IV Rank/Percentile (252-day window)
- Earnings cache behavior (SQLite-cached, cleared on refresh, Yahoo overrides patched in-place)
- Historical data backfill process (what backfill.py does at a high level, not code walkthrough)
- JSON blob storage in scan_results (regime, tickers, historical columns)

**Scope excludes:**
- Database function signatures — read `database.py`
- CSV helper implementation — read `csv_store.py`
- Backfill script internals (BSM solver, API calls) — read `backfill.py`

**Rot risk:** Medium — triggers: new table, schema change, new CSV format
- `backend/database.py` (init_db, all table definitions)
- `backend/csv_store.py` (DAILY_HEADER, QUOTES_HEADER)

**Section outline:**
1. SQLite Database (`vol_history.db`)
2. Table: `daily_iv` (per-ticker daily IV history)
3. Table: `scan_results` (full scan JSON snapshots)
4. Table: `scan_log` (audit log)
5. Table: `earnings_cache` (FMP date cache)
6. Table: `verification_results` + `earnings_verification_results`
7. CSV Files (daily metrics + option quotes)
8. Data Lifecycle (accumulation, pruning, backfill)
9. Earnings Date Pipeline (FMP → cache → Yahoo override)

**Open questions:** None.

---

## 7. `deployment.md`

**Purpose:** Answers "how do I run, build, and deploy this?" — Docker, environment variables, volumes, Cloudflare tunnel, and operational gotchas.

**Audience:** Both

**Scope includes:**
- Docker Compose 3-service stack (backend, frontend, cloudflared)
- Port mapping: backend 8030→8000, frontend 3000→3000
- Bind mounts: `./backend/data:/app/data`, `./utils:/app/utils`
- Backend source is baked into Docker image (not bind-mounted) — requires rebuild for code changes
- Environment variables (all 5 with required/optional, purpose)
- Frontend build-time `BACKEND_URL` arg
- API proxy (next.config.js rewrites)
- Healthcheck config
- Local dev commands (backend + frontend)
- Backfill and repair script usage
- SGT timezone caveat (host in UTC+8, all trading logic uses ET)

**Scope excludes:**
- Architecture decisions — see `architecture.md`
- What the scan does — see `scoring-and-strategy.md`

**Rot risk:** Medium — triggers: new env var, new service, Docker config change
- `docker-compose.yml`
- `backend/Dockerfile`
- `frontend/Dockerfile`
- `frontend/next.config.js`

**Section outline:**
1. Docker Compose Stack
2. Environment Variables
3. Running Locally (without Docker)
4. Building & Rebuilding
5. Data Persistence (volumes, SQLite, CSVs)
6. Cloudflare Tunnel
7. Backfill & Repair Scripts
8. Operational Gotchas (SGT timezone, image rebuild, in-memory counter reset)

**Open questions:** None.

---

## 8. `fragile-seams.md`

**Purpose:** Answers "what will break if I'm not careful?" — known fragile areas, recurring bugs, data quality issues, and edge cases that have bitten before.

**Audience:** Both

**Scope includes:**
- Skew expiration alignment (recurred 2x — wide chain must pass exact date, not DTE)
- Vega convention instability (MarketData.app flips between per-1% and raw BSM)
- FMP earnings date drift (dates shift multi-week day-over-day)
- CSV append_daily_csv race condition (rewrites entire file)
- In-memory earnings refresh counter (resets on container restart)
- EEM historical IV anomaly (289.88% outlier in SQLite + CSV)
- RV10 sensitivity (single outlier close shifts acceleration across sizing thresholds)
- Skew = 0 for 5+ tickers (insufficient liquid 25-delta puts)
- UTC+8 host timezone risk (all trading logic assumes ET, Docker runs in SGT)
- Silent frontend API error handling (empty catch blocks)
- Scan gate edge case (scanned at 11pm ET → can't rescan until midnight)
- `get_previous_day_scan` walks 50 rows max (gap > 50 scans → no day-over-day)

**Scope excludes:**
- Deliberate design choices that look like bugs — see `decisions/`
- Tech debt that's annoying but not dangerous — see `known-issues` section of `CLAUDE.md`
- How to fix these — this file documents the hazard, not the remedy

**Rot risk:** High — new fragile seams discovered regularly; old ones may get fixed
- `backend/calculator.py` (liquidity filter, vega normalization, skew computation)
- `backend/marketdata_client.py` (options chain 2-call strategy)
- `backend/main.py` (scan gates, CSV persistence, earnings pipeline)
- `backend/csv_store.py` (append_daily_csv rewrite)

**Section outline:**
1. Data Quality Seams (vega convention, skew=0, EEM anomaly, RV10 sensitivity)
2. API Integration Seams (skew expiration alignment, FMP earnings drift)
3. Persistence Seams (CSV race condition, in-memory counter, scan gate edge)
4. Timezone Seams (UTC+8 host, ET trading logic)
5. Frontend Seams (silent errors, scan polling assumptions)
6. Historical Incidents (what broke, when, how it was fixed)

**Open questions:** None.

---

## 9. `decisions/` (ADR directory)

**Purpose:** Answers "why was this non-obvious choice made?" — one file per deliberate design decision that a new contributor might be tempted to "fix" without knowing the history.

**Audience:** Both

**Candidate ADRs** (to be confirmed in Phase 2):

| # | Title | Why it's non-obvious |
|---|---|---|
| 001 | Single-source scoring (backend only) | Frontend could recompute but deliberately doesn't — avoids formula drift |
| 002 | NO DATA over computed-from-rejected-contracts | MIN_ATM_CONTRACTS=3 gate. Tempting to lower threshold or skip filter. |
| 003 | Earnings gate is frontend-only | Backend doesn't know about the 14-day rule. Looks like a bug but is deliberate. |
| 004 | Negative VRP cap at 44 (not 45) | One point below CONDITIONAL threshold — intentional gap, not off-by-one. |
| 005 | Rate limit 10/min (API supports 50) | Safety margin — scan takes 13 min instead of 3. Tempting to increase. |
| 006 | Two independent regime classifiers | Backend Phase-1 names vs. frontend NBA names. Frontend ignores backend's overall_regime. |
| 007 | ScoringParams permissive override | `run_full_scan()` passes min_iv_rank=0, min_vrp=-999. Params object is vestigial. |
| 008 | Vega normalization by magnitude threshold | `|v| > 5` → divide by 100. Heuristic that handles MarketData.app convention flips. |
| 009 | Sequential scan (Semaphore=1) | Despite asyncio.gather, tickers run one at a time. Rate limit would be overwhelmed otherwise. |

**Rot risk per ADR:** Low individually (decisions don't change often), but the set grows over time.

**Open questions:**
- Are there decisions I'm missing? The XLB exclusion mentioned in the spec — I don't see XLB excluded in the current code (it's in UNIVERSE). Was this resolved?
- Should "holiday calendar duplicated in frontend and backend" be an ADR (deliberate) or a known issue (tech debt)?

---

## Summary: Proposed File Count

| File | Rot Risk | Priority |
|---|---|---|
| `scoring-and-strategy.md` | High | Phase 3 |
| `fragile-seams.md` | High | Phase 3 |
| `data-model.md` | Medium | Phase 4 |
| `architecture.md` | Medium | Phase 4 |
| `deployment.md` | Medium | Phase 4 |
| `methodology.md` | Low | Phase 4 |
| `domain-glossary.md` | Low | Phase 4 |
| `decisions/` (9 ADRs) | Low | Phase 4 |
| `README.md` | Low | Phase 4 (last) |

**Total: 8 files + 9 ADRs + README = 18 files**

---

## Phase 1 Complete — Awaiting Review

Questions for the reviewer:
1. Is the file set right? Any file that should be merged, split, added, or dropped?
2. Are the scope boundaries clean? Any overlap that bothers you?
3. Are the candidate ADRs the right set? Anything missing or not worth documenting?
4. Is the methodology.md file warranted, or is it too academic for this project?
5. Should the import graph go in architecture.md or be excluded as code-mirroring?
