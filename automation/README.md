# History Auto-Updater

Automatically appends the daily entries to **six** history files from the live dashboard:
`history/metrics-logs.md`, `history/credit-put-spreads.md`, `history/daily-briefings.md`, plus (since
2026-07-06, the v2 shadow era) `history/v2-metrics-logs.md` and `history/v2-briefings.md`, plus (since
2026-07-23) `history/portfolio-evals.md` (a daily behavioural evaluation of the OPEN journal book).
Runs on your Mac via `launchd`, uses your Claude **Max subscription** (no API cost), and **never**
touches git — you review and push manually.

## How it works
Deterministic Python fetches the scan, reproduces the exact tables, and computes every number;
Claude (headless `claude -p`) writes only the briefing prose + CPS Notable + the v2 briefing. Self-healing:
backfills any missed trading days (from the live API for today, or the prod SQLite over SSH for past days).
Capture-before-Claude: data is written before Claude runs, so an auth failure never loses data.

**The two v2 logs** read prod's `GET /api/shadow/*` endpoints (`render/shadow_table.py` renders the
deterministic divergence table; `run_v2_briefing` writes the analysis ending in a **Calibration read**).
Both are **best-effort and OFF the metrics+briefing done-gate** — a shadow-fetch or Claude failure never
blocks the v1 history (pre-deploy the job logged `shadow fetch failed (HTTP 404) — continuing`, by design).
They retire/merge into the v1 logs at the Phase E cutover.

**The portfolio-eval log** (`portfolio-evals.md`) reads the OPEN book from the prod-DB snapshot
(`positions` + `position_marks`, marked by the 18:30 scan — no journal token, no API). `render/
portfolio_eval.py` assembles the deterministic header (book summary + per-position marks/flags +
closed-today post-mortems; flags are recomputed via a faithful port of `positions_api.compute_flags`)
and `run_portfolio_eval` writes the behavioural prose. **Advisory/read-only — touches no CONFIG/
eligibility/scoring.** Empty book → no entry. Best-effort + off the v1 done-gate + self-healing like
the v2 logs; the snapshot is now taken every run (not just backfill days) so the book can be read.

Since 2026-07-15 the shadow table carries an **Earnings** column (DTE from the same day's NP payload —
the v1-UI reality check: `v1_action` in `shadow_diff` is the backend's *pre*-earnings-gate view) and the
summary line ends with **day-flips** (true day-over-day gate churn, computed against the prior trading
day's rows via `/api/shadow/diff?date=` with a DB-snapshot fallback; omitted if neither is reachable —
never blocks). Rationale: the API's `oscillation` is a rolling-window *cumulative* metric that the
briefing writer had misread as daily churn; `V2_BRIEFING_PROMPT` now carries the metric definitions.

## Run manually
```bash
python3 -m automation.run_history_update --dry-run     # fetch + render, write nothing
python3 -m automation.run_history_update --no-claude   # write data tables only (no briefing)
python3 -m automation.run_history_update --shadow      # write to staging/shadow/ (real history untouched)
python3 -m automation.run_history_update               # full: write the real history files
```

## Tests
```bash
for t in renderers core edges orchestrator claude portfolio_eval; do python3 automation/tests/test_$t.py; done
# or, from the automation/ dir:  python -m pytest -q
```

## Scheduling (launchd)
```bash
zsh automation/launchd/install.sh        # install + load the daily 09:00 SGT job
launchctl start com.optionharvest.history # run once now
launchctl list | grep optionharvest      # status
```
**The job has been LIVE since 2026-06-05** (writes the real history files daily at 09:00 SGT; runs on
next wake if the Mac was asleep). To revert to validation mode, add `<string>--shadow</string>` back to
`automation/launchd/com.optionharvest.history.plist` and re-run `install.sh` — shadow mode writes to
`staging/shadow/` and leaves the real history untouched.

`install.sh` builds a tiny ad-hoc-signed wrapper app (`launchd/ThetaHarvest.app`, from `launchd/app/`
+ `make_icon.py`) and points the job at it, so Login Items & Extensions → "Allow in the Background"
shows **"Theta Harvest"** instead of "Python Software Foundation" (the python.org code-sign identity).
Rebuild standalone with `zsh automation/launchd/build_app.sh`.

**Name vs icon:** that pane derives the row from the launched program's code-signing identity. With
free **ad-hoc** signing macOS shows the executable's *filename* (so the binary is named `Theta Harvest`)
but a **generic icon** + "unidentified developer". A custom icon (the θ `AppIcon.icns` is pre-built into
the bundle) only renders if the app is signed with a paid **Apple Developer ID**, or registered via
**SMAppService**. Name was the free win; the icon was not worth a paid cert.

## Shadow validation (historical — completed 2026-06-05)
The original rollout ran ~2 weeks in `--shadow`, comparing `staging/shadow/*.md` against hand-written
entries each morning, then flipped live. The mode remains available for validating future pipeline changes.

## Gotchas
- **Paths are hardcoded** in `launchd/run.sh` AND `launchd/app/launcher.c` (nvm node + framework
  python). If node or python is upgraded, update the paths in both, then `zsh build_app.sh` (it
  recompiles `launcher.c` — the app's main executable must be a Mach-O binary, not a script, or
  Login Items shows it as a loose script instead of the "Theta Harvest" app).
- **Full Disk Access is not required** — the repo lives under `~/Projects`, which is not a TCC-protected
  folder. (Historically, when the repo sat under `~/Downloads`, FDA had to be granted to
  `launchd/ThetaHarvest.app` and re-confirmed after every rebuild; moving to `~/Projects` removed that.)
- `ANTHROPIC_API_KEY` must stay **unset** in the job env (the wrapper unsets it) so Claude uses the
  Max plan, not the paid API.
- If the Max session expires, the run leaves briefings pending and fires a macOS notification —
  run `claude` once to re-login and the next run backfills them.
