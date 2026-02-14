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

    Scoring components:
    - VRP (0-25): IV/RV ratio above 1.0
    - IV Rank (0-25): Higher = richer premiums
    - Term Structure (0-20, -5 penalty): Contango good, backwardation bad
    - RV Acceleration (0 to -15): Rising RV is a warning
    - Skew (0-10): Moderate skew = well-compensated tail premium

    Regime overrides can subtract 20-35 additional points.
    """
    score = 0
    flags = []
    regime = "NORMAL"

    # ── VRP Score (0-25) ──────────────────────────────
    vrp_score = min(25, max(0, (surface.vrp_ratio - 1) * 30))
    score += vrp_score

    if surface.vrp < 0:
        flags.append("Negative VRP — implied vol is BELOW realized. No premium edge.")
    elif surface.vrp < params.min_vrp:
        flags.append(f"VRP {surface.vrp:.1f} below minimum threshold {params.min_vrp}")
        score -= 10

    # ── IV Rank Score (0-25) ──────────────────────────
    iv_rank_score = min(25, surface.iv.iv_rank * 0.3)
    score += iv_rank_score

    if surface.iv.iv_rank < params.min_iv_rank:
        flags.append(f"IV Rank {surface.iv.iv_rank:.0f} below minimum {params.min_iv_rank}")
        score -= 10

    # ── Term Structure Score (0-20, -5 penalty) ───────
    ts = surface.term_structure
    if ts.slope < 0.85:
        term_score = 18
    elif ts.slope < 0.95:
        term_score = 12
    elif ts.slope < 1.0:
        term_score = 6
    else:
        term_score = -5
        flags.append("⚠ Term structure in backwardation — acute stress signal")
    score += max(0, term_score)

    # ── RV Acceleration (0 to -15) ────────────────────
    rv_accel = surface.rv.rv_acceleration
    if rv_accel > 1.15:
        score -= 15
        flags.append("RV accelerating — realized vol rising faster than implied")
    elif rv_accel > 1.05:
        score -= 8
        flags.append("RV slightly elevated vs 30-day average")

    if rv_accel > params.max_rv_accel:
        flags.append(f"RV acceleration {rv_accel:.2f} exceeds threshold {params.max_rv_accel}")

    # ── Skew Assessment (0-10) ────────────────────────
    skew = abs(surface.skew.skew_25d)
    if skew > 10:
        score += 5
        flags.append("Steep skew — tail premium is rich, but may reflect informed protection buying")
    elif skew > 7:
        score += 8
    elif skew > 4:
        score += 6
    else:
        score += 3

    if skew > params.max_skew:
        flags.append(f"Skew {skew:.1f} exceeds threshold {params.max_skew} — extreme fear pricing")

    # ── Regime Detection ──────────────────────────────
    if ts.slope > 1.05:
        regime = "DANGER"
        flags.insert(0, "🚫 Deep backwardation — regime change likely. Do NOT sell premium.")
        score -= 35
    elif ts.slope > 1.0:
        regime = "CAUTION"
        flags.insert(0, "⚠ Backwardation detected — reduce size, use defined-risk only")
        score -= 20

    if surface.iv.iv_rank > 90 and rv_accel > 1.1:
        if regime != "DANGER":
            regime = "CAUTION"
        flags.append("⚠ Extreme IV + rising RV — potential regime shift, not just fear")

    # ── Clamp score ───────────────────────────────────
    score = max(0, min(100, int(score)))

    # ── Recommendation ────────────────────────────────
    if score >= 70 and regime == "NORMAL":
        rec = "SELL PREMIUM"
    elif score >= 55 and regime == "NORMAL":
        rec = "CONDITIONAL"
    elif regime == "DANGER":
        rec = "AVOID"
    elif regime == "CAUTION":
        rec = "REDUCE SIZE"
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
