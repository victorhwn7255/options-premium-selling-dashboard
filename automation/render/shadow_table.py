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

SHADOW_HEADER = ("| Ticker | v1 Action | v1 Regime | v2 Eligible | v2 Gate | Divergence | "
                 "sigma_fwd | FVRP | z | 1M/3M | accel_dn |")
SHADOW_SEP = ("|--------|-----------|-----------|-------------|---------|------------|"
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


def shadow_summary_line(s: dict | None) -> str:
    """The deterministic `**Shadow summary:**` header (also reused verbatim by v2-briefings).

    Pulls agreement/divergence counts, the index-sleeve gating rate (v1 vs v2 — the G2 canary),
    gate oscillation (v1 vs v2), and warm coverage from the `/api/shadow/summary` dict (or the
    per-day counts at backfill). Missing fields degrade to '—' rather than raising.
    """
    if not s:
        return "**Shadow summary:** (unavailable)"
    dc = s.get("divergence_counts") or {}
    n = s.get("n_ticker_days", 0)
    return (
        f"**Shadow summary:** Checked {n} / {dc.get('AGREE', 0)} agree / "
        f"{dc.get('V2_STRICTER', 0)} V2_STRICTER / {dc.get('V2_LOOSER', 0)} V2_LOOSER / "
        f"{dc.get('STATE_MISMATCH', 0)} state_mismatch / {dc.get('NODATA_SKEW', 0)} nodata | "
        f"index-gating v1 {_pct(s.get('index_gating_rate_v1'))} vs v2 {_pct(s.get('index_gating_rate_v2'))} | "
        f"oscillation v1 {_osc(s.get('oscillation_v1'))} vs v2 {_osc(s.get('oscillation_v2'))} | "
        f"warm {_pct(s.get('warm_coverage'))}"
    )


def _shadow_row(r: dict) -> str:
    return (
        f"| {r['ticker']} | {r.get('v1_action') or '—'} | {r.get('v1_regime') or '—'} | "
        f"{_yn(r.get('v2_eligible'))} | {r.get('v2_gate_state') or '—'} | "
        f"{r.get('divergence_class') or '—'} | {fixed(r.get('sigma_fwd'), 3) or '—'} | "
        f"{fixed(r.get('fvrp_ratio'), 2) or '—'} | {_signed(r.get('fvrp_z'), 2)} | "
        f"{fixed(r.get('slope_1m3m'), 3) or '—'} | {fixed(r.get('accel_dn'), 3) or '—'} |"
    )


def render_shadow_snapshot(rows: list[dict], summary: dict | None) -> str:
    """Shadow-summary line + (if any) the v2-vs-v1 divergence table. No heading.

    Rows are sorted decision-changing-first (V2_STRICTER, then V2_LOOSER), then by ticker.
    """
    lines = [shadow_summary_line(summary)]
    if rows:
        srt = sorted(rows, key=lambda r: (_RANK.get(r.get("divergence_class"), 2), r.get("ticker") or ""))
        lines += ["", SHADOW_HEADER, SHADOW_SEP]
        lines += [_shadow_row(r) for r in srt]
    return "\n".join(lines)
