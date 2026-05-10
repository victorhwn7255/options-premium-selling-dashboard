"""
API response models (Pydantic v2).
"""

from pydantic import BaseModel
from typing import Optional


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
