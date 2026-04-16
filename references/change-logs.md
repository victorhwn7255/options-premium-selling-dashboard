# Change Log

Project change history in reverse chronological order. Most recent changes appear at the top.

---

## Update Protocol

**When to add an entry:** After any session that produces a meaningful change — new feature, bug fix, architectural change, scoring adjustment, or infrastructure update. Do not log trivial edits (typos, formatting, comment tweaks).

**Who updates:** The agent (or contributor) at the end of a work session, before handing back to the user.

**How to update:**
1. Add a new row at the **top** of the table (below the header row)
2. Fill all columns — leave nothing blank
3. `Version` = the branch name or release tag (e.g., `v1.20`). Use `—` for changes on `main` between releases
4. `Category` = one of: `Feature`, `Fix`, `Refactor`, `Infra`, `Docs`, `Data`
5. `Summary` = one sentence describing *what changed and why* — not a commit message
6. `Key files` = 2-4 most important files touched (not every file)

**Granularity:** One row per logical change, not per commit. A feature that took 3 commits gets one row. A session that fixed 2 unrelated bugs gets 2 rows.

---

## Log

| Date | Version | Category | Summary | Key files |
|------|---------|----------|---------|-----------|
| 2026-04-16 | v1.20 | Docs | Restructured `/context/` into tiered subdirectories (`1-domain/`, `2-system/`, `3-guardrails/`); rewrote `start-here.md` as agent onboarding entry point with reading order | `context/start-here.md`, `CLAUDE.md` |
| 2026-04-16 | v1.20 | Docs | Updated CLAUDE.md with accurate endpoint table, test commands, ticker count, git policy, and agent onboarding instructions | `CLAUDE.md` |
| 2026-04-16 | v1.15 | Docs | Built initial `/context/` folder — glossary, methodology, scoring-and-strategy, architecture, data-model, deployment, fragile-seams, 11 ADRs | `context/` (all files) |
| 2026-04-15 | v1.15 | Fix | Added vega normalization heuristic — MarketData.app intermittently returns raw BSM vega (~100x larger); divide by 100 when \|vega\| > 5 | `backend/calculator.py` |
| 2026-04-02 | v1.12 | Feature | Added strategy summary and OpenBB data exploration | `references/strategy.md` |
| 2026-03-27 | v1.11 | Feature | UI improvements — dark/light theme, ticker drawer, score breakdown, keyboard navigation | `frontend/src/components/`, `frontend/src/hooks/`, `globals.css` |
| 2026-03-25 | v1.08 | Feature | Day-over-day scan comparison; shows delta badges for score, IV rank, VRP changes | `backend/main.py`, `backend/database.py`, `frontend/src/app/page.tsx` |
| 2026-03-25 | v1.08 | Fix | Skew expiration alignment (recurrence) — switched from `dte=` to `expiration=YYYY-MM-DD` to match API exactly | `backend/marketdata_client.py` |
| 2026-03-25 | v1.08 | Fix | CSV date bug — `append_daily_csv()` used stale bar date instead of current ET trading date | `backend/csv_store.py` |
| 2026-03-25 | v1.08 | Refactor | Replaced penalty-based scoring with additive model (VRP 0-30, IV Pct 0-25, Term 0-20, RV 0-15, Skew 0-10) | `backend/scorer.py`, `frontend/src/lib/scoring.ts` |
| 2026-03-21 | v1.07 | Fix | Skew expiration alignment — wide chain hardcoded `dte=30`, causing most tickers to have zero skew | `backend/marketdata_client.py`, `backend/calculator.py` |
| 2026-03-13 | v1.05 | Fix | Bug fixes for scoring and data pipeline stability | `backend/` |
| 2026-02-22 | v1.03 | Feature | Yahoo Finance earnings verification — cross-checks FMP dates, auto-overrides on >5-day discrepancy | `backend/main.py`, `utils/verify_metrics.py` |
| 2026-02-18 | v1.02 | Feature | Frontend upgrades — leaderboard UI, regime banner, detail panel | `frontend/src/components/`, `frontend/src/app/page.tsx` |
| 2026-02-14 | v1.00 | Infra | Cloudflare tunnel deployment, PC hosting setup, Docker compose stack | `docker-compose.yml`, `backend/Dockerfile`, `frontend/Dockerfile` |
| 2026-02-14 | v1.00 | Feature | Initial release — full scan pipeline, scoring engine, SQLite persistence, Next.js dashboard | `backend/`, `frontend/` |
