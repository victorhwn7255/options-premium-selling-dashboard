"""
estimators.py — v2 integration layer over theta_core (Phase A, silent).

Bridges the stored `daily_bars` OHLC series to the pure Module-A estimators in
`theta_core` (the ported golden master). Pure functions, matching calculator.py's
style — no I/O, no framework deps. EWMAs are always **recomputed from bars** (no
persisted EWMA state): corruption-proof, trivially backfillable, deterministic.

Consumed by forecast.py (pooled panel + forecaster) and, in Phase A3, by the
live scan in main.py.
"""

from __future__ import annotations

import math

import theta_core as tc


def bars_to_daily_inputs(bars: list[dict]) -> list[dict]:
    """Map an oldest→newest OHLC bar series to per-session daily inputs.

    Each bar is a dict with o/h/l/c (and date). The first bar has no prior
    close, so it produces no output — result length is len(bars) - 1.
    Returns dicts: {date, r, v, s_neg, s_pos} (v = GK+overnight variance proxy).
    """
    out: list[dict] = []
    for i in range(1, len(bars)):
        prev, b = bars[i - 1], bars[i]
        di = tc.daily_inputs(b["o"], b["h"], b["l"], b["c"], prev["c"])
        di["date"] = b["date"]
        out.append(di)
    return out


def replay_ewma(daily: list[dict]) -> tc.EwmaState:
    """Replay the full daily-input series into a fresh EwmaState and return the
    final state. Deterministic recompute-from-scratch (no persisted state)."""
    st = tc.EwmaState()
    for di in daily:
        st.update(di["v"], di["s_neg"])
    return st


def replay_ewma_series(daily: list[dict]) -> list[dict]:
    """Like replay_ewma, but snapshot the EWMA state after **each** session —
    the per-t feature source for the pooled training panel.

    Each snapshot: {date, v, s_neg, e_v:{m:..}, e_sneg:{m:..}, vbar}.
    """
    st = tc.EwmaState()
    out: list[dict] = []
    for di in daily:
        st.update(di["v"], di["s_neg"])
        out.append({
            "date": di["date"],
            "v": di["v"],
            "s_neg": di["s_neg"],
            "e_v": {m: st.v[m] for m in tc.EwmaState.COMS_V},
            "e_sneg": {m: st.sneg[m] for m in tc.EwmaState.COMS_SNEG},
            "vbar": st.vbar,
        })
    return out


def downside_accel(st: tc.EwmaState) -> float:
    """A_t = sqrt(E_5(s_neg) / E_25(s_neg)) — the sign-aware acceleration that
    feeds gate G3 (spec Module B). Returns 1.0 (neutral) if undefined."""
    a, b = st.sneg.get(5), st.sneg.get(25)
    if not a or not b or b <= 0:
        return 1.0
    return math.sqrt(a / b)


def concentration_10d(daily: list[dict]) -> float:
    """max(s_neg) / sum(s_neg) over the trailing 10 sessions — the jump-vs-
    diffusive discriminator feeding the transient tag. 0.0 if no downside."""
    window = [di["s_neg"] for di in daily[-10:]]
    total = sum(window)
    return (max(window) / total) if total > 0 else 0.0


def yz21_series(bars: list[dict], n: int = 21) -> list[dict]:
    """Yang-Zhang level vol at each session with ≥ n+1 trailing bars (display /
    percentile use only — the forecast, not YZ, drives decisions). Returns
    {date, yz} with yz annualized."""
    o = [b["o"] for b in bars]
    h = [b["h"] for b in bars]
    l = [b["l"] for b in bars]
    c = [b["c"] for b in bars]
    out: list[dict] = []
    for i in range(n, len(bars)):
        yz = tc.yang_zhang(o[: i + 1], h[: i + 1], l[: i + 1], c[: i + 1], n=n)
        out.append({"date": bars[i]["date"], "yz": yz})
    return out
