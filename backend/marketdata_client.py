"""
MarketData.app API client for options and equity data.

Subscription tiers used by this scanner:
  - Starter ($12/mo): Options chains (IV, Greeks), stock candles, stock quotes

Environment variable: MARKETDATA_TOKEN
"""

import httpx
import asyncio
import logging
import random
from datetime import date, datetime, timedelta
from typing import Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

# ── Rate limiter ────────────────────────────────────────
class RateLimiter:
    """Token-bucket rate limiter for MarketData API calls."""

    def __init__(self, calls_per_minute: int = 50):
        self.calls_per_minute = calls_per_minute
        self.interval = 60.0 / calls_per_minute
        self._last_call = 0.0
        self._lock = asyncio.Lock()

    async def acquire(self):
        async with self._lock:
            now = asyncio.get_running_loop().time()
            elapsed = now - self._last_call
            if elapsed < self.interval:
                await asyncio.sleep(self.interval - elapsed)
            self._last_call = asyncio.get_running_loop().time()


# ── Data classes ────────────────────────────────────────
@dataclass
class OptionContract:
    ticker: str
    strike: float
    expiration: str  # YYYY-MM-DD
    contract_type: str  # call / put
    implied_volatility: Optional[float] = None
    delta: Optional[float] = None
    gamma: Optional[float] = None
    theta: Optional[float] = None
    vega: Optional[float] = None
    open_interest: int = 0
    volume: int = 0
    last_price: Optional[float] = None
    bid: Optional[float] = None
    ask: Optional[float] = None


@dataclass
class DailyBar:
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: int


@dataclass
class StockSnapshot:
    ticker: str
    price: float
    change: float
    change_pct: float
    volume: int
    prev_close: float


# ── Client ──────────────────────────────────────────────
class MarketDataClient:
    """
    Async HTTP client for the MarketData.app REST API.

    Columnar response format: all fields are parallel arrays.
    Status field: "s" = "ok" | "no_data" | "error".
    """
    BASE = "https://api.marketdata.app"

    def __init__(self, api_key: str, rate_limit: int = 50):
        self.api_key = api_key
        self.limiter = RateLimiter(rate_limit)
        self.client = httpx.AsyncClient(
            timeout=30.0,
            headers={"Authorization": f"Bearer {api_key}"},
        )

    async def close(self):
        await self.client.aclose()

    async def _get(self, url: str, params: dict = None) -> dict:
        """Make a rate-limited GET request with retry logic."""
        params = params or {}
        max_retries = 5

        for attempt in range(max_retries):
            await self.limiter.acquire()
            try:
                resp = await self.client.get(url, params=params)
                if resp.status_code == 429:
                    wait = 2 ** (attempt + 1) + random.uniform(0, 2)
                    logger.warning(f"Rate limited (attempt {attempt + 1}), waiting {wait:.1f}s")
                    await asyncio.sleep(wait)
                    continue
                resp.raise_for_status()
                data = resp.json()

                # Check MarketData status field
                status = data.get("s")
                if status == "error":
                    msg = data.get("errmsg", "Unknown error")
                    logger.error(f"MarketData API error: {msg}")
                    return {}
                if status == "no_data":
                    logger.warning(f"MarketData returned no_data for {url}")
                    return {}

                return data
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 403:
                    raise PermissionError(
                        "MarketData API returned 403. Check your API token and "
                        "subscription tier — options chains require the Starter plan ($12/mo)."
                    )
                if e.response.status_code == 402:
                    raise PermissionError(
                        f"MarketData API returned 402 for {url}. "
                        "This endpoint requires a premium subscription."
                    )
                if attempt == max_retries - 1:
                    raise
                await asyncio.sleep(1)
            except httpx.RequestError as e:
                if attempt == max_retries - 1:
                    raise
                logger.warning(f"Request error (attempt {attempt + 1}): {e}")
                await asyncio.sleep(1)

        return {}

    # ── Stock endpoints ─────────────────────────────────

    async def get_stock_snapshot(self, ticker: str) -> Optional[StockSnapshot]:
        """
        Get current price quote for a stock/ETF.
        """
        url = f"{self.BASE}/v1/stocks/quotes/{ticker}/"
        data = await self._get(url)

        if not data or data.get("s") != "ok":
            return None

        price = data["last"][0]
        change = data["change"][0] if data.get("change") else 0
        change_pct = (data["changepct"][0] * 100) if data.get("changepct") else 0
        volume = data["volume"][0] if data.get("volume") else 0
        prev_close = price - change

        return StockSnapshot(
            ticker=ticker,
            price=price,
            change=round(change, 2),
            change_pct=round(change_pct, 2),
            volume=volume,
            prev_close=round(prev_close, 2),
        )

    async def get_daily_bars(
        self,
        ticker: str,
        from_date: date,
        to_date: date,
    ) -> list[DailyBar]:
        """
        Get daily OHLCV bars for RV computation.
        """
        url = f"{self.BASE}/v1/stocks/candles/D/{ticker}/"
        data = await self._get(url, {
            "from": from_date.isoformat(),
            "to": to_date.isoformat(),
            "adjusted": "true",
        })

        if not data or data.get("s") != "ok":
            return []

        bars = []
        n = len(data.get("c", []))
        for i in range(n):
            # MarketData timestamps are in seconds (not milliseconds)
            dt = datetime.fromtimestamp(data["t"][i]).strftime("%Y-%m-%d")
            bars.append(DailyBar(
                date=dt,
                open=data["o"][i],
                high=data["h"][i],
                low=data["l"][i],
                close=data["c"][i],
                volume=data["v"][i] if data.get("v") and i < len(data["v"]) else 0,
            ))
        return bars

    # ── Options endpoint ────────────────────────────────

    async def get_options_chain(
        self,
        underlying: str,
    ) -> list[OptionContract]:
        """
        Get options chain via two optimized calls:
          1. Narrow (strikeLimit=12, all expiries) → ATM IV + term structure
          2. Wide (strikeLimit=30, 20-40 DTE) → skew computation

        Requires: Starter subscription ($12/mo) or above.
        """
        url = f"{self.BASE}/v1/options/chain/{underlying}/"

        # Call 1: Narrow chain — all expirations, tight strikes for ATM IV + term structure
        narrow_data = await self._get(url, {
            "expiration": "all",
            "strikeLimit": 12,
        })

        # Call 2: Wide chain — nearest-to-30-DTE expiry, wide strikes for skew
        wide_data = await self._get(url, {
            "strikeLimit": 60,
            "dte": 30,
        })

        # Parse and merge both responses, deduplicating by (strike, expiration, side)
        seen = set()
        contracts = []

        for data in [narrow_data, wide_data]:
            if not data or data.get("s") != "ok":
                continue
            n = len(data.get("strike", []))
            for i in range(n):
                iv = data["iv"][i] if data.get("iv") and i < len(data["iv"]) and data["iv"][i] is not None else None
                if iv is None or iv <= 0:
                    continue

                exp_ts = data["expiration"][i]
                exp_str = datetime.fromtimestamp(exp_ts).strftime("%Y-%m-%d")
                strike = data["strike"][i]
                side = data["side"][i]

                key = (strike, exp_str, side)
                if key in seen:
                    continue
                seen.add(key)

                contracts.append(OptionContract(
                    ticker=underlying,
                    strike=strike,
                    expiration=exp_str,
                    contract_type=side,
                    implied_volatility=iv,
                    delta=data["delta"][i] if data.get("delta") and i < len(data["delta"]) and data["delta"][i] is not None else None,
                    gamma=data["gamma"][i] if data.get("gamma") and i < len(data["gamma"]) and data["gamma"][i] is not None else None,
                    theta=data["theta"][i] if data.get("theta") and i < len(data["theta"]) and data["theta"][i] is not None else None,
                    vega=data["vega"][i] if data.get("vega") and i < len(data["vega"]) and data["vega"][i] is not None else None,
                    open_interest=data["openInterest"][i] if data.get("openInterest") and i < len(data["openInterest"]) else 0,
                    volume=data["volume"][i] if data.get("volume") and i < len(data["volume"]) else 0,
                    last_price=data["last"][i] if data.get("last") and i < len(data["last"]) else None,
                    bid=data["bid"][i] if data.get("bid") and i < len(data["bid"]) else None,
                    ask=data["ask"][i] if data.get("ask") and i < len(data["ask"]) else None,
                ))

        logger.info(f"Fetched {len(contracts)} options contracts for {underlying}")
        return contracts

    # ── Earnings endpoint ────────────────────────────────

    async def get_earnings(self, ticker: str) -> Optional[str]:
        """Get next earnings date for a ticker. Returns YYYY-MM-DD or None."""
        url = f"{self.BASE}/v1/stocks/earnings/{ticker}/"
        try:
            data = await self._get(url, {"from": date.today().isoformat()})
            if not data or data.get("s") != "ok":
                return None
            report_dates = data.get("reportDate", [])
            today = date.today()
            for ts in report_dates:
                if ts is None:
                    continue
                d = datetime.fromtimestamp(ts).date()
                if d >= today:
                    return d.isoformat()
            return None
        except Exception as e:
            logger.warning(f"{ticker}: Earnings fetch failed — {e}")
            return None
