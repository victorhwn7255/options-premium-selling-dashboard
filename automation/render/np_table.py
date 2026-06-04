"""Render the Naked Puts `metrics-logs.md` data table from a raw scan.

Ports the frontend's input transform (`frontend/src/lib/scoring.ts:convertApiTicker`)
and output format (`frontend/src/components/Leaderboard.tsx:handleCopy`), operating on
the raw snake_case `TickerResult` dicts as served by `/api/scan/latest` or stored in the
SQLite `scan_results.tickers` JSON. Output byte-matches the dashboard's clipboard string.
"""
from __future__ import annotations

from ._fmt import fixed

NP_HEADER = "| Ticker | Score | IV | IV Pct | RV30 | VRP | Term Slope | RV Accel | 25Δ Skew | θ/V | Earnings | Regime |"
NP_SEP = "|--------|-------|----|--------|------|-----|------------|----------|----------|-----|----------|--------|"

# frontend/src/lib/scoring.ts:23-32
_RECOMMENDATION_MAP = {
    "SELL PREMIUM": "SELL",
    "CONDITIONAL": "CONDITIONAL",
    "WATCHLIST": "WATCHLIST",
    "AVOID": "AVOID",
    "REDUCE SIZE": "AVOID",
    "NO DATA": "NO DATA",
}


def map_recommendation(rec: str) -> str:
    return _RECOMMENDATION_MAP.get(rec, "NO EDGE")


def transform_ticker(t: dict) -> dict:
    """Port of convertApiTicker for the fields that feed the table (raw snake_case in)."""
    score = t["signal_score"]
    action = map_recommendation(t["recommendation"])
    action_reason = None
    dte = t.get("earnings_dte")
    is_etf = bool(t.get("is_etf"))

    # Earnings gate (scoring.ts:55-60): DTE <= 14 on a non-ETF -> score 0 / SKIP
    if dte is not None and dte <= 14 and not is_etf:
        action_reason = f"Earnings in {dte}d"
        score = 0
        action = "SKIP"

    theta, vega = t.get("theta"), t.get("vega")
    theta_vega = (
        abs(theta / vega)
        if (theta is not None and vega is not None and vega != 0)
        else None
    )
    return {
        "sym": t["ticker"],
        "score": int(score),
        "iv": t.get("iv_current"),
        "iv_pct": t.get("iv_percentile"),
        "rv30": t.get("rv30"),
        "vrp": t.get("vrp"),
        "term_slope": t.get("term_slope"),
        "rv_accel": t.get("rv_acceleration"),
        "skew": t.get("skew_25d"),
        "theta_vega": theta_vega,
        "earnings_dte": dte,
        "is_etf": is_etf,
        "action": action,
        "action_reason": action_reason,
        "regime": t.get("regime"),
    }


def format_np_row(x: dict) -> str:
    """Reproduce Leaderboard.tsx:302-305 byte-for-byte."""
    iv = fixed(x["iv"], 1) if x["iv"] is not None else "N/A"
    vrp = fixed(x["vrp"], 1) if x["vrp"] is not None else "N/A"
    tv = fixed(x["theta_vega"], 2) if x["theta_vega"] is not None else "—"
    earnings = f"{x['earnings_dte']}d" if x["earnings_dte"] else ("ETF" if x["is_etf"] else "TBD")
    regime = x["action_reason"] if x["action"] == "SKIP" else f"{x['action']} ({x['regime']})"
    return (
        f"| {x['sym']} | {x['score']} | {iv} | {fixed(x['iv_pct'], 0)} | {fixed(x['rv30'], 1)} | "
        f"{vrp} | {fixed(x['term_slope'], 2)} | {fixed(x['rv_accel'], 2)} | {fixed(x['skew'], 1)} | "
        f"{tv} | {earnings} | {regime} |"
    )


def render_np_table(tickers_raw: list[dict]) -> str:
    """Full table block: header + separator + score-descending rows (no `## date` heading)."""
    rows = [transform_ticker(t) for t in tickers_raw]
    # Stable sort by score descending; SKIP / NO DATA (score 0) sink to the bottom in API order.
    rows.sort(key=lambda r: r["score"], reverse=True)
    return "\n".join([NP_HEADER, NP_SEP, *(format_np_row(r) for r in rows)])
