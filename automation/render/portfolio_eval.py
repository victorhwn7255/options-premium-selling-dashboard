"""Render the deterministic header of a `portfolio-evals.md` entry from the journal book.

The portfolio-eval analog of `render_shadow_snapshot` / `render_cps_snapshot`: a
`**Book summary:**` line + a per-open-position table + (if any) a closed-today post-mortem
line. Operates on the book dict from `db_source.read_book_by_date` (open positions with their
latest mark + parsed checklist, plus positions closed on the eval date) and the same day's
scan rows (regime / v1 action / v2 gate / FVRP context).

Flags are RECOMPUTED here (not stored) by mirroring `backend/positions_api.compute_flags` —
the marks table carries the inputs (capture_pct, dte, earnings_dte, unrealized_pnl,
short_delta, underlying_close) but not the flags, which the API derives at read time.

Advisory only — this changes no live decision and touches no CONFIG/eligibility/scoring. The
prose evaluation paragraph is written separately by Claude (see portfolio-evals.md).
"""
from __future__ import annotations

from ._fmt import fixed

# Journal management-rule defaults (mirror backend/positions_api.py DEFAULT_* constants).
DEFAULT_TARGET_CAPTURE = 0.75
DEFAULT_EXIT_DTE = 21

BOOK_HEADER = ("| # | Ticker | Structure | Strikes | Expiry | Qty | Credit | Mark | uPnL | "
               "Capture | DTE | Δ | Regime | v1 Action | v2 Gate | FVRP | Flags |")
BOOK_SEP = ("|---|--------|-----------|---------|--------|-----|--------|------|------|"
            "---------|-----|---|--------|-----------|---------|------|-------|")


def compute_flags(pos: dict, mark: dict | None, trow: dict | None,
                  today: str) -> list[dict]:
    """Management flags for one open position — a faithful port of
    `backend/positions_api.compute_flags` (each flag cites the exit rule it comes from).
    Recomputed here because the marks table does not persist the flags."""
    flags: list[dict] = []
    target = pos.get("target_capture") or DEFAULT_TARGET_CAPTURE
    exit_dte = pos.get("exit_dte_plan") or DEFAULT_EXIT_DTE
    rv_accel = (trow or {}).get("rv_acceleration")

    if pos.get("expiry") and pos["expiry"] < today:
        flags.append({"code": "PENDING_SETTLEMENT",
                      "detail": f"expired {pos['expiry']} — confirm fills/assignment",
                      "rule": "settlement facts live at the broker; never auto-closed"})
    if not mark:
        return flags

    cap = mark.get("capture_pct")
    if cap is not None:
        eff_target = 0.50 if (rv_accel is not None and rv_accel > 1.10) else target
        if cap >= eff_target:
            flags.append({"code": "PROFIT_TARGET",
                          "detail": f"capture {cap:.0%} >= target {eff_target:.0%}"
                                    + (" (50% variant: RV accel > 1.10)" if eff_target == 0.50 else ""),
                          "rule": "strategy_v1 exits: take 75% in NORMAL / 50% when RV is rising"})
    if mark.get("dte") is not None and mark["dte"] <= exit_dte:
        flags.append({"code": "TIME_EXIT", "detail": f"DTE {mark['dte']} <= plan {exit_dte}",
                      "rule": "strategy_v1 exits: close at 21 DTE — gamma outgrows theta"})
    if (mark.get("earnings_dte") is not None and mark.get("dte") is not None
            and 0 <= mark["earnings_dte"] <= mark["dte"]):
        flags.append({"code": "EARNINGS_WALL",
                      "detail": f"earnings in {mark['earnings_dte']}d, inside remaining {mark['dte']}d",
                      "rule": "earnings gate: binary gap risk no premium pays for"})
    if ((trow or {}).get("regime") == "DANGER"
            and mark.get("unrealized_pnl") is not None and mark["unrealized_pnl"] < 0):
        flags.append({"code": "DANGER_UNDERWATER",
                      "detail": f"regime DANGER with unrealized {mark['unrealized_pnl']:+.0f}",
                      "rule": "ADR-refined exit: leave DANGER names only when underwater"})
    tested = False
    if mark.get("underlying_close") is not None and pos.get("short_strike") is not None:
        tested = mark["underlying_close"] <= pos["short_strike"]
    if not tested and mark.get("short_delta") is not None:
        tested = abs(mark["short_delta"]) >= 0.30
    if tested:
        flags.append({"code": "TESTED",
                      "detail": f"spot {mark.get('underlying_close')} vs short strike "
                                f"{pos.get('short_strike')} (Δ {mark.get('short_delta')})",
                      "rule": "short strike under pressure — defend/roll decision point"})
    return flags


# ── formatting helpers ──────────────────────────────────────────────────────
def _usd(x, dp: int = 0) -> str:
    """A dollar amount with thousands separators ('$1,234'); '—' when None."""
    if x is None:
        return "—"
    return "$" + f"{float(x):,.{dp}f}"


def _signed_usd(x) -> str:
    """A signed dollar P&L ('+$310' / '-$120'); '—' when None."""
    if x is None:
        return "—"
    v = float(x)
    return ("+" if v >= 0 else "-") + "$" + f"{abs(v):,.0f}"


def _pct(x) -> str:
    """A 0-1 rate as a whole-percent string ('50%'); '—' when None."""
    return f"{fixed(x * 100, 0)}%" if x is not None else "—"


def _strikes(pos: dict) -> str:
    ss = pos.get("short_strike")
    ss_s = fixed(ss, 0) if ss is not None and float(ss).is_integer() else (fixed(ss, 2) or "—")
    if pos.get("structure") == "put_spread" and pos.get("long_strike") is not None:
        ls = pos["long_strike"]
        ls_s = fixed(ls, 0) if float(ls).is_integer() else fixed(ls, 2)
        return f"{ss_s}/{ls_s}P"
    return f"{ss_s}P"


def _flag_codes(flags: list[dict]) -> str:
    return ", ".join(f["code"] for f in flags) if flags else "—"


def _notional(pos: dict) -> float:
    return (pos.get("short_strike") or 0) * 100 * (pos.get("contracts") or 0)


def _credit_at_risk(pos: dict) -> float:
    return (pos.get("entry_credit") or 0) * 100 * (pos.get("contracts") or 0)


def _book_summary(open_book: list[dict]) -> str:
    n = len(open_book)
    credit = sum(_credit_at_risk(p) for p in open_book)
    by_ticker: dict[str, float] = {}
    total_notional = 0.0
    for p in open_book:
        no = _notional(p)
        total_notional += no
        by_ticker[p["ticker"]] = by_ticker.get(p["ticker"], 0.0) + no
    if by_ticker and total_notional:
        top_tkr = max(by_ticker, key=by_ticker.get)
        conc = f"{top_tkr} {_pct(by_ticker[top_tkr] / total_notional)}"
    else:
        conc = "—"
    return (f"**Book summary:** {n} open · credit at risk {_usd(credit)} · "
            f"notional {_usd(total_notional)} · top concentration {conc}")


def _row(i: int, pos: dict, flags: list[dict], trow: dict) -> str:
    mark = pos.get("mark") or {}
    credit = fixed(pos.get("entry_credit"), 2)
    mk = fixed(mark.get("option_mid"), 2)
    dte = mark.get("dte")
    delta = fixed(mark.get("short_delta"), 2)
    return (
        f"| {i} | {pos['ticker']} | {pos.get('structure') or '—'} | {_strikes(pos)} | "
        f"{pos.get('expiry') or '—'} | {pos.get('contracts') or '—'} | "
        f"{('$' + credit) if credit is not None else '—'} | "
        f"{('$' + mk) if mk is not None else '—'} | "
        f"{_signed_usd(mark.get('unrealized_pnl'))} | {_pct(mark.get('capture_pct'))} | "
        f"{dte if dte is not None else '—'} | {delta if delta is not None else '—'} | "
        f"{trow.get('regime') or '—'} | {trow.get('recommendation') or '—'} | "
        f"{trow.get('v2_gate_state') or '—'} | {fixed(trow.get('fvrp_ratio'), 2) or '—'} | "
        f"{_flag_codes(flags)} |"
    )


def _closed_line(p: dict) -> str:
    thesis = (p.get("thesis") or "").strip()
    thesis_s = f' — thesis "{thesis}"' if thesis else ""
    cap = p.get("close_debit")
    cap_pct = None
    if p.get("entry_credit"):
        cap_pct = (p["entry_credit"] - (cap if cap is not None else 0)) / p["entry_credit"]
    return (f"- {p['ticker']} {p.get('structure') or '—'} {_strikes(p)} ×{p.get('contracts') or '—'}"
            f"{thesis_s} → realized {_signed_usd(p.get('realized_pnl'))} "
            f"(capture {_pct(cap_pct)}, exit {p.get('exit_reason') or '—'})")


def render_portfolio_header(book: dict, scan_by_ticker: dict, eval_date: str) -> str:
    """Book-summary line + open-position table + (if any) closed-today post-mortem block.
    No `## date` heading (the orchestrator adds it). `scan_by_ticker` maps ticker -> the same
    day's scan row (regime / recommendation / v2_gate_state / fvrp_ratio context)."""
    open_book = book.get("open") or []
    lines = [_book_summary(open_book)]
    if open_book:
        lines += ["", BOOK_HEADER, BOOK_SEP]
        for i, p in enumerate(open_book, 1):
            trow = scan_by_ticker.get(p["ticker"]) or {}
            flags = compute_flags(p, p.get("mark"), trow, eval_date)
            lines.append(_row(i, p, flags, trow))
    closed = book.get("closed_today") or []
    if closed:
        lines += ["", f"**Closed {eval_date}:**"]
        lines += [_closed_line(p) for p in closed]
    return "\n".join(lines)


def flags_for_book(book: dict, scan_by_ticker: dict, eval_date: str) -> dict:
    """{ticker: [flag dicts]} for every open position — the rule-citing detail the prose prompt
    needs (the table shows only codes). Same compute_flags port used by the renderer."""
    out = {}
    for p in book.get("open") or []:
        trow = scan_by_ticker.get(p["ticker"]) or {}
        out[p["ticker"]] = compute_flags(p, p.get("mark"), trow, eval_date)
    return out


# Scan-row fields worth handing the model as the "what the system thinks now" context.
_SCAN_CTX_KEYS = ("regime", "recommendation", "signal_score", "vrp_ratio", "term_slope",
                  "rv_acceleration", "skew_25d", "iv_percentile", "earnings_dte", "is_etf",
                  "sigma_fwd", "fvrp_ratio", "fvrp_z", "slope_1m3m", "accel_dn",
                  "v2_gate_state", "v2_eligible")
_MARK_CTX_KEYS = ("option_mid", "underlying_close", "short_delta", "unrealized_pnl",
                  "capture_pct", "dte", "earnings_dte", "mark_source")


def build_book_context(book: dict, scan_by_ticker: dict, eval_date: str) -> dict:
    """The JSON context handed to Claude alongside the deterministic header: per open position
    its identity + mark + rule-citing flags + entry checklist (thesis / deviation_reason /
    v1&v2-at-entry) + today's scan row; plus any trade closed today with its realized outcome;
    plus the book-level aggregates. Everything here is GIVEN — the model never recomputes it."""
    open_book = book.get("open") or []
    positions = []
    for p in open_book:
        trow = scan_by_ticker.get(p["ticker"]) or {}
        mark = p.get("mark") or {}
        chk = p.get("checklist") or {}
        positions.append({
            "ticker": p["ticker"],
            "structure": p.get("structure"),
            "strikes": _strikes(p),
            "expiry": p.get("expiry"),
            "contracts": p.get("contracts"),
            "entry_date": p.get("entry_date"),
            "entry_credit": p.get("entry_credit"),
            "target_capture": p.get("target_capture"),
            "exit_dte_plan": p.get("exit_dte_plan"),
            "thesis": p.get("thesis"),
            "credit_at_risk": _credit_at_risk(p),
            "notional": _notional(p),
            "mark": {k: mark.get(k) for k in _MARK_CTX_KEYS if k in mark},
            "flags": compute_flags(p, p.get("mark"), trow, eval_date),
            "entry_checklist": {"deviation_reason": chk.get("deviation_reason"),
                                "checks": chk.get("checks"), "values": chk.get("values")},
            "scan_now": {k: trow.get(k) for k in _SCAN_CTX_KEYS if k in trow},
        })
    closed = []
    for p in book.get("closed_today") or []:
        cd = p.get("close_debit")
        cap = ((p["entry_credit"] - (cd or 0)) / p["entry_credit"]
               if p.get("entry_credit") else None)
        closed.append({
            "ticker": p["ticker"], "structure": p.get("structure"), "strikes": _strikes(p),
            "contracts": p.get("contracts"), "thesis": p.get("thesis"),
            "realized_pnl": p.get("realized_pnl"), "exit_reason": p.get("exit_reason"),
            "capture_pct": cap, "followed_plan": p.get("followed_plan"),
        })
    total_notional = sum(_notional(p) for p in open_book)
    return {
        "date": eval_date,
        "summary": {
            "n_open": len(open_book),
            "credit_at_risk": sum(_credit_at_risk(p) for p in open_book),
            "notional": total_notional,
        },
        "positions": positions,
        "closed_today": closed,
    }
