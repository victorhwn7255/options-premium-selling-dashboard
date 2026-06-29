"""Central configuration for the history auto-updater."""
from __future__ import annotations

import os
from pathlib import Path
from zoneinfo import ZoneInfo

REPO_ROOT = Path(__file__).resolve().parents[1]
HISTORY_DIR = REPO_ROOT / "history"
METRICS_FILE = HISTORY_DIR / "metrics-logs.md"
CPS_FILE = HISTORY_DIR / "credit-put-spreads.md"
BRIEFINGS_FILE = HISTORY_DIR / "daily-briefings.md"

AUTOMATION_DIR = REPO_ROOT / "automation"
STAGING_DIR = AUTOMATION_DIR / "staging"
LOG_FILE = AUTOMATION_DIR / "logs" / "run.log"

# --- Public API (daily, common case) -------------------------------------------------
API_BASE = "https://theta.thevixguy.com"
# Cloudflare 403s the default urllib User-Agent, so always send a real one.
USER_AGENT = "theta-harvest-automation/1.0 (history-updater)"
HTTP_TIMEOUT = 30

# Network resilience for the wake-race: the launchd job fires at 09:00 as the Mac wakes,
# often before Wi-Fi/DNS is ready — the first fetch then dies with socket.gaierror / URLError
# and crashes the whole run (see launchd.err 2026-06-26..28). Retry transient DNS/connection/
# 5xx failures with exponential backoff so the run self-heals instead of losing the day.
# Coverage ≈ 3 + 6 + 12 + 24 + 30 + 30 ≈ 105s across the retries — enough for Wi-Fi to associate.
HTTP_MAX_ATTEMPTS = 7    # total tries before giving up
HTTP_RETRY_BASE = 3      # seconds; per-attempt sleep = min(BASE * 2**(n-1), CAP)
HTTP_RETRY_CAP = 30      # max seconds between attempts

# --- Lightsail SQLite (backfill only) ------------------------------------------------
SSH_ALIAS = "option-harvest"
REMOTE_DB = "~/option-harvest/backend/data/vol_history.db"
SSH_TIMEOUT = 120

# --- Constants -----------------------------------------------------------------------
ET = ZoneInfo("America/New_York")
NP_BACKFILL_LIMIT = 50   # scan_results prune window (scans)
CPS_BACKFILL_LIMIT = 14  # cps_scan_responses prune window (days)
MIN_TICKERS = 30         # partial-scan guard (mirrors backend get_vrp_history floor)

# launchd has a minimal PATH; the wrapper sets CLAUDE_BIN to an absolute path.
CLAUDE_BIN = os.environ.get("CLAUDE_BIN", "claude")

SHADOW_DIR = STAGING_DIR / "shadow"  # scratch history copy used by --shadow (Phase 6 validation)
