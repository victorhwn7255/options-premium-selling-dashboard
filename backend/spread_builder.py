"""
Credit Put Spreads — candidate builder.

Builds Credit Put Spread candidates from existing scan results and the
existing options-chain fetch.

Architectural rules (see references/credit-put-spreads.md):

  • Filter first, rank second. No 60/30/10 weighting.
  • Inherit the Naked Puts base hard gates (earnings, DANGER, negative VRP,
    weak VRP ratio, RV shock, extreme skew, NO_DATA).
  • Universe filter is applied FIRST so non-CPS tickers cost zero work.
  • Construction filters (DTE / delta / width / credit-to-width) are binary.
  • Execution filters (bid_ask_ratio / OI / volume) are binary, per leg.
  • Ranking happens upstream (orchestrator) — this module only constructs
    one best candidate per ticker.

This module does NOT modify scorer.py or calculator.py. It consumes the
TickerResult produced by those engines untouched.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Iterable, Optional

import config as cfg
from marketdata_client import OptionContract
from models import (
    CreditPutSpreadAction,
    CreditPutSpreadCandidate,
    CreditPutSpreadLeg,
    RegimeOverlay,
    RegimeOverlayStatus,
)


# ────────────────────────────────────────────────────────────────────────
# Result wrapper — exposes rejection reasons for tests/diagnostics.
# Production API returns just the candidate; tests use the full outcome.
# ────────────────────────────────────────────────────────────────────────
@dataclass
class CPSBuildOutcome:
    """Per-ticker CPS build result."""
    ticker: str
    action: CreditPutSpreadAction
    candidate: Optional[CreditPutSpreadCandidate] = None
    rejection_reasons: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


# ────────────────────────────────────────────────────────────────────────
# Small math helpers
# ────────────────────────────────────────────────────────────────────────

def compute_expected_move(spot: float, iv_pct: float, dte: int) -> float:
    """Annualised-IV expected-move approximation (one standard deviation)."""
    if spot <= 0 or iv_pct <= 0 or dte <= 0:
        return 0.0
    return spot * (iv_pct / 100.0) * math.sqrt(dte / 365.0)


def compute_bid_ask_ratio(bid: Optional[float], ask: Optional[float]) -> Optional[float]:
    """bid_ask_ratio = (ask - bid) / mid. None if bid/ask invalid."""
    if bid is None or ask is None:
        return None
    if bid <= 0 or ask <= 0 or ask <= bid:
        return None
    mid = (bid + ask) / 2.0
    if mid <= 0:
        return None
    return (ask - bid) / mid


def compute_vrp_zscore(history: Iterable[float], current: float) -> Optional[float]:
    """60-day rolling z-score of VRP. None if too few points."""
    series = [v for v in history if v is not None]
    if len(series) < 20:  # Demand at least 20 points (~ 1 trading month)
        return None
    mean = sum(series) / len(series)
    var = sum((v - mean) ** 2 for v in series) / len(series)
    std = math.sqrt(var)
    if std == 0:
        return None
    return (current - mean) / std


def parse_dte(expiration: str, asof: Optional[date] = None) -> int:
    """Days-to-expiry from ISO YYYY-MM-DD, relative to asof (default today)."""
    if asof is None:
        asof = date.today()
    exp = datetime.fromisoformat(expiration).date()
    return (exp - asof).days


# ────────────────────────────────────────────────────────────────────────
# Leg-level construction
# ────────────────────────────────────────────────────────────────────────

def _make_leg(c: OptionContract, dte: int) -> CreditPutSpreadLeg:
    """Construct a CreditPutSpreadLeg view of an OptionContract."""
    bid = float(c.bid or 0.0)
    ask = float(c.ask or 0.0)
    mid = (bid + ask) / 2.0 if (bid > 0 and ask > 0) else 0.0
    return CreditPutSpreadLeg(
        strike=c.strike,
        expiration=c.expiration,
        dte=dte,
        delta=c.delta,
        bid=bid,
        ask=ask,
        mid=mid,
        iv=c.implied_volatility,
        theta=c.theta,
        vega=c.vega,
        open_interest=c.open_interest or 0,
        volume=c.volume or 0,
        bid_ask_ratio=compute_bid_ask_ratio(c.bid, c.ask),
    )


def passes_execution_filter(leg: CreditPutSpreadLeg) -> tuple[bool, list[str]]:
    """Hard execution filter — both legs of a SELL_CPS must pass."""
    reasons: list[str] = []
    if leg.bid <= 0:
        reasons.append(f"strike {leg.strike}: bid <= 0")
    if leg.ask <= 0 or leg.ask <= leg.bid:
        reasons.append(f"strike {leg.strike}: ask invalid (<= bid)")
    if leg.bid_ask_ratio is None or leg.bid_ask_ratio > cfg.CPS_MAX_BID_ASK_RATIO:
        reasons.append(
            f"strike {leg.strike}: bid_ask_ratio "
            f"{leg.bid_ask_ratio:.3f} > {cfg.CPS_MAX_BID_ASK_RATIO:.2f}"
            if leg.bid_ask_ratio is not None
            else f"strike {leg.strike}: bid_ask_ratio unavailable"
        )
    if (leg.open_interest or 0) < cfg.CPS_MIN_OPEN_INTEREST:
        reasons.append(
            f"strike {leg.strike}: OI {leg.open_interest} < {cfg.CPS_MIN_OPEN_INTEREST}"
        )
    if (leg.volume or 0) < cfg.CPS_MIN_VOLUME:
        reasons.append(
            f"strike {leg.strike}: volume {leg.volume} < {cfg.CPS_MIN_VOLUME}"
        )
    return (len(reasons) == 0, reasons)


# ────────────────────────────────────────────────────────────────────────
# Expiration / short / long selection
# ────────────────────────────────────────────────────────────────────────

def select_cps_expiration(
    chain: Iterable[OptionContract],
    asof: Optional[date] = None,
    target_dte: int = cfg.CPS_TARGET_DTE,
    min_dte: int = cfg.CPS_MIN_DTE,
    max_dte: int = cfg.CPS_MAX_DTE,
) -> Optional[tuple[str, int]]:
    """Pick the expiration in [min_dte, max_dte] closest to target_dte.

    Returns (expiration_iso, dte) or None.
    """
    if asof is None:
        asof = date.today()
    seen: dict[str, int] = {}
    for c in chain:
        if c.expiration in seen:
            continue
        try:
            dte = parse_dte(c.expiration, asof)
        except (ValueError, TypeError):
            continue
        if min_dte <= dte <= max_dte:
            seen[c.expiration] = dte
    if not seen:
        return None
    best = min(seen.items(), key=lambda kv: abs(kv[1] - target_dte))
    return best


def select_short_put(
    puts: Iterable[OptionContract],
    target_delta: float = cfg.CPS_TARGET_SHORT_DELTA,
    min_delta: float = cfg.CPS_MIN_SHORT_DELTA,
    max_delta: float = cfg.CPS_MAX_SHORT_DELTA,
) -> Optional[OptionContract]:
    """Pick the short put closest to target |delta| inside the band."""
    candidates: list[tuple[float, OptionContract]] = []
    for c in puts:
        if c.delta is None:
            continue
        abs_delta = abs(c.delta)
        if min_delta <= abs_delta <= max_delta:
            candidates.append((abs(abs_delta - target_delta), c))
    if not candidates:
        return None
    candidates.sort(key=lambda x: x[0])
    return candidates[0][1]


def select_long_put(
    puts: Iterable[OptionContract],
    short_put: OptionContract,
    spot: float,
    atr14: Optional[float],
) -> Optional[OptionContract]:
    """ATR-aware long put selection.

    target_width = max(nearest_strike_step, CPS_WIDTH_ATR_MULTIPLIER × ATR14)

    Constraints:
      • long_strike < short_strike,
      • width in [CPS_MIN_WIDTH_ATR_RATIO, CPS_MAX_WIDTH_ATR_RATIO] × ATR14
        (skipped when ATR is unavailable),
      • picks the strike whose width is closest to the target.
    """
    lower_puts = [c for c in puts if c.strike < short_put.strike and c.delta is not None]
    if not lower_puts:
        return None

    # Strike-grid step from available chain
    strikes = sorted({c.strike for c in puts})
    strike_steps = [b - a for a, b in zip(strikes, strikes[1:]) if b > a]
    nearest_step = min(strike_steps) if strike_steps else 1.0

    if atr14 and atr14 > 0:
        target_width = max(nearest_step, cfg.CPS_WIDTH_ATR_MULTIPLIER * atr14)
        min_width = cfg.CPS_MIN_WIDTH_ATR_RATIO * atr14
        max_width = cfg.CPS_MAX_WIDTH_ATR_RATIO * atr14
    else:
        # No ATR — fall back to a few strike steps as a sane default
        target_width = max(nearest_step, 5.0)
        min_width = nearest_step
        max_width = max(target_width * 2, target_width + 5)

    in_band = [
        c for c in lower_puts
        if min_width <= (short_put.strike - c.strike) <= max_width
    ]
    pool = in_band if in_band else lower_puts
    return min(pool, key=lambda c: abs((short_put.strike - c.strike) - target_width))


# ────────────────────────────────────────────────────────────────────────
# Spread economics
# ────────────────────────────────────────────────────────────────────────

def compute_spread_economics(
    short_leg: CreditPutSpreadLeg,
    long_leg: CreditPutSpreadLeg,
) -> dict:
    """Per-share spread economics. Multiply by 100 for per-contract dollars."""
    net_credit = short_leg.mid - long_leg.mid
    width = short_leg.strike - long_leg.strike
    max_loss = width - net_credit
    credit_to_width = (net_credit / width) if width > 0 else 0.0
    breakeven = short_leg.strike - net_credit
    return {
        "net_credit": net_credit,
        "width": width,
        "max_loss": max_loss,
        "credit_to_width": credit_to_width,
        "breakeven": breakeven,
    }


# ────────────────────────────────────────────────────────────────────────
# Base hard gate inheritance
# ────────────────────────────────────────────────────────────────────────

def passes_base_hard_gates(ticker_result) -> tuple[bool, list[str]]:
    """Mirror the Naked Puts hard gates. Returns (ok, rejection_reasons).

    Operates on a TickerResult-like object exposing:
      term_slope, vrp, vrp_ratio, rv_acceleration, skew_25d, earnings_dte,
      is_etf, regime, iv_current.
    """
    reasons: list[str] = []
    if getattr(ticker_result, "iv_current", None) is None:
        reasons.append("NO_DATA: iv_current is None")
    if getattr(ticker_result, "regime", None) == "DANGER":
        reasons.append("AVOID: ticker regime is DANGER")
    slope = getattr(ticker_result, "term_slope", None)
    if slope is not None and slope > cfg.CPS_DANGER_SLOPE:
        reasons.append(f"AVOID: term_slope {slope:.2f} > {cfg.CPS_DANGER_SLOPE}")
    vrp = getattr(ticker_result, "vrp", None)
    if vrp is not None and vrp < 0:
        reasons.append("NO_EDGE: VRP is negative")
    vrp_ratio = getattr(ticker_result, "vrp_ratio", None)
    if vrp_ratio is not None and vrp_ratio < cfg.CPS_MIN_VRP_RATIO:
        reasons.append(
            f"NO_EDGE: vrp_ratio {vrp_ratio:.2f} < {cfg.CPS_MIN_VRP_RATIO}"
        )
    accel = getattr(ticker_result, "rv_acceleration", None)
    if accel is not None and accel > cfg.CPS_RV_ACCEL_WAIT:
        reasons.append(f"WAIT: rv_acceleration {accel:.2f} > {cfg.CPS_RV_ACCEL_WAIT}")
    skew = getattr(ticker_result, "skew_25d", None)
    if skew is not None and skew > cfg.CPS_EXTREME_SKEW:
        reasons.append(f"AVOID: skew {skew:.1f} > {cfg.CPS_EXTREME_SKEW}")
    dte_e = getattr(ticker_result, "earnings_dte", None)
    is_etf = getattr(ticker_result, "is_etf", False)
    if dte_e is not None and dte_e <= cfg.CPS_EARNINGS_GATE_DTE and not is_etf:
        reasons.append(f"AVOID: earnings in {dte_e}d <= {cfg.CPS_EARNINGS_GATE_DTE}")
    return (len(reasons) == 0, reasons)


# ────────────────────────────────────────────────────────────────────────
# Top-level construction
# ────────────────────────────────────────────────────────────────────────

def _rv_accel_status_label(accel: Optional[float]) -> Optional[str]:
    """Mirror the frontend RV Accel Status labels (display only)."""
    if accel is None:
        return None
    if accel <= 0.85:
        return "Excellent"
    if accel <= 1.00:
        return "Good"
    if accel <= 1.10:
        return "Acceptable"
    if accel <= 1.20:
        return "Caution"
    return "Avoid / Wait"


def _action_from_reason(reason: str) -> CreditPutSpreadAction:
    """Extract the most-severe action label from a rejection-reason string."""
    if reason.startswith("AVOID"):
        return "AVOID"
    if reason.startswith("WAIT"):
        return "WAIT"
    if reason.startswith("NO_DATA"):
        return "NO_DATA"
    if reason.startswith("NO_EDGE"):
        return "NO_EDGE"
    return "NO_EDGE"


def _worst_action(actions: list[CreditPutSpreadAction]) -> CreditPutSpreadAction:
    """Pick the most-restrictive action. AVOID > NO_DATA > WAIT > NO_EDGE > WATCH > SELL."""
    order = ["AVOID", "NO_DATA", "WAIT", "NO_EDGE", "WATCH_CPS", "SELL_CPS"]
    for a in order:
        if a in actions:
            return a  # type: ignore[return-value]
    return "NO_EDGE"


def build_candidate_outcome_for_ticker(
    ticker: str,
    ticker_result,
    chain: list[OptionContract],
    spot: float,
    atr14: Optional[float] = None,
    regime_overlay: Optional[RegimeOverlay] = None,
    consecutive_sell_days: int = 0,
    exact_spread_consecutive_days: int = 0,
    vrp_history_60d: Optional[list[float]] = None,
    asof: Optional[date] = None,
) -> CPSBuildOutcome:
    """Produce one CPS build outcome for a ticker.

    Returns a CPSBuildOutcome with `action`, `candidate` (may be None),
    `rejection_reasons`, `warnings`, and `notes`. The candidate is only
    populated when a valid spread shape could be constructed — AVOID /
    NO_DATA / NO_EDGE outcomes typically have `candidate=None`.
    """
    notes: list[str] = []
    warnings: list[str] = []
    reasons: list[str] = []

    # 1. Universe filter — first and cheapest
    if ticker not in cfg.CPS_UNIVERSE:
        return CPSBuildOutcome(
            ticker=ticker,
            action="NO_EDGE",
            rejection_reasons=[f"NO_EDGE: {ticker} not in CPS_UNIVERSE"],
        )

    # 2. Inherited base hard gates
    gate_ok, gate_reasons = passes_base_hard_gates(ticker_result)
    if not gate_ok:
        action = _worst_action([_action_from_reason(r) for r in gate_reasons])
        return CPSBuildOutcome(
            ticker=ticker,
            action=action,
            rejection_reasons=gate_reasons,
        )

    if not chain:
        return CPSBuildOutcome(
            ticker=ticker,
            action="NO_DATA",
            rejection_reasons=["NO_DATA: empty option chain"],
        )

    # 3. Expiration selection
    exp_pick = select_cps_expiration(chain, asof=asof)
    if exp_pick is None:
        return CPSBuildOutcome(
            ticker=ticker,
            action="NO_DATA",
            rejection_reasons=[
                f"NO_DATA: no expiration in [{cfg.CPS_MIN_DTE}, {cfg.CPS_MAX_DTE}] DTE"
            ],
        )
    expiration, dte = exp_pick
    notes.append(f"Selected expiration {expiration} ({dte} DTE)")

    # 4. Short put selection
    puts_in_exp = [
        c for c in chain
        if c.expiration == expiration and c.contract_type == "put"
    ]
    short_contract = select_short_put(puts_in_exp)
    if short_contract is None:
        return CPSBuildOutcome(
            ticker=ticker,
            action="NO_DATA",
            rejection_reasons=[
                f"NO_DATA: no put with |delta| in "
                f"[{cfg.CPS_MIN_SHORT_DELTA}, {cfg.CPS_MAX_SHORT_DELTA}]"
            ],
        )

    # 5. Long put selection
    long_contract = select_long_put(puts_in_exp, short_contract, spot, atr14)
    if long_contract is None:
        return CPSBuildOutcome(
            ticker=ticker,
            action="NO_DATA",
            rejection_reasons=[
                "NO_DATA: no eligible long put below short strike"
            ],
        )

    short_leg = _make_leg(short_contract, dte)
    long_leg = _make_leg(long_contract, dte)

    # 6. Execution filters — both legs
    short_ok, short_reasons = passes_execution_filter(short_leg)
    long_ok, long_reasons = passes_execution_filter(long_leg)
    if not (short_ok and long_ok):
        return CPSBuildOutcome(
            ticker=ticker,
            action="NO_DATA",
            rejection_reasons=(
                [f"short {r}" for r in short_reasons]
                + [f"long {r}" for r in long_reasons]
            ),
        )

    # 7. Spread economics
    econ = compute_spread_economics(short_leg, long_leg)
    if econ["net_credit"] <= 0:
        return CPSBuildOutcome(
            ticker=ticker,
            action="NO_DATA",
            rejection_reasons=[
                f"NO_DATA: net_credit {econ['net_credit']:.3f} <= 0"
            ],
        )
    if econ["max_loss"] <= 0:
        return CPSBuildOutcome(
            ticker=ticker,
            action="NO_DATA",
            rejection_reasons=[
                f"NO_DATA: max_loss {econ['max_loss']:.3f} <= 0"
            ],
        )
    if econ["credit_to_width"] < cfg.CPS_WATCH_MIN_CREDIT_TO_WIDTH:
        return CPSBuildOutcome(
            ticker=ticker,
            action="NO_EDGE",
            rejection_reasons=[
                f"NO_EDGE: credit_to_width {econ['credit_to_width']:.3f} < "
                f"{cfg.CPS_WATCH_MIN_CREDIT_TO_WIDTH:.2f}"
            ],
        )

    # 8. Width-to-context metadata + high-credit warning
    iv_pct = getattr(ticker_result, "iv_current", None) or 0.0
    em = compute_expected_move(spot, iv_pct, dte)
    width_to_atr = (
        econ["width"] / atr14 if (atr14 and atr14 > 0) else None
    )
    width_to_em = (econ["width"] / em) if em > 0 else None

    if econ["credit_to_width"] > cfg.CPS_HIGH_CREDIT_TO_WIDTH_WARNING:
        warnings.append(
            "High credit/width may indicate elevated tail risk. "
            "Verify regime, skew, and RV Accel before acting."
        )

    # 9. Regime overlay — DANGER blocks SELL_CPS; UNKNOWN warns but does not block
    overlay_status: Optional[RegimeOverlayStatus] = (
        regime_overlay.status if regime_overlay is not None else None
    )
    overlay_blocks_sell = False
    if regime_overlay is not None:
        if regime_overlay.status == "DANGER":
            overlay_blocks_sell = True
            reasons.append("WAIT: regime overlay DANGER (VIX>VIX3M or VVIX>danger)")
        elif regime_overlay.status == "CAUTION":
            warnings.append("Regime overlay CAUTION — vol-of-vol elevated")
        elif regime_overlay.status == "UNKNOWN":
            warnings.append(
                "Regime overlay UNKNOWN — VIX/VIX3M/VVIX unavailable. "
                "Candidates not blocked, but verify manually."
            )

    # 10. VRP z-score (60-day rolling)
    vrp_now = getattr(ticker_result, "vrp", None)
    z = None
    if vrp_history_60d is not None and vrp_now is not None:
        z = compute_vrp_zscore(vrp_history_60d, vrp_now)
        if z is None:
            warnings.append(
                "60-day VRP z-score UNKNOWN — insufficient history (< 20 points)."
            )

    # 11. Decide action
    base_score = float(getattr(ticker_result, "signal_score", 0) or 0)
    rec = getattr(ticker_result, "recommendation", "")

    # SELL_CPS requires:
    #   • base score / recommendation passes the existing SELL threshold,
    #   • credit/width ≥ 25%,
    #   • all hard gates clean,
    #   • ticker-level consecutive_sell_days ≥ 2,
    #   • overlay not DANGER,
    #   • VRP z-score known and ≥ floor (when history available).
    action: CreditPutSpreadAction
    base_passes_sell = base_score >= 65 or rec == "SELL PREMIUM"
    base_passes_watch = base_score >= 60 or rec in ("SELL PREMIUM", "CONDITIONAL")

    sell_blocked_reasons: list[str] = []
    if not base_passes_sell:
        sell_blocked_reasons.append(
            f"base_score {base_score:.0f} or rec '{rec}' below SELL threshold"
        )
    if econ["credit_to_width"] < cfg.CPS_MIN_CREDIT_TO_WIDTH:
        sell_blocked_reasons.append(
            f"credit_to_width {econ['credit_to_width']:.3f} < "
            f"{cfg.CPS_MIN_CREDIT_TO_WIDTH}"
        )
    if consecutive_sell_days < cfg.CPS_SELL_CONFIRMATION_DAYS:
        sell_blocked_reasons.append(
            f"consecutive_sell_days {consecutive_sell_days} < "
            f"{cfg.CPS_SELL_CONFIRMATION_DAYS}"
        )
    if overlay_blocks_sell:
        sell_blocked_reasons.append("regime overlay DANGER blocks SELL_CPS")
    if z is not None and z < cfg.CPS_VRP_ZSCORE_60D_MIN:
        sell_blocked_reasons.append(
            f"60d VRP z-score {z:.2f} < {cfg.CPS_VRP_ZSCORE_60D_MIN}"
        )

    if not sell_blocked_reasons:
        action = "SELL_CPS"
    elif base_passes_watch and econ["credit_to_width"] >= cfg.CPS_WATCH_MIN_CREDIT_TO_WIDTH:
        action = "WATCH_CPS"
        # Surface what's keeping us from SELL_CPS as informational notes
        notes.extend(sell_blocked_reasons)
    else:
        action = "NO_EDGE"
        reasons.extend(sell_blocked_reasons)

    # 12. Carry overlay snapshot onto the candidate
    candidate = CreditPutSpreadCandidate(
        ticker=ticker,
        spot=spot,
        action=action,
        base_score=base_score,
        rank_score=base_score,
        regime=getattr(ticker_result, "regime", "NORMAL") or "NORMAL",
        expiration=expiration,
        dte=dte,
        short_put=short_leg,
        long_put=long_leg,
        width=econ["width"],
        net_credit=econ["net_credit"],
        max_loss=econ["max_loss"],
        credit_to_width=econ["credit_to_width"],
        breakeven=econ["breakeven"],
        atr14=atr14,
        expected_move=em or None,
        expected_move_lower=(spot - em) if em > 0 else None,
        width_to_atr=width_to_atr,
        width_to_expected_move=width_to_em,
        vrp=vrp_now,
        vrp_ratio=getattr(ticker_result, "vrp_ratio", None),
        vrp_zscore_60d=z,
        iv_percentile=getattr(ticker_result, "iv_percentile", None),
        term_slope=getattr(ticker_result, "term_slope", None),
        rv_accel=getattr(ticker_result, "rv_acceleration", None),
        rv_accel_status=_rv_accel_status_label(
            getattr(ticker_result, "rv_acceleration", None)
        ),
        skew=getattr(ticker_result, "skew_25d", None),
        earnings_dte=getattr(ticker_result, "earnings_dte", None),
        consecutive_sell_days=consecutive_sell_days,
        exact_spread_consecutive_days=exact_spread_consecutive_days,
        vix=regime_overlay.vix if regime_overlay else None,
        vix3m=regime_overlay.vix3m if regime_overlay else None,
        vvix=regime_overlay.vvix if regime_overlay else None,
        regime_overlay_status=overlay_status,
        notes=notes,
        warnings=warnings,
        rejection_reasons=reasons,
    )
    return CPSBuildOutcome(
        ticker=ticker,
        action=action,
        candidate=candidate,
        rejection_reasons=reasons,
        warnings=warnings,
        notes=notes,
    )


def build_credit_put_spread_candidates(
    scan_results: dict,
    option_chains: dict[str, list[OptionContract]],
    spot_prices: dict[str, float],
    atr_values: Optional[dict[str, float]] = None,
    regime_overlay: Optional[RegimeOverlay] = None,
    consecutive_sell_days: Optional[dict[str, int]] = None,
    exact_spread_consecutive_days: Optional[dict[str, int]] = None,
    vrp_history_60d: Optional[dict[str, list[float]]] = None,
    asof: Optional[date] = None,
) -> list[CreditPutSpreadCandidate]:
    """Build the ranked CPS candidate list for the latest scan.

    Inputs are dict-keyed by ticker so this function has no DB / network
    dependency — orchestration (main.py) hydrates the dicts before calling.

    Ranking: Base Edge Score desc, with tie-breakers in this order:
      1. higher credit_to_width
      2. lower average bid_ask_ratio across both legs
      3. better RV Accel status (Excellent > Good > Acceptable > Caution > Avoid/Wait)
      4. cleaner term_slope (further below 1.0)

    Returns only actionable candidates (SELL_CPS / WATCH_CPS / WAIT). Hard-gate
    rejects (AVOID / NO_EDGE / NO_DATA) are filtered out at this layer; callers
    can use `build_candidate_outcome_for_ticker` directly if they need them.
    """
    atr_values = atr_values or {}
    consecutive_sell_days = consecutive_sell_days or {}
    exact_spread_consecutive_days = exact_spread_consecutive_days or {}
    vrp_history_60d = vrp_history_60d or {}

    actionable: list[CreditPutSpreadCandidate] = []
    for ticker in cfg.CPS_UNIVERSE:
        tr = scan_results.get(ticker)
        chain = option_chains.get(ticker, [])
        spot = spot_prices.get(ticker, 0.0)
        if tr is None or spot <= 0:
            continue
        outcome = build_candidate_outcome_for_ticker(
            ticker=ticker,
            ticker_result=tr,
            chain=chain,
            spot=spot,
            atr14=atr_values.get(ticker),
            regime_overlay=regime_overlay,
            consecutive_sell_days=consecutive_sell_days.get(ticker, 0),
            exact_spread_consecutive_days=exact_spread_consecutive_days.get(ticker, 0),
            vrp_history_60d=vrp_history_60d.get(ticker),
            asof=asof,
        )
        # WAIT is intentionally included alongside SELL_CPS/WATCH_CPS: the
        # base hard-gate path emits WAIT when RV Accel exceeds CPS_RV_ACCEL_WAIT
        # (see passes_base_hard_gates + _action_from_reason). Surfacing WAIT
        # candidates lets the UI explain "edge present but environment dirty"
        # rather than silently dropping them. Locked by test_rv_accel_shock_rejects.
        if outcome.candidate is not None and outcome.action in (
            "SELL_CPS", "WATCH_CPS", "WAIT"
        ):
            actionable.append(outcome.candidate)

    _RV_ORDER = {
        "Excellent": 0, "Good": 1, "Acceptable": 2, "Caution": 3, "Avoid / Wait": 4,
    }

    def _rv_rank(c: CreditPutSpreadCandidate) -> int:
        return _RV_ORDER.get(c.rv_accel_status or "Acceptable", 2)

    def _avg_bar(c: CreditPutSpreadCandidate) -> float:
        vals = [
            v for v in (c.short_put.bid_ask_ratio, c.long_put.bid_ask_ratio)
            if v is not None
        ]
        return sum(vals) / len(vals) if vals else 1.0

    def _action_rank(c: CreditPutSpreadCandidate) -> int:
        # SELL_CPS first, then WATCH_CPS, then WAIT
        return {"SELL_CPS": 0, "WATCH_CPS": 1, "WAIT": 2}.get(c.action, 3)

    actionable.sort(
        key=lambda c: (
            _action_rank(c),
            -c.base_score,
            -c.credit_to_width,
            _avg_bar(c),
            _rv_rank(c),
            c.term_slope if c.term_slope is not None else 1.0,
        )
    )
    return actionable
