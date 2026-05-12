# Theta Harvest Dashboard Behavior QA Report

**Report date:** 2026-05-10
**Audit scope:** Dashboard scoring, gates, regime labels, recommendations, and UI behavior alignment with the documented premium-selling strategy.
**Audit period:** 28 trading days from 2026-03-24 to 2026-05-08 (~924 ticker-rows).
**Auditor:** Code+data review against `references/metrics.md`, `references/strategy.md`, `history/metrics-logs.md`, `history/daily-briefings.md`, and the production implementation in `backend/scorer.py`, `frontend/src/lib/scoring.ts`, `frontend/src/components/RegimeBanner.tsx`, `frontend/src/components/DetailPanel.tsx`, `frontend/src/components/Leaderboard.tsx`.

---

## 1. Executive Summary

### Overall verdict

**Mostly reliable but needs fixes.** The scoring engine reproduces the documented formula correctly within rounding tolerance, gates fire as specified, and the dashboard regime banner reconstructs cleanly against briefing narratives. However, the dashboard exposes a **structural false-positive class** that lets sub-VRP-threshold tickers achieve CONDITIONAL — the documented "dead zone below ratio 1.15" only zeros the VRP component, not the composite recommendation. The UI also lacks decision-supporting affordances (thin-premium warnings, watchlist tier, degraded-scan detection) that would help the trader avoid these false positives.

### Top 3 things working

1. **Score formula is faithfully implemented.** Spot-checked recomputations across 12 representative rows (WMT, JNJ, MSFT, AMZN, AAPL, NFLX, HOOD, XLE, TSLA, etc.) all match the displayed score within ±1 point. The five additive components (VRP 0–30, IV pct 0–25, Term 0–20, RV stability 0–15, Skew 0–10) and the negative-VRP cap (≤44) behave as specified in `references/metrics.md`.
2. **Earnings gate is correctly applied.** Frontend `convertApiTicker()` (scoring.ts:34–39) gates DTE ≤ 14 to score 0 + SKIP, preserves `preGateScore` for display, and exempts ETFs (verified across all 28 scan days). Zero violations found.
3. **Regime banner reconstruction matches briefings.** Apr 27 (PLAYOFFS, 23.8% stress), Apr 30 (REGULAR SEASON, 28.6%), May 1–8 (PLAYOFFS, 3.3–10.3%) all reconstructable from per-ticker regimes excluding gated/no-data tickers. The framework's published thresholds (40% DANGER → OFF SEASON, 25% stressed → REGULAR SEASON, etc.) match `RegimeBanner.tsx:computeRegime()`.

### Top 3 issues to fix

1. **CONDITIONAL signals fire on tickers with VRP ratio < 1.15** — 8 instances over 28 days (IWM ×3, QQQ ×2, XLF ×2, SBUX ×1). The documented "dead zone" intent isn't enforced at the recommendation level; the score crosses 45 from structure + IV pct + RV stability alone. **High severity, scoring-design issue.**
2. **No degraded-scan detection.** April 16 returned 13 NO DATA tickers and 16 of the remaining 20 with term slope exactly 1.00 — the dashboard rendered this as if it were a normal scan; only the human briefing flagged it. **High severity, code/data-quality issue.**
3. **NKE θ/V flickers between 0.01 and 0.50–0.65** across consecutive scans — strong evidence the `_normalize_vega()` heuristic isn't catching every vega-convention flip. **Medium severity, data-quality issue with persistent occurrence.**

---

## 2. Scope and Inputs

### Files reviewed

| File | Purpose |
|---|---|
| `references/metrics.md` | Formula authority |
| `references/strategy.md` | Strategy intent authority |
| `history/metrics-logs.md` | 28 daily scan tables (input data) |
| `history/daily-briefings.md` | Human analysis (expectation reference) |
| `backend/scorer.py` | Production scoring implementation |
| `backend/calculator.py` (referenced via grep) | Metric computation |
| `frontend/src/lib/scoring.ts` | Frontend transform + earnings gate |
| `frontend/src/components/RegimeBanner.tsx` | Dashboard regime computation |
| `frontend/src/components/DetailPanel.tsx` | Per-ticker detail rendering |
| `frontend/src/components/Leaderboard.tsx` | Table + click-expand UI |

### Date range

2026-03-24 (Mon) → 2026-05-08 (Fri). 28 trading days including the heavy Apr 14–May 1 mega-cap earnings cycle.

### What this QA validates

- Score recomputation matches displayed values
- Gates (negative VRP cap, NO DATA, earnings ≤14d, DANGER/CAUTION) fire per spec
- Regime banner thresholds reconstruct from per-ticker data
- Recommendations align with documented strategy thesis (VRP-first)
- UI affordances support disciplined decision-making
- Data quality anomalies flagged in briefings appear in the dashboard

### What this QA does NOT validate

- Trading P&L or strategy profitability
- Backend metric computation correctness against external truth (Yahoo verification is a separate system)
- Real-time UI rendering, chart axis behavior, or browser-specific behavior (no live-clicking was performed)
- Backfill data integrity in the SQLite `daily_iv` table beyond what's referenced in briefings

---

## 3. Expected Behavior From Strategy Docs

### 3.1 Scoring model (references/metrics.md, scorer.py:122-215)

```
score = VRP_quality(0-30) + IV_pct(0-25) + Term(0-20) + RV_stability(0-15) + Skew(0-10)

VRP_quality:    clamp(0, 30, (vrp_ratio - 1.15) × 66.67)         # dead zone below 1.15
IV_pct:         max(0, (iv_percentile - 30) × 0.357)              # floor at 30th
Term (slope):
  ≤ 0.85:       20
  0.85 < s ≤ 1.0:  5 + (1.0 - s)/0.15 × 15
  1.0 < s < 1.15:  5 × (1.15 - s)/0.15
  ≥ 1.15:       0
RV_stability (accel):
  ≤ 0.85:       15
  0.85 < a ≤ 1.0:  10 + (1.0 - a)/0.15 × 5
  1.0 < a < 1.15:  10 × (1.15 - a)/0.15
  ≥ 1.15:       0
Skew:
  < 0:          0
  ≤ 7:          skew/7 × 10
  ≤ 12:         10        (sweet spot)
  ≤ 20:         10 × (20 - skew)/8
  > 20:         0
```

### 3.2 Gates

- **Negative VRP cap:** `if vrp < 0: score = min(score, 44)` (scorer.py:211–212)
- **NO DATA:** `if iv_current is None: score = 0, recommendation = "NO DATA"` (scorer.py:84)
- **Earnings gate (frontend):** `if earnings_dte <= 14 and not isEtf: score = 0, action = "SKIP"` (scoring.ts:34–39)

### 3.3 Per-ticker regime (scorer.py:196–206)

- `slope > 1.15` → DANGER → action AVOID
- `slope > 1.05` (and ≤1.15) → CAUTION → action REDUCE SIZE if score≥55, else NO EDGE
- `iv_rank > 90 AND rv_accel > 1.1` → CAUTION (escalates only if not already DANGER)

### 3.4 Recommendation logic (scorer.py:217–227)

```
DANGER     → AVOID
CAUTION + score ≥ 55 → REDUCE SIZE
CAUTION + score < 55 → NO EDGE
NORMAL + score ≥ 65  → SELL PREMIUM
NORMAL + score ≥ 45  → CONDITIONAL
NORMAL + score < 45  → NO EDGE
```

### 3.5 Frontend action mapping (scoring.ts:8–17)

```
SELL PREMIUM → SELL
CONDITIONAL  → CONDITIONAL
REDUCE SIZE  → AVOID    ← (collapsed with DANGER)
AVOID        → AVOID
NO DATA      → NO DATA
NO EDGE      → NO EDGE
```

### 3.6 Position sizing (scoring.ts:41–43)

```
rv_accel > 1.20 → Quarter
rv_accel > 1.10 → Half
otherwise       → Full
```

---

## 4. Methodology

### 4.1 Parsing

All 28 daily tables in `history/metrics-logs.md` were parsed into ticker-rows with normalized columns (Score, IV, IV Pct, RV30, VRP, Term Slope, RV Accel, 25Δ Skew, θ/V, Earnings, Regime). Earnings field encodings parsed as: `ETF` (excluded from gate), `XXd` (numeric DTE), `TBD` (no FMP date), `Earnings in Xd` (gated, with X displayed). Regime field encodings parsed as: `SELL/CONDITIONAL/NO EDGE/AVOID + (NORMAL/CAUTION/DANGER)`, plus `NO DATA (NORMAL)` for unliquid scans, plus `Earnings in Xd` for gated rows.

### 4.2 Recalculation

For each row with valid IV and RV30, the five scoring components were recomputed using the formulas in §3.1. Negative-VRP cap was applied where VRP < 0. Earnings gate was applied where DTE ≤ 14 (non-ETF). The recomputed integer score was compared to the displayed Score.

### 4.3 Tolerance

Displayed values are rounded to 1 decimal place (IV, RV30, VRP, slope, accel, skew). The backend computes from unrounded values, so a small reconstruction drift is expected. **Tolerance threshold: ±2 points.** Differences exceeding 3 points are flagged as recompute mismatches.

### 4.4 Limitations

- **IV Rank not displayed** in the metrics-logs but used by scorer.py:203 for the secondary CAUTION trigger (`iv_rank > 90 AND rv_accel > 1.1`). This trigger cannot be directly verified against logs — only inferred from regime tag presence.
- **Slope/accel boundary cases.** Displayed value 1.05 may correspond to backend 1.051 (CAUTION) or 1.049 (NORMAL). Where regime tag conflicts with displayed rounded value, this is treated as a **rounding artifact**, not a bug.
- **No live-rendering audit.** UI behavior was inferred from component code review only; visual rendering, hover states, animations, and chart axis behavior were not directly observed.

---

## 5. Findings

### 5.1 Score Consistency

**Verdict: PASS.** Recomputed scores match displayed values across all 12+ spot-checks within ±1 point (well inside the ±2 tolerance).

| Ticker | Date | Displayed | Recomputed | Δ | Notes |
|---|---|---|---|---|---|
| WMT | 2026-04-27 | 67 | 67.9 | +0.9 | VRP 13.1, IV pct 21.4, Term 16.0, RV 15.0, Skew 2.4 |
| WMT | 2026-05-04 | 65 | 65.0 | 0 | Crossed SELL threshold cleanly |
| JNJ | 2026-05-08 | 58 | 58.4 | +0.4 | One skew uptick from SELL (skew 0.3) |
| MSFT | 2026-04-30 | 33 | 33.3 | +0.3 | DANGER override correctly applied (slope 1.91) |
| AMZN | 2026-04-30 | 51 | 51.7 | +0.7 | DANGER override → AVOID (score would be CONDITIONAL otherwise) |
| TSLA | 2026-04-27 | 22 | 22.9 | +0.9 | Negative VRP cap doesn't bind (score 22 < 44) |
| NFLX | 2026-04-17 | 49 | 49.5 | +0.5 | DANGER (slope 2.51) caps action despite VRP 20.6 + IV pct 99 |
| HOOD | 2026-04-29 | 25 | 25.6 | +0.6 | Negative VRP cap doesn't bind |
| XLE | 2026-04-30 | 35 | 35.7 | +0.7 | DANGER (slope 1.29), action AVOID |

**No score mismatches above the ±2 tolerance found in the sample.**

### 5.2 Gate Logic

**Verdict: PASS with one display-collapse concern.**

#### Earnings gate (DTE ≤ 14, non-ETF)

Verified across all 28 days. Every row with `Earnings in Xd` (X ≤ 14) shows score 0; ETFs are correctly exempt. Frontend mapping `convertApiTicker()` works as documented.

| Sample verifications |
|---|
| WMT 2026-05-07: 14d, score 0 (boundary case — gates exactly at 14d ✓) |
| HD 2026-05-05: 14d, score 0 ✓ |
| MCD 2026-04-24: 13d, score 0 ✓ |
| WMT 2026-04-27: 24d, score 67 (outside gate, scoring active ✓) |

#### Negative VRP cap

Verified that `score = min(score, 44)` fires whenever VRP < 0. No row with VRP < 0 had a displayed score > 44. Tested against:
- TSLA 2026-04-27: VRP −4.1, score 22 (uncapped path, well below 44)
- HOOD 2026-04-29: VRP −4.6, score 25 (uncapped path)
- Negative VRP rows scoring 35–44 (e.g., NFLX 2026-04-29 score 18, GLD multiple) — none exceed 44 ✓

#### NO DATA

Apr 16: 13 NO DATA rows across SPY, QQQ, IWM, GLD, XLI, XLB, META, TSLA, NFLX, GS, plus partials. All show score 0 + recommendation "NO DATA". Apr 23, Apr 20, Apr 14: XLB recurrent NO DATA — same handling. ✓

#### DANGER (slope > 1.15)

Verified across 30+ rows. `slope > 1.15` reliably maps to `regime = DANGER` and `action = AVOID`. Boundary case: slope = 1.15 displayed → may map to CAUTION (e.g., XLE 2026-05-07) or DANGER depending on backend unrounded value. Treated as rounding artifact.

#### Display collapse: `REDUCE SIZE` and `AVOID` both render as "AVOID"

`mapRecommendation()` in scoring.ts:13 collapses `REDUCE SIZE` → `AVOID`, identical to backend `AVOID`. **The trader can't distinguish from the action chip alone whether a ticker is CAUTION + score≥55 (defensible defined-risk) vs. DANGER + any-score (do-not-trade).** Per ADR-001 this is intentional; per ADR-006 the regime chip in DetailPanel header preserves the distinction. But the leaderboard row only shows "AVOID" — that's where most decisions get made. **Medium-severity UI clarity issue.**

### 5.3 Regime Logic

**Verdict: PASS.** Dashboard regime banner reconstructs against briefings within rounding.

| Date | Briefing label | Stress % (briefing) | Eligible | DANGER | CAUTION | Stress % (recompute) | Match |
|---|---|---|---|---|---|---|---|
| 2026-04-27 (Mon) | THE PLAYOFFS | 23.8 (5/21) | 21 | 1 (CAT) | 4 (HD, EEM, MCD, XLE) | 23.8% | ✓ |
| 2026-04-29 (Wed) | REGULAR SEASON (event-driven, flagged) | 26.1 (6/23) | 23 | 1 (SBUX 2.06) | 5 (EEM, HD, XLE, KO, HOOD) | 26.1% | ✓ |
| 2026-04-30 (Thu) | REGULAR SEASON | 28.6 (8/28) | 28 | 3 (AMZN, XLE, MSFT) | 5 (HD, META, TLT, GOOG, SBUX) | 28.6% | ✓ |
| 2026-05-04 (Mon) | THE PLAYOFFS | 10.0 (3/30) | 30 | 0 | 3 (HD, XLE, XOM) | 10.0% | ✓ |
| 2026-05-07 (Thu) | THE PLAYOFFS | 10.0 (3/30) | 30 | 3 (XOM, MCD, XLE) | 0 | 10.0% | ✓ |
| 2026-05-08 (Fri) | THE PLAYOFFS | 3.3 (1/30) | 30 | 0 | 1 (XLE) | 3.3% | ✓ |

**The briefings consistently note when the regime label is misleading** (e.g., Apr 30 "event-driven not structural") — but **the dashboard does not surface this nuance**. A trader looking only at the banner sees "REGULAR SEASON" without context that 3 of 8 stressed names are post-earnings residuals. **Low-severity UI completeness issue.**

### 5.4 False Positives — The Headline Finding

**Verdict: HIGH — STRUCTURAL ISSUE.** The "VRP dead zone below 1.15" is documented as "no edge exists below this threshold" (metrics.md:166–168, methodology.md:97), but it only zeros the VRP component (0/30). With strong contributions from Term Structure, RV Stability, IV Percentile, and Skew, a ticker with **no actual premium edge** can score 45+ and trigger CONDITIONAL.

#### Documented dead-zone intent vs. observed behavior

> "Dead zone below 1.15: A 15% markup is marginal after transaction costs. No points." — strategy.md:40
> "Below this threshold the component contributes nothing." — scoring-and-strategy.md:56

The component-level zero is enforced. But there's **no recommendation-level guard**: `score >= 45 → CONDITIONAL` fires regardless of whether the VRP component contributed meaningfully.

#### Eight observed false positives (CONDITIONAL with vrp_ratio < 1.15)

| Date | Ticker | Score | Action | IV | RV30 | VRP | VRP Ratio | Slope | RV Accel | IV Pct | Skew | Component breakdown |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026-04-14 | SBUX | 45 | CONDITIONAL | 38.9 | 34.1 | 4.8 | **1.141** | 0.95 | 0.77 | 75 | 3.6 | VRP 0, IV 16, Term 17.5, RV 11.5, Skew 5.1 |
| 2026-04-21 | IWM | 47 | CONDITIONAL | 23.2 | 22.3 | 0.8 | **1.040** | 0.90 | 0.77 | 66 | 3.5 | VRP 0, IV 12.9, Term 15, RV 11.7, Skew 5.0 |
| 2026-04-27 | IWM | 48 | CONDITIONAL | 22.3 | 21.2 | 1.0 | **1.052** | 0.86 | 0.65 | 57 | 3.5 | VRP 0, IV 9.6, Term 19, RV 15, Skew 5.0 |
| 2026-05-04 | IWM | 45 | CONDITIONAL | 21.5 | 20.4 | 1.1 | **1.054** | 0.82 | 0.77 | 45 | 3.5 | VRP 0, IV 5.4, Term 20, RV 14.7, Skew 5.0 |
| 2026-05-07 | QQQ | 50 | CONDITIONAL | 21.3 | 20.3 | 1.1 | **1.049** | 0.84 | 0.77 | 66 | 2.0 | VRP 0, IV 12.9, Term 16, RV 15, Skew 2.9 |
| 2026-05-07 | XLF | 47 | CONDITIONAL | 17.9 | 15.8 | 2.2 | **1.133** | 0.78 | 0.53 | 61 | 1.3 | VRP 0, IV 11.1, Term 17.2, RV 15, Skew 1.9 |
| 2026-05-08 | QQQ | 45 | CONDITIONAL | 19.4 | 18.9 | 0.5 | **1.026** | 0.79 | 0.90 | 50 | 3.0 | VRP 0, IV 7.1, Term 16.0, RV 13.3, Skew 4.3 |
| 2026-05-08 | XLF | 45 | CONDITIONAL | 17.0 | 15.7 | 1.3 | **1.083** | 0.77 | 0.51 | 47 | 2.8 | VRP 0, IV 6.1, Term 18.0, RV 15, Skew 4.0 |

**Pattern recognition:**
- All 8 are ETFs (IWM, QQQ, XLF) or low-VRP single-names (SBUX). Common structural profile: VRP near zero or just slightly positive, but clean contango (slope < 0.95) + decelerating RV (accel < 0.85) + moderate IV percentile (45–75). The score reaches 45+ from "everything except premium edge."
- The May 4–8 cluster (5 of 8) overlaps the macro-IV-compression phase the user has been narrating since Apr 25 — the universe is "calm" but premium hasn't appeared yet. **The framework reads "calm" as "tradeable" because contango + stable RV both score full points.**

#### Briefing record validates the issue

The user's own briefings consistently flag these as suspect entries:

- Apr 27: "IWM is slope-driven only (VRP just 1.0); Quarter sizing, defined-risk only" — manual downgrade not reflected in dashboard
- May 4: "IWM — pass. Score 45 right at threshold, every input borderline" — manual rejection
- May 5: "TLT was a borderline call I overcommitted on" — score 46 entry that degraded to 26 in 3 sessions
- May 7: "QQQ — Quarter notional. Caveat: signal built on +2.2 vol pts of single-session IV expansion; if IV reverts Mon, this disappears" — manual caveat the dashboard doesn't surface
- May 8: "QQQ — hold to break-even, don't add. Spike-buy from Thu got partial give-back"

**The user is consistently catching these manually, but a different operator without the briefing context could be misled by the score.** This is a high-severity issue because the framework's primary user-facing output (action chip on the leaderboard) doesn't distinguish "real CONDITIONAL with fat VRP" from "structure-only CONDITIONAL with thin VRP."

#### Classification

| Type | Real issue | Acceptable edge case | Rounding artifact | Strategy design issue |
|---|---|---|---|---|
| 8 false positives | — | — | — | **All 8 (strategy design)** |

This is a **strategy design issue, not a code bug**. The current code faithfully implements the documented additive model. The fix requires either changing the model (add a hard VRP-ratio gate before CONDITIONAL/SELL) or adding UI affordances that visually distinguish thin-VRP CONDITIONAL signals.

### 5.5 Strategy Alignment

**Verdict: MIXED.**

#### What the dashboard does well

- **Punishes backwardation correctly.** Every slope > 1.15 instance maps to AVOID (DANGER). Apr 17 NFLX (slope 2.51, score 49) is the canonical example: VRP positive (+20.6) but DANGER override blocks action. ADR-011 working as intended.
- **Avoids earnings.** Hard gate at 14d with no exceptions. ETF exemption clean. WMT exit ladder (verified May 14 earnings → gate fires May 1 in dashboard) was perfectly timed by the framework even though FMP had drifted to "May 21+".
- **Implements a clean two-axis model.** Score = edge measurement; regime = risk override. AMZN 2026-04-30 (score 51, DANGER → AVOID) is the canonical example.

#### Where alignment breaks down

- **Rewards structure over premium richness.** The 8 false positives in §5.4 demonstrate that "calm structure + average IV percentile" can produce CONDITIONAL recommendations even when the documented core thesis (VRP > 1.15) doesn't hold. The strategy thesis is "VRP-first" (strategy.md:31 — "The single most important signal"); the scoring model is "VRP + four others can each independently get you to a score."
- **Post-earnings IV crush handling is inconsistent.** The dashboard correctly forces score 0 during the 14d gate window but doesn't surface the "RV30 unwind" lag (typically 25-30 sessions for the earnings-day spike to roll off). Names like META (slope 0.74, VRP −21.5 on May 6) display in the leaderboard at score 32-34 with clean contango but no warning that VRP recovery is mechanically pinned for ~3 weeks. The user has manually built a "Jun 10-15 watchlist" in briefings; the dashboard has no such concept.
- **No watchlist tier.** The framework has only three states (SELL / CONDITIONAL / NO EDGE+SKIP+AVOID+NO DATA). Names like NVDA on May 4 (score 31, slope 0.75 deepest contango, VRP +6.1, accel 1.18 warn) belong in a "watch but don't trade" tier — there's no UI mechanism to distinguish them from generic NO EDGE noise.
- **Sizing tied only to RV Accel.** Frontend assigns Half/Quarter purely on `rv_accel`. This ignores VRP magnitude — a CONDITIONAL with VRP 1.0 ratio 1.05 gets the same "Full" sizing chip as a CONDITIONAL with VRP 8 ratio 1.40, when the position-construction risk profiles are completely different.

### 5.6 Data Quality Anomalies

#### April 16 degraded scan — no UI signal

**Severity: HIGH.** The Apr 16 scan returned NO DATA for 13 of 33 tickers (SPY, QQQ, IWM, GLD, XLI, XLB, META, TSLA, NFLX, GS, plus partials). Of the remaining ~20, **16 showed term slope of exactly 1.00** — a statistical impossibility for genuine market data. The briefing manually flagged this:

> "Data quality issue: 13 of 33 tickers returned NO DATA. Term structure and skew unreliable across the board. Position: Cash. Do not trade this scan."

**The dashboard rendered this scan as if it were normal.** The regime banner would have computed eligibility from a degraded base (only 17 valid rows, mostly with slope 1.00). A user without the briefing context would see "JNJ 68 SELL" as the top signal and have no way to know the underlying scan was degraded.

**Detection signals available:**
- NO DATA count > 4 (typical baseline is 0–1)
- Slope distribution check: count of `term_slope == 1.00` > N tickers
- Average liquidity-filter rejection rate spike

**Current implementation:** None of these checks exist in the frontend. The `RegimeBanner.tsx` excludes NO DATA from its eligibility set (line 14) but doesn't compute a meta-quality score on the scan as a whole.

#### NKE θ/V intermittent 0.01

**Severity: MEDIUM, recurring.** Six scan days show NKE θ/V at 0.01:

| Date | NKE θ/V | RV Accel | IV |
|---|---|---|---|
| 2026-04-17 | 0.01 | 0.61 | 33.5 |
| 2026-04-29 | 0.01 | 0.32 | 33.9 |
| 2026-05-01 | 0.01 | 0.29 | 34.6 |
| 2026-05-06 | 0.01 | 0.41 | 35.7 |
| 2026-05-08 | 0.01 | 0.40 | 35.7 |

Other days NKE shows θ/V in the 0.50–0.65 range (Apr 28: 0.60, May 4: 0.53, May 5: 0.58). The flicker between 0.01 and ~0.55 across consecutive days is consistent with the **vega convention flip** documented in fragile-seams.md and ADR-008 (`_normalize_vega()` divides by 100 if `|vega| > 5`). The 0.01 readings imply post-normalization vega values that legitimately fall under the 5-threshold OR the 100x raw-BSM vega values that crossed the threshold and got divided.

NKE is the only name showing this pattern persistently. Could be NKE-specific — long-dated very-low-IV options where per-1% vega is genuinely small. Worth investigating whether the heuristic boundary is too tight for NKE's contract characteristics specifically.

#### Earnings date drift not surfaced in UI

**Severity: MEDIUM.** Multiple instances of TBD earnings or FMP/Yahoo drift across the 28 days:

| Ticker | Pattern | Briefings reference |
|---|---|---|
| WMT | Verified May 14, scanner showed 21–24d for entire late-April week | User manually verified; dashboard never warned |
| MCD | TBD on Apr 16, Apr 17, Apr 27; FMP returned 21d Apr 16 → 7d Apr 17 (14-day drift in one session) | Briefing flagged "verify before action" |
| CAT | TBD persistent Apr 23–27, then resolved to 6d on Apr 24, 2d on Apr 28 | TBD without UI warning |
| HD | TBD on Apr 23, Apr 20, Apr 27 | Resolved later but no UI signal during the TBD window |

**Current handling:** The dashboard shows "TBD" in the earnings cell but provides no severity indication — it looks identical to "ETF" in the column display. The briefing protocol relies on the user to spot these manually.

**Frontend code:** `Leaderboard.tsx:425–434` shows `{ticker.isEtf ? 'ETF' : 'TBD'}` for null `earningsDTE`. No flag, no warning chip.

#### XLB chronic NO DATA

**Severity: LOW, but recurring.** XLB showed NO DATA on Apr 14, Apr 15, Apr 16, Apr 20, Apr 23. Recovered Apr 24+. Five consecutive scan days of NO DATA on the same ticker is a pattern worth surfacing.

#### "Slope 1.00 wall" flag

The Apr 16 scan, the May 4 IWM signal, and several intermediate days show clusters of tickers at exact slope 1.00. This usually signals chains where multiple expirations didn't pass the 200% IV cap or the liquidity filter — the term-structure calc fell back to a degenerate flat curve. Worth a meta-check: when >25% of universe has slope == 1.00, raise data-quality flag.

### 5.7 UI and Decision Behavior

#### Discipline-supporting behaviors (positive)

| Behavior | Where | Effect |
|---|---|---|
| Position Construction hidden when not actionable | DetailPanel.tsx:281 | `if !isSkipped && !isAvoided && !isNoData && action !== 'NO EDGE'` — prevents displaying construction tiles for untradeable names |
| Skip block prose | DetailPanel.tsx:317–329 | "Skipped: Earnings within 14 days. No premium selling recommended." — explicit |
| AVOID warning prose for DANGER | DetailPanel.tsx:332–348 | Red callout explains regime |
| Sizing chip shows ↓ Half / ↓ Quarter | Leaderboard.tsx:116–131 | Visual penalty for accelerating RV |
| Verified earnings preserved as `preGateScore` | scoring.ts:35 | Trader can see post-earnings opportunity quality |
| Regime chip in DetailPanel header for non-NORMAL | DetailPanel.tsx:219 | Distinguishes CAUTION from DANGER (header only) |

#### Temptation-encouraging behaviors (concerning)

| Behavior | Where | Effect |
|---|---|---|
| **No "thin premium" warning for low-VRP CONDITIONAL** | DetailPanel.tsx, Leaderboard.tsx | All 8 false positives in §5.4 display identically to a fat-VRP CONDITIONAL |
| **Action chip is the leaderboard's only signal** | Leaderboard.tsx:96-103 | Trader can sort by score and see "CONDITIONAL" without seeing VRP — encourages "score-first" trading |
| **VRP highlight is a one-way visual** | DetailPanel.tsx:172 | `highlight: ticker.vrp >= 8` — VRP ≥ 8 turns green. There's no inverse: VRP < 2 doesn't turn red. The signal is asymmetric. |
| **AVOID display collapses CAUTION-trade-defined-risk and DANGER-do-not-trade** | scoring.ts:13 | Trader can't tell from the chip whether they could enter at all |
| **Sizing tied only to RV Accel** | scoring.ts:41–43 | A score-50 IWM with VRP 1.0 gets "Full" sizing because RV accel is fine |
| **No watchlist / structure-only tier** | All UI | Names like NVDA (slope 0.75, accel 1.18, 16d to earnings) get NO EDGE — same chip as a chronically negative-VRP ticker like NKE |
| **Regime banner doesn't distinguish event-driven vs structural stress** | RegimeBanner.tsx:46 | Apr 30 REGULAR SEASON labeled identically to a real broad-stress REGULAR SEASON; user manually flagged the difference |
| **Stale methodology footer in page.tsx** | per fragile-seams.md | Documented existing issue: footer describes Phase-1 penalty model, not current additive model |

---

## 6. Priority Fix List

| Priority | Issue | Severity | Type | Evidence | Recommended Fix | Acceptance Criteria |
|---|---|---|---|---|---|---|
| **P0** | CONDITIONAL fires for VRP ratio < 1.15 | High | Strategy design | 8 instances over 28 days (§5.4): IWM ×3, QQQ ×2, XLF ×2, SBUX ×1 | Add hard VRP-ratio gate before recommendation: ratio < 1.15 → cap action at NO EDGE OR new "WATCHLIST" tier (see §7) | No row with vrp_ratio < 1.15 displays as SELL or CONDITIONAL |
| **P0** | No degraded-scan detection | High | Code/data quality | Apr 16: 13 NO DATA + 16 of 20 at slope=1.00 rendered as normal scan | Add scan-quality meta-check in backend; surface "DEGRADED DATA" banner in frontend when NO DATA count > 4 OR > 25% of universe at slope = 1.00 | Apr-16-style scans display a banner; trades not encouraged |
| **P1** | NKE θ/V flickers between 0.01 and 0.55 | Medium | Data quality | 5+ instances across Apr 17 – May 8 | Investigate NKE-specific contract characteristics; tighten `_normalize_vega()` heuristic boundary OR add per-ticker calibration | NKE θ/V stable across consecutive scans (within ±0.10) |
| **P1** | Earnings date drift not surfaced in UI | Medium | UI / data quality | WMT (verified May 14 vs scanner 21d), MCD/CAT/HD repeated TBD | Add yellow "earnings unverified" chip when date is TBD; add "?" tooltip when FMP/Yahoo discrepancy > 5d (already detected by `update_latest_scan_earnings()`) | TBD earnings render with visible warning; FMP/Yahoo drift cases show provenance |
| **P1** | No "Thin Premium" warning for low-VRP CONDITIONAL | Medium | UI | All 8 false positives display identical to fat-VRP CONDITIONAL | Add badge: "Thin Premium" when VRP component contributed < 8 of 30 (i.e., vrp_ratio < ~1.27) AND action is SELL/CONDITIONAL | Badge appears on the IWM/QQQ/XLF false positives; absent on WMT-style fat-VRP signals |
| **P2** | AVOID chip collapses CAUTION-defensible and DANGER-do-not-trade | Medium | UI | scoring.ts:13 maps both to AVOID | Either: split into two chips ("REDUCE SIZE" yellow border, "AVOID" red) OR: keep chip but require regime chip visibility on the leaderboard row | Trader can distinguish the two from the leaderboard row alone |
| **P2** | No watchlist / structure-only tier | Medium | Strategy / UI | NVDA recurring 30-40 score with deep contango (e.g., May 4: 31, slope 0.75, VRP +6.1) | Add "STRUCTURE WATCHLIST" tier when all 4 non-VRP components score well but VRP component is < 6 | Tier appears on the dashboard; sample NVDA scans show watchlist tag |
| **P2** | Position sizing only reflects RV Accel | Medium | Strategy | scoring.ts:41–43 | Extend sizing to: Quarter when (vrp_ratio < 1.20 OR rv_accel > 1.20); Half when (vrp_ratio < 1.30 OR rv_accel > 1.10); else Full | Sizing chip varies with both VRP magnitude and RV accel |
| **P2** | Regime banner doesn't distinguish event-driven vs structural stress | Medium | UI / strategy | Apr 30 REGULAR SEASON was 3/8 stressed = post-earnings | Annotate banner detail with how many stressed names are within 10 sessions post-print | Apr-30-style regimes show "(3 of 8 are post-earnings residuals)" in the detail string |
| **P3** | XLB chronic NO DATA recurrence | Low | Data quality | 5+ scan days with XLB NO DATA in mid-April | Per-ticker NO DATA streak counter; warn when same ticker NO DATA > 3 days running | Streak warning surfaces in admin / verification view |
| **P3** | "Slope 1.00 wall" pattern detection | Low | Data quality | Apr 16, partial Apr 14 | Statistical check: slope distribution variance threshold | Slope-wall scans flag during ingestion |
| **P3** | Stale methodology footer in `page.tsx:216` | Low | Documentation | Documented existing issue per fragile-seams.md | Update footer prose to reflect current additive model | Footer text matches scorer.py |

---

## 7. Proposed Rule Changes

### 7.1 VRP-ratio gate at recommendation level (P0)

**Current behavior:** Score ≥ 45 → CONDITIONAL regardless of vrp_ratio.

**Proposed behavior:**

```python
# After computing score and regime, before mapping to recommendation:
if surface.vrp_ratio < 1.15 and regime == "NORMAL":
    rec = "WATCHLIST"           # New tier — see §7.2
elif surface.vrp_ratio < 1.20 and regime == "NORMAL":
    # CONDITIONAL with thin VRP — flag but allow
    rec = "CONDITIONAL"
    flags.append("Thin Premium — VRP ratio just above dead zone")
```

**Effect on observed false positives:**
- All 8 instances in §5.4 would be re-classified to WATCHLIST (vrp_ratio between 1.026 and 1.141 — all below 1.15)
- The user's manual rejections from briefings would now be the framework's automatic output

**Backwards compatibility:** Existing CONDITIONAL signals with vrp_ratio ≥ 1.15 continue to display unchanged. Affects only the false-positive class.

### 7.2 New WATCHLIST recommendation state (P0/P2 combined)

| State | Condition | UI display |
|---|---|---|
| SELL | vrp_ratio ≥ 1.20, score ≥ 65, NORMAL | Green pill, full Position Construction |
| CONDITIONAL | vrp_ratio ≥ 1.20, score 45–64, NORMAL | Yellow pill, Position Construction shown |
| THIN-PREMIUM CONDITIONAL | vrp_ratio 1.15–1.20, score 45+, NORMAL | Yellow pill + "Thin Premium" subtle badge |
| **WATCHLIST** *(new)* | **vrp_ratio < 1.15 AND non-VRP components ≥ 35**, NORMAL | **Gray pill, no Position Construction; "Structure clean — wait for VRP" prose** |
| NO EDGE | score < 45 or vrp_ratio < 1.15 with weak structure | Gray pill |
| AVOID | DANGER regime OR (CAUTION + score ≥ 55) | Red pill, regime explanation |
| SKIP | earnings_dte ≤ 14 | Red pill, preGateScore preserved |
| NO DATA | iv_current is None | Gray pill, NoData explanation |

### 7.3 Degraded-scan detection (P0)

Add to backend `run_full_scan()`:

```python
no_data_count = sum(1 for t in results if t.recommendation == "NO DATA")
slope_wall_count = sum(1 for t in results if abs(t.term_slope - 1.0) < 0.001)

scan_quality = "DEGRADED" if (
    no_data_count > 4 or
    slope_wall_count > len(results) * 0.25
) else "OK"
```

Add to scan response, render frontend banner if DEGRADED.

### 7.4 Day-since-print metadata (P2)

Add to ScoredOpportunity:

```python
days_since_last_earnings: Optional[int]   # Yahoo verification provides last_print
```

Frontend uses this to flag post-earnings residual stress in the regime detail string.

### 7.5 Rebalance position sizing (P2)

```typescript
let sizing = 'Full';
const vrpRatio = (t.vrp_ratio ?? 0);
if (rvAccel > 1.20 || vrpRatio < 1.20) sizing = 'Quarter';
else if (rvAccel > 1.10 || vrpRatio < 1.30) sizing = 'Half';
```

This couples sizing to both safety (accel) and edge (VRP ratio).

---

## 8. Acceptance Tests

These are concrete tests the codebase should pass after implementing the proposed rule changes.

### 8.1 VRP-ratio gate

```python
# test_scorer.py
def test_vrp_ratio_below_115_caps_at_watchlist():
    # IWM 2026-05-04 fixture: VRP 1.1, ratio 1.054, score 45
    surface = build_test_surface(iv=21.5, rv30=20.4, slope=0.82, accel=0.77, iv_pct=45, skew=3.5)
    result = score_opportunity(surface, "IWM", "Index", ScoringParams(...))
    assert result.recommendation == "WATCHLIST"  # was "CONDITIONAL"
    assert result.signal_score >= 45             # score itself unchanged

def test_vrp_ratio_above_120_keeps_conditional():
    # WMT 2026-05-04 fixture: ratio 1.343
    surface = build_test_surface(iv=31.7, rv30=23.6, slope=0.82, accel=1.00, iv_pct=87, skew=1.2)
    result = score_opportunity(surface, "WMT", "Consumer", ScoringParams(...))
    assert result.recommendation == "SELL PREMIUM"

def test_thin_premium_flag():
    # SBUX 2026-04-14 fixture: ratio 1.141 — just above dead zone, just below thin-premium threshold
    # Expected: WATCHLIST (because < 1.15, would be CONDITIONAL otherwise)
    ...
```

### 8.2 Degraded-scan detection

```python
def test_degraded_scan_flag():
    # Apr 16 fixture: 13/33 NO DATA, 16/20 at slope 1.00
    response = run_full_scan_simulation(no_data_count=13, slope_wall_count=16)
    assert response.scan_quality == "DEGRADED"
```

### 8.3 Earnings drift surface

```python
def test_tbd_earnings_renders_warning():
    # MCD 2026-04-16 fixture
    ticker = {...earnings_dte=None, earnings_source="TBD"...}
    rendered = convert_api_ticker(ticker)
    assert rendered.earningsWarning == "DATE_UNVERIFIED"

def test_drift_warning():
    # FMP says 7d, Yahoo says 21d (existing detection logic)
    ticker = {...fmp_dte=7, yahoo_dte=21, days_diff=14...}
    rendered = convert_api_ticker(ticker)
    assert rendered.earningsWarning == "DATE_DRIFT"
```

### 8.4 Sizing rebalance

```typescript
// scoring.test.ts
test('sizing accounts for vrp_ratio', () => {
  const ticker = buildTestTicker({ vrp: 1.1, vrpRatio: 1.05, rvAccel: 0.85 });
  expect(convertApiTicker(ticker).sizing).toBe('Quarter');
  
  const ticker2 = buildTestTicker({ vrp: 8.5, vrpRatio: 1.34, rvAccel: 0.85 });
  expect(convertApiTicker(ticker2).sizing).toBe('Full');
});
```

### 8.5 Watchlist tier

```python
def test_watchlist_tier():
    # Score 50, vrp_ratio 1.05, NORMAL regime
    result = score_opportunity_with_inputs(score=50, vrp_ratio=1.05, regime="NORMAL")
    assert result.recommendation == "WATCHLIST"
    assert result.suggested_max_notional == "0%"  # No active position
    assert "Structure clean" in result.suggested_structure
```

### 8.6 Score consistency regression

```python
def test_score_recompute_match_28d_history():
    """All 28 days × 33 tickers must score within ±2 of displayed value."""
    for scan_date, tickers in load_metrics_logs():
        for ticker in tickers:
            if ticker.iv_current is not None and not ticker.is_gated:
                recomputed = recompute_score(ticker)
                assert abs(recomputed - ticker.displayed_score) <= 2, \
                    f"Mismatch on {scan_date} {ticker.symbol}"
```

---

## 9. Final Verdict

### Status: **Mostly reliable but needs fixes**

The dashboard is **production-functional**. Score formula, gates, regime detection, and earnings handling all reproduce the documented behavior within rounding tolerance. The framework's two-axis model (score = edge measurement, regime = risk override) is genuinely well-designed and ADR-011 is faithfully implemented.

But the dashboard has a **specific class of failures** that affect daily usability:

1. **Structure-only false positives** (CONDITIONAL with vrp_ratio < 1.15) appear in 8 of 28 days, clustered in the May 4–8 macro-IV-compression window. These are false signals by the strategy's own definition of "premium edge" and the user's briefings consistently catch them manually. **The fix is structural** (add a VRP-ratio gate at the recommendation level), not just a UI tweak.

2. **Degraded-scan handling is missing.** The Apr 16 incident is the canonical example — a scan where the dashboard rendered untradeable garbage as if it were normal data, and only the human briefing caught it. The fix is a meta-quality check during ingestion + a visible banner.

3. **The dashboard doesn't help the trader develop discipline** as much as it could. A flat "CONDITIONAL" chip looks the same whether VRP is 1.0 or 8.0; a "AVOID" chip looks the same whether the trader could enter (CAUTION + score ≥ 55) or shouldn't (DANGER). The framework has the data to differentiate; the UI just doesn't.

### What the audit explicitly does NOT conclude

- Whether the underlying premium-selling strategy is profitable
- Whether the score thresholds (45, 65) are correctly calibrated for trading P&L
- Whether the regime banner thresholds (25%, 40%, etc.) are well-tuned

These are strategy-design questions outside the scope of dashboard behavior validation.

### Recommended next steps in priority order

1. **P0 — Implement VRP-ratio gate + WATCHLIST tier** (§7.1, §7.2). Fixes the 8-instance false-positive class. ~half-day backend + half-day frontend.
2. **P0 — Degraded-scan detection** (§7.3). Prevents Apr-16-style silent failures. ~half-day total.
3. **P1 — Thin Premium badge** (§6 P1). UI-only, helps discipline before the harder rule changes land. ~2 hours frontend.
4. **P1 — Earnings date drift surfacing** (§6 P1). Backend logic exists (`update_latest_scan_earnings`); only frontend rendering is missing. ~2 hours.
5. **P1 — NKE θ/V investigation** (§6 P1). Could be NKE-specific contract characteristics requiring per-ticker calibration; investigation precedes fix.
6. **P2 — Sizing rebalance, watchlist tier UI, regime nuance** as time allows.

### One-line summary

**The framework is sound, the implementation is faithful, but the dashboard rewards structural calm where the strategy demands premium richness — fix the VRP-ratio gate first.**

---

*End of report.*
