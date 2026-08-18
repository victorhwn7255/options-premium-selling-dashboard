#!/usr/bin/env python3
"""Generate backend/kelly_seed.json — the distilled Kelly seed for Phase C3 sizing.

Reads the 2026-07 backtest artifacts (automation/staging/backtest/{trades,prices}.json),
keeps ONLY the SELL + COND cohorts (the trades the strategy would actually take — the
other cohorts are counterfactuals the scanner rejects), computes per-trade PnL/margin
using the golden-master `theta_core.margin_short_put` with the EXACT spot at entry from
prices.json, and precomputes `f_star_seed` by running `theta_core.kelly_base` itself
(the 2000-boot grid — minutes offline, never in a request path).

Sanctioned by plan §C3 ("seeded from the 2026-07 backtest trades ... until the live log
has >= kelly_min_trades closed trades spanning a genuine vol event"). Advisory only —
P2-clean (no live behavior reads this; sizing is a recommendation layer).

Run from repo root:  python3 utils/make_kelly_seed.py
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "backend"))

import numpy as np  # noqa: E402
import theta_core as tc  # noqa: E402

BT = REPO / "automation" / "staging" / "backtest"
OUT = REPO / "backend" / "kelly_seed.json"
COHORTS = ("SELL", "COND")


def main() -> None:
    trades = json.loads((BT / "trades.json").read_text())
    prices = json.loads((BT / "prices.json").read_text())

    pnl_per_margin, months, skipped = [], [], 0
    for cohort in COHORTS:
        for t in trades.get(cohort, []):
            if t.get("censored"):
                skipped += 1
                continue
            ohlc = (prices.get(t["t"]) or {}).get(t["entry"])  # [o, h, l, c] per bt_data
            if not ohlc:
                skipped += 1
                continue
            spot = float(ohlc[3])  # close at entry (bt_run's own convention: px[d][3])
            margin = tc.margin_short_put(t["prem"], spot, t["K"])  # $/contract
            if margin <= 0:
                skipped += 1
                continue
            pnl_per_margin.append(t["net"] * 100.0 / margin)  # net is per-share
            months.append(t["entry"][:7])

    n = len(pnl_per_margin)
    if n < tc.CONFIG["kelly_min_trades"]:
        raise SystemExit(f"only {n} usable trades — refusing to write a thin seed")

    print(f"{n} usable trades ({skipped} skipped) across {len(set(months))} months; "
          f"mean pnl/margin {np.mean(pnl_per_margin):+.4f}, worst {min(pnl_per_margin):+.4f}")
    print("running theta_core.kelly_base (block bootstrap + disaster injection) ...")
    f_star = tc.kelly_base(np.asarray(pnl_per_margin), np.asarray(months))
    print(f"f_star_seed = {f_star:.4f}")

    OUT.write_text(json.dumps({
        "generated": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "source": "2026-07 backtest (automation/staging/backtest/trades.json)",
        "cohorts": list(COHORTS),
        "n_trades": n,
        "n_months": len(set(months)),
        "f_star_seed": round(float(f_star), 4),
        "note": ("f_star precomputed by theta_core.kelly_base at generation time; "
                 "runtime reads this value and never runs the bootstrap. "
                 "Regenerate with utils/make_kelly_seed.py."),
        "pnl_per_margin": [round(x, 6) for x in pnl_per_margin],
        "months": months,
    }, indent=1))
    print(f"wrote {OUT} ({OUT.stat().st_size / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
