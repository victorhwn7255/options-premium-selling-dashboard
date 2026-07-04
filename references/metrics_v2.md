---
last_verified: 2026-07-04
verified_against: theta-harvest-v2-spec.md + theta_harvest_core.py (reference implementation)
status: v2 — ADOPTED 2026-07-04. Supersedes metrics.md v1 in full.
precedence: If any number here disagrees with theta-harvest-v2-spec.md, the SPEC wins.
audience: Claude Code agents + human review
companions: strategy.md (trading rules) · theta-harvest-v2-spec.md (exact formulas) ·
            theta_harvest_core.py (reference math, function names cited below)
---

# Theta Harvest — Metrics Reference (v2)

## 0. Conventions (apply everywhere)

- Volatilities are **annualized decimals** internally (×100 → vol points for display).
  Annualization factor 252. Trade/forecast horizon h = 21 sessions.
- **All percentiles and z-scores on vol quantities are computed in log space.**
  Log RV is ≈ Gaussian; raw RV has kurtosis ~96. No exceptions.
- **No step windows.** All memory is EWMA (center-of-mass parameterization,
  λ = m/(1+m)). Step windows (rolling 10d/30d sums) create mean-reverting signal
  churn that flips gates on noise — this was the JNJ oscillation mechanism.
- Every metric below cites its reference implementation in `theta_harvest_core.py`.
- [PROVISIONAL] marks constants owned by the calibration process (governance:
  strategy.md §9), not by this document.

## 1. Data inputs

- **Bars:** daily OHLC per ticker (MarketData.app). Both O and H/L are load-bearing
  (overnight decomposition + range estimators) — bar integrity checks required;
  split-adjusted series only (unadjusted history mixing with post-split data has
  produced ~658% RV artifacts before).
- **IV30:** 30-day constant-maturity ATM Black-Scholes IV, interpolated across the
  two nearest expirations within ±10 days tolerance, capped at 200%. (INHERITED
  from v1 — retained as a consistent internal signal; it is not model-free implied
  variance and internal thresholds are therefore not comparable to
  variance-swap-literature magnitudes. Known, accepted limitation.)
- **Tenor IVs:** 1M and 3M ATM IV for the term-structure slope. The v1 1W/1Y
  construction is retired (1W event-contaminated, 1Y thin on single names).
- **Earnings dates:** FMP primary, Yahoo cross-check, hard verification against IR
  page / TipRanks on any disagreement. Unverified dates gate the name (strategy §3.4).

## 2. Realized-volatility metrics

| Metric | Definition | Ref impl |
|---|---|---|
| `v_t` daily variance proxy | overnight² + Garman-Klass body: `o² + max(0.5(u−d)² − (2ln2−1)c², 0)` | `daily_inputs()` |
| `s_neg_t`, `s_pos_t` | signed daily semivariance from close-to-close return: `r²·1[r<0]`, `r²·1[r≥0]` | `daily_inputs()` |
| `YZ21` | Yang-Zhang level estimator, n=21, annualized — **display/percentile use only** | `yang_zhang()` |
| `E_m(v)` | EWMA of `v_t`, centers of mass m ∈ {1, 5, 25, 125} | `EwmaState` |
| `E_m(s⁻)` | EWMA of `s_neg_t`, m ∈ {5, 25} | `EwmaState` |
| `vbar` | expanding mean of `v_t` (min 120 obs; pooled universe mean before that) — each name's long-run anchor | `EwmaState.vbar` |
| `A_t` downside acceleration | `sqrt(E_5(s⁻)/E_25(s⁻))` — feeds gate G3 | `GateState.update()` |
| `concentration_10d` | max single-day `s_neg` ÷ 10-session sum — jump-vs-diffusive discriminator, feeds the transient tag | `GateState.update()` |

Close-to-close RV30/RV10 are **retired** from all decision paths. They may remain as
display columns during transition, clearly labeled `legacy_`.

## 3. Forward RV forecast (the VRP denominator)

One **pooled** ridge regression across all 33 tickers (each demeaned by its own
`vbar`), log space, expanding window, refit monthly. Features: four demeaned log
variance-EWMAs, the downside share `ln(E_5(s⁻)/E_5(v))`, and the lagged **global
volatility factor** `G_t` = cross-ticker mean of `E_5(v)/vbar`. Target: annualized
forward realized variance over the next 21 sessions, log-normal-corrected on
inversion. Seed betas apply until ≥ 250 pooled target observations exist.

Outputs per ticker-day:

- `sigma_fwd` — forecast total vol over the holding horizon (annualized).
- `sigma_fwd_dn` — same regression on forward *downside* semivariance. Drives gates
  and the risk dial; a put seller's risk object is downside variance specifically.

Ref impl: `PooledForecaster`, `forecast_features()`. Pooling is deliberate: per-name
fits on ~1 year of history overfit; the cross-section's job is estimating one robust
model, not 33 fragile ones.

## 4. Signal metrics

| Metric | Definition | Use |
|---|---|---|
| `FVRP_ratio` | `IV30 / sigma_fwd` | Tradeability core. Dead zones: 1.20 index / 1.15 single [PROVISIONAL, owned by Test T1] |
| `FVRP_z` | z-score of `ln(FVRP_ratio)`, trailing 252d per ticker (min 60 obs, else pooled) | Opportunity dial input |
| `abs_premium` | `(IV30 − sigma_fwd) × 100` vol points | Floor at 2.0 pts [PROVISIONAL] — ratio richness must also be fundable in dollars |
| `slope_1m3m` | `IV_1M / IV_3M` | Gate G2. CAUTION ≥ 1.00 / exit ≤ 0.98; DANGER ≥ 1.05 / exit ≤ 1.02 [PROVISIONAL] |
| `gate_state` | NORMAL / CAUTION / DANGER + `transient_tag` | 2-day confirmation on all transitions; hysteresis everywhere |
| `global_factor` | `G_t` as §3, plus its 20-session change z-score | Gate G5 (book-wide freeze at z > 2 [PROVISIONAL]) |
| `composite_score` | v1 0–100 formula, unchanged | **Telemetry only.** Never allocates, never ranks for entry priority |

Ref impl: `fvrp()`, `GateState`, `reentry_ramp()`.

## 5. Sizing metrics (logged on every entry)

| Metric | Definition | Ref impl |
|---|---|---|
| `margin_per_contract` | `100·max(P + α·S − max(S−K,0), P + 0.10·K)`, α = 0.20 (0.15 IBKR) | `margin_short_put()` |
| `f_star` | block-bootstrap Kelly on per-margin-dollar trade outcomes, disaster-injected (2% × 3×worst [PROVISIONAL]); quarter-Kelly φ = 0.25 applied downstream | `kelly_base()` |
| `dial_R` | `clip(median_252(sigma_fwd_dn)/sigma_fwd_dn, 0.25, 1.25)` — risk dial | `dial_R()` |
| `dial_O` | `clip(1 + 0.25·clip(FVRP_z, −2, 2), 0.5, 1.5)` — opportunity dial | `dial_O()` |
| `contracts` | `floor(E·φ·f*·R·O / M)` then caps | `contracts()` |
| `stress_pnl_20_2x` | full-book BSM reprice at {spot×0.80, IV×2, +5 sessions}; also report {×0.90, IV×1.5} | `stressed_pnl()` |
| cap checks | notional ≤ 100% eq · margin ≤ 30% · name margin ≤ 8% · name stress ≤ 2.5% · book stress ≤ 15% [PROVISIONAL] | `entry_allowed()` |

Precedence is structural: **caps > dials > Kelly base**. Dials computed at entry
only; open positions never resized daily.

## 6. Friction metrics

- **Pre-screen (scan time):** reject if `quoted_spread/mid > 0.10`; skip if
  `(spread + commissions) / (0.65 × credit) > 0.25`. Ref: `friction_prescreen()`.
- **Fill telemetry (every fill):** `fill_vs_mid = (fill − mid)/half_spread`.
  Alarm when rolling 20-fill mean > 0.50 — documented strategies survive at ~50% of
  half-spread and die near quoted.
- **Spread-aware exit trigger values** logged on every use of the 21-DTE decay
  exception (strategy §5.3).

## 7. Measurement & validation metrics (portfolio_daily)

| Metric | Definition | Notes |
|---|---|---|
| `PSR(0)`, `PSR(0.5)` | Probabilistic Sharpe Ratio on **daily** P&L, native frequency, worst-case moments (bootstrap 5th-pct skew / 95th-pct kurtosis) while sample is short | Acceptance bar 0.95. Raw Sharpe is never quoted without PSR beside it |
| `MinTRL` | minimum track record length at 95% for the claimed benchmark | On ~336 daily obs, rejecting "no skill" needs ann. Sharpe ≈ 1.4–1.55 — calibrates humility about the 16-month window |
| DSR hurdle | deflated-Sharpe threshold from trial-registry count N | Registry is append-only; every test raises the bar, adopted or not |
| `capture` | per closed trade and per ticker-day: `IV30²(entry) − RV_realized(hold)` (variance points + log form) | Ground truth of the edge; feeds E4 and the future option-momentum feature |
| `monitor_e4` | rolling 90-day mean of `capture` portfolio-wide; < 0 → gross ×0.5 + naked→spread migration | **Lagging damage-control indicator, not tail protection** — framing is part of the metric |
| benchmarks | rolling 12-month NAV vs Cboe PUT and SPY TR | Pre-committed interpretation: bull-market lag vs SPY is regime-expected |
| four-moment monitor | 60-day mean/SD/skew/kurt of daily P&L; alert on skew z < −2 vs trailing year | |

Ref impl: `psr()`, `realized_capture()`, `health_monitor()`.

## 8. Known limitations (accepted, documented)

1. **Semivariance is close-to-close.** Sign is not recoverable from ranges; daily
   signed semivariance is coarser than the intraday estimators in the source
   literature. Effect sizes may be smaller than published; thresholds are
   [PROVISIONAL] partly for this reason.
2. **IV30 is ATM BSM, not model-free implied variance.** Consistent internally;
   not comparable to variance-swap magnitudes in the literature.
3. **The forecast denominator is unvalidated on internal data until Test T1 runs.**
   Until then, `FVRP_ratio` and legacy `IV30/RV30` are both logged for divergence
   analysis; only FVRP gates.
4. **`monitor_e4` lags by construction** — it confirms a losing regime after losses
   are booked. It must never be described or used as a leading tail defense.
5. **Self-built IV history bootstrap:** `FVRP_z` and any IV percentile degrade
   silently below ~60 observations per ticker; the pooled fallback is a shrinkage
   patch, not a fix. Percentile-dependent displays carry an insufficiency flag.
6. **The stress scenario {−20%, IV×2} is a convention, not a worst case.** The
   historical sample used to size everything contains no true disaster; the disaster
   injection in `kelly_base()` exists precisely because of this.

## 9. Migration notes for implementation agents

- Schema additions: spec Module G (`daily_iv`, `trades`, `portfolio_daily`,
  `trial_registry.jsonl`).
- Backfill order: bars-integrity check → `v/s_neg/s_pos` → EWMAs + `vbar` →
  forward-RV targets (needs 21-session lookahead; last 21 sessions have no target)
  → pooled fit → `sigma_fwd`/`sigma_fwd_dn`/`FVRP` history → gate-state replay.
- Run v2 gates and sizing in **shadow mode alongside v1 for ≥ 10 sessions**, diff
  the decisions daily, before any cutover.
- Nothing in this file authorizes a backtest: all backtests go through the trial
  registry, and only T1–T3 may change live behavior (strategy.md §9).
