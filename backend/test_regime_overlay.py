"""Unit tests for regime_overlay.py — VIX / VIX3M / VVIX status logic.

yfinance is NOT exercised in these tests — `fetch_regime_overlay` is
called with an injected fetcher so the suite runs offline.
"""

from __future__ import annotations

import os
import sys
import traceback

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config as cfg
from regime_overlay import (
    build_overlay_from_values,
    fetch_regime_overlay,
    compute_vrp_zscore_60d,
)


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


def test_normal_when_all_values_present_and_low():
    o = build_overlay_from_values(vix=18.0, vix3m=20.0, vvix=95.0)
    assert o.status == "NORMAL", o.status
    assert o.vix_backwardation is False
    assert o.warnings == []


def test_caution_when_vvix_between_caution_and_danger():
    o = build_overlay_from_values(vix=18.0, vix3m=20.0, vvix=120.0)
    assert o.status == "CAUTION", o.status
    assert any("VVIX" in w and "elevated" in w for w in o.warnings)


def test_danger_when_vvix_over_danger_threshold():
    o = build_overlay_from_values(vix=18.0, vix3m=20.0, vvix=135.0)
    assert o.status == "DANGER", o.status
    assert any("vol-of-vol extreme" in w for w in o.warnings)


def test_danger_when_vix_backwardation():
    """VIX > VIX3M → DANGER (front-end fear elevated)."""
    o = build_overlay_from_values(vix=22.0, vix3m=20.0, vvix=95.0)
    assert o.status == "DANGER", o.status
    assert o.vix_backwardation is True
    assert any("backwardation" in w for w in o.warnings)


def test_danger_when_both_vix_backwardation_and_vvix_extreme():
    """Both DANGER triggers produce two warnings."""
    o = build_overlay_from_values(vix=25.0, vix3m=20.0, vvix=135.0)
    assert o.status == "DANGER"
    assert len(o.warnings) >= 2


def test_unknown_when_any_value_missing():
    """Missing input → UNKNOWN (not NORMAL — explicit per build plan §5)."""
    o = build_overlay_from_values(vix=18.0, vix3m=None, vvix=95.0)
    assert o.status == "UNKNOWN", o.status
    assert any("UNKNOWN" in w for w in o.warnings)
    assert any("^VIX3M" in w for w in o.warnings)


def test_unknown_does_not_fabricate_normal():
    """When all three are None, never silently report NORMAL."""
    o = build_overlay_from_values(vix=None, vix3m=None, vvix=None)
    assert o.status == "UNKNOWN", o.status
    assert o.vix_backwardation is None


def test_fetch_with_injected_fetcher_returning_data():
    """fetch_regime_overlay routes a fetcher's responses through the
    overlay logic — used to mock yfinance in production tests."""
    values = {"^VIX": 17.5, "^VIX3M": 19.5, "^VVIX": 92.0}
    o = fetch_regime_overlay(fetcher=lambda s: values.get(s))
    assert o.status == "NORMAL"


def test_fetch_with_injected_fetcher_returning_none():
    """Fetcher that fails on every symbol → UNKNOWN overlay."""
    o = fetch_regime_overlay(fetcher=lambda s: None)
    assert o.status == "UNKNOWN"


def test_vrp_zscore_basic():
    """Simple z-score against a flat 60-day history."""
    history = [1.0, 2.0] * 30   # mean 1.5, pstdev 0.5
    z = compute_vrp_zscore_60d(history, current=3.0)
    assert z is not None
    assert abs(z - 3.0) < 1e-6  # (3 - 1.5) / 0.5


def test_vrp_zscore_insufficient_points():
    """Fewer than 20 points → None (UNKNOWN)."""
    history = [1.0] * 5
    assert compute_vrp_zscore_60d(history, current=2.0) is None


def test_vrp_zscore_zero_variance():
    """Zero-variance history → None (z undefined)."""
    history = [5.0] * 60
    assert compute_vrp_zscore_60d(history, current=5.0) is None


def test_vrp_zscore_clips_to_60_points():
    """If history > 60 points, only the last 60 are used — z reflects the
    recent regime, not the ancient zeros."""
    # 1000 zeros (ancient regime) + last 60 alternating around mean 10
    history = [0.0] * 1000 + ([5.0, 15.0] * 30)
    z = compute_vrp_zscore_60d(history, current=20.0)
    assert z is not None
    # Last-60 mean = 10.0, pstdev = 5.0 → z = (20-10)/5 = 2.0
    assert abs(z - 2.0) < 1e-6, f"expected z≈2.0, got {z}"


# ── Runner ────────────────────────────────────────────────────────────


if __name__ == "__main__":
    print("Phase 2 — regime_overlay.py unit tests")
    print("=" * 64)
    tests = [
        ("NORMAL when all values low", test_normal_when_all_values_present_and_low),
        ("CAUTION when VVIX > CAUTION", test_caution_when_vvix_between_caution_and_danger),
        ("DANGER when VVIX > DANGER", test_danger_when_vvix_over_danger_threshold),
        ("DANGER on VIX backwardation", test_danger_when_vix_backwardation),
        ("DANGER both triggers", test_danger_when_both_vix_backwardation_and_vvix_extreme),
        ("UNKNOWN on missing value", test_unknown_when_any_value_missing),
        ("UNKNOWN does not fabricate NORMAL", test_unknown_does_not_fabricate_normal),
        ("fetch_regime_overlay routes fetcher", test_fetch_with_injected_fetcher_returning_data),
        ("fetch_regime_overlay None → UNKNOWN", test_fetch_with_injected_fetcher_returning_none),
        ("VRP z-score basic math", test_vrp_zscore_basic),
        ("VRP z-score < 20 points → None", test_vrp_zscore_insufficient_points),
        ("VRP z-score zero variance → None", test_vrp_zscore_zero_variance),
        ("VRP z-score clips to 60 points", test_vrp_zscore_clips_to_60_points),
    ]
    for name, fn in tests:
        run(name, fn)
    print("\n" + "=" * 64)
    print(f"Results: {passed} passed, {len(failed)} failed")
    print("=" * 64)
    if failed:
        sys.exit(1)
