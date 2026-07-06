"""
Tests for the v2 estimator integration layer + migration idempotence.

Run: cd backend && python -m pytest test_estimators.py -v
"""

import math
import os
import sys
import tempfile
from collections import Counter
from pathlib import Path

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import theta_core as tc      # noqa: E402
import estimators as est     # noqa: E402
import database as db        # noqa: E402


def _bars(n=80, seed=2):
    rng = np.random.default_rng(seed)
    c = 100.0
    out = []
    for i in range(n):
        r = rng.normal(0, 0.01)
        p = c
        c = p * math.exp(r)
        o = p * math.exp(rng.normal(0, 0.003))
        hi = max(o, c) * math.exp(abs(rng.normal(0, 0.005)))
        lo = min(o, c) * math.exp(-abs(rng.normal(0, 0.005)))
        out.append({"date": f"2025-{1 + i // 28:02d}-{1 + i % 28:02d}",
                    "o": o, "h": hi, "l": lo, "c": c, "v": 1e6})
    return out


def test_daily_inputs_length_and_formula():
    bars = _bars()
    di = est.bars_to_daily_inputs(bars)
    assert len(di) == len(bars) - 1
    p, b = bars[5], bars[6]
    ref = tc.daily_inputs(b["o"], b["h"], b["l"], b["c"], p["c"])
    assert abs(di[5]["v"] - ref["v"]) < 1e-12
    assert di[5]["date"] == b["date"]
    # sign split is exclusive and complete
    for d in di:
        assert (d["s_neg"] > 0) != (d["s_pos"] > 0) or d["r"] == 0.0


def test_replay_determinism():
    di = est.bars_to_daily_inputs(_bars())
    s1 = est.replay_ewma(di)
    s2 = est.replay_ewma(di)          # recompute-from-scratch is deterministic
    for m in tc.EwmaState.COMS_V:
        assert s1.v[m] == s2.v[m]
    assert s1.vbar == s2.vbar
    # the per-session series' final snapshot equals the whole-series replay
    last = est.replay_ewma_series(di)[-1]
    for m in tc.EwmaState.COMS_V:
        assert abs(last["e_v"][m] - s1.v[m]) < 1e-12
    for m in tc.EwmaState.COMS_SNEG:
        assert abs(last["e_sneg"][m] - s1.sneg[m]) < 1e-12
    assert abs(last["vbar"] - s1.vbar) < 1e-12


def test_replay_matches_manual_accumulation():
    di = est.bars_to_daily_inputs(_bars())
    st = tc.EwmaState()
    for d in di:
        st.update(d["v"], d["s_neg"])
    s = est.replay_ewma(di)
    for m in tc.EwmaState.COMS_V:
        assert s.v[m] == st.v[m]
    assert s.vbar == st.vbar


def test_yz_accel_concentration_sane():
    bars = _bars(120)
    yz = est.yz21_series(bars)
    assert yz and all(x["yz"] > 0 for x in yz)
    st = est.replay_ewma(est.bars_to_daily_inputs(bars))
    assert est.downside_accel(st) > 0
    assert 0.0 <= est.concentration_10d(est.bars_to_daily_inputs(bars)) <= 1.0


def test_migration_idempotence():
    saved_db, saved_tr = db.DB_PATH, db.TRIAL_REGISTRY_PATH
    try:
        tmp = tempfile.mkdtemp()
        db.DB_PATH = Path(tmp) / "t.db"
        db.TRIAL_REGISTRY_PATH = Path(tmp) / "tr.jsonl"
        db.init_db()
        db.init_db()   # second run must be a no-op
        conn = db.get_connection()
        cols = [r[1] for r in conn.execute("PRAGMA table_info(daily_iv)")]
        assert not [c for c, n in Counter(cols).items() if n > 1]   # no duplicate columns
        tabs = {r[0] for r in conn.execute("select name from sqlite_master where type='table'")}
        assert {"daily_bars", "index_daily", "gate_state", "shadow_diff",
                "positions", "trades", "portfolio_daily"} <= tabs
        conn.close()
    finally:
        db.DB_PATH, db.TRIAL_REGISTRY_PATH = saved_db, saved_tr


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
