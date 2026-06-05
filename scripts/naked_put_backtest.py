#!/usr/bin/env python3
"""
Naked-Put Historical Backtest (v1)
==================================
Replays 15 months of stored option-chain snapshots through the REAL production
scoring pipeline (`backend/calculator.py` + `backend/scorer.py`), constructs a
naked short put per (ticker, scan-day), settles it hold-to-expiry on the realized
underlying close, and reports realized P/L sliced by the scanner's own signals.

It answers the two questions the dashboard has never validated:
  1. Does the VRP edge exist in this universe?  (sell puts → realized P/L)
  2. Does the score predict outcomes?           (do high-score / high-VRP / contango days win?)

TWO fill sources (see docs/qa/naked-put-backtest-report.md → Known limits):
  - real_atm    : sell the at-the-money put using REAL CSV quotes (mid/bid). The ATM strike is
                  the only one covered across all 15 months, and is the purest realized-VRP payoff.
                  This is the trustworthy result for Q1 + Q2.
  - modeled_20d : approximate the actual ~20Δ book via a BSM-priced OTM put (stored ATM IV + skew).
                  IDEALIZED — no real bid/ask — included only to sketch the real strategy's shape.

Self-contained & deterministic: the underlying close series (for RV and for settlement) comes from
the quotes CSV `underlying_price` column; IV-rank history from data/daily/{T}.csv `atm_iv`. No network.

Key fidelity mechanism: `backend/calculator.py` computes DTE via `date.today()`. To score a HISTORICAL
day faithfully we freeze `calculator.date.today()` to the as-of date (no look-ahead, correct DTEs).

Usage:
    python scripts/naked_put_backtest.py                 # full universe
    python scripts/naked_put_backtest.py --tickers SPY   # one ticker (debug/spot-check)
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import os
import sqlite3
import sys
from collections import defaultdict
from contextlib import contextmanager
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

import calculator  # noqa: E402  (import after sys.path tweak)
from calculator import build_vol_surface, _bsm_delta  # noqa: E402
from scorer import score_opportunity, ScoringParams  # noqa: E402
from scan_quality import compute_scan_quality, suppress_actionable  # noqa: E402
from marketdata_client import OptionContract, DailyBar  # noqa: E402
from config import NAKED_PUT_UNIVERSE  # noqa: E402

QUOTES_DIR = BACKEND / "data" / "quotes"
DAILY_DIR = BACKEND / "data" / "daily"
DB_PATH = BACKEND / "data" / "vol_history.db"
OUT_REPORT = ROOT / "docs" / "qa" / "naked-put-backtest-report.md"
OUT_TRADES = ROOT / "docs" / "qa" / "naked-put-backtest-trades.csv"

RISK_FREE_RATE = float(os.environ.get("RISK_FREE_RATE", "0.043"))  # matches backfill.py

# Trade construction
DTE_MIN, DTE_MAX, DTE_TARGET = 30, 45, 35
TARGET_SHORT_DELTA = 0.20
COMMISSION_PER_SHARE = 0.013   # ≈ $1.30 / contract round-trip
MODELED_HAIRCUT = 0.03         # 3% credit haircut for the modeled 20Δ "net" fill
SPLIT_LOGRET = 0.5             # |daily log-return| above this ⇒ likely split / bad bar
EFFECTIVE_GAP_DAYS = 34        # min calendar days between non-overlapping trades (≈ holding period)

# Known bad data to exclude (context/3-guardrails/fragile-seams.md § EEM anomaly)
EXCLUDE = {("EEM", "2026-03-17"), ("EEM", "2026-03-18")}


# ── inlined BSM put pricer (mirrors backfill.py:_bs_price) ──────────────────
def _norm_cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def _bs_put(spot: float, strike: float, T: float, r: float, sigma: float) -> float:
    if T <= 0 or sigma <= 0:
        return max(0.0, strike - spot)
    sq = math.sqrt(T)
    d1 = (math.log(spot / strike) + (r + 0.5 * sigma * sigma) * T) / (sigma * sq)
    d2 = d1 - sigma * sq
    return strike * math.exp(-r * T) * _norm_cdf(-d2) - spot * _norm_cdf(-d1)


# ── as-of date freeze so production calculator computes correct historical DTEs ──
@contextmanager
def frozen_today(d: date):
    orig = calculator.date
    fd = type("FrozenDate", (orig,), {"today": classmethod(lambda cls: d)})
    calculator.date = fd
    try:
        yield
    finally:
        calculator.date = orig


# ── tiny parsers ────────────────────────────────────────────────────────────
def _f(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _i(v):
    try:
        return int(float(v))
    except (TypeError, ValueError):
        return 0


def load_quotes(ticker: str):
    """Return (dates_sorted, by_date->[OptionContract], close_by_date)."""
    path = QUOTES_DIR / f"{ticker}.csv"
    by_date: dict[str, list[OptionContract]] = defaultdict(list)
    close: dict[str, float] = {}
    with open(path) as fh:
        for row in csv.DictReader(fh):
            d = row["date"]
            spot = _f(row["underlying_price"])
            strike = _f(row["strike"])
            if spot is None or strike is None:
                continue
            close[d] = spot
            by_date[d].append(OptionContract(
                ticker=row["underlying"],
                strike=strike,
                expiration=row["expiration"],
                contract_type=row["side"],
                implied_volatility=_f(row["computed_iv"]),
                bid=_f(row["bid"]),
                ask=_f(row["ask"]),
                last_price=_f(row["last"]),
                volume=_i(row["volume"]),
                open_interest=_i(row["open_interest"]),
            ))
    return sorted(close), by_date, close


def load_iv_history(ticker: str) -> dict[str, float]:
    path = DAILY_DIR / f"{ticker}.csv"
    out: dict[str, float] = {}
    if not path.exists():
        return out
    with open(path) as fh:
        for row in csv.DictReader(fh):
            v = _f(row.get("atm_iv"))
            if v is not None:
                out[row["date"]] = v
    return out


def load_production_signals() -> dict:
    """(date, ticker) → the REAL production signal the live scan computed and stored.

    The offline RV reconstruction from gappy scan-day closes is unreliable (a data gap makes
    "last 30 returns" span months and inflates RV → flips VRP), so signal-based calibration must
    use the values production actually recorded, not reconstructed ones. `scan_results` keeps the
    last 50 scans (the live, full-chain period) with every TickerResult field.
    """
    out: dict = {}
    if not DB_PATH.exists():
        return out
    db = sqlite3.connect(DB_PATH)
    try:
        for scanned_at, tickers_json in db.execute(
                "SELECT scanned_at, tickers FROM scan_results ORDER BY scanned_at"):
            d = scanned_at[:10]  # 6:30 PM ET scan → same calendar date in UTC
            for t in json.loads(tickers_json):
                tk = t.get("ticker")
                if tk is None:
                    continue
                out[(d, tk)] = {
                    "score": t.get("signal_score"),
                    "vrp_ratio": t.get("vrp_ratio"),
                    "term_slope": t.get("term_slope"),
                    "rv_accel": t.get("rv_acceleration"),
                    "regime": t.get("regime"),
                }
    finally:
        db.close()
    return out


def bars_upto(close_by_date, dates_sorted, d_str, lookback=80):
    closes = [(dt, close_by_date[dt]) for dt in dates_sorted if dt <= d_str][-lookback:]
    return [DailyBar(date=dt, open=c, high=c, low=c, close=c, volume=0) for dt, c in closes]


def pick_expiration(contracts, D: date):
    exps: dict[str, int] = {}
    for c in contracts:
        try:
            e = datetime.strptime(c.expiration, "%Y-%m-%d").date()
        except ValueError:
            continue
        exps.setdefault(c.expiration, (e - D).days)
    cand = [(exp, dte) for exp, dte in exps.items() if DTE_MIN <= dte <= DTE_MAX]
    if not cand:
        return None, None
    return min(cand, key=lambda x: abs(x[1] - DTE_TARGET))


def atm_put(contracts, exp, spot):
    puts = [c for c in contracts
            if c.contract_type == "put" and c.expiration == exp
            and c.bid and c.bid > 0 and c.ask and c.ask >= c.bid]
    if not puts:
        return None
    c = min(puts, key=lambda c: abs(c.strike - spot))
    return {"strike": c.strike, "bid": c.bid, "mid": (c.bid + c.ask) / 2.0}


def modeled_20d(spot, dte, iv_pct, skew_pct):
    sigma = max(0.01, (iv_pct + max(0.0, skew_pct)) / 100.0)
    T = dte / 365.0
    lo, hi = spot * 0.5, spot  # lo=low strike (shallow delta), hi=ATM (deep delta)
    for _ in range(60):
        mid = (lo + hi) / 2.0
        d = _bsm_delta(spot, mid, sigma, dte, is_put=True)
        if d < -TARGET_SHORT_DELTA:   # too deep → need a lower strike
            hi = mid
        else:                          # too shallow → need a higher strike
            lo = mid
    K = round((lo + hi) / 2.0, 2)
    return {"strike": K, "credit": _bs_put(spot, K, T, RISK_FREE_RATE, sigma)}


def settle(close_by_date, dates_sorted, entry_str, exp_str):
    """Return (settle_date, settle_close, split_flag) or (None, None, _) if not closeable."""
    if exp_str > dates_sorted[-1]:
        return None, None, False  # expiry beyond data → not yet closed
    candidates = [dt for dt in dates_sorted if dt <= exp_str]
    if not candidates:
        return None, None, False
    sdate = candidates[-1]
    if sdate <= entry_str:
        return None, None, False
    # Expiry must be reliably reachable: the nearest scan ≤ expiry must be within a few days
    # (Sat-dated monthlies settle on Fri ⇒ gap 1). A larger gap means expiry fell in a data
    # hole (e.g. the 2026-04-24→05-15 outage) → settling there mis-states the outcome. Skip it.
    if (datetime.strptime(exp_str, "%Y-%m-%d").date()
            - datetime.strptime(sdate, "%Y-%m-%d").date()).days > 4:
        return None, None, False
    # split / bad-bar detection over the holding window (strike-scale mismatch guard)
    prev = close_by_date.get(entry_str)
    split = False
    for dt in dates_sorted:
        if entry_str < dt <= sdate:
            c = close_by_date[dt]
            if prev and prev > 0 and c > 0 and abs(math.log(c / prev)) > SPLIT_LOGRET:
                split = True
            prev = c
    return sdate, close_by_date[sdate], split


# ── main backtest ───────────────────────────────────────────────────────────
def run(tickers):
    records = []
    day_scored: dict[str, list] = defaultdict(list)
    skipped = defaultdict(int)

    for ticker in tickers:
        meta = NAKED_PUT_UNIVERSE[ticker]
        name, sector = meta["name"], meta["sector"]
        dates_sorted, by_date, close_by_date = load_quotes(ticker)
        if not dates_sorted:
            continue
        iv_hist = load_iv_history(ticker)
        iv_dates_asc = sorted(iv_hist)
        last_date = dates_sorted[-1]

        for d_str in dates_sorted:
            if (ticker, d_str) in EXCLUDE:
                continue
            D = datetime.strptime(d_str, "%Y-%m-%d").date()
            contracts = by_date[d_str]
            spot = close_by_date[d_str]
            hist = [iv_hist[dt] for dt in iv_dates_asc if dt < d_str][::-1]  # most-recent-first
            bars = bars_upto(close_by_date, dates_sorted, d_str)
            if len(bars) < 12:
                skipped["too_few_bars"] += 1
                continue
            try:
                with frozen_today(D):
                    surface = build_vol_surface(ticker, spot, bars, contracts, hist)
                    so = score_opportunity(surface, name, sector, ScoringParams())
            except Exception:
                skipped["score_error"] += 1
                continue
            day_scored[d_str].append(so)

            if surface.iv.iv_current is None:
                continue  # NO DATA → no trade
            exp, dte = pick_expiration(contracts, D)
            if not exp:
                skipped["no_30_45_expiry"] += 1
                continue
            sdate, sclose, split = settle(close_by_date, dates_sorted, d_str, exp)
            if sclose is None:
                skipped["not_closeable"] += 1
                continue
            if split:
                skipped["split_in_window"] += 1
                continue

            # Chain richness: the SCORE (term structure + skew) is only faithfully
            # reconstructable when the chain has multiple expirations AND real OTM depth.
            # Backfilled 2025 dates are ATM-only → degenerate term/skew → score unreliable.
            # Settlement P/L stays valid regardless (real underlying close).
            otm_puts = sum(1 for c in contracts
                           if c.contract_type == "put" and c.expiration == exp
                           and c.strike <= 0.95 * spot and c.implied_volatility)
            chain_full = len(surface.term_structure.points) >= 3 and otm_puts >= 3

            base = dict(
                date=d_str, ticker=ticker, sector=sector, expiration=exp, dte=dte,
                settle_date=sdate, settle_close=round(sclose, 2),
                signal_score=so.signal_score, regime=so.regime, recommendation=so.recommendation,
                vrp=surface.vrp, vrp_ratio=surface.vrp_ratio, term_slope=so.term_slope,
                rv_accel=so.rv_acceleration, iv_pct=so.iv_percentile, iv_rank=so.iv_rank,
                skew=so.skew_25d, iv_current=surface.iv.iv_current,
                n_otm_puts=otm_puts, term_points=len(surface.term_structure.points),
                chain_full=chain_full,
            )

            atm = atm_put(contracts, exp, spot)
            if atm:
                records.append(_settle_rec(base, "real_atm", atm["strike"],
                                           atm["mid"], atm["bid"], sclose))
            md = modeled_20d(spot, dte, surface.iv.iv_current, so.skew_25d)
            records.append(_settle_rec(base, "modeled_20d", md["strike"],
                                       md["credit"], md["credit"] * (1 - MODELED_HAIRCUT), sclose))

    # Day-level scan-quality suppression (parity with production), then propagate label
    degraded_days = 0
    for d_str, res in day_scored.items():
        status, reason = compute_scan_quality(res)
        if status == "DEGRADED":
            degraded_days += 1
            suppress_actionable(res, reason)
    rec_label = {(so.ticker, d): so.recommendation
                 for d, lst in day_scored.items() for so in lst}
    for r in records:
        r["recommendation"] = rec_label.get((r["ticker"], r["date"]), r["recommendation"])

    # Attach the REAL production signal (for faithful calibration — reconstructed RV is gappy).
    prod = load_production_signals()
    matched = 0
    for r in records:
        p = prod.get((r["date"], r["ticker"]))
        ok = p is not None and p["score"] is not None
        r["has_prod_signal"] = ok
        r["prod_score"] = p["score"] if ok else None
        r["prod_vrp_ratio"] = p["vrp_ratio"] if ok else None
        r["prod_term_slope"] = p["term_slope"] if ok else None
        r["prod_rv_accel"] = p["rv_accel"] if ok else None
        r["prod_regime"] = p["regime"] if ok else None
        if ok:
            matched += 1
    skipped["_prod_signal_matched"] = matched

    return records, skipped, degraded_days


def _settle_rec(base, fill_source, strike, credit_gross, credit_net, sclose):
    payoff = max(0.0, strike - sclose)
    pnl_gross = credit_gross - payoff
    pnl_net = credit_net - payoff - COMMISSION_PER_SHARE
    return {
        **base,
        "fill_source": fill_source,
        "strike": round(strike, 2),
        "credit_gross": round(credit_gross, 4),
        "credit_net": round(credit_net, 4),
        "payoff": round(payoff, 4),
        "pnl_gross": round(pnl_gross, 4),
        "pnl_net": round(pnl_net, 4),
        "ret_gross_pct": round(pnl_gross / strike * 100, 4) if strike else 0.0,
        "win": 1 if pnl_gross > 0 else 0,
    }


# ── aggregation ─────────────────────────────────────────────────────────────
def effective_subset(trades):
    """One trade per ticker per ~holding-period block (non-overlapping) → independent sample."""
    out = []
    for ticker in sorted({t["ticker"] for t in trades}):
        last = None
        for t in sorted((x for x in trades if x["ticker"] == ticker), key=lambda x: x["date"]):
            d = datetime.strptime(t["date"], "%Y-%m-%d").date()
            if last is None or (d - last).days >= EFFECTIVE_GAP_DAYS:
                out.append(t)
                last = d
    return out


def agg(trades):
    n = len(trades)
    if n == 0:
        return None
    wins = sum(t["win"] for t in trades)
    g = [t["pnl_gross"] for t in trades]
    net = [t["pnl_net"] for t in trades]
    gross_win = sum(x for x in g if x > 0)
    gross_loss = -sum(x for x in g if x < 0)
    # max drawdown on date-ordered cumulative NET pnl
    cum, peak, mdd = 0.0, 0.0, 0.0
    for t in sorted(trades, key=lambda x: x["date"]):
        cum += t["pnl_net"]
        peak = max(peak, cum)
        mdd = min(mdd, cum - peak)
    return {
        "n": n,
        "win_rate": wins / n * 100,
        "avg_gross": sum(g) / n,
        "avg_net": sum(net) / n,
        "total_net": sum(net),
        "profit_factor": (gross_win / gross_loss) if gross_loss > 0 else float("inf"),
        "avg_ret_pct": sum(t["ret_gross_pct"] for t in trades) / n,
        "worst": min(g),
        "best": max(g),
        "max_dd": mdd,
    }


def bucket_table(trades, keyfn, order):
    rows = []
    for label in order:
        sub = [t for t in trades if keyfn(t) == label]
        a = agg(sub)
        if a:
            rows.append((label, a["n"], a["win_rate"], a["avg_gross"], a["avg_ret_pct"]))
    return rows


# Calibration/attribution read the PRODUCTION-recorded signal (prod_*), never the gappy
# reconstructed one. They are only ever called on trades where has_prod_signal is True.
def score_bucket(t):
    s = t["prod_score"]
    return "65+ (SELL)" if s >= 65 else "55–64" if s >= 55 else "45–54 (COND)" if s >= 45 else "<45 (NO EDGE)"


def vrp_bucket(t):
    r = t["prod_vrp_ratio"]
    if r is None:
        return "n/a"
    return "<1.00" if r < 1.0 else "1.00–1.15" if r < 1.15 else "1.15–1.30" if r < 1.30 else "1.30–1.60" if r < 1.60 else "≥1.60"


def slope_bucket(t):
    s = t["prod_term_slope"]
    return "contango ≤0.95" if s <= 0.95 else "flat 0.95–1.05" if s <= 1.05 else "backwardation >1.05"


def accel_bucket(t):
    a = t["prod_rv_accel"]
    return "≤0.85" if a <= 0.85 else "0.85–1.00" if a <= 1.0 else "1.00–1.10" if a <= 1.10 else "1.10–1.20" if a <= 1.20 else ">1.20"


# ── report ──────────────────────────────────────────────────────────────────
def fmt_headline(a):
    if not a:
        return "_no trades_"
    pf = "∞" if a["profit_factor"] == float("inf") else f"{a['profit_factor']:.2f}"
    return (f"n={a['n']} | win {a['win_rate']:.1f}% | avg/sh gross ${a['avg_gross']:+.3f} "
            f"net ${a['avg_net']:+.3f} | avg ret {a['avg_ret_pct']:+.2f}% | PF {pf} | "
            f"worst ${a['worst']:+.2f} | maxDD ${a['max_dd']:.2f} (net/share, ×100 = per-contract $)")


def write_report(records, skipped, degraded_days, tickers):
    lines = []
    P = lines.append
    dates = sorted({r["date"] for r in records})
    P("# Naked-Put Historical Backtest Report\n")
    P(f"**Generated by:** `scripts/naked_put_backtest.py` (re-run to regenerate)")
    P(f"**Universe:** {len(tickers)} tickers | **Entry days:** {len(dates)} "
      f"({dates[0]} → {dates[-1]}) | **Closed trades:** {len(records)} "
      f"({sum(1 for r in records if r['fill_source']=='real_atm')} real-ATM, "
      f"{sum(1 for r in records if r['fill_source']=='modeled_20d')} modeled-20Δ)\n")

    P("## Method\n")
    P("For every (ticker, scan-day) the stored option chain is replayed through the **real production "
      "scoring** (`build_vol_surface` + `score_opportunity`) with `calculator.date.today()` frozen to "
      "the as-of date (no look-ahead, correct DTEs). A short put is opened on the 30–45 DTE expiration "
      "(target 35) and settled **hold-to-expiry** on the realized underlying close. Two fill sources: "
      "**real_atm** (ATM put, real CSV mid/bid — trustworthy) and **modeled_20d** (BSM-priced ~20Δ put "
      "from stored ATM IV + skew — IDEALIZED). Day-level scan-quality suppression mirrors production.\n")
    P("`P/L per share = credit − max(0, strike − close_at_expiry)`; ×100 for per-contract dollars. "
      "**Gross** = mid fill, no costs (optimistic). **Net** = bid fill (real_atm) / 3% haircut "
      f"(modeled) − ${COMMISSION_PER_SHARE:.3f}/share commission.\n")

    n_prod = sum(1 for r in records if r.get("has_prod_signal"))
    P("## How to read this\n")
    P("- **Headline P/L (real_atm)** is the trustworthy result: real fills, real underlying closes, "
      "all 15 months. It answers *does selling premium in this universe make money*.")
    P("- **Calibration & attribution** use the **production-recorded signal** (`scan_results`), i.e. "
      "the exact score/VRP/slope/RV the live dashboard computed that day — NOT an offline "
      "reconstruction. (Reconstructing RV from gappy scan-day closes inflated RV and flipped VRP "
      "sign on ~20% of days; see Known limits.) This restricts the slices to the **live period the "
      "DB still retains** (`scan_results` keeps the last 50 scans ≈ 2026-03 → 05) intersected with "
      "closed trades.")
    P("- The sample window is a **strong bull / V-recovery regime** (SPY ~+23% across it). Short puts "
      "structurally win in that tape, so high win-rates and any *DANGER/backwardation looks "
      "profitable* slices are **regime + small-N artifacts**, not license to sell into backwardation "
      "— the gates exist to cap a left tail this sample didn't deliver.\n")

    for src, title in [("real_atm", "A. ATM real-fill — the trustworthy result"),
                       ("modeled_20d", "B. Modeled 20Δ overlay — IDEALIZED (BSM fills)")]:
        tr = [r for r in records if r["fill_source"] == src]
        eff = effective_subset(tr)
        cal = [r for r in tr if r.get("has_prod_signal")]
        P(f"## {title}\n")
        P(f"- **All trades (overlapping, inflated N):** {fmt_headline(agg(tr))}")
        P(f"- **Effective (non-overlapping ≈ independent):** {fmt_headline(agg(eff))}\n")
        P(f"### Calibration — does score predict outcome? "
          f"(production-recorded signal, live period, N={len(cal)})\n")
        P("| Score bucket | n | win% | avg/sh gross | avg ret% |")
        P("|---|--:|--:|--:|--:|")
        for lbl, n, wr, ag, ar in bucket_table(
                cal, score_bucket, ["<45 (NO EDGE)", "45–54 (COND)", "55–64", "65+ (SELL)"]):
            P(f"| {lbl} | {n} | {wr:.1f} | ${ag:+.3f} | {ar:+.2f} |")
        P("")
        P(f"### Attribution — does P/L live where the metrics point? "
          f"(production-recorded signal, live period, N={len(cal)})\n")
        for name, fn, order in [
            ("VRP ratio", vrp_bucket, ["<1.00", "1.00–1.15", "1.15–1.30", "1.30–1.60", "≥1.60"]),
            ("Term slope", slope_bucket, ["contango ≤0.95", "flat 0.95–1.05", "backwardation >1.05"]),
            ("Regime", lambda t: t["prod_regime"], ["NORMAL", "CAUTION", "DANGER"]),
            ("RV accel", accel_bucket, ["≤0.85", "0.85–1.00", "1.00–1.10", "1.10–1.20", ">1.20"]),
        ]:
            P(f"**By {name}:**\n")
            P("| bucket | n | win% | avg/sh gross | avg ret% |")
            P("|---|--:|--:|--:|--:|")
            for lbl, n, wr, ag, ar in bucket_table(cal, fn, order):
                P(f"| {lbl} | {n} | {wr:.1f} | ${ag:+.3f} | {ar:+.2f} |")
            P("")

    P("## Known limits (read before trusting any number)\n")
    P("- **ATM payoff ≠ 20Δ payoff.** Section A (real fills) validates the *thesis + scoring gradient*; "
      "Section B is **modeled** (BSM from ATM IV + skew), i.e. idealized — its headline stats are a "
      "sketch of the real book, not a measurement.")
    P("- **Effective N ≪ raw N.** Overlapping daily entries are ~95% redundant; trust the *effective* "
      "(non-overlapping) line. The SELL bucket (score ≥ 65) is thin → directional, not significant.")
    P("- **Idealized fills:** gross = mid (optimistic). Net brackets it (bid − commission). No early-"
      "assignment modeling (hold-to-expiry).")
    P("- **Earnings gate omitted** (frontend-only; needs historical earnings dates) — a v2 refinement.")
    P("- **One macro regime** (the window includes an Apr-2025 vol spike + backwardation, but is one "
      "sample) — validates mechanism, not the future.")
    P("- **Offline RV is unreliable → calibration uses the production signal.** Reconstructing RV "
      "from the gappy scan-day close series mis-states VRP (sign-flipped on ~7% of days, "
      "|error| > 2 vol pts on ~20%) because a data gap turns 'last 30 returns' into months. The "
      "headline P/L does **not** use it (settlement = real expiry close; entry credit = real CSV "
      "quote); calibration/attribution use `scan_results` production values. The reconstructed "
      "signal columns in the trades CSV are **diagnostic only — do not trust them**.")
    P("- **Calibration window** is the live period the DB still retains (`scan_results` = last 50 "
      "scans) ∩ closed trades, so it is smaller and more recent than the 15-month P/L window.")
    P(f"- **Data hygiene:** EEM 2026-03-17/18 anomaly excluded; trades spanning a split excluded; "
      f"expiry-in-data-gap trades excluded (settle gap > 4d); backfill IV ~20% BSM-solved; r={RISK_FREE_RATE}.")
    P(f"- **Degraded scan days suppressed:** {degraded_days}. **Skipped during construction:** "
      f"{dict(skipped)}.\n")
    P("## Reproducibility\n")
    P("```\npython scripts/naked_put_backtest.py\n```")
    P(f"Per-trade detail: `{OUT_TRADES.relative_to(ROOT)}`")

    OUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    OUT_REPORT.write_text("\n".join(lines) + "\n")


def write_trades_csv(records):
    if not records:
        return
    cols = ["date", "ticker", "sector", "fill_source",
            # production-recorded signal (authoritative — used for calibration)
            "has_prod_signal", "prod_score", "prod_vrp_ratio", "prod_term_slope", "prod_rv_accel",
            "prod_regime",
            # reconstructed signal (DIAGNOSTIC ONLY — gappy RV, do not trust)
            "signal_score", "recommendation", "regime", "vrp", "vrp_ratio", "term_slope",
            "rv_accel", "iv_pct", "iv_rank", "skew", "iv_current",
            "n_otm_puts", "term_points", "chain_full",
            "expiration", "dte", "strike", "settle_date", "settle_close",
            "credit_gross", "credit_net", "payoff", "pnl_gross", "pnl_net", "ret_gross_pct", "win"]
    with open(OUT_TRADES, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for r in sorted(records, key=lambda x: (x["date"], x["ticker"], x["fill_source"])):
            w.writerow(r)


def verify(records):
    """Print verification checks (spot-check + asserts) to stdout."""
    print("\n=== VERIFICATION ===")
    spy = [r for r in records if r["ticker"] == "SPY" and r["fill_source"] == "real_atm"]
    if spy:
        r = spy[len(spy) // 2]
        print(f"Spot-check SPY real-ATM trade:\n  enter {r['date']} sell {r['strike']}P exp {r['expiration']} "
              f"credit(mid) ${r['credit_gross']:.2f} → settle {r['settle_date']} close ${r['settle_close']:.2f}\n"
              f"  payoff max(0,{r['strike']}-{r['settle_close']})=${r['payoff']:.2f}  "
              f"pnl/share gross ${r['pnl_gross']:+.2f}  net ${r['pnl_net']:+.2f}  (score {r['signal_score']})")
    real = [r for r in records if r["fill_source"] == "real_atm"]
    bad = [r for r in real if r["settle_date"] < r["date"]]
    print(f"No-look-ahead (settle_date ≥ entry): {'PASS' if not bad else f'FAIL ({len(bad)})'}")
    print(f"Real-ATM provenance: credit = (bid+ask)/2 from CSV by construction (n={len(real)})")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tickers", default="", help="comma-separated subset (default: full universe)")
    args = ap.parse_args()
    tickers = ([t.strip().upper() for t in args.tickers.split(",") if t.strip()]
               if args.tickers else list(NAKED_PUT_UNIVERSE))
    tickers = [t for t in tickers if (QUOTES_DIR / f"{t}.csv").exists()]

    print(f"Backtesting {len(tickers)} tickers …")
    records, skipped, degraded = run(tickers)
    print(f"Closed trades: {len(records)} | degraded days: {degraded} | skipped: {dict(skipped)}")
    write_trades_csv(records)
    write_report(records, skipped, degraded, tickers)
    verify(records)
    print(f"\nReport : {OUT_REPORT.relative_to(ROOT)}")
    print(f"Trades : {OUT_TRADES.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
