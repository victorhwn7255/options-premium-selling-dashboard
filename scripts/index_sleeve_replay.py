"""Index-sleeve 10-year gate replay — trial X1 (Signal-Quality WS1). REPORT-ONLY.

Replays the v2 veto layer (G3 downside-accel + transient tag, G4 negative forward VRP, the
dead zone, G5 book freeze, a market-wide term-structure proxy for G2, the live VVIX/VIX-backwardation
overlays, v1's rv10/rv30 gate and the proposed G6 macro window) across 2016 -> present on the
index sleeve (SPY/QQQ/IWM, +GLD when ^GVZ is available) and grades every gate against the
forward realized capture of the underlying — the same target `backend/capture.py` records live.

Why the index sleeve and IV proxies: per-ticker IV30 exists only from 2025-02; bars and the VIX
family go back to 2016. Proxies: ^VIX -> SPY, ^VXN -> QQQ, ^RVX -> IWM, ^GVZ -> GLD, each level-
calibrated by k = median(atm_iv / proxy) over the 2025-26 overlap (raw and k-adjusted both reported).

READ-ONLY. Never imports `backend/database.py` for prod data: reads `automation/staging/snap.db`
(the automation's daily prod copy) with `?mode=ro`; index proxies missing/stale in the snapshot are
pulled from yfinance into a local cache. (Importing `backend/forecast.py` touches only the LOCAL dev
DB's idempotent migrations.) Walk-forward forecaster: monthly refits on panel rows whose target
window ended before the refit date — no look-ahead.

Acceptance (pre-registered, `tasks/signal-quality/00-index.md` P1–P5) is evaluated at the end.

Run:  python3 scripts/index_sleeve_replay.py [--end YYYY-MM-DD] [--no-yf] [--quick] [--out DIR]
"""
from __future__ import annotations

import argparse
import json
import math
import random
import sqlite3
import statistics
import sys
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "backend"))

import theta_core as tc          # noqa: E402  (pure)
import estimators as est         # noqa: E402  (pure)
import gates                     # noqa: E402  (pure)
import macro_calendar as mc      # noqa: E402  (pure)
import forecast as fc            # noqa: E402  (imports database -> local dev DB migrations only)

SNAP = REPO / "automation" / "staging" / "snap.db"
CACHE_DIR = REPO / "automation" / "staging" / "replay"
PROXY_CACHE = CACHE_DIR / "index_proxies.json"
OUT_DIR = REPO / "docs" / "signal-quality"

SLEEVE = {"SPY": "^VIX", "QQQ": "^VXN", "IWM": "^RVX", "GLD": "^GVZ"}
# When a name's own vol index is unavailable (Cboe RVX is thinly published), fall back to ^VIX
# with the name's own k-calibration — flagged in the report's provenance line.
PROXY_FALLBACK = {"IWM": "^VIX", "QQQ": "^VIX"}
TERM_FRONT, TERM_BACK, VOL_OF_VOL = "^VIX", "^VIX3M", "^VVIX"
HOLD = tc.HOLD_SESSIONS
ANN = tc.ANN

# Named stress windows (peak -> trough, from SPY closes). "Inside" = [start - HOLD sessions, trough].
EVENTS = [
    ("2018-02 Volmageddon", "2018-01-26", "2018-02-08"),
    ("2018-Q4 drawdown", "2018-09-20", "2018-12-24"),
    ("2020-03 COVID crash", "2020-02-19", "2020-03-23"),
    ("2022 bear market", "2022-01-03", "2022-10-12"),
    ("2024-08 carry unwind", "2024-07-16", "2024-08-05"),
    ("2025-04 tariff shock", "2025-02-19", "2025-04-08"),
]
MUST_PASS_070 = {"2020-03 COVID crash", "2022 bear market"}
POST_TROUGH_SESSIONS = 30

# Instrument (standardized short 20Δ put; conventions of the 2026-07 backtest, bt_run.py)
R, SLIP, COMM = 0.04, 0.04, 0.0065
ENTRY_DTE, TARGET_DELTA, PROFIT_TARGET, TIME_EXIT_DTE = 45, 0.20, 0.75, 21
DANGER_UW = tc.CONFIG["danger_underwater_mult"]
SKEW_PTS = {"SPY": 0.04, "QQQ": 0.035, "IWM": 0.03, "GLD": 0.01}   # documented assumption (25Δ put skew, vol pts)

# Gate constants — the [PROVISIONAL] values the live layer uses (CONFIG) + WS3's proposed G5/G6 ones
G5_Z, G5_WINDOW = tc.CONFIG["g5_global_z"], 252
G6_PRE_DAYS, G6_POST_DAYS = 3, 0
VVIX_DANGER = 130.0
V1_ACCEL = 1.10


# ─────────────────────────────────────────────────────────────── data
def _ro(path: Path) -> sqlite3.Connection:
    return sqlite3.connect(f"file:{path}?mode=ro", uri=True)


def load_bars(conn) -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = defaultdict(list)
    for t, d, o, h, l, c, v in conn.execute(
            "SELECT ticker, date, o, h, l, c, v FROM daily_bars WHERE quarantine = 0 ORDER BY ticker, date"):
        out[t].append({"date": d, "o": o, "h": h, "l": l, "c": c, "v": v})
    return dict(out)


def load_index_snapshot(conn) -> dict[str, dict[str, float]]:
    out: dict[str, dict[str, float]] = defaultdict(dict)
    for s, d, c in conn.execute("SELECT symbol, date, c FROM index_daily WHERE c IS NOT NULL"):
        out[s][d] = float(c)
    return dict(out)


def load_atm_iv(conn, tickers) -> dict[str, dict[str, float]]:
    ph = ",".join("?" * len(tickers))
    out: dict[str, dict[str, float]] = defaultdict(dict)
    for t, d, iv in conn.execute(
            f"SELECT ticker, date, atm_iv FROM daily_iv WHERE atm_iv IS NOT NULL AND ticker IN ({ph})", list(tickers)):
        out[t][d] = float(iv)
    return dict(out)


def fetch_proxies_yf(symbols: list[str], period: str = "12y") -> dict[str, dict[str, float]]:
    """yfinance closes for the index symbols, cached locally (provenance recorded)."""
    import yfinance as yf
    out = {}
    for s in symbols:
        df = yf.download(s, period=period, auto_adjust=False, progress=False, threads=False)
        if df is None or df.empty:
            continue
        if hasattr(df.columns, "levels"):
            df.columns = [c[0] for c in df.columns]
        closes = df["Close"] if "Close" in df else df.iloc[:, 0]
        out[s] = {str(idx.date()): float(v) for idx, v in closes.items() if v == v}
    return out


def index_series(symbols: list[str], snap_idx: dict, bars_max_date: str, use_yf: bool) -> tuple[dict, dict]:
    """Per symbol: prefer the snapshot when it reaches within ~5 sessions of the bars; else the
    yfinance cache (refreshed if older than a day). Returns (series, provenance)."""
    series, prov = {}, {}
    cache = {}
    if PROXY_CACHE.exists():
        cache = json.loads(PROXY_CACHE.read_text())
    stale_cache = (not cache) or (datetime.now() - datetime.fromisoformat(cache.get("_fetched", "2000-01-01"))).days > 1
    need_yf = []
    for s in symbols:
        snap = snap_idx.get(s) or {}
        if snap and max(snap) >= (date.fromisoformat(bars_max_date) - timedelta(days=8)).isoformat():
            series[s], prov[s] = snap, f"snap.db (to {max(snap)})"
        else:
            need_yf.append(s)
    if need_yf and use_yf:
        if stale_cache or any(s not in cache for s in need_yf):
            CACHE_DIR.mkdir(parents=True, exist_ok=True)
            fresh = fetch_proxies_yf(need_yf)
            cache.update(fresh)
            cache["_fetched"] = datetime.now().isoformat(timespec="seconds")
            PROXY_CACHE.write_text(json.dumps(cache))
        for s in need_yf:
            if s in cache:
                series[s], prov[s] = cache[s], f"yfinance cache ({cache.get('_fetched', '?')[:10]}, to {max(cache[s])})"
            elif s in snap_idx:
                series[s], prov[s] = snap_idx[s], f"snap.db STALE (to {max(snap_idx[s])})"
    else:
        for s in need_yf:
            if s in snap_idx:
                series[s], prov[s] = snap_idx[s], f"snap.db STALE (to {max(snap_idx[s])})"
    return series, prov


# ─────────────────────────────────────────────────────── math helpers
def ncdf(x):
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def inv_ncdf(p):
    # Acklam's rational approximation (as in bt_run.py)
    a = [-3.969683028665376e+01, 2.209460984245205e+02, -2.759285104469687e+02,
         1.383577518672690e+02, -3.066479806614716e+01, 2.506628277459239e+00]
    b = [-5.447609879822406e+01, 1.615858368580409e+02, -1.556989798598866e+02,
         6.680131188771972e+01, -1.328068155288572e+01]
    c = [-7.784894002430293e-03, -3.223964580411365e-01, -2.400758277161838e+00,
         -2.549732539343734e+00, 4.374664141464968e+00, 2.938163982698783e+00]
    d = [7.784695709041462e-03, 3.224671290700398e-01, 2.445134137142996e+00, 3.754408661907416e+00]
    plow, phigh = 0.02425, 1 - 0.02425
    if p < plow:
        q = math.sqrt(-2 * math.log(p))
        return (((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)
    if p > phigh:
        q = math.sqrt(-2 * math.log(1 - p))
        return -(((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)
    q = p - 0.5; r = q * q
    return (((((a[0]*r+a[1])*r+a[2])*r+a[3])*r+a[4])*r+a[5])*q / (((((b[0]*r+b[1])*r+b[2])*r+b[3])*r+b[4])*r+1)


def put_price(S, K, T, sig):
    if T <= 0:
        return max(0.0, K - S)
    sq = sig * math.sqrt(T)
    d1 = (math.log(S / K) + (R + sig * sig / 2) * T) / sq
    return K * math.exp(-R * T) * ncdf(-(d1 - sq)) - S * ncdf(-d1)


def strike_for_delta(S, T, sig, tgt):
    d1 = -inv_ncdf(tgt)
    return S * math.exp((R + sig * sig / 2) * T - d1 * sig * math.sqrt(T))


def rv_cc(closes: list[float]) -> float | None:
    if len(closes) < 3 or any(c is None or c <= 0 for c in closes):
        return None
    lr = np.diff(np.log(np.asarray(closes, dtype=float)))
    return float(np.std(lr, ddof=1) * math.sqrt(ANN)) if len(lr) > 1 else None


def z_of(x: float, hist: list[float]) -> float | None:
    if len(hist) < 60:
        return None
    sd = statistics.pstdev(hist)
    return (x - statistics.fmean(hist)) / sd if sd > 1e-12 else 0.0


# ─────────────────────────────────────── walk-forward forecaster (no look-ahead)
def build_panel_rows(series_by_ticker: dict, g_by_date: dict) -> list[tuple]:
    """Mirror of forecast.ForecastEngine.build_panel, but each row keeps its target-end date so
    monthly refits can select rows whose forward window ended BEFORE the refit date."""
    rows = []
    ln_ann = math.log(ANN)
    for snaps in series_by_ticker.values():
        v = [s["v"] for s in snaps]
        sn = [s["s_neg"] for s in snaps]
        for i in range(len(snaps) - HOLD):
            snap = snaps[i]
            g, vbar = g_by_date.get(snap["date"]), snap["vbar"]
            if g is None or g <= 0 or vbar <= 0:
                continue
            rvfwd = (ANN / HOLD) * sum(v[i + 1: i + 1 + HOLD])
            rvfwd_dn = (ANN / HOLD) * sum(sn[i + 1: i + 1 + HOLD])
            if rvfwd <= 0:
                continue
            base = math.log(vbar) + ln_ann
            rows.append((snaps[i + HOLD]["date"], tc.forecast_features(fc._StateView(snap), g),
                         math.log(rvfwd) - base, math.log(max(rvfwd_dn, 1e-12)) - base))
    rows.sort(key=lambda r: r[0])
    return rows


class WalkForward:
    """Monthly refits: for month M the model is fit on panel rows with target_end < first session of M."""

    def __init__(self, panel_rows: list[tuple]):
        self.end_dates = np.array([r[0] for r in panel_rows])
        self.X = np.array([r[1] for r in panel_rows])
        self.yt = np.array([r[2] for r in panel_rows])
        self.yd = np.array([r[3] for r in panel_rows])
        self._month = None
        self.engine = fc.ForecastEngine()
        self.refits: list[tuple[str, int, bool]] = []

    def ensure(self, session_date: str) -> None:
        m = session_date[:7]
        if m == self._month:
            return
        mask = self.end_dates < session_date
        eng = fc.ForecastEngine()
        n = int(mask.sum())
        if n:
            eng.fc_total.fit(self.X[mask], self.yt[mask])
            eng.fc_dn.fit(self.X[mask], self.yd[mask])
        eng.n_obs = eng.fc_total.n_obs
        eng.fitted = eng.n_obs >= tc.CONFIG["min_pooled_obs"]
        self.engine, self._month = eng, m
        self.refits.append((m, n, eng.fitted))

    def predict(self, snap: dict, g: float) -> tuple[float, float, bool]:
        sf, sfd = self.engine.predict(snap, g)
        return sf, sfd, self.engine.fitted


# ───────────────────────────────────────────────────────── the replay
def replay(bars: dict, idx: dict, atm_iv: dict, end: str | None, quick: bool) -> dict:
    tickers_all = sorted(bars)
    proxy_sym: dict[str, str] = {}
    for t, s in SLEEVE.items():
        if t not in bars:
            continue
        if s in idx and len(idx[s]) > 500:
            proxy_sym[t] = s
        elif PROXY_FALLBACK.get(t) in idx:
            proxy_sym[t] = PROXY_FALLBACK[t]
    sleeve = list(proxy_sym)
    series = {t: est.replay_ewma_series(est.bars_to_daily_inputs(bars[t])) for t in tickers_all}
    g_by_date, g_mean = fc.build_global_factor(series)
    wf = WalkForward(build_panel_rows(series, g_by_date))

    # proxy level calibration k = median(atm_iv/100 / proxy/100) over the overlap
    k, k_n = {}, {}
    for t in sleeve:
        ps = idx[proxy_sym[t]]
        ratios = [atm_iv[t][d] / ps[d] for d in atm_iv.get(t, {}) if d in ps and ps[d] > 0]
        k[t] = statistics.median(ratios) if len(ratios) >= 30 else 1.0
        k_n[t] = len(ratios)

    master = [b["date"] for b in bars["SPY"]]
    if end:
        master = [d for d in master if d <= end]
    if quick:
        master = [d for d in master if d >= "2017-06-01"]
    pos = {t: {b["date"]: i for i, b in enumerate(bars[t])} for t in sleeve}
    snap_at = {t: {s["date"]: s for s in series[t]} for t in sleeve}
    daily_in = {t: {s["date"]: s for s in series[t]} for t in sleeve}   # snapshots carry s_neg for concentration

    gs = {t: tc.GateState() for t in sleeve}
    fvrp_hist: dict[str, list[float]] = {t: [] for t in sleeve}
    g_diff_hist: list[float] = []
    g_dates = sorted(g_mean)
    g_pos = {d: i for i, d in enumerate(g_dates)}

    rows: list[dict] = []
    for d in master:
        wf.ensure(d)
        vix, vix3m, vvix = idx[TERM_FRONT].get(d), idx[TERM_BACK].get(d), idx.get(VOL_OF_VOL, {}).get(d)
        slope = (vix / vix3m) if (vix and vix3m) else None
        # G5 inputs: SPY proxy FVRP (computed below in ticker order — SPY first) + global-factor 20-session Δ z
        gi = g_pos.get(d)
        gz = None
        if gi is not None and gi >= 20:
            diff = g_mean[g_dates[gi]] - g_mean[g_dates[gi - 20]]
            gz = z_of(diff, g_diff_hist[-G5_WINDOW:])
            g_diff_hist.append(diff)
        g6_fomc, g6_kind, g6_dte = mc.in_window(date.fromisoformat(d), G6_PRE_DAYS, G6_POST_DAYS, kinds=("FOMC",))
        g6_all, _, _ = mc.in_window(date.fromisoformat(d), G6_PRE_DAYS, G6_POST_DAYS)
        index_fvrp = None
        for t in sorted(sleeve, key=lambda x: 0 if x == "SPY" else 1):
            i = pos[t].get(d)
            snap = snap_at[t].get(d)
            proxy = idx[proxy_sym[t]].get(d)
            if i is None or snap is None or not proxy or slope is None or i < 30:
                continue
            g = g_by_date.get(d) or 1.0
            sf, sfd, fitted = wf.predict(snap, g)
            a5, a25 = snap["e_sneg"].get(5), snap["e_sneg"].get(25)
            accel_dn = math.sqrt(a5 / a25) if (a5 and a25 and a25 > 0) else 1.0
            conc = est.concentration_10d([daily_in[t][x["date"]] for x in bars[t][max(0, i - 9): i + 1] if x["date"] in daily_in[t]])
            iv_raw = proxy / 100.0
            iv_adj = iv_raw * k[t]
            closes = [b["c"] for b in bars[t][i - 30: i + 1]]
            rv30 = rv_cc(closes)
            rv10 = rv_cc([b["c"] for b in bars[t][i - 10: i + 1]])
            fv = tc.fvrp(iv_adj, sf, log_hist=fvrp_hist[t][-252:])
            fvrp_hist[t].append(fv["ratio"])
            fv_raw = tc.fvrp(iv_raw, sf)
            veto_trail = tc.fvrp_veto_ratio(iv_adj, sf, rv30)
            if t == "SPY":
                index_fvrp = fv["ratio"]
            frozen = (index_fvrp is not None and index_fvrp < 1.0) or (gz is not None and gz > G5_Z)
            # gate state machine (G2 on the market term proxy, G3 from bars) + eligibility
            st = gs[t]
            st.update(slope, accel_dn, conc)
            el = gates.evaluate_eligibility(st, is_etf=True, fvrp_ratio=fv["ratio"],
                                            abs_premium_volpts=fv["abs_premium_volpts"], earnings_dte=None,
                                            accel_dn=accel_dn, slope_1m3m=slope, book_frozen=frozen)
            # forward capture (the target) — needs HOLD forward closes
            fwd = [b["c"] for b in bars[t][i: i + HOLD + 1]]
            rvf = rv_cc(fwd) if len(fwd) == HOLD + 1 else None
            cap = tc.realized_capture(iv_adj, rvf)["var_points"] if rvf else None
            cap_raw = tc.realized_capture(iv_raw, rvf)["var_points"] if rvf else None
            rows.append({
                "date": d, "ticker": t, "spot": bars[t][i]["c"], "iv_raw": iv_raw, "iv_adj": iv_adj,
                "sigma_fwd": sf, "sigma_fwd_dn": sfd, "fitted": fitted, "fvrp": fv["ratio"], "fvrp_raw": fv_raw["ratio"],
                "fvrp_z": fv["z"], "veto_trail": veto_trail, "abs_prem": fv["abs_premium_volpts"],
                "slope": slope, "accel_dn": accel_dn, "conc": conc, "rv30": rv30, "rv10": rv10,
                "gate": st.state, "transient": st.transient, "blackout": st._blackout,
                "eligible": el.eligible, "reasons": el.ineligibility_reasons,
                "index_fvrp": index_fvrp, "gz": gz, "frozen": frozen,
                "vix": vix, "vix3m": vix3m, "vvix": vvix,
                "g6_fomc": g6_fomc, "g6_all": g6_all, "g6_dte": g6_dte,
                "capture": cap, "capture_raw": cap_raw, "rv_fwd": rvf,
                # individual veto signals (raw triggers, for attribution)
                "v_g2": slope >= tc.CONFIG["g2_caution_in"],
                "v_g3": accel_dn >= tc.CONFIG["g3_in"],
                "v_g4": fv["ratio"] < 1.0,
                "v_dz": 1.0 <= fv["ratio"] < tc.CONFIG["dead_zone_index"],
                "v_g5": frozen,
                "v_g6": g6_fomc,
                "v_transient": st.transient or st._blackout > 0,
                "v_v2": (not el.eligible) or g6_fomc,           # the v2 layer incl. G5/G6 proposals
                "v_v2_core": not el.eligible,                   # without G6
                "v_bwd": vix > vix3m, "v_vvix": bool(vvix and vvix > VVIX_DANGER),
                "v_v1_accel": bool(rv10 and rv30 and rv10 / rv30 > V1_ACCEL),
                "v_v1_negvrp": bool(rv30 and iv_adj < rv30),
            })
            rows[-1]["v_v1"] = rows[-1]["v_v1_accel"] or rows[-1]["v_v1_negvrp"] or rows[-1]["v_bwd"] or rows[-1]["v_vvix"]
            rows[-1]["v_max_den"] = veto_trail < 1.0 or veto_trail < tc.CONFIG["dead_zone_index"]
            # T1-style sensitivity: the SAME v2 layer with the denominator swapped to trailing RV30
            # (v1's measure) — separates the layer's DESIGN from the forecaster's calibration.
            fr30 = (iv_adj / rv30) if rv30 else None
            rows[-1]["fvrp_rv30"] = fr30
            state_veto = (st.state != "NORMAL") or st.transient or st._blackout > 0
            rows[-1]["v_g4_rv30"] = bool(fr30 is not None and fr30 < 1.0)
            rows[-1]["v_v2_rv30"] = state_veto or fr30 is None or fr30 < 1.0 or fr30 < tc.CONFIG["dead_zone_index"] \
                or (iv_adj - rv30) * 100.0 < tc.CONFIG["abs_premium_floor_volpts"]
            rows[-1]["v_v2_rv30_g5g6"] = rows[-1]["v_v2_rv30"] or g6_fomc or (gz is not None and gz > G5_Z) \
                or (t != "SPY" and rows[-1]["index_fvrp"] is not None and False)   # G5's index leg re-evaluated below
            rows[-1]["v_state"] = state_veto
    return {"rows": rows, "sleeve": sleeve, "k": k, "k_n": k_n, "refits": wf.refits, "master": master,
            "proxy_sym": proxy_sym}


# ───────────────────────────────────────────────────── instrument leg
def simulate_puts(rows_by_ticker: dict[str, list[dict]], bars: dict) -> dict[str, list[dict]]:
    """Standardized short 20Δ put entered at the NEXT session's close after each row's date, marked
    daily with the (carried) proxy IV, exits per the live rules. Returns per-row trade outcomes."""
    out: dict[str, list[dict]] = {}
    for t, rows in rows_by_ticker.items():
        idx = {r["date"]: r for r in rows}
        b = bars[t]
        pos = {x["date"]: i for i, x in enumerate(b)}
        trades = []
        for r in rows:
            i = pos.get(r["date"])
            if i is None or i + 1 >= len(b):
                trades.append(None); continue
            e = i + 1
            S0 = b[e]["c"]
            sig0 = r["iv_adj"] + SKEW_PTS.get(t, 0.03)
            T0 = ENTRY_DTE / 365.0
            K = strike_for_delta(S0, T0, sig0, TARGET_DELTA)
            gross = put_price(S0, K, T0, sig0)
            credit = gross * (1 - SLIP) - COMM
            margin = tc.margin_short_put(gross, S0, K)
            exit_px, exit_why, j = None, None, e + 1
            cal_entry = date.fromisoformat(b[e]["date"])
            last_sig = sig0
            while j < len(b):
                dte = ENTRY_DTE - (date.fromisoformat(b[j]["date"]) - cal_entry).days
                rj = idx.get(b[j]["date"])
                if rj is not None:
                    last_sig = rj["iv_adj"] + SKEW_PTS.get(t, 0.03)
                if dte <= 0:
                    exit_px, exit_why = max(0.0, K - b[j]["c"]), "expiry"; break
                px = put_price(b[j]["c"], K, dte / 365.0, last_sig)
                if px <= (1 - PROFIT_TARGET) * gross:
                    exit_px, exit_why = px * (1 + SLIP) + COMM, "profit_target"; break
                if dte <= TIME_EXIT_DTE:
                    exit_px, exit_why = px * (1 + SLIP) + COMM, "time_21dte"; break
                if rj is not None and rj["gate"] == "DANGER" and px >= DANGER_UW * gross:
                    exit_px, exit_why = px * (1 + SLIP) + COMM, "danger_underwater"; break
                j += 1
            if exit_px is None:
                trades.append(None); continue          # censored (no exit inside the data)
            pnl = credit - exit_px
            trades.append({"entry": b[e]["date"], "exit": b[min(j, len(b) - 1)]["date"], "K": round(K, 2),
                           "credit": credit, "pnl": pnl, "margin": margin,
                           "pnl_per_margin": (pnl * 100.0 / margin) if margin > 0 else None, "why": exit_why})
        out[t] = trades
    return out


# ────────────────────────────────────────────────────────── metrics
def label_sessions(master: list[str]) -> dict:
    """inside-event / post-trough labels per master session; window bounds by index."""
    mpos = {d: i for i, d in enumerate(master)}

    def first_at_or_after(s):
        for d in master:
            if d >= s:
                return mpos[d]
        return None
    ev = []
    for name, start, trough in EVENTS:
        si, ti = first_at_or_after(start), first_at_or_after(trough)
        if si is None or ti is None:
            continue
        ev.append({"name": name, "start": start, "trough": trough, "in_lo": max(0, si - HOLD), "in_hi": ti,
                   "post_lo": ti + 1, "post_hi": min(len(master) - 1, ti + POST_TROUGH_SESSIONS), "start_idx": si, "trough_idx": ti})
    inside, post = {}, {}
    for e in ev:
        for i in range(e["in_lo"], e["in_hi"] + 1):
            inside[master[i]] = e["name"]
        for i in range(e["post_lo"], e["post_hi"] + 1):
            post[master[i]] = e["name"]
    return {"events": ev, "inside": inside, "post": post}


def gate_metrics(rows: list[dict], flag: str, labels: dict) -> dict:
    inside, post = labels["inside"], labels["post"]
    by_date: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        by_date[r["date"]].append(r)
    res = [r for r in rows if r["capture"] is not None]
    loss_in = [r for r in res if r["capture"] < 0 and r["date"] in inside]
    win_out = [r for r in res if r["capture"] > 0 and r["date"] not in inside and r["date"] not in post]
    win_post = [r for r in res if r["capture"] > 0 and r["date"] in post]
    lw_tot = sum(-r["capture"] for r in loss_in)
    lw_veto = sum(-r["capture"] for r in loss_in if r[flag])
    per_event = {}
    for e in labels["events"]:
        li = [r for r in loss_in if inside.get(r["date"]) == e["name"]]
        tot = sum(-r["capture"] for r in li)
        vet = sum(-r["capture"] for r in li if r[flag])
        wp = [r for r in win_post if post.get(r["date"]) == e["name"]]
        # lead: sessions from the first veto inside the window to the window start; dwell: sessions after trough still vetoed
        inside_dates = sorted(d for d in by_date if inside.get(d) == e["name"])
        first_veto = next((d for d in inside_dates if any(r[flag] for r in by_date[d])), None)
        lead = None
        if first_veto:
            start_d = next((d for d in inside_dates if d >= e["start"]), None)
            lead = (inside_dates.index(start_d) - inside_dates.index(first_veto)) if start_d else None
        post_dates = sorted(d for d in by_date if post.get(d) == e["name"])
        dwell = 0
        for d in post_dates:
            if all(r[flag] for r in by_date[d]):
                dwell += 1
            else:
                break
        per_event[e["name"]] = {"recall_lw": (vet / tot) if tot else None, "n_loss_days": len(li),
                                "recall_days": (sum(1 for r in li if r[flag]) / len(li)) if li else None,
                                "release_clear": (sum(1 for r in wp if not r[flag]) / len(wp)) if wp else None,
                                "lead_sessions": lead, "dwell_after_trough": dwell}
    return {
        "recall_lw": (lw_veto / lw_tot) if lw_tot else None,
        "recall_days": (sum(1 for r in loss_in if r[flag]) / len(loss_in)) if loss_in else None,
        "clearance_out": (sum(1 for r in win_out if not r[flag]) / len(win_out)) if win_out else None,
        "veto_share_out_win": (sum(1 for r in win_out if r[flag]) / len(win_out)) if win_out else None,
        "false_veto_cost": (statistics.fmean(r["capture"] for r in win_out if r[flag]) if any(r[flag] for r in win_out) else None),
        "release_clear": (sum(1 for r in win_post if not r[flag]) / len(win_post)) if win_post else None,
        "n_loss_in": len(loss_in), "n_win_out": len(win_out), "n_win_post": len(win_post),
        "per_event": per_event,
    }


def bootstrap_lb(rows: list[dict], flag: str, labels: dict, n_boot: int = 2000, seed: int = 7) -> float | None:
    """One-sided 90% lower bound of the pooled loss-weighted recall, block-bootstrapping MONTHS."""
    inside = labels["inside"]
    by_month: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        if r["capture"] is not None and r["capture"] < 0 and r["date"] in inside:
            by_month[r["date"][:7]].append(r)
    months = sorted(by_month)
    if len(months) < 3:
        return None
    rng = random.Random(seed)
    vals = []
    for _ in range(n_boot):
        pick = [months[rng.randrange(len(months))] for _ in months]
        tot = sum(-r["capture"] for m in pick for r in by_month[m])
        vet = sum(-r["capture"] for m in pick for r in by_month[m] if r[flag])
        if tot:
            vals.append(vet / tot)
    vals.sort()
    return vals[int(0.10 * len(vals))] if vals else None


def evaluate_acceptance(m_v2: dict, lb: float | None, m_v1: dict, per_gate: dict) -> dict:
    pe = m_v2["per_event"]
    ev_ok = [n for n, v in pe.items() if v["recall_lw"] is not None and v["recall_lw"] >= 0.50]
    must = all((pe.get(n, {}).get("recall_lw") or 0) >= 0.70 for n in MUST_PASS_070)
    flags = {g: v["veto_share_out_win"] for g, v in per_gate.items() if v["veto_share_out_win"] is not None and v["veto_share_out_win"] > 0.40}
    rel_ok = sum(1 for v in pe.values() if v["release_clear"] is not None and v["release_clear"] >= 0.50)
    return {
        "P1": {"pass": (m_v2["recall_lw"] or 0) >= 0.80 and (lb or 0) >= 0.70, "recall_lw": m_v2["recall_lw"], "lb90": lb},
        "P2": {"pass": len(ev_ok) >= 5 and must, "events_ge_050": ev_ok, "must_pass_070": must},
        "P3": {"pass": (m_v2["clearance_out"] or 0) >= 0.50, "clearance_out": m_v2["clearance_out"], "calibration_flags": flags},
        "P4": {"pass": rel_ok >= 4, "events_release_ge_050": rel_ok},
        "P5": {"pass": (m_v2["recall_lw"] or 0) >= (m_v1["recall_lw"] or 0), "v2": m_v2["recall_lw"], "v1": m_v1["recall_lw"]},
    }


# ────────────────────────────────────────────────────────── report
def _pct(x):
    return "—" if x is None else f"{x*100:.0f}%"


def _f(x, n=2):
    return "—" if x is None else f"{x:.{n}f}"


def write_report(res: dict, labels: dict, per_gate: dict, lb: float, acc: dict, sens: dict, trades: dict,
                 prov: dict, out_dir: Path, run_date: str) -> Path:
    rows = res["rows"]
    n_res = sum(1 for r in rows if r["capture"] is not None)
    L = []
    L.append(f"# X1 — Index-sleeve 10-year gate replay ({run_date})\n")
    L.append("Trial `X1-2026-09-index-sleeve-replay` · **report-only** (P2) · harness `scripts/index_sleeve_replay.py` · "
             "acceptance P1–P5 pre-registered in `tasks/signal-quality/00-index.md` (confirmed by the user 2026-09-03).\n")
    L.append("## Data & method\n")
    L.append(f"- Sleeve: {', '.join(res['sleeve'])} on IV proxies "
             f"{', '.join(f'{t}←{res['proxy_sym'][t]}' + (' (FALLBACK — own index unavailable)' if res['proxy_sym'][t] != SLEEVE[t] else '') for t in res['sleeve'])}; "
             f"sessions {res['master'][0]} → {res['master'][-1]} ({len(res['master'])}); ticker-days {len(rows)}, resolved (21 fwd sessions) {n_res}.")
    L.append("- Provenance: " + "; ".join(f"{s}: {p}" for s, p in prov.items()) + ".")
    L.append("- Proxy level calibration k = median(atm_iv / proxy) over the 2025–26 overlap: " +
             ", ".join(f"{t} {res['k'][t]:.3f} (n={res['k_n'][t]})" for t in res["sleeve"]) + ". All FVRP/capture figures use the k-adjusted proxy unless marked raw.")
    fitted = [m for m, n, f in res["refits"] if f]
    L.append(f"- Walk-forward forecaster: {len(res['refits'])} monthly refits, each on panel rows whose target window ended before the refit month; "
             f"fitted (≥{tc.CONFIG['min_pooled_obs']} pooled obs) from {fitted[0] if fitted else '—'}; earlier months run on seed betas and are flagged.")
    L.append(f"- Target: `capture = (IV_adj² − RV_cc(t→t+21)²)·1e4` (the live `capture_30d` definition). Loss day = capture < 0. "
             f"Inside-event = [window start − {HOLD} sessions, trough]; post-trough = {POST_TROUGH_SESSIONS} sessions after the trough; outside = the rest.")
    L.append("- Gates replayed with the live CONFIG (G2 on the VIX/VIX3M market proxy, G3/transient from bars, G4 + dead zone on k-adjusted FVRP, "
             f"G5 = SPY FVRP < 1 or 20-session ΔG_t z > {G5_Z} over {G5_WINDOW}, G6 = FOMC window −{G6_PRE_DAYS}d..0d); overlays VIX>VIX3M, VVIX>{VVIX_DANGER:.0f}; "
             f"v1 layer = rv10/rv30 > {V1_ACCEL} or negative trailing VRP or the overlays.\n")
    L.append("## Event windows\n")
    L.append("| Event | Peak | Trough | Loss-day sessions |\n|---|---|---|---|")
    for e in labels["events"]:
        L.append(f"| {e['name']} | {e['start']} | {e['trough']} | {e['in_hi'] - e['in_lo'] + 1} |")
    L.append("\n## Acceptance (P1–P5)\n")
    L.append("| Criterion | Result | Detail |\n|---|---|---|")
    L.append(f"| P1 pooled loss-weighted recall ≥ 0.80, LB90 ≥ 0.70 | **{'PASS' if acc['P1']['pass'] else 'FAIL'}** | recall {_pct(acc['P1']['recall_lw'])}, LB90 {_pct(acc['P1']['lb90'])} |")
    L.append(f"| P2 per-event ≥ 0.50 in ≥ 5/6, ≥ 0.70 in 2020-03 + 2022 | **{'PASS' if acc['P2']['pass'] else 'FAIL'}** | ≥0.50: {len(acc['P2']['events_ge_050'])}/6; must-pass: {acc['P2']['must_pass_070']} |")
    L.append(f"| P3 outside-event win-day clearance ≥ 0.50 | **{'PASS' if acc['P3']['pass'] else 'FAIL'}** | clearance {_pct(acc['P3']['clearance_out'])}; calibration flags (>40% veto share): {', '.join(f'{g} {_pct(v)}' for g, v in acc['P3']['calibration_flags'].items()) or 'none'} |")
    L.append(f"| P4 post-trough release ≥ 0.50 in ≥ 4/6 | **{'PASS' if acc['P4']['pass'] else 'FAIL'}** | {acc['P4']['events_release_ge_050']}/6 |")
    L.append(f"| P5 v2 layer ≥ v1 live index vetoes | **{'PASS' if acc['P5']['pass'] else 'FAIL'}** | v2 {_pct(acc['P5']['v2'])} vs v1 {_pct(acc['P5']['v1'])} |")
    L.append("\n## Per-gate attribution (pooled)\n")
    L.append("| Gate | Recall (loss-wtd) | Recall (days) | Clearance outside | Veto share of outside win days | False-veto cost (mean capture) | Release clear |\n|---|---|---|---|---|---|---|")
    for g, m in per_gate.items():
        L.append(f"| {g} | {_pct(m['recall_lw'])} | {_pct(m['recall_days'])} | {_pct(m['clearance_out'])} | {_pct(m['veto_share_out_win'])} | {_f(m['false_veto_cost'], 0)} | {_pct(m['release_clear'])} |")
    L.append("\n## Per-event (v2 any-veto layer)\n")
    L.append("| Event | Recall (loss-wtd) | Recall (days) | Loss days | Lead (sessions before peak) | Dwell after trough | Release clear |\n|---|---|---|---|---|---|---|")
    for n, v in per_gate["v2 any-veto (core+G5+G6)"]["per_event"].items():
        L.append(f"| {n} | {_pct(v['recall_lw'])} | {_pct(v['recall_days'])} | {v['n_loss_days']} | {v['lead_sessions'] if v['lead_sessions'] is not None else '—'} | {v['dwell_after_trough']} | {_pct(v['release_clear'])} |")
    L.append("\n## Sensitivity (reported, not adopted)\n")
    L.append("| Variant | Recall (loss-wtd) | Clearance outside | Release |\n|---|---|---|---|")
    for name, m in sens.items():
        L.append(f"| {name} | {_pct(m['recall_lw'])} | {_pct(m['clearance_out'])} | {_pct(m['release_clear'])} |")
    L.append("\n## Instrument leg (standardized 20Δ put, model-priced — a sketch, not a measurement)\n")
    L.append("| Ticker | Trades | Win rate | Mean P&L/share (all days) | Mean P&L (v2-cleared) | Mean P&L (v2-vetoed) | Mean P&L (v1-cleared) |\n|---|---|---|---|---|---|---|")
    for t, tr in trades.items():
        rs = [r for r in rows if r["ticker"] == t]
        pairs = [(r, x) for r, x in zip(rs, tr) if x is not None]
        if not pairs:
            continue
        def mean_pnl(sel):
            xs = [x["pnl"] for r, x in pairs if sel(r)]
            return statistics.fmean(xs) if xs else None
        wins = sum(1 for _, x in pairs if x["pnl"] > 0) / len(pairs)
        L.append(f"| {t} | {len(pairs)} | {_pct(wins)} | {_f(mean_pnl(lambda r: True), 3)} | {_f(mean_pnl(lambda r: not r['v_v2']), 3)} | {_f(mean_pnl(lambda r: r['v_v2']), 3)} | {_f(mean_pnl(lambda r: not r['v_v1']), 3)} |")
    L.extend([""] + diagnostics(res, labels, rows, trades))
    L.append("\n## Caveats\n")
    L.append("- IV proxies are 30-day model-free variance indices, not ATM BSM IV; the k-adjustment removes the level gap on the overlap but not its time variation. "
             "Per-name G2 (1M/3M) is not replayable (no historical chains) — the market term proxy stands in for every sleeve name.")
    L.append("- Seed-beta months (before the forecaster reaches the pooled-obs minimum) are flagged in `refits`; the instrument leg uses fixed skew offsets and model fills.")
    L.append("- Overlapping 21-session windows: every CI is block-bootstrapped by month; raw ticker-day counts are not independent samples.")
    L.append(f"- G5/G6 use WS3's proposed [PROVISIONAL] constants (z {G5_Z}, window {G5_WINDOW}; FOMC −{G6_PRE_DAYS}d). Nothing here changes CONFIG (P2/P3).")
    out_dir.mkdir(parents=True, exist_ok=True)
    p = out_dir / f"X1-index-sleeve-replay-{run_date}.md"
    p.write_text("\n".join(L) + "\n")
    return p


def diagnostics(res: dict, labels: dict, rows: list[dict], trades: dict) -> list[str]:
    """Forecaster bias vs realized, and what the SAME layer does with a bias-corrected σ_fwd
    (per-ticker in-sample median correction — flagged) across dead zones. Reported, not adopted."""
    L = ["## Diagnostics — forecaster bias and the calibration-corrected layer (in-sample, flagged)\n"]
    L.append("| Ticker | capture>0 share | FVRP<1 share | FVRP<1.20 share | IV/RV30<1 share | median ln(σ_fwd/RV_fwd) | median ln(RV30/RV_fwd) | log-MAE σ_fwd | log-MAE RV30 | state-only veto share |\n|---|---|---|---|---|---|---|---|---|---|")
    bias = {}
    for t in res["sleeve"]:
        rs = [r for r in rows if r["ticker"] == t and r["capture"] is not None and r["fitted"]]
        if not rs:
            continue
        bias[t] = statistics.median(math.log(r["sigma_fwd"] / r["rv_fwd"]) for r in rs)
        b30 = statistics.median(math.log(r["rv30"] / r["rv_fwd"]) for r in rs if r["rv30"])
        mae_sf = statistics.fmean(abs(math.log(r["sigma_fwd"] / r["rv_fwd"])) for r in rs)
        mae_30 = statistics.fmean(abs(math.log(r["rv30"] / r["rv_fwd"])) for r in rs if r["rv30"])
        L.append(f"| {t} | {_pct(sum(1 for r in rs if r['capture'] > 0) / len(rs))} | {_pct(sum(1 for r in rs if r['fvrp'] < 1) / len(rs))} | "
                 f"{_pct(sum(1 for r in rs if r['fvrp'] < tc.CONFIG['dead_zone_index']) / len(rs))} | "
                 f"{_pct(sum(1 for r in rs if r['fvrp_rv30'] and r['fvrp_rv30'] < 1) / len(rs))} | {bias[t]:+.3f} | {b30:+.3f} | "
                 f"{mae_sf:.3f} | {mae_30:.3f} | {_pct(sum(1 for r in rs if r['v_state']) / len(rs))} |")
    L.append("\nReading rule: `capture>0 share` is how often selling was actually paid; `FVRP<1 share` is how often the forecaster said there was no forward premium. "
             "A gap between them is forecaster bias, not edge. `ln(σ_fwd/RV_fwd)` > 0 means σ_fwd over-forecasts realized close-to-close vol (the `+½·resid_var` log-normal mean correction targets E[variance], "
             "while capture is defined on realized vol).\n")
    spy = {r["date"]: r for r in rows if r["ticker"] == "SPY"}

    def corrected(dz):
        for r in rows:
            b = bias.get(r["ticker"], 0.0)
            f = r["fvrp"] * math.exp(b)
            prem = (r["iv_adj"] - r["sigma_fwd"] / math.exp(b)) * 100.0
            sp = spy.get(r["date"])
            idx_f = (sp["fvrp"] * math.exp(bias.get("SPY", 0.0))) if sp else None
            frozen = (idx_f is not None and idx_f < 1.0) or (r["gz"] is not None and r["gz"] > G5_Z)
            r["v_diag"] = r["v_state"] or f < 1.0 or f < dz or prem < tc.CONFIG["abs_premium_floor_volpts"] or frozen or r["g6_fomc"]
        return gate_metrics(rows, "v_diag", labels), bootstrap_lb(rows, "v_diag", labels, n_boot=500)

    L.append("| Layer variant | Recall (loss-wtd) | LB90 | Clearance outside | Release | Events ≥ 0.50 | 2020 / 2022 must-pass | Release ≥ 0.50 events |\n|---|---|---|---|---|---|---|---|")
    for dz in (tc.CONFIG["dead_zone_index"], 1.10, 1.00):
        m, lb = corrected(dz)
        pe = m["per_event"]
        ok = sum(1 for v in pe.values() if (v["recall_lw"] or 0) >= 0.5)
        must = all((pe.get(n, {}).get("recall_lw") or 0) >= 0.7 for n in MUST_PASS_070)
        rel = sum(1 for v in pe.values() if (v["release_clear"] or 0) >= 0.5)
        L.append(f"| bias-corrected σ_fwd, dead zone {dz:.2f}, G5+G6 | {_pct(m['recall_lw'])} | {_pct(lb)} | {_pct(m['clearance_out'])} | {_pct(m['release_clear'])} | {ok}/6 | {must} | {rel}/6 |")
    # instrument leg under the corrected layer at the live dead zone
    corrected(tc.CONFIG["dead_zone_index"])
    L.append("\n| Ticker | Corrected-layer cleared n | Mean P&L/share cleared | Vetoed n | Mean P&L vetoed | All days |\n|---|---|---|---|---|---|")
    for t in res["sleeve"]:
        rs = [r for r in rows if r["ticker"] == t]
        pairs = [(r, x) for r, x in zip(rs, trades.get(t, [])) if x is not None]
        cl = [x["pnl"] for r, x in pairs if not r["v_diag"]]
        ve = [x["pnl"] for r, x in pairs if r["v_diag"]]
        if pairs:
            L.append(f"| {t} | {len(cl)} | {_f(statistics.fmean(cl), 3) if cl else '—'} | {len(ve)} | {_f(statistics.fmean(ve), 3) if ve else '—'} | {_f(statistics.fmean(x['pnl'] for _, x in pairs), 3)} |")
    L.append("")
    return L


def kelly_seed_candidate(trades: dict, out_dir: Path, run_date: str) -> Path | None:
    pnl, months = [], []
    for t, tr in trades.items():
        for x in tr:
            if x and x["pnl_per_margin"] is not None:
                pnl.append(round(x["pnl_per_margin"], 6)); months.append(x["entry"][:7])
    if len(pnl) < tc.CONFIG["kelly_min_trades"]:
        return None
    f_star = tc.kelly_base(np.asarray(pnl), np.asarray(months), rng=np.random.default_rng(0), n_boot=500)
    p = out_dir / "X1-kelly-seed-candidate.json"
    p.write_text(json.dumps({"generated": run_date, "source": "X1 index-sleeve replay (model-priced 20Δ puts on IV proxies, 2016→)",
                             "cohorts": ["index-sleeve, all sessions (overlapping daily entries)"], "n_trades": len(pnl),
                             "n_months": len(set(months)), "f_star_seed": round(float(f_star), 4),
                             "note": "CANDIDATE ONLY — backend/kelly_seed.json untouched; overlapping entries are not uniqueness-weighted (AFML caveat).",
                             "pnl_per_margin": pnl, "months": months}, indent=1))
    return p


# ─────────────────────────────────────────────────────────── main
def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="X1 index-sleeve gate replay (report-only).")
    ap.add_argument("--end", default=None); ap.add_argument("--no-yf", action="store_true")
    ap.add_argument("--quick", action="store_true", help="2017-06 onward (faster smoke run)")
    ap.add_argument("--out", default=str(OUT_DIR)); ap.add_argument("--snap", default=str(SNAP))
    ap.add_argument("--n-boot", type=int, default=2000)
    a = ap.parse_args(argv)
    run_date = date.today().isoformat()
    conn = _ro(Path(a.snap))
    try:
        bars = load_bars(conn)
        snap_idx = load_index_snapshot(conn)
        atm_iv = load_atm_iv(conn, list(SLEEVE))
    finally:
        conn.close()
    bars_max = max(b["date"] for b in bars["SPY"])
    idx, prov = index_series([TERM_FRONT, TERM_BACK, VOL_OF_VOL] + list(SLEEVE.values()), snap_idx, bars_max, use_yf=not a.no_yf)
    missing = [s for s in (TERM_FRONT, TERM_BACK) if s not in idx]
    if missing:
        print(f"ERROR: term proxies missing {missing}", file=sys.stderr); return 2
    print(f"bars to {bars_max}; index series: " + "; ".join(f"{s}: {p}" for s, p in prov.items()))
    res = replay(bars, idx, atm_iv, a.end, a.quick)
    rows = res["rows"]
    labels = label_sessions(res["master"])
    # G5's index leg on the trailing denominator (SPY iv/rv30 < 1) for the rv30 variant
    spy_fr30 = {r["date"]: r["fvrp_rv30"] for r in rows if r["ticker"] == "SPY"}
    for r in rows:
        f = spy_fr30.get(r["date"])
        r["v_v2_rv30_g5g6"] = r["v_v2_rv30"] or r["g6_fomc"] or (r["gz"] is not None and r["gz"] > G5_Z) or (f is not None and f < 1.0)
    gate_flags = {
        "v2 any-veto (core+G5+G6)": "v_v2", "v2 core (state machine + dead zone)": "v_v2_core",
        "state machine only (G2 proxy/G3/transient, no FVRP)": "v_state",
        "v2 layer with TRAILING RV30 denominator (T1 variant)": "v_v2_rv30_g5g6",
        "G4 negative FVRP on trailing RV30": "v_g4_rv30",
        "G2 term proxy (VIX/VIX3M ≥ caution)": "v_g2", "G3 downside accel": "v_g3", "G4 negative FVRP": "v_g4",
        "dead zone (1.0 ≤ FVRP < 1.20)": "v_dz", "G5 book freeze": "v_g5", "G6 FOMC window": "v_g6",
        "transient/blackout": "v_transient", "overlay VIX>VIX3M": "v_bwd", "overlay VVIX>130": "v_vvix",
        "v1 rv10/rv30 > 1.10": "v_v1_accel", "v1 negative trailing VRP": "v_v1_negvrp", "v1 live index vetoes (any)": "v_v1",
        "WS4 max-denominator veto": "v_max_den",
    }
    per_gate = {name: gate_metrics(rows, flag, labels) for name, flag in gate_flags.items()}
    lb = bootstrap_lb(rows, "v_v2", labels, n_boot=a.n_boot)
    acc = evaluate_acceptance(per_gate["v2 any-veto (core+G5+G6)"], lb, per_gate["v1 live index vetoes (any)"], per_gate)
    # sensitivity: G5 z/window and G6 window
    sens = {}
    for z in (1.5, 2.0, 2.5):
        for w in (126, 252):
            flag = f"v_g5_{z}_{w}"
            hist: list[float] = []
            # recompute frozen with (z, w) from stored gz series is not possible (gz depends on window) —
            # approximate by rescaling: rows carry gz for W=252; for w=126 use the same series (documented).
            for r in rows:
                fr = (r["index_fvrp"] is not None and r["index_fvrp"] < 1.0) or (r["gz"] is not None and r["gz"] > z)
                r[flag] = (not r["eligible"]) or r["g6_fomc"] or fr
            sens[f"G5 z={z}, window={w}{' (gz series at 252)' if w != 252 else ''}"] = gate_metrics(rows, flag, labels)
    for kd in (1, 2, 3):
        flag = f"v_g6_{kd}"
        for r in rows:
            g, _, _ = mc.in_window(date.fromisoformat(r["date"]), kd, 0, kinds=("FOMC",))
            r[flag] = (not r["eligible"]) or g
        sens[f"G6 FOMC window −{kd}d..0d"] = gate_metrics(rows, flag, labels)
    for r in rows:
        r["v_v2_g6all"] = (not r["eligible"]) or r["g6_all"]
    sens["G6 FOMC+CPI+NFP (2024+ coverage)"] = gate_metrics(rows, "v_v2_g6all", labels)
    rows_by_t = defaultdict(list)
    for r in rows:
        rows_by_t[r["ticker"]].append(r)
    trades = simulate_puts(rows_by_t, bars)
    out_dir = Path(a.out)
    rep = write_report(res, labels, per_gate, lb, acc, sens, trades, prov, out_dir, run_date)
    seed = kelly_seed_candidate(trades, out_dir, run_date)
    summary = {"run_date": run_date, "sessions": len(res["master"]), "ticker_days": len(rows),
               "acceptance": acc, "v2": {k: v for k, v in per_gate["v2 any-veto (core+G5+G6)"].items() if k != "per_event"},
               "v1": {k: v for k, v in per_gate["v1 live index vetoes (any)"].items() if k != "per_event"},
               "lb90": lb, "k": res["k"], "provenance": prov, "report": str(rep), "seed": str(seed) if seed else None}
    (out_dir / f"X1-results-{run_date}.json").write_text(json.dumps(summary, indent=1, default=str))
    print(json.dumps({k: summary[k] for k in ("acceptance", "lb90", "report", "seed")}, indent=1, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
