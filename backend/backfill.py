"""
Historical IV backfill script for Theta Harvest.

Fetches historical options data from MarketData.app and populates
the SQLite database with daily ATM IV, RV30, VRP, and term slope.
This gives the scanner enough history (252 trading days) for accurate
IV Rank and IV Percentile calculations.

Two-step approach for historical IV:
  1. Chain endpoint → contract symbols + metadata (IV is null for historical)
  2. Quotes endpoint → bid/ask/mid prices for nearest-ATM contracts (~6 calls)
  3. Black-Scholes solver → compute IV from option mid price

Usage:
    export MARKETDATA_TOKEN=your_token_here
    python backfill.py --days 252 --verbose
    python backfill.py --days 5 --tickers SPY --dry-run
    python backfill.py --resume --verbose
"""

import os
import sys
import csv
import math
import argparse
import asyncio
import logging
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Optional

import httpx
import numpy as np
from tqdm import tqdm

from marketdata_client import (
    RateLimiter, OptionContract, DailyBar, MarketDataClient,
)
from database import store_daily_iv, get_connection, init_db
from main import UNIVERSE

logger = logging.getLogger("backfill")

RISK_FREE_RATE = float(os.environ.get("RISK_FREE_RATE", "0.043"))


# ── Black-Scholes IV solver ───────────────────────────────

def _norm_cdf(x: float) -> float:
    """Standard normal CDF using math.erf (no scipy needed)."""
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def _bs_price(
    spot: float, strike: float, T: float, r: float, sigma: float, is_call: bool,
) -> float:
    """Black-Scholes European option price."""
    if T <= 0 or sigma <= 0:
        return 0.0
    sqrt_T = math.sqrt(T)
    d1 = (math.log(spot / strike) + (r + 0.5 * sigma ** 2) * T) / (sigma * sqrt_T)
    d2 = d1 - sigma * sqrt_T
    if is_call:
        return spot * _norm_cdf(d1) - strike * math.exp(-r * T) * _norm_cdf(d2)
    else:
        return strike * math.exp(-r * T) * _norm_cdf(-d2) - spot * _norm_cdf(-d1)


def compute_iv_from_price(
    option_price: float,
    spot: float,
    strike: float,
    dte_days: int,
    is_call: bool,
    r: float = RISK_FREE_RATE,
) -> Optional[float]:
    """
    Compute implied volatility from an option's market price using bisection.
    Returns IV as a decimal (e.g. 0.15 for 15% annualized vol).
    """
    if option_price <= 0 or spot <= 0 or strike <= 0 or dte_days <= 0:
        return None

    T = dte_days / 365.0

    # Intrinsic value check
    if is_call:
        intrinsic = max(0.0, spot - strike * math.exp(-r * T))
    else:
        intrinsic = max(0.0, strike * math.exp(-r * T) - spot)

    if option_price < intrinsic * 0.95:
        return None  # Below intrinsic — no valid IV

    # Bisection: search IV between 1% and 500%
    lo, hi = 0.01, 5.0
    for _ in range(100):
        mid = (lo + hi) / 2.0
        price = _bs_price(spot, strike, T, r, mid, is_call)
        if abs(price - option_price) < 0.001:
            return mid
        if price > option_price:
            hi = mid
        else:
            lo = mid

    # Return best estimate if converged close enough
    result = (lo + hi) / 2.0
    final_price = _bs_price(spot, strike, T, r, result, is_call)
    if abs(final_price - option_price) / option_price < 0.05:
        return result
    return None


# ── Historical ATM IV computation ──────────────────────────
# calculator.compute_atm_iv uses date.today() internally for DTE,
# which doesn't work for historical dates. This version accepts a
# reference date parameter.

def compute_atm_iv_historical(
    contracts: list[OptionContract],
    spot_price: float,
    as_of: date,
    target_dte: int = 30,
) -> Optional[float]:
    """
    Compute ATM implied volatility using strike-bracketing interpolation.

    For each expiry:
      1. Average call+put IV at each strike
      2. Find the two strikes that bracket spot, interpolate by distance
    Then interpolate between expiries to the target DTE.
    """
    by_expiry: dict[str, list[OptionContract]] = {}
    for c in contracts:
        by_expiry.setdefault(c.expiration, []).append(c)

    expiry_dte: dict[str, int] = {}
    for exp_str in by_expiry:
        try:
            exp_date = datetime.strptime(exp_str, "%Y-%m-%d").date()
            dte = (exp_date - as_of).days
            if dte > 0:
                expiry_dte[exp_str] = dte
        except ValueError:
            continue

    if not expiry_dte:
        return None

    def _interpolated_atm_iv(exp: str) -> Optional[float]:
        """ATM IV at one expiry via strike-bracket interpolation."""
        chain = by_expiry[exp]

        # Average call+put IV at each strike
        strike_ivs: dict[float, list[float]] = {}
        for c in chain:
            if c.implied_volatility and c.implied_volatility > 0:
                strike_ivs.setdefault(c.strike, []).append(c.implied_volatility)

        if not strike_ivs:
            return None

        strike_avg = {k: float(np.mean(v)) for k, v in strike_ivs.items()}
        sorted_strikes = sorted(strike_avg.keys())

        # Find strikes that bracket spot
        below = [s for s in sorted_strikes if s <= spot_price]
        above = [s for s in sorted_strikes if s > spot_price]

        if below and above:
            s_lo, s_hi = below[-1], above[0]
            iv_lo, iv_hi = strike_avg[s_lo], strike_avg[s_hi]
            w = (spot_price - s_lo) / (s_hi - s_lo) if s_hi != s_lo else 0.5
            return iv_lo * (1 - w) + iv_hi * w

        # Only one side — use nearest strike
        nearest = min(sorted_strikes, key=lambda s: abs(s - spot_price))
        return strike_avg[nearest]

    # Collect ATM IV per expiry (decimal → percentage)
    expiry_ivs: list[tuple[int, float]] = []
    for exp, dte in expiry_dte.items():
        iv = _interpolated_atm_iv(exp)
        if iv is not None:
            expiry_ivs.append((dte, iv * 100))

    if not expiry_ivs:
        return None

    expiry_ivs.sort(key=lambda x: x[0])

    if len(expiry_ivs) == 1:
        return round(expiry_ivs[0][1], 2)

    # Pick the two expiries closest to target DTE and interpolate
    by_target = sorted(expiry_ivs, key=lambda x: abs(x[0] - target_dte))
    dte1, iv1 = by_target[0]
    dte2, iv2 = by_target[1]

    if dte1 == dte2:
        return round((iv1 + iv2) / 2, 2)

    w = (target_dte - dte1) / (dte2 - dte1)
    w = max(0.0, min(1.0, w))
    return round(iv1 * (1 - w) + iv2 * w, 2)


def compute_term_slope_historical(
    contracts: list[OptionContract],
    spot_price: float,
    as_of: date,
) -> Optional[float]:
    """
    Compute term structure slope (front/back IV ratio) for a historical date.
    Uses strike-bracket interpolation per expiry for consistency.
    Returns front_iv / back_iv ratio.
    """
    by_expiry: dict[str, list[OptionContract]] = {}
    for c in contracts:
        by_expiry.setdefault(c.expiration, []).append(c)

    expiry_ivs: list[tuple[int, float]] = []

    for exp_str, chain in by_expiry.items():
        try:
            exp_date = datetime.strptime(exp_str, "%Y-%m-%d").date()
            dte = (exp_date - as_of).days
            if dte <= 0:
                continue
        except ValueError:
            continue

        # Average call+put IV at each strike
        strike_ivs: dict[float, list[float]] = {}
        for c in chain:
            if c.implied_volatility and c.implied_volatility > 0:
                strike_ivs.setdefault(c.strike, []).append(c.implied_volatility)
        if not strike_ivs:
            continue

        strike_avg = {k: float(np.mean(v)) for k, v in strike_ivs.items()}
        sorted_strikes = sorted(strike_avg.keys())

        below = [s for s in sorted_strikes if s <= spot_price]
        above = [s for s in sorted_strikes if s > spot_price]

        if below and above:
            s_lo, s_hi = below[-1], above[0]
            w = (spot_price - s_lo) / (s_hi - s_lo) if s_hi != s_lo else 0.5
            atm_iv = strike_avg[s_lo] * (1 - w) + strike_avg[s_hi] * w
        else:
            nearest = min(sorted_strikes, key=lambda s: abs(s - spot_price))
            atm_iv = strike_avg[nearest]

        expiry_ivs.append((dte, atm_iv * 100))

    expiry_ivs.sort(key=lambda x: x[0])

    if len(expiry_ivs) < 2:
        return None

    front_iv = expiry_ivs[0][1]
    back_iv = expiry_ivs[-1][1]
    slope = front_iv / back_iv if back_iv > 0 else 1.0
    return round(slope, 3)


def compute_rv30_from_bars(bars: list[DailyBar]) -> Optional[float]:
    """
    Compute 30-day annualized realized volatility from daily bars.
    Returns percentage (e.g. 15.2), or None if insufficient bars.
    Needs 31 bars (30 returns).
    """
    if len(bars) < 31:
        return None
    closes = np.array([b.close for b in bars[-31:]])
    log_returns = np.diff(np.log(closes))
    rv = float(np.std(log_returns, ddof=1) * math.sqrt(252) * 100)
    return round(rv, 2)


# ── ATM symbol selection ──────────────────────────────────

def pick_atm_symbols(
    chain_data: dict, spot_price: float, as_of: date, max_expiries: int = 3,
) -> list[dict]:
    """
    From a chain response, select contracts for ATM IV computation.

    For each of the 3 closest-to-30-DTE expirations:
      - Find the 2 strikes that bracket spot (just below + just above)
      - Include both call and put at each strike
      → up to 4 contracts per expiry, ~8-12 total

    Each dict: {"symbol": str, "strike": float, "side": str, "exp_ts": int}
    """
    n = len(chain_data.get("optionSymbol", []))
    if n == 0:
        return []

    # Use chain's underlyingPrice or provided spot
    up = chain_data.get("underlyingPrice", [])
    chain_spot = next((p for p in up if p is not None and p > 0), None) if up else None
    spot = chain_spot or spot_price
    if not spot or spot <= 0:
        return []

    atm_range = spot * 0.02  # 2% of spot

    # Group near-ATM contracts by expiry
    by_expiry: dict[int, list[dict]] = {}
    for i in range(n):
        strike = chain_data["strike"][i]
        if abs(strike - spot) > atm_range:
            continue
        exp_ts = chain_data["expiration"][i]
        by_expiry.setdefault(exp_ts, []).append({
            "symbol": chain_data["optionSymbol"][i],
            "strike": strike,
            "side": chain_data["side"][i],
            "exp_ts": exp_ts,
        })

    # Fallback: widen to 5% if nothing within 2%
    if not by_expiry:
        atm_range = spot * 0.05
        for i in range(n):
            strike = chain_data["strike"][i]
            if abs(strike - spot) > atm_range:
                continue
            exp_ts = chain_data["expiration"][i]
            by_expiry.setdefault(exp_ts, []).append({
                "symbol": chain_data["optionSymbol"][i],
                "strike": strike,
                "side": chain_data["side"][i],
                "exp_ts": exp_ts,
            })

    if not by_expiry:
        return []

    # Sort expiries by DTE proximity to 30 days
    as_of_ts = datetime.combine(as_of, datetime.min.time()).timestamp()
    sorted_expiries = sorted(
        by_expiry.keys(),
        key=lambda ts: abs((ts - as_of_ts) / 86400 - 30),
    )

    # For each expiry: find 2 bracketing strikes, include call+put at each
    selected = []
    for exp_ts in sorted_expiries[:max_expiries]:
        contracts = by_expiry[exp_ts]
        strikes = sorted(set(c["strike"] for c in contracts))

        # Strikes just below and just above spot
        below = [s for s in strikes if s <= spot]
        above = [s for s in strikes if s > spot]

        bracket = set()
        if below:
            bracket.add(below[-1])
        if above:
            bracket.add(above[0])

        # If only one side, add next nearest as fallback
        if len(bracket) < 2:
            remaining = [s for s in strikes if s not in bracket]
            if remaining:
                bracket.add(min(remaining, key=lambda s: abs(s - spot)))

        # Include both call and put at each bracketing strike
        for c in contracts:
            if c["strike"] in bracket:
                selected.append(c)

    return selected


# ── Helpers ──────────────────────────────────────────────

def _safe_get(data: dict, key: str, idx: int):
    """Safely get a value from a columnar API response."""
    arr = data.get(key)
    if arr and idx < len(arr):
        return arr[idx]
    return None


# ── API helpers ────────────────────────────────────────────

class BackfillClient:
    """
    Thin async HTTP client for backfill operations.
    Uses two-step approach: chain (for symbols) → quotes (for IV).
    """
    BASE = "https://api.marketdata.app"

    def __init__(self, api_key: str, rate_limit: int = 15):
        self.api_key = api_key
        self.limiter = RateLimiter(rate_limit)
        self.client = httpx.AsyncClient(
            timeout=30.0,
            headers={"Authorization": f"Bearer {api_key}"},
        )
        self.remaining_credits: Optional[int] = None

    async def close(self):
        await self.client.aclose()

    async def _get(self, url: str, params: dict = None) -> dict:
        """Rate-limited GET with retry and credit tracking."""
        params = params or {}
        max_retries = 5

        for attempt in range(max_retries):
            await self.limiter.acquire()
            try:
                resp = await self.client.get(url, params=params)

                # Track remaining API credits from response header
                credit_header = resp.headers.get("x-api-ratelimit-remaining")
                if credit_header is not None:
                    try:
                        self.remaining_credits = int(credit_header)
                    except ValueError:
                        pass

                if resp.status_code == 429:
                    wait = 2 ** (attempt + 1) + 1
                    logger.warning(f"Rate limited (attempt {attempt + 1}), waiting {wait:.0f}s")
                    await asyncio.sleep(wait)
                    continue

                resp.raise_for_status()
                data = resp.json()

                status = data.get("s")
                if status == "error":
                    msg = data.get("errmsg", "Unknown error")
                    logger.warning(f"API error: {msg}")
                    return {}
                if status == "no_data":
                    logger.debug(f"  API returned no_data for {url}")
                    return {}

                return data

            except httpx.HTTPStatusError as e:
                if e.response.status_code == 403:
                    raise PermissionError(
                        "MarketData API returned 403. Check your API token and subscription."
                    )
                if e.response.status_code in (400, 402):
                    raise  # Client error / payment required, retrying won't help
                if attempt == max_retries - 1:
                    raise
                await asyncio.sleep(1)
            except httpx.RequestError as e:
                if attempt == max_retries - 1:
                    raise
                logger.warning(f"Request error (attempt {attempt + 1}): {e}")
                await asyncio.sleep(1)

        return {}

    async def fetch_daily_bars(
        self, ticker: str, from_date: date, to_date: date,
    ) -> list[DailyBar]:
        """Fetch daily OHLCV bars for a ticker. Paginates in ~300-day chunks
        to work around API limits on bars per request."""
        url = f"{self.BASE}/v1/stocks/candles/D/{ticker}/"
        all_bars: list[DailyBar] = []
        seen_dates: set[str] = set()

        chunk_start = from_date
        while chunk_start < to_date:
            chunk_end = min(chunk_start + timedelta(days=350), to_date)
            try:
                data = await self._get(url, {
                    "from": chunk_start.isoformat(),
                    "to": chunk_end.isoformat(),
                    "adjusted": "true",
                })
            except httpx.HTTPStatusError as e:
                if e.response.status_code in (400, 402):
                    # Older data not available on this plan — skip chunk
                    chunk_start = chunk_end + timedelta(days=1)
                    continue
                raise

            if data and data.get("s") == "ok":
                n = len(data.get("c", []))
                for i in range(n):
                    dt = datetime.fromtimestamp(data["t"][i]).strftime("%Y-%m-%d")
                    if dt not in seen_dates:
                        seen_dates.add(dt)
                        all_bars.append(DailyBar(
                            date=dt,
                            open=data["o"][i],
                            high=data["h"][i],
                            low=data["l"][i],
                            close=data["c"][i],
                            volume=data["v"][i] if data.get("v") and i < len(data["v"]) else 0,
                        ))

            chunk_start = chunk_end + timedelta(days=1)

        all_bars.sort(key=lambda b: b.date)
        return all_bars

    async def fetch_option_quote(
        self, symbol: str, as_of: date, underlying: str,
    ) -> Optional[OptionContract]:
        """
        Fetch a single historical option quote.
        Priority: API-provided IV → Black-Scholes fallback from mid price.
        """
        url = f"{self.BASE}/v1/options/quotes/{symbol}/"
        data = await self._get(url, {"date": as_of.isoformat()})

        if not data or data.get("s") != "ok":
            return None

        exp_ts = _safe_get(data, "expiration", 0)
        if exp_ts is None:
            return None
        exp_str = datetime.fromtimestamp(exp_ts).strftime("%Y-%m-%d")

        strike = _safe_get(data, "strike", 0)
        side = _safe_get(data, "side", 0) or "call"
        spot = _safe_get(data, "underlyingPrice", 0)
        mid = _safe_get(data, "mid", 0)
        bid = _safe_get(data, "bid", 0)
        ask = _safe_get(data, "ask", 0)

        # Priority 1: API-provided IV (exchange-quality, accounts for
        # American exercise, dividends, and proper rate curves)
        iv = _safe_get(data, "iv", 0)
        iv_source = "api"

        # Priority 2: Black-Scholes fallback from mid price
        if iv is None or iv <= 0:
            iv_source = "bs"
            price = mid
            if (price is None or price <= 0) and bid and ask and bid > 0 and ask > 0:
                price = (bid + ask) / 2.0

            if price and price > 0 and spot and strike:
                exp_date = datetime.fromtimestamp(exp_ts).date()
                dte = (exp_date - as_of).days
                iv = compute_iv_from_price(price, spot, strike, dte, side == "call")

            if iv is None or iv <= 0:
                logger.debug(f"    Quote {symbol}: no IV (mid={mid}, bid={bid}, ask={ask})")
                return None

        logger.debug(
            f"    Quote {symbol}: IV={iv:.4f} ({iv*100:.1f}%) [{iv_source}]"
        )

        return OptionContract(
            ticker=underlying,
            strike=strike or 0,
            expiration=exp_str,
            contract_type=side,
            implied_volatility=iv,
            delta=_safe_get(data, "delta", 0),
            gamma=_safe_get(data, "gamma", 0),
            theta=_safe_get(data, "theta", 0),
            vega=_safe_get(data, "vega", 0),
            open_interest=_safe_get(data, "openInterest", 0) or 0,
            volume=_safe_get(data, "volume", 0) or 0,
            last_price=_safe_get(data, "last", 0),
            bid=_safe_get(data, "bid", 0),
            ask=_safe_get(data, "ask", 0),
        )

    async def fetch_historical_chain(
        self, underlying: str, as_of: date, spot_price: float,
    ) -> list[OptionContract]:
        """
        Two-step historical chain fetch:
        1. Chain endpoint → contract symbols + metadata (IV is null for historical)
        2. Quotes endpoint → IV + Greeks for nearest-ATM contracts (~4-6 calls)
        """
        # Step 1: Chain for contract metadata
        url = f"{self.BASE}/v1/options/chain/{underlying}/"
        chain_data = await self._get(url, {
            "date": as_of.isoformat(),
            "strikeLimit": 6,
            "expiration": "all",
        })

        if not chain_data or chain_data.get("s") != "ok":
            return []

        # Step 2: Filter to nearest-ATM symbols
        atm_symbols = pick_atm_symbols(chain_data, spot_price, as_of)
        if not atm_symbols:
            logger.debug(f"  {underlying} {as_of}: No ATM symbols found in chain")
            return []

        logger.debug(
            f"  {underlying} {as_of}: Fetching quotes for {len(atm_symbols)} ATM contracts"
        )

        # Step 3: Fetch quotes for each ATM symbol
        contracts = []
        for sym in atm_symbols:
            contract = await self.fetch_option_quote(sym["symbol"], as_of, underlying)
            if contract:
                contracts.append(contract)

        logger.debug(
            f"  {underlying} {as_of}: Got IV for {len(contracts)}/{len(atm_symbols)} contracts"
        )
        return contracts


# ── DB helpers ─────────────────────────────────────────────

def get_existing_dates(ticker: str) -> set[str]:
    """Return set of date strings already in DB for this ticker."""
    conn = get_connection()
    cursor = conn.execute(
        "SELECT date FROM daily_iv WHERE ticker = ?", (ticker,)
    )
    dates = {row[0] for row in cursor.fetchall()}
    conn.close()
    return dates


# ── CSV helpers (shared module) ────────────────────────────
from csv_store import DATA_DIR, append_quotes_csv, append_daily_csv


# ── Main orchestration ─────────────────────────────────────

async def run_backfill(args: argparse.Namespace):
    api_key = os.environ.get("MARKETDATA_TOKEN")
    if not api_key:
        logger.error("MARKETDATA_TOKEN environment variable not set.")
        sys.exit(1)

    # Resolve tickers
    if args.tickers:
        tickers = [t.strip().upper() for t in args.tickers.split(",")]
        invalid = [t for t in tickers if t not in UNIVERSE]
        if invalid:
            logger.error(f"Unknown tickers: {', '.join(invalid)}. Available: {', '.join(UNIVERSE.keys())}")
            sys.exit(1)
    else:
        tickers = list(UNIVERSE.keys())

    init_db()

    client = BackfillClient(api_key=api_key, rate_limit=1000)

    try:
        # ── Phase 1: Fetch daily bars ──────────────────────
        # Need extra bars beyond --days for RV30 computation (30 prior bars)
        lookback_calendar = int(args.days * 1.6) + 60
        from_date = date.today() - timedelta(days=lookback_calendar)
        to_date = date.today()

        bars_by_ticker: dict[str, dict[str, DailyBar]] = {}
        all_bars_list: dict[str, list[DailyBar]] = {}

        for ticker in tqdm(tickers, desc="Bars", unit="tk", ncols=80, leave=False):
            bars = await client.fetch_daily_bars(ticker, from_date, to_date)
            if not bars:
                logger.warning(f"  {ticker}: No bars returned, skipping")
                continue
            bars_by_ticker[ticker] = {b.date: b for b in bars}
            all_bars_list[ticker] = bars

        if not bars_by_ticker:
            print("  Error: No bar data fetched. Exiting.")
            return

        # Build trading day calendar from the first ticker's bars
        reference_ticker = "SPY" if "SPY" in bars_by_ticker else list(bars_by_ticker.keys())[0]
        reference_bars = all_bars_list[reference_ticker]
        # Trading days sorted newest first (for --batch-size to get most recent first)
        all_trading_days = sorted(
            [b.date for b in reference_bars],
            reverse=True,
        )

        # Skip today — historical options data isn't available same-day.
        # Yesterday may 400 early morning but works by afternoon.
        today = date.today().isoformat()
        all_trading_days = [d for d in all_trading_days if d < today]

        # Limit to requested number of days
        trading_days = all_trading_days[:args.days]

        print(
            f"  {len(bars_by_ticker)} tickers | "
            f"{len(trading_days)} trading days "
            f"({trading_days[-1]} → {trading_days[0]})"
        )

        # ── Phase 2: Backfill daily metrics ────────────────
        # Pre-load existing dates if resuming
        existing_dates: dict[str, set[str]] = {}
        if args.resume:
            for ticker in tickers:
                if ticker in bars_by_ticker:
                    existing_dates[ticker] = get_existing_dates(ticker)
            total_existing = sum(len(v) for v in existing_dates.values())
            print(f"  Resume: {total_existing} existing entries, skipping")

        # Apply batch size
        if args.batch_size:
            trading_days = trading_days[:args.batch_size]

        # Count total work
        total_work = 0
        skipped = 0
        for day_str in trading_days:
            for ticker in tickers:
                if ticker not in bars_by_ticker:
                    continue
                if args.resume and day_str in existing_dates.get(ticker, set()):
                    skipped += 1
                    continue
                total_work += 1

        if args.dry_run:
            print(f"\n{'='*50}")
            print("DRY RUN — no API calls will be made")
            print(f"{'='*50}")
            print(f"  Tickers:         {', '.join(t for t in tickers if t in bars_by_ticker)}")
            print(f"  Trading days:    {len(trading_days)}")
            print(f"  Data points:     {total_work}")
            print(f"  Chain calls:     {total_work}")
            print(f"  Quote calls:     ~{total_work * 10}")
            print(f"  Total API calls: ~{total_work * 11}")
            if skipped:
                print(f"  Skipped (resume): {skipped}")
            return

        # ── Phase 2: Backfill with progress bar ────────────
        # Build flat work list: [(day_str, ticker), ...]
        work_items: list[tuple[str, str]] = []
        for day_str in trading_days:
            for ticker in tickers:
                if ticker not in bars_by_ticker:
                    continue
                if args.resume and day_str in existing_dates.get(ticker, set()):
                    continue
                work_items.append((day_str, ticker))

        completed = 0
        errors = 0
        no_data = 0

        bar_fmt = (
            "{l_bar}{bar}| {n_fmt}/{total_fmt} "
            "[{elapsed}<{remaining}, {rate_fmt}] {postfix}"
        )
        pbar = tqdm(
            work_items,
            desc="Backfill",
            bar_format=bar_fmt,
            unit="pt",
            ncols=110,
            disable=False,
        )

        for day_str, ticker in pbar:
            day_date = datetime.strptime(day_str, "%Y-%m-%d").date()

            # Check credit limit
            if client.remaining_credits is not None and client.remaining_credits < args.credit_limit:
                pbar.close()
                logger.warning(
                    f"Stopping: credits ({client.remaining_credits:,}) "
                    f"below limit ({args.credit_limit:,}). "
                    f"{completed}/{len(work_items)} done."
                )
                return

            # Get spot price from bars
            bar = bars_by_ticker[ticker].get(day_str)
            if bar is None:
                continue
            spot_price = bar.close

            # Update progress bar description
            pbar.set_postfix_str(
                f"{ticker} {day_str}", refresh=False
            )

            # Fetch historical option chain (two-step: chain → quotes)
            try:
                contracts = await client.fetch_historical_chain(
                    ticker, day_date, spot_price,
                )
            except Exception as e:
                errors += 1
                pbar.set_postfix_str(f"{ticker} {day_str} ERR", refresh=False)
                logger.debug(f"{ticker} {day_str}: {e}")
                continue

            if not contracts:
                no_data += 1
                continue

            # Compute ATM IV
            atm_iv = compute_atm_iv_historical(contracts, spot_price, day_date)
            if atm_iv is None:
                no_data += 1
                continue

            # Compute RV30 from bars up to this date
            ticker_bars = all_bars_list[ticker]
            bars_up_to_date = [b for b in ticker_bars if b.date <= day_str]
            rv30 = compute_rv30_from_bars(bars_up_to_date)

            # Compute VRP
            vrp = round(atm_iv - rv30, 2) if rv30 is not None else None

            # Compute term structure slope
            term_slope = compute_term_slope_historical(contracts, spot_price, day_date)

            # Store in database + CSV
            store_daily_iv(
                ticker=ticker, atm_iv=atm_iv, rv30=rv30,
                vrp=vrp, term_slope=term_slope, as_of=day_date,
            )
            append_quotes_csv(ticker, day_str, contracts, spot_price)
            append_daily_csv(
                ticker, day_str, spot_price,
                atm_iv, rv30, vrp, term_slope,
            )

            completed += 1
            credits = client.remaining_credits
            credits_str = f"{credits:,}" if credits is not None else "?"
            vrp_str = f"{vrp:+.1f}" if vrp is not None else "?"

            pbar.set_postfix_str(
                f"{ticker} {day_str} IV={atm_iv:.1f} VRP={vrp_str} | cr:{credits_str}",
                refresh=True,
            )

        pbar.close()

        # ── Summary ──────────────────────────────────────────
        print(f"\n  Done: {completed} stored, {errors} errors, {no_data} no-data skips")

        conn = get_connection()
        for ticker in tickers:
            if ticker not in bars_by_ticker:
                continue
            count = conn.execute(
                "SELECT COUNT(*) FROM daily_iv WHERE ticker = ?", (ticker,)
            ).fetchone()[0]
            latest = conn.execute(
                "SELECT date, atm_iv FROM daily_iv WHERE ticker = ? ORDER BY date DESC LIMIT 1",
                (ticker,),
            ).fetchone()
            oldest = conn.execute(
                "SELECT date FROM daily_iv WHERE ticker = ? ORDER BY date ASC LIMIT 1",
                (ticker,),
            ).fetchone()
            quotes_path = DATA_DIR / "quotes" / f"{ticker}.csv"
            q_rows = sum(1 for _ in open(quotes_path)) - 1 if quotes_path.exists() else 0
            if latest and oldest:
                print(
                    f"  {ticker}: {count} days ({oldest[0]} → {latest[0]}) "
                    f"latest IV={latest[1]:.1f} | {q_rows} quotes"
                )
            else:
                print(f"  {ticker}: {count} days")
        conn.close()

    finally:
        await client.close()


def main():
    parser = argparse.ArgumentParser(
        description="Backfill historical IV data for Theta Harvest scanner.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python backfill.py --days 5 --tickers SPY --dry-run   # Preview without API calls
  python backfill.py --days 5 --tickers SPY --verbose    # Small test run
  python backfill.py --days 252 --verbose                # Full year backfill
  python backfill.py --resume --verbose                  # Continue interrupted run
        """,
    )
    parser.add_argument(
        "--days", type=int, default=252,
        help="Trading days to backfill (default: 252, ~1 year)",
    )
    parser.add_argument(
        "--tickers", type=str, default=None,
        help="Comma-separated tickers (default: all in UNIVERSE)",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Show plan without making API calls",
    )
    parser.add_argument(
        "--resume", action="store_true",
        help="Skip dates already in the database",
    )
    parser.add_argument(
        "--batch-size", type=int, default=None,
        help="Max trading days per run (default: unlimited)",
    )
    parser.add_argument(
        "--verbose", action="store_true",
        help="Log per-ticker detail for each date",
    )
    parser.add_argument(
        "--credit-limit", type=int, default=1000,
        help="Stop when API credits drop below this (default: 1000)",
    )

    args = parser.parse_args()

    # In verbose mode: show debug logs. Otherwise: suppress all logger output
    # (tqdm handles display).
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.setLevel(logging.DEBUG)
    else:
        logging.getLogger().setLevel(logging.WARNING)
        logger.setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)

    tickers_str = args.tickers or "ALL"
    resume_str = " --resume" if args.resume else ""
    batch_str = f" --batch-size {args.batch_size}" if args.batch_size else ""
    print(f"Theta Harvest — Backfill ({args.days} days, {tickers_str}){resume_str}{batch_str}")

    asyncio.run(run_backfill(args))


if __name__ == "__main__":
    main()
