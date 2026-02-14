"""FMP (Financial Modeling Prep) client for earnings dates."""

import httpx
import logging
from datetime import date
from typing import Optional

from database import get_cached_earnings, store_cached_earnings

logger = logging.getLogger(__name__)
BASE = "https://financialmodelingprep.com"

# Tickers where FMP uses a different symbol than MarketData.app
_FMP_ALIASES = {
    "GOOG": "GOOGL",
}


async def get_next_earnings(ticker: str, api_key: str) -> Optional[str]:
    """
    Fetch next earnings date from FMP with SQLite-backed caching.
    Returns cached date if it's still in the future, otherwise re-fetches.
    """
    # Use cache if we have a future date
    cached = get_cached_earnings(ticker)
    if cached:
        logger.debug(f"{ticker}: Using cached earnings date {cached}")
        return cached

    # Fetch fresh data (try alias if primary ticker fails)
    result = await _fetch_earnings(ticker, api_key)
    if result is None and ticker in _FMP_ALIASES:
        result = await _fetch_earnings(_FMP_ALIASES[ticker], api_key)
    if result:
        store_cached_earnings(ticker, result)
    return result


async def _fetch_earnings(ticker: str, api_key: str) -> Optional[str]:
    """Raw FMP API call. Returns YYYY-MM-DD or None."""
    url = f"{BASE}/stable/earnings"
    params = {"symbol": ticker, "limit": 4, "apikey": api_key}
    try:
        async with httpx.AsyncClient(timeout=10.0) as c:
            resp = await c.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()
        if not data or not isinstance(data, list):
            return None
        today = date.today().isoformat()
        future_dates = [
            entry["date"] for entry in data
            if entry.get("date") and entry["date"] >= today
        ]
        return min(future_dates) if future_dates else None
    except Exception as e:
        logger.warning(f"{ticker}: FMP earnings fetch failed — {e}")
        return None
