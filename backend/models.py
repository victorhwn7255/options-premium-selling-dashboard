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
    iv_current: float
    iv_rank: float
    iv_percentile: float
    rv10: float
    rv20: float
    rv30: float
    vrp: float
    vrp_ratio: float
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



class HealthResponse(BaseModel):
    status: str
    marketdata_connected: bool
    db_initialized: bool
    tickers_configured: int
    historical_data_points: int
