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
