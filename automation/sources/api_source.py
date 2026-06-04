"""Fetch the latest Naked Puts and CPS scans from the public API.

Only the *latest* scan is available here; older days come from db_source. A real
User-Agent is required — Cloudflare 403s the default `Python-urllib` UA.
"""
from __future__ import annotations

import json
import urllib.request
from datetime import date, datetime

from .. import config


def _get(path: str) -> dict:
    req = urllib.request.Request(
        config.API_BASE + path,
        headers={"User-Agent": config.USER_AGENT, "Accept": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=config.HTTP_TIMEOUT) as resp:
        return json.load(resp)


def fetch_latest_np() -> dict:
    """GET /api/scan/latest -> {scanned_at, regime, tickers:[...], ...}."""
    return _get("/api/scan/latest")


def fetch_latest_cps() -> dict:
    """GET /api/credit-put-spreads/latest -> {scan_date, regime_overlay, candidates, ...}."""
    return _get("/api/credit-put-spreads/latest")


def et_date(scanned_at_utc: str) -> date:
    """Convert a `scan_results.scanned_at` UTC string ('...Z') to its ET calendar date."""
    return datetime.fromisoformat(scanned_at_utc.replace("Z", "+00:00")).astimezone(config.ET).date()
