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
from typing import Optional

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
    store_scan_result, get_latest_scan, get_scan_history, get_previous_day_scan,
    clear_earnings_cache, update_latest_scan_earnings,
    store_verification_result, get_latest_verification,
    store_earnings_verification, get_latest_earnings_verification,
    get_vrp_history_by_date,
    # ── Credit Put Spreads (Phase 3) ──
    get_vrp_history, record_cps_candidate, get_consecutive_sell_days,
    get_consecutive_exact_spread_days,
    save_cps_scan_response, get_latest_cps_scan_response,
)
from models import (
    ScanResponse, TickerResult, RegimeSummary,
    HistoricalPoint, HealthResponse, TermStructurePointOut, SkewPointOut,
    TickerDelta, TickerComparison, ComparisonResponse,
    VrpHistoryPoint, VrpHistoryResponse,
    # ── Credit Put Spreads ──
    CreditPutSpreadsResponse, CPSRejectionSummary, RegimeOverlay,
)
from scan_quality import compute_scan_quality, suppress_actionable
# ── Credit Put Spreads (Phase 3) ──
import config as cfg
from regime_overlay import fetch_regime_overlay
from spread_builder import build_candidate_outcome_for_ticker


def _apply_scan_quality(tickers: list) -> tuple[str, Optional[str]]:
    """
    Compute scan-quality on a TickerResult list and suppress actionable rows
    in-place if degraded. Used for both fresh scans and cached reads so the
    QA gate applies uniformly. Returns (quality, reason).
    """
    quality, reason = compute_scan_quality(tickers)
    if quality == "DEGRADED":
        suppress_actionable(tickers, reason)
    return quality, reason


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("option-harvest")


# ── Ticker Universe ─────────────────────────────────────
# Universe (33 tickers) and CPS_UNIVERSE live in backend/config.py.
# The `UNIVERSE` name is kept as a module-level alias so backfill.py /
# repair_rv.py / cached-scan enrichment code still imports cleanly.
from config import NAKED_PUT_UNIVERSE as UNIVERSE  # noqa: E402


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
        # Skip weekends and US market holidays
        while not _is_trading_day(candidate.date()):
            candidate += timedelta(days=1)

        wait_secs = (candidate - now).total_seconds()
        logger.info(f"Scheduler: next scan at {candidate.strftime('%Y-%m-%d %H:%M %Z')} (in {wait_secs/3600:.1f}h)")
        await asyncio.sleep(wait_secs)

        logger.info("Scheduler: starting daily scan")
        try:
            scan_response = await run_full_scan()
            logger.info("Scheduler: daily scan completed successfully")
            # Fire-and-forget verification
            tickers_data = [t.model_dump() for t in scan_response.tickers]
            asyncio.create_task(run_post_scan_verification(scan_response.scanned_at, tickers_data))
        except Exception as e:
            logger.error(f"Scheduler: scan failed — {e}. Retrying in 5 minutes...")
            await asyncio.sleep(300)
            try:
                retry_response = await run_full_scan()
                logger.info("Scheduler: retry scan completed successfully")
                retry_data = [t.model_dump() for t in retry_response.tickers]
                asyncio.create_task(run_post_scan_verification(retry_response.scanned_at, retry_data))
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

    # Run verification against latest cached scan if none exists yet
    cached = get_latest_scan()
    if cached and cached.get("tickers"):
        latest_verif = get_latest_verification()
        latest_earn_verif = get_latest_earnings_verification()
        needs_run = (
            not latest_verif or latest_verif["scanned_at"] != cached["scanned_at"]
            or not latest_earn_verif or latest_earn_verif["scanned_at"] != cached["scanned_at"]
        )
        if needs_run:
            logger.info("Startup: running verification against latest cached scan")
            asyncio.create_task(
                run_post_scan_verification(cached["scanned_at"], cached["tickers"])
            )

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

        # 6. Store today's IV for future rank computation (skip if no reliable IV)
        if surface.iv.iv_current is not None:
            store_daily_iv(
                ticker=ticker,
                atm_iv=surface.iv.iv_current,
                rv30=surface.rv.rv30,
                vrp=surface.vrp,
                term_slope=surface.term_structure.slope,
            )

        # 7. Persist to CSV files (daily metrics + option quotes)
        from zoneinfo import ZoneInfo
        trading_date = datetime.now(tz=ZoneInfo("America/New_York")).date().isoformat()
        if surface.iv.iv_current is not None:
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
            # ── Phase 3: pass raw chain + spot through for CPS construction.
            # Only used downstream when ticker is in CPS_UNIVERSE; cheap to
            # always include because both already live in this function scope.
            "_contracts": contracts,
            "_spot": snapshot.price,
        }

    except PermissionError as e:
        logger.error(f"{ticker}: {e}")
        raise
    except Exception as e:
        logger.error(f"{ticker}: Error during scan — {type(e).__name__}: {e}")
        return None


def _classify_rejection_reasons(reasons: list[str]) -> str:
    """Bucket a CPS rejection-reason list into one summary category."""
    text = " ".join(reasons).lower()
    if "regime overlay" in text:
        return "overlay"
    if any(k in text for k in ("avoid:", "no_edge: vrp", "wait: rv_accel", "earnings")):
        return "base_gate"
    if "consecutive_sell_days" in text:
        return "confirmation"
    if any(k in text for k in ("bid_ask_ratio", "oi ", "volume")):
        return "execution"
    return "construction"


def _build_cps_response(
    results: list[TickerResult],
    cps_raw_inputs: dict[str, dict],
    market_regime_label: str,
    scanned_at: str,
) -> CreditPutSpreadsResponse:
    """Build the /api/credit-put-spreads/latest response payload.

    Runs after the Naked Puts scoring loop completes. Reads only from
    inputs hydrated during the scan — no extra MarketData calls. Failure
    in any one ticker is caught and reported in `rejection_summary`
    rather than propagated.
    """
    scan_date = datetime.utcnow().date().isoformat()

    # One overlay fetch per scan (not per ticker).
    try:
        overlay = fetch_regime_overlay()
    except Exception as e:  # network / dependency / unknown
        logger.warning("Regime overlay fetch failed: %s", e)
        overlay = RegimeOverlay(
            status="UNKNOWN",
            warnings=[f"Regime overlay fetch errored ({type(e).__name__}); candidates not blocked."],
        )

    candidates = []
    summary = CPSRejectionSummary()
    by_ticker = {r.ticker: r for r in results}

    for ticker in cfg.CPS_UNIVERSE:
        tr = by_ticker.get(ticker)
        raw = cps_raw_inputs.get(ticker, {})
        spot = raw.get("spot", 0.0)
        if tr is None or spot <= 0:
            # Ticker didn't even produce a TickerResult — count as NO_DATA construction.
            summary.checked += 1
            summary.rejected_by_construction += 1
            try:
                record_cps_candidate(
                    scan_date=scan_date, ticker=ticker, action="NO_DATA",
                    sell_eligible=False, passed_filters=False,
                )
            except Exception:
                logger.exception("record_cps_candidate failed for %s", ticker)
            continue

        summary.checked += 1
        try:
            vrp_hist = get_vrp_history(ticker, days=60)
        except Exception:
            vrp_hist = None

        try:
            consec = get_consecutive_sell_days(ticker)
        except Exception:
            consec = 0

        outcome = build_candidate_outcome_for_ticker(
            ticker=ticker,
            ticker_result=tr,
            chain=raw.get("contracts") or [],
            spot=spot,
            atr14=raw.get("atr14"),
            regime_overlay=overlay,
            consecutive_sell_days=consec,
            exact_spread_consecutive_days=0,  # filled in below if candidate built
            vrp_history_60d=vrp_hist,
        )

        # Compute exact-spread streak NOW that we know the strike pair.
        if outcome.candidate is not None:
            try:
                exact = get_consecutive_exact_spread_days(
                    ticker=ticker,
                    expiration=outcome.candidate.expiration,
                    short_strike=outcome.candidate.short_put.strike,
                    long_strike=outcome.candidate.long_put.strike,
                )
                outcome.candidate.exact_spread_consecutive_days = exact
            except Exception:
                pass  # display-only context; never block on this

        # Bucket for the rejection summary.
        # An outcome is "actionable" only when a candidate was actually built —
        # SELL_CPS / WATCH_CPS reach step 12 with `candidate != None`. A WAIT
        # produced by base-gate failure (e.g. RV_accel > threshold) has
        # `candidate=None` and belongs in the rejection buckets so the
        # classifier can route it correctly (its "wait: rv_accel" reason maps
        # to `base_gate`). Counting it as actionable inflated the displayed
        # count while leaving the candidates list empty.
        if outcome.candidate is not None and outcome.action in ("SELL_CPS", "WATCH_CPS"):
            summary.actionable += 1
            candidates.append(outcome.candidate)
        else:
            bucket = _classify_rejection_reasons(outcome.rejection_reasons)
            if bucket == "overlay":
                summary.rejected_by_overlay += 1
            elif bucket == "base_gate":
                summary.rejected_by_base_gate += 1
            elif bucket == "confirmation":
                summary.rejected_by_confirmation += 1
            elif bucket == "execution":
                summary.rejected_by_execution += 1
            else:
                summary.rejected_by_construction += 1

        # Persist for tomorrow's confirmation lookup. Eligibility means
        # "passed every filter that does NOT depend on confirmation/overlay" —
        # i.e. the ticker would have been SELL_CPS-or-WATCH_CPS today.
        sell_eligible = outcome.action in ("SELL_CPS", "WATCH_CPS")
        try:
            cand = outcome.candidate
            record_cps_candidate(
                scan_date=scan_date,
                ticker=ticker,
                action=outcome.action,
                expiration=cand.expiration if cand else None,
                short_strike=cand.short_put.strike if cand else None,
                long_strike=cand.long_put.strike if cand else None,
                credit_to_width=cand.credit_to_width if cand else None,
                base_score=cand.base_score if cand else None,
                regime=cand.regime if cand else None,
                passed_filters=sell_eligible,
                sell_eligible=sell_eligible,
            )
        except Exception:
            logger.exception("record_cps_candidate failed for %s", ticker)

    # Top-level ranking — same key as build_credit_put_spread_candidates().
    _action_order = {"SELL_CPS": 0, "WATCH_CPS": 1, "WAIT": 2}
    _rv_order = {"Excellent": 0, "Good": 1, "Acceptable": 2, "Caution": 3, "Avoid / Wait": 4}
    candidates.sort(key=lambda c: (
        _action_order.get(c.action, 9),
        -c.base_score,
        -c.credit_to_width,
        _rv_order.get(c.rv_accel_status or "Acceptable", 2),
        c.term_slope if c.term_slope is not None else 1.0,
    ))

    message = None
    if not candidates:
        message = (
            "No Credit Put Spread candidates passed today's filters. "
            "Check rejection_summary for the dominant reason."
        )

    return CreditPutSpreadsResponse(
        scan_date=scan_date,
        market_regime=market_regime_label,
        cps_universe=list(cfg.CPS_UNIVERSE),
        regime_overlay=overlay,
        candidates=candidates,
        message=message,
        rejection_summary=summary,
    )


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

    # Phase 3: capture raw chain + spot for CPS-universe tickers so the
    # spread builder can run after the scoring loop without re-fetching.
    cps_raw_inputs: dict[str, dict] = {}

    for result in scan_results:
        if isinstance(result, Exception):
            errors.append(str(result))
            continue
        ticker, data = result
        if data is None:
            errors.append(f"{ticker}: scan returned no data")
            continue

        if ticker in cfg.CPS_UNIVERSE:
            cps_raw_inputs[ticker] = {
                "contracts": data.get("_contracts") or [],
                "spot": data.get("_spot") or 0.0,
                "atr14": data.get("atr14"),
            }

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

    # ── Scan Quality Detection ──────────────────────
    # See references/dashboard-behavior-qa-report.md §5.6 / §7.3.
    # When DEGRADED, downgrade SELL/CONDITIONAL/WATCHLIST → NO EDGE so the
    # dashboard doesn't surface tradeable signals from unreliable inputs.
    scan_quality, scan_quality_reason = _apply_scan_quality(results)
    if scan_quality == "DEGRADED":
        logger.warning(f"Scan quality DEGRADED: {scan_quality_reason}")

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
            desc = "Rising realized vol — environment less clean, favor defined-risk structures and require strong confirmation"
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
        scan_quality=scan_quality,
        scan_quality_reason=scan_quality_reason,
    )

    # Persist to SQLite for cached retrieval
    store_scan_result(
        scanned_at=scanned_at,
        regime=regime.model_dump(),
        tickers=[t.model_dump() for t in results],
        historical={k: [p.model_dump() for p in v] for k, v in historical.items()},
    )

    # ── Phase 3: Credit Put Spreads candidate build + cache ─────────
    # Runs after Naked Puts persistence so a CPS failure can never affect
    # the existing scan result. Any exception is logged and swallowed.
    try:
        cps_response = _build_cps_response(
            results=results,
            cps_raw_inputs=cps_raw_inputs,
            market_regime_label=regime.overall_regime,
            scanned_at=scanned_at,
        )
        save_cps_scan_response(
            scan_date=cps_response.scan_date,
            response_dict=cps_response.model_dump(),
        )
        logger.info(
            "CPS scan: %d actionable / %d checked",
            cps_response.rejection_summary.actionable if cps_response.rejection_summary else 0,
            cps_response.rejection_summary.checked if cps_response.rejection_summary else 0,
        )
    except Exception:
        logger.exception("CPS build/persist failed — Naked Puts unaffected")

    return response


# ── Post-Scan Verification ──────────────────────────────
async def run_post_scan_verification(scanned_at: str, tickers_data: list[dict]):
    """Run metrics verification after a scan completes. Non-blocking, non-critical."""
    try:
        # Add utils/ to sys.path so we can import verify_metrics
        # In Docker: /app/utils (sibling to main.py), locally: ../utils (parent of backend/)
        app_dir = Path(__file__).resolve().parent
        candidates = [app_dir / "utils", app_dir.parent / "utils"]
        for candidate in candidates:
            utils_dir = str(candidate)
            if candidate.exists() and utils_dir not in sys.path:
                sys.path.insert(0, utils_dir)
                break
        from verify_metrics import fetch_yahoo_bars, fetch_vix, verify_all

        ticker_symbols = [t["ticker"] for t in tickers_data]

        # Fetch Yahoo data (blocking I/O, run in executor)
        loop = asyncio.get_running_loop()
        yahoo_data = await loop.run_in_executor(None, fetch_yahoo_bars, ticker_symbols)

        vix_close = None
        if "SPY" in ticker_symbols:
            vix_close = await loop.run_in_executor(None, fetch_vix)

        # Run metrics verification
        report = verify_all(tickers_data, yahoo_data, vix_close, scan_timestamp=scanned_at)
        report_dict = report.to_dict()

        # Store in database
        store_verification_result(report_dict)

        logger.info(
            f"Metrics verification: {report.total_pass}/{report.total_checks} PASS, "
            f"{report.total_fail} FAIL, {report.total_warn} WARN"
        )

        # Run earnings verification (separate from metrics)
        try:
            from verify_metrics import fetch_yahoo_earnings, verify_earnings

            non_etf = [t["ticker"] for t in tickers_data if not t.get("is_etf", False)]
            yahoo_earnings = await loop.run_in_executor(
                None, fetch_yahoo_earnings, non_etf, scanned_at
            )
            earnings_report = verify_earnings(tickers_data, yahoo_earnings, scan_timestamp=scanned_at)
            store_earnings_verification(earnings_report)

            logger.info(
                f"Earnings verification: {earnings_report['pass_count']}/{earnings_report['total_checks']} PASS, "
                f"{earnings_report['fail_count']} FAIL, {earnings_report['skip_count']} SKIP"
            )

            # Backfill missing FMP earnings dates from Yahoo
            yahoo_fills = {}
            for check in earnings_report["checks"]:
                if check.get("note") == "Filled from Yahoo (FMP missing)" and check.get("yahoo_dte") is not None:
                    yahoo_fills[check["ticker"]] = check["yahoo_dte"]
            if yahoo_fills:
                update_latest_scan_earnings(yahoo_fills)
                logger.info(f"Filled {len(yahoo_fills)} missing earnings from Yahoo: {', '.join(sorted(yahoo_fills))}")

            # Override FMP with Yahoo when both exist but differ by >5 days
            yahoo_overrides = {}
            for check in earnings_report["checks"]:
                if (check["status"] == "FAIL"
                        and check.get("diff_days") is not None
                        and abs(check["diff_days"]) > 5
                        and check.get("yahoo_dte") is not None):
                    yahoo_overrides[check["ticker"]] = check["yahoo_dte"]
            if yahoo_overrides:
                update_latest_scan_earnings(yahoo_overrides)
                logger.info(f"Overrode {len(yahoo_overrides)} earnings with Yahoo (>5d diff): {', '.join(sorted(yahoo_overrides))}")
        except Exception as e:
            logger.warning(f"Earnings verification failed (non-critical): {e}")

    except Exception as e:
        logger.warning(f"Post-scan verification failed (non-critical): {e}")


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

    ticker_models = [TickerResult(**t) for t in cached["tickers"]]
    quality, reason = _apply_scan_quality(ticker_models)

    return ScanResponse(
        timestamp=cached["scanned_at"],
        regime=RegimeSummary(**cached["regime"]),
        tickers=ticker_models,
        historical={
            k: [HistoricalPoint(**p) for p in v]
            for k, v in cached["historical"].items()
        },
        scanned_at=cached["scanned_at"],
        cached=True,
        scan_quality=quality,
        scan_quality_reason=reason,
    )


def _is_scanned_today(scanned_at: str) -> bool:
    """Check if a scanned_at UTC timestamp falls on today in ET."""
    from zoneinfo import ZoneInfo
    et = ZoneInfo("America/New_York")
    scan_dt = datetime.fromisoformat(scanned_at.replace("Z", "+00:00"))
    return scan_dt.astimezone(et).date() == datetime.now(tz=et).date()


def _us_market_holidays(year: int) -> set[date]:
    """Return all NYSE-closed dates for a given year. Pure datetime math, no deps."""

    def _observe(d: date) -> date:
        """Fri if Sat, Mon if Sun."""
        if d.weekday() == 5:
            return d - timedelta(days=1)
        if d.weekday() == 6:
            return d + timedelta(days=1)
        return d

    def _nth_weekday(year: int, month: int, weekday: int, n: int) -> date:
        """Return the nth occurrence of weekday in month (1-indexed)."""
        first = date(year, month, 1)
        offset = (weekday - first.weekday()) % 7
        return first + timedelta(days=offset + 7 * (n - 1))

    def _last_weekday(year: int, month: int, weekday: int) -> date:
        """Return the last occurrence of weekday in month."""
        if month == 12:
            last_day = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            last_day = date(year, month + 1, 1) - timedelta(days=1)
        offset = (last_day.weekday() - weekday) % 7
        return last_day - timedelta(days=offset)

    def _easter(year: int) -> date:
        """Anonymous Gregorian algorithm for Easter Sunday."""
        a = year % 19
        b, c = divmod(year, 100)
        d, e = divmod(b, 4)
        f = (b + 8) // 25
        g = (b - f + 1) // 3
        h = (19 * a + b - d - g + 15) % 30
        i, k = divmod(c, 4)
        l = (32 + 2 * e + 2 * i - h - k) % 7  # noqa: E741
        m = (a + 11 * h + 22 * l) // 451
        month = (h + l - 7 * m + 114) // 31
        day = ((h + l - 7 * m + 114) % 31) + 1
        return date(year, month, day)

    holidays = set()
    holidays.add(_observe(date(year, 1, 1)))                   # New Year's Day
    holidays.add(_nth_weekday(year, 1, 0, 3))                  # MLK Day (3rd Mon Jan)
    holidays.add(_nth_weekday(year, 2, 0, 3))                  # Presidents' Day (3rd Mon Feb)
    holidays.add(_easter(year) - timedelta(days=2))             # Good Friday
    holidays.add(_last_weekday(year, 5, 0))                     # Memorial Day (last Mon May)
    holidays.add(_observe(date(year, 6, 19)))                   # Juneteenth
    holidays.add(_observe(date(year, 7, 4)))                    # Independence Day
    holidays.add(_nth_weekday(year, 9, 0, 1))                   # Labor Day (1st Mon Sep)
    holidays.add(_nth_weekday(year, 11, 3, 4))                  # Thanksgiving (4th Thu Nov)
    holidays.add(_observe(date(year, 12, 25)))                  # Christmas
    return holidays


def _is_trading_day(d: date) -> bool:
    """True if d is a weekday and not a US market holiday."""
    if d.weekday() >= 5:
        return False
    return d not in _us_market_holidays(d.year)


@app.post("/api/scan")
async def trigger_scan():
    """Manually trigger a full scan (limited to once per day). Runs in background."""
    global _scan_task
    from zoneinfo import ZoneInfo
    et = ZoneInfo("America/New_York")
    today_et = datetime.now(tz=et).date()

    # Block scans on non-trading days (weekends + holidays)
    if not _is_trading_day(today_et):
        cached = get_latest_scan()
        if cached and cached.get("scanned_at"):
            for t in cached["tickers"]:
                if t.get("ticker") in UNIVERSE:
                    t["is_etf"] = UNIVERSE[t["ticker"]].get("etf", False)
            ticker_models = [TickerResult(**t) for t in cached["tickers"]]
            quality, reason = _apply_scan_quality(ticker_models)
            return ScanResponse(
                timestamp=cached["scanned_at"],
                regime=RegimeSummary(**cached["regime"]),
                tickers=ticker_models,
                historical={
                    k: [HistoricalPoint(**p) for p in v]
                    for k, v in cached["historical"].items()
                },
                scanned_at=cached["scanned_at"],
                cached=True,
                message="Market is closed today. Showing last available scan.",
                scan_quality=quality,
                scan_quality_reason=reason,
            )
        return JSONResponse({"status": "closed", "message": "Market is closed today"})

    # Block scans before 6:30 PM ET (market closes 4 PM, data settles by ~6:30 PM)
    now_et = datetime.now(tz=et)
    if now_et.hour < 18 or (now_et.hour == 18 and now_et.minute < 30):
        cached = get_latest_scan()
        if cached and cached.get("scanned_at"):
            for t in cached["tickers"]:
                if t.get("ticker") in UNIVERSE:
                    t["is_etf"] = UNIVERSE[t["ticker"]].get("etf", False)
            ticker_models = [TickerResult(**t) for t in cached["tickers"]]
            quality, reason = _apply_scan_quality(ticker_models)
            return ScanResponse(
                timestamp=cached["scanned_at"],
                regime=RegimeSummary(**cached["regime"]),
                tickers=ticker_models,
                historical={
                    k: [HistoricalPoint(**p) for p in v]
                    for k, v in cached["historical"].items()
                },
                scanned_at=cached["scanned_at"],
                cached=True,
                message="Scan available after 6:30 PM ET.",
                scan_quality=quality,
                scan_quality_reason=reason,
            )
        return JSONResponse({"status": "waiting", "message": "Scan available after 6:30 PM ET"})

    cached = get_latest_scan()
    if cached and cached.get("scanned_at") and _is_scanned_today(cached["scanned_at"]):
        # Already scanned today — return cached result
        for t in cached["tickers"]:
            if t.get("ticker") in UNIVERSE:
                t["is_etf"] = UNIVERSE[t["ticker"]].get("etf", False)
        ticker_models = [TickerResult(**t) for t in cached["tickers"]]
        quality, reason = _apply_scan_quality(ticker_models)
        return ScanResponse(
            timestamp=cached["scanned_at"],
            regime=RegimeSummary(**cached["regime"]),
            tickers=ticker_models,
            historical={
                k: [HistoricalPoint(**p) for p in v]
                for k, v in cached["historical"].items()
            },
            scanned_at=cached["scanned_at"],
            cached=True,
            scan_quality=quality,
            scan_quality_reason=reason,
        )

    # If a scan is already running, return status
    if _scan_task and not _scan_task.done():
        return JSONResponse({"status": "scanning", **_scan_progress})

    # Start scan in background
    async def _background_scan():
        try:
            scan_response = await run_full_scan()
            _scan_progress["status"] = "completed"
            logger.info("Background scan completed successfully")
            # Fire-and-forget verification
            tickers_data = [t.model_dump() for t in scan_response.tickers]
            asyncio.create_task(run_post_scan_verification(scan_response.scanned_at, tickers_data))
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


def _compute_deltas(current: dict, previous: dict) -> TickerDelta:
    """Compute day-over-day deltas between two ticker result dicts."""
    def _safe_sub(a, b):
        if a is None or b is None:
            return None
        return round(a - b, 4)

    regime_changed = current["regime"] != previous["regime"]
    return TickerDelta(
        score=current["signal_score"] - previous["signal_score"],
        iv=_safe_sub(current.get("iv_current"), previous.get("iv_current")),
        iv_percentile=round(current["iv_percentile"] - previous["iv_percentile"], 1),
        rv30=round(current["rv30"] - previous["rv30"], 2),
        vrp=_safe_sub(current.get("vrp"), previous.get("vrp")),
        term_slope=round(current["term_slope"] - previous["term_slope"], 3),
        rv_acceleration=round(current["rv_acceleration"] - previous["rv_acceleration"], 3),
        skew_25d=round(current["skew_25d"] - previous["skew_25d"], 1),
        regime_changed=regime_changed,
        previous_regime=previous["regime"] if regime_changed else None,
    )


@app.get("/api/scan/comparison", response_model=ComparisonResponse)
async def get_scan_comparison():
    """Return today's scan with day-over-day deltas from the previous day's scan."""
    latest = get_latest_scan()
    if not latest:
        return ComparisonResponse(current_scanned_at="", tickers=[])

    previous = get_previous_day_scan(latest["scanned_at"])
    prev_by_ticker = {}
    if previous:
        prev_by_ticker = {t["ticker"]: t for t in previous["tickers"]}

    comparisons = []
    for t in latest["tickers"]:
        ticker_sym = t["ticker"]
        # Enrich with is_etf from UNIVERSE
        if ticker_sym in UNIVERSE:
            t["is_etf"] = UNIVERSE[ticker_sym].get("etf", False)

        prev_t = prev_by_ticker.get(ticker_sym)
        if prev_t and ticker_sym in UNIVERSE:
            prev_t["is_etf"] = UNIVERSE[ticker_sym].get("etf", False)

        deltas = _compute_deltas(t, prev_t) if prev_t else None

        comparisons.append(TickerComparison(
            ticker=ticker_sym,
            current=TickerResult(**t),
            previous=TickerResult(**prev_t) if prev_t else None,
            deltas=deltas,
        ))

    return ComparisonResponse(
        current_scanned_at=latest["scanned_at"],
        previous_scanned_at=previous["scanned_at"] if previous else None,
        tickers=comparisons,
    )


@app.get("/api/credit-put-spreads/latest", response_model=CreditPutSpreadsResponse)
async def get_credit_put_spreads_latest():
    """Return the most recent cached Credit Put Spreads response.

    Built and persisted by `run_full_scan()` after the existing Naked Puts
    scoring loop. This endpoint never re-runs the builder — it just reads
    whatever the most recent scan produced. When no scan has produced a CPS
    response yet (fresh deploy, empty DB), returns an empty shell with
    `regime_overlay.status="UNKNOWN"` and a clear `message`.
    """
    cached = get_latest_cps_scan_response()
    if cached is None:
        return CreditPutSpreadsResponse(
            scan_date=datetime.utcnow().date().isoformat(),
            market_regime="UNKNOWN",
            cps_universe=list(cfg.CPS_UNIVERSE),
            regime_overlay=RegimeOverlay(
                status="UNKNOWN",
                warnings=["No scan has produced a Credit Put Spreads response yet."],
            ),
            candidates=[],
            message="No cached CPS response yet — wait for the next scan.",
            rejection_summary=CPSRejectionSummary(),
        )
    # Re-parse via Pydantic so the response matches the declared model.
    return CreditPutSpreadsResponse.model_validate(cached)


@app.get("/api/ticker/{ticker}/history")
async def ticker_history(ticker: str, days: int = Query(default=120, le=365)):
    """Get historical IV/RV series for a specific ticker."""
    ticker = ticker.upper()
    if ticker not in UNIVERSE:
        raise HTTPException(404, f"Ticker {ticker} not in universe")

    series = get_historical_series(ticker, lookback_days=days)
    return {"ticker": ticker, "history": series}


@app.get("/api/vrp-history", response_model=VrpHistoryResponse)
async def vrp_history(year: int = Query(default=None, ge=2020, le=2099)):
    """
    Daily Avg VRP across the full ticker universe for a calendar year.
    Powers the activity grid in the regime banner.
    """
    if year is None:
        year = date.today().year
    rows = get_vrp_history_by_date(f"{year}-01-01", f"{year}-12-31")
    return VrpHistoryResponse(
        year=year,
        points=[VrpHistoryPoint(**row) for row in rows],
    )


@app.get("/api/universe")
async def get_universe():
    """Return the configured ticker universe."""
    return {
        "tickers": [
            {"ticker": t, "name": m["name"], "sector": m["sector"]}
            for t, m in UNIVERSE.items()
        ]
    }


_EARNINGS_REFRESH_LIMIT = 1
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
    from zoneinfo import ZoneInfo
    et = ZoneInfo("America/New_York")
    today_et = datetime.now(tz=et).date()
    if not _is_trading_day(today_et):
        return {"earnings": {}, "remaining": _get_earnings_remaining(),
                "message": "Market is closed today"}

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
    # Only update non-None values so Yahoo-filled dates survive FMP refresh
    non_none = {k: v for k, v in results.items() if v is not None}
    if non_none:
        update_latest_scan_earnings(non_none)

    # Re-apply Yahoo overrides for >5d discrepancies from latest verification
    latest_ev = get_latest_earnings_verification()
    if latest_ev and latest_ev.get("checks"):
        yahoo_overrides = {}
        for check in latest_ev["checks"]:
            if (check["status"] == "FAIL"
                    and check.get("diff_days") is not None
                    and abs(check["diff_days"]) > 5
                    and check.get("yahoo_dte") is not None):
                yahoo_overrides[check["ticker"]] = check["yahoo_dte"]
                results[check["ticker"]] = check["yahoo_dte"]
        if yahoo_overrides:
            update_latest_scan_earnings(yahoo_overrides)
            logger.info(f"Earnings refresh: re-applied {len(yahoo_overrides)} Yahoo overrides (>5d diff): {', '.join(sorted(yahoo_overrides))}")

    return {"earnings": results, "remaining": remaining}


@app.get("/api/verify/latest")
async def get_latest_verification_endpoint():
    """Return the most recent verification result."""
    result = get_latest_verification()
    if not result:
        return {"message": "No verification results yet. Run a scan first."}
    return result


@app.get("/api/verify/earnings/latest")
async def get_latest_earnings_verification_endpoint():
    """Return the most recent earnings verification result."""
    result = get_latest_earnings_verification()
    if not result:
        return {"message": "No earnings verification results yet. Run a scan first."}
    return result


# ── Run directly ────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    logger.info(f"Starting Theta Harvest on port {port}")
    logger.info(f"Dashboard: http://localhost:3000  (Next.js frontend)")
    logger.info(f"API docs:  http://localhost:{port}/docs")
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True, reload_excludes=["data/*", "*.db"])
