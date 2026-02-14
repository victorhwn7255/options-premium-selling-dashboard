"""
Theta Harvest — FastAPI backend.

Connects to MarketData.app, computes vol metrics,
and serves data to the Next.js frontend.

Data subscriptions:
  - Starter ($12/mo): options chains, stock candles, stock quotes

Usage:
    export MARKETDATA_TOKEN=your_token_here
    uvicorn main:app --reload --port 8000

Or:
    python main.py
"""

import os
import sys
import time
import asyncio
import logging
from datetime import date, datetime, timedelta
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from marketdata_client import MarketDataClient
from fmp_client import get_next_earnings
from csv_store import append_daily_csv, append_quotes_csv
from calculator import build_vol_surface, compute_realized_vol, compute_atm_iv, find_atm_greeks, compute_atr14
from scorer import score_opportunity, ScoringParams
from database import (
    store_daily_iv, get_historical_ivs, get_historical_series, log_scan,
    store_scan_result, get_latest_scan, get_scan_history,
    clear_earnings_cache, update_latest_scan_earnings,
)
from models import (
    ScanResponse, TickerResult, RegimeSummary,
    HistoricalPoint, HealthResponse, TermStructurePointOut, SkewPointOut,
)


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("option-harvest")


# ── Ticker Universe ─────────────────────────────────────
# Add or remove tickers here. Each needs a display name and sector.
UNIVERSE = {
    # ETFs
    "SPY":  {"name": "S&P 500 ETF",        "sector": "Index",      "etf": True},
    "QQQ":  {"name": "Nasdaq 100 ETF",      "sector": "Index",      "etf": True},
    "IWM":  {"name": "Russell 2000 ETF",     "sector": "Index",      "etf": True},
    "EEM":  {"name": "Emerging Markets ETF", "sector": "Index",      "etf": True},
    "GLD":  {"name": "SPDR Gold Trust",      "sector": "Commodities","etf": True},
    "TLT":  {"name": "20+ Year Treasury ETF","sector": "Fixed Income","etf": True},
    "XLE":  {"name": "Energy Select SPDR",   "sector": "Sector ETF", "etf": True},
    "XLF":  {"name": "Financial Select SPDR","sector": "Sector ETF", "etf": True},
    "XLV":  {"name": "Health Care Select SPDR","sector": "Sector ETF","etf": True},
    "XLI":  {"name": "Industrial Select SPDR","sector": "Sector ETF", "etf": True},
    "XLB":  {"name": "Materials Select SPDR", "sector": "Sector ETF", "etf": True},
    # Stocks
    "AAPL": {"name": "Apple",                "sector": "Tech"},
    "MSFT": {"name": "Microsoft",            "sector": "Tech"},
    "GOOG": {"name": "Alphabet",             "sector": "Tech"},
    "AMZN": {"name": "Amazon",               "sector": "Consumer"},
    "META": {"name": "Meta Platforms",        "sector": "Tech"},
    "NVDA": {"name": "NVIDIA",               "sector": "Tech"},
    "TSLA": {"name": "Tesla",                "sector": "Consumer"},
    "NFLX": {"name": "Netflix",              "sector": "Consumer"},
    "PLTR": {"name": "Palantir",             "sector": "Tech"},
    "HOOD": {"name": "Robinhood Markets",    "sector": "Financials"},
    "GS":   {"name": "Goldman Sachs",        "sector": "Financials"},
    "JPM":  {"name": "JPMorgan Chase",       "sector": "Financials"},
    "XOM":  {"name": "Exxon Mobil",          "sector": "Energy"},
    "WMT":  {"name": "Walmart",              "sector": "Consumer"},
    "MCD":  {"name": "McDonald's",           "sector": "Consumer"},
    "KO":   {"name": "Coca-Cola",            "sector": "Consumer"},
}


# ── Application Lifecycle ───────────────────────────────
client: MarketDataClient = None
fmp_api_key: str = None
_scheduler_task: asyncio.Task = None
_scan_task: asyncio.Task = None
_scan_progress: dict = {"status": "idle", "current": 0, "total": 0, "ticker": ""}


async def _cron_loop():
    """Simple asyncio cron: run scan at 6:30 PM ET, Mon-Fri."""
    from zoneinfo import ZoneInfo
    et = ZoneInfo("America/New_York")
    target_hour, target_minute = 18, 30  # 6:30 PM ET

    while True:
        now = datetime.now(tz=et)
        # Next occurrence of target_hour:target_minute on a weekday
        candidate = now.replace(hour=target_hour, minute=target_minute, second=0, microsecond=0)
        if candidate <= now:
            candidate += timedelta(days=1)
        # Skip weekends (5=Sat, 6=Sun)
        while candidate.weekday() >= 5:
            candidate += timedelta(days=1)

        wait_secs = (candidate - now).total_seconds()
        logger.info(f"Scheduler: next scan at {candidate.strftime('%Y-%m-%d %H:%M %Z')} (in {wait_secs/3600:.1f}h)")
        await asyncio.sleep(wait_secs)

        logger.info("Scheduler: starting daily scan")
        try:
            await run_full_scan()
            logger.info("Scheduler: daily scan completed successfully")
        except Exception as e:
            logger.error(f"Scheduler: scan failed — {e}. Retrying in 5 minutes...")
            await asyncio.sleep(300)
            try:
                await run_full_scan()
                logger.info("Scheduler: retry scan completed successfully")
            except Exception as e2:
                logger.error(f"Scheduler: retry also failed — {e2}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    global client, fmp_api_key, _scheduler_task
    api_key = os.environ.get("MARKETDATA_TOKEN")
    if not api_key:
        logger.error(
            "MARKETDATA_TOKEN environment variable not set. "
            "Set it and restart: export MARKETDATA_TOKEN=your_token"
        )
        client = None
    else:
        client = MarketDataClient(api_key=api_key, rate_limit=10)
        logger.info("MarketData client initialized (api.marketdata.app)")
        _scheduler_task = asyncio.create_task(_cron_loop())
        logger.info("Scheduler started: daily scan at 6:30 PM ET, Mon-Fri")

    fmp_api_key = os.environ.get("FMP_API_KEY")
    if fmp_api_key:
        logger.info("FMP API key loaded for earnings data")
    yield
    if _scheduler_task:
        _scheduler_task.cancel()
    if client:
        await client.close()


app = FastAPI(
    title="Theta Harvest",
    description="Volatility analysis dashboard for premium selling opportunities. "
                "Data powered by MarketData.app.",
    version="2.0.0",
    lifespan=lifespan,
)

_cors_origins = [
    "http://localhost:3000",   # Next.js dev server
    "http://localhost:8000",
    "http://localhost:8030",   # Docker backend mapped port
    "http://127.0.0.1:3000",
]
# Add extra origins from CORS_ORIGINS env var (comma-separated)
_extra = os.environ.get("CORS_ORIGINS", "")
if _extra:
    _cors_origins.extend(o.strip() for o in _extra.split(",") if o.strip())

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Core Scan Logic ─────────────────────────────────────
async def scan_single_ticker(ticker: str, meta: dict) -> dict:
    """Fetch data and compute vol surface for one ticker."""
    try:
        # 1. Get current price
        snapshot = await client.get_stock_snapshot(ticker)
        if not snapshot or snapshot.price <= 0:
            logger.warning(f"{ticker}: No price data")
            return None

        # 2. Get daily bars — 120 trading days for RV + chart history
        from_date = date.today() - timedelta(days=180)
        bars = await client.get_daily_bars(ticker, from_date, date.today())
        if len(bars) < 11:
            logger.warning(f"{ticker}: Only {len(bars)} bars, need 11+")
            return None

        # 3. Get options chain (Starter $12/mo required)
        contracts = await client.get_options_chain(ticker)
        if not contracts:
            logger.warning(f"{ticker}: No options data — check MarketData.app subscription")
            return None

        # 3b. Get next earnings date (skip for ETFs)
        if meta.get("etf"):
            earnings_date_str = None
        elif fmp_api_key:
            earnings_date_str = await get_next_earnings(ticker, fmp_api_key)
        else:
            earnings_date_str = await client.get_earnings(ticker)
        earnings_dte = None
        if earnings_date_str:
            earn_date = datetime.strptime(earnings_date_str, "%Y-%m-%d").date()
            earnings_dte = (earn_date - date.today()).days

        # 3c. Extract ATM theta/vega from options chain
        theta, vega = find_atm_greeks(contracts, snapshot.price)

        # 3d. Compute ATR 14
        atr14 = compute_atr14(bars)

        # 4. Get historical IV from our database
        historical_ivs = get_historical_ivs(ticker)

        # 5. Build vol surface
        surface = build_vol_surface(
            ticker=ticker,
            spot_price=snapshot.price,
            bars=bars,
            contracts=contracts,
            historical_ivs=historical_ivs,
        )

        # 6. Store today's IV for future rank computation
        store_daily_iv(
            ticker=ticker,
            atm_iv=surface.iv.iv_current,
            rv30=surface.rv.rv30,
            vrp=surface.vrp,
            term_slope=surface.term_structure.slope,
        )

        # 7. Persist to CSV files (daily metrics + option quotes)
        trading_date = bars[-1].date  # latest bar = most recent trading day
        append_daily_csv(
            ticker, trading_date, snapshot.price,
            surface.iv.iv_current, surface.rv.rv30,
            surface.vrp, surface.term_structure.slope,
        )
        append_quotes_csv(ticker, trading_date, contracts, snapshot.price)

        return {
            "surface": surface,
            "name": meta["name"],
            "sector": meta["sector"],
            "earnings_dte": earnings_dte,
            "theta": theta,
            "vega": vega,
            "atr14": atr14,
        }

    except PermissionError as e:
        logger.error(f"{ticker}: {e}")
        raise
    except Exception as e:
        logger.error(f"{ticker}: Error during scan — {type(e).__name__}: {e}")
        return None


async def run_full_scan() -> ScanResponse:
    """Scan all tickers in the universe."""
    if client is None:
        raise RuntimeError("MarketData API token not configured. Set MARKETDATA_TOKEN env var.")

    # Permissive defaults — no filtering, all tickers included
    params = ScoringParams(
        min_iv_rank=0, min_vrp=-999, max_rv_accel=999,
        max_skew=999, only_contango=False,
        sectors=list({m["sector"] for m in UNIVERSE.values()}),
    )

    start = time.time()
    results: list[TickerResult] = []
    errors = []

    # Scan tickers with concurrency limit (avoid rate limit storms)
    semaphore = asyncio.Semaphore(1)
    total_tickers = len(UNIVERSE)
    scanned_count = 0

    async def _scan_with_limit(ticker, meta):
        nonlocal scanned_count
        async with semaphore:
            _scan_progress["ticker"] = ticker
            result = ticker, await scan_single_ticker(ticker, meta)
            scanned_count += 1
            _scan_progress["current"] = scanned_count
            return result

    _scan_progress.update({"status": "scanning", "current": 0, "total": total_tickers, "ticker": ""})

    tasks = [_scan_with_limit(t, m) for t, m in UNIVERSE.items()]
    scan_results = await asyncio.gather(*tasks, return_exceptions=True)

    for result in scan_results:
        if isinstance(result, Exception):
            errors.append(str(result))
            continue
        ticker, data = result
        if data is None:
            errors.append(f"{ticker}: scan returned no data")
            continue

        scored = score_opportunity(
            surface=data["surface"],
            name=data["name"],
            sector=data["sector"],
            params=params,
        )
        scored.earnings_dte = data.get("earnings_dte")
        scored.theta = data.get("theta")
        scored.vega = data.get("vega")
        scored.atr14 = data.get("atr14")

        results.append(TickerResult(
            ticker=scored.ticker,
            name=scored.name,
            sector=scored.sector,
            price=scored.price,
            iv_current=scored.iv_current,
            iv_rank=scored.iv_rank,
            iv_percentile=scored.iv_percentile,
            rv10=scored.rv10,
            rv20=scored.rv20,
            rv30=scored.rv30,
            vrp=scored.vrp,
            vrp_ratio=scored.vrp_ratio,
            rv_acceleration=scored.rv_acceleration,
            term_slope=scored.term_slope,
            is_contango=scored.is_contango,
            skew_25d=scored.skew_25d,
            signal_score=scored.signal_score,
            regime=scored.regime,
            recommendation=scored.recommendation,
            flags=scored.flags,
            suggested_delta=scored.suggested_delta,
            suggested_structure=scored.suggested_structure,
            suggested_dte=scored.suggested_dte,
            suggested_max_notional=scored.suggested_max_notional,
            earnings_dte=scored.earnings_dte,
            is_etf=UNIVERSE[scored.ticker].get("etf", False),
            theta=round(scored.theta, 4) if scored.theta is not None else None,
            vega=round(scored.vega, 4) if scored.vega is not None else None,
            atr14=scored.atr14,
            term_structure_points=[
                TermStructurePointOut(**p) for p in scored.term_structure_points
            ],
            skew_points=[
                SkewPointOut(**p) for p in scored.skew_points
            ],
        ))

    # Sort by score descending
    results.sort(key=lambda r: r.signal_score, reverse=True)

    # Compute regime summary
    if results:
        avg_iv_rank = sum(r.iv_rank for r in results) / len(results)
        avg_rv_accel = sum(r.rv_acceleration for r in results) / len(results)
        danger_count = sum(1 for r in results if r.regime == "DANGER")
        caution_count = sum(1 for r in results if r.regime == "CAUTION")

        # SPY term slope as VIX proxy
        spy_result = next((r for r in results if r.ticker == "SPY"), None)
        vix_term = spy_result.term_slope if spy_result else None

        overall = "NORMAL"
        color = "#6B8C5A"
        desc = "Contango, moderate IV — standard premium selling conditions"

        if danger_count >= 2 or (vix_term and vix_term > 1.05):
            overall = "ELEVATED RISK"
            color = "#C45A5A"
            desc = "Multiple backwardation signals — reduce exposure, widen spreads, hedge tails"
        elif caution_count >= 3 or avg_rv_accel > 1.1:
            overall = "CAUTION"
            color = "#C49A5A"
            desc = "Rising realized vol — tighten position sizing, favor defined-risk structures"
        elif avg_iv_rank > 80:
            overall = "OPPORTUNITY"
            color = "#C47B5A"
            desc = "Elevated IV with contained RV — favorable premium selling environment"

        regime = RegimeSummary(
            overall_regime=overall,
            regime_color=color,
            description=desc,
            avg_iv_rank=round(avg_iv_rank, 1),
            avg_rv_accel=round(avg_rv_accel, 3),
            danger_count=danger_count,
            caution_count=caution_count,
            total_tickers=len(results),
            vix_term_slope=vix_term,
        )
    else:
        regime = RegimeSummary(
            overall_regime="NO DATA",
            regime_color="#9A8E82",
            description="No tickers returned data. Check MarketData API token and subscription.",
            avg_iv_rank=0, avg_rv_accel=0, danger_count=0,
            caution_count=0, total_tickers=0,
        )

    # Historical data for charts
    historical = {}
    for ticker in ["SPY", "QQQ"]:
        series = get_historical_series(ticker, lookback_days=120)
        if series:
            historical[ticker] = [HistoricalPoint(**s) for s in series]

    duration = time.time() - start
    log_scan(len(results), duration, errors if errors else None)
    logger.info(f"Scan complete: {len(results)} tickers in {duration:.1f}s ({len(errors)} errors)")

    scanned_at = datetime.utcnow().isoformat() + "Z"

    response = ScanResponse(
        timestamp=datetime.now().isoformat(),
        regime=regime,
        tickers=results,
        historical=historical,
        scanned_at=scanned_at,
        cached=False,
    )

    # Persist to SQLite for cached retrieval
    store_scan_result(
        scanned_at=scanned_at,
        regime=regime.model_dump(),
        tickers=[t.model_dump() for t in results],
        historical={k: [p.model_dump() for p in v] for k, v in historical.items()},
    )

    return response


# ── API Endpoints ───────────────────────────────────────

@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """Check system status."""
    from database import get_connection
    conn = get_connection()
    count = conn.execute("SELECT COUNT(*) FROM daily_iv").fetchone()[0]
    conn.close()

    return HealthResponse(
        status="ok" if client else "degraded",
        marketdata_connected=client is not None,
        db_initialized=True,
        tickers_configured=len(UNIVERSE),
        historical_data_points=count,
    )


@app.get("/api/scan/latest", response_model=ScanResponse)
async def get_latest_cached_scan():
    """Return the most recent cached scan result, or an empty response if none exists."""
    cached = get_latest_scan()
    if not cached:
        return ScanResponse(
            timestamp=datetime.now().isoformat(),
            regime=None,
            tickers=[],
            historical={},
            scanned_at=None,
            cached=False,
            message="No scan results yet. The scanner runs automatically after market close (~6:30 PM ET).",
        )
    # Enrich cached tickers with is_etf from UNIVERSE (may be missing in old data)
    for t in cached["tickers"]:
        if t.get("ticker") in UNIVERSE:
            t["is_etf"] = UNIVERSE[t["ticker"]].get("etf", False)

    return ScanResponse(
        timestamp=cached["scanned_at"],
        regime=RegimeSummary(**cached["regime"]),
        tickers=[TickerResult(**t) for t in cached["tickers"]],
        historical={
            k: [HistoricalPoint(**p) for p in v]
            for k, v in cached["historical"].items()
        },
        scanned_at=cached["scanned_at"],
        cached=True,
    )


def _is_scanned_today(scanned_at: str) -> bool:
    """Check if a scanned_at UTC timestamp falls on today in ET."""
    from zoneinfo import ZoneInfo
    et = ZoneInfo("America/New_York")
    scan_dt = datetime.fromisoformat(scanned_at.replace("Z", "+00:00"))
    return scan_dt.astimezone(et).date() == datetime.now(tz=et).date()


@app.post("/api/scan")
async def trigger_scan():
    """Manually trigger a full scan (limited to once per day). Runs in background."""
    global _scan_task

    cached = get_latest_scan()
    if cached and cached.get("scanned_at") and _is_scanned_today(cached["scanned_at"]):
        # Already scanned today — return cached result
        for t in cached["tickers"]:
            if t.get("ticker") in UNIVERSE:
                t["is_etf"] = UNIVERSE[t["ticker"]].get("etf", False)
        return ScanResponse(
            timestamp=cached["scanned_at"],
            regime=RegimeSummary(**cached["regime"]),
            tickers=[TickerResult(**t) for t in cached["tickers"]],
            historical={
                k: [HistoricalPoint(**p) for p in v]
                for k, v in cached["historical"].items()
            },
            scanned_at=cached["scanned_at"],
            cached=True,
        )

    # If a scan is already running, return status
    if _scan_task and not _scan_task.done():
        return JSONResponse({"status": "scanning", **_scan_progress})

    # Start scan in background
    async def _background_scan():
        try:
            await run_full_scan()
            _scan_progress["status"] = "completed"
            logger.info("Background scan completed successfully")
        except Exception as e:
            _scan_progress["status"] = "error"
            _scan_progress["error"] = str(e)
            logger.error(f"Background scan failed: {e}")

    _scan_task = asyncio.create_task(_background_scan())
    return JSONResponse({"status": "scanning", "current": 0, "total": len(UNIVERSE), "ticker": ""})


@app.get("/api/scan/status")
async def scan_status():
    """Check current scan progress."""
    if _scan_task and not _scan_task.done():
        return _scan_progress
    return {"status": _scan_progress.get("status", "idle"), **_scan_progress}


@app.get("/api/scan/history")
async def get_scan_history_endpoint(limit: int = Query(default=10, le=50)):
    """Return metadata for recent scans."""
    return {"scans": get_scan_history(limit=limit)}


@app.get("/api/ticker/{ticker}/history")
async def ticker_history(ticker: str, days: int = Query(default=120, le=365)):
    """Get historical IV/RV series for a specific ticker."""
    ticker = ticker.upper()
    if ticker not in UNIVERSE:
        raise HTTPException(404, f"Ticker {ticker} not in universe")

    series = get_historical_series(ticker, lookback_days=days)
    return {"ticker": ticker, "history": series}


@app.get("/api/universe")
async def get_universe():
    """Return the configured ticker universe."""
    return {
        "tickers": [
            {"ticker": t, "name": m["name"], "sector": m["sector"]}
            for t, m in UNIVERSE.items()
        ]
    }


_EARNINGS_REFRESH_LIMIT = 3
_earnings_refresh_tracker: dict = {"date": None, "count": 0}


def _get_earnings_remaining() -> int:
    today = date.today().isoformat()
    if _earnings_refresh_tracker["date"] != today:
        return _EARNINGS_REFRESH_LIMIT
    return max(0, _EARNINGS_REFRESH_LIMIT - _earnings_refresh_tracker["count"])


@app.get("/api/earnings/remaining")
async def earnings_remaining():
    """Return how many earnings refreshes remain today."""
    return {"remaining": _get_earnings_remaining()}


@app.post("/api/earnings/refresh")
async def refresh_earnings():
    """Clear earnings cache and re-fetch from FMP (max 3x/day)."""
    if not fmp_api_key:
        raise HTTPException(400, "FMP_API_KEY not configured")

    today = date.today().isoformat()
    if _earnings_refresh_tracker["date"] != today:
        _earnings_refresh_tracker["date"] = today
        _earnings_refresh_tracker["count"] = 0

    if _earnings_refresh_tracker["count"] >= _EARNINGS_REFRESH_LIMIT:
        return {"earnings": {}, "remaining": 0}

    _earnings_refresh_tracker["count"] += 1
    remaining = _EARNINGS_REFRESH_LIMIT - _earnings_refresh_tracker["count"]

    clear_earnings_cache()
    results = {}
    for ticker, meta in UNIVERSE.items():
        if meta.get("etf"):
            continue
        earnings_date_str = await get_next_earnings(ticker, fmp_api_key)
        earnings_dte = None
        if earnings_date_str:
            earn_date = datetime.strptime(earnings_date_str, "%Y-%m-%d").date()
            earnings_dte = (earn_date - date.today()).days
        results[ticker] = earnings_dte
    update_latest_scan_earnings(results)
    return {"earnings": results, "remaining": remaining}


# ── Run directly ────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    logger.info(f"Starting Theta Harvest on port {port}")
    logger.info(f"Dashboard: http://localhost:3000  (Next.js frontend)")
    logger.info(f"API docs:  http://localhost:{port}/docs")
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True, reload_excludes=["data/*", "*.db"])
