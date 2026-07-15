"""Render the deterministic part of a `v2-metrics-logs.md` entry from the v2-shadow surface.

The v2 analog of `render_cps_snapshot` (whose structure this mirrors exactly): a
`**Shadow summary:**` header line + a per-ticker v2-vs-v1 divergence table. Operates on the
raw rows from `/api/shadow/diff` (or the DB-backfill join of `shadow_diff` + `daily_iv`) and
the aggregate dict from `/api/shadow/summary` (or the per-day counts computed at backfill).

Advisory only — Phase A of the v1->v2 arc; this changes no live decision. The `**Calibration
read:**` prose paragraph is written separately by Claude (see v2-briefings.md).
"""
from __future__ import annotations

from ._fmt import fixed

SHADOW_HEADER = ("| Ticker | v1 Action | v1 Regime | Earnings | v2 Eligible | v2 Gate | Divergence | "
                 "sigma_fwd | FVRP | z | 1M/3M | accel_dn |")
SHADOW_SEP = ("|--------|-----------|-----------|----------|-------------|---------|------------|"
              "-----------|------|------|-------|----------|")

# Decision-changing classes float to the top of the table (mirrors the backend ORDER BY).
_RANK = {"V2_STRICTER": 0, "V2_LOOSER": 1}


def _pct(x) -> str:
    """A 0-1 rate as a whole-percent string ('45%'); '—' when unavailable."""
    return f"{fixed(x * 100, 0)}%" if x is not None else "—"


def _osc(x) -> str:
    """A mean-transitions-per-ticker float to 2 dp; '—' when unavailable."""
    return fixed(x, 2) if x is not None else "—"


def _signed(x, n: int) -> str:
    """Signed fixed-dp ('+1.20' / '-0.50'); '—' when None."""
    if x is None:
        return "—"
    s = fixed(x, n)
    return s if s.startswith("-") else "+" + s


def _yn(x) -> str:
    """Boolean (or 0/1) eligibility as Yes/No; '—' when None."""
    if x is None:
        return "—"
    return "Yes" if x else "No"


def compute_day_flips(rows: list[dict], prev_rows: list[dict] | None) -> dict | None:
    """True day-over-day gate churn: how many tickers changed v1 regime / v2 gate state vs the
    prior session, out of those comparable on both days (non-null state both sides).

    Returns {"v1": (flips, comparable), "v2": (flips, comparable)}, or None when there is no
    prior day to compare against (first entry, or the prior rows were unavailable) — callers
    then omit the segment entirely, matching pre-2026-07-15 entries.
    """
    if not rows or not prev_rows:
        return None
    prev = {r.get("ticker"): r for r in prev_rows}
    out = {}
    for key, col in (("v1", "v1_regime"), ("v2", "v2_gate_state")):
        flips = comparable = 0
        for r in rows:
            p = prev.get(r.get("ticker"))
            cur_s, prev_s = r.get(col), (p or {}).get(col)
            if p is None or cur_s is None or prev_s is None:
                continue
            comparable += 1
            if cur_s != prev_s:
                flips += 1
        out[key] = (flips, comparable)
    return out if any(c for _, c in out.values()) else None


def _flips_str(f: tuple[int, int]) -> str:
    return f"{f[0]}/{f[1]}"


def shadow_summary_line(s: dict | None, flips: dict | None = None) -> str:
    """The deterministic `**Shadow summary:**` header (also reused verbatim by v2-briefings).

    Pulls agreement/divergence counts, the index-sleeve gating rate (v1 vs v2 — the G2 canary),
    gate oscillation (v1 vs v2), and warm coverage from the `/api/shadow/summary` dict (or the
    per-day counts at backfill). Missing fields degrade to '—' rather than raising. `flips`
    (from `compute_day_flips`) appends the true day-over-day churn; None omits the segment
    (first entry / prior day unavailable / pre-2026-07-15 entries).
    """
    if not s:
        return "**Shadow summary:** (unavailable)"
    dc = s.get("divergence_counts") or {}
    n = s.get("n_ticker_days", 0)
    line = (
        f"**Shadow summary:** Checked {n} / {dc.get('AGREE', 0)} agree / "
        f"{dc.get('V2_STRICTER', 0)} V2_STRICTER / {dc.get('V2_LOOSER', 0)} V2_LOOSER / "
        f"{dc.get('STATE_MISMATCH', 0)} state_mismatch / {dc.get('NODATA_SKEW', 0)} nodata | "
        f"index-gating v1 {_pct(s.get('index_gating_rate_v1'))} vs v2 {_pct(s.get('index_gating_rate_v2'))} | "
        f"oscillation v1 {_osc(s.get('oscillation_v1'))} vs v2 {_osc(s.get('oscillation_v2'))} | "
        f"warm {_pct(s.get('warm_coverage'))}"
    )
    if flips:
        line += (f" | day-flips v1 {_flips_str(flips['v1'])} vs v2 {_flips_str(flips['v2'])}")
    return line


def _earnings_cell(r: dict, earnings_by_ticker: dict | None) -> str:
    """Days-to-earnings for the v1-UI reality check ('15d'); 'ETF' = exempt from the earnings
    gate in both engines; 'TBD' = date unknown. Same vocabulary as the NP table's column."""
    if r.get("is_etf"):
        return "ETF"
    dte = (earnings_by_ticker or {}).get(r.get("ticker"))
    return f"{dte}d" if dte is not None else "TBD"


def _shadow_row(r: dict, earnings_by_ticker: dict | None = None) -> str:
    return (
        f"| {r['ticker']} | {r.get('v1_action') or '—'} | {r.get('v1_regime') or '—'} | "
        f"{_earnings_cell(r, earnings_by_ticker)} | "
        f"{_yn(r.get('v2_eligible'))} | {r.get('v2_gate_state') or '—'} | "
        f"{r.get('divergence_class') or '—'} | {fixed(r.get('sigma_fwd'), 3) or '—'} | "
        f"{fixed(r.get('fvrp_ratio'), 2) or '—'} | {_signed(r.get('fvrp_z'), 2)} | "
        f"{fixed(r.get('slope_1m3m'), 3) or '—'} | {fixed(r.get('accel_dn'), 3) or '—'} |"
    )


def render_shadow_snapshot(rows: list[dict], summary: dict | None,
                           earnings_by_ticker: dict | None = None,
                           flips: dict | None = None) -> str:
    """Shadow-summary line + (if any) the v2-vs-v1 divergence table. No heading.

    Rows are sorted decision-changing-first (V2_STRICTER, then V2_LOOSER), then by ticker.
    `earnings_by_ticker` maps ticker -> earnings_dte from the same day's NP scan payload
    (the shadow_diff rows themselves don't carry it); `flips` comes from `compute_day_flips`.
    """
    lines = [shadow_summary_line(summary, flips)]
    if rows:
        srt = sorted(rows, key=lambda r: (_RANK.get(r.get("divergence_class"), 2), r.get("ticker") or ""))
        lines += ["", SHADOW_HEADER, SHADOW_SEP]
        lines += [_shadow_row(r, earnings_by_ticker) for r in srt]
    return "\n".join(lines)
