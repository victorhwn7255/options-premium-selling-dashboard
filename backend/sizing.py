"""Phase C3 — advisory sizing engine (recommends; NEVER places or auto-sizes an order).

Pure orchestration around the golden-master-guarded `theta_core` Module C
(`margin_short_put` / `kelly_base` / `dial_R` / `dial_O` / `contracts` /
`stressed_pnl` / `entry_allowed`). This module owns NO thresholds — every
constant comes from `theta_core.CONFIG` (P3). `changes_live_behavior: NO`:
nothing here touches scores, recommendations, eligibility, or gates.

Design notes (plan `tasks/todo.md` 2026-08-18, decisions 3-5):
- Kelly seed: `kelly_seed.json` is a distilled artifact of the 2026-07 backtest
  (SELL + COND cohorts only — the trades the strategy would actually take), with
  `f_star_seed` PRECOMPUTED at generation time by `theta_core.kelly_base` itself
  (the 2000-boot grid is minutes of work — computed once offline, never in a
  request). Regenerate with `utils/make_kelly_seed.py`.
- The LIVE Kelly path (fit f* from the journal's closed trades) is deliberately
  deferred to Phase D: it requires >= CONFIG[kelly_min_trades] closed trades
  SPANNING a genuine vol event, and switching to it must be an operator act
  (an explicit `kelly_live_enabled` setting), not an automatic flip.
- Caps REJECT, never trim (plan invariant): `largest_compliant()` walks n down
  from the raw recommendation through `theta_core.entry_allowed` and reports the
  largest passing size PLUS the name of the cap that binds above it. The core
  function stays byte-untouched.
- put_spread positions are stress-modeled as their SHORT leg only (theta_core
  Position models a short put). This OVERSTATES the loss — conservative — and is
  flagged in the payload notes.
"""
from __future__ import annotations

import json
import logging
import statistics
from datetime import date, datetime
from pathlib import Path
from typing import Optional

import theta_core as tc
from database import get_connection, get_latest_position_marks, get_positions, get_setting

logger = logging.getLogger("option-harvest")

SEED_PATH = Path(__file__).parent / "kelly_seed.json"

# Display-only mild scenario from plan §C3 ({-10%, IV x1.5, +5d elapsed}).
# The book-stress CAP is evaluated ONLY on CONFIG's severe scenario
# (stress_spot_mult / stress_iv_mult / stress_days_elapsed) — no threshold
# lives in this constant (P3); it exists purely so the stress panel can show
# a second, milder reference point.
MILD_SPOT_MULT = 0.90
MILD_IV_MULT = 1.5


class SizingUnavailable(Exception):
    """A precondition for sizing is missing (equity unset, ticker has no scan data)."""


# ── Kelly ───────────────────────────────────────────────────────────────────
_seed_cache: Optional[dict] = None


def load_kelly_seed(path: Optional[Path] = None) -> Optional[dict]:
    """The distilled backtest seed, cached. None when the artifact is absent."""
    global _seed_cache
    p = path or SEED_PATH
    if _seed_cache is not None and path is None:
        return _seed_cache
    try:
        seed = json.loads(Path(p).read_text())
    except (OSError, ValueError):
        return None
    if path is None:
        _seed_cache = seed
    return seed


def kelly_f_star() -> dict:
    """Raw f* (phi is applied downstream by theta_core.contracts) + provenance.

    source: 'seed'  — backtest-seeded (the normal Phase-C state)
            'floor' — cold-start floor (seed artifact missing)
    The 'live' source arrives in Phase D (>= kelly_min_trades closed trades
    through a vol event + explicit kelly_live_enabled switch)."""
    n_closed = len([p for p in get_positions(status="closed") if p.get("realized_pnl") is not None])
    seed = load_kelly_seed()
    if seed is not None and seed.get("f_star_seed") is not None:
        return {"f_star": float(seed["f_star_seed"]), "source": "seed",
                "n_seed_trades": seed.get("n_trades"), "n_live_closed": n_closed,
                "seed_generated": seed.get("generated"),
                "live_path": f"Phase D (needs >= {tc.CONFIG['kelly_min_trades']} closed trades "
                             f"through a vol event; log has {n_closed})"}
    return {"f_star": float(tc.CONFIG["kelly_cold_start_floor"]), "source": "floor",
            "n_seed_trades": 0, "n_live_closed": n_closed,
            "note": "kelly_seed.json missing — conservative cold-start floor in effect"}


# ── Market context (daily_iv) ───────────────────────────────────────────────
def _latest_daily_row(ticker: str) -> Optional[dict]:
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT date, spot, atm_iv, sigma_fwd, sigma_fwd_dn, fvrp_z FROM daily_iv "
            "WHERE ticker = ? ORDER BY date DESC LIMIT 1", (ticker,)).fetchone()
    finally:
        conn.close()
    if not row:
        return None
    keys = ("date", "spot", "atm_iv", "sigma_fwd", "sigma_fwd_dn", "fvrp_z")
    return dict(zip(keys, row))


def sigma_dn_median_252(ticker: str) -> Optional[float]:
    """Trailing-252-session median of sigma_fwd_dn — dial_R's anchor."""
    conn = get_connection()
    try:
        vals = [r[0] for r in conn.execute(
            "SELECT sigma_fwd_dn FROM daily_iv WHERE ticker = ? AND sigma_fwd_dn IS NOT NULL "
            "ORDER BY date DESC LIMIT 252", (ticker,))]
    finally:
        conn.close()
    return statistics.median(vals) if vals else None


def _equity() -> float:
    nav = get_setting("nav")
    if not nav:
        raise SizingUnavailable("equity (NAV) is not set — PUT /api/positions/settings first")
    return float(nav)


# ── Book construction ───────────────────────────────────────────────────────
def build_book() -> tuple[list, dict, list[str]]:
    """Open journal book as theta_core.Position[] + per-ticker margin$ + caveats.

    spot: latest mark's underlying_close (fallback: ticker's daily_iv spot).
    iv:   the mark's own contract IV (mark_iv), else ticker ATM IV from daily_iv.
    Margin is computed on the CURRENT mark (falls back to entry credit)."""
    positions = get_positions(status="open")
    marks = get_latest_position_marks()
    book, margins, notes = [], {}, []
    today = date.today()
    for p in positions:
        mark = marks.get(p["id"]) or {}
        drow = _latest_daily_row(p["ticker"]) or {}
        spot = mark.get("underlying_close") or drow.get("spot")
        # per-contract IV from the mark when available (S3); ticker ATM IV fallback
        iv = mark.get("mark_iv") or (drow.get("atm_iv") or 0.0) / 100.0
        premium = mark.get("option_mid") or p.get("entry_credit") or 0.0
        dte = mark.get("dte")
        if dte is None and p.get("expiry"):
            dte = max((datetime.strptime(p["expiry"], "%Y-%m-%d").date() - today).days, 0)
        if spot is None or not iv or dte is None:
            notes.append(f"{p['ticker']}#{p['id']}: missing spot/iv/dte — excluded from stress")
            continue
        if p.get("structure") == "put_spread":
            notes.append(f"{p['ticker']}#{p['id']}: put_spread stressed as short leg only "
                         "(conservative — overstates loss)")
        book.append(tc.Position(
            ticker=p["ticker"], spot=float(spot), strike=float(p["short_strike"]),
            iv=float(iv), dte_sessions=int(dte), contracts=int(p["contracts"]),
            entry_premium=float(p.get("entry_credit") or 0.0)))
        m = tc.margin_short_put(float(premium), float(spot), float(p["short_strike"]))
        margins[p["ticker"]] = margins.get(p["ticker"], 0.0) + m * int(p["contracts"])
    return book, margins, notes


# ── Caps wrapper: reject, never trim ────────────────────────────────────────
def largest_compliant(book: list, candidate, equity: float,
                      book_margins: dict, margin_per_contract: float,
                      rec: int) -> tuple[int, str]:
    """Walk n down from `rec` to the largest size that passes every cap.

    Returns (n, binding_cap): binding_cap is 'none' when the raw recommendation
    passes untouched, else the cap that rejected n+1 (the plan's reject-not-trim
    contract: the caller shows the largest compliant size AND names the cap)."""
    if rec <= 0:
        return 0, "none"
    binding = "none"
    for n in range(rec, 0, -1):
        cand = tc.Position(ticker=candidate.ticker, spot=candidate.spot,
                           strike=candidate.strike, iv=candidate.iv,
                           dte_sessions=candidate.dte_sessions, contracts=n,
                           entry_premium=candidate.entry_premium)
        margins = dict(book_margins)
        margins[cand.ticker] = margins.get(cand.ticker, 0.0) + margin_per_contract * n
        ok, cap = tc.entry_allowed(book, cand, equity, margins)
        if ok:
            return n, binding
        binding = cap
    return 0, binding


# ── The product surfaces ────────────────────────────────────────────────────
def size_candidate(ticker: str, strike: float, premium: float, dte: int,
                   spot: Optional[float] = None, iv: Optional[float] = None) -> dict:
    """Full advisory sizing chain for one candidate short put.

    The complete arithmetic is the payload — a mis-sized recommendation must be
    visible on its face (plan §C3). Raises SizingUnavailable on missing NAV or
    market context."""
    ticker = ticker.upper()
    equity = _equity()
    drow = _latest_daily_row(ticker)
    if drow is None:
        raise SizingUnavailable(f"{ticker}: no daily_iv row — ticker not in the scan universe?")
    spot = float(spot if spot is not None else (drow.get("spot") or 0.0))
    if spot <= 0:
        raise SizingUnavailable(f"{ticker}: no spot available")
    iv = float(iv if iv is not None else (drow.get("atm_iv") or 0.0) / 100.0)

    kelly = kelly_f_star()
    f_star = kelly["f_star"]
    M = tc.margin_short_put(float(premium), spot, float(strike))

    sig_now = drow.get("sigma_fwd_dn")
    sig_med = sigma_dn_median_252(ticker)
    if sig_now and sig_med:
        R = tc.dial_R(sig_med, sig_now)
        r_driver = f"forecast downside vol {sig_now:.4f} vs 252d median {sig_med:.4f} -> R {R:.2f}"
    else:
        R, r_driver = 1.0, "sigma_fwd_dn unavailable -> R neutral 1.00"
    fz = drow.get("fvrp_z")
    if fz is not None:
        O = tc.dial_O(float(fz))
        o_driver = f"FVRP z {fz:+.2f} -> O {O:.2f}"
    else:
        O, o_driver = 1.0, "fvrp_z unavailable -> O neutral 1.00"

    rec_raw = tc.contracts(equity, f_star, R, O, M)
    book, book_margins, notes = build_book()
    candidate = tc.Position(ticker=ticker, spot=spot, strike=float(strike), iv=iv,
                            dte_sessions=int(dte), contracts=max(rec_raw, 1),
                            entry_premium=float(premium))
    rec_final, binding_cap = largest_compliant(book, candidate, equity, book_margins, M, rec_raw)

    stress_before = float(tc.stressed_pnl(book)) if book else 0.0
    final_cand = tc.Position(ticker=ticker, spot=spot, strike=float(strike), iv=iv,
                             dte_sessions=int(dte), contracts=rec_final,
                             entry_premium=float(premium))
    stress_after = (float(tc.stressed_pnl(book + [final_cand]))
                    if rec_final > 0 else stress_before)

    return {
        "ticker": ticker, "strike": strike, "premium": premium, "dte": dte,
        "spot": spot, "iv": round(iv, 4),
        "equity": equity, "phi": tc.CONFIG["kelly_fraction"],
        "kelly": kelly,
        "dial_R": round(R, 4), "dial_R_driver": r_driver,
        "dial_O": round(O, 4), "dial_O_driver": o_driver,
        "margin_per_contract": round(M, 2),
        "rec_contracts_raw": rec_raw,
        "rec_contracts": rec_final,
        "binding_cap": binding_cap,
        "f_star_zero": f_star == 0.0,
        "arithmetic": (f"floor({equity:,.0f} x {tc.CONFIG['kelly_fraction']} x {f_star:.3f}"
                       f" x {R:.2f} x {O:.2f} / {M:,.0f}) = {rec_raw}"
                       + ("" if binding_cap == "none"
                          else f" -> {rec_final} ({binding_cap} binds)")),
        "incremental_book_stress": round(-(stress_after - stress_before), 2),
        "book_notes": notes,
        "advisory": "advisory — you enter the trade; the app never places or sizes an order",
    }


def book_stress() -> dict:
    """Portfolio stress panel: both scenarios + all five caps with headroom."""
    equity = _equity()
    c = tc.CONFIG
    book, margins, notes = build_book()

    severe = float(-tc.stressed_pnl(book)) if book else 0.0   # positive = loss $
    mild = float(-tc.stressed_pnl(book, spot_mult=MILD_SPOT_MULT,
                                  iv_mult=MILD_IV_MULT)) if book else 0.0
    total_margin = sum(margins.values())
    notional = sum(p.strike * 100 * p.contracts for p in book)

    def cap_row(name, value, limit):
        value, limit = float(value), float(limit)  # numpy scalars are not JSON-safe
        return {"cap": name, "value": round(value, 2), "limit": round(limit, 2),
                "pct_of_limit": round(value / limit, 4) if limit else None,
                "headroom": round(limit - value, 2), "breached": bool(value > limit)}

    caps = [
        cap_row("book_stress", severe, c["cap_book_stress_frac"] * equity),
        cap_row("margin_util", total_margin, c["cap_margin_frac"] * equity),
        cap_row("notional", notional, c["cap_notional_frac"] * equity),
    ]
    per_name = []
    for t in sorted(margins):
        name_positions = [p for p in book if p.ticker == t]
        name_stress = float(-tc.stressed_pnl(name_positions))
        per_name.append({
            "ticker": t,
            "margin": cap_row("name_margin", margins[t], c["cap_name_margin_frac"] * equity),
            "stress": cap_row("name_stress", name_stress, c["cap_name_stress_frac"] * equity),
        })

    # Headroom readout: for each open name, how many MORE contracts of its own
    # position-clone fit before any cap binds (the "≈N more before X binds" line).
    headroom = []
    for t in sorted(margins):
        proto = next(p for p in book if p.ticker == t)
        per_contract_margin = margins[t] / max(sum(p.contracts for p in book if p.ticker == t), 1)
        n, cap = 0, "none"
        for extra in range(1, 51):
            cand = tc.Position(ticker=t, spot=proto.spot, strike=proto.strike, iv=proto.iv,
                               dte_sessions=proto.dte_sessions, contracts=extra,
                               entry_premium=proto.entry_premium)
            m2 = dict(margins)
            m2[t] = m2[t] + per_contract_margin * extra
            ok, cap_name = tc.entry_allowed(book, cand, equity, m2)
            if not ok:
                cap = cap_name
                break
            n = extra
        headroom.append({"ticker": t, "more_contracts": n, "binding_cap": cap})

    return {
        "equity": equity,
        "scenarios": {
            "severe": {"label": f"-{(1 - c['stress_spot_mult']) * 100:.0f}% spot, "
                                f"IV x{c['stress_iv_mult']:.0f}, +{c['stress_days_elapsed']}d",
                       "loss": round(severe, 2),
                       "pct_equity": round(severe / equity, 4)},
            "mild": {"label": f"-{(1 - MILD_SPOT_MULT) * 100:.0f}% spot, "
                              f"IV x{MILD_IV_MULT}, +{c['stress_days_elapsed']}d",
                     "loss": round(mild, 2),
                     "pct_equity": round(mild / equity, 4)},
        },
        "caps": caps,
        "per_name": per_name,
        "headroom": headroom,
        "positions_stressed": len(book),
        "book_notes": notes,
        "caveat": ("convention, not a worst case — priced per-name, no cross-name "
                   "correlation; a correlated gap can exceed this."),
    }
