---
last_verified: 2026-04-16
verified_against: 2134cff
---

# Context — Theta Harvest

Curated knowledge for onboarding new contributors (human or Claude Code agent) without reading 8,500 lines of source. Each file has a freshness header and explicit scope boundary. Cross-references point to primary sources in [`references/`](../references/) and to the code itself — nothing here duplicates what well-named code already says.

## What is Theta Harvest?

A volatility premium scanner for options sellers. Scans 33 tickers daily after market close, computes implied vs. realized volatility metrics, scores each on a 0–100 scale for premium-selling edge, classifies market regimes, and presents actionable trade construction on a single-page dashboard.

## Reading Order

**If you're about to write code:** Start with `architecture.md` (how pieces connect), then `scoring-and-strategy.md` (the core logic), then `fragile-seams.md` (what will break).

**If you're about to deploy or operate:** Start with `deployment.md`.

**If you're new to options selling:** Start with `domain-glossary.md`, then read [`references/strategy.md`](../references/strategy.md).

**If you're evaluating the model:** Start with `methodology.md`, then `scoring-and-strategy.md`.

## File Index

| File | Purpose |
|------|---------|
| [`architecture.md`](architecture.md) | Service topology, data flow, ownership boundary, module graph |
| [`scoring-and-strategy.md`](scoring-and-strategy.md) | Scoring formula, gates, regime detection, recommendations, position construction |
| [`fragile-seams.md`](fragile-seams.md) | Known fragile areas, hazards, historical incidents |
| [`data-model.md`](data-model.md) | SQLite schema (6 tables), CSV formats, data lifecycle |
| [`deployment.md`](deployment.md) | Docker stack, env vars, local dev, CLI scripts, operational gotchas |
| [`methodology.md`](methodology.md) | Academic basis, approximation rationale, known model limitations |
| [`domain-glossary.md`](domain-glossary.md) | Term definitions, formulas, thresholds quick reference |
| [`decisions/`](decisions/) | Architecture Decision Records (11 ADRs) — non-obvious design choices |

### Decisions Index

| ADR | Title |
|-----|-------|
| [001](decisions/001-single-source-scoring.md) | Single-source scoring (backend only) |
| [002](decisions/002-no-data-over-computed-from-rejected.md) | NO DATA over computed-from-rejected contracts |
| [003](decisions/003-earnings-gate-frontend-only.md) | Earnings gate is frontend-only |
| [004](decisions/004-negative-vrp-cap-at-44.md) | Negative VRP cap at 44 (not 45) |
| [005](decisions/005-rate-limit-10-per-minute.md) | Rate limit 10 calls/min (API supports 50) |
| [006](decisions/006-two-independent-regime-classifiers.md) | Two independent regime classifiers |
| [007](decisions/007-scoring-params-permissive-override.md) | ScoringParams permissive override |
| [008](decisions/008-vega-normalization-heuristic.md) | Vega normalization by magnitude threshold |
| [009](decisions/009-sequential-scan-semaphore-1.md) | Sequential scan (Semaphore=1) |
| [010](decisions/010-holiday-calendar-duplicated.md) | Holiday calendar duplicated in frontend and backend |
| [011](decisions/011-additive-scoring-replaces-penalty-based.md) | Additive scoring replaces penalty-based |

## Primary Sources

These are canonical and authoritative — `/context/` links to them but does not duplicate their content:

| File | What it covers |
|------|----------------|
| [`references/strategy.md`](../references/strategy.md) | Trading strategy thesis, the 5 signals, daily workflow, position management |
| [`references/metrics_report.md`](../references/metrics_report.md) | Every metric formula, data source, computation detail |

## Keeping Context Fresh

Every file has a `last_verified` date and `verified_against` git hash in its frontmatter. When you change code listed in a file's `rot_triggers`, update the corresponding context file. High-rot-risk files (`scoring-and-strategy.md`, `fragile-seams.md`) should be re-verified after any change to `scorer.py`, `calculator.py`, `scoring.ts`, or `RegimeBanner.tsx`.
