"""
Golden-master test: backend/theta_core.py must reproduce the frozen reference
references/theta_harvest_core.py to 1e-9 across every Module A/B/C/E function.

This is the regression guard for the port (P3): if anyone edits theta_core.py
away from the reference (e.g. during integration), these fail. Plus the two
targeted regressions from the 2026-07-04 corrections: friction_prescreen passes
a liquid index put, and resid_var / kelly floor read from CONFIG.

Run: cd backend && python -m pytest test_theta_core.py -v   (or python test_theta_core.py)
"""

import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)                                   # backend/theta_core.py
sys.path.insert(0, os.path.join(ROOT, "references"))       # the frozen reference

import theta_core as port          # noqa: E402  (the ported production copy)
import theta_harvest_core as ref   # noqa: E402  (the golden master)

TOL = 1e-9


def _make_ohlc(n=320, seed=1):
    """Deterministic synthetic OHLC series (dicts o/h/l/c) for fixtures."""
    rng = np.random.default_rng(seed)
    c = 100.0
    bars = []
    for i in range(n):
        ret = rng.normal(0, 0.012)
        prev = c
        c = prev * np.exp(ret)
        o = prev * np.exp(rng.normal(0, 0.004))
        hi = max(o, c) * np.exp(abs(rng.normal(0, 0.006)))
        lo = min(o, c) * np.exp(-abs(rng.normal(0, 0.006)))
        bars.append({"date": f"2025-{1+i//28:02d}-{1+i%28:02d}",
                     "o": o, "h": hi, "l": lo, "c": c, "v": 1e6})
    return bars


def test_config_identical():
    assert port.CONFIG == ref.CONFIG
    assert len(port.CONFIG) == 44


def test_daily_inputs_1e9():
    bars = _make_ohlc()
    for i in range(1, len(bars)):
        p, b = bars[i - 1], bars[i]
        a = port.daily_inputs(b["o"], b["h"], b["l"], b["c"], p["c"])
        e = ref.daily_inputs(b["o"], b["h"], b["l"], b["c"], p["c"])
        for k in ("r", "v", "s_neg", "s_pos"):
            assert abs(a[k] - e[k]) < TOL, (k, a[k], e[k])


def test_yang_zhang_1e9():
    bars = _make_ohlc()
    o = [b["o"] for b in bars]; h = [b["h"] for b in bars]
    l = [b["l"] for b in bars]; c = [b["c"] for b in bars]
    for i in range(22, len(bars)):
        assert abs(port.yang_zhang(o[:i], h[:i], l[:i], c[:i])
                   - ref.yang_zhang(o[:i], h[:i], l[:i], c[:i])) < TOL


def test_ewma_replay_1e9():
    bars = _make_ohlc()
    sp, sr = port.EwmaState(), ref.EwmaState()
    for i in range(1, len(bars)):
        p, b = bars[i - 1], bars[i]
        dp = port.daily_inputs(b["o"], b["h"], b["l"], b["c"], p["c"])
        sp.update(dp["v"], dp["s_neg"]); sr.update(dp["v"], dp["s_neg"])
    for m in port.EwmaState.COMS_V:
        assert abs(sp.v[m] - sr.v[m]) < TOL
    for m in port.EwmaState.COMS_SNEG:
        assert abs(sp.sneg[m] - sr.sneg[m]) < TOL
    assert abs(sp.vbar - sr.vbar) < TOL


def test_forecaster_fit_predict_1e9():
    bars = _make_ohlc(n=400)
    # build a tiny pooled panel from one synthetic ticker
    def _panel(mod):
        st = mod.EwmaState(); snaps = []
        for i in range(1, len(bars)):
            p, b = bars[i - 1], bars[i]
            d = mod.daily_inputs(b["o"], b["h"], b["l"], b["c"], p["c"])
            st.update(d["v"], d["s_neg"])
            snaps.append((d["v"], {"vbar": st.vbar,
                                   "v": dict(st.v), "sneg": dict(st.sneg)}))
        X, y = [], []
        vser = [s[0] for s in snaps]
        for i in range(len(snaps) - mod.HOLD_SESSIONS):
            _v, sv = snaps[i]
            g = 1.0
            rvfwd = (mod.ANN / mod.HOLD_SESSIONS) * sum(vser[i + 1:i + 1 + mod.HOLD_SESSIONS])
            view = type("SV", (), sv)  # attribute view
            X.append(mod.forecast_features(view, g))
            y.append(np.log(rvfwd) - np.log(sv["vbar"]) - np.log(mod.ANN))
        return np.asarray(X), np.asarray(y), snaps
    Xp, yp, snp = _panel(port)
    Xr, yr, snr = _panel(ref)
    assert np.allclose(Xp, Xr, atol=TOL) and np.allclose(yp, yr, atol=TOL)
    fp, fr = port.PooledForecaster(), ref.PooledForecaster()
    fp.fit(Xp, yp); fr.fit(Xr, yr)
    assert abs(fp.intercept - fr.intercept) < TOL
    assert np.allclose(fp.beta, fr.beta, atol=TOL)
    assert abs(fp.resid_var - fr.resid_var) < TOL
    viewp = type("SV", (), snp[-1][1]); viewr = type("SV", (), snr[-1][1])
    assert abs(fp.predict_sigma_fwd(viewp, 1.0) - fr.predict_sigma_fwd(viewr, 1.0)) < TOL


def test_fvrp_1e9():
    hist = [1.1 + 0.01 * i for i in range(80)]
    a = port.fvrp(0.25, 0.20, hist); e = ref.fvrp(0.25, 0.20, hist)
    for k in ("ratio", "z", "abs_premium_volpts"):
        assert abs(a[k] - e[k]) < TOL


def test_gate_state_sequence_agrees():
    """Feed both machines the same path; state + transient must match every step."""
    gp, gr = port.GateState(), ref.GateState()
    path = [(0.95, 1.02, 0.2), (0.99, 1.12, 0.6), (1.01, 1.15, 0.7),
            (1.06, 1.20, 0.3), (1.07, 1.05, 0.2), (0.97, 1.00, 0.1),
            (0.96, 0.98, 0.1), (0.94, 0.95, 0.1)]
    for slope, accel, conc in path:
        gp.update(slope, accel, conc); gr.update(slope, accel, conc)
        assert gp.state == gr.state and gp.transient == gr.transient
        assert (gp.entry_eligible(1.30, 1.20, 3.0)
                == gr.entry_eligible(1.30, 1.20, 3.0))


def test_sizing_1e9():
    assert abs(port.margin_short_put(2.0, 500, 480) - ref.margin_short_put(2.0, 500, 480)) < TOL
    assert abs(port.dial_R(0.16, 0.18) - ref.dial_R(0.16, 0.18)) < TOL
    assert abs(port.dial_O(1.2) - ref.dial_O(1.2)) < TOL
    assert port.contracts(100_000, 0.5, 0.9, 1.1, 4800) == ref.contracts(100_000, 0.5, 0.9, 1.1, 4800)
    assert abs(port.reentry_ramp(0.15, 0.18) - ref.reentry_ramp(0.15, 0.18)) < TOL


def test_kelly_base_1e9():
    x = np.array([0.1, -0.05, 0.08, -0.3, 0.12, 0.06] * 5)   # 30 trades
    months = np.array([1, 1, 2, 2, 3, 3] * 5)
    a = port.kelly_base(x, months, rng=np.random.default_rng(7), n_boot=50)
    e = ref.kelly_base(x, months, rng=np.random.default_rng(7), n_boot=50)
    assert abs(a - e) < TOL


def test_psr_1e9():
    rng = np.random.default_rng(3)
    r = rng.normal(0.0004, 0.01, 200)
    a = port.psr(r, worst_case=True, n_boot=50, rng=np.random.default_rng(11))
    e = ref.psr(r, worst_case=True, n_boot=50, rng=np.random.default_rng(11))
    for k in ("psr", "sr_daily", "skew", "kurt", "mintrl_days"):
        assert abs(a[k] - e[k]) < TOL


def test_realized_capture_and_health_1e9():
    a = port.realized_capture(0.25, 0.18); e = ref.realized_capture(0.25, 0.18)
    assert abs(a["var_points"] - e["var_points"]) < TOL and abs(a["log"] - e["log"]) < TOL
    hp = port.health_monitor(np.array([1.0, -2.0, 0.5]))
    hr = ref.health_monitor(np.array([1.0, -2.0, 0.5]))
    assert hp == hr


# ── Targeted regressions from the 2026-07-04 corrections ──────────────────

def test_friction_prescreen_passes_liquid_index_put():
    # SPY-like: mid $2.00, 1¢ spread, ~$1.30 round-trip commission.
    ok, reason = port.friction_prescreen(1.995, 2.005, 1.30)
    assert ok is True, reason
    # wide/thin one must reject
    bad, why = port.friction_prescreen(1.00, 1.50, 1.30)
    assert bad is False and why == "spread_over_mid"


def test_resid_var_and_kelly_floor_from_config():
    assert port.PooledForecaster().resid_var == port.CONFIG["resid_var_prior"]
    # cold start (< kelly_min_trades) returns the CONFIG floor, not a fitted f*
    few = np.array([0.1, -0.05, 0.08])
    assert port.kelly_base(few, np.array([1, 1, 2])) == port.CONFIG["kelly_cold_start_floor"]


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
