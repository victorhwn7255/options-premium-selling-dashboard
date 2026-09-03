"""GET /api/thresholds — the guide's single source. Named constants must equal their owning
module; the scorer's inline literals are pinned by BEHAVIOUR (boundary surfaces through
score_opportunity); positions_api's inline literals by source tripwires.

Run:  cd backend && python -m pytest test_thresholds.py -v
"""
from __future__ import annotations

import json
from pathlib import Path

import config as cfg
import theta_core as tc
import thresholds as th
from calculator import (ImpliedVolMetrics, RealizedVol, TermStructure, VolSkew, VolSurface)
from scorer import ScoringParams, score_opportunity


def _surface(vrp_ratio=1.60, iv_pct=30.0, slope=1.15, accel=1.15, skew=0.0, vrp=5.0, ivr=50.0):
    return VolSurface(
        ticker="T", price=100.0,
        rv=RealizedVol(rv10=10.0, rv20=10.0, rv30=10.0, rv60=10.0, rv_acceleration=accel),
        iv=ImpliedVolMetrics(iv_current=20.0, iv_rank=ivr, iv_percentile=iv_pct),
        term_structure=TermStructure(points=[], slope=slope, is_contango=slope < 1.0, front_iv=20.0, back_iv=20.0),
        skew=VolSkew(points=[], skew_25d=skew, put_skew_slope=0.0, call_skew_slope=0.0),
        vrp=vrp, vrp_ratio=vrp_ratio)


def _score(**kw):
    return score_opportunity(_surface(**kw), name="T", sector="Tech", params=ScoringParams())


def test_named_constants_match_owners():
    t = th.build_thresholds()
    assert t["cps"]["sell_credit_to_width"] == cfg.CPS_MIN_CREDIT_TO_WIDTH
    assert t["cps"]["confirmation_days"] == cfg.CPS_SELL_CONFIRMATION_DAYS
    assert t["cps"]["vvix_danger"] == cfg.VVIX_DANGER and t["cps"]["universe"] == list(cfg.CPS_UNIVERSE)
    assert t["sizing"]["cap_book_stress_frac"] == tc.CONFIG["cap_book_stress_frac"]
    assert t["sizing"]["kelly_fraction"] == tc.CONFIG["kelly_fraction"]
    assert t["v2"]["dead_zone_index"] == tc.CONFIG["dead_zone_index"]
    assert t["v2"]["veto_denominator"] == tc.CONFIG["veto_denominator"]
    assert t["exits"]["danger_underwater_mult"] == tc.CONFIG["danger_underwater_mult"]
    assert t["exits"]["profit_target"] == 0.75 and t["exits"]["time_exit_dte"] == 21
    assert t["data_quality"]["min_atm_contracts"] == 3
    assert t["sizing"]["f_star_seed"] is None or isinstance(t["sizing"]["f_star_seed"], float)


def test_scorer_literals_pinned_by_behaviour():
    v = th.V1_SCORER
    # Isolate the VRP component: everything else at its zero (iv_pct 30, slope 1.15, accel 1.15, skew 0).
    assert _score(vrp_ratio=v["vrp_ratio_dead_zone"]).signal_score == 0
    assert _score(vrp_ratio=v["vrp_ratio_cap"]).signal_score == v["vrp_points"]
    assert _score(vrp_ratio=v["vrp_ratio_cap"] + 0.5).signal_score == v["vrp_points"]      # capped
    # IV percentile floor and top.
    assert _score(vrp_ratio=1.0, iv_pct=v["iv_pct_floor"]).signal_score == 0
    assert _score(vrp_ratio=1.0, iv_pct=100.0).signal_score == v["iv_pct_points"]
    # Term / accel hinges and skew nodes.
    assert _score(vrp_ratio=1.0, slope=v["term_hinges"][0]).signal_score == v["term_points"][0]
    assert _score(vrp_ratio=1.0, slope=v["term_hinges"][1]).signal_score == v["term_points"][1]
    assert _score(vrp_ratio=1.0, accel=v["accel_hinges"][0]).signal_score == v["accel_points"][0]
    assert _score(vrp_ratio=1.0, accel=v["accel_hinges"][1]).signal_score == v["accel_points"][1]
    assert _score(vrp_ratio=1.0, skew=v["skew_nodes"][1]).signal_score == v["skew_points"]
    assert _score(vrp_ratio=1.0, skew=v["skew_nodes"][2]).signal_score == v["skew_points"]
    assert _score(vrp_ratio=1.0, skew=v["skew_nodes"][3]).signal_score == 0
    # Recommendation tiers need a NORMAL regime, so accel sits at the 1.0 hinge (10 pts, no CAUTION):
    # 30 (ratio 1.60) + 20 (slope 0.85) + 10 (accel 1.0) + iv_pct 5 / 4.29 → 65 / 64.
    assert _score(slope=0.85, accel=1.0, iv_pct=44.0).recommendation == "SELL PREMIUM"
    assert _score(slope=0.85, accel=1.0, iv_pct=42.0).recommendation == "CONDITIONAL"
    # 30 + 10 (accel 1.0) + term 5 (slope 1.0) → 45 ; slope 1.01 → 44.67 → 44.
    assert _score(slope=1.0, accel=1.0).recommendation == "CONDITIONAL"
    assert _score(slope=1.01, accel=1.0).recommendation == "NO EDGE"
    # Negative-VRP cap and WATCHLIST demotion.
    assert _score(vrp=-1.0, iv_pct=100.0, slope=0.85, accel=0.85, skew=8.0).signal_score == v["negative_vrp_cap"]
    assert _score(vrp_ratio=1.14, iv_pct=100.0, slope=0.85, accel=1.0).recommendation == "WATCHLIST"


def test_regime_literals_pinned_by_behaviour():
    r = th.REGIME_PER_TICKER
    assert _score(slope=r["danger_slope"] + 0.01).regime == "DANGER"
    assert _score(slope=r["danger_slope"]).regime != "DANGER"
    assert _score(slope=r["caution_slope"] + 0.01, accel=0.9).regime == "CAUTION"
    assert _score(slope=r["caution_slope"], accel=0.9).regime == "NORMAL"
    assert _score(slope=0.9, accel=r["caution_accel"] + 0.01).regime == "CAUTION"
    assert _score(slope=0.9, accel=r["caution_accel"]).regime == "NORMAL"
    assert _score(slope=0.9, accel=1.11, ivr=91).regime == "CAUTION"


def test_positions_api_literals_tripwire():
    src = Path(__file__).with_name("positions_api.py").read_text()
    e = th.EXIT_RULES
    assert f"eff_target = {e['profit_target_rv_rising']:.2f} if (rv_accel is not None and rv_accel > {e['rv_rising_accel']:.2f})" in src
    assert f">= {e['tested_delta']:.2f}" in src
    assert f"< {e['spread_aware_premium_mult']:.1f} * spread" in src and f"> {e['spread_aware_sigma_mult']:.1f} * sigma_t" in src


def test_endpoint_serves_json():
    from fastapi.testclient import TestClient
    import main
    r = TestClient(main.app).get("/api/thresholds")
    assert r.status_code == 200
    body = r.json()
    for k in ("provenance", "v1_scorer", "regime_per_ticker", "dashboard_regime", "earnings_gate_days",
              "rv_accel_status", "position_hints", "cps", "exits", "sizing", "v2", "data_quality"):
        assert k in body
    json.dumps(body)   # serialisable
