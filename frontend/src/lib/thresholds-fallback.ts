// GENERATED from GET /api/thresholds (backend/thresholds.py) on 2026-09-03 — the offline fallback for the
// "How to use" guide. Regenerate with:  python -c "import thresholds,json;print(json.dumps(thresholds.build_thresholds()))"
// The live endpoint always wins; this copy is only shown when the fetch fails (marked 'cached').
import type { Thresholds } from './types';

export const THRESHOLDS_FALLBACK: Thresholds = {
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
    "data_quality": "backend/calculator.py"
  },
  "v1_scorer": {
    "vrp_ratio_dead_zone": 1.15,
    "vrp_ratio_cap": 1.6,
    "vrp_points": 30,
    "iv_pct_floor": 30,
    "iv_pct_points": 25,
    "term_hinges": [
      0.85,
      1.0,
      1.15
    ],
    "term_points": [
      20,
      5,
      0
    ],
    "accel_hinges": [
      0.85,
      1.0,
      1.15
    ],
    "accel_points": [
      15,
      10,
      0
    ],
    "skew_nodes": [
      0,
      7,
      12,
      20
    ],
    "skew_points": 10,
    "sell": 65,
    "conditional": 45,
    "reduce_size": 55,
    "negative_vrp_cap": 54
  },
  "regime_per_ticker": {
    "danger_slope": 1.15,
    "caution_slope": 1.05,
    "caution_accel": 1.1,
    "caution_ivr": 90,
    "caution_ivr_accel": 1.1
  },
  "dashboard_regime": {
    "off_season_danger_pct": 0.4,
    "regular_season_stress_pct": 0.25,
    "finals_avg_vrp": 8,
    "finals_avg_slope": 0.9,
    "finals_ever_triggered": false
  },
  "earnings_gate_days": 14,
  "rv_accel_status": [
    {
      "max": 0.85,
      "label": "Excellent",
      "meaning": "vol decelerating — clean"
    },
    {
      "max": 1.0,
      "label": "Good",
      "meaning": "stable to declining — favourable"
    },
    {
      "max": 1.1,
      "label": "Acceptable",
      "meaning": "mildly rising — trade selectively"
    },
    {
      "max": 1.2,
      "label": "Caution",
      "meaning": "vol heating up — wait or require strong confirmation"
    },
    {
      "max": null,
      "label": "Avoid / Wait",
      "meaning": "vol spiking — no new naked entries"
    }
  ],
  "position_hints": [
    {
      "condition": "DANGER regime",
      "delta": "N/A",
      "structure": "No position",
      "dte": "N/A",
      "notional": "0%"
    },
    {
      "condition": "WATCHLIST (ratio < 1.15)",
      "delta": "N/A",
      "structure": "Wait for premium to expand",
      "dte": "N/A",
      "notional": "0%"
    },
    {
      "condition": "CAUTION regime",
      "delta": "10–15Δ",
      "structure": "Iron condor or wide put spread (defined risk only)",
      "dte": "21–30",
      "notional": "1–2%"
    },
    {
      "condition": "NORMAL · IV Rank ≥ 80 · VRP > 8",
      "delta": "16–20Δ",
      "structure": "Short strangle or jade lizard",
      "dte": "30–45",
      "notional": "2–5%"
    },
    {
      "condition": "NORMAL · IV Rank ≥ 80 · VRP > 4",
      "delta": "16–20Δ",
      "structure": "Iron condor or put credit spread",
      "dte": "30–45",
      "notional": "2–5%"
    },
    {
      "condition": "NORMAL · IV Rank ≥ 80 · VRP ≤ 4",
      "delta": "16–20Δ",
      "structure": "Put credit spread, strict width",
      "dte": "30–45",
      "notional": "2–5%"
    },
    {
      "condition": "NORMAL · IV Rank < 80",
      "delta": "20–30Δ",
      "structure": "Put credit spread, narrow width",
      "dte": "45–60",
      "notional": "2–3%"
    }
  ],
  "cps": {
    "universe": [
      "SPY",
      "QQQ",
      "IWM",
      "EEM",
      "GLD",
      "TLT",
      "XLE",
      "XLF",
      "XLV",
      "XLI",
      "XLB"
    ],
    "target_dte": 35,
    "min_dte": 30,
    "max_dte": 45,
    "target_short_delta": 0.2,
    "min_short_delta": 0.15,
    "max_short_delta": 0.25,
    "sell_credit_to_width": 0.25,
    "watch_credit_to_width": 0.1,
    "thin_premium_threshold": 0.18,
    "high_credit_to_width_warning": 0.35,
    "max_bid_ask_ratio": 0.2,
    "min_open_interest": 100,
    "min_volume": 25,
    "confirmation_days": 2,
    "vvix_caution": 110.0,
    "vvix_danger": 130.0,
    "vrp_zscore_60d_min": 0.5,
    "time_exit_dte": 21,
    "profit_target_frac": 0.5,
    "defensive_mark_multiple": 2.0,
    "event_risk_dte": 14,
    "pin_risk_dte": 2,
    "inherited_gates": {
      "earnings_dte": 14,
      "danger_slope": 1.15,
      "min_vrp_ratio": 1.15,
      "rv_accel_wait": 1.2,
      "extreme_skew": 20.0
    }
  },
  "exits": {
    "profit_target": 0.75,
    "profit_target_rv_rising": 0.5,
    "rv_rising_accel": 1.1,
    "time_exit_dte": 21,
    "tested_delta": 0.3,
    "spread_aware_premium_mult": 2.0,
    "spread_aware_sigma_mult": 1.5,
    "spread_aware_decay_to_dte": 7,
    "stop_loss": null,
    "danger_underwater_mult": 1.25
  },
  "sizing": {
    "kelly_fraction": 0.25,
    "kelly_min_trades": 20,
    "f_star_seed": 0.0,
    "dial_R_bounds": [
      0.25,
      1.25
    ],
    "dial_O_bounds": [
      0.5,
      1.5
    ],
    "cap_notional_frac": 1.0,
    "cap_margin_frac": 0.3,
    "cap_name_margin_frac": 0.08,
    "cap_name_stress_frac": 0.025,
    "cap_book_stress_frac": 0.15,
    "stress_spot_mult": 0.8,
    "stress_iv_mult": 2.0,
    "stress_days_elapsed": 5,
    "margin_alpha": 0.2
  },
  "v2": {
    "dead_zone_index": 1.2,
    "dead_zone_single": 1.15,
    "abs_premium_floor_volpts": 2.0,
    "g1_earnings_gate_days": 14,
    "g2_caution_in": 1.0,
    "g2_caution_out": 0.98,
    "g2_danger_in": 1.05,
    "g2_danger_out": 1.02,
    "g3_in": 1.1,
    "g3_out": 1.05,
    "g3_concentration": 0.5,
    "confirm_days": 2,
    "transient_blackout_days": 3,
    "veto_denominator": "sigma_fwd",
    "max_spread_over_mid": 0.1,
    "max_rtc_over_capture": 0.25
  },
  "data_quality": {
    "min_atm_contracts": 3,
    "max_spread_ratio": 0.5,
    "max_iv": 2.0
  }
};
