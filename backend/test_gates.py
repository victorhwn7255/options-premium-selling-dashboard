"""Unit tests for gates.py — the Phase B v2 eligibility orchestration extracted from
main._compute_v2_shadow. Locks the seven-condition decision + reason strings so the
extraction is behavior-preserving and future edits can't silently drift the surface.

Run: python -m pytest test_gates.py -v
"""
import gates
import theta_core as tc

DZ_SINGLE = tc.CONFIG["dead_zone_single"]   # 1.15
DZ_INDEX = tc.CONFIG["dead_zone_index"]     # 1.20
FLOOR = tc.CONFIG["abs_premium_floor_volpts"]  # 2.0
GATE_DAYS = tc.CONFIG["g1_earnings_gate_days"]  # 14


def _normal():
    return tc.GateState()  # NORMAL, no transient/blackout, no pending


# ── G1 earnings resolution (the asymmetric v1/v2 gate) ──

def test_resolve_earnings_gate():
    assert gates.resolve_earnings_gate(True, None) == (False, False, False)       # ETF exempt
    assert gates.resolve_earnings_gate(True, 3) == (False, False, False)          # ETF exempt even dated
    assert gates.resolve_earnings_gate(False, 8) == (True, True, False)           # dated in-window: both gate
    assert gates.resolve_earnings_gate(False, GATE_DAYS) == (True, True, False)   # boundary (<=)
    assert gates.resolve_earnings_gate(False, GATE_DAYS + 1) == (False, False, False)  # outside window
    assert gates.resolve_earnings_gate(False, None) == (False, True, True)        # D4: unverified -> v2 only


# ── eligibility decision + reasons ──

def test_fully_eligible_single_name():
    e = gates.evaluate_eligibility(_normal(), is_etf=False, fvrp_ratio=1.30,
        abs_premium_volpts=3.0, earnings_dte=30, accel_dn=0.9, slope_1m3m=0.95)
    assert e.eligible is True
    assert e.ineligibility_reasons == []
    assert e.gate_state == "NORMAL" and e.v1_earnings_gated is False


def test_dead_zone_blocks_single():
    e = gates.evaluate_eligibility(_normal(), is_etf=False, fvrp_ratio=1.10,
        abs_premium_volpts=3.0, earnings_dte=30, accel_dn=0.9, slope_1m3m=0.95)
    assert e.eligible is False
    assert f"< {DZ_SINGLE:.2f} dead zone" in "; ".join(e.ineligibility_reasons)


def test_index_dead_zone_is_higher_than_single():
    # FVRP 1.17 passes the single-name band (1.15) but not the index/ETF band (1.20)
    single = gates.evaluate_eligibility(_normal(), is_etf=False, fvrp_ratio=1.17,
        abs_premium_volpts=3.0, earnings_dte=30, accel_dn=0.9, slope_1m3m=0.95)
    index = gates.evaluate_eligibility(_normal(), is_etf=True, fvrp_ratio=1.17,
        abs_premium_volpts=3.0, earnings_dte=None, accel_dn=0.9, slope_1m3m=0.95)
    assert single.eligible is True
    assert index.eligible is False
    assert f"< {DZ_INDEX:.2f} dead zone" in "; ".join(index.ineligibility_reasons)


def test_neg_vrp_reason():
    e = gates.evaluate_eligibility(_normal(), is_etf=True, fvrp_ratio=0.90,
        abs_premium_volpts=3.0, earnings_dte=None, accel_dn=0.9, slope_1m3m=0.95)
    assert e.eligible is False
    assert any("neg fwd-VRP" in r for r in e.ineligibility_reasons)


def test_premium_floor_reason():
    e = gates.evaluate_eligibility(_normal(), is_etf=True, fvrp_ratio=1.30,
        abs_premium_volpts=1.0, earnings_dte=None, accel_dn=0.9, slope_1m3m=0.95)
    assert e.eligible is False
    assert any("abs premium" in r for r in e.ineligibility_reasons)


def test_gate_danger_vetoes_with_amzn_style_reason():
    gs = tc.GateState(); gs.state = "DANGER"
    e = gates.evaluate_eligibility(gs, is_etf=True, fvrp_ratio=1.30,
        abs_premium_volpts=3.0, earnings_dte=None, accel_dn=0.70, slope_1m3m=1.14)
    assert e.eligible is False
    joined = "; ".join(e.ineligibility_reasons)
    # AMZN signature: benign (sub-1.0) accel, backwardated slope, yet DANGER (a G2 story)
    assert "gate DANGER (accel_dn 0.70, slope 1.14)" in joined


def test_earnings_dated_gates_both_sides():
    e = gates.evaluate_eligibility(_normal(), is_etf=False, fvrp_ratio=1.30,
        abs_premium_volpts=3.0, earnings_dte=8, accel_dn=0.9, slope_1m3m=0.95)
    assert e.eligible is False
    assert e.v1_earnings_gated is True   # both gate -> AGREE in divergence, not false STRICTER
    assert "gate G1 earnings (in 8d)" in e.ineligibility_reasons


def test_earnings_unverified_is_d4_hardening_only():
    e = gates.evaluate_eligibility(_normal(), is_etf=False, fvrp_ratio=1.30,
        abs_premium_volpts=3.0, earnings_dte=None, accel_dn=0.9, slope_1m3m=0.95)
    assert e.eligible is False
    assert e.v1_earnings_gated is False  # v1 only warns -> genuine V2_STRICTER
    assert any("earnings_unverified" in r for r in e.ineligibility_reasons)


def test_no_fvrp_is_ineligible():
    e = gates.evaluate_eligibility(_normal(), is_etf=True, fvrp_ratio=None,
        abs_premium_volpts=None, earnings_dte=None, accel_dn=1.0, slope_1m3m=None)
    assert e.eligible is False
    assert any("no FVRP" in r for r in e.ineligibility_reasons)


def test_book_freeze_g5_overrides_everything():
    e = gates.evaluate_eligibility(_normal(), is_etf=True, fvrp_ratio=1.30,
        abs_premium_volpts=3.0, earnings_dte=None, accel_dn=0.9, slope_1m3m=0.95,
        book_frozen=True)
    assert e.eligible is False   # otherwise-perfect row, frozen by G5
    assert any("book freeze (G5" in r for r in e.ineligibility_reasons)


def test_structured_surface_propagates_gate_fields():
    gs = tc.GateState(); gs.state = "CAUTION"; gs.transient = True
    gs._pending = "DANGER"; gs._pending_days = 1
    e = gates.evaluate_eligibility(gs, is_etf=True, fvrp_ratio=1.30,
        abs_premium_volpts=3.0, earnings_dte=None, accel_dn=1.2, slope_1m3m=0.99)
    assert e.gate_state == "CAUTION"
    assert e.transient is True
    assert e.pending == "DANGER" and e.pending_days == 1


def test_reasons_order_matches_inline_contract():
    # Multi-failure single name: earnings(unverified) → FVRP dead-zone → premium floor,
    # gate NORMAL (no gate reason). Order must match the pre-extraction inline path.
    e = gates.evaluate_eligibility(_normal(), is_etf=False, fvrp_ratio=1.10,
        abs_premium_volpts=1.0, earnings_dte=None, accel_dn=0.9, slope_1m3m=0.95)
    rs = e.ineligibility_reasons
    assert rs[0].startswith("earnings_unverified")
    assert "dead zone" in rs[1]
    assert "abs premium" in rs[2]
