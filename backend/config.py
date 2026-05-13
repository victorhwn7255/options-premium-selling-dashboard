"""
Centralized configuration constants.

Owns the ticker universes (Naked Puts + Credit Put Spreads) and all
CPS-specific tuning knobs. Imported by main.py, backfill.py, repair_rv.py,
spread_builder.py, and (later) regime_overlay.py.
"""

from typing import Final


# ────────────────────────────────────────────────────────────────────────
# Naked Puts universe — 33 tickers, the existing daily-scan set.
# Moved out of backend/main.py during Phase 1 of the Credit Put Spreads build
# so both universes have a single source of truth.
# ────────────────────────────────────────────────────────────────────────
NAKED_PUT_UNIVERSE: Final[dict[str, dict]] = {
    # ETFs
    "SPY":  {"name": "S&P 500 ETF",            "sector": "Index",        "etf": True},
    "QQQ":  {"name": "Nasdaq 100 ETF",          "sector": "Index",        "etf": True},
    "IWM":  {"name": "Russell 2000 ETF",         "sector": "Index",        "etf": True},
    "EEM":  {"name": "Emerging Markets ETF",     "sector": "Index",        "etf": True},
    "GLD":  {"name": "SPDR Gold Trust",          "sector": "Commodities",  "etf": True},
    "TLT":  {"name": "20+ Year Treasury ETF",    "sector": "Fixed Income", "etf": True},
    "XLE":  {"name": "Energy Select SPDR",       "sector": "Sector ETF",   "etf": True},
    "XLF":  {"name": "Financial Select SPDR",    "sector": "Sector ETF",   "etf": True},
    "XLV":  {"name": "Health Care Select SPDR",  "sector": "Sector ETF",   "etf": True},
    "XLI":  {"name": "Industrial Select SPDR",   "sector": "Sector ETF",   "etf": True},
    "XLB":  {"name": "Materials Select SPDR",    "sector": "Sector ETF",   "etf": True},
    # Stocks
    "AAPL": {"name": "Apple",                    "sector": "Tech"},
    "MSFT": {"name": "Microsoft",                "sector": "Tech"},
    "GOOG": {"name": "Alphabet",                 "sector": "Tech"},
    "AMZN": {"name": "Amazon",                   "sector": "Consumer"},
    "META": {"name": "Meta Platforms",            "sector": "Tech"},
    "NVDA": {"name": "NVIDIA",                   "sector": "Tech"},
    "TSLA": {"name": "Tesla",                    "sector": "Consumer"},
    "NFLX": {"name": "Netflix",                  "sector": "Consumer"},
    "PLTR": {"name": "Palantir",                 "sector": "Tech"},
    "HOOD": {"name": "Robinhood Markets",        "sector": "Financials"},
    "GS":   {"name": "Goldman Sachs",            "sector": "Financials"},
    "JPM":  {"name": "JPMorgan Chase",           "sector": "Financials"},
    "XOM":  {"name": "Exxon Mobil",              "sector": "Energy"},
    "WMT":  {"name": "Walmart",                  "sector": "Consumer"},
    "MCD":  {"name": "McDonald's",               "sector": "Consumer"},
    "KO":   {"name": "Coca-Cola",                "sector": "Consumer"},
    "CAT":  {"name": "Caterpillar",              "sector": "Industrials"},
    "UBER": {"name": "Uber Technologies",        "sector": "Tech"},
    "JNJ":  {"name": "Johnson & Johnson",        "sector": "Healthcare"},
    "SBUX": {"name": "Starbucks",                "sector": "Consumer"},
    "NKE":  {"name": "Nike",                     "sector": "Consumer"},
    "HD":   {"name": "Home Depot",               "sector": "Consumer"},
}


# ────────────────────────────────────────────────────────────────────────
# Credit Put Spreads — MVP universe (index ETFs only).
# Both legs must be tradable, so MVP requires deep options chains and dense
# strike grids. Expansion to extended universe is a Phase-6 decision after
# replay confirms candidate quality.
# ────────────────────────────────────────────────────────────────────────
CPS_UNIVERSE: Final[list[str]] = ["SPY", "QQQ", "IWM"]

CPS_UNIVERSE_EXTENDED: Final[list[str]] = ["SPY", "QQQ", "IWM", "EEM", "TLT", "XLE"]


# ────────────────────────────────────────────────────────────────────────
# CPS construction targets
# ────────────────────────────────────────────────────────────────────────
CPS_TARGET_DTE: Final[int] = 35
CPS_MIN_DTE: Final[int] = 30
CPS_MAX_DTE: Final[int] = 45

CPS_TARGET_SHORT_DELTA: Final[float] = 0.20
CPS_MIN_SHORT_DELTA: Final[float] = 0.15
CPS_MAX_SHORT_DELTA: Final[float] = 0.25


# ────────────────────────────────────────────────────────────────────────
# CPS economics thresholds
# ────────────────────────────────────────────────────────────────────────
CPS_MIN_CREDIT_TO_WIDTH: Final[float] = 0.25         # SELL_CPS gate
CPS_WATCH_MIN_CREDIT_TO_WIDTH: Final[float] = 0.20   # WATCH_CPS gate
CPS_HIGH_CREDIT_TO_WIDTH_WARNING: Final[float] = 0.35  # Tail-risk warning above this

# Width selection: ATR-scaled hybrid target.
# target_width = max(nearest_valid_strike_width, CPS_WIDTH_ATR_MULTIPLIER × ATR14)
CPS_WIDTH_ATR_MULTIPLIER: Final[float] = 0.75
CPS_MIN_WIDTH_ATR_RATIO: Final[float] = 0.75
CPS_MAX_WIDTH_ATR_RATIO: Final[float] = 1.50


# ────────────────────────────────────────────────────────────────────────
# CPS execution (per leg) — both legs must pass
# ────────────────────────────────────────────────────────────────────────
CPS_MAX_BID_ASK_RATIO: Final[float] = 0.20            # Hard reject above this
CPS_PREFERRED_BID_ASK_RATIO: Final[float] = 0.15      # Preferred quality threshold

CPS_MIN_OPEN_INTEREST: Final[int] = 100
CPS_PREFERRED_OPEN_INTEREST: Final[int] = 500

CPS_MIN_VOLUME: Final[int] = 25
CPS_PREFERRED_VOLUME: Final[int] = 100

# Minimum number of band-eligible (delta ∈ [CPS_MIN_SHORT_DELTA, CPS_MAX_SHORT_DELTA])
# puts an expiration must offer to be preferred by select_cps_expiration.
# Prevents the builder from picking an expiration that only has the narrow
# 12-strike ATM cluster (no 0.20-delta strike available).
CPS_MIN_COVERAGE_PUTS: Final[int] = 3


# ────────────────────────────────────────────────────────────────────────
# Multi-day confirmation
# ────────────────────────────────────────────────────────────────────────
# Ticker-level (gating) — SELL_CPS requires this many consecutive scan days
# where the ticker passed all CPS filters. Tracks ticker, not exact spread,
# because strikes shift day-to-day with the chain.
CPS_SELL_CONFIRMATION_DAYS: Final[int] = 2


# ────────────────────────────────────────────────────────────────────────
# Pin-risk rule (Phase 2 spread_exit_evaluator.py)
# ────────────────────────────────────────────────────────────────────────
# pin_threshold = max(CPS_PIN_RISK_MIN_DISTANCE, CPS_PIN_RISK_SPOT_PCT × spot)
CPS_PIN_RISK_DTE: Final[int] = 2
CPS_PIN_RISK_MIN_DISTANCE: Final[float] = 0.50
CPS_PIN_RISK_SPOT_PCT: Final[float] = 0.001
CPS_TIME_EXIT_DTE: Final[int] = 21
CPS_PROFIT_TARGET_FRAC: Final[float] = 0.50          # Close at ≤ 50% of original credit
CPS_DEFENSIVE_MARK_MULTIPLE: Final[float] = 2.0      # Close when mark ≥ 2× original credit
CPS_EVENT_RISK_DTE: Final[int] = 14                  # Earnings within this many days


# ────────────────────────────────────────────────────────────────────────
# Inherited base gates (mirrors backend/scorer.py — display only,
# logic lives in scorer.py / scoring.ts and is NOT redefined here).
# These constants are referenced by spread_builder.py for hard-gate
# rejection of CPS candidates.
# ────────────────────────────────────────────────────────────────────────
CPS_EARNINGS_GATE_DTE: Final[int] = 14
CPS_DANGER_SLOPE: Final[float] = 1.15
CPS_MIN_VRP_RATIO: Final[float] = 1.15
CPS_RV_ACCEL_WAIT: Final[float] = 1.20
CPS_RV_ACCEL_PREFERRED: Final[float] = 1.10
CPS_EXTREME_SKEW: Final[float] = 20.0


# ────────────────────────────────────────────────────────────────────────
# Regime overlay — VIX / VIX3M / VVIX bands (Phase 2 regime_overlay.py)
# ────────────────────────────────────────────────────────────────────────
VVIX_CAUTION: Final[float] = 110.0
VVIX_DANGER: Final[float] = 130.0
# VIX/VIX3M backwardation triggers caution when VIX > VIX3M.
# 60-day VRP z-score floor for SELL_CPS eligibility (downgrade to WATCH below).
CPS_VRP_ZSCORE_60D_MIN: Final[float] = 0.5
