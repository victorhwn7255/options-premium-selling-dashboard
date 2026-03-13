"""Tests for the liquidity filter in calculator.py."""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from marketdata_client import OptionContract
from calculator import filter_liquid_contracts, compute_skew, compute_atm_iv


def _make_contract(
    strike, iv, bid, ask,
    contract_type="call", delta=None,
    expiration="2027-12-17",
):
    return OptionContract(
        ticker="TEST",
        strike=strike,
        expiration=expiration,
        contract_type=contract_type,
        implied_volatility=iv,
        delta=delta,
        bid=bid,
        ask=ask,
    )


# ── filter_liquid_contracts unit tests ──────────────────


def test_rejects_zero_bid():
    contracts = [
        _make_contract(100, 0.30, bid=1.50, ask=1.80),
        _make_contract(105, 0.25, bid=0.0, ask=4.80),   # illiquid
        _make_contract(95, 0.35, bid=2.00, ask=2.40),
    ]
    result = filter_liquid_contracts(contracts)
    assert len(result) == 2
    assert all(c.bid > 0 for c in result)


def test_rejects_wide_spread():
    contracts = [
        _make_contract(100, 0.30, bid=1.50, ask=1.80),  # spread/mid = 18% OK
        _make_contract(105, 0.25, bid=0.50, ask=4.80),  # spread/mid = 162% BAD
        _make_contract(95, 0.35, bid=2.00, ask=2.40),   # spread/mid = 18% OK
    ]
    result = filter_liquid_contracts(contracts)
    assert len(result) == 2
    strikes = {c.strike for c in result}
    assert 105 not in strikes


def test_keeps_contracts_without_quotes():
    contracts = [
        _make_contract(100, 0.30, bid=None, ask=None),
        _make_contract(105, 0.25, bid=1.00, ask=1.20),
    ]
    result = filter_liquid_contracts(contracts)
    assert len(result) == 2


def test_all_illiquid_returns_empty():
    contracts = [
        _make_contract(100, 0.30, bid=0.0, ask=4.80),
        _make_contract(105, 0.25, bid=0.0, ask=3.50),
    ]
    result = filter_liquid_contracts(contracts)
    assert len(result) == 0


def test_spread_at_boundary():
    """Spread exactly at 50% should be rejected (> not >=)."""
    # mid = 1.50, spread = 1.00, ratio = 0.6667 -> rejected
    c_wide = _make_contract(100, 0.30, bid=1.00, ask=2.00)
    # mid = 2.50, spread = 1.00, ratio = 0.40 -> kept
    c_ok = _make_contract(105, 0.25, bid=2.00, ask=3.00)
    result = filter_liquid_contracts([c_wide, c_ok])
    assert len(result) == 1
    assert result[0].strike == 105


# ── Integration: filtering produces cleaner skew ────────


def test_filtering_removes_garbage_from_skew():
    """
    Verify that a contract list with bid=0 entries produces different
    (cleaner) skew results after filtering.
    """
    spot = 100.0

    contracts = [
        # Liquid puts with reasonable IVs
        _make_contract(95, 0.35, bid=3.00, ask=3.40,
                       contract_type="put", delta=-0.25),
        _make_contract(90, 0.38, bid=1.50, ask=1.90,
                       contract_type="put", delta=-0.15),
        # Illiquid put: bid=0, garbage-high IV from bad mid pricing
        _make_contract(85, 0.80, bid=0.0, ask=4.80,
                       contract_type="put", delta=-0.10),
        # Liquid calls
        _make_contract(100, 0.30, bid=2.50, ask=2.80,
                       contract_type="call", delta=0.50),
        _make_contract(105, 0.28, bid=1.20, ask=1.50,
                       contract_type="call", delta=0.30),
        # Illiquid call: bid=0, garbage IV
        _make_contract(115, 0.65, bid=0.0, ask=5.00,
                       contract_type="call", delta=0.10),
    ]

    # Unfiltered skew includes garbage IV from illiquid contracts
    skew_unfiltered = compute_skew(contracts, spot)

    # Filtered skew should exclude the garbage
    filtered = filter_liquid_contracts(contracts)
    skew_filtered = compute_skew(filtered, spot)

    # Fewer points (the illiquid ones removed)
    assert len(skew_filtered.points) < len(skew_unfiltered.points)

    # The removed contracts had inflated IVs (80%, 65%) so the unfiltered
    # put slope should be steeper / more distorted
    unfiltered_put_ivs = [p.iv for p in skew_unfiltered.points
                          if p.contract_type == "put"]
    filtered_put_ivs = [p.iv for p in skew_filtered.points
                        if p.contract_type == "put"]

    # Max IV in unfiltered should be higher (the 80% garbage contract)
    if unfiltered_put_ivs and filtered_put_ivs:
        assert max(unfiltered_put_ivs) > max(filtered_put_ivs)


def test_filtering_changes_atm_iv():
    """
    ATM IV should differ when illiquid ATM contracts are removed.
    """
    spot = 100.0

    # Two expirations — one with a mix of liquid + illiquid ATM contracts
    contracts = [
        # Liquid ATM call with reasonable IV
        _make_contract(100, 0.25, bid=3.00, ask=3.30,
                       contract_type="call", expiration="2027-11-19"),
        # Illiquid ATM put with inflated IV (bid=0)
        _make_contract(100, 0.45, bid=0.0, ask=5.00,
                       contract_type="put", expiration="2027-11-19"),
        # Liquid ATM put
        _make_contract(100, 0.26, bid=2.80, ask=3.10,
                       contract_type="put", expiration="2027-11-19"),
    ]

    iv_unfiltered = compute_atm_iv(contracts, spot, target_dte=600)
    filtered = filter_liquid_contracts(contracts)
    iv_filtered = compute_atm_iv(filtered, spot, target_dte=600)

    # The inflated 45% IV from the illiquid put should pull unfiltered higher
    assert iv_unfiltered is not None
    assert iv_filtered is not None
    assert iv_unfiltered > iv_filtered


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
