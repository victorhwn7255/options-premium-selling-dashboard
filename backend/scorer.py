"""
Opportunity scoring engine for premium selling.

Produces a composite score (0-100) and regime classification for each ticker.
"""

from dataclasses import dataclass, field
from typing import Optional
from calculator import VolSurface


@dataclass
class ScoredOpportunity:
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
    regime: str            # NORMAL / CAUTION / DANGER
    recommendation: str    # SELL PREMIUM / CONDITIONAL / REDUCE SIZE / AVOID / NO EDGE
    flags: list[str] = field(default_factory=list)

    # Position construction suggestions
    suggested_delta: str = ""
    suggested_structure: str = ""
    suggested_dte: str = ""
    suggested_max_notional: str = ""

    # Additional data fields
    earnings_dte: Optional[int] = None
    theta: Optional[float] = None
    vega: Optional[float] = None
    atr14: Optional[float] = None

    # Term structure and skew data for charts
    term_structure_points: list[dict] = field(default_factory=list)
    skew_points: list[dict] = field(default_factory=list)


@dataclass
class ScoringParams:
    min_iv_rank: float = 60
    min_vrp: float = 3.0
    max_rv_accel: float = 1.15
    max_skew: float = 15.0
    only_contango: bool = True
    sectors: list[str] = field(default_factory=lambda: [
        "Index", "Tech", "Financials", "Energy", "Commodities", "Bonds",
    ])


def score_opportunity(
    surface: VolSurface,
    name: str,
    sector: str,
    params: ScoringParams,
) -> ScoredOpportunity:
    """
    Score a single ticker based on its vol surface.

    Score measures premium edge quality (0-100) with NO regime subtraction.
    Regime is a separate risk signal that drives recommendation and sizing only.

    Scoring components (all continuous, no cliffs):
    - VRP Quality (0-30): IV/RV ratio above 1.15 (dead zone below — marginal after costs)
    - IV Percentile (0-25): Floor at 30th pctile (no edge selling cheap premium)
    - Term Structure (0-20): Deep contango = 20, flat = 5, backwardation tapers to 0
    - RV Stability (0-15): Low acceleration = stable environment
    - Skew (0-10): Positive put skew = premium to harvest; 7-12 sweet spot
    """
    score = 0.0
    flags = list(surface.low_confidence_flags)  # carry forward liquidity warnings
    regime = "NORMAL"

    # ── VRP Quality (0-30) ────────────────────────────
    # Dead zone below 1.15 — a 10% edge is marginal after costs
    # Maps: 1.15→0, 1.60→30. Below 1.15 → 0.
    vrp_score = min(30, max(0, (surface.vrp_ratio - 1.15) * (30.0 / 0.45)))
    score += vrp_score

    if surface.vrp < 0:
        flags.append("Negative VRP — implied vol is BELOW realized. No premium edge.")

    # ── IV Percentile (0-25) ──────────────────────────
    # Floor at 30th percentile — no edge selling cheap premium
    # Maps: 30→0, 100→25. Below 30 → 0.
    iv_pct_score = max(0, (surface.iv.iv_percentile - 30) * (25.0 / 70.0))
    score += iv_pct_score

    # ── Term Structure (0-20) ─────────────────────────
    ts = surface.term_structure
    if ts.slope <= 0.85:
        term_score = 20.0
    elif ts.slope >= 1.15:
        term_score = 0.0
    elif ts.slope <= 1.0:
        # Linear: 20 at 0.85 → 5 at 1.0 (flat is neutral, not half-positive)
        term_score = 5.0 + (1.0 - ts.slope) / 0.15 * 15.0
    else:
        # Linear: 5 at 1.0 → 0 at 1.15
        term_score = 5.0 * (1.15 - ts.slope) / 0.15
    score += term_score

    if ts.slope > 1.0:
        flags.append("Term structure in backwardation — stress signal")

    # ── RV Stability (0-15) ──────────────────────────
    rv_accel = surface.rv.rv_acceleration
    if rv_accel <= 0.85:
        rv_score = 15.0
    elif rv_accel >= 1.15:
        rv_score = 0.0
    elif rv_accel <= 1.0:
        # Linear: 15 at 0.85 → 10 at 1.0
        rv_score = 10.0 + (1.0 - rv_accel) / 0.15 * 5.0
    else:
        # Linear: 10 at 1.0 → 0 at 1.15
        rv_score = 10.0 * (1.15 - rv_accel) / 0.15
    score += rv_score

    if rv_accel > 1.1:
        flags.append("RV accelerating — realized vol rising faster than implied")

    # ── Skew Assessment (0-10) ────────────────────────
    # Positive skew (puts > ATM) is the premium to harvest.
    # Negative skew is abnormal and scores 0.
    skew = surface.skew.skew_25d
    if skew < 0:
        skew_score = 0.0
        flags.append("Inverted skew — puts cheaper than ATM, unusual")
    elif skew <= 7:
        skew_score = skew / 7.0 * 10.0        # Linear: 0 at 0, 10 at 7
    elif skew <= 12:
        skew_score = 10.0                      # Sweet spot
    elif skew <= 20:
        skew_score = 10.0 * (20.0 - skew) / 8.0  # Taper: 10 at 12, 0 at 20
    else:
        skew_score = 0.0
    score += skew_score

    if skew > 15:
        flags.append("Extreme skew — may reflect informed protection buying")

    # ── Regime Detection (separate from score) ────────
    if ts.slope > 1.15:
        regime = "DANGER"
        flags.insert(0, "Deep backwardation — regime change likely. Do NOT sell premium.")
    elif ts.slope > 1.05:
        regime = "CAUTION"
        flags.insert(0, "Backwardation detected — reduce size, use defined-risk only")

    if surface.iv.iv_rank > 90 and rv_accel > 1.1:
        if regime != "DANGER":
            regime = "CAUTION"
        flags.append("Extreme IV + rising RV — potential regime shift, not just fear")

    # ── Clamp score ───────────────────────────────────
    score = max(0, min(100, int(score)))

    # ── Recommendation (combines score + regime) ──────
    if regime == "DANGER":
        rec = "AVOID"
    elif regime == "CAUTION":
        rec = "REDUCE SIZE" if score >= 55 else "NO EDGE"
    elif score >= 65:
        rec = "SELL PREMIUM"
    elif score >= 45:
        rec = "CONDITIONAL"
    else:
        rec = "NO EDGE"

    # ── Position Construction ─────────────────────────
    if regime == "DANGER":
        delta = "N/A"
        structure = "No position recommended"
        dte = "N/A"
        notional = "0%"
    elif regime == "CAUTION":
        delta = "10–15Δ"
        structure = "Iron condor or wide put spread (defined risk only)"
        dte = "21–30 DTE"
        notional = "1–2% portfolio"
    elif surface.iv.iv_rank >= 80:
        delta = "16–20Δ"
        dte = "30–45 DTE"
        notional = "2–5% portfolio"
        if surface.vrp > 8:
            structure = "Short strangle or jade lizard if directional"
        elif surface.vrp > 4:
            structure = "Iron condor or put credit spread"
        else:
            structure = "Put credit spread with strict width limits"
    else:
        delta = "20–30Δ"
        structure = "Put credit spread, narrow width"
        dte = "45–60 DTE"
        notional = "2–3% portfolio"

    # ── Build chart data ──────────────────────────────
    ts_points = [
        {"tenor_label": p.tenor_label, "tenor_days": p.tenor_days, "iv": p.iv}
        for p in surface.term_structure.points
    ]

    skew_points = [
        {"delta": p.delta, "iv": p.iv, "type": p.contract_type}
        for p in surface.skew.points
    ]

    return ScoredOpportunity(
        ticker=surface.ticker,
        name=name,
        sector=sector,
        price=round(surface.price, 2),
        iv_current=surface.iv.iv_current,
        iv_rank=surface.iv.iv_rank,
        iv_percentile=surface.iv.iv_percentile,
        rv10=surface.rv.rv10,
        rv20=surface.rv.rv20,
        rv30=surface.rv.rv30,
        vrp=surface.vrp,
        vrp_ratio=surface.vrp_ratio,
        rv_acceleration=surface.rv.rv_acceleration,
        term_slope=surface.term_structure.slope,
        is_contango=surface.term_structure.is_contango,
        skew_25d=surface.skew.skew_25d,
        signal_score=score,
        regime=regime,
        recommendation=rec,
        flags=flags,
        suggested_delta=delta,
        suggested_structure=structure,
        suggested_dte=dte,
        suggested_max_notional=notional,
        term_structure_points=ts_points,
        skew_points=skew_points,
    )
