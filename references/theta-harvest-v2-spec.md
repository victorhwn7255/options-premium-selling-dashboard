---
last_verified: 2026-07-04
verified_against: 18-paper synthesis (premium-selling-research-synthesis-2026-07.md) + Claude review 2026-07-04
status: DESIGN SPEC — constants marked [PROVISIONAL] require calibration on internal data before production
companion: theta_harvest_core.py (reference implementation of all Module A/C/E math)
---

# Theta Harvest v2 — Strategy & Metrics Engineering Specification

Scope: exact definitions for Tier 1 (sizing, caps, frictions, measurement) and Tier 2
(forward-VRP redefinition, sign-aware gates), plus the three pre-registered Tier 3 tests.
Design principles inherited from the research synthesis, with two corrections applied:
the sizing dial is split into independent risk and opportunity dials (not raw IV-rank),
and a single precedence rule governs the sizing stack (caps > dials > Kelly base).

Every constant is either DERIVED (from a formula), INHERITED (from current system,
unchanged), or [PROVISIONAL] (literature-motivated starting value; owned by the
calibration process, not by this document).

---

## Module A — Estimators and the Forward VRP

### A1. Daily inputs (per ticker, per session)

From OHLC bars (all logs natural):

```
r_t   = ln(C_t / C_{t-1})                     # close-to-close return
o_t   = ln(O_t / C_{t-1})                     # overnight return
u_t   = ln(H_t / O_t);  d_t = ln(L_t / O_t);  c_t = ln(C_t / O_t)
```

**Daily variance proxy** (Garman-Klass with overnight jump — the efficient level input):

```
GK_t  = 0.5 * (u_t - d_t)^2 - (2*ln2 - 1) * c_t^2
v_t   = o_t^2 + max(GK_t, 0)                  # daily variance, decimal^2
```

**Daily signed semivariance proxies** (close-to-close; sign is not range-recoverable):

```
s_neg_t = r_t^2 * 1[r_t < 0]
s_pos_t = r_t^2 * 1[r_t >= 0]
```

**Level estimator for display/percentiles**: Yang-Zhang over n=21 sessions
(k = 0.34 / (1.34 + (n+1)/(n-1))), annualized ×252, reported in vol points.
Replaces close-to-close RV30 everywhere RV is *displayed*; the forecast (A3) replaces
it everywhere RV is *used*.

All percentile and z-score computations on any vol quantity are done in **log space**
(log RV ≈ Gaussian; raw RV kurtosis ~96).

### A2. EWMA mixture (smooth memory — no step windows anywhere)

EWMA with center of mass m: `lambda_m = m / (1 + m)`;
`E_m(t) = (1 - lambda_m) * x_t + lambda_m * E_m(t-1)`.

Maintain per ticker:

```
E_1(v), E_5(v), E_25(v), E_125(v)        # variance-proxy EWMAs
E_5(s_neg), E_25(s_neg)                  # downside semivariance EWMAs
Vbar_i = expanding mean of v_t           # long-run anchor (min 120 obs; else pooled universe mean)
```

Global volatility factor (portfolio regime input, lagged one day):

```
G_t = mean_i( E_5(v)_{i,t-1} / Vbar_i )
```

### A3. Forward RV forecast (pooled panel, log space)

**Target** (annualized forward variance over the trade horizon h = 21 sessions):

```
RVfwd_t = (252 / h) * sum_{j=1..h} v_{t+j}
y_t     = ln(RVfwd_t)
```

**Features** (all demeaned by the ticker's own anchor so one pooled model fits all names):

```
x1 = ln(E_1(v))   - ln(Vbar_i)
x2 = ln(E_5(v))   - ln(Vbar_i)
x3 = ln(E_25(v))  - ln(Vbar_i)
x4 = ln(E_125(v)) - ln(Vbar_i)
x5 = ln(E_5(s_neg) / E_5(v))              # downside share (sign information)
x6 = ln(G_t)                               # global factor
```

**Estimation**: single pooled OLS across all 33 tickers, target `y - ln(Vbar_i)`,
expanding window, refit monthly. Ridge penalty lambda = 1e-3 [PROVISIONAL] for
stability on short history. Forecast with log-normal correction:

```
sigma_fwd_i(t)    = sqrt( Vbar_i * exp( x'beta + 0.5*resid_var ) )     # annualized vol, decimal
```

**Downside forecast** `sigma_fwd_dn`: identical regression with target
`ln( (252/h) * sum s_neg_{t+j} )`. Drives gates (Module B) and the risk dial (C3).

Seed betas until the panel supports estimation (>= 250 pooled target observations):
`beta = [0.10, 0.25, 0.35, 0.20, 0.15, 0.10]` [PROVISIONAL — HAR-typical weights
shifted toward slower components at the 21d horizon].

### A4. Forward VRP (the tradeability core)

```
FVRP_ratio_i = IV30_i / sigma_fwd_i                     # both annualized vol, decimal
FVRP_z_i     = zscore( ln(FVRP_ratio_i) ; trailing 252d, min 60 obs, else pooled )
```

Dead zones (ineligible below): index/ETF sleeve **1.20**, single names **1.15**
[PROVISIONAL — re-expressed against forecast RV; subject to pre-registered Test T1].
Absolute-premium floor: `IV30 - sigma_fwd >= 2.0 vol points` [PROVISIONAL] — a ratio
on a 10-vol name is not a fundable edge after frictions.

The composite 0–100 score is retained for **gating and telemetry only**. No
cross-sectional allocation by rank. IV percentile (25 pts) is demoted from
tradeability input to capital-efficiency context.

---

## Module B — Gate State Machine (hysteresis everywhere)

Per-ticker state: `NORMAL -> CAUTION -> DANGER`, plus tag `CAUTION_TRANSIENT`.
All transitions require **2 consecutive sessions** beyond threshold (reuse of the
existing 2-day confirmation, applied to regimes). Hysteresis: exit threshold is
always tighter than entry threshold, so a state cannot flip on one noisy print.

**G1 — Earnings (INHERITED, hardened).** No naked single-name entry with earnings
inside the holding window + 5 sessions. Date must be verified against the company IR
page or TipRanks when FMP and scanner disagree; unverified = gated.

**G2 — Term structure.** Slope = `IV_1M / IV_3M` (replaces 1W/1Y — front tenor was
event-contaminated, back tenor thin; docs inconsistency resolved in favor of 1M/3M).

```
CAUTION: enter slope >= 1.00, exit <= 0.98      [PROVISIONAL]
DANGER:  enter slope >= 1.05, exit <= 1.02      [PROVISIONAL]
```

**G3 — Downside RV acceleration** (replaces rv10/rv30 on total vol):

```
A_t = sqrt( E_5(s_neg) / E_25(s_neg) )          # vol-space ratio
CAUTION: enter A >= 1.10, exit <= 1.05
```

Transient tag: if the trailing-10-session concentration
`max(s_neg) / sum(s_neg) > 0.5` AND G2 is NORMAL, tag `CAUTION_TRANSIENT`:
new entries blocked 3 sessions, then eligibility restored without waiting for A to
mean-revert (jump-driven spikes have ~zero persistence; diffusive downside moves are
the persistent, dangerous kind).

**G4 — Negative forward VRP.** `FVRP_ratio < 1.00` → ineligible, unconditionally.

**G5 — Portfolio regime (new).** Book-wide freeze on NEW entries when either:
(a) index (SPY) FVRP_ratio < 1.00, or (b) 20-session change in global factor G_t has
z > 2.0 [PROVISIONAL]. Existing positions are managed by their own rules; the health
monitor (E4) governs de-grossing.

**Post-spike re-entry ramp (replaces binary gate clearance).** After DANGER clears:
eligibility fraction ramps as `min(1, sigma_fwd_dn(pre-spike) / sigma_fwd_dn(now))^2`
applied to the opportunity dial output — sized up exactly as the forecast collapses
under still-elevated IV, which is where the corpus locates the fattest entries.

---

## Module C — Sizing (two dials, one precedence rule)

**Precedence: Caps (C6) > Dials (C3, C4) > Kelly base (C2).** Dials are computed at
entry; open positions are never resized daily (churn is pure friction).

### C1. Margin per contract (short put)

```
M = 100 * max( P + alpha*S - max(S - K, 0),  P + 0.10*K )
alpha = 0.20 (CBOE/Reg-T default; set 0.15 for IBKR)     # broker-configurable
```

Logged on every trade: `M`, and portfolio margin utilization. Sizing is
**margin-normalized**: all returns in the sizing layer are per margin dollar.

### C2. Kelly base (from the trade log, not GBM)

Outcomes: `x_j = PnL_j / M_j` per closed trade. Estimate `f*` by maximizing
`E[ln(1 + f*x)]` over a **block bootstrap by calendar month** (respects loss
clustering). Disaster injection: until the log contains a genuine vol event, each
bootstrap draw includes, with probability 2% per trade [PROVISIONAL], a synthetic
outcome of `3x the worst observed loss` — the sample contains no disaster, so the
naive f* is a benign-regime artifact. Apply fraction **phi = 0.25 (quarter-Kelly)**
[PROVISIONAL — half-Kelly is standard but assumes the tail is in the data; it is not].

### C3. Risk dial (forecast-downside-RV, NOT IV rank)

```
R_i = clip( median_252d(sigma_fwd_dn_i) / sigma_fwd_dn_i , 0.25, 1.25 )
```

R = 1 in a normal regime; cuts exposure when *forecast* downside vol is elevated
(persists through genuine deterioration); does not punish elevated IV per se.

### C4. Opportunity dial (forward VRP)

```
O_i = clip( 1 + 0.25 * clip(FVRP_z_i, -2, 2) , 0.5, 1.5 )    # kappa = 0.25 [PROVISIONAL]
```

Rationale for the split: (1 - IV_rank) conflates risk and opportunity and shrinks
size in post-spike windows where forecast RV has collapsed under elevated IV — the
best documented selling conditions. Here the risk dial handles danger, the
opportunity dial handles richness, and they can disagree.

### C5. Contracts

```
N_i = floor( Equity * phi * f_star * R_i * O_i / M_i )
```

### C6. Portfolio caps and the stress gate (binding; reject entries that breach)

```
Aggregate short-put notional (sum K*100*N)  <= 100% of equity     # cash-secured standard
Total initial margin                        <= 30% of equity      # band 25-35
Per-name initial margin                     <= 8%  of equity      [PROVISIONAL]
Per-name stressed loss                      <= 2.5% of equity     [PROVISIONAL]
Portfolio stressed loss                     <= 15% of equity      [PROVISIONAL]
```

**Stress revaluation** (per cycle and before every entry): full-book BSM reprice at
`{spot x0.80, IV x2.0, t + 5 sessions}`; report the intermediate `{x0.90, IV x1.5}`
scenario alongside. The no-stop-loss policy is only coherent if this gate guarantees
the implicit margin stop is unreachable — that is this module's entire purpose.

---

## Module D — Frictions

**D1. Pre-screen (scan time, per candidate contract):**

```
reject if quoted_spread / mid > 0.10
skip   if (2*half_spread + commissions) / (premium * 0.65) > 0.25
```

(0.65 = expected capture fraction under current profit-target rules [PROVISIONAL].)

**D2. Telemetry (per fill):** log `(fill - mid) / half_spread`. Alarm when the
rolling 20-fill mean exceeds 0.50 — at ~50% of half-spread the literature's
cost-filtered strategies survive; at ~76% they are marginal.

**D3. Spread-aware exit:** at 21 DTE, if remaining premium < 2 x current quoted
spread AND the strike is OTM by more than 1.5 x sigma_fwd (holding-horizon scaled)
AND no gate is active on the name: let the position decay to 7 DTE instead of paying
the second crossing. Otherwise the 21-DTE close is unconditional. Every exception is
logged with its trigger.

**D4. No rotation.** Never close position A to open marginally higher-scored B.
Entry requires the signal to persist (2-day confirmation already enforces this).

---

## Module E — Measurement Substrate (what makes the system falsifiable)

**E1. PSR / MinTRL (daily P&L, native frequency, never annualized inside the stat):**

```
sigma_SR = sqrt( (1 - g3*SR + ((g4-1)/4)*SR^2) / (n-1) )
PSR(SR*) = Phi( (SR - SR*) / sigma_SR )
MinTRL(SR*, a) = 1 + (1 - g3*SR + ((g4-1)/4)*SR^2) * ( Z_a / (SR - SR*) )^2
```

Report PSR(0) and PSR(0.5 annualized -> 0.5/sqrt(252) daily) with **worst-case
moments** (bootstrap 5th-percentile skew, 95th-percentile kurtosis) while the sample
is short. Acceptance bar 0.95. Evaluation frequency is daily, permanently.

**E2. Trial registry (append-only, no deletions):** JSONL rows
`{id, date, hypothesis, config_hash, data_window, registered_before_run: bool,
result_summary, adopted: bool}`. The Deflated Sharpe hurdle is computed from the
registry count N — every backtest ever run raises the bar whether or not it was
acted on. Governing rule: **three pre-registered confirmatory tests (Module F) may
change the system; everything else is exploratory and non-binding** until confirmed
on out-of-sample live data.

**E3. Realized VRP capture log (ground truth for the edge):** per closed trade and,
independently, per ticker-day: `IV30^2(entry) - RV_realized(holding window)` in
variance points, plus the log form. This series is simultaneously (a) the edge
validator, (b) the input to E4, and (c) the future option-momentum feature — build
once, three consumers.

**E4. Trailing-VRP health monitor (damage control, NOT tail protection):** rolling
90-day mean of E3 portfolio-wide. When < 0: new-entry gross x0.5 and naked -> spread
migration for new single-name entries. Explicitly documented as a lagging indicator;
the leading defenses are Module B and Module C.

**E5. Benchmarks:** daily NAV vs Cboe PUT and SPY total return; rolling 12-month
panel in the briefing. Bull-market lag vs SPY is regime-expected and is read against
PUT, not against absolute return.

**E6. Four-moment monitor:** rolling 60-day mean/SD/skew/kurtosis of daily P&L;
alert on z < -2 deterioration of skew vs the book's own trailing year.

---

## Module F — Pre-Registered Confirmatory Tests (the only three)

**T1 — Forward vs trailing VRP.** Population: historical ticker-days where
`IV/sigma_fwd` and `IV/RV30_trailing` disagree on eligibility. Instrument:
standardized short 20-delta put, current exit rules, logged effective spreads.
Metric: net expectancy difference + bootstrap CI; secondary: false-block rate in
post-spike windows. Adopt forecast denominator if point estimate >= 0 and post-spike
false-blocks fall. Registered before execution.

**T2 — DTE/delta grid.** {entry 45, 30} x {exit 21, 14, 10} x {20-30Δ, 30-40Δ},
net of two crossings at logged effective spread. Metric: PSR(0) per cell plus
stressed-gamma exposure per cell. Pre-commitment: adopt a change only if PSR improves
AND the stress-gate headroom does not shrink — a benign sample flatters later exits
and this is written down *before* seeing results.

**T3 — Naked vs defined-risk per underlying.** PSR(0.5) comparison per name;
adoption of the E4 migration rule if spreads dominate on PSR for the names where the
monitor historically dipped.

---

## Module G — Schema Additions

`daily_iv` (per ticker-day): `v_gk, s_neg, s_pos, ewma_v_{1,5,25,125},
ewma_sneg_{5,25}, vbar, sigma_fwd, sigma_fwd_dn, fvrp_ratio, fvrp_z, slope_1m3m,
gate_state, transient_tag, global_factor, capture_30d (backfilled)`

`trades`: `margin_per_contract, margin_util_at_entry, fill_vs_mid_entry/exit,
quoted_spread_entry/exit, iv_entry, sigma_fwd_entry, rv_realized_hold, capture,
dial_R, dial_O, f_star_at_entry, stressed_loss_at_entry`

`portfolio_daily`: `nav, notional_short_put, margin_total, stress_pnl_20_2x,
stress_pnl_10_15x, psr0, psr05, mintrl, monitor_e4, skew60, kurt60`

`trial_registry.jsonl`: as E2.

---

## Calibration ownership

[PROVISIONAL] constants in this spec: ridge lambda, seed betas, dead zones (1.20/1.15),
absolute-premium floor (2.0 pts), G2 slope thresholds, G5 z-trigger, disaster-injection
probability, phi = 0.25, kappa = 0.25, per-name caps, stress limits, capture fraction
0.65. Each is a literature-motivated starting point. They are calibrated by the
process in E2/F — never by iterating against the same 16 months until a number looks
good. The spec is falsifiable by T1-T3; the final authority is the data, not this
document.
