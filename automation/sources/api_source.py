"""Fetch the latest Naked Puts and CPS scans from the public API.

Only the *latest* scan is available here; older days come from db_source. A real
User-Agent is required — Cloudflare 403s the default `Python-urllib` UA.
"""
from __future__ import annotations

import json
import socket
import sys
import time
import urllib.error
import urllib.request
from datetime import date, datetime

from .. import config

# 4xx (auth, not-found) won't fix themselves — fail fast. DNS/connection drops and these
# HTTP codes are transient (the wake-race, a flaky tunnel, a restarting backend) — retry.
_RETRYABLE_HTTP = {429, 500, 502, 503, 504}


def _get(path: str) -> dict:
    """GET JSON, retrying transient network failures with exponential backoff.

    The launchd job fires at 09:00 as the Mac wakes — before Wi-Fi/DNS is ready — so the
    first fetch often raises ``socket.gaierror`` / ``URLError``. Without retries that crashed
    the entire run and silently dropped the day (history stuck at 2026-06-23). Retrying lets
    the run wait out the wake-race instead.
    """
    url = config.API_BASE + path
    req = urllib.request.Request(
        url, headers={"User-Agent": config.USER_AGENT, "Accept": "application/json"},
    )
    last_err: Exception | None = None
    for attempt in range(1, config.HTTP_MAX_ATTEMPTS + 1):
        try:
            with urllib.request.urlopen(req, timeout=config.HTTP_TIMEOUT) as resp:
                return json.load(resp)
        except urllib.error.HTTPError as e:
            if e.code not in _RETRYABLE_HTTP:
                raise
            last_err = e
        except (urllib.error.URLError, socket.gaierror, TimeoutError, ConnectionError) as e:
            last_err = e
        if attempt < config.HTTP_MAX_ATTEMPTS:
            delay = min(config.HTTP_RETRY_CAP, config.HTTP_RETRY_BASE * 2 ** (attempt - 1))
            print(f"[api_source] {url} attempt {attempt}/{config.HTTP_MAX_ATTEMPTS} failed "
                  f"({type(last_err).__name__}: {last_err}); retrying in {delay}s", file=sys.stderr)
            time.sleep(delay)
    raise last_err


def fetch_latest_np() -> dict:
    """GET /api/scan/latest -> {scanned_at, regime, tickers:[...], ...}."""
    return _get("/api/scan/latest")


def fetch_latest_cps() -> dict:
    """GET /api/credit-put-spreads/latest -> {scan_date, regime_overlay, candidates, ...}."""
    return _get("/api/credit-put-spreads/latest")


def et_date(scanned_at_utc: str) -> date:
    """Convert a `scan_results.scanned_at` UTC string ('...Z') to its ET calendar date."""
    return datetime.fromisoformat(scanned_at_utc.replace("Z", "+00:00")).astimezone(config.ET).date()
