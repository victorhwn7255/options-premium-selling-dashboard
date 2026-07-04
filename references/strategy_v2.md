---
last_verified: 2026-07-04
verified_against: theta-harvest-v2-spec.md + theta_harvest_core.py (reference implementation)
status: v2 — ADOPTED 2026-07-04. Supersedes strategy.md v1 in full.
precedence: If any number here disagrees with theta-harvest-v2-spec.md, the SPEC wins.
audience: Claude Code agents + human review
companions: metrics.md (metric definitions) · theta-harvest-v2-spec.md (exact formulas) ·
            theta_harvest_core.py (reference math) · premium-selling-research-synthesis-2026-07.md (evidence)
---

# Theta Harvest — Trading Strategy (v2)

## 0. What changed from v1 (read this first)

| Area | v1 | v2 | Why |
|---|---|---|---|
| VRP definition | IV30 / trailing RV30 | IV30 / **pooled forecast of forward RV** (`sigma_fwd`) | Trailing RV overstates edge in complacency, understates it post-spike — bias is regime-correlated in the worst direction |
| RV estimator | close-to-close | GK+overnight daily proxy; YZ for levels; EWMA memory | Close-to-close is the noisiest defensible input; step windows cause churn |
| Term slope | 1W / 1Y (8 tenors) | **1M / 3M** | Front tenor was event-contaminated, back tenor thin; matches CPS overlay |
| RV accel gate | rv10/rv30 > 1.10, no hysteresis | **Downside semivariance** EWMA5/EWMA25 with hysteresis + transient tag | Sign matters (only downside vol persists); hysteresis kills the JNJ oscillation |
| Score role | Cross-sectional ranking + gate | **Gate + telemetry only** | No evidence ranking pays in a 33-name mega-liquid universe; the null is also unresolvable at this sample size |
| Sizing | Trader discretion | **Systematic: Kelly base × risk dial × opportunity dial, under hard caps + stress gate** | Sizing spans a ~50x range of outcomes on identical signals; it is the system's largest lever and was its largest gap |
| Frictions | Post-hoc observation | **Pre-screen at scan + per-fill telemetry** | Frictions are co-equal with signal quality; ~29% measured drag must be managed, not observed |
| Validation | Raw Sharpe / profit factor | **PSR / MinTRL / DSR + trial registry + PUT benchmark** | Negative-skew short samples systematically inflate raw Sharpe |
| THE FINALS trigger | Absolute VRP > 8 pts AND slope < 0.90 (unreachable) | Removed; replaced by continuous opportunity dial + post-spike re-entry ramp | The AND was near measure-zero; the ramp does the intended job continuously |

Unchanged and protected: earnings gate (hardened), 2-day confirmation, 45 DTE entry /
21 DTE exit / 75% profit target, no stop-loss (now made coherent by the stress gate),
no discretionary overrides, XLB never traded.

---

## 1. Thesis and expectations

The system harvests the variance risk premium: option-implied volatility systematically
exceeds subsequently realized volatility. The premium is real, persistent, and
concentrated in **index products** and **short-dated, downside variance**. It is
compensation for bearing crash risk — the edge and the tail are the same object.

Consequences the system is built around:

1. **The index/ETF book is the return engine.** Single names are satellites that must
   clear the same signal bar plus liquidity and earnings hurdles; single-name VRP is
   weak and heterogeneous in liquid mega-caps and loads on variance beta with the
   market, not on a name's own vol.
2. **Realistic performance target is the PUT-index profile**: equity-like returns at
   roughly two-thirds the volatility, worst-case drawdown on the order of −35% even
   fully collateralized, and *expected* underperformance vs SPY in calm bull markets.
3. **The benchmark is pre-committed**: rolling 12-month returns are judged against the
   Cboe PUT index and SPY. Lagging SPY in a low-vol bull is regime-expected, not
   system failure. This clause exists so the system is not dismantled in the regime
   that precedes its best one.
4. **The edge is the spread, not the level.** IV level or percentile alone has no
   time-series predictive power. The single documented losing state (2008-type) had
   record-high IV with negative realized VRP. Everything in the entry logic keys off
   IV relative to *forecast* RV.

## 2. Universe and structures

- **Tab 1 (naked puts):** 33-ticker universe (22 single names, 11 index/ETF).
  Risk budget tilts toward SPY/QQQ/IWM and sector ETFs. XLB is permanently excluded
  regardless of signal (structurally illiquid chain).
- **Tab 2 (credit put spreads):** SPY/QQQ/IWM only, same signal threshold as Tab 1
  (capital efficiency play, not a lower bar). Governed by its own build plan.
- Contracts sold: 20–30 delta puts, 45 DTE entry (±10 days chain tolerance),
  managed per Section 5. The 30–40Δ band and later exits are under pre-registered
  Test T2 and are NOT live.

## 3. Entry rules

A ticker-day is **entry-eligible** iff ALL of the following hold:

1. **Gate state NORMAL** (Section 4) with no transient blackout active.
2. **Forward VRP above the dead zone**: `FVRP_ratio = IV30 / sigma_fwd` ≥ 1.20
   (index/ETF) or ≥ 1.15 (single names) [PROVISIONAL — Test T1 owns these].
3. **Absolute premium floor**: `IV30 − sigma_fwd ≥ 2.0 vol points`. A rich ratio on a
   10-vol name is not a fundable edge after frictions.
4. **Earnings clear (single names)**: no earnings inside the holding window + 5
   sessions. The date must be verified (IR page / TipRanks) whenever FMP and the
   scanner disagree; **unverified = gated**. This gate's integrity is a known
   operational failure point — treat date verification as part of the trade.
5. **Friction pre-screen passes**: quoted spread ≤ 10% of mid, AND round-trip cost
   (one full spread + commissions) ≤ 25% of expected premium capture (65% of credit).
6. **2-day confirmation**: eligibility must hold on two consecutive scans before
   entry. Daily single-name VRP is too noisy for single-observation significance.
7. **Portfolio gate G5 open** and all sizing caps satisfied for the proposed size
   (Section 6) — an entry that breaches a cap is rejected, not trimmed into
   compliance by intuition; the sizing module computes the largest compliant size.

The composite 0–100 score is retained for telemetry and dashboards. **It does not
allocate.** No candidate is preferred over another because its score is higher; no
position is rotated into a marginally higher-scored name, ever.

## 4. Gate system (risk vetoes — priced insurance, not alpha)

Per-ticker state machine `NORMAL → CAUTION → DANGER` with hysteresis (exit thresholds
tighter than entry) and 2-consecutive-session confirmation on every transition.
Exact thresholds: spec Module B.

- **G1 Earnings** — as in Section 3.4.
- **G2 Term structure** — slope = IV_1M / IV_3M. CAUTION at ≥ 1.00, DANGER at ≥ 1.05.
  Backwardation is a time-series tail gate for an unhedged seller. It is deliberately
  NOT a ranking penalty: cross-sectionally, backwardated names pay sellers the most —
  avoiding them is insurance with a known premium cost, and we pay it.
- **G3 Downside RV acceleration** — `sqrt(EWMA5(s⁻)/EWMA25(s⁻))`, CAUTION at ≥ 1.10,
  exit ≤ 1.05. Sign-aware: upside-driven vol spikes do not trigger it.
  **Transient tag**: if the spike is single-day-dominated (concentration > 0.5) and
  G2 is NORMAL, the name gets a 3-session blackout then restored eligibility —
  jump vol has ~zero persistence; diffusive downside vol is the dangerous kind and
  waits out full hysteresis.
- **G4 Negative forward VRP** — `FVRP_ratio < 1.0` → ineligible unconditionally.
- **G5 Portfolio regime** — book-wide freeze on NEW entries when index FVRP < 1.0 or
  the global vol factor's 20-session change z-scores above 2. Existing positions are
  managed by their own exit rules.

**Post-spike re-entry ramp**: after DANGER clears, eligibility scales continuously
with the decay of forecast downside vol toward its pre-spike level (spec B, ramp
formula) rather than snapping back binary. The aftermath of a spike — IV still
elevated, forecast RV collapsing — is historically the richest selling window; the
ramp is how the system participates in it with sizing discipline instead of either
abstaining or lunging.

## 5. Exit rules

1. **Profit target 75%** of credit received (ADR-013).
2. **21 DTE unconditional close**, with ONE exception:
3. **Spread-aware decay exception** — at 21 DTE, if remaining premium < 2× current
   quoted spread AND strike is OTM by > 1.5× holding-horizon-scaled `sigma_fwd` AND
   no gate is active on the name: hold to 7 DTE instead of paying the second
   crossing. Every use is logged with its trigger values.
4. **DANGER flip on an open position**: close if the position is underwater;
   profitable positions may run to target/21 DTE (ADR-012 lineage — retained, but
   flagged: the supporting evidence is small and from a benign sample).
5. **No stop-losses.** This is only coherent because the stress gate (Section 6)
   guarantees the *implicit* stop — the margin call — is unreachable. If the sizing
   module is ever disabled, the no-stop policy is disabled with it. They are one
   design, not two.

## 6. Position sizing (systematic; precedence: caps > dials > Kelly base)

Size is computed at entry and **never resized daily** (churn is pure friction).

- **Kelly base** `f*`: block-bootstrapped (by month) growth-optimal fraction from the
  system's own trade log in per-margin-dollar units, with a synthetic disaster
  injection (2% probability of 3× worst observed loss per draw) until the log
  contains a genuine vol event. Applied at **quarter-Kelly** (φ = 0.25).
  `f* = 0` is a signal that the edge net of tail is not there — respect it.
- **Risk dial R** ∈ [0.25, 1.25]: median forecast downside vol ÷ current forecast
  downside vol. Cuts size when *forecast* risk is elevated. It does not punish high
  IV per se.
- **Opportunity dial O** ∈ [0.5, 1.5]: increasing in the forward-VRP z-score.
  Rewards richness relative to forecast. R and O are independent by design and may
  disagree — post-spike, R recovers as the forecast decays while O is elevated;
  that combination is the intended fat-entry state.
- **Contracts** = floor(Equity × φ × f* × R × O ÷ margin per contract).
- **Hard caps (binding, reject entries that breach):** aggregate short-put notional
  ≤ 100% of equity; total initial margin ≤ 30%; per-name margin ≤ 8%; per-name
  stressed loss ≤ 2.5%; **book stressed loss ≤ 15% of equity** under full BSM
  reprice at {spot −20%, IV ×2, +5 sessions}. The stress gate runs before every
  entry and every cycle.

## 7. Portfolio management and health

- **Trailing realized-VRP health monitor** (rolling 90-day mean of entry-IV² minus
  subsequently realized variance, portfolio-wide): when negative, new-entry gross is
  halved and new single-name entries migrate naked → defined-risk spreads.
  **This is damage control for a persistent losing regime, NOT tail protection** —
  it turns negative only after losses are booked. The leading defenses are the gates
  and the pre-committed sizing.
- **Four-moment monitor** on daily P&L; alert on skew deterioration vs the book's
  own trailing year.
- **Tail overlay (priced, not yet automated):** the dashboard displays the current
  cost to hedge the book with 3–6-month OTM index puts / VIX calls. The long end of
  the variance curve carries ~zero premium historically, so this insurance is cheap;
  purchase remains a human decision until separately systematized.

## 8. What this strategy deliberately does NOT do

No cross-sectional allocation by score. No rotation between open and marginally
better candidates. No universe expansion into higher-friction names (the measured
richness there is partly a liquidity illusion; revisit only if fill telemetry proves
≤ 50%-of-half-spread execution on the current universe). No trading XLB. No
discretionary threshold overrides. No stop-losses (see 5.5 for the condition that
makes this safe). No shorter-DTE sleeve (hypothesis only; requires Tier 1 telemetry
live first). No naked entries into unverified earnings dates.

## 9. Governance — how this strategy is allowed to change

Exactly **three pre-registered confirmatory tests** may change live behavior:
**T1** forward-vs-trailing VRP (owns the dead zones and the denominator),
**T2** DTE/delta grid net of two crossings judged on PSR + stress headroom
(owns entry/exit tenor and the delta band),
**T3** naked-vs-spread per underlying on PSR (owns the migration rule).
All other analyses are exploratory and non-binding until confirmed on new live data.
Every backtest run is recorded in the append-only trial registry; the deflated-Sharpe
hurdle rises with the registry count whether or not a result was adopted. Thresholds
are never iterated against the same window until a number looks good.
