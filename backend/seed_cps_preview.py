"""
PREVIEW-ONLY: seed the cps_scan_responses cache with a plausible response
so the populated CPS tab can be reviewed in the browser before merging
Phase 1-5 to production.

NOT FOR COMMIT. Add to .gitignore or delete after preview is done.

Data inspiration: the past 5 trading days (May 5–May 11) where SPY / QQQ / IWM
showed varied CPS-eligibility. We synthesise candidates that exercise every
UI state (SELL_CPS, WATCH_CPS, high-c/w warning, multi-day confirmation).

Usage:
    python backend/seed_cps_preview.py            # seed the preview
    python backend/seed_cps_preview.py --revert   # delete the preview row

Revert manually if needed:
    sqlite3 backend/data/vol_history.db \\
        "DELETE FROM cps_scan_responses WHERE scan_date = '2026-05-12-preview';"
"""

import argparse
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import save_cps_scan_response, get_latest_scan, get_connection

PREVIEW_SCAN_DATE = "2026-05-12-preview"


def _build_leg(strike, delta, bid, ask, oi, vol, iv=18.0, expiration="2026-06-20", dte=39):
    mid = round((bid + ask) / 2, 4)
    return {
        "strike": strike,
        "expiration": expiration,
        "dte": dte,
        "delta": delta,
        "bid": bid,
        "ask": ask,
        "mid": mid,
        "iv": iv,
        "theta": -0.05,
        "vega": 0.10,
        "open_interest": oi,
        "volume": vol,
        "bid_ask_ratio": round((ask - bid) / mid, 4),
    }


def _make_candidate(
    ticker: str,
    spot: float,
    action: str,
    base_score: float,
    short_strike: float,
    long_strike: float,
    short_bid: float,
    short_ask: float,
    long_bid: float,
    long_ask: float,
    iv_pct: float,
    rv_accel: float,
    rv_status: str,
    term_slope: float,
    vrp: float,
    vrp_ratio: float,
    skew: float,
    consec_days: int,
    exact_consec: int,
    vrp_z: float | None,
    notes: list[str] | None = None,
    warnings: list[str] | None = None,
    rejection_reasons: list[str] | None = None,
    regime: str = "NORMAL",
    overlay_status: str = "NORMAL",
    atr14: float = 4.5,
    dte: int = 39,
    expiration: str = "2026-06-20",
):
    short_leg = _build_leg(short_strike, -0.20, short_bid, short_ask, 1850, 320,
                           iv=iv_pct * 0.32, expiration=expiration, dte=dte)
    long_leg = _build_leg(long_strike, -0.10, long_bid, long_ask, 1420, 210,
                          iv=iv_pct * 0.34, expiration=expiration, dte=dte)
    net_credit = round(short_leg["mid"] - long_leg["mid"], 4)
    width = round(short_strike - long_strike, 4)
    max_loss = round(width - net_credit, 4)
    credit_to_width = round(net_credit / width, 4) if width > 0 else 0.0
    breakeven = round(short_strike - net_credit, 4)
    em = round(spot * (iv_pct / 100.0) * math.sqrt(dte / 365.0), 4)

    return {
        "ticker": ticker,
        "spot": spot,
        "action": action,
        "base_score": base_score,
        "rank_score": base_score,
        "regime": regime,
        "expiration": expiration,
        "dte": dte,
        "short_put": short_leg,
        "long_put": long_leg,
        "width": width,
        "net_credit": net_credit,
        "max_loss": max_loss,
        "credit_to_width": credit_to_width,
        "breakeven": breakeven,
        "atr14": atr14,
        "expected_move": em,
        "expected_move_lower": round(spot - em, 4),
        "width_to_atr": round(width / atr14, 4) if atr14 > 0 else None,
        "width_to_expected_move": round(width / em, 4) if em > 0 else None,
        "vrp": vrp,
        "vrp_ratio": vrp_ratio,
        "vrp_zscore_60d": vrp_z,
        "iv_percentile": iv_pct,
        "term_slope": term_slope,
        "rv_accel": rv_accel,
        "rv_accel_status": rv_status,
        "skew": skew,
        "earnings_dte": None,
        "consecutive_sell_days": consec_days,
        "exact_spread_consecutive_days": exact_consec,
        "vix": 18.4,
        "vix3m": 20.6,
        "vvix": 96.3,
        "regime_overlay_status": overlay_status,
        "notes": notes or [],
        "warnings": warnings or [],
        "rejection_reasons": rejection_reasons or [],
    }


def build_preview_response():
    """Compose a realistic CPS response showcasing all populated UI states."""
    # Pull May 11 spots from the synced production scan for ticker context.
    latest = get_latest_scan()
    by_ticker = {t["ticker"]: t for t in latest["tickers"]}
    spy_spot = by_ticker.get("SPY", {}).get("price", 482.50)
    qqq_spot = by_ticker.get("QQQ", {}).get("price", 514.20)
    iwm_spot = by_ticker.get("IWM", {}).get("price", 214.80)

    # SPY — SELL_CPS (best case) — passes every filter + 2-day confirmation
    spy = _make_candidate(
        ticker="SPY", spot=spy_spot,
        action="SELL_CPS", base_score=72,
        short_strike=480, long_strike=476,
        short_bid=2.05, short_ask=2.10,
        long_bid=0.78, long_ask=0.82,
        iv_pct=55.0, rv_accel=0.78, rv_status="Excellent",
        term_slope=0.63, vrp=1.6, vrp_ratio=1.17, skew=2.6,
        consec_days=2, exact_consec=1, vrp_z=1.34,
        notes=["Confirmed: ticker passed all filters 2 consecutive scans."],
    )

    # QQQ — WATCH_CPS — only 1-day confirmation; full UI showcase of the
    # "filters pass but waiting for confirmation" note.
    qqq = _make_candidate(
        ticker="QQQ", spot=qqq_spot,
        action="WATCH_CPS", base_score=58,
        short_strike=510, long_strike=506,
        short_bid=2.40, short_ask=2.50,
        long_bid=1.15, long_ask=1.25,
        iv_pct=64.0, rv_accel=0.95, rv_status="Good",
        term_slope=0.77, vrp=4.0, vrp_ratio=1.23, skew=2.4,
        consec_days=1, exact_consec=1, vrp_z=0.92,
        notes=[
            "consecutive_sell_days 1 < 2 — needs another eligible day for SELL_CPS.",
        ],
    )

    # IWM — WATCH_CPS — high c/w warning (>35%) to exercise the warning chip
    iwm = _make_candidate(
        ticker="IWM", spot=iwm_spot,
        action="WATCH_CPS", base_score=62,
        short_strike=212, long_strike=209,
        short_bid=1.55, short_ask=1.60,
        long_bid=0.30, long_ask=0.35,
        iv_pct=50.0, rv_accel=1.05, rv_status="Acceptable",
        term_slope=0.80, vrp=2.0, vrp_ratio=1.18, skew=2.4,
        consec_days=2, exact_consec=1, vrp_z=0.41,
        warnings=[
            "High credit/width may indicate elevated tail risk. "
            "Verify regime, skew, and RV Accel before acting.",
        ],
        notes=[
            "60d VRP z-score 0.41 < 0.5 floor — downgraded to WATCH from SELL_CPS.",
        ],
    )

    return {
        "scan_date": PREVIEW_SCAN_DATE,
        "market_regime": "THE PLAYOFFS",
        "cps_universe": ["SPY", "QQQ", "IWM"],
        "regime_overlay": {
            "status": "NORMAL",
            "vix": 18.4,
            "vix3m": 20.6,
            "vvix": 96.3,
            "vix_backwardation": False,
            "warnings": [],
        },
        "candidates": [spy, qqq, iwm],
        "message": None,
        "rejection_summary": {
            "checked": 3,
            "actionable": 3,
            "rejected_by_base_gate": 0,
            "rejected_by_construction": 0,
            "rejected_by_execution": 0,
            "rejected_by_overlay": 0,
            "rejected_by_confirmation": 0,
        },
    }


def revert():
    conn = get_connection()
    conn.execute(
        "DELETE FROM cps_scan_responses WHERE scan_date = ?",
        (PREVIEW_SCAN_DATE,),
    )
    conn.commit()
    conn.close()
    print(f"Deleted preview row scan_date={PREVIEW_SCAN_DATE}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--revert", action="store_true", help="Delete the preview row")
    args = ap.parse_args()
    if args.revert:
        revert()
        return
    response = build_preview_response()
    save_cps_scan_response(PREVIEW_SCAN_DATE, response)
    print("Seeded CPS preview")
    print(f"  scan_date: {PREVIEW_SCAN_DATE}")
    print(f"  candidates: {len(response['candidates'])}")
    print(f"  actions: {[c['action'] for c in response['candidates']]}")
    print(f"  overlay: {response['regime_overlay']['status']} "
          f"(VIX {response['regime_overlay']['vix']} / "
          f"VIX3M {response['regime_overlay']['vix3m']} / "
          f"VVIX {response['regime_overlay']['vvix']})")
    print()
    print("Refresh http://localhost:3002 → Credit Put Spreads tab.")
    print("Revert with: python backend/seed_cps_preview.py --revert")


if __name__ == "__main__":
    main()
