"""Render the deterministic part of a `credit-put-spreads.md` entry from a raw CPS scan.

Ports `frontend/src/components/CreditPutSpreadsTab.tsx:buildScanMarkdown`, operating on the
raw snake_case response from `/api/credit-put-spreads/latest` or the stored
`cps_scan_responses.response_json`. Produces the scan-summary line, overlay line, and
candidates table (the `**Notable:**` paragraph is written separately by Claude).
"""
from __future__ import annotations

from ._fmt import fixed, round_half_up

CPS_HEADER = "| # | Ticker | Action | Days | Score | C/W | Credit | Width | Max Loss | RV Status | Notes |"
CPS_SEP = "|---|--------|--------|------|-------|------|--------|-------|----------|-----------|-------|"


def _scan_summary(s: dict | None) -> str:
    if not s:
        return "**Scan summary:** (unavailable)"
    return (
        f"**Scan summary:** Checked {s['checked']} / {s['actionable']} actionable / "
        f"{s['rejected_by_base_gate']} base_gate / {s['rejected_by_construction']} construction / "
        f"{s['rejected_by_execution']} execution / {s['rejected_by_overlay']} overlay / "
        f"{s['rejected_by_confirmation']} confirmation"
    )


def _overlay_line(o: dict) -> str:
    bw = o.get("vix_backwardation")
    term = "—" if bw is None else ("Backwardation" if bw else "Contango")
    vix = fixed(o.get("vix"), 2) or "—"
    vix3m = fixed(o.get("vix3m"), 2) or "—"
    vvix = fixed(o.get("vvix"), 1) or "—"
    return f"**Overlay:** VIX {vix} / VIX3M {vix3m} / VVIX {vvix} — {o['status']}, {term}"


def _candidate_row(i: int, c: dict) -> str:
    action = c["action"].replace("_CPS", "")
    w = c["width"]
    width = f"${fixed(w, 0)}" if float(w).is_integer() else f"${fixed(w, 2)}"
    warnings = c.get("warnings") or []
    # JS does .trim().slice(0,18); the 18-char cut can leave a trailing space (e.g.
    # "High credit/width "). The dashboard keeps it, but the history files use the
    # trimmed style, so strip again after slicing to keep committed markdown clean.
    note = (warnings[0] if warnings else "").split("—")[0].strip()[:18].strip() or "—"
    return (
        f"| {i} | {c['ticker']} | {action} | {c['consecutive_sell_days']}d | "
        f"{round_half_up(c['base_score'])} | {fixed(c['credit_to_width'] * 100, 1)}% | "
        f"${fixed(c['net_credit'], 2)} | {width} | ${fixed(c['max_loss'], 2)} | "
        f"{c['rv_accel_status'] or '—'} | {note} |"
    )


def render_cps_snapshot(cps: dict) -> str:
    """Scan-summary + overlay + (if any) candidates table. No heading, no Notable paragraph."""
    lines = [_scan_summary(cps.get("rejection_summary")), _overlay_line(cps["regime_overlay"])]
    candidates = cps.get("candidates") or []
    if candidates:
        lines += ["", CPS_HEADER, CPS_SEP]
        lines += [_candidate_row(i, c) for i, c in enumerate(candidates, 1)]
    return "\n".join(lines)
