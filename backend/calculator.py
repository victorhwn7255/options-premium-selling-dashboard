"""
Volatility calculations: RV, IV rank/percentile, term structure, skew, VRP.

All computations are pure functions operating on data from MarketDataClient.
"""

import math
import numpy as np
from datetime import date, datetime
from typing import Optional
from dataclasses import dataclass
from marketdata_client import DailyBar, OptionContract


# ── Output structures ───────────────────────────────────
@dataclass
class RealizedVol:
    rv10: float
    rv20: float
    rv30: float
    rv60: float
    rv_acceleration: float  # rv10 / rv30 — rising RV is dangerous

    @property
    def primary(self) -> float:
        return self.rv30


@dataclass
class ImpliedVolMetrics:
    iv_current: float        # ATM 30-day IV
    iv_rank: float           # 0-100, percentile rank vs trailing 252 days
    iv_percentile: float     # 0-100, % of days IV was below current
    iv_30d_ago: Optional[float] = None
    iv_60d_ago: Optional[float] = None


@dataclass
class TermStructurePoint:
    tenor_days: int
    tenor_label: str
    iv: float


@dataclass
class TermStructure:
    points: list[TermStructurePoint]
    slope: float             # front / back ratio (< 1 = contango, > 1 = backwardation)
    is_contango: bool
    front_iv: float
    back_iv: float


@dataclass
class SkewPoint:
    delta: float
    iv: float
    contract_type: str


@dataclass
class VolSkew:
    points: list[SkewPoint]
    skew_25d: float          # 25-delta put IV minus ATM IV
    put_skew_slope: float    # regression slope of put wing
    call_skew_slope: float


@dataclass
class VolSurface:
    ticker: str
    price: float
    rv: RealizedVol
    iv: ImpliedVolMetrics
    term_structure: TermStructure
    skew: VolSkew
    vrp: float               # IV current - RV30
    vrp_ratio: float          # IV current / RV30


# ── Realized Volatility ────────────────────────────────
def compute_realized_vol(bars: list[DailyBar]) -> RealizedVol:
    """
    Compute annualized realized volatility from daily closing prices.
    Uses close-to-close log returns.
    """
    if len(bars) < 11:
        raise ValueError(f"Need at least 11 bars for RV10, got {len(bars)}")

    closes = np.array([b.close for b in bars])
    log_returns = np.diff(np.log(closes))

    annualization = math.sqrt(252)

    def _rv(returns: np.ndarray) -> float:
        return float(np.std(returns, ddof=1) * annualization * 100)

    rv10 = _rv(log_returns[-10:])
    rv20 = _rv(log_returns[-20:]) if len(log_returns) >= 20 else rv10
    rv30 = _rv(log_returns[-30:]) if len(log_returns) >= 30 else rv20
    rv60 = _rv(log_returns[-60:]) if len(log_returns) >= 60 else rv30

    rv_accel = rv10 / rv30 if rv30 > 0 else 1.0

    return RealizedVol(
        rv10=round(rv10, 2),
        rv20=round(rv20, 2),
        rv30=round(rv30, 2),
        rv60=round(rv60, 2),
        rv_acceleration=round(rv_accel, 3),
    )


# ── ATM Implied Volatility ─────────────────────────────
def compute_atm_iv(
    contracts: list[OptionContract],
    spot_price: float,
    target_dte: int = 30,
    dte_tolerance: int = 10,
) -> Optional[float]:
    """
    Compute ATM implied volatility for a target DTE.

    Strategy: find the two nearest expirations bracketing target_dte,
    get ATM contracts at each, then interpolate IV to the target tenor.
    If only one expiration is close enough, use it directly.
    """
    today = date.today()

    # Group contracts by expiration
    by_expiry: dict[str, list[OptionContract]] = {}
    for c in contracts:
        by_expiry.setdefault(c.expiration, []).append(c)

    # Calculate DTE for each expiration
    expiry_dte = {}
    for exp_str in by_expiry:
        try:
            exp_date = datetime.strptime(exp_str, "%Y-%m-%d").date()
            dte = (exp_date - today).days
            if dte > 0:
                expiry_dte[exp_str] = dte
        except ValueError:
            continue

    if not expiry_dte:
        return None

    # Find nearest ATM IV at a given expiration
    def _atm_iv_at_expiry(exp: str) -> Optional[float]:
        chain = by_expiry[exp]
        # Filter to near-ATM (within 3% of spot)
        atm_range = spot_price * 0.03
        near_atm = [
            c for c in chain
            if abs(c.strike - spot_price) <= atm_range
            and c.implied_volatility is not None
            and c.implied_volatility > 0
        ]
        if not near_atm:
            return None

        # Average put and call IV at the strike nearest to spot
        nearest_strike = min(near_atm, key=lambda c: abs(c.strike - spot_price)).strike
        at_strike = [c for c in near_atm if c.strike == nearest_strike]

        ivs = [c.implied_volatility for c in at_strike if c.implied_volatility]
        return np.mean(ivs) * 100 if ivs else None  # Convert to percentage

    # Find the two expirations closest to target_dte
    sorted_expiries = sorted(expiry_dte.items(), key=lambda x: abs(x[1] - target_dte))

    # Try the closest expiration first
    best_exp, best_dte = sorted_expiries[0]
    if abs(best_dte - target_dte) <= dte_tolerance:
        iv = _atm_iv_at_expiry(best_exp)
        if iv is not None:
            # If we have a second expiration, interpolate
            if len(sorted_expiries) > 1:
                next_exp, next_dte = sorted_expiries[1]
                next_iv = _atm_iv_at_expiry(next_exp)
                if next_iv is not None and best_dte != next_dte:
                    # Linear interpolation to target_dte
                    weight = (target_dte - best_dte) / (next_dte - best_dte)
                    weight = max(0, min(1, weight))
                    iv = iv * (1 - weight) + next_iv * weight
            return round(iv, 2)

    # Fallback: just use the closest
    for exp, dte in sorted_expiries[:3]:
        iv = _atm_iv_at_expiry(exp)
        if iv is not None:
            return round(iv, 2)

    return None


# ── ATM Greeks ─────────────────────────────────────────
def find_atm_greeks(
    contracts: list[OptionContract],
    spot_price: float,
    target_dte: int = 30,
    dte_tolerance: int = 10,
) -> tuple[Optional[float], Optional[float]]:
    """Return (theta, vega) from the ATM option nearest to target_dte."""
    today = date.today()

    # Group contracts by expiration
    by_expiry: dict[str, list[OptionContract]] = {}
    for c in contracts:
        by_expiry.setdefault(c.expiration, []).append(c)

    # Calculate DTE for each expiration
    expiry_dte = {}
    for exp_str in by_expiry:
        try:
            exp_date = datetime.strptime(exp_str, "%Y-%m-%d").date()
            dte = (exp_date - today).days
            if dte > 0:
                expiry_dte[exp_str] = dte
        except ValueError:
            continue

    if not expiry_dte:
        return None, None

    # Find nearest expiration to target_dte
    sorted_expiries = sorted(expiry_dte.items(), key=lambda x: abs(x[1] - target_dte))
    best_exp, best_dte = sorted_expiries[0]
    if abs(best_dte - target_dte) > dte_tolerance + 15:
        return None, None

    chain = by_expiry[best_exp]
    atm_range = spot_price * 0.03
    near_atm = [
        c for c in chain
        if abs(c.strike - spot_price) <= atm_range
        and c.implied_volatility is not None
        and c.implied_volatility > 0
    ]
    if not near_atm:
        return None, None

    nearest = min(near_atm, key=lambda c: abs(c.strike - spot_price))
    return nearest.theta, nearest.vega


# ── ATR 14 ─────────────────────────────────────────────
def compute_atr14(bars: list[DailyBar]) -> Optional[float]:
    """Compute 14-period Average True Range from daily bars."""
    if len(bars) < 15:
        return None
    true_ranges = []
    for i in range(1, len(bars)):
        high = bars[i].high
        low = bars[i].low
        prev_close = bars[i - 1].close
        tr = max(high - low, abs(high - prev_close), abs(low - prev_close))
        true_ranges.append(tr)
    atr = sum(true_ranges[-14:]) / 14
    return round(atr, 2)


# ── IV Rank & Percentile ───────────────────────────────
def compute_iv_rank(
    current_iv: float,
    historical_ivs: list[float],
) -> tuple[float, float]:
    """
    IV Rank = (current - 52wk low) / (52wk high - 52wk low) * 100
    IV Percentile = % of days where IV was below current level

    historical_ivs should be ~252 trading days of daily ATM IV values.
    """
    if not historical_ivs or len(historical_ivs) < 20:
        return 50.0, 50.0  # Default when insufficient history

    iv_min = min(historical_ivs)
    iv_max = max(historical_ivs)
    iv_range = iv_max - iv_min

    if iv_range < 0.1:
        rank = 50.0
    else:
        rank = (current_iv - iv_min) / iv_range * 100

    percentile = sum(1 for iv in historical_ivs if iv < current_iv) / len(historical_ivs) * 100

    return round(max(0, min(100, rank)), 1), round(percentile, 1)


# ── Term Structure ──────────────────────────────────────
def compute_term_structure(
    contracts: list[OptionContract],
    spot_price: float,
) -> TermStructure:
    """
    Build the IV term structure from ATM options at each available expiration.
    """
    today = date.today()
    target_tenors = [
        (7, "1W"), (14, "2W"), (30, "1M"), (60, "2M"),
        (90, "3M"), (120, "4M"), (180, "6M"), (365, "1Y"),
    ]

    # Group by expiration and compute ATM IV at each
    by_expiry: dict[str, list[OptionContract]] = {}
    for c in contracts:
        by_expiry.setdefault(c.expiration, []).append(c)

    expiry_ivs = []
    atm_range = spot_price * 0.03

    for exp_str, chain in by_expiry.items():
        try:
            exp_date = datetime.strptime(exp_str, "%Y-%m-%d").date()
            dte = (exp_date - today).days
            if dte <= 0:
                continue
        except ValueError:
            continue

        near_atm = [
            c for c in chain
            if abs(c.strike - spot_price) <= atm_range
            and c.implied_volatility is not None
            and c.implied_volatility > 0
        ]
        if not near_atm:
            continue

        nearest_strike = min(near_atm, key=lambda c: abs(c.strike - spot_price)).strike
        at_strike = [c for c in near_atm if c.strike == nearest_strike]
        ivs = [c.implied_volatility * 100 for c in at_strike if c.implied_volatility]
        if ivs:
            expiry_ivs.append((dte, np.mean(ivs)))

    expiry_ivs.sort(key=lambda x: x[0])

    if len(expiry_ivs) < 2:
        # Not enough data for meaningful term structure
        return TermStructure(
            points=[], slope=1.0, is_contango=True,
            front_iv=0, back_iv=0,
        )

    # Interpolate to target tenors
    dte_arr = np.array([x[0] for x in expiry_ivs])
    iv_arr = np.array([x[1] for x in expiry_ivs])

    points = []
    for target_dte, label in target_tenors:
        if target_dte < dte_arr[0] - 5 or target_dte > dte_arr[-1] + 30:
            continue
        iv = float(np.interp(target_dte, dte_arr, iv_arr))
        points.append(TermStructurePoint(
            tenor_days=target_dte,
            tenor_label=label,
            iv=round(iv, 2),
        ))

    if len(points) < 2:
        return TermStructure(
            points=points, slope=1.0, is_contango=True,
            front_iv=points[0].iv if points else 0,
            back_iv=points[0].iv if points else 0,
        )

    front_iv = points[0].iv
    back_iv = points[-1].iv
    slope = front_iv / back_iv if back_iv > 0 else 1.0

    return TermStructure(
        points=points,
        slope=round(slope, 3),
        is_contango=slope < 1.0,
        front_iv=round(front_iv, 2),
        back_iv=round(back_iv, 2),
    )


# ── Skew ────────────────────────────────────────────────
def compute_skew(
    contracts: list[OptionContract],
    spot_price: float,
    target_dte: int = 30,
    dte_tolerance: int = 10,
) -> VolSkew:
    """
    Compute the volatility skew for the nearest-to-target expiration.
    Returns IV by delta if Greeks available, or by moneyness if not.
    """
    today = date.today()

    # Find the best expiration near target_dte
    by_expiry: dict[str, tuple[int, list[OptionContract]]] = {}
    for c in contracts:
        try:
            exp_date = datetime.strptime(c.expiration, "%Y-%m-%d").date()
            dte = (exp_date - today).days
            if dte > 0:
                if c.expiration not in by_expiry:
                    by_expiry[c.expiration] = (dte, [])
                by_expiry[c.expiration][1].append(c)
        except ValueError:
            continue

    if not by_expiry:
        return VolSkew(points=[], skew_25d=0, put_skew_slope=0, call_skew_slope=0)

    # Pick expiration nearest to target_dte
    best_exp = min(by_expiry, key=lambda k: abs(by_expiry[k][0] - target_dte))
    dte, chain = by_expiry[best_exp]

    # Separate puts and calls, filter for valid IV
    puts = [c for c in chain if c.contract_type == "put" and c.implied_volatility and c.implied_volatility > 0]
    calls = [c for c in chain if c.contract_type == "call" and c.implied_volatility and c.implied_volatility > 0]

    points = []

    # If we have Greeks (delta), use delta-space skew
    has_greeks = any(c.delta is not None for c in puts + calls)

    if has_greeks:
        for c in puts:
            if c.delta is not None and -0.9 < c.delta < -0.05:
                points.append(SkewPoint(
                    delta=round(abs(c.delta) * 100, 1),
                    iv=round(c.implied_volatility * 100, 2),
                    contract_type="put",
                ))
        for c in calls:
            if c.delta is not None and 0.05 < c.delta < 0.9:
                points.append(SkewPoint(
                    delta=round(c.delta * 100, 1),
                    iv=round(c.implied_volatility * 100, 2),
                    contract_type="call",
                ))
    else:
        # Fallback: use moneyness as a proxy for delta
        for c in puts:
            moneyness = c.strike / spot_price
            if 0.8 < moneyness < 1.0:
                pseudo_delta = round((1 - moneyness) * 100 * 2, 1)  # rough approximation
                points.append(SkewPoint(
                    delta=min(50, max(5, pseudo_delta)),
                    iv=round(c.implied_volatility * 100, 2),
                    contract_type="put",
                ))
        for c in calls:
            moneyness = c.strike / spot_price
            if 1.0 < moneyness < 1.2:
                pseudo_delta = round((1 - (moneyness - 1) * 2) * 50, 1)
                points.append(SkewPoint(
                    delta=min(50, max(5, pseudo_delta)),
                    iv=round(c.implied_volatility * 100, 2),
                    contract_type="call",
                ))

    # Compute 25-delta skew: IV of 25Δ put - ATM IV
    atm_iv = None
    put_25d_iv = None

    put_points = sorted([p for p in points if p.contract_type == "put"], key=lambda p: p.delta)
    call_points = sorted([p for p in points if p.contract_type == "call"], key=lambda p: p.delta, reverse=True)

    # ATM = ~50 delta
    all_points = put_points + call_points
    near_50 = [p for p in all_points if 40 < p.delta < 60]
    if near_50:
        atm_iv = np.mean([p.iv for p in near_50])

    # 25-delta put
    near_25_puts = [p for p in put_points if 20 < p.delta < 30]
    if near_25_puts:
        put_25d_iv = np.mean([p.iv for p in near_25_puts])

    skew_25d = round(put_25d_iv - atm_iv, 2) if (put_25d_iv and atm_iv) else 0

    # Simple slope computation
    put_slope = 0
    if len(put_points) >= 2:
        deltas = np.array([p.delta for p in put_points])
        ivs = np.array([p.iv for p in put_points])
        if len(deltas) > 1:
            coeffs = np.polyfit(deltas, ivs, 1)
            put_slope = round(coeffs[0], 4)

    call_slope = 0
    if len(call_points) >= 2:
        deltas = np.array([p.delta for p in call_points])
        ivs = np.array([p.iv for p in call_points])
        if len(deltas) > 1:
            coeffs = np.polyfit(deltas, ivs, 1)
            call_slope = round(coeffs[0], 4)

    return VolSkew(
        points=sorted(points, key=lambda p: p.delta),
        skew_25d=skew_25d,
        put_skew_slope=put_slope,
        call_skew_slope=call_slope,
    )


# ── Full Surface Builder ────────────────────────────────
def build_vol_surface(
    ticker: str,
    spot_price: float,
    bars: list[DailyBar],
    contracts: list[OptionContract],
    historical_ivs: list[float],
) -> VolSurface:
    """
    Assemble the complete volatility surface for a single underlying.
    This is the main entry point called per-ticker by the scanner.
    """
    rv = compute_realized_vol(bars)

    iv_current = compute_atm_iv(contracts, spot_price, target_dte=30)
    if iv_current is None:
        iv_current = rv.rv30  # Fallback — shouldn't happen with good data

    iv_rank, iv_pct = compute_iv_rank(iv_current, historical_ivs)

    iv_metrics = ImpliedVolMetrics(
        iv_current=iv_current,
        iv_rank=iv_rank,
        iv_percentile=iv_pct,
    )

    term_structure = compute_term_structure(contracts, spot_price)
    skew = compute_skew(contracts, spot_price)

    vrp = round(iv_current - rv.rv30, 2)
    vrp_ratio = round(iv_current / rv.rv30, 3) if rv.rv30 > 0 else 1.0

    return VolSurface(
        ticker=ticker,
        price=spot_price,
        rv=rv,
        iv=iv_metrics,
        term_structure=term_structure,
        skew=skew,
        vrp=vrp,
        vrp_ratio=vrp_ratio,
    )
