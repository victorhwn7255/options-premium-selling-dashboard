"""Display thresholds — the single source the "How to use" guide renders from (GET /api/thresholds).

Read-only, additive, no new constants: every number here is either imported from the module that
owns it (config.py, theta_core.CONFIG, calculator.py, positions_api defaults) or — for the scorer's
inline literals and the frontend-owned gates — mirrored here and PINNED by behavioural / tripwire
tests in test_thresholds.py, so the guide's pills can never drift from the code again (ADR-001
spirit: the backend is the source of truth; P1 letter: the frontend only displays).

Groups marked frontend-owned are reproduced for display only — their logic lives in the frozen
scoring.ts / RegimeBanner.tsx (ADR-003, ADR-006).
"""
from __future__ import annotations

import json
from pathlib import Path

import config as cfg
import theta_core as tc
from calculator import MAX_IV, MAX_SPREAD_RATIO, MIN_ATM_CONTRACTS
from positions_api import DEFAULT_EXIT_DTE, DEFAULT_TARGET_CAPTURE

_SEED = Path(__file__).parent / "kelly_seed.json"

# scorer.py inline literals (pinned by test_thresholds.py::test_scorer_literals_pinned_by_behaviour)
V1_SCORER = {
    "vrp_ratio_dead_zone": 1.15, "vrp_ratio_cap": 1.60, "vrp_points": 30,
    "iv_pct_floor": 30, "iv_pct_points": 25,
    "term_hinges": [0.85, 1.00, 1.15], "term_points": [20, 5, 0],
    "accel_hinges": [0.85, 1.00, 1.15], "accel_points": [15, 10, 0],
    "skew_nodes": [0, 7, 12, 20], "skew_points": 10,
    "sell": 65, "conditional": 45, "reduce_size": 55, "negative_vrp_cap": 54,
}
REGIME_PER_TICKER = {
    "danger_slope": 1.15, "caution_slope": 1.05, "caution_accel": 1.10,
    "caution_ivr": 90, "caution_ivr_accel": 1.1,
}
# frontend-owned (scoring.ts / RegimeBanner.tsx) — display mirror
DASHBOARD_REGIME = {"off_season_danger_pct": 0.40, "regular_season_stress_pct": 0.25,
                    "finals_avg_vrp": 8, "finals_avg_slope": 0.90, "finals_ever_triggered": False}
EARNINGS_GATE_DAYS = 14
RV_ACCEL_STATUS = [
    {"max": 0.85, "label": "Excellent", "meaning": "vol decelerating — clean"},
    {"max": 1.00, "label": "Good", "meaning": "stable to declining — favourable"},
    {"max": 1.10, "label": "Acceptable", "meaning": "mildly rising — trade selectively"},
    {"max": 1.20, "label": "Caution", "meaning": "vol heating up — wait or require strong confirmation"},
    {"max": None, "label": "Avoid / Wait", "meaning": "vol spiking — no new naked entries"},
]
# scorer.py construction table (display mirror of the elif chain)
POSITION_HINTS = [
    {"condition": "DANGER regime", "delta": "N/A", "structure": "No position", "dte": "N/A", "notional": "0%"},
    {"condition": "WATCHLIST (ratio < 1.15)", "delta": "N/A", "structure": "Wait for premium to expand", "dte": "N/A", "notional": "0%"},
    {"condition": "CAUTION regime", "delta": "10–15Δ", "structure": "Iron condor or wide put spread (defined risk only)", "dte": "21–30", "notional": "1–2%"},
    {"condition": "NORMAL · IV Rank ≥ 80 · VRP > 8", "delta": "16–20Δ", "structure": "Short strangle or jade lizard", "dte": "30–45", "notional": "2–5%"},
    {"condition": "NORMAL · IV Rank ≥ 80 · VRP > 4", "delta": "16–20Δ", "structure": "Iron condor or put credit spread", "dte": "30–45", "notional": "2–5%"},
    {"condition": "NORMAL · IV Rank ≥ 80 · VRP ≤ 4", "delta": "16–20Δ", "structure": "Put credit spread, strict width", "dte": "30–45", "notional": "2–5%"},
    {"condition": "NORMAL · IV Rank < 80", "delta": "20–30Δ", "structure": "Put credit spread, narrow width", "dte": "45–60", "notional": "2–3%"},
]
# positions_api.compute_flags inline literals (tripwire-tested)
EXIT_RULES = {
    "profit_target": DEFAULT_TARGET_CAPTURE, "profit_target_rv_rising": 0.50, "rv_rising_accel": 1.10,
    "time_exit_dte": DEFAULT_EXIT_DTE, "tested_delta": 0.30,
    "spread_aware_premium_mult": 2.0, "spread_aware_sigma_mult": 1.5, "spread_aware_decay_to_dte": 7,
    "stop_loss": None,
}


def _f_star_seed() -> float | None:
    try:
        return float(json.loads(_SEED.read_text()).get("f_star_seed"))
    except Exception:  # noqa: BLE001 — display only
        return None


def build_thresholds() -> dict:
    c = tc.CONFIG
    return {
        "provenance": {
            "v1_scorer": "backend/scorer.py (inline literals; pinned by behavioural tests)",
            "regime_per_ticker": "backend/scorer.py (inline literals; pinned by behavioural tests)",
            "dashboard_regime": "frontend/src/components/RegimeBanner.tsx (frontend-owned, ADR-006)",
            "earnings_gate_days": "frontend/src/lib/scoring.ts (frontend-owned, ADR-003; frozen at Phase B)",
            "rv_accel_status": "frontend/src/lib/scoring.ts getRvAccelStatus (frontend-owned; frozen)",
            "position_hints": "backend/scorer.py construction table",
            "cps": "backend/config.py",
            "exits": "backend/positions_api.py (defaults + inline literals, tripwire-tested) · theta_core.CONFIG",
            "sizing": "backend/theta_core.CONFIG (golden master, P3) · backend/kelly_seed.json",
            "v2": "backend/theta_core.CONFIG",
            "data_quality": "backend/calculator.py",
        },
        "v1_scorer": dict(V1_SCORER),
        "regime_per_ticker": dict(REGIME_PER_TICKER),
        "dashboard_regime": dict(DASHBOARD_REGIME),
        "earnings_gate_days": EARNINGS_GATE_DAYS,
        "rv_accel_status": [dict(r) for r in RV_ACCEL_STATUS],
        "position_hints": [dict(r) for r in POSITION_HINTS],
        "cps": {
            "universe": list(cfg.CPS_UNIVERSE),
            "target_dte": cfg.CPS_TARGET_DTE, "min_dte": cfg.CPS_MIN_DTE, "max_dte": cfg.CPS_MAX_DTE,
            "target_short_delta": cfg.CPS_TARGET_SHORT_DELTA,
            "min_short_delta": cfg.CPS_MIN_SHORT_DELTA, "max_short_delta": cfg.CPS_MAX_SHORT_DELTA,
            "sell_credit_to_width": cfg.CPS_MIN_CREDIT_TO_WIDTH,
            "watch_credit_to_width": cfg.CPS_WATCH_MIN_CREDIT_TO_WIDTH,
            "thin_premium_threshold": cfg.CPS_THIN_PREMIUM_THRESHOLD,
            "high_credit_to_width_warning": cfg.CPS_HIGH_CREDIT_TO_WIDTH_WARNING,
            "max_bid_ask_ratio": cfg.CPS_MAX_BID_ASK_RATIO, "min_open_interest": cfg.CPS_MIN_OPEN_INTEREST,
            "min_volume": cfg.CPS_MIN_VOLUME, "confirmation_days": cfg.CPS_SELL_CONFIRMATION_DAYS,
            "vvix_caution": cfg.VVIX_CAUTION, "vvix_danger": cfg.VVIX_DANGER,
            "vrp_zscore_60d_min": cfg.CPS_VRP_ZSCORE_60D_MIN,
            "time_exit_dte": cfg.CPS_TIME_EXIT_DTE, "profit_target_frac": cfg.CPS_PROFIT_TARGET_FRAC,
            "defensive_mark_multiple": cfg.CPS_DEFENSIVE_MARK_MULTIPLE, "event_risk_dte": cfg.CPS_EVENT_RISK_DTE,
            "pin_risk_dte": cfg.CPS_PIN_RISK_DTE,
            "inherited_gates": {"earnings_dte": cfg.CPS_EARNINGS_GATE_DTE, "danger_slope": cfg.CPS_DANGER_SLOPE,
                                "min_vrp_ratio": cfg.CPS_MIN_VRP_RATIO, "rv_accel_wait": cfg.CPS_RV_ACCEL_WAIT,
                                "extreme_skew": cfg.CPS_EXTREME_SKEW},
        },
        "exits": {**EXIT_RULES, "danger_underwater_mult": c["danger_underwater_mult"]},
        "sizing": {
            "kelly_fraction": c["kelly_fraction"], "kelly_min_trades": c["kelly_min_trades"],
            "f_star_seed": _f_star_seed(),
            "dial_R_bounds": list(c["dial_R_bounds"]), "dial_O_bounds": list(c["dial_O_bounds"]),
            "cap_notional_frac": c["cap_notional_frac"], "cap_margin_frac": c["cap_margin_frac"],
            "cap_name_margin_frac": c["cap_name_margin_frac"], "cap_name_stress_frac": c["cap_name_stress_frac"],
            "cap_book_stress_frac": c["cap_book_stress_frac"],
            "stress_spot_mult": c["stress_spot_mult"], "stress_iv_mult": c["stress_iv_mult"],
            "stress_days_elapsed": c["stress_days_elapsed"], "margin_alpha": c["margin_alpha"],
        },
        "v2": {
            "dead_zone_index": c["dead_zone_index"], "dead_zone_single": c["dead_zone_single"],
            "abs_premium_floor_volpts": c["abs_premium_floor_volpts"],
            "g1_earnings_gate_days": c["g1_earnings_gate_days"],
            "g2_caution_in": c["g2_caution_in"], "g2_caution_out": c["g2_caution_out"],
            "g2_danger_in": c["g2_danger_in"], "g2_danger_out": c["g2_danger_out"],
            "g3_in": c["g3_in"], "g3_out": c["g3_out"], "g3_concentration": c["g3_concentration"],
            "confirm_days": c["confirm_days"], "transient_blackout_days": c["transient_blackout_days"],
            "veto_denominator": c["veto_denominator"],
            "max_spread_over_mid": c["max_spread_over_mid"], "max_rtc_over_capture": c["max_rtc_over_capture"],
        },
        "data_quality": {"min_atm_contracts": MIN_ATM_CONTRACTS, "max_spread_ratio": MAX_SPREAD_RATIO,
                         "max_iv": MAX_IV},
    }
