---
last_verified: 2026-04-16
verified_against: dc030c3
rot_risk: low
rot_triggers:
  - context/ (any file added or removed)
audience: both
---

# Context — Theta Harvest

## Agent Onboarding Instructions

**If you are a new Claude Code agent starting a session, follow these steps:**

1. **Read every file in this `/context/` folder** in the order listed below. Do not skip any files.
2. **Also read** the two primary source files: [`references/strategy.md`](../references/strategy.md) and [`references/metrics.md`](../references/metrics.md).
3. **Read session memory** — these carry knowledge from previous agents:
   - [`tasks/lessons.md`](../tasks/lessons.md) — mistakes and patterns from past sessions (learn so you don't repeat them)
   - [`references/change-logs.md`](../references/change-logs.md) — recent project changes in reverse chronological order
4. **After reading everything**, respond to the user with a structured summary of your understanding — cover: what the project does, the architecture, the scoring engine, the regime system, key fragile areas, and important design decisions.
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
| 12 | [`tasks/lessons.md`](../tasks/lessons.md) | Mistakes and patterns from previous agents — avoid repeating them |
| 13 | [`references/change-logs.md`](../references/change-logs.md) | Recent project changes — know what was last touched and why |

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

**Rule of thumb for decisions vs. fragile seams:**
- If a new contributor would be tempted to "fix" it without reading history → decision (ADR).
- If it's a bug you've mapped but not fully cured → fragile seam.

---

## Freshness Discipline

Every file has a `last_verified` date and `verified_against` git hash in its frontmatter. When you change code listed in a file's `rot_triggers`, update the corresponding context file. If a header is more than a quarter stale, flag it for re-verification rather than trusting it — stale reference material is worse than none.

High-rot-risk files (`1-domain/scoring-and-strategy.md`, `3-guardrails/fragile-seams.md`) should be re-verified after any change to `scorer.py`, `calculator.py`, `scoring.ts`, or `RegimeBanner.tsx`.
