# Build the /context Folder for Option Harvest

## Mission

Build a `/context/` folder at the project root that captures the curated, current-state knowledge a new contributor — human or Claude Code agent — needs to be productive without reading 8,500 lines of source. The folder is **derived explanation**. It is neither primary source material nor a code mirror.

**Definition of done:** A new reader opens `/context/README.md`, follows the reading order, and within 30 minutes understands the domain, the architecture, the non-obvious design choices, and where to look next. Nothing in `/context/` duplicates code. Every file has a freshness header and a clean scope boundary.

---

## Existing Repo State (What You're Working With)

- `CLAUDE.md` at root — session-bootstrap instructions for Claude Code (currently gitignored)
- `references/` — canonical primary sources:
  - `strategy.md` — the trading strategy thesis (AUTHORITATIVE, do not duplicate)
  - `metrics_report.md` — metrics research (AUTHORITATIVE, do not duplicate)
  - `checkpoints/` — historical phase summaries, partially stale
- `tasks/notes.md` — ~1,310 lines of curated study notes, validated against code
- `backend/` — 12 Python files (main, calculator, scorer, database, marketdata_client, fmp_client, csv_store, models, backfill, repair_rv, tests)
- `frontend/` — 18 TypeScript files (Next.js 14)
- Data: SQLite (6 tables) + CSVs
- Deployment: Docker on Windows, Cloudflare tunnel, host in SGT (UTC+8)

---

## Architectural Principles (Non-Negotiable)

1. **No code-mirroring.** Do NOT write `backend.md` or `frontend.md` that lists every module, function, constant, or import graph. Well-named code + docstrings already do that job and can't drift. Docs exist to capture what code *can't* encode: *why*, *what's weird*, *what domain terms mean*, and *how pieces fit above the implementation*.

2. **`/context/` is derived; `/references/` is primary.** Link liberally from `/context/` into `/references/`. Never duplicate strategy or metrics content.

3. **Decisions ≠ Known Issues.** A *decision* is a deliberate, non-obvious choice that's easy to second-guess later (why XLB is excluded; why NO DATA is preferred over computed-from-rejected-contracts). A *known issue* is a fragile seam or gotcha (skew expiration alignment bug, UTC+8 date risk, FMP earnings drift). These go in different files.

4. **Every file has a Freshness Header.** No exceptions.

5. **Every file has a Scope Boundary** at the top, explicitly listing what it does NOT cover and where that content lives.

6. **Favor fewer, cleaner files over many overlapping ones.** If three files all want to own "data flow between frontend and backend," pick one. Overlap is the #1 cause of doc rot.

---

## Candidate File Set (Subject to Revision in Phase 1)

This is a starting hypothesis. Phase 1 may reshape it.

- `README.md` — index, reading order, audience routing (new human vs. agent)
- `architecture.md` — service boundaries, data flow, codebase map (high-level only)
- `domain-glossary.md` — VRP, IV percentile, 25-delta skew, term structure, RV acceleration, regime labels, with formulas
- `methodology.md` — academic basis: Bollerslev-Zhou, Carr-Wu, Guo-Loeper, the ATM-BS-as-approximation caveat
- `scoring-and-strategy.md` — composite 0–100 scoring, gates (negative VRP, MIN_ATM_CONTRACTS, IV bounds), how strategy becomes code
- `data-model.md` — SQLite schema, CSV formats, persistence patterns
- `deployment.md` — Docker, env vars, Cloudflare tunnel, rebuild workflow, SGT timezone caveat
- `fragile-seams.md` — skew expiration alignment (recurred 2x), UTC+8 date risk, FMP earnings drift, liquidity edge cases
- `decisions/` — one ADR per non-obvious design choice

---

## Workflow — 5 Phases with Explicit STOP Points

### Phase 1: Skeleton Draft → STOP for review

Produce a single file `context/SKELETONS.md` containing one section per proposed file. Each section must include:

- **Proposed filename**
- **Purpose** — one sentence: what question does this file answer that no other file does?
- **Audience** — humans / agents / both
- **Scope includes** — 3–6 bullets of what this file owns
- **Scope excludes** — 2–4 bullets of what it does NOT cover, with pointers to where each lives
- **Rot risk** — high / medium / low, with specific source paths that should trigger updates
- **Section outline** — 5–10 H2/H3 headers, no content
- **Open questions** — anything you're unsure about, especially overlap with other files

Then STOP and request review. Do NOT write prose content yet.

### Phase 2: Content-Source Mapping → STOP for review

Produce `context/SOURCE_MAP.md` — a migration plan:

- For each approved file, list source material (line ranges from `tasks/notes.md`, sections of `references/checkpoints/`, specific source files to reference but not duplicate)
- Flag content in `tasks/notes.md` that has NO natural home in `/context/` — decide explicitly whether it stays in notes or gets archived
- Flag content in `references/checkpoints/` that is stale and should be archived rather than migrated
- Identify candidate ADRs for the `decisions/` folder

Then STOP and request review. Migration scope must be explicit before writing begins.

### Phase 3: Write the Two Highest-Rot-Risk Files First → STOP for review

Write `scoring-and-strategy.md` and `fragile-seams.md` in full, following the Final File Template below. These are the highest-stakes files — staleness here causes production issues. Getting tone, depth, and format right on these two sets the quality bar for the remaining files.

Then STOP and request review. These two gate the rest.

### Phase 4: Write Remaining Files

Once the reference pair is approved, write the rest in this order (highest rot risk first):

1. `data-model.md`
2. `architecture.md`
3. `deployment.md`
4. `methodology.md`
5. `domain-glossary.md`
6. `decisions/` ADRs (one per non-obvious decision)
7. `README.md` — written LAST because it indexes everything else

### Phase 5: Integration & Cleanup

- Add `@context/` imports to `CLAUDE.md` for the most session-relevant files (likely `architecture.md`, `scoring-and-strategy.md`, `fragile-seams.md`). Trim `CLAUDE.md` of anything now better-covered in `/context/`.
- Rename `references/checkpoints/` → `references/archive/`. Add `references/archive/README.md` clarifying these are historical snapshots, not authoritative.
- Do NOT delete `tasks/notes.md`. It remains the raw scratchpad.
- Commit each phase separately for clean history.

---

## Final File Template

Every `/context/` file (except `README.md` and ADRs) must open with:

```markdown
---
last_verified: YYYY-MM-DD
verified_against: <git short hash>
rot_risk: high | medium | low
rot_triggers:
  - backend/scorer.py
  - backend/calculator.py
audience: humans | agents | both
---

# <File Title>

## Purpose
<One paragraph: what question does this file answer? Why does it exist?>

## Scope
**This file covers:**
- <explicit list>

**This file does NOT cover:**
- <X> — see `context/<other-file>.md`
- <Y> — see `references/strategy.md`

## <First content section>
...
```

---

## ADR Template (decisions/NNN-short-title.md)

```markdown
---
last_verified: YYYY-MM-DD
verified_against: <git short hash>
status: active | superseded-by-XXX | deprecated
---

# ADR-NNN: <Short title>

## Context
<What situation forced a choice? What constraints were in play?>

## Decision
<What was chosen, one paragraph.>

## Alternatives Considered
<2–4 other options and why each was rejected.>

## Consequences
<What this decision makes easy, what it makes hard, what it locks in.>

## Revisit If
<Specific conditions that should trigger reopening this decision.>
```

**Example ADRs to consider** (identify the full list during Phase 1):
- Single-source scoring (backend owns the formula; frontend never recomputes)
- NO DATA preferred over computed-from-rejected-contracts when MIN_ATM_CONTRACTS fails
- Hardcoded XLB exclusion
- Negative VRP gate capping composite score at 44
- ATM Black-Scholes IV as practical proxy for model-free implied variance

---

## Quality Bar

**Good:**
- A quant-literate reader understands *why* the scoring formula is shaped this way after 10 minutes with `scoring-and-strategy.md` + `methodology.md`.
- A new engineer touching `calculator.py` reads `fragile-seams.md` first and learns the two prior skew-alignment failures before making changes.
- Every file is readable in under 15 minutes.
- Every cross-file reference is a link, not a duplicate.

**Bad:**
- Walls of prose explaining what a function does (the code already does this better).
- Stale information with no freshness header to warn the reader.
- Three files all claiming to own "how frontend talks to backend."
- An ADR that reads as a current-state description rather than a choice-with-alternatives.
- Migration that silently drops content from `tasks/notes.md` without flagging it.

---

## When in Doubt

- **Unsure whether content belongs in `/context/` or stays in `tasks/notes.md`?** Default to `tasks/notes.md` until the content has been re-validated and has a clear home.
- **Unsure whether a choice is a Decision or a Known Issue?** Ask: *"Would a new contributor be tempted to 'fix' this without knowing the history?"* If yes → Decision (ADR). If it's just a bug we know about → `fragile-seams.md`.
- **Unsure whether to merge two proposed files?** Merge. It's cheaper to split later than to dedupe later.
- **Unsure about factual content?** Do not invent. Flag it in the Open Questions section for Phase 1 review.

---

## Do NOT

- Do NOT duplicate `references/strategy.md` or `references/metrics_report.md`. Link to them.
- Do NOT produce a file that walks through every module or function. That's what the code is for.
- Do NOT skip the STOP points. Phases 1, 2, and 3 each require explicit human review before proceeding.
- Do NOT delete anything in `references/` or `tasks/` without explicit approval. Archive instead.
- Do NOT write `README.md` before the other files exist. It must index real content.

---

## Start Here

Begin Phase 1 now. Produce `context/SKELETONS.md` per the spec above, then stop and await review.
