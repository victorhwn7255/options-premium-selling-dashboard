"""Trade Journal (J1) — positions/journal/settings API + the scan-time mark step.

Design (tasks/positions-journal-build-plan.md):
- Every route sits behind auth.require_owner (fail-closed; the public demo never
  sees or touches the book). Reads AND writes.
- Never hand-enter what the system recorded: entry attaches `scan_ref` + a
  backend-evaluated checklist snapshot from the entry-day scan (v1 + v2 fields).
- Marks are computed inside the daily scan from the in-memory chains
  (`mark_open_positions_from_scan`), with a targeted single-quote fallback and
  flagged carried marks — never silent interpolation.
- Closing a position populates the Module-G `trades` telemetry (Phase C/D
  consumer); missing telemetry inputs degrade to NULL, never block a close.
- P1: all flags/checklists are computed here, server-side. P2/P3: analytics are
  descriptive; nothing here feeds CONFIG or live thresholds.
"""
from __future__ import annotations

import csv
import json
import logging
import math
from datetime import date, datetime
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from auth import require_owner
from database import (
    create_position, get_position, get_positions, update_position,
    store_position_mark, get_position_marks, get_latest_position_marks,
    get_setting, get_all_settings, set_setting,
    store_trade_telemetry, upsert_portfolio_daily_partial,
    get_latest_scan, get_bars,
)

logger = logging.getLogger("option-harvest")

router = APIRouter(prefix="/api", tags=["journal"], dependencies=[Depends(require_owner)])

QUOTES_DIR = Path(__file__).parent / "data" / "quotes"

EXIT_REASONS = {"profit_target", "time_exit", "earnings_wall", "danger_underwater",
                "stop", "rolled", "assigned", "expired", "discretionary"}
_STATUS_FOR_EXIT = {"assigned": "assigned", "expired": "expired", "rolled": "rolled"}

DEFAULT_TARGET_CAPTURE = 0.75
DEFAULT_EXIT_DTE = 21


# ── Pydantic bodies ─────────────────────────────────────────────────────────
class PositionCreate(BaseModel):
    ticker: str
    structure: str = Field(pattern="^(naked_put|put_spread)$")
    short_strike: float
    long_strike: Optional[float] = None          # required for put_spread
    expiry: str                                   # YYYY-MM-DD
    contracts: int = Field(gt=0)
    entry_date: Optional[str] = None              # default: today (ET scan date convention)
    entry_credit: float = Field(gt=0)             # net credit per share
    entry_commissions: float = 0.0
    thesis: Optional[str] = None
    target_capture: Optional[float] = None
    exit_dte_plan: Optional[int] = None
    max_loss_plan: Optional[float] = None
    deviation_reason: Optional[str] = None        # required when the entry checklist fails


class PositionPatch(BaseModel):
    thesis: Optional[str] = None
    target_capture: Optional[float] = None
    exit_dte_plan: Optional[int] = None
    max_loss_plan: Optional[float] = None


class PositionClose(BaseModel):
    close_date: Optional[str] = None
    close_debit: float = Field(ge=0)              # net debit per share to close (0 = expired worthless)
    close_commissions: float = 0.0
    exit_reason: str
    followed_plan: Optional[bool] = None
    notes: Optional[str] = None


class PositionRoll(BaseModel):
    close: PositionClose
    open: PositionCreate


class SettingsBody(BaseModel):
    nav: Optional[float] = None
    default_target_capture: Optional[float] = None
    default_exit_dte: Optional[int] = None
    default_commission_per_contract: Optional[float] = None


# ── Pure helpers (unit-tested without HTTP) ─────────────────────────────────
def occ_symbol(ticker: str, expiry: str, side: str, strike: float) -> str:
    """Standard OCC symbol (MarketData quote endpoint): TICKER+YYMMDD+C/P+strike*1000/8."""
    yymmdd = expiry.replace("-", "")[2:]
    return f"{ticker}{yymmdd}{'C' if side == 'call' else 'P'}{int(round(strike * 1000)):08d}"


def net_close_debit(short_mid: Optional[float], long_mid: Optional[float],
                    structure: str) -> Optional[float]:
    """Debit per share to close: buy back the short leg, sell the long leg."""
    if short_mid is None:
        return None
    if structure == "put_spread":
        if long_mid is None:
            return None
        return round(short_mid - long_mid, 4)
    return round(short_mid, 4)


def position_pnl(entry_credit: float, net_debit: float, contracts: int,
                 commissions: float = 0.0) -> float:
    return round((entry_credit - net_debit) * 100 * contracts - commissions, 2)


def capture_pct(entry_credit: float, net_debit: float) -> Optional[float]:
    if not entry_credit:
        return None
    return round((entry_credit - net_debit) / entry_credit, 4)


def find_contract(contracts: list, expiry: str, strike: float, side: str = "put"):
    for c in contracts:
        if (c.contract_type == side and c.expiration == expiry
                and abs(c.strike - strike) < 1e-6):
            return c
    return None


def build_entry_checklist(trow: Optional[dict], deviation_reason: Optional[str]) -> dict:
    """Backend-evaluated entry discipline snapshot from the entry-day scan row.
    Mirrors the documented v1 entry rules; purely descriptive (P1: server-side)."""
    if not trow:
        return {"scan_row": False, "checks": {}, "values": {},
                "deviation_reason": deviation_reason,
                "note": "ticker not in the latest scan — no snapshot available"}
    score = trow.get("signal_score")
    regime = trow.get("regime")
    ratio = trow.get("vrp_ratio")
    dte_e = trow.get("earnings_dte")
    is_etf = bool(trow.get("is_etf"))
    checks = {
        "score_ge_65": (score is not None and score >= 65),
        "regime_normal": regime == "NORMAL",
        "vrp_ratio_ge_1_15": (ratio is not None and ratio >= 1.15),
        "earnings_clear": bool(is_etf or dte_e is None or dte_e > 14),
        "recommendation_actionable": trow.get("recommendation") in ("SELL PREMIUM", "CONDITIONAL"),
    }
    values = {k: trow.get(k) for k in (
        "signal_score", "recommendation", "regime", "vrp", "vrp_ratio", "term_slope",
        "rv_acceleration", "skew_25d", "iv_percentile", "earnings_dte", "is_etf",
        # v2 shadow opinion at entry — free Phase-D head-to-head data
        "sigma_fwd", "fvrp_ratio", "fvrp_z", "slope_1m3m", "accel_dn",
        "v2_gate_state", "v2_eligible",
    )}
    return {"scan_row": True, "checks": checks, "values": values,
            "deviation_reason": deviation_reason}


def compute_flags(pos: dict, mark: Optional[dict], trow: Optional[dict],
                  today: Optional[str] = None) -> list[dict]:
    """Management flags for an open position — each cites the rule it comes from.
    Computed server-side only (P1)."""
    flags = []
    today = today or date.today().isoformat()
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
                          "detail": f"capture {cap:.0%} ≥ target {eff_target:.0%}"
                                    + (" (50% variant: RV accel > 1.10)" if eff_target == 0.50 else ""),
                          "rule": "strategy_v1 exits: take 75% in NORMAL / 50% when RV is rising"})
    if mark.get("dte") is not None and mark["dte"] <= exit_dte:
        flags.append({"code": "TIME_EXIT", "detail": f"DTE {mark['dte']} ≤ plan {exit_dte}",
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


def quote_from_csv(ticker: str, quote_date: str, expiry: str, strike: float,
                   side: str = "put") -> Optional[dict]:
    """Look up a contract's captured EOD quote in data/quotes/{ticker}.csv.
    Streamed line filter — files are append-only, dated rows. Returns
    {bid, ask, mid, underlying_price} or None (missing is fine; callers NULL out)."""
    path = QUOTES_DIR / f"{ticker}.csv"
    if not path.exists():
        return None
    try:
        with open(path, newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if (row.get("date") == quote_date and row.get("expiration") == expiry
                        and row.get("side") == side
                        and abs(float(row.get("strike") or 0) - strike) < 1e-6):
                    def _num(key):
                        v = row.get(key)
                        return float(v) if v not in (None, "") else None
                    return {"bid": _num("bid"), "ask": _num("ask"), "mid": _num("mid"),
                            "underlying_price": _num("underlying_price")}
    except Exception:  # noqa: BLE001 — telemetry lookup must never raise into a close
        logger.exception("quote_from_csv failed for %s %s", ticker, quote_date)
    return None


def _latest_scan_rows() -> dict[str, dict]:
    cached = get_latest_scan()
    if not cached or not cached.get("tickers"):
        return {}
    return {t.get("ticker"): t for t in cached["tickers"]}


def _hold_rv(ticker: str, start: str, end: str) -> Optional[float]:
    """Annualized realized vol over the holding window from stored daily bars."""
    try:
        bars = get_bars(ticker)  # chronological; filter to the hold window
        closes = [b["c"] for b in bars if b.get("c") and start <= b["date"] <= end]
        if len(closes) < 5:
            return None
        rets = [math.log(closes[i] / closes[i - 1]) for i in range(1, len(closes))]
        mean = sum(rets) / len(rets)
        var = sum((r - mean) ** 2 for r in rets) / (len(rets) - 1)
        return round(math.sqrt(var * 252), 4)
    except Exception:  # noqa: BLE001
        return None


# ── Routes ──────────────────────────────────────────────────────────────────
@router.post("/positions")
async def open_position(body: PositionCreate):
    if body.structure == "put_spread" and body.long_strike is None:
        raise HTTPException(422, "put_spread requires long_strike")
    if body.structure == "put_spread" and body.long_strike >= body.short_strike:
        raise HTTPException(422, "long_strike must be below short_strike")

    rows = _latest_scan_rows()
    trow = rows.get(body.ticker.upper())
    checklist = build_entry_checklist(trow, body.deviation_reason)
    failures = [k for k, ok in checklist.get("checks", {}).items() if not ok]
    if failures and not body.deviation_reason:
        raise HTTPException(
            422, f"entry checklist failed ({', '.join(failures)}) — "
                 "journal a deviation_reason to proceed")

    cached = get_latest_scan() or {}
    settings = get_all_settings()
    fields = {
        "ticker": body.ticker.upper(),
        "structure": body.structure,
        "short_strike": body.short_strike,
        "long_strike": body.long_strike,
        "expiry": body.expiry,
        "contracts": body.contracts,
        "entry_date": body.entry_date or date.today().isoformat(),
        "entry_credit": body.entry_credit,
        "entry_commissions": body.entry_commissions,
        "thesis": body.thesis,
        "target_capture": body.target_capture
            or float(settings.get("default_target_capture", DEFAULT_TARGET_CAPTURE)),
        "exit_dte_plan": body.exit_dte_plan
            or int(settings.get("default_exit_dte", DEFAULT_EXIT_DTE)),
        "max_loss_plan": body.max_loss_plan,
        "checklist_json": json.dumps(checklist),
        "scan_ref": cached.get("scanned_at"),
        "entry_spot": (trow or {}).get("price"),
        "entry_iv": (trow or {}).get("iv_current"),
        "entry_sigma_fwd": (trow or {}).get("sigma_fwd"),
        "entry_fvrp": (trow or {}).get("fvrp_ratio"),
    }
    pos_id = create_position(fields)
    return get_position(pos_id)


@router.get("/positions/open")
async def open_book():
    positions = get_positions(status="open")
    marks = get_latest_position_marks()
    rows = _latest_scan_rows()
    out = []
    for p in positions:
        mark = marks.get(p["id"])
        p["latest_mark"] = mark
        p["flags"] = compute_flags(p, mark, rows.get(p["ticker"]))
        out.append(p)
    return {"positions": out, "count": len(out)}


@router.get("/positions/{position_id}")
async def position_detail(position_id: int):
    p = get_position(position_id)
    if not p:
        raise HTTPException(404, "position not found")
    marks = get_position_marks(position_id)
    p["marks"] = marks
    p["flags"] = compute_flags(p, marks[-1] if marks else None,
                               _latest_scan_rows().get(p["ticker"]))
    return p


@router.get("/positions/{position_id}/marks")
async def position_marks(position_id: int):
    if not get_position(position_id):
        raise HTTPException(404, "position not found")
    return {"marks": get_position_marks(position_id)}


@router.patch("/positions/{position_id}")
async def patch_position(position_id: int, body: PositionPatch):
    p = get_position(position_id)
    if not p:
        raise HTTPException(404, "position not found")
    fields = {k: v for k, v in body.model_dump().items() if v is not None}
    update_position(position_id, fields)
    return get_position(position_id)


@router.post("/positions/{position_id}/close")
async def close_position(position_id: int, body: PositionClose):
    p = get_position(position_id)
    if not p:
        raise HTTPException(404, "position not found")
    if p["status"] != "open":
        raise HTTPException(409, f"position is {p['status']}, not open")
    if body.exit_reason not in EXIT_REASONS:
        raise HTTPException(422, f"exit_reason must be one of {sorted(EXIT_REASONS)}")

    close_date = body.close_date or date.today().isoformat()
    total_comm = (p.get("entry_commissions") or 0) + body.close_commissions
    realized = position_pnl(p["entry_credit"], body.close_debit, p["contracts"], total_comm)
    cap = capture_pct(p["entry_credit"], body.close_debit)
    update_position(position_id, {
        "status": _STATUS_FOR_EXIT.get(body.exit_reason, "closed"),
        "close_date": close_date,
        "close_debit": body.close_debit,
        "close_commissions": body.close_commissions,
        "realized_pnl": realized,
        "exit_reason": body.exit_reason,
        "followed_plan": None if body.followed_plan is None else int(body.followed_plan),
        # Exit commentary lives with the close, not in the entry thesis
        # (simplify-2026-07-17-journal §S2).
        "close_fills": json.dumps({"notes": body.notes}) if body.notes else None,
    })

    # Module-G telemetry (Phase C/D consumer) — every input degrades to NULL.
    eq = quote_from_csv(p["ticker"], p["entry_date"], p["expiry"], p["short_strike"])
    xq = quote_from_csv(p["ticker"], close_date, p["expiry"], p["short_strike"])
    store_trade_telemetry({
        "position_id": position_id,
        "ticker": p["ticker"],
        "fill_vs_mid_entry": (round(p["entry_credit"] - eq["mid"], 4)
                              if eq and eq.get("mid") is not None and p["structure"] == "naked_put" else None),
        "fill_vs_mid_exit": (round(body.close_debit - xq["mid"], 4)
                             if xq and xq.get("mid") is not None and p["structure"] == "naked_put" else None),
        "quoted_spread_entry": (round(eq["ask"] - eq["bid"], 4)
                                if eq and eq.get("ask") is not None and eq.get("bid") is not None else None),
        "quoted_spread_exit": (round(xq["ask"] - xq["bid"], 4)
                               if xq and xq.get("ask") is not None and xq.get("bid") is not None else None),
        "iv_entry": p.get("entry_iv"),
        "sigma_fwd_entry": p.get("entry_sigma_fwd"),
        "rv_realized_hold": _hold_rv(p["ticker"], p["entry_date"], close_date),
        "capture": cap,
    })
    return get_position(position_id)


@router.post("/positions/{position_id}/roll")
async def roll_position(position_id: int, body: PositionRoll):
    old = get_position(position_id)
    if not old:
        raise HTTPException(404, "position not found")
    if old["status"] != "open":
        raise HTTPException(409, f"position is {old['status']}, not open")
    # Open the NEW leg first, then close the old one. If the replacement fails
    # its entry checklist (422), we must not have already committed the old leg
    # closed-with-no-replacement — that would orphan it invisibly. Worst case
    # here is instead a harmless no-op (nothing changed) or, only after both
    # succeed, two rows sharing a roll_group_id. (simplify-2026-07-22 roll bug)
    group = old.get("roll_group_id") or position_id
    new_pos = await open_position(body.open)          # may 422 — old leg untouched
    update_position(new_pos["id"], {"roll_group_id": group})
    body.close.exit_reason = "rolled"
    await close_position(position_id, body.close)
    update_position(position_id, {"roll_group_id": group})
    return {"closed": get_position(position_id), "opened": get_position(new_pos["id"])}


@router.get("/journal")
async def journal(exit_reason: Optional[str] = None, ticker: Optional[str] = None):
    closed = [p for p in get_positions() if p["status"] != "open"]
    if exit_reason:
        closed = [p for p in closed if p.get("exit_reason") == exit_reason]
    if ticker:
        closed = [p for p in closed if p["ticker"] == ticker.upper()]
    for p in closed:
        try:
            p["checklist"] = json.loads(p.get("checklist_json") or "{}")
        except ValueError:
            p["checklist"] = {}
        p.pop("checklist_json", None)
    return {"trades": closed, "count": len(closed)}


@router.get("/journal/analytics")
async def journal_analytics():
    """Descriptive aggregates over closed trades. Every bucket carries its n —
    the UI greys buckets under n=10 (no lessons from noise). Findings feed
    Phase-F trial proposals, never CONFIG (P2/P3)."""
    closed = [p for p in get_positions() if p["status"] != "open"
              and p.get("realized_pnl") is not None]

    def _values(p):
        try:
            return json.loads(p.get("checklist_json") or "{}").get("values", {})
        except ValueError:
            return {}

    def _bucket(rows):
        n = len(rows)
        if n == 0:
            return {"n": 0}
        pnls = [r["realized_pnl"] for r in rows]
        wins = [x for x in pnls if x > 0]
        losses = [x for x in pnls if x <= 0]
        return {
            "n": n,
            "win_rate": round(len(wins) / n, 4),
            "total_pnl": round(sum(pnls), 2),
            "avg_pnl": round(sum(pnls) / n, 2),
            "profit_factor": (round(sum(wins) / abs(sum(losses)), 2)
                              if losses and sum(losses) != 0 else None),
        }

    def _score_band(v):
        s = v.get("signal_score")
        if s is None:
            return "unknown"
        return "65+" if s >= 65 else ("45-64" if s >= 45 else "<45")

    groups = {
        "by_regime": lambda p: _values(p).get("regime") or "unknown",
        "by_score_band": lambda p: _score_band(_values(p)),
        "by_exit_reason": lambda p: p.get("exit_reason") or "unknown",
        "by_structure": lambda p: p.get("structure") or "unknown",
        "by_v2_eligible_at_entry": lambda p: str(_values(p).get("v2_eligible")),
    }
    breakdown = {}
    for name, keyfn in groups.items():
        buckets: dict[str, list] = {}
        for p in closed:
            buckets.setdefault(keyfn(p), []).append(p)
        breakdown[name] = {k: _bucket(v) for k, v in sorted(buckets.items())}

    followed = [p for p in closed if p.get("followed_plan") == 1]
    deviated = [p for p in closed if p.get("followed_plan") == 0]
    return {
        "overall": _bucket(closed),
        "discipline": {
            "followed_plan": _bucket(followed),
            "deviated": _bucket(deviated),
            "followed_rate": (round(len(followed) / (len(followed) + len(deviated)), 4)
                              if (followed or deviated) else None),
        },
        "breakdown": breakdown,
        "note": "descriptive only — findings route to Phase-F trials, never CONFIG (P2/P3)",
    }


@router.get("/settings")
async def read_settings():
    s = get_all_settings()
    return {
        "nav": float(s["nav"]) if s.get("nav") else None,
        "default_target_capture": float(s.get("default_target_capture", DEFAULT_TARGET_CAPTURE)),
        "default_exit_dte": int(s.get("default_exit_dte", DEFAULT_EXIT_DTE)),
        "default_commission_per_contract": (float(s["default_commission_per_contract"])
                                            if s.get("default_commission_per_contract") else None),
    }


@router.put("/settings")
async def write_settings(body: SettingsBody):
    for key, val in body.model_dump().items():
        if val is not None:
            set_setting(key, str(val))
    return await read_settings()


# ── Scan-time mark step (called from main.run_full_scan post-loop) ──────────
async def mark_open_positions_from_scan(chain_inputs: dict, earnings_by_ticker: dict,
                                        client) -> int:
    """Mark every open position from the scan's in-memory chains. Isolation
    contract: the CALLER wraps this in try/except (like CPS and the v2 shadow) —
    a mark failure must never touch the v1 scan. Per position: chain lookup →
    targeted single-quote fallback → carried (previous mark, flagged).
    Returns the number of positions marked."""
    positions = get_positions(status="open")
    if not positions:
        return 0
    today = date.today().isoformat()
    prev_marks = get_latest_position_marks()
    marked = 0

    for p in positions:
        if p.get("expiry") and p["expiry"] < today:
            continue  # PENDING_SETTLEMENT — flagged at read time, facts live at the broker
        tkr = p["ticker"]
        chain = chain_inputs.get(tkr) or {}
        contracts = chain.get("contracts") or []
        spot = chain.get("spot")
        dte = ((datetime.strptime(p["expiry"], "%Y-%m-%d").date() - date.today()).days
               if p.get("expiry") else None)
        earn = earnings_by_ticker.get(tkr)

        short_c = find_contract(contracts, p["expiry"], p["short_strike"])
        long_c = (find_contract(contracts, p["expiry"], p["long_strike"])
                  if p.get("long_strike") else None)
        short_mid = (round((short_c.bid + short_c.ask) / 2, 4)
                     if short_c and short_c.bid is not None and short_c.ask is not None else None)
        long_mid = (round((long_c.bid + long_c.ask) / 2, 4)
                    if long_c and long_c.bid is not None and long_c.ask is not None else None)
        short_delta = short_c.delta if short_c else None
        bid = short_c.bid if short_c else None
        ask = short_c.ask if short_c else None
        source = "scan_chain"

        net = net_close_debit(short_mid, long_mid, p["structure"])
        if net is None and client is not None:
            # Fallback: the ticker's scan failed (XLB-class) or the strike was absent.
            try:
                q = await client.get_option_quote(
                    occ_symbol(tkr, p["expiry"], "put", p["short_strike"]))
                lq = (await client.get_option_quote(
                    occ_symbol(tkr, p["expiry"], "put", p["long_strike"]))
                    if p.get("long_strike") else None)
                if q and q.get("mid") is not None:
                    short_mid, bid, ask = q["mid"], q.get("bid"), q.get("ask")
                    short_delta = q.get("delta")
                    spot = spot or q.get("underlying_price")
                    long_mid = lq.get("mid") if lq else None
                    net = net_close_debit(short_mid, long_mid, p["structure"])
                    source = "quote_fallback"
            except Exception:  # noqa: BLE001
                logger.warning("journal: quote fallback failed for %s", tkr)

        if net is None:
            prev = prev_marks.get(p["id"])
            if not prev:
                continue  # nothing to carry yet — first mark waits for data
            store_position_mark(
                p["id"], today, underlying_close=prev.get("underlying_close"),
                option_bid=prev.get("option_bid"), option_ask=prev.get("option_ask"),
                option_mid=prev.get("option_mid"), short_delta=prev.get("short_delta"),
                unrealized_pnl=prev.get("unrealized_pnl"),
                capture_pct=prev.get("capture_pct"),
                dte=dte, earnings_dte=earn, mark_source="carried")
            marked += 1
            continue

        store_position_mark(
            p["id"], today, underlying_close=spot, option_bid=bid, option_ask=ask,
            option_mid=net, short_delta=short_delta,
            unrealized_pnl=position_pnl(p["entry_credit"], net, p["contracts"]),
            capture_pct=capture_pct(p["entry_credit"], net),
            dte=dte, earnings_dte=earn, mark_source=source)
        marked += 1

    # Partial portfolio_daily row (nav from settings; PSR/stress stay NULL → Phase C).
    nav = get_setting("nav")
    notional = sum((p.get("short_strike") or 0) * 100 * (p.get("contracts") or 0)
                   for p in positions)
    upsert_portfolio_daily_partial(
        today, nav=float(nav) if nav else None,
        notional_short_put=notional or None)
    return marked
