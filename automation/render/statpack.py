"""Compute the verified stat-pack handed to Claude for the daily briefing.

Ports `frontend/src/components/RegimeBanner.tsx:computeRegime` (regime label + aggregates,
over the *eligible* set = action not in {SKIP, NO DATA}) and adds day-over-day deltas vs the
prior day's NP table parsed from the markdown. Every number Claude needs is computed here so
the LLM never does arithmetic — it only writes prose around these values.
"""
from __future__ import annotations

from ._fmt import fixed
from .np_table import transform_ticker


def _signed_vrp(avg_vrp: float) -> str:
    """Match the banner's `avgVRP.toFixed(1)` (JS rounding), with a leading + for non-negatives."""
    s = fixed(avg_vrp, 1)
    return s if s.startswith("-") else f"+{s}"


def _regime_label(danger_pct: float, stress_pct: float, avg_vrp: float, avg_slope: float) -> str:
    # Precedence from RegimeBanner.tsx:39-62
    if danger_pct > 0.40:
        return "OFF SEASON"
    if stress_pct > 0.25:
        return "REGULAR SEASON"
    if avg_vrp > 8 and avg_slope < 0.90:
        return "THE FINALS"
    return "THE PLAYOFFS"


def compute_statpack(tickers_raw: list[dict], prior_np: dict | None = None) -> dict:
    """tickers_raw: today's raw scan tickers. prior_np: {ticker: {score, ...}} from yesterday's
    parsed markdown table (or None on the first day / when unavailable)."""
    rows = [transform_ticker(t) for t in tickers_raw]
    eligible = [r for r in rows if r["action"] not in ("SKIP", "NO DATA")]
    n = len(eligible) or 1  # avoid div-by-zero; matches the all-excluded guard's intent

    avg_vrp = sum((r["vrp"] or 0) for r in eligible) / n
    avg_slope = sum(r["term_slope"] for r in eligible) / n
    avg_accel = sum(r["rv_accel"] for r in eligible) / n

    danger = sum(1 for r in eligible if r["regime"] == "DANGER")
    stress = sum(1 for r in eligible if r["regime"] in ("DANGER", "CAUTION"))
    danger_pct = danger / n
    stress_pct = stress / n

    s_count = sum(1 for r in eligible if r["action"] == "SELL")
    c_count = sum(1 for r in eligible if r["action"] == "CONDITIONAL")
    w_count = sum(1 for r in eligible if r["action"] == "WATCHLIST")
    tradeable = s_count + c_count  # banner definition (WATCHLIST excluded)

    neg_vrp = sum(1 for r in eligible if (r["vrp"] is not None and r["vrp"] < 0))
    neg_vrp_pct = round(100 * neg_vrp / n)

    tradeable_str = f"{s_count}S / {c_count}C" + (f" + {w_count}W" if w_count else "")

    # Day-over-day score deltas vs the prior day's parsed NP table.
    deltas = []
    if prior_np:
        for r in sorted(rows, key=lambda x: x["score"], reverse=True):
            prev = prior_np.get(r["sym"], {}).get("score")
            if prev is None:
                continue
            d = r["score"] - prev
            if abs(d) >= 3:
                deltas.append({"ticker": r["sym"], "prev": prev, "today": r["score"], "delta": d})

    return {
        "regime_label": _regime_label(danger_pct, stress_pct, avg_vrp, avg_slope),
        "tradeable_str": tradeable_str,
        "avg_vrp_str": _signed_vrp(avg_vrp),
        "aggregates": {
            "avg_vrp": round(avg_vrp, 2),
            "avg_term_slope": round(avg_slope, 3),
            "avg_rv_accel": round(avg_accel, 3),
            "eligible_count": len(eligible),
            "danger_count": danger,
            "stress_count": stress,
            "danger_pct": round(danger_pct, 3),
            "stress_pct": round(stress_pct, 3),
            "neg_vrp_pct": neg_vrp_pct,
            "sell": s_count,
            "conditional": c_count,
            "watchlist": w_count,
            "tradeable": tradeable,
        },
        "day_over_day": deltas,
    }
