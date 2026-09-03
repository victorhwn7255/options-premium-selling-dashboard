"""X1 replay harness — pure-function tests on synthetic data (no snapshot, no network).

Run:  python3 -m pytest scripts/test_index_sleeve_replay.py -v
"""
from __future__ import annotations

import sys
from datetime import date, timedelta
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

import index_sleeve_replay as X  # noqa: E402
import estimators as est          # noqa: E402
import forecast as fc             # noqa: E402


def _weekdays(start: date, n: int) -> list[str]:
    out, d = [], start
    while len(out) < n:
        if d.weekday() < 5:
            out.append(d.isoformat())
        d += timedelta(days=1)
    return out


def _bars(dates, seed, drift=0.0, crash_at=None, crash=-0.08):
    rng = np.random.default_rng(seed)
    c, out = 100.0, []
    for i, d in enumerate(dates):
        r = rng.normal(drift, 0.01) + (crash if crash_at is not None and i == crash_at else 0.0)
        c *= float(np.exp(r))
        out.append({"date": d, "o": c * 0.999, "h": c * 1.008, "l": c * 0.992, "c": c, "v": 1e6})
    return out


def test_panel_rows_have_no_lookahead_and_walkforward_masks_by_target_end():
    dates = _weekdays(date(2016, 1, 4), 400)
    bars = {t: _bars(dates, s) for t, s in (("A", 1), ("B", 2), ("C", 3))}
    series = {t: est.replay_ewma_series(est.bars_to_daily_inputs(b)) for t, b in bars.items()}
    g, _ = fc.build_global_factor(series)
    rows = X.build_panel_rows(series, g)
    # each row's target-end date is exactly HOLD sessions after its feature date and rows are date-sorted
    ends = [r[0] for r in rows]
    assert ends == sorted(ends) and len(rows) > 0
    wf = X.WalkForward(rows)
    wf.ensure("2017-03-01")
    m, n_used, fitted = wf.refits[-1]
    assert m == "2017-03" and n_used == sum(1 for r in rows if r[0] < "2017-03-01")
    assert n_used < len(rows)                            # future rows excluded
    snap = series["A"][-1]
    sf, sfd, _ = wf.predict(snap, g[snap["date"]])
    assert sf > 0 and sfd > 0


def test_labels_and_gate_metrics_hand_case(monkeypatch):
    master = _weekdays(date(2018, 1, 1), 120)
    monkeypatch.setattr(X, "EVENTS", [("toy", master[50], master[60])])   # peak idx 50, trough idx 60
    labels = X.label_sessions(master)
    e = labels["events"][0]
    assert e["in_lo"] == 50 - X.HOLD and e["in_hi"] == 60 and e["post_lo"] == 61
    # rows: one ticker; loss days inside the event with weights; a gate that catches the big ones only
    rows = []
    for i, d in enumerate(master):
        cap = -100.0 if 45 <= i <= 60 else (10.0 if i not in (30, 31) else -5.0)   # two small losses outside
        veto = (50 <= i <= 60)                                                       # catches idx 50..60
        rows.append({"date": d, "ticker": "T", "capture": cap, "v": veto})
    m = X.gate_metrics(rows, "v", labels)
    # inside window is idx 29..60 → loss days: 30,31 (−5 each) + 45..60 (−100 each, 16 days)
    tot = 2 * 5 + 16 * 100
    vet = 11 * 100                                                                     # idx 50..60
    assert abs(m["recall_lw"] - vet / tot) < 1e-9
    assert abs(m["recall_days"] - 11 / 18) < 1e-9
    assert m["clearance_out"] == 1.0                     # nothing vetoed outside
    assert m["release_clear"] == 1.0                     # post-trough win days all clear
    pe = m["per_event"]["toy"]
    assert pe["lead_sessions"] == 0 and pe["dwell_after_trough"] == 0
    lb = X.bootstrap_lb(rows, "v", labels, n_boot=300)
    assert lb is None or lb <= m["recall_lw"] + 1e-9    # LB never exceeds the point estimate


def test_acceptance_logic():
    names = ["2018-02 Volmageddon", "2018-Q4 drawdown", "2020-03 COVID crash", "2022 bear market",
             "2024-08 carry unwind", "2025-04 tariff shock"]
    pe = {n: {"recall_lw": 0.9, "release_clear": 0.6} for n in names}
    good = {"recall_lw": 0.85, "clearance_out": 0.55, "per_event": pe}
    per_gate = {"x": {"veto_share_out_win": 0.45}}
    acc = X.evaluate_acceptance(good, 0.72, {"recall_lw": 0.8}, per_gate)
    assert all(acc[k]["pass"] for k in ("P1", "P3", "P4", "P5"))
    assert acc["P3"]["calibration_flags"] == {"x": 0.45}
    bad = X.evaluate_acceptance({**good, "recall_lw": 0.75}, 0.72, {"recall_lw": 0.8}, {})
    assert bad["P1"]["pass"] is False and bad["P5"]["pass"] is False


def test_bsm_helpers_consistent():
    S, T, sig = 100.0, 45 / 365, 0.20
    K = X.strike_for_delta(S, T, sig, 0.20)
    assert K < S
    p = X.put_price(S, K, T, sig)
    assert 0 < p < K
    assert X.put_price(S, K, 0.0, sig) == max(0.0, K - S)
