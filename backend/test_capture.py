"""Forward realized capture (WS2a) — hand-computed values, the lag-21 boundary, idempotence,
the per-run bound, the whitelist round-trip (the silent-failure guard) and the aggregates.

Run:  cd backend && python -m pytest test_capture.py -v
"""
from __future__ import annotations

import math
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pytest

import database
import theta_core as tc
import capture as cap


def _weekdays(start: date, n: int) -> list[date]:
    out, d = [], start
    while len(out) < n:
        if d.weekday() < 5:
            out.append(d)
        d += timedelta(days=1)
    return out


@pytest.fixture()
def db(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "t.db")
    monkeypatch.setattr(database, "TRIAL_REGISTRY_PATH", tmp_path / "reg.jsonl")
    database.init_db()
    return tmp_path


def _seed(ticker: str, dates: list[date], closes: list[float], iv_pct: float, iv_dates: int):
    rows = []
    for d, c in zip(dates, closes):
        rows.append((ticker, d.isoformat(), c * 0.995, c * 1.01, c * 0.99, c, 1_000_000, "test", 1, 0))
    database.store_daily_bars(rows)
    for d in dates[:iv_dates]:
        database.store_daily_iv(ticker, iv_pct, rv30=20.0, vrp=iv_pct - 20.0, term_slope=0.9, as_of=d)


def test_hand_computed_capture_and_lag_boundary(db):
    rng = np.random.default_rng(7)
    dates = _weekdays(date(2026, 1, 5), 40)
    rets = rng.normal(0, 0.012, size=40)
    closes = list(100.0 * np.exp(np.cumsum(rets)))
    _seed("SPY", dates, closes, iv_pct=25.0, iv_dates=25)   # IV rows on the first 25 sessions
    as_of = dates[-1] + timedelta(days=60)                   # prefilter wide open; bars decide
    stats = cap.fill_resolved(as_of=as_of)
    # Row t resolves iff bars through t+21 exist: indices 0..18 (18+21 = 39 = last bar) → 19 rows.
    assert stats["resolved"] == 19 and stats["unresolved"] == 6 and stats["candidates"] == 25

    conn = database.get_connection()
    r = conn.execute("SELECT rv_fwd_21_cc, rv_fwd_21, capture_30d, capture_30d_log, capture_resolved_at "
                     "FROM daily_iv WHERE ticker='SPY' AND date=?", (dates[3].isoformat(),)).fetchone()
    unresolved = conn.execute("SELECT capture_30d FROM daily_iv WHERE ticker='SPY' AND date=?",
                              (dates[19].isoformat(),)).fetchone()
    conn.close()
    # Hand computation: 22 closes t..t+21 → 21 log returns, ddof=1, annualized.
    win = closes[3:3 + 22]
    lr = np.diff(np.log(win))
    rv_cc = float(np.std(lr, ddof=1) * math.sqrt(252))
    assert abs(r[0] - rv_cc) < 1e-6
    exp = tc.realized_capture(0.25, rv_cc)
    assert abs(r[2] - exp["var_points"]) < 1e-3 and abs(r[3] - exp["log"]) < 1e-5
    assert r[1] is not None and r[1] > 0                     # GK+overnight forward vol present
    assert r[4] == as_of.isoformat()
    assert unresolved[0] is None                             # date index 19 needs bar 40 — absent


def test_idempotent_bounded_and_prefilter(db):
    dates = _weekdays(date(2026, 1, 5), 40)
    closes = [100.0 + 0.3 * i for i in range(40)]
    _seed("QQQ", dates, closes, iv_pct=20.0, iv_dates=25)
    as_of = dates[-1] + timedelta(days=60)
    s1 = cap.fill_resolved(as_of=as_of, limit=5)
    assert s1["candidates"] == 5 and s1["resolved"] == 5        # bounded per run
    s2 = cap.fill_resolved(as_of=as_of)
    assert s2["resolved"] == 14                                 # the remaining resolvable rows
    s3 = cap.fill_resolved(as_of=as_of)
    assert s3["resolved"] == 0                                  # idempotent: nothing left to fill
    early = cap.fill_resolved(as_of=dates[0] + timedelta(days=10))
    assert early["candidates"] == 0                             # prefilter: nothing old enough


def test_dry_run_writes_nothing(db):
    dates = _weekdays(date(2026, 1, 5), 30)
    _seed("IWM", dates, [100.0 + i for i in range(30)], iv_pct=18.0, iv_dates=5)
    s = cap.fill_resolved(as_of=dates[-1] + timedelta(days=60), dry_run=True)
    assert s["resolved"] == 5
    conn = database.get_connection()
    n = conn.execute("SELECT COUNT(*) FROM daily_iv WHERE capture_30d IS NOT NULL").fetchone()[0]
    conn.close()
    assert n == 0


def test_whitelist_round_trip_guards_silent_failure(db):
    database.store_daily_iv("SPY", 22.0, as_of=date(2026, 3, 2))
    n = database.store_daily_iv_v2("SPY", as_of=date(2026, 3, 2), rv_fwd_21_cc=0.2, rv_fwd_21=0.21,
                                   capture_30d=84.0, capture_30d_log=0.19, capture_resolved_at="2026-04-01")
    assert n == 1
    with pytest.raises(ValueError):
        database.store_daily_iv_v2("SPY", as_of=date(2026, 3, 2), capture_30d_typo=1.0)
    for col in ("rv_fwd_21_cc", "rv_fwd_21", "capture_30d", "capture_30d_log", "capture_resolved_at",
                "fvrp_ratio_trail", "veto_disagree"):
        assert col in database._V2_IV_COLS
    # WS4 columns round-trip + summary
    assert database.store_daily_iv_v2("SPY", as_of=date(2026, 3, 2), fvrp_ratio_trail=1.02, veto_disagree=1) == 1
    database.store_shadow_diff([{"date": "2026-03-02", "ticker": "SPY", "is_etf": 1, "v1_action": "NO EDGE",
                                 "v1_regime": "NORMAL", "v2_eligible": 0, "v2_gate_state": "NORMAL",
                                 "v2_transient": 0, "divergence_class": "AGREE", "divergence_reason": "",
                                 "v2_warm": 1}])
    v = database.get_veto_summary(10)
    assert v["veto_denominator"] == "sigma_fwd" and v["veto_disagree_rate"] == 1.0 and v["veto_disagree_n"] == 1


def test_capture_summary_aggregates(db):
    d = date(2026, 3, 2)
    for tkr, capv, rec, elig, warm in (("A", 100.0, "SELL PREMIUM", 1, 1), ("B", -50.0, "NO EDGE", 0, 1),
                                       ("C", -10.0, "NO EDGE", 0, 0), ("D", 30.0, None, None, None)):
        database.store_daily_iv(tkr, 24.0, rv30=24.0, as_of=d)
        fields = dict(capture_30d=capv, capture_30d_log=0.1, rv_fwd_21_cc=0.20, rv_fwd_21=0.21, sigma_fwd=0.22)
        if rec is not None:
            fields.update(legacy_recommendation=rec, v2_eligible=elig, v2_warm=warm)
        database.store_daily_iv_v2(tkr, as_of=d, **fields)
    s = database.get_capture_summary(60)
    assert s["capture_n_resolved"] == 4 and s["capture_window_dates"] == [d.isoformat()]
    assert abs(s["capture_mean_all"] - 17.5) < 1e-9
    assert s["capture_mean_v1_actionable"] == 100.0 and s["capture_mean_v2_eligible"] == 100.0
    assert s["capture_neg_rate_v2_vetoed"] == 1.0 and s["capture_neg_rate_v2_cleared"] == 0.0
    assert s["capture_neg_rate_v2_vetoed_warm"] == 1.0 and s["capture_neg_rate_v1_gated"] == 1.0
    assert abs(s["sigma_fwd_log_mae"] - abs(math.log(0.22 / 0.20))) < 1e-9
    assert abs(s["rv30_log_mae"] - abs(math.log(0.24 / 0.20))) < 1e-9
    assert abs(s["sigma_fwd_log_mae_gk"] - abs(math.log(0.22 / 0.21))) < 1e-9
    for k in database.CAPTURE_SUMMARY_KEYS:
        assert k in s
    empty = database.get_capture_summary(60) if False else None  # placeholder for readability


def test_capture_summary_empty(db):
    s = database.get_capture_summary(60)
    assert s["capture_n_resolved"] == 0 and s["capture_window_dates"] == [] and s["capture_mean_all"] is None
