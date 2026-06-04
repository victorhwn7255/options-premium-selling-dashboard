# History Auto-Updater

Automatically appends the daily entries to `history/metrics-logs.md`, `history/credit-put-spreads.md`,
and `history/daily-briefings.md` from the live dashboard. Runs on your Mac via `launchd`, uses your
Claude **Max subscription** (no API cost), and **never** touches git — you review and push manually.

## How it works
Deterministic Python fetches the scan, reproduces the exact tables, and computes every number;
Claude (headless `claude -p`) writes only the briefing prose + CPS Notable. Self-healing: backfills
any missed trading days (from the live API for today, or the prod SQLite over SSH for past days).
Capture-before-Claude: data is written before Claude runs, so an auth failure never loses data.

## Run manually
```bash
python3 -m automation.run_history_update --dry-run     # fetch + render, write nothing
python3 -m automation.run_history_update --no-claude   # write data tables only (no briefing)
python3 -m automation.run_history_update --shadow      # write to staging/shadow/ (real history untouched)
python3 -m automation.run_history_update               # full: write the real history files
```

## Tests
```bash
for t in renderers core edges orchestrator claude; do python3 automation/tests/test_$t.py; done
```

## Scheduling (launchd)
```bash
zsh automation/launchd/install.sh        # install + load the daily 09:00 SGT job
launchctl start com.optionharvest.history # run once now
launchctl list | grep optionharvest      # status
```
The plist ships in **`--shadow`** mode (writes to `staging/shadow/`). After the shadow-validation
period, edit `automation/launchd/com.optionharvest.history.plist`, remove the `<string>--shadow</string>`
line, and re-run `install.sh` to go live on the real history files.

## Phase 6 — shadow validation
For ~1–2 weeks, let it run in `--shadow` and each morning compare `staging/shadow/*.md` against what
you'd write by hand. When consistent, flip to live (above).

## Gotchas
- **Paths are hardcoded** in `launchd/run.sh` (nvm node + framework python). If node or python is
  upgraded, update the two paths there.
- `ANTHROPIC_API_KEY` must stay **unset** in the job env (the wrapper unsets it) so Claude uses the
  Max plan, not the paid API.
- If the Max session expires, the run leaves briefings pending and fires a macOS notification —
  run `claude` once to re-login and the next run backfills them.
