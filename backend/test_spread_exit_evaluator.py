"""Unit tests for spread_exit_evaluator.py — CPS management decisions."""

from __future__ import annotations

import os
import sys
import traceback

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config as cfg
from spread_exit_evaluator import (
    OpenSpreadSnapshot,
    evaluate_open_spread,
    pin_risk_threshold,
)


def base_snap(**overrides) -> OpenSpreadSnapshot:
    """Sensible default open-spread state — short 500 / long 495, 35 DTE."""
    defaults = dict(
        ticker="SPY",
        short_strike=500.0,
        long_strike=495.0,
        expiration="2026-06-19",
        dte=35,
        spot=520.0,
        original_credit=1.25,
        current_mark=1.10,
        earnings_dte=None,
        regime="NORMAL",
        is_etf=True,
    )
    defaults.update(overrides)
    return OpenSpreadSnapshot(**defaults)


passed = 0
failed: list[tuple[str, str]] = []


def run(name, fn):
    global passed
    print(f"\nTest: {name}")
    try:
        fn()
        passed += 1
        print(f"  PASS: {name}")
    except AssertionError as e:
        failed.append((name, str(e)))
        print(f"  FAIL: {name}\n    {e}")
    except Exception as e:
        failed.append((name, f"{type(e).__name__}: {e}"))
        print(f"  ERROR: {name}\n    {type(e).__name__}: {e}\n{traceback.format_exc()}")


# ── Tests ─────────────────────────────────────────────────────────────


def test_hold_when_nothing_triggers():
    """35 DTE, mark above target, spot well above short → HOLD."""
    d = evaluate_open_spread(base_snap())
    assert d.action == "HOLD", d.action


def test_profit_target_at_half_credit():
    """Mark ≤ 50% × original credit → CLOSE_PROFIT_TARGET."""
    d = evaluate_open_spread(base_snap(current_mark=0.50))  # 0.50 ≤ 0.625
    assert d.action == "CLOSE_PROFIT_TARGET", d.action


def test_defensive_when_mark_double_credit():
    """Mark ≥ 2× original credit → CLOSE_DEFENSIVE."""
    d = evaluate_open_spread(base_snap(current_mark=2.50))  # ≥ 2 × 1.25
    assert d.action == "CLOSE_DEFENSIVE", d.action
    assert "credit" in d.reason.lower()


def test_defensive_when_short_strike_breached():
    """Spot at/below short strike → CLOSE_DEFENSIVE."""
    d = evaluate_open_spread(base_snap(spot=499.0))
    assert d.action == "CLOSE_DEFENSIVE", d.action
    assert "short strike" in d.reason


def test_defensive_when_regime_flips_to_danger():
    """Regime DANGER → CLOSE_DEFENSIVE even if everything else is fine."""
    d = evaluate_open_spread(base_snap(regime="DANGER"))
    assert d.action == "CLOSE_DEFENSIVE", d.action
    assert "DANGER" in d.reason


def test_time_exit_at_or_below_21_dte():
    """DTE ≤ 21 with no other trigger → CLOSE_TIME."""
    d = evaluate_open_spread(base_snap(dte=21))
    assert d.action == "CLOSE_TIME", d.action
    # And one DTE below boundary
    d2 = evaluate_open_spread(base_snap(dte=15))
    assert d2.action == "CLOSE_TIME", d2.action


def test_time_exit_at_22_dte_holds():
    """One day above the time-exit boundary → still HOLD."""
    d = evaluate_open_spread(base_snap(dte=22))
    assert d.action == "HOLD", d.action


def test_pin_risk_dte_2_and_near_short_strike():
    """DTE ≤ 2 and |spot - short_strike| ≤ max($0.50, 0.1%×spot) → CLOSE_PIN_RISK."""
    d = evaluate_open_spread(base_snap(dte=2, spot=500.30))  # within $0.50 of 500
    assert d.action == "CLOSE_PIN_RISK", d.action


def test_pin_risk_dte_0_at_strike():
    """Expiry day with spot exactly at short strike → CLOSE_PIN_RISK."""
    d = evaluate_open_spread(base_snap(dte=0, spot=500.00))
    assert d.action == "CLOSE_PIN_RISK", d.action


def test_pin_risk_threshold_scales_with_spot():
    """Pin threshold scales with higher-priced ETFs."""
    assert pin_risk_threshold(500.0) == 0.5
    assert pin_risk_threshold(1500.0) == 1.5  # 0.1% × 1500
    # Larger pin risk distance at higher spot
    d = evaluate_open_spread(base_snap(
        dte=2, spot=1500.80, short_strike=1500.0,
    ))
    # 0.1% × 1500 = 1.5 → 0.80 is within → PIN
    assert d.action == "CLOSE_PIN_RISK", d.action


def test_pin_risk_does_not_fire_far_from_strike():
    """DTE ≤ 2 but spot well away from short → no pin trigger."""
    # Mark is at original credit so profit target doesn't fire either
    d = evaluate_open_spread(base_snap(
        dte=2, spot=515.0, current_mark=1.25,
    ))
    # DTE 2 still triggers CLOSE_TIME (≤ 21)
    assert d.action == "CLOSE_TIME", d.action


def test_event_risk_blocks_non_etf_earnings():
    """Earnings ≤ 14 DTE on a non-ETF → CLOSE_EVENT_RISK."""
    d = evaluate_open_spread(base_snap(
        is_etf=False, earnings_dte=10, dte=35,
    ))
    assert d.action == "CLOSE_EVENT_RISK", d.action


def test_event_risk_ignores_etfs():
    """ETFs are exempt from event-risk trigger by convention."""
    d = evaluate_open_spread(base_snap(
        is_etf=True, earnings_dte=10, dte=35,
    ))
    assert d.action == "HOLD", d.action


def test_event_risk_ignores_far_earnings():
    """earnings_dte well outside the event window → no trigger."""
    d = evaluate_open_spread(base_snap(
        is_etf=False, earnings_dte=60, dte=35,
    ))
    assert d.action == "HOLD", d.action


def test_pin_risk_wins_over_event_risk():
    """When multiple triggers fire, pin-risk wins (higher precedence)."""
    d = evaluate_open_spread(base_snap(
        is_etf=False, earnings_dte=10, dte=2, spot=500.20,
    ))
    assert d.action == "CLOSE_PIN_RISK", d.action


def test_event_risk_wins_over_time_exit():
    """Event risk beats time exit when DTE is in the time-exit window."""
    d = evaluate_open_spread(base_snap(
        is_etf=False, earnings_dte=10, dte=18, spot=520.0,
    ))
    # DTE 18 ≤ 21 (time) AND earnings 10 ≤ 14 (event); event has higher precedence
    assert d.action == "CLOSE_EVENT_RISK", d.action


def test_defensive_wins_over_profit_target():
    """If both short-strike-breach and profit-target conditions are met,
    defensive wins (an in-the-money spread cannot still be at profit)."""
    # Contrived: mark 0.50 (would be profit target) but spot below short
    d = evaluate_open_spread(base_snap(spot=495.0, current_mark=0.50))
    assert d.action == "CLOSE_DEFENSIVE", d.action


# ── Runner ────────────────────────────────────────────────────────────


if __name__ == "__main__":
    print("Phase 2 — spread_exit_evaluator.py unit tests")
    print("=" * 64)
    tests = [
        ("HOLD when nothing triggers", test_hold_when_nothing_triggers),
        ("CLOSE_PROFIT_TARGET at half credit", test_profit_target_at_half_credit),
        ("CLOSE_DEFENSIVE when mark double credit", test_defensive_when_mark_double_credit),
        ("CLOSE_DEFENSIVE when short breached", test_defensive_when_short_strike_breached),
        ("CLOSE_DEFENSIVE when regime DANGER", test_defensive_when_regime_flips_to_danger),
        ("CLOSE_TIME at DTE ≤ 21", test_time_exit_at_or_below_21_dte),
        ("HOLD at DTE = 22", test_time_exit_at_22_dte_holds),
        ("CLOSE_PIN_RISK at DTE 2 near strike", test_pin_risk_dte_2_and_near_short_strike),
        ("CLOSE_PIN_RISK at DTE 0 at strike", test_pin_risk_dte_0_at_strike),
        ("Pin threshold scales with spot", test_pin_risk_threshold_scales_with_spot),
        ("Pin does not fire far from strike", test_pin_risk_does_not_fire_far_from_strike),
        ("CLOSE_EVENT_RISK on non-ETF earnings ≤ 14d", test_event_risk_blocks_non_etf_earnings),
        ("ETF exempt from event risk", test_event_risk_ignores_etfs),
        ("No event risk far from earnings", test_event_risk_ignores_far_earnings),
        ("Pin risk > event risk precedence", test_pin_risk_wins_over_event_risk),
        ("Event risk > time exit precedence", test_event_risk_wins_over_time_exit),
        ("Defensive > profit target precedence", test_defensive_wins_over_profit_target),
    ]
    for name, fn in tests:
        run(name, fn)
    print("\n" + "=" * 64)
    print(f"Results: {passed} passed, {len(failed)} failed")
    print("=" * 64)
    if failed:
        sys.exit(1)
