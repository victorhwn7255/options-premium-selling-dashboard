"""
theta_harvest_core.py — reference implementation of theta-harvest-v2-spec.md

Modules mirror the spec: A (estimators / forward VRP), B (gates), C (sizing),
E (measurement). Pure functions + small state classes; no I/O, no framework
dependencies. Intended to be ported into backend/ by Claude Code with the
project's own data access layer.

Dependencies: numpy, pandas, scipy.
All vols are ANNUALIZED DECIMALS unless a name says vol_points.
All [PROVISIONAL] constants are surfaced in CONFIG — never hardcoded below.

Corrections (2026-07-04, pre-port review — see docs/theta-harvest-v2-evaluation-2026-07.md):
  * friction_prescreen: round-trip cost now computed in consistent PER-CONTRACT dollars.
    The prior version mixed a per-share spread with a per-contract commission and then ×100'd
    the sum — a ~40× over-charge that REJECTED textbook-liquid index puts (SPY/QQQ/IWM, the
    designated return engine). This is the golden master for Phase A; the bug must not be
    reproduced by the "1e-9 fixture" gate.
  * PooledForecaster.resid_var (0.25) and kelly_base's cold-start floor (0.10) / min-trades (20)
    moved into CONFIG — they were hardcoded, contradicting the "never hardcoded" rule above and
    (for resid_var) silently deflating cold-start FVRP ~13% via the exp(0.5·resid_var) correction.
  * 2026-07-05 (Phase 0.6 CONFIG audit): lifted 5 remaining inline constants into CONFIG with
    IDENTICAL values (behavior-preserving) so line-11's "never hardcoded below" holds fully —
    fvrp_min_obs (60), reentry_ramp_exponent (2), margin_otm_min_frac (0.10), dial_O_z_clip (2.0),
    psr_min_obs (30). Golden-master outputs unchanged; fixtures derived before/after are identical.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from scipy.stats import norm

ANN = 252
HOLD_SESSIONS = 21  # forecast/trade horizon (45 DTE entry -> 21 DTE exit ~ 21 sessions)

CONFIG = {
    # Module A
    "ridge_lambda": 1e-3,                 # [PROVISIONAL]
    "seed_betas": [0.10, 0.25, 0.35, 0.20, 0.15, 0.10],  # [PROVISIONAL]
    "min_pooled_obs": 250,
    "dead_zone_index": 1.20,              # [PROVISIONAL]
    "dead_zone_single": 1.15,             # [PROVISIONAL]
    "abs_premium_floor_volpts": 2.0,      # [PROVISIONAL]
    "fvrp_min_obs": 60,                   # [PROVISIONAL] min trailing obs before FVRP z-score is computed
    "resid_var_prior": 0.25,              # [PROVISIONAL] log-target residual-variance prior. ONLY
                                          # active before the first pooled fit() (which overrides it
                                          # from actual residuals once n >= min_pooled_obs). With the
                                          # build-plan backfill warm-start this is moot in production,
                                          # but it stays governable rather than hardcoded.
    # Module B
    "g2_caution_in": 1.00, "g2_caution_out": 0.98,   # [PROVISIONAL]
    "g2_danger_in": 1.05, "g2_danger_out": 1.02,     # [PROVISIONAL]
    "g3_in": 1.10, "g3_out": 1.05,
    "g3_concentration": 0.50,
    "g5_global_z": 2.0,                   # [PROVISIONAL]
    "confirm_days": 2,
    "transient_blackout_days": 3,
    "reentry_ramp_exponent": 2,           # [PROVISIONAL] curvature of the post-DANGER re-entry ramp
    # Module C
    "margin_alpha": 0.20,                 # 0.15 for IBKR
    "margin_otm_min_frac": 0.10,          # [PROVISIONAL] Reg-T alt. minimum as a fraction of strike
    "kelly_fraction": 0.25,               # quarter-Kelly [PROVISIONAL]
    "kelly_min_trades": 20,               # below this many closed trades, use the cold-start floor
    "kelly_cold_start_floor": 0.10,       # [PROVISIONAL] raw f* floor until the trade log matures
    "disaster_prob": 0.02,                # [PROVISIONAL]
    "disaster_mult": 3.0,
    "dial_R_bounds": (0.25, 1.25),
    "dial_O_kappa": 0.25,                 # [PROVISIONAL]
    "dial_O_bounds": (0.50, 1.50),
    "dial_O_z_clip": 2.0,                 # [PROVISIONAL] symmetric clip on FVRP z before the O-dial tilt
    "cap_notional_frac": 1.00,
    "cap_margin_frac": 0.30,
    "cap_name_margin_frac": 0.08,         # [PROVISIONAL]
    "cap_name_stress_frac": 0.025,        # [PROVISIONAL]
    "cap_book_stress_frac": 0.15,         # [PROVISIONAL]
    "stress_spot_mult": 0.80,
    "stress_iv_mult": 2.0,
    "stress_days_elapsed": 5,
    # Exits (strategy §5)
    "danger_underwater_mult": 1.25,       # [PROVISIONAL] mark >= this × credit => "underwater" (§5.4)
    # Module D
    "max_spread_over_mid": 0.10,
    "max_rtc_over_capture": 0.25,
    "capture_fraction": 0.65,             # [PROVISIONAL]
    # Module E
    "psr_benchmark_annual": 0.5,
    "psr_min_obs": 30,                    # [PROVISIONAL] min daily obs before PSR is defined
}


# ----------------------------------------------------------------------------
# Module A — Estimators
# ----------------------------------------------------------------------------

def daily_inputs(o: float, h: float, l: float, c: float, prev_c: float) -> dict:
    """A1: per-session return decomposition and variance proxies (decimal^2/day)."""
    r = math.log(c / prev_c)
    on = math.log(o / prev_c)
    u, d, cc = math.log(h / o), math.log(l / o), math.log(c / o)
    gk = 0.5 * (u - d) ** 2 - (2 * math.log(2) - 1) * cc ** 2
    return {
        "r": r,
        "v": on ** 2 + max(gk, 0.0),
        "s_neg": r * r if r < 0 else 0.0,
        "s_pos": r * r if r >= 0 else 0.0,
    }


def yang_zhang(o, h, l, c, n: int = 21) -> float:
    """A1: Yang-Zhang level estimator over trailing n bars. Returns annualized vol."""
    o, h, l, c = (np.asarray(x, dtype=float)[-(n + 1):] for x in (o, h, l, c))
    on = np.log(o[1:] / c[:-1])
    cc = np.log(c[1:] / o[1:])
    u = np.log(h[1:] / o[1:])
    d = np.log(l[1:] / o[1:])
    rs = u * (u - cc) + d * (d - cc)
    k = 0.34 / (1.34 + (n + 1) / (n - 1))
    var = on.var(ddof=1) + k * cc.var(ddof=1) + (1 - k) * rs.mean()
    return math.sqrt(max(var, 0.0) * ANN)


class EwmaState:
    """A2: smooth memory. Center-of-mass m -> lambda = m/(1+m)."""

    COMS_V = (1, 5, 25, 125)
    COMS_SNEG = (5, 25)

    def __init__(self):
        self.v = {m: None for m in self.COMS_V}
        self.sneg = {m: None for m in self.COMS_SNEG}
        self._vbar_sum, self._vbar_n = 0.0, 0

    @staticmethod
    def _step(prev, x, m):
        lam = m / (1.0 + m)
        return x if prev is None else (1 - lam) * x + lam * prev

    def update(self, v: float, s_neg: float) -> None:
        for m in self.COMS_V:
            self.v[m] = self._step(self.v[m], v, m)
        for m in self.COMS_SNEG:
            self.sneg[m] = self._step(self.sneg[m], s_neg, m)
        self._vbar_sum += v
        self._vbar_n += 1

    @property
    def vbar(self) -> float:
        """Expanding long-run mean of the daily variance proxy."""
        return self._vbar_sum / max(self._vbar_n, 1)


def forecast_features(st: EwmaState, global_factor: float) -> np.ndarray:
    """A3 feature vector x1..x6 (demeaned log EWMAs, downside share, global factor)."""
    eps = 1e-12
    lvb = math.log(max(st.vbar, eps))
    x = [math.log(max(st.v[m], eps)) - lvb for m in EwmaState.COMS_V]
    x.append(math.log(max(st.sneg[5], eps) / max(st.v[5], eps)))
    x.append(math.log(max(global_factor, eps)))
    return np.array(x)


class PooledForecaster:
    """A3: one ridge regression across all tickers; target ln(RVfwd) - ln(vbar)."""

    def __init__(self, ridge_lambda: float = CONFIG["ridge_lambda"]):
        self.lmb = ridge_lambda
        self.beta = np.array(CONFIG["seed_betas"], dtype=float)
        self.intercept = 0.0
        self.resid_var = CONFIG["resid_var_prior"]  # prior; fit() overrides from data once n>=min_pooled_obs
        self.n_obs = 0

    def fit(self, X: np.ndarray, y_centered: np.ndarray) -> None:
        """X: (n,6) features; y_centered: ln(RVfwd) - ln(vbar) per row. Expanding refit monthly."""
        n, k = X.shape
        if n < CONFIG["min_pooled_obs"]:
            return  # keep seed betas until the panel supports estimation
        Xa = np.column_stack([np.ones(n), X])
        A = Xa.T @ Xa + self.lmb * n * np.eye(k + 1)
        coef = np.linalg.solve(A, Xa.T @ y_centered)
        self.intercept, self.beta = coef[0], coef[1:]
        resid = y_centered - Xa @ coef
        self.resid_var = float(resid.var(ddof=k + 1))
        self.n_obs = n

    def predict_sigma_fwd(self, st: EwmaState, global_factor: float,
                          daily_target: bool = False) -> float:
        """Annualized forward vol over the holding horizon (log-normal corrected)."""
        x = forecast_features(st, global_factor)
        log_ratio = self.intercept + x @ self.beta + 0.5 * self.resid_var
        ann_var = st.vbar * ANN * math.exp(log_ratio)
        return math.sqrt(max(ann_var, 1e-10))


def fvrp(iv30: float, sigma_fwd: float, log_hist: list[float] | None = None) -> dict:
    """A4: forward VRP ratio and z-score (log space, trailing history supplied by caller)."""
    ratio = iv30 / max(sigma_fwd, 1e-6)
    z = 0.0
    if log_hist and len(log_hist) >= CONFIG["fvrp_min_obs"]:
        h = np.log(np.asarray(log_hist))
        sd = h.std(ddof=1)
        z = (math.log(ratio) - h.mean()) / sd if sd > 1e-9 else 0.0
    return {"ratio": ratio, "z": z,
            "abs_premium_volpts": (iv30 - sigma_fwd) * 100.0}


# ----------------------------------------------------------------------------
# Module B — Gate state machine
# ----------------------------------------------------------------------------

@dataclass
class GateState:
    state: str = "NORMAL"            # NORMAL | CAUTION | DANGER
    transient: bool = False
    _pending: str | None = None
    _pending_days: int = 0
    _blackout: int = 0

    def _confirm(self, proposed: str) -> None:
        if proposed == self.state:
            self._pending, self._pending_days = None, 0
            return
        if proposed == self._pending:
            self._pending_days += 1
        else:
            self._pending, self._pending_days = proposed, 1
        if self._pending_days >= CONFIG["confirm_days"]:
            self.state = proposed
            self._pending, self._pending_days = None, 0

    def update(self, slope_1m3m: float, accel_dn: float,
               concentration_10d: float) -> None:
        c = CONFIG
        # G2 term structure with hysteresis
        if slope_1m3m >= c["g2_danger_in"]:
            g2 = "DANGER"
        elif self.state == "DANGER" and slope_1m3m > c["g2_danger_out"]:
            g2 = "DANGER"
        elif slope_1m3m >= c["g2_caution_in"]:
            g2 = "CAUTION"
        elif self.state in ("CAUTION", "DANGER") and slope_1m3m > c["g2_caution_out"]:
            g2 = "CAUTION"
        else:
            g2 = "NORMAL"
        # G3 downside acceleration with hysteresis
        if accel_dn >= c["g3_in"]:
            g3 = "CAUTION"
        elif self.state != "NORMAL" and accel_dn > c["g3_out"]:
            g3 = "CAUTION"
        else:
            g3 = "NORMAL"
        # Transient tag: single-day-dominated downside spike in normal term structure
        self.transient = (g3 == "CAUTION" and g2 == "NORMAL"
                          and concentration_10d > c["g3_concentration"])
        if self.transient and self._blackout == 0:
            self._blackout = c["transient_blackout_days"]
        elif self._blackout > 0:
            self._blackout -= 1
        order = {"NORMAL": 0, "CAUTION": 1, "DANGER": 2}
        proposed = max((g2, g3), key=lambda s: order[s])
        self._confirm(proposed)

    def entry_eligible(self, fvrp_ratio: float, dead_zone: float,
                       abs_premium_volpts: float) -> bool:
        if fvrp_ratio < 1.0 or fvrp_ratio < dead_zone:
            return False
        if abs_premium_volpts < CONFIG["abs_premium_floor_volpts"]:
            return False
        if self.state == "DANGER":
            return False
        if self.transient or self._blackout > 0:
            return False
        return self.state == "NORMAL"


def reentry_ramp(sigma_dn_prespike: float, sigma_dn_now: float) -> float:
    """Post-DANGER eligibility fraction: sized up as the downside forecast decays."""
    return min(1.0, (sigma_dn_prespike / max(sigma_dn_now, 1e-9)) ** CONFIG["reentry_ramp_exponent"])


# ----------------------------------------------------------------------------
# Module C — Sizing
# ----------------------------------------------------------------------------

def margin_short_put(premium: float, spot: float, strike: float,
                     alpha: float = CONFIG["margin_alpha"]) -> float:
    """C1: Reg-T style initial margin per contract (dollars)."""
    otm = max(spot - strike, 0.0)
    return 100.0 * max(premium + alpha * spot - otm, premium + CONFIG["margin_otm_min_frac"] * strike)


def kelly_base(pnl_per_margin: np.ndarray, months: np.ndarray,
               rng: np.random.Generator | None = None,
               n_boot: int = 2000) -> float:
    """C2: block-bootstrap Kelly with disaster injection. Returns raw f* (apply phi outside).

    pnl_per_margin: realized PnL_j / M_j per closed trade.
    months: month label per trade (block bootstrap unit).
    """
    rng = rng or np.random.default_rng(7)
    x = np.asarray(pnl_per_margin, dtype=float)
    if len(x) < CONFIG["kelly_min_trades"]:
        return CONFIG["kelly_cold_start_floor"]  # conservative floor until the log matures
    worst = x.min()
    disaster = CONFIG["disaster_mult"] * worst  # a negative number
    blocks = pd.Series(x).groupby(pd.Series(months)).apply(lambda s: s.values)
    keys = list(blocks.index)

    def neg_growth(f: float) -> float:
        total, count = 0.0, 0
        for _ in range(n_boot):
            draw = np.concatenate([blocks[k] for k in rng.choice(keys, size=len(keys))])
            inject = rng.random(len(draw)) < CONFIG["disaster_prob"]
            d = np.where(inject, disaster, draw)
            arg = 1.0 + f * d
            if (arg <= 0).any():
                return 1e9  # ruin at this f
            total += np.log(arg).sum()
            count += len(d)
        return -total / count

    grid = np.concatenate([[0.0], np.linspace(0.01, 2.0, 80)])
    vals = [neg_growth(f) for f in grid]
    f_opt = float(grid[int(np.argmin(vals))])
    # f*=0 is a signal, not a parameter: the log (with disaster injection) shows no
    # positive-growth size. Surface it upstream instead of trading a floor.
    return f_opt


def dial_R(sigma_dn_median_252: float, sigma_dn_now: float) -> float:
    lo, hi = CONFIG["dial_R_bounds"]
    return float(np.clip(sigma_dn_median_252 / max(sigma_dn_now, 1e-9), lo, hi))


def dial_O(fvrp_z: float) -> float:
    lo, hi = CONFIG["dial_O_bounds"]
    z = float(np.clip(fvrp_z, -CONFIG["dial_O_z_clip"], CONFIG["dial_O_z_clip"]))
    return float(np.clip(1.0 + CONFIG["dial_O_kappa"] * z, lo, hi))


def contracts(equity: float, f_star: float, R: float, O: float,
              margin_per_contract: float) -> int:
    n = equity * CONFIG["kelly_fraction"] * f_star * R * O / max(margin_per_contract, 1e-9)
    return max(int(n), 0)


# --- C6 stress gate -----------------------------------------------------------

def _bsm_put(S, K, sigma, t_years, r=0.0):
    if t_years <= 0 or sigma <= 0:
        return max(K - S, 0.0)
    sq = sigma * math.sqrt(t_years)
    d1 = (math.log(S / K) + (r + 0.5 * sigma * sigma) * t_years) / sq
    d2 = d1 - sq
    return K * math.exp(-r * t_years) * norm.cdf(-d2) - S * norm.cdf(-d1)


@dataclass
class Position:
    ticker: str
    spot: float
    strike: float
    iv: float                 # current IV of the contract, decimal
    dte_sessions: int
    contracts: int
    entry_premium: float      # per share


def stressed_pnl(book: list[Position],
                 spot_mult=CONFIG["stress_spot_mult"],
                 iv_mult=CONFIG["stress_iv_mult"],
                 days=CONFIG["stress_days_elapsed"]) -> float:
    """C6: full-book BSM reprice under {spot shock, IV shock, time elapsed}. Negative = loss."""
    total = 0.0
    for p in book:
        t_now = p.dte_sessions / ANN
        t_str = max(p.dte_sessions - days, 1) / ANN
        px_now = _bsm_put(p.spot, p.strike, p.iv, t_now)
        px_str = _bsm_put(p.spot * spot_mult, p.strike, p.iv * iv_mult, t_str)
        total += (px_now - px_str) * 100 * p.contracts  # short: loss when price rises
    return total


def entry_allowed(book: list[Position], candidate: Position, equity: float,
                  margins: dict[str, float]) -> tuple[bool, str]:
    """C6 caps with precedence over dials. margins: ticker -> current initial margin $."""
    c = CONFIG
    trial = book + [candidate]
    notional = sum(p.strike * 100 * p.contracts for p in trial)
    if notional > c["cap_notional_frac"] * equity:
        return False, "notional_cap"
    total_margin = sum(margins.values())
    if total_margin > c["cap_margin_frac"] * equity:
        return False, "margin_cap"
    if margins.get(candidate.ticker, 0.0) > c["cap_name_margin_frac"] * equity:
        return False, "name_margin_cap"
    name_stress = -stressed_pnl([p for p in trial if p.ticker == candidate.ticker])
    if name_stress > c["cap_name_stress_frac"] * equity:
        return False, "name_stress_cap"
    book_stress = -stressed_pnl(trial)
    if book_stress > c["cap_book_stress_frac"] * equity:
        return False, "book_stress_cap"
    return True, "ok"


# ----------------------------------------------------------------------------
# Module D — Frictions
# ----------------------------------------------------------------------------

def friction_prescreen(bid: float, ask: float, commissions_rt: float) -> tuple[bool, str]:
    mid = 0.5 * (bid + ask)
    if mid <= 0:
        return False, "no_market"
    spread = ask - bid
    if spread / mid > CONFIG["max_spread_over_mid"]:
        return False, "spread_over_mid"
    # Round-trip cost and capture BOTH in per-contract dollars. `spread` and `mid` are
    # per-share (×100 → per contract); `commissions_rt` is already per-contract. The prior
    # version added a per-share spread to a per-contract commission and then ×100'd the sum,
    # over-charging commissions 100× and rejecting even penny-wide liquid index puts.
    rtc = spread * 100.0 + commissions_rt   # one full spread (two half-spread crossings) + commissions
    capture = mid * 100.0 * CONFIG["capture_fraction"]
    if capture <= 0 or rtc / capture > CONFIG["max_rtc_over_capture"]:
        return False, "rtc_over_capture"
    return True, "ok"


# ----------------------------------------------------------------------------
# Module E — Measurement
# ----------------------------------------------------------------------------

def psr(returns_daily: np.ndarray, sr_benchmark_daily: float = 0.0,
        worst_case: bool = True, n_boot: int = 2000,
        rng: np.random.Generator | None = None) -> dict:
    """E1: Probabilistic Sharpe Ratio on daily P&L, native frequency."""
    r = np.asarray(returns_daily, dtype=float)
    n = len(r)
    if n < CONFIG["psr_min_obs"]:
        return {"psr": float("nan"), "sr_daily": float("nan"), "n": n}
    sr = r.mean() / r.std(ddof=1)
    g3 = pd.Series(r).skew()
    g4 = pd.Series(r).kurt() + 3.0
    if worst_case:
        rng = rng or np.random.default_rng(11)
        sk, ku = [], []
        for _ in range(n_boot):
            b = rng.choice(r, size=n, replace=True)
            s = pd.Series(b)
            sk.append(s.skew())
            ku.append(s.kurt() + 3.0)
        g3, g4 = float(np.percentile(sk, 5)), float(np.percentile(ku, 95))
    denom = math.sqrt(max(1 - g3 * sr + (g4 - 1) / 4 * sr * sr, 1e-9))
    stat = (sr - sr_benchmark_daily) * math.sqrt(n - 1) / denom
    z95 = norm.ppf(0.95)
    mintrl = 1 + (1 - g3 * sr + (g4 - 1) / 4 * sr * sr) * (z95 / max(sr - sr_benchmark_daily, 1e-9)) ** 2
    return {"psr": float(norm.cdf(stat)), "sr_daily": float(sr),
            "sr_annual": float(sr * math.sqrt(ANN)),
            "skew": float(g3), "kurt": float(g4),
            "mintrl_days": float(mintrl), "n": n}


def realized_capture(iv_entry: float, rv_realized_hold: float) -> dict:
    """E3: per-trade VRP capture in variance points and log form."""
    return {"var_points": (iv_entry ** 2 - rv_realized_hold ** 2) * 1e4,
            "log": math.log(max(iv_entry, 1e-6) ** 2 / max(rv_realized_hold, 1e-6) ** 2)}


def health_monitor(capture_series_90d: np.ndarray) -> dict:
    """E4: lagging damage-control indicator (NOT tail protection)."""
    m = float(np.mean(capture_series_90d)) if len(capture_series_90d) else float("nan")
    return {"mean_90d": m, "degross": bool(m < 0), "gross_mult": 0.5 if m < 0 else 1.0}
