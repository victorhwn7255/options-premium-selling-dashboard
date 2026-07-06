"""
forecast.py — pooled forward-RV forecaster orchestration (Phase A, silent).

Builds the pooled training panel from stored `daily_bars` across all tickers,
fits `theta_core.PooledForecaster` (one model over the whole cross-section, each
name demeaned by its own vbar), and produces per-ticker `sigma_fwd` /
`sigma_fwd_dn` and the FVRP core.

Target derivation (must match theta_core.predict_sigma_fwd, which returns
`sqrt(vbar * ANN * exp(intercept + x·beta + 0.5·resid_var))`):

    RVfwd_t   = (ANN / h) * sum_{j=1..h} v_{t+j}         # annualized forward variance
    y_centered = ln(RVfwd_t) - ln(vbar_t) - ln(ANN)      # ⇒ predict inverts exactly

`sigma_fwd_dn` uses an identical regression on forward **downside** semivariance
(sum of s_neg); the intercept absorbs the downside/total level shift.

Units: `compute_fvrp` expects iv30 as an **annualized decimal** (0.20), not a
percent — callers convert `iv_current / 100` first.
"""

from __future__ import annotations

import math
from collections import defaultdict

import numpy as np

import theta_core as tc
import estimators as est
import database as db

HOLD = tc.HOLD_SESSIONS          # 21-session forecast/trade horizon
_LN_ANN = math.log(tc.ANN)


class _StateView:
    """Adapts a replay_ewma_series snapshot to the attribute surface
    theta_core.forecast_features / predict_sigma_fwd expect on an EwmaState
    (.vbar, .v[m], .sneg[m])."""

    __slots__ = ("vbar", "v", "sneg")

    def __init__(self, snap: dict):
        self.vbar = snap["vbar"]
        self.v = snap["e_v"]
        self.sneg = snap["e_sneg"]


def build_global_factor(series_by_ticker: dict[str, list[dict]]) -> tuple[dict, dict]:
    """G_t = cross-ticker mean of E_5(v)/vbar, lagged one session (spec A2).

    Returns (G_by_date, mean_by_date). G_by_date[d] is the *lagged* mean (uses
    the prior trading date), which is what feeds the features/gate G5.
    """
    per_date: dict[str, list[float]] = defaultdict(list)
    for snaps in series_by_ticker.values():
        for s in snaps:
            vb, e5 = s["vbar"], s["e_v"].get(5)
            if vb and vb > 0 and e5 is not None:
                per_date[s["date"]].append(e5 / vb)
    mean_by_date = {d: sum(vals) / len(vals) for d, vals in per_date.items() if vals}
    dates = sorted(mean_by_date)
    g_by_date: dict[str, float] = {}
    for i, d in enumerate(dates):
        g_by_date[d] = mean_by_date[dates[i - 1]] if i > 0 else mean_by_date[d]
    return g_by_date, mean_by_date


class ForecastEngine:
    """Two pooled ridge forecasters (total vol, downside vol) sharing features."""

    def __init__(self):
        self.fc_total = tc.PooledForecaster()
        self.fc_dn = tc.PooledForecaster()
        self.n_obs = 0
        self.fitted = False

    def build_panel(self, series_by_ticker: dict[str, list[dict]],
                    g_by_date: dict) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Stack (features, total target, downside target) over every ticker-t
        that has a full 21-session forward window and a valid global factor."""
        X, y_tot, y_dn = [], [], []
        for snaps in series_by_ticker.values():
            v = [s["v"] for s in snaps]
            sn = [s["s_neg"] for s in snaps]
            for i in range(len(snaps) - HOLD):
                snap = snaps[i]
                g = g_by_date.get(snap["date"])
                vbar = snap["vbar"]
                if g is None or g <= 0 or vbar <= 0:
                    continue
                rvfwd = (tc.ANN / HOLD) * sum(v[i + 1: i + 1 + HOLD])
                rvfwd_dn = (tc.ANN / HOLD) * sum(sn[i + 1: i + 1 + HOLD])
                if rvfwd <= 0:
                    continue
                base = math.log(vbar) + _LN_ANN
                X.append(tc.forecast_features(_StateView(snap), g))
                y_tot.append(math.log(rvfwd) - base)
                y_dn.append(math.log(max(rvfwd_dn, 1e-12)) - base)
        return np.asarray(X), np.asarray(y_tot), np.asarray(y_dn)

    def fit(self, X: np.ndarray, y_tot: np.ndarray, y_dn: np.ndarray) -> None:
        if len(X):
            self.fc_total.fit(X, y_tot)
            self.fc_dn.fit(X, y_dn)
        self.n_obs = self.fc_total.n_obs
        self.fitted = self.n_obs >= tc.CONFIG["min_pooled_obs"]

    def predict(self, snap: dict, g: float) -> tuple[float, float]:
        """(sigma_fwd, sigma_fwd_dn) — both annualized decimals."""
        sv = _StateView(snap)
        return (self.fc_total.predict_sigma_fwd(sv, g),
                self.fc_dn.predict_sigma_fwd(sv, g))


def train_from_db(tickers: list[str], as_of: str | None = None) -> tuple:
    """Read stored bars, build per-ticker EWMA snapshot series + the global
    factor, and fit the engine. Returns (engine, series_by_ticker, g_by_date).

    `as_of` (YYYY-MM-DD) truncates bars to that date for point-in-time backfill.
    """
    series_by_ticker: dict[str, list[dict]] = {}
    for tkr in tickers:
        bars = db.get_bars(tkr)
        if as_of:
            bars = [b for b in bars if b["date"] <= as_of]
        if len(bars) < 2:
            continue
        series_by_ticker[tkr] = est.replay_ewma_series(est.bars_to_daily_inputs(bars))
    g_by_date, _ = build_global_factor(series_by_ticker)
    engine = ForecastEngine()
    engine.fit(*engine.build_panel(series_by_ticker, g_by_date))
    return engine, series_by_ticker, g_by_date


def compute_fvrp(iv30_decimal: float, sigma_fwd: float,
                 hist_ratios: list[float] | None = None) -> dict:
    """FVRP ratio + z-score + absolute premium (vol points). `iv30_decimal` is
    an annualized decimal (iv_current/100); `hist_ratios` is the trailing FVRP
    ratio history (theta_core.fvrp logs it internally for the z-score)."""
    return tc.fvrp(iv30_decimal, sigma_fwd, log_hist=hist_ratios)
