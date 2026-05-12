"""
Credit Put Spread — exit-rule evaluator.

Pure backend logic. Evaluates an open CPS position and returns a
`SpreadExitDecision` (action + reason + notes). No DB, no I/O, no UI
dependency — the Journal will hold open positions and call this evaluator
once per scan when it ships in Phase 6.

Action precedence (highest priority first; the FIRST match wins so the
trader sees the most urgent reason rather than a stale lower-priority
trigger):

  1. CLOSE_PIN_RISK      — DTE ≤ 2 AND spot near short strike
  2. CLOSE_EVENT_RISK    — earnings ≤ 14 DTE entering window
  3. CLOSE_DEFENSIVE     — short-strike breach OR mark ≥ 2× credit
                           OR regime flipped to DANGER
  4. CLOSE_TIME          — DTE ≤ 21
  5. CLOSE_PROFIT_TARGET — current mark ≤ 50% of original credit
  6. HOLD                — none of the above

See references/credit-put-spreads.md §10 for the canonical rule table.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import config as cfg
from models import SpreadExitDecision


# ────────────────────────────────────────────────────────────────────────
# Input dataclass — keeps the evaluator's signature small and pure.
# The Journal will hydrate this from an OpenSpread row at evaluation time.
# ────────────────────────────────────────────────────────────────────────

@dataclass
class OpenSpreadSnapshot:
    """Current state of an open CPS position at evaluation time."""
    ticker: str
    short_strike: float
    long_strike: float
    expiration: str  # YYYY-MM-DD
    dte: int
    spot: float
    original_credit: float
    # Current mark-to-close per share (positive number; what it would cost
    # to buy the spread back today).
    current_mark: float
    # Optional context — None means "not flagged".
    earnings_dte: Optional[int] = None
    regime: Optional[str] = None  # "NORMAL" / "CAUTION" / "DANGER" / None
    is_etf: bool = False


# ────────────────────────────────────────────────────────────────────────
# Pin-risk distance — explicit because spreads have multi-leg pin/assignment
# complexity that simple naked-put pin rules don't capture.
# ────────────────────────────────────────────────────────────────────────

def pin_risk_threshold(spot: float) -> float:
    """max($0.50, 0.1% of spot). Scales with higher-priced ETFs."""
    return max(cfg.CPS_PIN_RISK_MIN_DISTANCE, cfg.CPS_PIN_RISK_SPOT_PCT * spot)


def _is_pin_risk(snap: OpenSpreadSnapshot) -> bool:
    if snap.dte > cfg.CPS_PIN_RISK_DTE:
        return False
    threshold = pin_risk_threshold(snap.spot)
    return abs(snap.spot - snap.short_strike) <= threshold


def _is_event_risk(snap: OpenSpreadSnapshot) -> bool:
    """Earnings within event-risk window; ETFs exempt by convention."""
    if snap.is_etf:
        return False
    if snap.earnings_dte is None:
        return False
    return snap.earnings_dte <= cfg.CPS_EVENT_RISK_DTE


def _is_defensive(snap: OpenSpreadSnapshot) -> tuple[bool, Optional[str]]:
    """Three independent defensive triggers."""
    # 1. Short-strike breach
    if snap.spot <= snap.short_strike:
        return (
            True,
            f"Spot {snap.spot:.2f} ≤ short strike {snap.short_strike:.2f} — short leg in the money."
        )
    # 2. Mark blew through 2× original credit
    if (
        snap.original_credit > 0
        and snap.current_mark >= cfg.CPS_DEFENSIVE_MARK_MULTIPLE * snap.original_credit
    ):
        return (
            True,
            (
                f"Current mark {snap.current_mark:.2f} ≥ "
                f"{cfg.CPS_DEFENSIVE_MARK_MULTIPLE:.0f}× original credit "
                f"{snap.original_credit:.2f}."
            ),
        )
    # 3. Regime flipped to DANGER
    if snap.regime == "DANGER":
        return (True, "Ticker regime flipped to DANGER (term slope > 1.15).")
    return (False, None)


def _is_time_exit(snap: OpenSpreadSnapshot) -> bool:
    return snap.dte <= cfg.CPS_TIME_EXIT_DTE


def _is_profit_target(snap: OpenSpreadSnapshot) -> bool:
    if snap.original_credit <= 0:
        return False
    return snap.current_mark <= cfg.CPS_PROFIT_TARGET_FRAC * snap.original_credit


# ────────────────────────────────────────────────────────────────────────
# Public evaluator
# ────────────────────────────────────────────────────────────────────────

def evaluate_open_spread(snap: OpenSpreadSnapshot) -> SpreadExitDecision:
    """Return the highest-priority action for an open CPS position.

    Precedence is documented in the module docstring. First matching rule wins.
    """
    notes: list[str] = [
        f"DTE {snap.dte}, spot {snap.spot:.2f}, "
        f"mark {snap.current_mark:.2f} / credit {snap.original_credit:.2f}"
    ]

    if _is_pin_risk(snap):
        return SpreadExitDecision(
            action="CLOSE_PIN_RISK",
            reason=(
                f"Pin risk: DTE {snap.dte} ≤ {cfg.CPS_PIN_RISK_DTE} AND "
                f"|spot − short_strike| = {abs(snap.spot - snap.short_strike):.2f} ≤ "
                f"max(${cfg.CPS_PIN_RISK_MIN_DISTANCE:.2f}, "
                f"{cfg.CPS_PIN_RISK_SPOT_PCT*100:.1f}% × spot)."
            ),
            notes=notes,
        )

    if _is_event_risk(snap):
        return SpreadExitDecision(
            action="CLOSE_EVENT_RISK",
            reason=(
                f"Earnings in {snap.earnings_dte}d ≤ "
                f"{cfg.CPS_EVENT_RISK_DTE} — close before binary event."
            ),
            notes=notes,
        )

    defensive_hit, defensive_reason = _is_defensive(snap)
    if defensive_hit:
        return SpreadExitDecision(
            action="CLOSE_DEFENSIVE",
            reason=defensive_reason or "Defensive trigger.",
            notes=notes,
        )

    if _is_time_exit(snap):
        return SpreadExitDecision(
            action="CLOSE_TIME",
            reason=f"DTE {snap.dte} ≤ {cfg.CPS_TIME_EXIT_DTE} — close or reassess.",
            notes=notes,
        )

    if _is_profit_target(snap):
        return SpreadExitDecision(
            action="CLOSE_PROFIT_TARGET",
            reason=(
                f"Mark {snap.current_mark:.2f} ≤ "
                f"{cfg.CPS_PROFIT_TARGET_FRAC*100:.0f}% × credit "
                f"{snap.original_credit:.2f}."
            ),
            notes=notes,
        )

    return SpreadExitDecision(
        action="HOLD",
        reason="No exit trigger hit — let theta accrue.",
        notes=notes,
    )
