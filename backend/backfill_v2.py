"""
backfill_v2.py — train the forward-RV forecaster and backfill v2 metrics.

Phase A (silent). Reads `daily_bars`, fits the pooled forecaster (theta_core),
and writes per-ticker-date v2 metrics onto EXISTING `daily_iv` rows (v1 history)
via store_daily_iv_v2: EWMAs, vbar, sigma_fwd/sigma_fwd_dn, fvrp_ratio, fvrp_z,
accel_dn, global_factor. This is what makes the forecaster launch **trained**
and seeds the FVRP z-score window before the live shadow logging (A3) begins.

Bounds / honesty:
  * `slope_1m3m` (gate G2) and `earnings` (G1) need option-chain / earnings data
    we do NOT have historically — they stay NULL here and come online in the live
    scan (A3). The gate_state replay here is therefore **G3-only** (downside-accel),
    a bars-only baseline for the shadow oscillation metric.
  * `sigma_fwd` uses full-history (in-sample) betas to seed the backfill; the live
    scan refits monthly forward-only. The FVRP z baseline itself is trailing-only
    (no look-ahead) — z at date t uses only ratios up to t.

Usage:
  python backfill_v2.py --dry-run          # train + report, write nothing
  python backfill_v2.py                     # train + backfill daily_iv v2 columns
  python backfill_v2.py --tickers SPY,QQQ
"""

from __future__ import annotations

import argparse
import math
import sys

import numpy as np

import theta_core as tc
import estimators as est
import forecast as fc
import database as db
from config import NAKED_PUT_UNIVERSE

NEUTRAL_SLOPE = 0.95   # inert G2 placeholder for the bars-only (G3) gate replay
FVRP_WINDOW = 252
FVRP_MIN = tc.CONFIG["fvrp_min_obs"]   # 60


def _iv_by_date(ticker: str) -> dict:
    conn = db.get_connection()
    rows = dict(conn.execute(
        "SELECT date, atm_iv FROM daily_iv WHERE ticker = ? AND atm_iv IS NOT NULL",
        (ticker,)).fetchall())
    conn.close()
    return rows


def _accel_dn(snap: dict) -> float:
    a5, a25 = snap["e_sneg"].get(5), snap["e_sneg"].get(25)
    return math.sqrt(a5 / a25) if (a5 and a25 and a25 > 0) else 1.0


def backfill_ticker(ticker: str, snaps: list[dict], g_by_date: dict,
                    engine, dry_run: bool) -> dict:
    iv_map = _iv_by_date(ticker)
    snap_by_date = {s["date"]: s for s in snaps}
    idx_of = {s["date"]: i for i, s in enumerate(snaps)}
    # dates we can write: have a daily_iv row (atm_iv), a snapshot, and a G_t.
    dates = sorted(d for d in iv_map if d in snap_by_date and d in g_by_date)

    gate = tc.GateState()
    gate_seen = 0  # advance the machine over ALL snaps for correct hysteresis
    written, ratios, fvrp_obs = 0, [], 0

    for d in dates:
        i = idx_of[d]
        snap = snap_by_date[d]
        g = g_by_date[d]
        sf, sfd = engine.predict(snap, g)
        iv30_dec = iv_map[d] / 100.0
        ratio = iv30_dec / max(sf, 1e-6)
        ratios.append(ratio)
        window = ratios[-FVRP_WINDOW:]
        z = 0.0
        if len(window) >= FVRP_MIN:
            lw = np.log(np.asarray(window))
            sd = lw.std(ddof=1)
            if sd > 1e-9:
                z = float((math.log(ratio) - lw.mean()) / sd)
                fvrp_obs += 1
        accel = _accel_dn(snap)
        if not dry_run:
            db.store_daily_iv_v2(
                ticker, as_of=d,
                v_gk=snap["v"], s_neg=snap["s_neg"],
                ewma_v_1=snap["e_v"][1], ewma_v_5=snap["e_v"][5],
                ewma_v_25=snap["e_v"][25], ewma_v_125=snap["e_v"][125],
                ewma_sneg_5=snap["e_sneg"][5], ewma_sneg_25=snap["e_sneg"][25],
                vbar=snap["vbar"], sigma_fwd=sf, sigma_fwd_dn=sfd,
                fvrp_ratio=ratio, fvrp_z=z, accel_dn=accel, global_factor=g,
            )
        written += 1

    # G3-only gate replay over the full snapshot series; persist on daily_iv dates.
    date_set = set(dates)
    for i, snap in enumerate(snaps):
        accel = _accel_dn(snap)
        conc = est.concentration_10d(snaps[max(0, i - 9): i + 1])
        gate.update(NEUTRAL_SLOPE, accel, conc)
        gate_seen += 1
        if snap["date"] in date_set and not dry_run:
            db.store_gate_state(ticker, snap["date"], gate.state,
                                transient=gate.transient)

    return {"ticker": ticker, "written": written, "fvrp_z_obs": fvrp_obs,
            "iv_dates": len(iv_map)}


def main():
    ap = argparse.ArgumentParser(description="Train the v2 forecaster + backfill daily_iv v2 metrics.")
    ap.add_argument("--tickers", type=str, default=None)
    ap.add_argument("--dry-run", action="store_true", help="Train + report; write nothing")
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()

    tickers = ([t.strip().upper() for t in args.tickers.split(",")]
               if args.tickers else list(NAKED_PUT_UNIVERSE.keys()))
    bad = [t for t in tickers if t not in NAKED_PUT_UNIVERSE]
    if bad:
        print(f"ERROR: unknown tickers {bad}", file=sys.stderr)
        sys.exit(1)

    print(f"Training pooled forecaster over {len(tickers)} tickers"
          f"{' [DRY RUN]' if args.dry_run else ''} ...")
    engine, series, g_by_date = fc.train_from_db(tickers)
    print(f"  n_obs={engine.n_obs}  fitted={engine.fitted}  "
          f"(min_pooled_obs={tc.CONFIG['min_pooled_obs']})")
    if not engine.fitted:
        print("  ⚠ forecaster NOT trained — backfill bars first (backfill_bars.py).",
              file=sys.stderr)
        sys.exit(2)

    total_written, total_warm = 0, 0
    for t in tickers:
        if t not in series:
            print(f"  {t:5s} — no bars, skipped")
            continue
        r = backfill_ticker(t, series[t], g_by_date, engine, args.dry_run)
        total_written += r["written"]
        warm = r["fvrp_z_obs"] >= 1
        total_warm += 1 if warm else 0
        flag = "" if r["fvrp_z_obs"] >= FVRP_MIN else "  (z-window < 60: cold)"
        print(f"  {t:5s} rows={r['written']:4d}  fvrp_z_obs={r['fvrp_z_obs']:4d}{flag}")

    print(f"\n{'DRY RUN — nothing written. ' if args.dry_run else ''}"
          f"{total_written} daily_iv rows updated; "
          f"{total_warm}/{len(tickers)} tickers reached the 60-obs FVRP-z window.")


if __name__ == "__main__":
    main()
