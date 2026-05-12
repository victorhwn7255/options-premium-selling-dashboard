"""
API response models (Pydantic v2).
"""

from pydantic import BaseModel
from typing import Literal, Optional


class TermStructurePointOut(BaseModel):
    tenor_label: str
    tenor_days: int
    iv: float


class SkewPointOut(BaseModel):
    delta: float
    iv: float
    type: str


class TickerResult(BaseModel):
    ticker: str
    name: str
    sector: str
    price: float
    iv_current: Optional[float]
    iv_rank: float
    iv_percentile: float
    rv10: float
    rv20: float
    rv30: float
    vrp: Optional[float]
    vrp_ratio: Optional[float]
    rv_acceleration: float
    term_slope: float
    is_contango: bool
    skew_25d: float
    signal_score: int
    regime: str
    recommendation: str
    flags: list[str]
    suggested_delta: str
    suggested_structure: str
    suggested_dte: str
    suggested_max_notional: str
    earnings_dte: Optional[int] = None
    is_etf: bool = False
    theta: Optional[float] = None
    vega: Optional[float] = None
    atr14: Optional[float] = None
    term_structure_points: list[TermStructurePointOut] = []
    skew_points: list[SkewPointOut] = []
    # ── Scan-quality suppression audit (QA Phase 1 diagnostics) ──
    # When DEGRADED scan suppression downgrades SELL/CONDITIONAL/WATCHLIST → NO EDGE,
    # the original recommendation/score are preserved here so the frontend can
    # render an audit note. signal_score itself is *not* zeroed by suppression
    # (pre_suppression_score is a redundant explicit copy for clarity).
    suppressed_by_scan_quality: bool = False
    pre_suppression_recommendation: Optional[str] = None
    pre_suppression_score: Optional[int] = None
    scan_quality_suppression_reason: Optional[str] = None


class RegimeSummary(BaseModel):
    overall_regime: str
    regime_color: str
    description: str
    avg_iv_rank: float
    avg_rv_accel: float
    danger_count: int
    caution_count: int
    total_tickers: int
    vix_term_slope: Optional[float] = None


class HistoricalPoint(BaseModel):
    date: str
    iv: Optional[float] = None
    rv: Optional[float] = None
    vrp: Optional[float] = None
    term_slope: Optional[float] = None


class ScanResponse(BaseModel):
    timestamp: str
    regime: Optional[RegimeSummary] = None
    tickers: list[TickerResult]
    historical: dict[str, list[HistoricalPoint]] = {}
    scanned_at: Optional[str] = None
    cached: bool = False
    message: Optional[str] = None
    # Scan-quality detection (QA Phase 1, see references/dashboard-behavior-qa-report.md §5.6)
    # "OK" or "DEGRADED". When DEGRADED, actionable recommendations are suppressed
    # and the frontend renders a prominent banner.
    scan_quality: str = "OK"
    scan_quality_reason: Optional[str] = None



class TickerDelta(BaseModel):
    score: Optional[int] = None
    iv: Optional[float] = None
    iv_percentile: Optional[float] = None
    rv30: Optional[float] = None
    vrp: Optional[float] = None
    term_slope: Optional[float] = None
    rv_acceleration: Optional[float] = None
    skew_25d: Optional[float] = None
    regime_changed: bool = False
    previous_regime: Optional[str] = None


class TickerComparison(BaseModel):
    ticker: str
    current: TickerResult
    previous: Optional[TickerResult] = None
    deltas: Optional[TickerDelta] = None


class ComparisonResponse(BaseModel):
    current_scanned_at: str
    previous_scanned_at: Optional[str] = None
    tickers: list[TickerComparison]


class HealthResponse(BaseModel):
    status: str
    marketdata_connected: bool
    db_initialized: bool
    tickers_configured: int
    historical_data_points: int


class VrpHistoryPoint(BaseModel):
    date: str
    avg_vrp: float
    ticker_count: int


class VrpHistoryResponse(BaseModel):
    year: int
    points: list[VrpHistoryPoint]


# ════════════════════════════════════════════════════════════════════════
# Credit Put Spreads (Phase 1 — additive, no impact on existing models)
#
# See references/credit-put-spreads.md and
# references/credit_put_spreads_build_plan.md for the build spec.
# CPS is a defined-risk expression of the SAME volatility edge as Naked Puts;
# the existing scorer.py / calculator.py engines are untouched. CPS candidates
# are ranked by Base Edge Score AFTER passing binary construction + execution
# filters — there is no separate CPS scoring formula.
# ════════════════════════════════════════════════════════════════════════

CreditPutSpreadAction = Literal[
    "SELL_CPS",
    "WATCH_CPS",
    "WAIT",
    "AVOID",
    "NO_EDGE",
    "NO_DATA",
]

# UNKNOWN is explicit per Phase-1 clarification: when VIX / VIX3M / VVIX
# cannot be fetched (yfinance failure, weekend, etc.) the overlay returns
# UNKNOWN + warning, but candidates are NOT blocked. NORMAL / CAUTION / DANGER
# are the data-present cases.
RegimeOverlayStatus = Literal["NORMAL", "CAUTION", "DANGER", "UNKNOWN"]


class CreditPutSpreadLeg(BaseModel):
    """One leg of a credit put spread (short or long put)."""
    strike: float
    expiration: str
    dte: int
    delta: Optional[float] = None
    bid: float
    ask: float
    mid: float
    iv: Optional[float] = None
    theta: Optional[float] = None
    vega: Optional[float] = None
    open_interest: Optional[int] = None
    volume: Optional[int] = None
    # Note: bid_ask_ratio, NOT spread_ratio — avoids ambiguity with put-spread
    # width, credit spread, term spread, vol spread (see build plan §1.2).
    # bid_ask_ratio = (ask - bid) / mid
    bid_ask_ratio: Optional[float] = None


class RegimeOverlay(BaseModel):
    """Market-wide volatility regime overlay (VIX / VIX3M / VVIX).

    UNKNOWN status means data could not be fetched; this surfaces a warning
    but does NOT block CPS candidates. NORMAL / CAUTION / DANGER are the
    data-present cases — DANGER prevents new SELL_CPS entries.
    """
    status: RegimeOverlayStatus = "UNKNOWN"
    vix: Optional[float] = None
    vix3m: Optional[float] = None
    vvix: Optional[float] = None
    # True if VIX > VIX3M (front backwardation in the vol curve).
    vix_backwardation: Optional[bool] = None
    warnings: list[str] = []


class CreditPutSpreadCandidate(BaseModel):
    """A single CPS candidate (one short/long pair on one underlying)."""
    ticker: str
    spot: float

    action: CreditPutSpreadAction
    # Base Edge Score from the existing scoring engine (unchanged).
    base_score: float
    # rank_score == base_score in MVP; reserved field so future tie-breakers
    # (credit/width, bid/ask quality, RV Accel status, term slope) can stamp
    # a derived rank without changing the underlying score.
    rank_score: float
    regime: str  # Per-ticker regime from scorer.py (NORMAL / CAUTION / DANGER)

    expiration: str
    dte: int

    short_put: CreditPutSpreadLeg
    long_put: CreditPutSpreadLeg

    # Per-share economics (build plan §1.5 — multiply by 100 for per-contract).
    width: float
    net_credit: float
    max_loss: float
    credit_to_width: float
    breakeven: float

    # Width-selection context
    atr14: Optional[float] = None
    expected_move: Optional[float] = None
    expected_move_lower: Optional[float] = None
    width_to_atr: Optional[float] = None
    width_to_expected_move: Optional[float] = None

    # Base edge context (copied from the underlying's TickerResult)
    vrp: Optional[float] = None
    vrp_ratio: Optional[float] = None
    vrp_zscore_60d: Optional[float] = None
    iv_percentile: Optional[float] = None
    term_slope: Optional[float] = None
    rv_accel: Optional[float] = None
    rv_accel_status: Optional[str] = None
    skew: Optional[float] = None
    earnings_dte: Optional[int] = None

    # Multi-day confirmation (Phase 1 clarification §5):
    #   - consecutive_sell_days: ticker-level eligibility streak (the SELL_CPS gate)
    #   - exact_spread_consecutive_days: same-strike-pair streak (display-only context)
    # Track ticker-level because strikes shift day-to-day with the chain.
    consecutive_sell_days: int = 0
    exact_spread_consecutive_days: int = 0

    # Market-wide overlay (shared across candidates in a response, copied here
    # for self-contained per-row reasoning).
    vix: Optional[float] = None
    vix3m: Optional[float] = None
    vvix: Optional[float] = None
    regime_overlay_status: Optional[RegimeOverlayStatus] = None

    notes: list[str] = []
    warnings: list[str] = []
    rejection_reasons: list[str] = []


class CPSRejectionSummary(BaseModel):
    """Lightweight diagnostic counters — explains why the candidate list
    is empty without dumping every per-ticker outcome.

    Counts are non-overlapping at the *primary reason* level: each ticker
    in the CPS universe contributes to exactly one bucket per scan.
    """
    checked: int = 0                       # tickers in CPS_UNIVERSE evaluated
    actionable: int = 0                    # SELL_CPS / WATCH_CPS / WAIT
    rejected_by_base_gate: int = 0         # AVOID / NO_EDGE from inherited gates
    rejected_by_construction: int = 0      # NO_DATA from DTE / delta / long-leg
    rejected_by_execution: int = 0         # NO_DATA from bid/ask / OI / volume
    rejected_by_overlay: int = 0           # DANGER overlay blocked SELL_CPS
    rejected_by_confirmation: int = 0      # All filters pass but consec_sell_days < 2


class CreditPutSpreadsResponse(BaseModel):
    """Response shape for GET /api/credit-put-spreads/latest."""
    scan_date: str
    market_regime: str
    cps_universe: list[str]
    regime_overlay: RegimeOverlay
    candidates: list[CreditPutSpreadCandidate]
    # Optional human-readable message for empty / degraded states.
    message: Optional[str] = None
    # Per-scan diagnostic counters. Optional so old cached responses still parse.
    rejection_summary: Optional[CPSRejectionSummary] = None


# Exit-evaluator action enum (Phase 2 spread_exit_evaluator.py will use this).
# Declared in Phase 1 so the frontend can render exit-state badges without
# waiting on the evaluator implementation.
SpreadExitActionLiteral = Literal[
    "HOLD",
    "CLOSE_PROFIT_TARGET",
    "CLOSE_DEFENSIVE",
    "CLOSE_TIME",
    "CLOSE_PIN_RISK",
    "CLOSE_EVENT_RISK",
]


class SpreadExitDecision(BaseModel):
    """One management decision on an open CPS position (Phase 2 evaluator)."""
    action: SpreadExitActionLiteral
    reason: str
    # Optional per-decision context (current mark, DTE remaining, etc.).
    notes: list[str] = []
