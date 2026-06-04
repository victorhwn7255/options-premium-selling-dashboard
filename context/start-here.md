---
last_verified: 2026-06-04
verified_against: main
rot_risk: low
rot_triggers:
  - context/ (any file added or removed)
  - references/ (CPS docs added or removed)
  - tasks/todo.md (added/removed)
  - history/credit-put-spreads.md (added/removed)
  - automation/ (history auto-updater added/changed)
audience: both
---

# Context — Theta Harvest

## Agent Onboarding Instructions

**If you are a new Claude Code agent starting a session, follow these steps:**

1. **Read every file in this `/context/` folder** in the order listed below. Do not skip any files.
2. **Also read** the primary source files: [`references/strategy.md`](../references/strategy.md), [`references/metrics.md`](../references/metrics.md), [`references/credit-put-spreads.md`](../references/credit-put-spreads.md), and [`references/credit_put_spreads_build_plan.md`](../references/credit_put_spreads_build_plan.md).
3. **Read session memory and active state** — these carry knowledge from previous agents and current work:
   - [`tasks/lessons.md`](../tasks/lessons.md) — mistakes and patterns from past sessions (learn so you don't repeat them)
   - [`references/change-logs.md`](../references/change-logs.md) — recent project changes in reverse chronological order
   - [`tasks/todo.md`](../tasks/todo.md) — post-MVP backlog with prioritized bands
   - [`history/daily-briefings.md`](../history/daily-briefings.md) latest 5-7 entries — current regime, active positions
   - [`history/credit-put-spreads.md`](../history/credit-put-spreads.md) latest 3-5 entries — CPS confirmation streaks, c/w patterns
4. **After reading everything**, respond to the user with a structured summary of your understanding — cover: what the project does, the architecture, the scoring engine (Naked Puts + Credit Put Spreads), the regime system, current market regime and active positions, the **history auto-updater** (`automation/`), key fragile areas, and important design decisions.
5. **Wait for the user to confirm** your understanding is correct before starting any task.

### Reading Order

Read in this exact sequence:

| Step | File | What you'll learn |
|------|------|-------------------|
| 1 | This file (`start-here.md`) | Project overview, file map, how context is organized |
| 2 | `1-domain/glossary.md` | Domain vocabulary — VRP, IV percentile, skew, regime labels, thresholds |
| 3 | `1-domain/methodology.md` | Why the math is shaped this way — academic basis, approximations, limitations |
| 4 | `1-domain/scoring-and-strategy.md` | The complete scoring pipeline — 5 components, gates, regime, recommendations |
| 5 | `2-system/architecture.md` | Service topology, scan lifecycle, frontend data flow, ownership boundary |
| 6 | `2-system/data-model.md` | SQLite schema, CSV formats, data lifecycle |
| 7 | `2-system/deployment.md` | Docker stack, env vars, CLI scripts, operational gotchas |
| 8 | `3-guardrails/fragile-seams.md` | Known hazards that will break if you're not careful |
| 9 | `3-guardrails/decisions/` (all 11 ADRs) | Non-obvious design choices — read so you don't accidentally "fix" them |
| 10 | [`references/strategy.md`](../references/strategy.md) | Trading strategy thesis (primary source) |
| 11 | [`references/metrics.md`](../references/metrics.md) | Metric formulas and computation details (primary source) |
| 12 | [`references/credit-put-spreads.md`](../references/credit-put-spreads.md) | CPS canonical spec — defined-risk strategy, gates, position rules |
| 13 | [`references/credit_put_spreads_build_plan.md`](../references/credit_put_spreads_build_plan.md) | CPS build plan — Phase 1-5 shipped, Phase 6 items still active |
| 14 | [`tasks/lessons.md`](../tasks/lessons.md) | Mistakes and patterns from previous agents — avoid repeating them |
| 15 | [`references/change-logs.md`](../references/change-logs.md) | Recent project changes — know what was last touched and why |
| 16 | [`tasks/todo.md`](../tasks/todo.md) | Post-MVP backlog — what's queued and prioritized |
| 17 | [`history/daily-briefings.md`](../history/daily-briefings.md) (latest 5-7 entries) | Recent trading analysis — regime context, active positions, market state |
| 18 | [`history/credit-put-spreads.md`](../history/credit-put-spreads.md) (latest 3-5 entries) | Recent CPS scan snapshots — confirmation streaks, c/w patterns |
| 19 | [`automation/README.md`](../automation/README.md) | **History auto-updater** — the daily pipeline that now writes the 3 `history/` files automatically (deterministic tables + Claude-written briefings on the Max plan, launchd-scheduled, shadow/live modes, capture-before-Claude). Read so you don't duplicate or fight it. |

---

## What Is This Folder?

Curated knowledge for onboarding new contributors (human or Claude Code agent) without reading 8,500 lines of source. Each file has a freshness header and explicit scope boundary.

This folder is **derived explanation** — it captures *why*, *what's weird*, *how pieces fit together*, and *what will break*. It is not primary source material (that's [`references/`](../references/)) and not a code mirror (well-named source code is its own documentation).

## Quick Reading Paths (for humans)

**Writing code** (45 min): `1-domain/glossary.md` → `2-system/architecture.md` → `1-domain/scoring-and-strategy.md` → `3-guardrails/fragile-seams.md`.

**Deploying or debugging ops** (15 min): `2-system/deployment.md` → `3-guardrails/fragile-seams.md`.

**New to options selling** (30 min): `1-domain/glossary.md` → `1-domain/methodology.md` → [`references/strategy.md`](../references/strategy.md).

**Evaluating the model** (20 min): `1-domain/methodology.md` → `1-domain/scoring-and-strategy.md`.

---

## File Map

### `1-domain/` — Understand WHAT the system does

| File | Question it answers |
|------|---------------------|
| [`glossary.md`](1-domain/glossary.md) | What does this term mean? Definitions, formulas, thresholds for every domain concept. |
| [`methodology.md`](1-domain/methodology.md) | Why is the math shaped this way? Academic basis, approximations, known limitations. |
| [`scoring-and-strategy.md`](1-domain/scoring-and-strategy.md) | How does a ticker go from raw data to SELL/SKIP/AVOID? The complete scoring pipeline. |

### `2-system/` — Understand HOW it's built and run

| File | Question it answers |
|------|---------------------|
| [`architecture.md`](2-system/architecture.md) | How do the pieces fit together? Service topology, data flow, ownership boundary. |
| [`data-model.md`](2-system/data-model.md) | Where does data live and what shape is it? SQLite schema, CSV formats, lifecycle. |
| [`deployment.md`](2-system/deployment.md) | How do I run, build, and deploy this? Docker, env vars, CLI scripts, operational gotchas. |

### `3-guardrails/` — Read BEFORE changing code

| File | Question it answers |
|------|---------------------|
| [`fragile-seams.md`](3-guardrails/fragile-seams.md) | What will break if I'm not careful? Known hazards and historical incidents. |
| [`decisions/`](3-guardrails/decisions/) | Why was this non-obvious choice made? 11 ADRs documenting deliberate design decisions. |

### `history/` — Daily operational artifacts

| File | Question it answers |
|------|---------------------|
| [`metrics-logs.md`](../history/metrics-logs.md) | What were the raw Naked Puts scan numbers? One table per trading day with all 33 tickers, sorted by score. |
| [`daily-briefings.md`](../history/daily-briefings.md) | What was the analysis? Regime assessment, day-over-day deltas, trade recommendations, position calls. |
| [`credit-put-spreads.md`](../history/credit-put-spreads.md) | What were the CPS scan candidates? Scan summary + overlay + candidates table per day; confirmation streaks and c/w patterns. |

These files are maintained two ways: **(1) manually** through the **Daily Scan Workflow** (see `CLAUDE.md`) when the user pastes metrics (the `daily-briefing` skill analyses, recommends, and logs to all three files), and **(2) automatically** by the **history auto-updater** in [`automation/`](../automation/README.md) — a launchd-scheduled daily job that does the same thing unattended (deterministic tables + Claude-written briefings on the Max plan). Both write the identical format; don't hand-log a day the automation already covered.

### `automation/` — How the history files get written automatically

| File | Question it answers |
|------|---------------------|
| [`automation/README.md`](../automation/README.md) | What is the auto-updater, how do I run it (`--dry-run`/`--no-claude`/`--shadow`), how is it scheduled, and what are the gotchas? |

Architecture: a deterministic Python spine (`render/`, `sources/`, `history/`) reproduces the dashboard's exact tables and computes every number; headless Claude (`claude/`) writes only the briefing prose + CPS Notable on the user's Max subscription. **Capture-before-Claude** (data written before Claude runs → zero loss on auth failure), idempotent, self-healing backfill, **no git automation**. Validated by `automation/tests/` (87 byte-exact + behavioral checks).

## Sibling Skills

When the user pastes daily Naked Puts scan metrics or a CPS tab copy-button output, invoke the `daily-briefing` skill — it handles the analysis + logging workflow against `history/`. Don't reimplement that workflow inside an onboarding session.

### Decisions Index

| ADR | Title |
|-----|-------|
| [001](3-guardrails/decisions/001-single-source-scoring.md) | Single-source scoring (backend only) |
| [002](3-guardrails/decisions/002-no-data-over-computed-from-rejected.md) | NO DATA over computed-from-rejected contracts |
| [003](3-guardrails/decisions/003-earnings-gate-frontend-only.md) | Earnings gate is frontend-only |
| [004](3-guardrails/decisions/004-negative-vrp-cap-at-44.md) | Negative VRP cap at 44 (not 45) |
| [005](3-guardrails/decisions/005-rate-limit-10-per-minute.md) | Rate limit 10 calls/min (API supports 50) |
| [006](3-guardrails/decisions/006-two-independent-regime-classifiers.md) | Two independent regime classifiers |
| [007](3-guardrails/decisions/007-scoring-params-permissive-override.md) | ScoringParams permissive override |
| [008](3-guardrails/decisions/008-vega-normalization-heuristic.md) | Vega normalization by magnitude threshold |
| [009](3-guardrails/decisions/009-sequential-scan-semaphore-1.md) | Sequential scan (Semaphore=1) |
| [010](3-guardrails/decisions/010-holiday-calendar-duplicated.md) | Holiday calendar duplicated in frontend and backend |
| [011](3-guardrails/decisions/011-additive-scoring-replaces-penalty-based.md) | Additive scoring replaces penalty-based |

---

## Primary Sources

These are canonical and authoritative — `/context/` links to them but does not duplicate their content:

| File | What it covers |
|------|----------------|
| [`references/strategy.md`](../references/strategy.md) | Trading strategy thesis, the 5 signals, daily workflow, position management |
| [`references/metrics.md`](../references/metrics.md) | Every metric formula, data source, computation detail |

---

## Where New Content Goes

| When this happens                                     | Update this file                                    |
|------------------------------------------------------|-----------------------------------------------------|
| New domain term or formula                           | `1-domain/glossary.md`                              |
| Scoring formula or gate change                       | `1-domain/scoring-and-strategy.md`                  |
| New academic reference or methodology shift          | `1-domain/methodology.md`                           |
| Service added/removed, module boundary changed       | `2-system/architecture.md`                          |
| Schema change (SQLite or CSV)                        | `2-system/data-model.md`                            |
| Deployment, env, or infra change                     | `2-system/deployment.md`                            |
| New recurring bug, gotcha, or race condition         | `3-guardrails/fragile-seams.md`                     |
| Non-obvious design choice with rejected alternatives | New ADR in `3-guardrails/decisions/`                |
| User pastes daily scan metrics                       | `history/metrics-logs.md` + `history/daily-briefings.md` (see Daily Scan Workflow in CLAUDE.md) |

**Rule of thumb for decisions vs. fragile seams:**
- If a new contributor would be tempted to "fix" it without reading history → decision (ADR).
- If it's a bug you've mapped but not fully cured → fragile seam.

---

## Freshness Discipline

Every file has a `last_verified` date and `verified_against` git hash in its frontmatter. When you change code listed in a file's `rot_triggers`, update the corresponding context file. If a header is more than a quarter stale, flag it for re-verification rather than trusting it — stale reference material is worse than none.

High-rot-risk files (`1-domain/scoring-and-strategy.md`, `3-guardrails/fragile-seams.md`) should be re-verified after any change to `scorer.py`, `calculator.py`, `scoring.ts`, or `RegimeBanner.tsx`.
