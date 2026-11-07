# v2 Metrics Log — v1-vs-v2 Divergence (deterministic)

Deterministic v2-shadow record for the Theta Harvest v1→v2 build. Sister log to `metrics-logs.md` (v1 Naked Puts) — this is its v2 analog. One entry per trading day, descending order (newest first).

Authoritative data lives in the `shadow_diff` + `daily_iv` tables; this file is the human-readable mirror for day-over-day pattern recognition and the eventual Phase-B calibration. It is **advisory only** — Phase A of the v2 arc, changing no live decision.

---

## Update Protocol

**Trigger:** Written automatically by `automation/` alongside `metrics-logs.md` (best-effort — a failure here never blocks the v1 history).

**Steps:**
1. Insert new entry **at the top** of the log (immediately below the `---` after this protocol section)
2. Use heading format: `## YYYY-MM-DD (Day of week)`
3. Capture two blocks per entry: **Shadow summary** line, then the divergence **table**

**Required fields:**
- **Shadow summary** — `Checked N / A agree / S V2_STRICTER / L V2_LOOSER / M state_mismatch / K nodata | index-gating v1 X% vs v2 Y% | oscillation v1 a vs v2 b | warm C% | day-flips v1 f/N vs v2 g/N`
  (the `day-flips` segment is present from 2026-07-15 onward and is omitted when the prior day's rows are unavailable)
- **Table** — Ticker / v1 Action / v1 Regime / Earnings / v2 Eligible / v2 Gate / Divergence / sigma_fwd / FVRP / z / 1M/3M / accel_dn

**Column order:**
```
| Ticker | v1 Action | v1 Regime | Earnings | v2 Eligible | v2 Gate | Divergence | sigma_fwd | FVRP | z | 1M/3M | accel_dn |
```

**Divergence values:** `AGREE` | `V2_STRICTER` (v1 trades, v2 gates) | `V2_LOOSER` (v2 allows, v1 gates) | `STATE_MISMATCH` | `NODATA_SKEW`. Rows are sorted decision-changing-first (V2_STRICTER, then V2_LOOSER), then by ticker.

**Reading the fields correctly:**
- `oscillation` = mean *cumulative* gate-state transitions per ticker over the rolling 10-date summary window — **not** a daily flip rate. It rises mechanically while the window is still filling; once 10 dates accumulate, `Checked` caps at 330 and all summary counts become rolling. Use `day-flips` (true day-over-day churn) for stability claims.
- `Earnings` = days to next earnings from the same day's live scan (`ETF` = exempt, `TBD` = unknown/today). A non-ETF at ≤ 14d is earnings-gated in the **live v1 UI** (score 0, no trade) — the `v1 Action` shown is the backend's *pre*-earnings-gate view.
- **⚑ Series break — from 2026-07-22 (Phase B B0.4) the shadow applies G1 on both sides.** A dated non-ETF ≤ 14d (`g1_earnings_gate_days`) is now gated for **both** v1 (matching the live UI) and v2, so such rows read `AGREE` (both ineligible) rather than a false `V2_STRICTER` — the earnings common-mode is no longer a divergence. v2 additionally **hardens** the gate (D4 fallback): a single name with **no verified date** is v2-ineligible (`earnings_unverified`) while live-v1 only warns → a *genuine* `V2_STRICTER`. **Entries dated before 2026-07-22 omit G1 on both sides** — eligibility divergences on names inside the earnings window in those older entries are shadow artifacts, not real live divergences; the eligible-set and STRICTER/AGREE counts are not directly comparable across this break.

**Format changes:** 2026-07-15 — added the `Earnings` column and the `day-flips` summary segment. Entries before that date have neither. **2026-07-22 (Phase B B0.4)** — G1 earnings gate now applied in shadow eligibility (both sides; v2 hardened with the D4 unverified→gated fallback); see the ⚑ series-break note above. **2026-09-03 (Signal-Quality WS2a)** — the summary line may end with a `capture{N} n=… mean … / v2-veto-neg … / v2-clear-neg … / σfwd-vs-rv30 MAE … vs …` segment: forward realized capture (spec E3, `IV30² − RV²` over the next 21 sessions, variance pts ×1e4) aggregated over the last N **resolved** dates — it lags 21 sessions and is a read on past vetoes, never today's edge; `v2-veto-neg` = share of v2-ineligible ticker-days that were loss days (↑ = veto right), `v2-clear-neg` = share of v2-eligible ticker-days that were loss days (↓ = clearing right). Omitted when nothing is resolved.

---

> **IMPORTANT:** Entries are in **descending order** (newest first). New entries go immediately below this line.

---

## 2026-11-06 (Friday)

**Shadow summary:** Checked 330 / 165 agree / 22 V2_STRICTER / 2 V2_LOOSER / 136 state_mismatch / 5 nodata | index-gating v1 85% vs v2 99% | oscillation v1 2.67 vs v2 0.79 | warm 100% | day-flips v1 17/33 vs v2 3/33 | capture60 n=1957 mean +99 / v2-veto-neg 24% / v2-clear-neg 17% / σfwd-vs-rv30 MAE 0.29 vs 0.27 | veto-disagree 2%

| Ticker | v1 Action | v1 Regime | Earnings | v2 Eligible | v2 Gate | Divergence | sigma_fwd | FVRP | z | 1M/3M | accel_dn |
|--------|-----------|-----------|----------|-------------|---------|------------|-----------|------|------|-------|----------|
| AAPL | AVOID | DANGER | 90d | No | CAUTION | STATE_MISMATCH | 0.367 | 0.78 | -0.95 | 1.007 | 1.204 |
| AMZN | AVOID | DANGER | 90d | No | CAUTION | STATE_MISMATCH | 0.487 | 0.78 | -1.06 | 0.989 | 1.160 |
| CAT | AVOID | DANGER | 83d | No | DANGER | AGREE | 0.503 | 0.94 | -0.78 | 1.068 | 1.482 |
| EEM | AVOID | DANGER | ETF | No | DANGER | AGREE | 0.285 | 1.10 | +0.09 | 1.079 | 1.641 |
| GLD | NO EDGE | CAUTION | ETF | No | CAUTION | AGREE | 0.243 | 0.96 | -1.26 | 1.032 | 1.020 |
| GOOG | AVOID | DANGER | 89d | No | CAUTION | STATE_MISMATCH | 0.450 | 0.80 | -1.44 | 0.982 | 1.364 |
| GS | AVOID | DANGER | 76d | No | DANGER | AGREE | 0.431 | 0.89 | -0.85 | 1.104 | 1.636 |
| HD | AVOID | DANGER | 11d | No | DANGER | AGREE | 0.341 | 1.07 | +0.41 | 1.239 | 1.077 |
| HOOD | AVOID | DANGER | 95d | No | CAUTION | STATE_MISMATCH | 0.900 | 0.80 | -0.95 | 1.073 | 1.483 |
| IWM | AVOID | DANGER | ETF | No | CAUTION | STATE_MISMATCH | 0.269 | 0.91 | -0.24 | 1.093 | 1.760 |
| JNJ | AVOID | DANGER | 75d | No | CAUTION | STATE_MISMATCH | 0.287 | 0.97 | -0.70 | 1.088 | 0.923 |
| JPM | AVOID | DANGER | 69d | No | NORMAL | STATE_MISMATCH | 0.350 | 0.78 | -1.28 | 1.002 | 1.610 |
| KO | NO EDGE | CAUTION | 95d | No | CAUTION | AGREE | 0.245 | 0.87 | -0.49 | 0.987 | 1.008 |
| MCD | NO EDGE | CAUTION | TBD | No | DANGER | STATE_MISMATCH | 0.262 | 0.88 | -0.90 | 1.067 | 0.681 |
| META | AVOID | DANGER | 82d | No | NORMAL | STATE_MISMATCH | 0.524 | 0.85 | -0.15 | 1.012 | 1.110 |
| MSFT | NO EDGE | CAUTION | 82d | No | CAUTION | AGREE | 0.373 | 0.85 | -0.77 | 0.972 | 1.501 |
| NFLX | AVOID | DANGER | 74d | No | NORMAL | STATE_MISMATCH | 0.458 | 0.78 | -0.58 | 0.968 | 0.810 |
| NKE | NO EDGE | CAUTION | 41d | No | NORMAL | STATE_MISMATCH | 0.419 | 1.07 | -0.08 | 1.010 | 1.047 |
| NVDA | AVOID | DANGER | 12d | No | DANGER | AGREE | 0.528 | 1.17 | +2.46 | 1.273 | 1.737 |
| PLTR | AVOID | DANGER | 87d | No | CAUTION | STATE_MISMATCH | 0.815 | 0.71 | -0.99 | 1.008 | 1.633 |
| QQQ | AVOID | DANGER | ETF | No | DANGER | AGREE | 0.276 | 1.19 | +2.09 | 1.186 | 1.772 |
| SBUX | NO EDGE | CAUTION | 82d | No | DANGER | STATE_MISMATCH | 0.353 | 0.88 | -0.67 | 1.033 | 1.363 |
| SPY | AVOID | DANGER | ETF | No | DANGER | AGREE | 0.205 | 1.07 | +1.33 | 1.112 | 1.878 |
| TLT | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.139 | 0.93 | +0.45 | 0.976 | 0.823 |
| TSLA | AVOID | DANGER | 82d | No | DANGER | AGREE | 0.678 | 0.79 | -0.58 | 1.080 | 1.764 |
| UBER | NO EDGE | CAUTION | 89d | No | DANGER | STATE_MISMATCH | 0.512 | 0.72 | -0.98 | 1.048 | 0.834 |
| WMT | NO EDGE | CAUTION | 13d | No | DANGER | STATE_MISMATCH | 0.300 | 1.28 | +1.10 | 1.220 | 0.889 |
| XLB | NO DATA | NORMAL | ETF | No | CAUTION | NODATA_SKEW | — | — | — | — | — |
| XLE | NO EDGE | CAUTION | ETF | No | DANGER | STATE_MISMATCH | 0.353 | 0.84 | -0.47 | 1.042 | 1.702 |
| XLF | AVOID | DANGER | ETF | No | DANGER | AGREE | 0.255 | 0.87 | +0.02 | 1.112 | 1.612 |
| XLI | NO EDGE | CAUTION | ETF | No | DANGER | STATE_MISMATCH | 0.250 | 1.13 | +0.75 | 1.025 | 1.701 |
| XLV | NO EDGE | CAUTION | ETF | No | DANGER | STATE_MISMATCH | 0.232 | 1.04 | +0.28 | 1.101 | 1.486 |
| XOM | AVOID | DANGER | 84d | No | DANGER | AGREE | 0.371 | 0.87 | -0.57 | 1.044 | 1.626 |

---

## 2026-11-05 (Thursday)

**Shadow summary:** Checked 330 / 164 agree / 26 V2_STRICTER / 2 V2_LOOSER / 133 state_mismatch / 5 nodata | index-gating v1 84% vs v2 99% | oscillation v1 2.27 vs v2 0.73 | warm 100% | day-flips v1 12/33 vs v2 6/33 | capture60 n=1958 mean +101 / v2-veto-neg 24% / v2-clear-neg 15% / σfwd-vs-rv30 MAE 0.29 vs 0.27 | veto-disagree 3%

| Ticker | v1 Action | v1 Regime | Earnings | v2 Eligible | v2 Gate | Divergence | sigma_fwd | FVRP | z | 1M/3M | accel_dn |
|--------|-----------|-----------|----------|-------------|---------|------------|-----------|------|------|-------|----------|
| IWM | CONDITIONAL | NORMAL | ETF | No | CAUTION | V2_STRICTER | 0.236 | 0.90 | -0.38 | 1.015 | 0.903 |
| XLV | CONDITIONAL | NORMAL | ETF | No | DANGER | V2_STRICTER | 0.213 | 1.16 | +1.08 | 1.381 | 0.604 |
| AAPL | NO EDGE | CAUTION | 91d | No | CAUTION | AGREE | 0.369 | 0.65 | -2.37 | 0.926 | 1.152 |
| AMZN | NO EDGE | CAUTION | 91d | No | CAUTION | AGREE | 0.460 | 0.70 | -1.65 | 0.909 | 1.110 |
| CAT | NO EDGE | CAUTION | 84d | No | DANGER | STATE_MISMATCH | 0.472 | 0.89 | -1.17 | 0.999 | 1.411 |
| EEM | AVOID | DANGER | ETF | No | DANGER | AGREE | 0.249 | 1.28 | +0.88 | 1.167 | 0.999 |
| GLD | NO EDGE | CAUTION | ETF | No | CAUTION | AGREE | 0.245 | 0.88 | -2.03 | 0.971 | 1.095 |
| GOOG | NO EDGE | CAUTION | 90d | No | CAUTION | AGREE | 0.428 | 0.71 | -2.22 | 0.897 | 1.444 |
| GS | NO EDGE | CAUTION | 77d | No | DANGER | STATE_MISMATCH | 0.376 | 0.90 | -0.78 | 1.017 | 0.997 |
| HD | AVOID | DANGER | 12d | No | DANGER | AGREE | 0.338 | 1.02 | +0.09 | 1.205 | 0.989 |
| HOOD | NO EDGE | CAUTION | 96d | No | CAUTION | AGREE | 0.754 | 0.85 | -0.33 | 1.013 | 1.056 |
| JNJ | NO EDGE | CAUTION | 76d | No | CAUTION | AGREE | 0.282 | 0.92 | -1.17 | 1.017 | 0.853 |
| JPM | NO EDGE | CAUTION | 70d | No | NORMAL | STATE_MISMATCH | 0.304 | 0.78 | -1.35 | 0.971 | 0.936 |
| KO | NO EDGE | CAUTION | 96d | No | CAUTION | AGREE | 0.243 | 0.82 | -1.01 | 0.926 | 1.082 |
| MCD | NO EDGE | CAUTION | TBD | No | DANGER | STATE_MISMATCH | 0.263 | 0.85 | -1.15 | 1.055 | 0.623 |
| META | NO EDGE | NORMAL | 83d | No | NORMAL | AGREE | 0.457 | 0.85 | -0.14 | 0.951 | 0.899 |
| MSFT | NO EDGE | CAUTION | 83d | No | CAUTION | AGREE | 0.370 | 0.71 | -1.72 | 0.868 | 1.181 |
| NFLX | NO EDGE | NORMAL | 75d | No | NORMAL | AGREE | 0.436 | 0.78 | -0.61 | 0.972 | 0.816 |
| NKE | NO EDGE | CAUTION | 42d | No | NORMAL | STATE_MISMATCH | 0.404 | 1.05 | -0.12 | 0.999 | 0.809 |
| NVDA | AVOID | DANGER | 13d | No | DANGER | AGREE | 0.483 | 1.07 | +1.68 | 1.184 | 1.259 |
| PLTR | NO EDGE | NORMAL | 88d | No | CAUTION | STATE_MISMATCH | 0.789 | 0.65 | -1.63 | 0.943 | 1.226 |
| QQQ | NO EDGE | CAUTION | ETF | No | DANGER | STATE_MISMATCH | 0.241 | 1.15 | +1.80 | 1.162 | 1.275 |
| SBUX | NO EDGE | CAUTION | 83d | No | DANGER | STATE_MISMATCH | 0.319 | 0.78 | -1.20 | 0.811 | 0.748 |
| SPY | REDUCE SIZE | CAUTION | ETF | No | CAUTION | AGREE | 0.183 | 1.01 | +0.86 | 1.068 | 1.222 |
| TLT | NO EDGE | CAUTION | ETF | No | CAUTION | AGREE | 0.139 | 0.87 | -0.09 | 0.961 | 0.884 |
| TSLA | NO EDGE | CAUTION | 83d | No | CAUTION | AGREE | 0.604 | 0.79 | -0.57 | 1.058 | 0.998 |
| UBER | NO EDGE | CAUTION | 90d | No | DANGER | STATE_MISMATCH | 0.508 | 0.65 | -1.61 | 1.008 | 0.743 |
| WMT | NO EDGE | CAUTION | 14d | No | DANGER | STATE_MISMATCH | 0.293 | 1.24 | +0.89 | 1.221 | 0.854 |
| XLB | NO DATA | NORMAL | ETF | No | CAUTION | NODATA_SKEW | — | — | — | — | — |
| XLE | NO EDGE | CAUTION | ETF | No | DANGER | STATE_MISMATCH | 0.345 | 0.86 | -0.22 | 1.075 | 1.745 |
| XLF | AVOID | DANGER | ETF | No | DANGER | AGREE | 0.231 | 0.74 | -1.31 | 1.108 | 0.844 |
| XLI | REDUCE SIZE | CAUTION | ETF | No | DANGER | STATE_MISMATCH | 0.217 | 1.21 | +1.21 | 1.237 | 1.054 |
| XOM | AVOID | DANGER | 85d | No | DANGER | AGREE | 0.350 | 0.92 | -0.09 | 1.061 | 1.689 |

---

## 2026-11-04 (Wednesday)

**Shadow summary:** Checked 330 / 158 agree / 28 V2_STRICTER / 2 V2_LOOSER / 137 state_mismatch / 5 nodata | index-gating v1 83% vs v2 99% | oscillation v1 2.15 vs v2 0.61 | warm 100% | day-flips v1 6/33 vs v2 3/33 | capture60 n=1958 mean +96 / v2-veto-neg 24% / v2-clear-neg 14% / σfwd-vs-rv30 MAE 0.29 vs 0.27 | veto-disagree 3%

| Ticker | v1 Action | v1 Regime | Earnings | v2 Eligible | v2 Gate | Divergence | sigma_fwd | FVRP | z | 1M/3M | accel_dn |
|--------|-----------|-----------|----------|-------------|---------|------------|-----------|------|------|-------|----------|
| NKE | NO EDGE | CAUTION | 43d | Yes | NORMAL | V2_LOOSER | 0.365 | 1.18 | +0.38 | 1.005 | 0.869 |
| AAPL | NO EDGE | CAUTION | 92d | No | DANGER | STATE_MISMATCH | 0.364 | 0.65 | -2.46 | 0.924 | 1.238 |
| AMZN | NO EDGE | CAUTION | 92d | No | DANGER | STATE_MISMATCH | 0.417 | 0.74 | -1.36 | 0.880 | 1.192 |
| CAT | NO EDGE | CAUTION | 85d | No | DANGER | STATE_MISMATCH | 0.476 | 0.93 | -0.89 | 1.038 | 1.360 |
| EEM | AVOID | DANGER | ETF | No | DANGER | AGREE | 0.253 | 1.11 | +0.14 | 1.057 | 1.073 |
| GLD | NO EDGE | CAUTION | ETF | No | CAUTION | AGREE | 0.216 | 1.03 | -0.69 | 0.987 | 1.177 |
| GOOG | NO EDGE | CAUTION | 0d | No | CAUTION | AGREE | 0.439 | 0.70 | -2.34 | 0.903 | 1.551 |
| GS | AVOID | DANGER | 78d | No | DANGER | AGREE | 0.336 | 1.02 | +0.46 | 1.051 | 1.071 |
| HD | AVOID | DANGER | 13d | No | DANGER | AGREE | 0.297 | 1.28 | +1.78 | 1.315 | 1.062 |
| HOOD | AVOID | DANGER | 0d | No | CAUTION | STATE_MISMATCH | 0.752 | 0.86 | -0.18 | 1.011 | 1.134 |
| IWM | NO EDGE | CAUTION | ETF | No | CAUTION | AGREE | 0.213 | 0.95 | +0.23 | 1.008 | 0.970 |
| JNJ | NO EDGE | CAUTION | 77d | No | CAUTION | AGREE | 0.256 | 1.03 | -0.19 | 1.022 | 0.917 |
| JPM | AVOID | DANGER | 71d | No | NORMAL | STATE_MISMATCH | 0.264 | 0.90 | -0.01 | 0.964 | 1.005 |
| KO | NO EDGE | CAUTION | 97d | No | CAUTION | AGREE | 0.229 | 0.89 | -0.31 | 0.969 | 1.162 |
| MCD | AVOID | DANGER | TBD | No | DANGER | AGREE | 0.232 | 1.17 | +1.31 | 1.150 | 0.669 |
| META | NO EDGE | NORMAL | 84d | No | CAUTION | STATE_MISMATCH | 0.410 | 0.96 | +0.48 | 0.953 | 0.965 |
| MSFT | NO EDGE | CAUTION | 84d | No | DANGER | STATE_MISMATCH | 0.326 | 0.82 | -0.95 | 0.909 | 1.268 |
| NFLX | NO EDGE | CAUTION | 76d | No | NORMAL | STATE_MISMATCH | 0.401 | 0.84 | -0.28 | 0.950 | 0.876 |
| NVDA | AVOID | DANGER | 14d | No | DANGER | AGREE | 0.486 | 0.99 | +1.09 | 1.160 | 1.159 |
| PLTR | AVOID | DANGER | 89d | No | DANGER | AGREE | 0.751 | 0.71 | -1.02 | 0.982 | 1.273 |
| QQQ | AVOID | DANGER | ETF | No | DANGER | AGREE | 0.245 | 1.11 | +1.41 | 1.107 | 1.369 |
| SBUX | NO EDGE | CAUTION | 84d | No | DANGER | STATE_MISMATCH | 0.314 | 1.02 | -0.00 | 1.081 | 0.804 |
| SPY | NO EDGE | CAUTION | ETF | No | CAUTION | AGREE | 0.165 | 0.93 | +0.19 | 0.953 | 1.312 |
| TLT | NO EDGE | NORMAL | ETF | No | CAUTION | STATE_MISMATCH | 0.135 | 1.01 | +1.17 | 1.009 | 0.950 |
| TSLA | NO EDGE | CAUTION | 84d | No | CAUTION | AGREE | 0.513 | 0.89 | +0.64 | 1.007 | 0.657 |
| UBER | AVOID | DANGER | 0d | No | DANGER | AGREE | 0.403 | 1.03 | +1.25 | 1.093 | 0.798 |
| WMT | NO EDGE | CAUTION | 15d | No | DANGER | STATE_MISMATCH | 0.258 | 1.34 | +1.36 | 1.197 | 0.917 |
| XLB | NO DATA | NORMAL | ETF | No | CAUTION | NODATA_SKEW | — | — | — | — | — |
| XLE | AVOID | DANGER | ETF | No | DANGER | AGREE | 0.307 | 0.98 | +0.81 | 1.030 | 1.527 |
| XLF | NO EDGE | CAUTION | ETF | No | CAUTION | AGREE | 0.193 | 0.92 | +0.57 | 1.085 | 0.907 |
| XLI | REDUCE SIZE | CAUTION | ETF | No | DANGER | STATE_MISMATCH | 0.209 | 1.18 | +1.03 | 1.318 | 0.964 |
| XLV | NO EDGE | NORMAL | ETF | No | DANGER | STATE_MISMATCH | 0.188 | 1.03 | +0.22 | 0.958 | 0.648 |
| XOM | AVOID | DANGER | 86d | No | DANGER | AGREE | 0.320 | 1.01 | +0.75 | 1.023 | 1.486 |

---

## 2026-11-03 (Tuesday)

**Shadow summary:** Checked 330 / 151 agree / 34 V2_STRICTER / 1 V2_LOOSER / 139 state_mismatch / 5 nodata | index-gating v1 80% vs v2 99% | oscillation v1 2.27 vs v2 0.58 | warm 100% | day-flips v1 15/33 vs v2 5/33 | capture60 n=1957 mean +90 / v2-veto-neg 24% / v2-clear-neg 14% / σfwd-vs-rv30 MAE 0.29 vs 0.27 | veto-disagree 3%

| Ticker | v1 Action | v1 Regime | Earnings | v2 Eligible | v2 Gate | Divergence | sigma_fwd | FVRP | z | 1M/3M | accel_dn |
|--------|-----------|-----------|----------|-------------|---------|------------|-----------|------|------|-------|----------|
| XLB | CONDITIONAL | NORMAL | ETF | No | CAUTION | V2_STRICTER | 0.202 | 1.04 | -0.48 | 1.000 | 0.434 |
| NKE | NO EDGE | CAUTION | 44d | Yes | NORMAL | V2_LOOSER | 0.351 | 1.17 | +0.34 | 0.960 | 0.728 |
| AAPL | AVOID | DANGER | 93d | No | DANGER | AGREE | 0.320 | 1.00 | +1.02 | 1.114 | 1.098 |
| AMZN | NO EDGE | CAUTION | 93d | No | DANGER | STATE_MISMATCH | 0.443 | 0.76 | -1.23 | 1.025 | 1.280 |
| CAT | AVOID | DANGER | 86d | No | DANGER | AGREE | 0.517 | 0.85 | -1.48 | 1.096 | 1.461 |
| EEM | AVOID | DANGER | ETF | No | DANGER | AGREE | 0.275 | 1.08 | +0.01 | 1.091 | 1.152 |
| GLD | NO EDGE | CAUTION | ETF | No | CAUTION | AGREE | 0.235 | 0.97 | -1.21 | 1.015 | 1.249 |
| GOOG | NO EDGE | CAUTION | 1d | No | CAUTION | AGREE | 0.471 | 0.68 | -2.55 | 1.017 | 1.666 |
| GS | AVOID | DANGER | 79d | No | CAUTION | STATE_MISMATCH | 0.363 | 0.96 | -0.08 | 1.074 | 1.147 |
| HD | AVOID | DANGER | 14d | No | DANGER | AGREE | 0.290 | 1.22 | +1.43 | 1.142 | 0.680 |
| HOOD | AVOID | DANGER | 1d | No | CAUTION | STATE_MISMATCH | 0.812 | 0.78 | -1.15 | 1.029 | 1.218 |
| IWM | NO EDGE | CAUTION | ETF | No | CAUTION | AGREE | 0.226 | 0.94 | +0.10 | 1.028 | 1.042 |
| JNJ | AVOID | DANGER | 78d | No | CAUTION | STATE_MISMATCH | 0.259 | 1.03 | -0.21 | 1.043 | 0.805 |
| JPM | AVOID | DANGER | 72d | No | NORMAL | STATE_MISMATCH | 0.275 | 0.87 | -0.37 | 0.960 | 1.021 |
| KO | NO EDGE | CAUTION | TBD | No | CAUTION | AGREE | 0.231 | 0.92 | -0.04 | 1.029 | 1.126 |
| MCD | AVOID | DANGER | 1d | No | DANGER | AGREE | 0.233 | 1.11 | +0.94 | 1.113 | 0.538 |
| META | NO EDGE | NORMAL | 85d | No | CAUTION | STATE_MISMATCH | 0.426 | 0.95 | +0.44 | 1.036 | 1.037 |
| MSFT | NO EDGE | CAUTION | 85d | No | DANGER | STATE_MISMATCH | 0.342 | 0.87 | -0.64 | 1.040 | 1.362 |
| NFLX | NO EDGE | CAUTION | 77d | No | NORMAL | STATE_MISMATCH | 0.400 | 0.85 | -0.21 | 0.942 | 0.941 |
| NVDA | REDUCE SIZE | CAUTION | 15d | No | DANGER | STATE_MISMATCH | 0.480 | 1.00 | +1.11 | 1.107 | 1.245 |
| PLTR | AVOID | DANGER | 90d | No | DANGER | AGREE | 0.656 | 1.10 | +1.90 | 1.222 | 1.343 |
| QQQ | AVOID | DANGER | ETF | No | DANGER | AGREE | 0.264 | 1.02 | +0.56 | 1.087 | 1.471 |
| SBUX | NO EDGE | CAUTION | 85d | No | DANGER | STATE_MISMATCH | 0.328 | 0.95 | -0.32 | 1.028 | 0.863 |
| SPY | REDUCE SIZE | CAUTION | ETF | No | CAUTION | AGREE | 0.178 | 0.95 | +0.37 | 1.010 | 1.410 |
| TLT | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.139 | 1.00 | +1.09 | 1.028 | 0.732 |
| TSLA | NO EDGE | CAUTION | 85d | No | NORMAL | STATE_MISMATCH | 0.547 | 0.83 | -0.14 | 1.029 | 0.610 |
| UBER | AVOID | DANGER | 0d | No | DANGER | AGREE | 0.429 | 1.06 | +1.45 | 1.192 | 0.856 |
| WMT | REDUCE SIZE | CAUTION | 16d | No | DANGER | STATE_MISMATCH | 0.257 | 1.37 | +1.49 | 1.176 | 0.431 |
| XLE | AVOID | DANGER | ETF | No | DANGER | AGREE | 0.317 | 1.09 | +1.73 | 1.145 | 1.623 |
| XLF | AVOID | DANGER | ETF | No | CAUTION | STATE_MISMATCH | 0.201 | 0.90 | +0.33 | 1.042 | 0.853 |
| XLI | REDUCE SIZE | CAUTION | ETF | No | DANGER | STATE_MISMATCH | 0.217 | 1.24 | +1.34 | 1.153 | 1.036 |
| XLV | AVOID | DANGER | ETF | No | DANGER | AGREE | 0.197 | 1.13 | +0.87 | 1.065 | 0.653 |
| XOM | AVOID | DANGER | 87d | No | DANGER | AGREE | 0.331 | 1.04 | +1.01 | 1.084 | 1.562 |

---

## 2026-11-02 (Monday)

**Shadow summary:** Checked 330 / 145 agree / 41 V2_STRICTER / 0 V2_LOOSER / 139 state_mismatch / 5 nodata | index-gating v1 77% vs v2 99% | oscillation v1 1.94 vs v2 0.45 | warm 100% | day-flips v1 10/33 vs v2 1/33 | capture60 n=1957 mean +83 / v2-veto-neg 24% / v2-clear-neg 13% / σfwd-vs-rv30 MAE 0.29 vs 0.26 | veto-disagree 3%

| Ticker | v1 Action | v1 Regime | Earnings | v2 Eligible | v2 Gate | Divergence | sigma_fwd | FVRP | z | 1M/3M | accel_dn |
|--------|-----------|-----------|----------|-------------|---------|------------|-----------|------|------|-------|----------|
| MSFT | CONDITIONAL | NORMAL | 86d | No | DANGER | V2_STRICTER | 0.321 | 0.88 | -0.60 | 1.002 | 1.020 |
| NKE | CONDITIONAL | NORMAL | 45d | No | NORMAL | V2_STRICTER | 0.361 | 1.11 | +0.10 | 0.953 | 0.782 |
| XLB | CONDITIONAL | NORMAL | ETF | No | NORMAL | V2_STRICTER | 0.182 | 1.09 | -0.29 | 1.000 | 0.466 |
| XLE | CONDITIONAL | NORMAL | ETF | No | DANGER | V2_STRICTER | 0.285 | 0.99 | +0.90 | 1.113 | 0.954 |
| AAPL | AVOID | DANGER | 0d | No | DANGER | AGREE | 0.326 | 0.89 | +0.12 | 1.079 | 0.852 |
| AMZN | NO EDGE | CAUTION | 94d | No | DANGER | STATE_MISMATCH | 0.451 | 0.69 | -1.72 | 0.973 | 1.375 |
| CAT | AVOID | DANGER | 87d | No | DANGER | AGREE | 0.552 | 0.74 | -2.50 | 1.054 | 1.560 |
| EEM | AVOID | DANGER | ETF | No | DANGER | AGREE | 0.274 | 0.99 | -0.40 | 1.012 | 1.238 |
| GLD | NO EDGE | NORMAL | ETF | No | CAUTION | STATE_MISMATCH | 0.234 | 0.97 | -1.19 | 1.004 | 1.341 |
| GOOG | NO EDGE | CAUTION | 2d | No | CAUTION | AGREE | 0.504 | 0.62 | -3.25 | 1.005 | 1.790 |
| GS | NO EDGE | CAUTION | 80d | No | CAUTION | AGREE | 0.370 | 0.87 | -1.07 | 1.023 | 1.232 |
| HD | NO EDGE | NORMAL | 15d | No | DANGER | STATE_MISMATCH | 0.286 | 1.19 | +1.21 | 1.160 | 0.731 |
| HOOD | NO EDGE | CAUTION | 2d | No | CAUTION | AGREE | 0.855 | 0.70 | -2.26 | 1.020 | 1.298 |
| IWM | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.224 | 0.90 | -0.37 | 1.011 | 1.119 |
| JNJ | NO EDGE | NORMAL | 79d | No | CAUTION | STATE_MISMATCH | 0.267 | 0.96 | -0.77 | 1.004 | 0.793 |
| JPM | NO EDGE | NORMAL | 73d | No | NORMAL | AGREE | 0.279 | 0.82 | -0.86 | 0.940 | 1.097 |
| KO | NO EDGE | CAUTION | TBD | No | CAUTION | AGREE | 0.240 | 0.81 | -1.07 | 0.986 | 1.209 |
| MCD | AVOID | DANGER | 2d | No | DANGER | AGREE | 0.241 | 1.05 | +0.45 | 1.080 | 0.578 |
| META | NO EDGE | NORMAL | 86d | No | CAUTION | STATE_MISMATCH | 0.439 | 0.89 | +0.08 | 1.022 | 1.084 |
| NFLX | NO EDGE | CAUTION | 78d | No | CAUTION | AGREE | 0.410 | 0.84 | -0.24 | 0.959 | 1.011 |
| NVDA | NO EDGE | CAUTION | 16d | No | DANGER | STATE_MISMATCH | 0.474 | 0.94 | +0.62 | 1.086 | 1.311 |
| PLTR | AVOID | DANGER | 0d | No | DANGER | AGREE | 0.669 | 1.06 | +1.66 | 1.213 | 1.359 |
| QQQ | NO EDGE | CAUTION | ETF | No | CAUTION | AGREE | 0.270 | 0.96 | -0.10 | 1.068 | 1.534 |
| SBUX | NO EDGE | CAUTION | 86d | No | DANGER | STATE_MISMATCH | 0.330 | 0.83 | -0.93 | 0.908 | 0.927 |
| SPY | REDUCE SIZE | CAUTION | ETF | No | NORMAL | STATE_MISMATCH | 0.176 | 0.93 | +0.16 | 0.983 | 1.488 |
| TLT | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.139 | 0.93 | +0.46 | 0.974 | 0.787 |
| TSLA | NO EDGE | CAUTION | 86d | No | NORMAL | STATE_MISMATCH | 0.541 | 0.77 | -0.91 | 0.994 | 0.655 |
| UBER | AVOID | DANGER | 1d | No | DANGER | AGREE | 0.396 | 1.12 | +1.82 | 1.166 | 0.920 |
| WMT | AVOID | DANGER | 17d | No | DANGER | AGREE | 0.263 | 1.28 | +1.10 | 1.156 | 0.463 |
| XLF | NO EDGE | CAUTION | ETF | No | CAUTION | AGREE | 0.196 | 0.87 | +0.10 | 1.031 | 0.916 |
| XLI | REDUCE SIZE | CAUTION | ETF | No | DANGER | STATE_MISMATCH | 0.214 | 1.13 | +0.79 | 1.035 | 1.112 |
| XLV | NO EDGE | CAUTION | ETF | No | DANGER | STATE_MISMATCH | 0.208 | 1.08 | +0.51 | 1.071 | 0.693 |
| XOM | NO EDGE | NORMAL | 88d | No | DANGER | STATE_MISMATCH | 0.309 | 0.94 | +0.14 | 0.995 | 0.943 |

---

## 2026-10-30 (Friday)

**Shadow summary:** Checked 330 / 134 agree / 48 V2_STRICTER / 0 V2_LOOSER / 143 state_mismatch / 5 nodata | index-gating v1 75% vs v2 99% | oscillation v1 1.85 vs v2 0.52 | warm 100% | day-flips v1 10/33 vs v2 2/33 | capture60 n=1956 mean +76 / v2-veto-neg 25% / v2-clear-neg 14% / σfwd-vs-rv30 MAE 0.29 vs 0.26 | veto-disagree 3%

| Ticker | v1 Action | v1 Regime | Earnings | v2 Eligible | v2 Gate | Divergence | sigma_fwd | FVRP | z | 1M/3M | accel_dn |
|--------|-----------|-----------|----------|-------------|---------|------------|-----------|------|------|-------|----------|
| EEM | CONDITIONAL | NORMAL | ETF | No | DANGER | V2_STRICTER | 0.236 | 1.33 | +1.08 | 1.186 | 0.987 |
| AAPL | AVOID | DANGER | 3d | No | DANGER | AGREE | 0.262 | 1.01 | +1.15 | 1.059 | 0.692 |
| AMZN | AVOID | DANGER | 97d | No | DANGER | AGREE | 0.381 | 1.20 | +1.11 | 1.215 | 1.444 |
| CAT | NO EDGE | CAUTION | 90d | No | DANGER | STATE_MISMATCH | 0.559 | 0.70 | -3.03 | 1.054 | 1.620 |
| GLD | NO EDGE | NORMAL | ETF | No | CAUTION | STATE_MISMATCH | 0.197 | 1.10 | -0.21 | 1.015 | 0.910 |
| GOOG | NO EDGE | CAUTION | 5d | No | DANGER | STATE_MISMATCH | 0.523 | 0.57 | -3.93 | 0.995 | 1.919 |
| GS | NO EDGE | CAUTION | 83d | No | CAUTION | AGREE | 0.309 | 0.99 | +0.20 | 1.019 | 0.663 |
| HD | NO EDGE | NORMAL | 18d | No | DANGER | STATE_MISMATCH | 0.276 | 1.23 | +1.45 | 1.142 | 0.785 |
| HOOD | NO EDGE | NORMAL | 5d | No | CAUTION | STATE_MISMATCH | 0.723 | 0.77 | -1.34 | 0.990 | 1.003 |
| IWM | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.186 | 1.05 | +1.32 | 0.995 | 0.721 |
| JNJ | NO EDGE | NORMAL | 82d | No | CAUTION | STATE_MISMATCH | 0.246 | 0.97 | -0.68 | 0.991 | 0.812 |
| JPM | NO EDGE | NORMAL | 76d | No | NORMAL | AGREE | 0.258 | 0.87 | -0.34 | 0.938 | 0.747 |
| KO | NO EDGE | CAUTION | TBD | No | CAUTION | AGREE | 0.222 | 0.78 | -1.35 | 0.938 | 1.299 |
| MCD | AVOID | DANGER | 5d | No | DANGER | AGREE | 0.226 | 1.08 | +0.70 | 1.073 | 0.621 |
| META | NO EDGE | NORMAL | 89d | No | CAUTION | STATE_MISMATCH | 0.413 | 0.91 | +0.15 | 0.987 | 1.129 |
| MSFT | NO EDGE | NORMAL | 89d | No | DANGER | STATE_MISMATCH | 0.313 | 0.82 | -1.02 | 0.959 | 0.856 |
| NFLX | NO EDGE | NORMAL | 81d | No | CAUTION | STATE_MISMATCH | 0.393 | 0.83 | -0.28 | 0.918 | 1.086 |
| NKE | NO EDGE | NORMAL | 48d | No | NORMAL | AGREE | 0.348 | 1.13 | +0.18 | 1.018 | 0.840 |
| NVDA | NO EDGE | CAUTION | 19d | No | DANGER | STATE_MISMATCH | 0.385 | 1.08 | +1.79 | 1.056 | 0.993 |
| PLTR | AVOID | DANGER | 3d | No | DANGER | AGREE | 0.583 | 1.13 | +2.06 | 1.192 | 0.890 |
| QQQ | NO EDGE | CAUTION | ETF | No | CAUTION | AGREE | 0.214 | 1.11 | +1.41 | 1.048 | 1.188 |
| SBUX | AVOID | DANGER | 89d | No | DANGER | AGREE | 0.301 | 1.14 | +0.46 | 1.133 | 0.599 |
| SPY | NO EDGE | CAUTION | ETF | No | NORMAL | STATE_MISMATCH | 0.140 | 1.00 | +0.80 | 0.927 | 1.017 |
| TLT | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.132 | 0.94 | +0.54 | 0.963 | 0.846 |
| TSLA | NO EDGE | CAUTION | 89d | No | NORMAL | STATE_MISMATCH | 0.468 | 0.80 | -0.54 | 0.950 | 0.666 |
| UBER | AVOID | DANGER | 4d | No | DANGER | AGREE | 0.392 | 1.10 | +1.69 | 1.139 | 0.964 |
| WMT | NO EDGE | CAUTION | 20d | No | DANGER | STATE_MISMATCH | 0.248 | 1.29 | +1.13 | 1.141 | 0.498 |
| XLB | CONDITIONAL | NORMAL | ETF | Yes | NORMAL | AGREE | 0.175 | 1.24 | +0.26 | 0.967 | 0.500 |
| XLE | NO EDGE | NORMAL | ETF | No | DANGER | STATE_MISMATCH | 0.273 | 1.03 | +1.26 | 0.962 | 1.024 |
| XLF | NO EDGE | NORMAL | ETF | No | CAUTION | STATE_MISMATCH | 0.187 | 0.87 | +0.07 | 0.999 | 0.817 |
| XLI | NO EDGE | NORMAL | ETF | No | DANGER | STATE_MISMATCH | 0.188 | 1.02 | +0.16 | 1.021 | 0.785 |
| XLV | NO EDGE | CAUTION | ETF | No | DANGER | STATE_MISMATCH | 0.197 | 1.11 | +0.77 | 1.151 | 0.745 |
| XOM | AVOID | DANGER | 0d | No | DANGER | AGREE | 0.286 | 1.03 | +0.91 | 1.036 | 1.013 |

---

## 2026-10-29 (Thursday)

**Shadow summary:** Checked 330 / 125 agree / 53 V2_STRICTER / 0 V2_LOOSER / 145 state_mismatch / 7 nodata | index-gating v1 74% vs v2 100% | oscillation v1 1.70 vs v2 0.48 | warm 100% | day-flips v1 7/33 vs v2 1/33 | capture60 n=1956 mean +68 / v2-veto-neg 25% / v2-clear-neg 24% / σfwd-vs-rv30 MAE 0.29 vs 0.26 | veto-disagree 3%

| Ticker | v1 Action | v1 Regime | Earnings | v2 Eligible | v2 Gate | Divergence | sigma_fwd | FVRP | z | 1M/3M | accel_dn |
|--------|-----------|-----------|----------|-------------|---------|------------|-----------|------|------|-------|----------|
| CAT | CONDITIONAL | NORMAL | TBD | No | DANGER | V2_STRICTER | 0.394 | 1.23 | +1.17 | 1.175 | 1.006 |
| SPY | CONDITIONAL | NORMAL | ETF | No | CAUTION | V2_STRICTER | 0.139 | 1.00 | +0.79 | 0.915 | 1.043 |
| WMT | CONDITIONAL | NORMAL | 21d | No | DANGER | V2_STRICTER | 0.229 | 1.35 | +1.38 | 1.136 | 0.535 |
| XLI | CONDITIONAL | NORMAL | ETF | No | DANGER | V2_STRICTER | 0.190 | 1.29 | +1.65 | 1.000 | 0.844 |
| AAPL | AVOID | DANGER | 0d | No | DANGER | AGREE | 0.246 | 1.03 | +1.28 | 1.040 | 0.743 |
| AMZN | AVOID | DANGER | 0d | No | DANGER | AGREE | 0.310 | 1.43 | +2.01 | 1.169 | 1.128 |
| EEM | NO EDGE | NORMAL | ETF | No | DANGER | STATE_MISMATCH | 0.227 | 1.06 | -0.04 | 1.040 | 0.955 |
| GLD | NO EDGE | NORMAL | ETF | No | CAUTION | STATE_MISMATCH | 0.181 | 1.14 | +0.10 | 0.980 | 0.840 |
| GOOG | REDUCE SIZE | CAUTION | 6d | No | DANGER | STATE_MISMATCH | 0.284 | 1.36 | +2.14 | — | 1.003 |
| GS | NO EDGE | CAUTION | 84d | No | CAUTION | AGREE | 0.316 | 0.94 | -0.33 | 0.990 | 0.712 |
| HD | NO EDGE | CAUTION | 19d | No | DANGER | STATE_MISMATCH | 0.250 | 1.34 | +2.15 | 1.137 | 0.843 |
| HOOD | NO EDGE | CAUTION | 6d | No | DANGER | STATE_MISMATCH | 0.763 | 0.73 | -1.89 | 1.000 | 1.078 |
| IWM | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.184 | 0.96 | +0.40 | 0.946 | 0.775 |
| JNJ | NO EDGE | NORMAL | 83d | No | CAUTION | STATE_MISMATCH | 0.247 | 1.00 | -0.41 | 1.026 | 0.872 |
| JPM | NO EDGE | NORMAL | 77d | No | NORMAL | AGREE | 0.247 | 0.82 | -0.85 | 0.865 | 0.802 |
| KO | NO EDGE | CAUTION | TBD | No | CAUTION | AGREE | 0.227 | 0.80 | -1.18 | 0.972 | 1.395 |
| MCD | AVOID | DANGER | 6d | No | DANGER | AGREE | 0.211 | 1.13 | +1.00 | 1.054 | 0.667 |
| META | NO EDGE | NORMAL | 90d | No | CAUTION | STATE_MISMATCH | 0.397 | 0.96 | +0.46 | 1.010 | 1.213 |
| MSFT | AVOID | DANGER | 90d | No | DANGER | AGREE | 0.265 | 1.21 | +1.08 | 1.121 | 0.916 |
| NFLX | NO EDGE | CAUTION | 82d | No | CAUTION | AGREE | 0.408 | 0.76 | -0.72 | 0.892 | 1.166 |
| NKE | NO EDGE | CAUTION | 49d | No | NORMAL | STATE_MISMATCH | 0.343 | 1.12 | +0.16 | 0.934 | 0.902 |
| NVDA | NO EDGE | CAUTION | 20d | No | DANGER | STATE_MISMATCH | 0.402 | 1.01 | +1.22 | 1.059 | 1.047 |
| PLTR | AVOID | DANGER | 4d | No | DANGER | AGREE | 0.564 | 1.09 | +1.84 | 1.158 | 0.955 |
| QQQ | NO EDGE | CAUTION | ETF | No | CAUTION | AGREE | 0.198 | 1.09 | +1.24 | 0.994 | 1.139 |
| SBUX | AVOID | DANGER | 0d | No | DANGER | AGREE | 0.271 | 1.32 | +1.10 | 1.227 | 0.644 |
| TLT | NO EDGE | CAUTION | ETF | No | NORMAL | STATE_MISMATCH | 0.128 | 0.96 | +0.79 | 0.962 | 0.908 |
| TSLA | NO EDGE | CAUTION | 90d | No | NORMAL | STATE_MISMATCH | 0.502 | 0.74 | -1.26 | 0.949 | 0.714 |
| UBER | AVOID | DANGER | 5d | No | DANGER | AGREE | 0.377 | 1.15 | +1.94 | 1.178 | 1.035 |
| XLB | NO DATA | NORMAL | ETF | No | NORMAL | NODATA_SKEW | — | — | — | — | — |
| XLE | AVOID | DANGER | ETF | No | DANGER | AGREE | 0.267 | 1.09 | +1.78 | 1.041 | 1.100 |
| XLF | NO EDGE | NORMAL | ETF | No | CAUTION | STATE_MISMATCH | 0.169 | 0.95 | +0.78 | 0.996 | 0.878 |
| XLV | NO EDGE | CAUTION | ETF | No | DANGER | STATE_MISMATCH | 0.187 | 1.10 | +0.72 | 1.014 | 0.800 |
| XOM | AVOID | DANGER | 1d | No | DANGER | AGREE | 0.283 | 1.02 | +0.84 | 1.008 | 1.088 |

---

## 2026-10-28 (Wednesday)

**Shadow summary:** Checked 330 / 116 agree / 60 V2_STRICTER / 0 V2_LOOSER / 147 state_mismatch / 7 nodata | index-gating v1 71% vs v2 100% | oscillation v1 1.61 vs v2 0.64 | warm 100% | day-flips v1 4/33 vs v2 2/33 | capture60 n=1956 mean +56 / v2-veto-neg 26% / v2-clear-neg 31% / σfwd-vs-rv30 MAE 0.29 vs 0.26 | veto-disagree 3%

| Ticker | v1 Action | v1 Regime | Earnings | v2 Eligible | v2 Gate | Divergence | sigma_fwd | FVRP | z | 1M/3M | accel_dn |
|--------|-----------|-----------|----------|-------------|---------|------------|-----------|------|------|-------|----------|
| WMT | CONDITIONAL | NORMAL | 22d | No | DANGER | V2_STRICTER | 0.237 | 1.26 | +0.99 | 1.098 | 0.544 |
| XLE | CONDITIONAL | NORMAL | ETF | No | DANGER | V2_STRICTER | 0.284 | 1.15 | +2.27 | 1.158 | 1.182 |
| XLI | CONDITIONAL | NORMAL | ETF | No | DANGER | V2_STRICTER | 0.190 | 1.16 | +0.94 | 1.111 | 0.906 |
| AAPL | AVOID | DANGER | 1d | No | DANGER | AGREE | 0.263 | 1.02 | +1.20 | 1.069 | 0.651 |
| AMZN | AVOID | DANGER | 1d | No | DANGER | AGREE | 0.330 | 1.31 | +1.55 | 1.174 | 1.211 |
| CAT | AVOID | DANGER | 1d | No | DANGER | AGREE | 0.379 | 1.20 | +0.95 | 1.152 | 1.081 |
| EEM | NO EDGE | NORMAL | ETF | No | DANGER | STATE_MISMATCH | 0.228 | 1.08 | +0.02 | 0.991 | 1.026 |
| GLD | NO EDGE | NORMAL | ETF | No | CAUTION | STATE_MISMATCH | 0.180 | 1.12 | -0.08 | 0.972 | 0.902 |
| GOOG | AVOID | DANGER | 7d | No | DANGER | AGREE | 0.292 | 1.29 | +1.81 | 1.151 | 1.077 |
| GS | NO EDGE | CAUTION | 85d | No | CAUTION | AGREE | 0.331 | 0.91 | -0.61 | 0.994 | 0.765 |
| HD | NO EDGE | CAUTION | 20d | No | DANGER | STATE_MISMATCH | 0.252 | 1.33 | +2.12 | 1.130 | 0.898 |
| HOOD | AVOID | DANGER | 7d | No | DANGER | AGREE | 0.687 | 0.97 | +1.01 | 1.080 | 1.057 |
| IWM | NO EDGE | CAUTION | ETF | No | NORMAL | STATE_MISMATCH | 0.193 | 0.96 | +0.36 | 0.955 | 0.832 |
| JNJ | NO EDGE | NORMAL | 84d | No | CAUTION | STATE_MISMATCH | 0.236 | 1.01 | -0.29 | 0.984 | 0.937 |
| JPM | NO EDGE | NORMAL | 78d | No | NORMAL | AGREE | 0.247 | 0.84 | -0.62 | 0.891 | 0.862 |
| KO | NO EDGE | CAUTION | TBD | No | DANGER | STATE_MISMATCH | 0.239 | 0.80 | -1.16 | 1.010 | 1.499 |
| MCD | AVOID | DANGER | 7d | No | DANGER | AGREE | 0.212 | 1.13 | +1.03 | 1.027 | 0.717 |
| META | NO EDGE | NORMAL | 0d | No | CAUTION | STATE_MISMATCH | 0.413 | 0.93 | +0.28 | 1.013 | 1.286 |
| MSFT | AVOID | DANGER | 0d | No | DANGER | AGREE | 0.268 | 1.20 | +1.01 | 1.095 | 0.984 |
| NFLX | NO EDGE | CAUTION | 83d | No | CAUTION | AGREE | 0.429 | 0.71 | -1.01 | 0.885 | 1.242 |
| NKE | NO EDGE | CAUTION | 50d | No | NORMAL | STATE_MISMATCH | 0.342 | 1.14 | +0.25 | 0.949 | 0.898 |
| NVDA | NO EDGE | CAUTION | 21d | No | DANGER | STATE_MISMATCH | 0.413 | 0.99 | +1.03 | 1.061 | 1.084 |
| PLTR | AVOID | DANGER | 5d | No | DANGER | AGREE | 0.572 | 1.08 | +1.82 | 1.161 | 1.007 |
| QQQ | NO EDGE | CAUTION | ETF | No | CAUTION | AGREE | 0.208 | 1.02 | +0.57 | 0.982 | 1.223 |
| SBUX | AVOID | DANGER | 0d | No | DANGER | AGREE | 0.274 | 1.32 | +1.08 | 1.212 | 0.691 |
| SPY | NO EDGE | CAUTION | ETF | No | CAUTION | AGREE | 0.146 | 0.95 | +0.36 | 0.913 | 1.120 |
| TLT | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.120 | 1.03 | +1.37 | 0.961 | 0.647 |
| TSLA | NO EDGE | CAUTION | 0d | No | NORMAL | STATE_MISMATCH | 0.520 | 0.73 | -1.40 | 0.955 | 0.740 |
| UBER | AVOID | DANGER | 6d | No | DANGER | AGREE | 0.381 | 1.12 | +1.77 | 1.140 | 1.092 |
| XLB | NO DATA | NORMAL | ETF | No | NORMAL | NODATA_SKEW | — | — | — | — | — |
| XLF | NO EDGE | NORMAL | ETF | No | CAUTION | STATE_MISMATCH | 0.178 | 0.92 | +0.57 | 0.986 | 0.943 |
| XLV | NO EDGE | CAUTION | ETF | No | DANGER | STATE_MISMATCH | 0.172 | 1.10 | +0.66 | 0.871 | 0.859 |
| XOM | AVOID | DANGER | 2d | No | DANGER | AGREE | 0.290 | 1.03 | +0.94 | 1.037 | 1.169 |

---

## 2026-10-27 (Tuesday)

**Shadow summary:** Checked 330 / 104 agree / 70 V2_STRICTER / 0 V2_LOOSER / 150 state_mismatch / 6 nodata | index-gating v1 67% vs v2 100% | oscillation v1 1.67 vs v2 0.64 | warm 100% | day-flips v1 7/33 vs v2 3/33 | capture60 n=1956 mean +49 / v2-veto-neg 26% / v2-clear-neg 36% / σfwd-vs-rv30 MAE 0.29 vs 0.26 | veto-disagree 3%

| Ticker | v1 Action | v1 Regime | Earnings | v2 Eligible | v2 Gate | Divergence | sigma_fwd | FVRP | z | 1M/3M | accel_dn |
|--------|-----------|-----------|----------|-------------|---------|------------|-----------|------|------|-------|----------|
| WMT | CONDITIONAL | NORMAL | 23d | No | DANGER | V2_STRICTER | 0.250 | 1.26 | +0.99 | 1.147 | 0.492 |
| XLB | CONDITIONAL | NORMAL | ETF | No | NORMAL | V2_STRICTER | 0.187 | 1.12 | -0.15 | 1.079 | 0.620 |
| XLI | CONDITIONAL | NORMAL | ETF | No | NORMAL | V2_STRICTER | 0.199 | 1.10 | +0.61 | 1.056 | 0.973 |
| AAPL | AVOID | DANGER | 2d | No | DANGER | AGREE | 0.279 | 0.97 | +0.79 | 1.064 | 0.699 |
| AMZN | AVOID | DANGER | 2d | No | DANGER | AGREE | 0.330 | 1.34 | +1.67 | 1.180 | 1.301 |
| CAT | AVOID | DANGER | 2d | No | DANGER | AGREE | 0.382 | 1.19 | +0.94 | 1.118 | 1.161 |
| EEM | NO EDGE | CAUTION | ETF | No | DANGER | STATE_MISMATCH | 0.240 | 1.09 | +0.07 | 1.052 | 1.102 |
| GLD | NO EDGE | NORMAL | ETF | No | CAUTION | STATE_MISMATCH | 0.192 | 1.09 | -0.30 | 0.994 | 0.969 |
| GOOG | AVOID | DANGER | 1d | No | DANGER | AGREE | 0.293 | 1.27 | +1.68 | 1.106 | 1.157 |
| GS | NO EDGE | CAUTION | 86d | No | CAUTION | AGREE | 0.331 | 0.94 | -0.35 | 0.999 | 0.822 |
| HD | NO EDGE | CAUTION | 21d | No | DANGER | STATE_MISMATCH | 0.268 | 1.22 | +1.47 | 1.108 | 0.958 |
| HOOD | AVOID | DANGER | 8d | No | DANGER | AGREE | 0.692 | 0.97 | +1.03 | 1.098 | 1.135 |
| IWM | NO EDGE | CAUTION | ETF | No | CAUTION | AGREE | 0.195 | 0.98 | +0.55 | 0.973 | 0.894 |
| JNJ | NO EDGE | CAUTION | 85d | No | CAUTION | AGREE | 0.254 | 0.98 | -0.60 | 1.006 | 1.007 |
| JPM | NO EDGE | NORMAL | 79d | No | NORMAL | AGREE | 0.252 | 0.86 | -0.43 | 0.941 | 0.926 |
| KO | AVOID | DANGER | 0d | No | DANGER | AGREE | 0.201 | 1.06 | +1.11 | 1.020 | 1.458 |
| MCD | AVOID | DANGER | 8d | No | DANGER | AGREE | 0.223 | 1.11 | +0.87 | 1.064 | 0.732 |
| META | NO EDGE | NORMAL | 1d | No | CAUTION | STATE_MISMATCH | 0.447 | 0.87 | -0.08 | 1.010 | 1.354 |
| MSFT | AVOID | DANGER | 1d | No | DANGER | AGREE | 0.283 | 1.17 | +0.88 | 1.096 | 1.052 |
| NFLX | NO EDGE | CAUTION | 84d | No | CAUTION | AGREE | 0.457 | 0.69 | -1.18 | 0.928 | 1.269 |
| NKE | NO EDGE | CAUTION | 51d | No | NORMAL | STATE_MISMATCH | 0.363 | 1.09 | +0.05 | 0.958 | 0.916 |
| NVDA | NO EDGE | CAUTION | 22d | No | DANGER | STATE_MISMATCH | 0.426 | 0.96 | +0.76 | 1.073 | 1.165 |
| PLTR | AVOID | DANGER | 6d | No | DANGER | AGREE | 0.601 | 1.06 | +1.66 | 1.157 | 1.081 |
| QQQ | NO EDGE | CAUTION | ETF | No | CAUTION | AGREE | 0.217 | 1.01 | +0.51 | 0.999 | 1.314 |
| SBUX | AVOID | DANGER | 1d | No | DANGER | AGREE | 0.282 | 1.24 | +0.78 | 1.228 | 0.743 |
| SPY | NO EDGE | CAUTION | ETF | No | CAUTION | AGREE | 0.151 | 0.93 | +0.22 | 0.931 | 1.203 |
| TLT | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.130 | 1.00 | +1.12 | 0.967 | 0.693 |
| TSLA | NO EDGE | CAUTION | 1d | No | NORMAL | STATE_MISMATCH | 0.544 | 0.71 | -1.68 | 0.962 | 0.795 |
| UBER | AVOID | DANGER | 7d | No | DANGER | AGREE | 0.402 | 1.13 | +1.82 | 1.196 | 1.164 |
| XLE | AVOID | DANGER | ETF | No | DANGER | AGREE | 0.282 | 0.97 | +0.79 | 1.094 | 0.715 |
| XLF | NO EDGE | NORMAL | ETF | No | CAUTION | STATE_MISMATCH | 0.179 | 0.92 | +0.56 | 1.007 | 0.998 |
| XLV | NO EDGE | CAUTION | ETF | No | DANGER | STATE_MISMATCH | 0.179 | 1.11 | +0.77 | 1.052 | 0.922 |
| XOM | AVOID | DANGER | 3d | No | DANGER | AGREE | 0.275 | 1.08 | +1.40 | 1.028 | 0.460 |

---

## 2026-10-26 (Monday)

**Shadow summary:** Checked 330 / 90 agree / 81 V2_STRICTER / 0 V2_LOOSER / 153 state_mismatch / 6 nodata | index-gating v1 63% vs v2 100% | oscillation v1 1.58 vs v2 0.58 | warm 100% | day-flips v1 4/33 vs v2 1/33 | capture60 n=1956 mean +43 / v2-veto-neg 26% / v2-clear-neg 36% / σfwd-vs-rv30 MAE 0.29 vs 0.26 | veto-disagree 4%

| Ticker | v1 Action | v1 Regime | Earnings | v2 Eligible | v2 Gate | Divergence | sigma_fwd | FVRP | z | 1M/3M | accel_dn |
|--------|-----------|-----------|----------|-------------|---------|------------|-----------|------|------|-------|----------|
| SPY | CONDITIONAL | NORMAL | ETF | No | CAUTION | V2_STRICTER | 0.157 | 0.94 | +0.29 | 0.955 | 1.292 |
| WMT | CONDITIONAL | NORMAL | 24d | No | DANGER | V2_STRICTER | 0.262 | 1.19 | +0.68 | 1.145 | 0.528 |
| XLB | CONDITIONAL | NORMAL | ETF | No | NORMAL | V2_STRICTER | 0.202 | 1.04 | -0.49 | 1.000 | 0.666 |
| XLI | CONDITIONAL | NORMAL | ETF | No | NORMAL | V2_STRICTER | 0.212 | 1.00 | +0.05 | 0.934 | 1.046 |
| AAPL | CONDITIONAL | NORMAL | 3d | No | DANGER | STATE_MISMATCH | 0.265 | 1.02 | +1.21 | 1.054 | 0.523 |
| AMZN | AVOID | DANGER | 3d | No | DANGER | AGREE | 0.348 | 1.24 | +1.25 | 1.161 | 1.398 |
| CAT | AVOID | DANGER | 3d | No | DANGER | AGREE | 0.405 | 1.14 | +0.61 | 1.113 | 1.247 |
| EEM | NO EDGE | CAUTION | ETF | No | DANGER | STATE_MISMATCH | 0.244 | 1.09 | +0.09 | 1.093 | 1.180 |
| GLD | NO EDGE | NORMAL | ETF | No | CAUTION | STATE_MISMATCH | 0.201 | 1.07 | -0.40 | 1.008 | 1.041 |
| GOOG | AVOID | DANGER | 2d | No | DANGER | AGREE | 0.313 | 1.18 | +1.12 | 1.098 | 1.212 |
| GS | NO EDGE | NORMAL | 87d | No | DANGER | STATE_MISMATCH | 0.341 | 0.92 | -0.52 | 1.002 | 0.883 |
| HD | NO EDGE | CAUTION | 22d | No | DANGER | STATE_MISMATCH | 0.280 | 1.20 | +1.34 | 1.141 | 1.028 |
| HOOD | AVOID | DANGER | 1d | No | DANGER | AGREE | 0.736 | 0.92 | +0.46 | 1.085 | 1.177 |
| IWM | NO EDGE | CAUTION | ETF | No | CAUTION | AGREE | 0.203 | 0.99 | +0.75 | 0.982 | 0.961 |
| JNJ | NO EDGE | CAUTION | 86d | No | CAUTION | AGREE | 0.246 | 1.04 | -0.08 | 1.074 | 1.081 |
| JPM | NO EDGE | NORMAL | 80d | No | NORMAL | AGREE | 0.261 | 0.86 | -0.43 | 0.937 | 0.995 |
| KO | AVOID | DANGER | 1d | No | DANGER | AGREE | 0.213 | 1.00 | +0.60 | 1.014 | 1.566 |
| MCD | NO EDGE | NORMAL | 9d | No | DANGER | STATE_MISMATCH | 0.230 | 1.04 | +0.42 | 1.042 | 0.787 |
| META | NO EDGE | NORMAL | 2d | No | CAUTION | STATE_MISMATCH | 0.467 | 0.80 | -0.53 | 0.987 | 1.424 |
| MSFT | AVOID | DANGER | 2d | No | DANGER | AGREE | 0.278 | 1.15 | +0.78 | 1.080 | 1.130 |
| NFLX | NO EDGE | CAUTION | 85d | No | CAUTION | AGREE | 0.465 | 0.66 | -1.41 | 0.911 | 1.235 |
| NKE | NO EDGE | CAUTION | 52d | No | NORMAL | STATE_MISMATCH | 0.366 | 1.06 | -0.08 | 0.932 | 0.984 |
| NVDA | NO EDGE | CAUTION | 23d | No | DANGER | STATE_MISMATCH | 0.440 | 0.95 | +0.69 | 1.092 | 1.251 |
| PLTR | NO EDGE | CAUTION | 7d | No | DANGER | STATE_MISMATCH | 0.611 | 1.03 | +1.46 | 1.139 | 1.161 |
| QQQ | NO EDGE | CAUTION | ETF | No | CAUTION | AGREE | 0.226 | 1.05 | +0.87 | 1.023 | 1.411 |
| SBUX | AVOID | DANGER | 2d | No | DANGER | AGREE | 0.285 | 1.24 | +0.78 | 1.177 | 0.798 |
| TLT | NO EDGE | NORMAL | ETF | No | CAUTION | STATE_MISMATCH | 0.136 | 1.00 | +1.08 | 0.974 | 0.744 |
| TSLA | NO EDGE | CAUTION | 2d | No | DANGER | STATE_MISMATCH | 0.532 | 0.71 | -1.73 | 0.948 | 0.854 |
| UBER | NO EDGE | CAUTION | 8d | No | DANGER | STATE_MISMATCH | 0.420 | 1.04 | +1.32 | 1.100 | 1.232 |
| XLE | NO EDGE | CAUTION | ETF | No | DANGER | STATE_MISMATCH | 0.296 | 1.03 | +1.35 | 1.103 | 0.768 |
| XLF | NO EDGE | NORMAL | ETF | No | CAUTION | STATE_MISMATCH | 0.191 | 0.90 | +0.34 | 1.027 | 1.072 |
| XLV | NO EDGE | CAUTION | ETF | No | DANGER | STATE_MISMATCH | 0.181 | 0.99 | -0.08 | 0.839 | 0.991 |
| XOM | AVOID | DANGER | 4d | No | DANGER | AGREE | 0.291 | 1.04 | +1.07 | 1.040 | 0.494 |

---

## 2026-10-23 (Friday)

**Shadow summary:** Checked 330 / 84 agree / 88 V2_STRICTER / 0 V2_LOOSER / 152 state_mismatch / 6 nodata | index-gating v1 61% vs v2 100% | oscillation v1 1.55 vs v2 0.55 | warm 100% | day-flips v1 8/33 vs v2 2/33 | capture60 n=1957 mean +36 / v2-veto-neg 26% / v2-clear-neg 36% / σfwd-vs-rv30 MAE 0.29 vs 0.26 | veto-disagree 5%

| Ticker | v1 Action | v1 Regime | Earnings | v2 Eligible | v2 Gate | Divergence | sigma_fwd | FVRP | z | 1M/3M | accel_dn |
|--------|-----------|-----------|----------|-------------|---------|------------|-----------|------|------|-------|----------|
| NKE | CONDITIONAL | NORMAL | 55d | No | NORMAL | V2_STRICTER | 0.349 | 1.14 | +0.24 | 0.980 | 0.530 |
| SPY | CONDITIONAL | NORMAL | ETF | No | CAUTION | V2_STRICTER | 0.160 | 0.98 | +0.65 | 0.988 | 1.335 |
| WMT | CONDITIONAL | NORMAL | 27d | No | DANGER | V2_STRICTER | 0.258 | 1.22 | +0.83 | 1.145 | 0.412 |
| XLI | CONDITIONAL | NORMAL | ETF | No | NORMAL | V2_STRICTER | 0.204 | 1.00 | +0.01 | 0.992 | 0.879 |
| AAPL | SELL PREMIUM | NORMAL | 6d | No | DANGER | STATE_MISMATCH | 0.262 | 1.04 | +1.39 | 1.096 | 0.557 |
| AMZN | AVOID | DANGER | 6d | No | DANGER | AGREE | 0.365 | 1.16 | +0.92 | 1.173 | 1.485 |
| CAT | AVOID | DANGER | 6d | No | DANGER | AGREE | 0.419 | 1.13 | +0.53 | 1.138 | 1.267 |
| EEM | NO EDGE | CAUTION | ETF | No | DANGER | STATE_MISMATCH | 0.262 | 0.99 | -0.39 | 1.135 | 1.267 |
| GLD | NO EDGE | NORMAL | ETF | No | CAUTION | STATE_MISMATCH | 0.208 | 1.04 | -0.65 | 1.026 | 1.097 |
| GOOG | AVOID | DANGER | 5d | No | DANGER | AGREE | 0.321 | 1.16 | +1.01 | 1.112 | 1.267 |
| GS | NO EDGE | CAUTION | 90d | No | DANGER | STATE_MISMATCH | 0.347 | 0.95 | -0.23 | 1.032 | 0.743 |
| HD | NO EDGE | CAUTION | 25d | No | DANGER | STATE_MISMATCH | 0.264 | 1.30 | +1.94 | 1.166 | 0.463 |
| HOOD | AVOID | DANGER | 4d | No | DANGER | AGREE | 0.782 | 0.88 | -0.02 | 1.113 | 1.247 |
| IWM | NO EDGE | CAUTION | ETF | No | CAUTION | AGREE | 0.198 | 1.04 | +1.26 | 1.009 | 1.015 |
| JNJ | NO EDGE | CAUTION | 89d | No | CAUTION | AGREE | 0.257 | 1.01 | -0.35 | 1.042 | 1.079 |
| JPM | NO EDGE | NORMAL | 83d | No | NORMAL | AGREE | 0.248 | 0.91 | +0.04 | 0.945 | 0.806 |
| KO | AVOID | DANGER | 4d | No | DANGER | AGREE | 0.207 | 1.10 | +1.33 | 1.083 | 0.736 |
| MCD | WATCHLIST | NORMAL | 12d | No | DANGER | STATE_MISMATCH | 0.218 | 1.15 | +1.11 | 1.097 | 0.421 |
| META | NO EDGE | NORMAL | 5d | No | DANGER | STATE_MISMATCH | 0.486 | 0.78 | -0.66 | 1.018 | 1.523 |
| MSFT | AVOID | DANGER | 5d | No | DANGER | AGREE | 0.272 | 1.19 | +0.98 | 1.105 | 1.214 |
| NFLX | NO EDGE | CAUTION | 88d | No | CAUTION | AGREE | 0.490 | 0.64 | -1.50 | 0.963 | 1.279 |
| NVDA | NO EDGE | CAUTION | 26d | No | DANGER | STATE_MISMATCH | 0.462 | 0.93 | +0.49 | 1.116 | 1.337 |
| PLTR | REDUCE SIZE | CAUTION | 10d | No | DANGER | STATE_MISMATCH | 0.616 | 1.05 | +1.58 | 1.168 | 1.248 |
| QQQ | AVOID | DANGER | ETF | No | CAUTION | STATE_MISMATCH | 0.238 | 1.07 | +1.05 | 1.083 | 1.516 |
| SBUX | AVOID | DANGER | 5d | No | DANGER | AGREE | 0.285 | 1.19 | +0.61 | 1.143 | 0.713 |
| TLT | NO EDGE | NORMAL | ETF | No | CAUTION | STATE_MISMATCH | 0.144 | 0.99 | +0.99 | 1.034 | 0.656 |
| TSLA | NO EDGE | CAUTION | 5d | No | DANGER | STATE_MISMATCH | 0.550 | 0.74 | -1.36 | 1.013 | 0.906 |
| UBER | REDUCE SIZE | CAUTION | 11d | No | DANGER | STATE_MISMATCH | 0.384 | 1.06 | +1.43 | 1.120 | 0.924 |
| XLB | NO DATA | NORMAL | ETF | No | NORMAL | NODATA_SKEW | — | — | — | — | — |
| XLE | AVOID | DANGER | ETF | No | DANGER | AGREE | 0.298 | 0.97 | +0.78 | 1.066 | 0.825 |
| XLF | NO EDGE | NORMAL | ETF | No | CAUTION | STATE_MISMATCH | 0.178 | 0.97 | +0.98 | 1.032 | 0.676 |
| XLV | NO EDGE | CAUTION | ETF | No | DANGER | STATE_MISMATCH | 0.183 | 1.08 | +0.56 | 1.057 | 0.765 |
| XOM | AVOID | DANGER | 7d | No | DANGER | AGREE | 0.299 | 1.06 | +1.25 | 1.091 | 0.531 |

---

## 2026-10-22 (Thursday)

**Shadow summary:** Checked 330 / 76 agree / 96 V2_STRICTER / 0 V2_LOOSER / 152 state_mismatch / 6 nodata | index-gating v1 58% vs v2 100% | oscillation v1 1.33 vs v2 0.52 | warm 100% | day-flips v1 10/33 vs v2 2/33 | capture60 n=1957 mean +32 / v2-veto-neg 26% / v2-clear-neg 36% / σfwd-vs-rv30 MAE 0.29 vs 0.26 | veto-disagree 5%

| Ticker | v1 Action | v1 Regime | Earnings | v2 Eligible | v2 Gate | Divergence | sigma_fwd | FVRP | z | 1M/3M | accel_dn |
|--------|-----------|-----------|----------|-------------|---------|------------|-----------|------|------|-------|----------|
| SPY | CONDITIONAL | NORMAL | ETF | No | CAUTION | V2_STRICTER | 0.147 | 1.00 | +0.78 | 0.970 | 1.077 |
| TLT | CONDITIONAL | NORMAL | ETF | No | CAUTION | V2_STRICTER | 0.135 | 0.99 | +1.05 | 0.977 | 0.705 |
| WMT | SELL PREMIUM | NORMAL | 28d | No | DANGER | V2_STRICTER | 0.243 | 1.31 | +1.24 | 1.229 | 0.442 |
| XLI | CONDITIONAL | NORMAL | ETF | No | NORMAL | V2_STRICTER | 0.198 | 0.97 | -0.16 | 0.945 | 0.766 |
| AAPL | CONDITIONAL | NORMAL | 7d | No | DANGER | STATE_MISMATCH | 0.266 | 0.98 | +0.87 | 1.081 | 0.598 |
| AMZN | NO EDGE | CAUTION | 7d | No | DANGER | STATE_MISMATCH | 0.326 | 1.25 | +1.29 | 1.157 | 0.847 |
| CAT | AVOID | DANGER | 7d | No | DANGER | AGREE | 0.403 | 1.12 | +0.47 | 1.123 | 0.935 |
| EEM | AVOID | DANGER | ETF | No | CAUTION | STATE_MISMATCH | 0.227 | 1.15 | +0.35 | 1.073 | 0.918 |
| GLD | NO EDGE | NORMAL | ETF | No | CAUTION | STATE_MISMATCH | 0.181 | 1.09 | -0.26 | 0.999 | 0.673 |
| GOOG | AVOID | DANGER | 6d | No | DANGER | AGREE | 0.307 | 1.20 | +1.25 | 1.129 | 1.004 |
| GS | NO EDGE | NORMAL | 91d | No | DANGER | STATE_MISMATCH | 0.331 | 0.91 | -0.60 | 1.022 | 0.605 |
| HD | NO EDGE | CAUTION | 26d | No | DANGER | STATE_MISMATCH | 0.263 | 1.20 | +1.35 | 1.110 | 0.498 |
| HOOD | AVOID | DANGER | 5d | No | DANGER | AGREE | 0.745 | 0.89 | +0.08 | 1.088 | 1.130 |
| IWM | NO EDGE | CAUTION | ETF | No | CAUTION | AGREE | 0.200 | 0.95 | +0.32 | 0.972 | 1.090 |
| JNJ | NO EDGE | CAUTION | 90d | No | CAUTION | AGREE | 0.237 | 1.00 | -0.43 | 0.995 | 1.159 |
| JPM | NO EDGE | NORMAL | 84d | No | NORMAL | AGREE | 0.257 | 0.82 | -0.85 | 0.948 | 0.866 |
| KO | AVOID | DANGER | 5d | No | DANGER | AGREE | 0.198 | 1.08 | +1.19 | 1.068 | 0.791 |
| MCD | WATCHLIST | NORMAL | 13d | No | DANGER | STATE_MISMATCH | 0.209 | 1.17 | +1.28 | 1.063 | 0.452 |
| META | NO EDGE | CAUTION | 6d | No | DANGER | STATE_MISMATCH | 0.420 | 0.68 | -1.31 | — | 1.010 |
| MSFT | AVOID | DANGER | 6d | No | DANGER | AGREE | 0.271 | 1.19 | +0.98 | 1.115 | 0.928 |
| NFLX | NO EDGE | CAUTION | 89d | No | DANGER | STATE_MISMATCH | 0.529 | 0.57 | -2.05 | 0.960 | 1.374 |
| NKE | CONDITIONAL | NORMAL | 56d | Yes | NORMAL | AGREE | 0.333 | 1.16 | +0.31 | 0.952 | 0.569 |
| NVDA | NO EDGE | CAUTION | 27d | No | DANGER | STATE_MISMATCH | 0.436 | 0.92 | +0.39 | 1.079 | 0.914 |
| PLTR | REDUCE SIZE | CAUTION | 11d | No | DANGER | STATE_MISMATCH | 0.634 | 0.98 | +1.12 | 1.161 | 1.249 |
| QQQ | NO EDGE | CAUTION | ETF | No | CAUTION | AGREE | 0.217 | 1.08 | +1.21 | 1.045 | 1.214 |
| SBUX | NO EDGE | CAUTION | 6d | No | DANGER | STATE_MISMATCH | 0.273 | 1.11 | +0.31 | 1.014 | 0.766 |
| TSLA | AVOID | DANGER | 6d | No | DANGER | AGREE | 0.502 | 0.83 | -0.21 | 1.048 | 0.642 |
| UBER | REDUCE SIZE | CAUTION | 12d | No | DANGER | STATE_MISMATCH | 0.399 | 1.11 | +1.70 | 1.222 | 0.993 |
| XLB | NO DATA | NORMAL | ETF | No | NORMAL | NODATA_SKEW | — | — | — | — | — |
| XLE | NO EDGE | CAUTION | ETF | No | DANGER | STATE_MISMATCH | 0.270 | 1.07 | +1.64 | 1.095 | 0.748 |
| XLF | NO EDGE | NORMAL | ETF | No | CAUTION | STATE_MISMATCH | 0.184 | 0.88 | +0.14 | 1.044 | 0.726 |
| XLV | NO EDGE | CAUTION | ETF | No | DANGER | STATE_MISMATCH | 0.185 | 1.02 | +0.12 | 0.984 | 0.822 |
| XOM | AVOID | DANGER | 8d | No | DANGER | AGREE | 0.282 | 1.06 | +1.22 | 1.064 | 0.570 |

---

## 2026-10-21 (Wednesday)

**Shadow summary:** Checked 330 / 68 agree / 112 V2_STRICTER / 0 V2_LOOSER / 145 state_mismatch / 5 nodata | index-gating v1 53% vs v2 100% | oscillation v1 1.18 vs v2 0.48 | warm 100% | day-flips v1 4/33 vs v2 1/33 | capture60 n=1956 mean +26 / v2-veto-neg 26% / v2-clear-neg 36% / σfwd-vs-rv30 MAE 0.29 vs 0.26 | veto-disagree 5%

| Ticker | v1 Action | v1 Regime | Earnings | v2 Eligible | v2 Gate | Divergence | sigma_fwd | FVRP | z | 1M/3M | accel_dn |
|--------|-----------|-----------|----------|-------------|---------|------------|-----------|------|------|-------|----------|
| NKE | CONDITIONAL | NORMAL | 57d | No | NORMAL | V2_STRICTER | 0.350 | 1.13 | +0.21 | 0.971 | 0.512 |
| NVDA | CONDITIONAL | NORMAL | 28d | No | CAUTION | V2_STRICTER | 0.429 | 0.92 | +0.44 | 1.083 | 0.982 |
| SPY | CONDITIONAL | NORMAL | ETF | No | CAUTION | V2_STRICTER | 0.151 | 0.88 | -0.23 | 0.933 | 1.157 |
| TLT | CONDITIONAL | NORMAL | ETF | No | CAUTION | V2_STRICTER | 0.141 | 0.96 | +0.78 | 0.987 | 0.757 |
| WMT | SELL PREMIUM | NORMAL | 29d | No | DANGER | V2_STRICTER | 0.255 | 1.20 | +0.72 | 1.147 | 0.475 |
| XLI | CONDITIONAL | NORMAL | ETF | No | DANGER | V2_STRICTER | 0.201 | 0.99 | -0.01 | 0.932 | 0.823 |
| AAPL | SELL PREMIUM | NORMAL | 8d | No | DANGER | STATE_MISMATCH | 0.277 | 0.94 | +0.54 | 1.073 | 0.643 |
| AMZN | REDUCE SIZE | CAUTION | 8d | No | DANGER | STATE_MISMATCH | 0.338 | 1.18 | +1.01 | 1.155 | 0.909 |
| CAT | AVOID | DANGER | 8d | No | DANGER | AGREE | 0.400 | 1.15 | +0.63 | 1.150 | 1.004 |
| EEM | NO EDGE | NORMAL | ETF | No | CAUTION | STATE_MISMATCH | 0.238 | 1.01 | -0.28 | 1.011 | 0.986 |
| GLD | NO EDGE | NORMAL | ETF | No | CAUTION | STATE_MISMATCH | 0.185 | 1.08 | -0.38 | 0.995 | 0.723 |
| GOOG | AVOID | DANGER | 7d | No | DANGER | AGREE | 0.298 | 1.23 | +1.40 | 1.129 | 0.935 |
| GS | NO EDGE | NORMAL | 92d | No | DANGER | STATE_MISMATCH | 0.335 | 0.90 | -0.78 | 1.013 | 0.650 |
| HD | NO EDGE | NORMAL | 27d | No | DANGER | STATE_MISMATCH | 0.277 | 1.13 | +0.89 | 1.105 | 0.517 |
| HOOD | AVOID | DANGER | 6d | No | DANGER | AGREE | 0.746 | 0.88 | -0.03 | 1.084 | 1.213 |
| IWM | NO EDGE | CAUTION | ETF | No | CAUTION | AGREE | 0.207 | 0.93 | +0.03 | 0.983 | 1.171 |
| JNJ | NO EDGE | CAUTION | 91d | No | CAUTION | AGREE | 0.248 | 0.99 | -0.48 | 1.028 | 1.232 |
| JPM | NO EDGE | NORMAL | 85d | No | NORMAL | AGREE | 0.268 | 0.79 | -1.26 | 0.925 | 0.930 |
| KO | AVOID | DANGER | 6d | No | DANGER | AGREE | 0.204 | 1.04 | +0.90 | 1.046 | 0.526 |
| MCD | WATCHLIST | NORMAL | 14d | No | DANGER | STATE_MISMATCH | 0.214 | 1.16 | +1.20 | 1.092 | 0.483 |
| META | AVOID | DANGER | 7d | No | DANGER | AGREE | 0.416 | 1.09 | +1.03 | 1.158 | 1.085 |
| MSFT | CONDITIONAL | NORMAL | 7d | No | DANGER | STATE_MISMATCH | 0.275 | 1.15 | +0.81 | 1.112 | 0.997 |
| NFLX | AVOID | DANGER | 90d | No | DANGER | AGREE | 0.417 | 1.26 | +1.62 | 1.262 | 0.912 |
| PLTR | REDUCE SIZE | CAUTION | 12d | No | DANGER | STATE_MISMATCH | 0.633 | 0.98 | +1.12 | 1.169 | 1.341 |
| QQQ | NO EDGE | NORMAL | ETF | No | CAUTION | STATE_MISMATCH | 0.226 | 0.93 | -0.33 | 1.001 | 1.304 |
| SBUX | AVOID | DANGER | 7d | No | DANGER | AGREE | 0.283 | 1.23 | +0.72 | 1.196 | 0.813 |
| TSLA | AVOID | DANGER | 7d | No | DANGER | AGREE | 0.511 | 0.89 | +0.45 | 1.100 | 0.690 |
| UBER | REDUCE SIZE | CAUTION | 13d | No | DANGER | STATE_MISMATCH | 0.406 | 1.07 | +1.47 | 1.196 | 0.899 |
| XLB | NO DATA | NORMAL | ETF | No | NORMAL | NODATA_SKEW | — | — | — | — | — |
| XLE | NO EDGE | NORMAL | ETF | No | DANGER | STATE_MISMATCH | 0.280 | 0.97 | +0.82 | 1.061 | 0.803 |
| XLF | NO EDGE | NORMAL | ETF | No | CAUTION | STATE_MISMATCH | 0.184 | 0.87 | +0.09 | 0.981 | 0.780 |
| XLV | NO EDGE | CAUTION | ETF | No | DANGER | STATE_MISMATCH | 0.183 | 0.97 | -0.26 | 1.082 | 0.819 |
| XOM | NO EDGE | CAUTION | 9d | No | DANGER | STATE_MISMATCH | 0.294 | 1.06 | +1.21 | 1.108 | 0.613 |

---

## 2026-10-20 (Tuesday)

**Shadow summary:** Checked 330 / 60 agree / 121 V2_STRICTER / 0 V2_LOOSER / 144 state_mismatch / 5 nodata | index-gating v1 49% vs v2 100% | oscillation v1 1.18 vs v2 0.52 | warm 100% | day-flips v1 7/33 vs v2 3/33 | capture60 n=1955 mean +20 / v2-veto-neg 26% / v2-clear-neg 36% / σfwd-vs-rv30 MAE 0.29 vs 0.26 | veto-disagree 5%

| Ticker | v1 Action | v1 Regime | Earnings | v2 Eligible | v2 Gate | Divergence | sigma_fwd | FVRP | z | 1M/3M | accel_dn |
|--------|-----------|-----------|----------|-------------|---------|------------|-----------|------|------|-------|----------|
| MCD | CONDITIONAL | NORMAL | 15d | No | DANGER | V2_STRICTER | 0.220 | 1.14 | +1.05 | 1.088 | 0.519 |
| NKE | CONDITIONAL | NORMAL | 58d | No | NORMAL | V2_STRICTER | 0.349 | 1.10 | +0.08 | 0.937 | 0.550 |
| NVDA | CONDITIONAL | NORMAL | 29d | No | CAUTION | V2_STRICTER | 0.443 | 0.87 | -0.09 | 1.046 | 1.051 |
| QQQ | CONDITIONAL | NORMAL | ETF | No | CAUTION | V2_STRICTER | 0.232 | 0.94 | -0.24 | 1.025 | 1.401 |
| SPY | CONDITIONAL | NORMAL | ETF | No | CAUTION | V2_STRICTER | 0.154 | 0.91 | +0.02 | 0.950 | 1.243 |
| TLT | CONDITIONAL | NORMAL | ETF | No | CAUTION | V2_STRICTER | 0.143 | 0.98 | +0.89 | 0.997 | 0.813 |
| WMT | CONDITIONAL | NORMAL | 30d | No | DANGER | V2_STRICTER | 0.250 | 1.19 | +0.69 | 1.126 | 0.437 |
| XLI | CONDITIONAL | NORMAL | ETF | No | DANGER | V2_STRICTER | 0.192 | 1.06 | +0.38 | 1.017 | 0.884 |
| AAPL | SELL PREMIUM | NORMAL | 9d | No | DANGER | STATE_MISMATCH | 0.282 | 0.97 | +0.80 | 1.099 | 0.504 |
| AMZN | REDUCE SIZE | CAUTION | 9d | No | DANGER | STATE_MISMATCH | 0.357 | 1.13 | +0.79 | 1.179 | 0.977 |
| CAT | AVOID | DANGER | 9d | No | DANGER | AGREE | 0.395 | 1.17 | +0.75 | 1.167 | 1.079 |
| EEM | NO EDGE | CAUTION | ETF | No | CAUTION | AGREE | 0.244 | 0.99 | -0.38 | 0.985 | 1.059 |
| GLD | NO EDGE | NORMAL | ETF | No | CAUTION | STATE_MISMATCH | 0.189 | 1.07 | -0.43 | 0.993 | 0.748 |
| GOOG | REDUCE SIZE | CAUTION | 8d | No | DANGER | STATE_MISMATCH | 0.311 | 1.20 | +1.17 | 1.158 | 0.932 |
| GS | NO EDGE | NORMAL | 93d | No | DANGER | STATE_MISMATCH | 0.325 | 0.89 | -0.88 | 0.978 | 0.699 |
| HD | NO EDGE | NORMAL | 28d | No | DANGER | STATE_MISMATCH | 0.279 | 1.08 | +0.58 | 1.052 | 0.555 |
| HOOD | NO EDGE | CAUTION | 7d | No | DANGER | STATE_MISMATCH | 0.748 | 0.89 | +0.11 | 1.109 | 1.303 |
| IWM | NO EDGE | CAUTION | ETF | No | CAUTION | AGREE | 0.204 | 0.93 | -0.02 | 0.977 | 1.258 |
| JNJ | NO EDGE | CAUTION | 92d | No | CAUTION | AGREE | 0.248 | 0.96 | -0.71 | 1.018 | 1.324 |
| JPM | NO EDGE | NORMAL | 86d | No | NORMAL | AGREE | 0.271 | 0.82 | -0.85 | 0.969 | 0.999 |
| KO | NO EDGE | CAUTION | 7d | No | DANGER | STATE_MISMATCH | 0.216 | 1.00 | +0.64 | 1.075 | 0.565 |
| META | AVOID | DANGER | 1d | No | DANGER | AGREE | 0.419 | 1.07 | +0.89 | 1.159 | 1.112 |
| MSFT | SELL PREMIUM | NORMAL | 8d | No | DANGER | STATE_MISMATCH | 0.285 | 1.12 | +0.63 | 1.117 | 1.063 |
| NFLX | AVOID | DANGER | 0d | No | DANGER | AGREE | 0.426 | 1.19 | +1.34 | 1.285 | 0.881 |
| PLTR | REDUCE SIZE | CAUTION | 13d | No | DANGER | STATE_MISMATCH | 0.664 | 0.95 | +0.91 | 1.183 | 1.435 |
| SBUX | AVOID | DANGER | 8d | No | DANGER | AGREE | 0.286 | 1.25 | +0.78 | 1.274 | 0.874 |
| TSLA | AVOID | DANGER | 1d | No | DANGER | AGREE | 0.520 | 0.86 | +0.14 | 1.088 | 0.741 |
| UBER | REDUCE SIZE | CAUTION | 14d | No | DANGER | STATE_MISMATCH | 0.398 | 1.05 | +1.35 | 1.144 | 0.856 |
| XLB | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.196 | 1.00 | -0.66 | 1.000 | 0.600 |
| XLE | NO EDGE | NORMAL | ETF | No | DANGER | STATE_MISMATCH | 0.260 | 1.05 | +1.55 | 1.112 | 0.863 |
| XLF | NO EDGE | NORMAL | ETF | No | CAUTION | STATE_MISMATCH | 0.190 | 0.81 | -0.51 | 1.001 | 0.838 |
| XLV | NO EDGE | CAUTION | ETF | No | DANGER | STATE_MISMATCH | 0.179 | 1.03 | +0.19 | 0.866 | 0.880 |
| XOM | NO EDGE | CAUTION | 10d | No | CAUTION | AGREE | 0.274 | 1.09 | +1.47 | 1.067 | 0.648 |

---

## 2026-10-19 (Monday)

**Shadow summary:** Checked 330 / 51 agree / 129 V2_STRICTER / 0 V2_LOOSER / 145 state_mismatch / 5 nodata | index-gating v1 45% vs v2 100% | oscillation v1 1.09 vs v2 0.55 | warm 100% | day-flips v1 5/33 vs v2 1/33 | capture60 n=1932 mean +17 / v2-veto-neg 26% / v2-clear-neg 36% / σfwd-vs-rv30 MAE 0.29 vs 0.26 | veto-disagree 5%

| Ticker | v1 Action | v1 Regime | Earnings | v2 Eligible | v2 Gate | Divergence | sigma_fwd | FVRP | z | 1M/3M | accel_dn |
|--------|-----------|-----------|----------|-------------|---------|------------|-----------|------|------|-------|----------|
| GOOG | SELL PREMIUM | NORMAL | 9d | No | DANGER | V2_STRICTER | 0.327 | 1.12 | +0.73 | 1.124 | 1.001 |
| GS | CONDITIONAL | NORMAL | 94d | No | DANGER | V2_STRICTER | 0.349 | 0.89 | -0.84 | 1.020 | 0.721 |
| JPM | CONDITIONAL | NORMAL | 87d | No | NORMAL | V2_STRICTER | 0.274 | 0.83 | -0.75 | 0.953 | 0.618 |
| NKE | CONDITIONAL | NORMAL | 59d | No | NORMAL | V2_STRICTER | 0.372 | 1.02 | -0.24 | 0.932 | 0.591 |
| NVDA | CONDITIONAL | NORMAL | 30d | No | CAUTION | V2_STRICTER | 0.440 | 0.88 | +0.04 | 1.041 | 1.129 |
| QQQ | CONDITIONAL | NORMAL | ETF | No | CAUTION | V2_STRICTER | 0.230 | 0.94 | -0.27 | 1.026 | 1.504 |
| SPY | CONDITIONAL | NORMAL | ETF | No | NORMAL | V2_STRICTER | 0.158 | 0.91 | +0.03 | 0.954 | 1.335 |
| TLT | SELL PREMIUM | NORMAL | ETF | No | CAUTION | V2_STRICTER | 0.150 | 0.98 | +0.94 | 1.031 | 0.575 |
| WMT | CONDITIONAL | NORMAL | 31d | No | NORMAL | V2_STRICTER | 0.269 | 1.08 | +0.11 | 1.089 | 0.468 |
| XLF | CONDITIONAL | NORMAL | ETF | No | CAUTION | V2_STRICTER | 0.200 | 0.84 | -0.23 | 1.001 | 0.671 |
| XLI | CONDITIONAL | NORMAL | ETF | No | DANGER | V2_STRICTER | 0.203 | 1.12 | +0.72 | 1.071 | 0.878 |
| AAPL | SELL PREMIUM | NORMAL | 10d | No | DANGER | STATE_MISMATCH | 0.291 | 0.94 | +0.55 | 1.095 | 0.537 |
| AMZN | REDUCE SIZE | CAUTION | 10d | No | DANGER | STATE_MISMATCH | 0.337 | 1.17 | +0.97 | 1.161 | 1.049 |
| CAT | NO EDGE | CAUTION | 10d | No | DANGER | STATE_MISMATCH | 0.410 | 1.16 | +0.71 | 1.173 | 1.151 |
| EEM | NO EDGE | NORMAL | ETF | No | CAUTION | STATE_MISMATCH | 0.244 | 0.98 | -0.42 | 0.979 | 1.137 |
| GLD | NO EDGE | NORMAL | ETF | No | CAUTION | STATE_MISMATCH | 0.203 | 1.02 | -0.84 | 0.989 | 0.769 |
| HD | NO EDGE | CAUTION | 29d | No | NORMAL | STATE_MISMATCH | 0.293 | 1.07 | +0.48 | 1.072 | 0.597 |
| HOOD | NO EDGE | CAUTION | 8d | No | DANGER | STATE_MISMATCH | 0.792 | 0.87 | -0.14 | 1.103 | 1.368 |
| IWM | NO EDGE | CAUTION | ETF | No | CAUTION | AGREE | 0.214 | 0.93 | -0.00 | 1.007 | 1.351 |
| JNJ | NO EDGE | CAUTION | 93d | No | CAUTION | AGREE | 0.262 | 0.95 | -0.82 | 1.020 | 1.411 |
| KO | CONDITIONAL | NORMAL | 8d | No | DANGER | STATE_MISMATCH | 0.211 | 1.07 | +1.08 | 1.107 | 0.457 |
| MCD | WATCHLIST | NORMAL | 16d | No | DANGER | STATE_MISMATCH | 0.228 | 1.08 | +0.64 | 1.049 | 0.555 |
| META | AVOID | DANGER | 2d | No | DANGER | AGREE | 0.443 | 1.00 | +0.55 | 1.143 | 1.189 |
| MSFT | SELL PREMIUM | NORMAL | 9d | No | DANGER | STATE_MISMATCH | 0.305 | 1.03 | +0.21 | 1.101 | 1.142 |
| NFLX | AVOID | DANGER | 1d | No | DANGER | AGREE | 0.454 | 1.05 | +0.77 | 1.242 | 0.914 |
| PLTR | REDUCE SIZE | CAUTION | 14d | No | DANGER | STATE_MISMATCH | 0.683 | 0.91 | +0.58 | 1.174 | 1.541 |
| SBUX | NO EDGE | CAUTION | 9d | No | DANGER | STATE_MISMATCH | 0.295 | 1.16 | +0.46 | 1.129 | 0.938 |
| TSLA | AVOID | DANGER | 2d | No | DANGER | AGREE | 0.537 | 0.86 | +0.11 | 1.118 | 0.796 |
| UBER | REDUCE SIZE | CAUTION | 15d | No | DANGER | STATE_MISMATCH | 0.423 | 1.04 | +1.32 | 1.211 | 0.904 |
| XLB | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.209 | 0.95 | -0.89 | 1.054 | 0.645 |
| XLE | NO EDGE | NORMAL | ETF | No | DANGER | STATE_MISMATCH | 0.267 | 1.00 | +1.08 | 1.042 | 0.864 |
| XLV | NO EDGE | CAUTION | ETF | No | DANGER | STATE_MISMATCH | 0.182 | 1.11 | +0.77 | 1.121 | 0.861 |
| XOM | NO EDGE | NORMAL | 11d | No | CAUTION | STATE_MISMATCH | 0.291 | 0.99 | +0.62 | 1.027 | 0.671 |

---

## 2026-10-16 (Friday)

**Shadow summary:** Checked 330 / 50 agree / 129 V2_STRICTER / 0 V2_LOOSER / 146 state_mismatch / 5 nodata | index-gating v1 47% vs v2 100% | oscillation v1 1.12 vs v2 0.61 | warm 100% | day-flips v1 4/33 vs v2 7/33 | capture60 n=1932 mean +9 / v2-veto-neg 26% / v2-clear-neg 36% / σfwd-vs-rv30 MAE 0.29 vs 0.26 | veto-disagree 6%

| Ticker | v1 Action | v1 Regime | Earnings | v2 Eligible | v2 Gate | Divergence | sigma_fwd | FVRP | z | 1M/3M | accel_dn |
|--------|-----------|-----------|----------|-------------|---------|------------|-----------|------|------|-------|----------|
| GOOG | SELL PREMIUM | NORMAL | 12d | No | DANGER | V2_STRICTER | 0.320 | 1.16 | +0.94 | 1.132 | 0.714 |
| MCD | CONDITIONAL | NORMAL | 19d | No | DANGER | V2_STRICTER | 0.229 | 1.08 | +0.66 | 1.069 | 0.596 |
| PLTR | SELL PREMIUM | NORMAL | 17d | No | DANGER | V2_STRICTER | 0.603 | 1.03 | +1.43 | 1.187 | 0.899 |
| QQQ | SELL PREMIUM | NORMAL | ETF | No | CAUTION | V2_STRICTER | 0.225 | 0.99 | +0.28 | 1.036 | 1.205 |
| SPY | CONDITIONAL | NORMAL | ETF | No | NORMAL | V2_STRICTER | 0.149 | 0.96 | +0.49 | 0.967 | 1.089 |
| TLT | CONDITIONAL | NORMAL | ETF | No | CAUTION | V2_STRICTER | 0.158 | 0.91 | +0.30 | 1.023 | 0.617 |
| AAPL | CONDITIONAL | NORMAL | 13d | No | DANGER | STATE_MISMATCH | 0.278 | 0.96 | +0.69 | 1.093 | 0.577 |
| AMZN | REDUCE SIZE | CAUTION | 13d | No | DANGER | STATE_MISMATCH | 0.335 | 1.19 | +1.01 | 1.163 | 0.917 |
| CAT | NO EDGE | CAUTION | 13d | No | DANGER | STATE_MISMATCH | 0.432 | 1.08 | +0.14 | 1.173 | 1.229 |
| EEM | NO EDGE | NORMAL | ETF | No | CAUTION | STATE_MISMATCH | 0.252 | 0.96 | -0.55 | 1.000 | 1.057 |
| GLD | NO EDGE | NORMAL | ETF | No | CAUTION | STATE_MISMATCH | 0.210 | 0.99 | -1.03 | 1.003 | 0.823 |
| GS | NO EDGE | NORMAL | 97d | No | DANGER | STATE_MISMATCH | 0.343 | 0.89 | -0.90 | 1.025 | 0.679 |
| HD | NO EDGE | CAUTION | 32d | No | NORMAL | STATE_MISMATCH | 0.303 | 0.98 | -0.22 | 1.036 | 0.641 |
| HOOD | NO EDGE | NORMAL | 11d | No | DANGER | STATE_MISMATCH | 0.793 | 0.87 | -0.14 | 1.131 | 1.324 |
| IWM | NO EDGE | CAUTION | ETF | No | CAUTION | AGREE | 0.206 | 0.96 | +0.36 | 1.002 | 1.203 |
| JNJ | NO EDGE | CAUTION | 96d | No | CAUTION | AGREE | 0.272 | 0.85 | -1.69 | 1.010 | 1.516 |
| JPM | NO EDGE | NORMAL | 90d | No | CAUTION | STATE_MISMATCH | 0.265 | 0.81 | -0.95 | 0.962 | 0.664 |
| KO | NO EDGE | CAUTION | 11d | No | DANGER | STATE_MISMATCH | 0.215 | 0.97 | +0.34 | 1.044 | 0.490 |
| META | AVOID | DANGER | 5d | No | DANGER | AGREE | 0.428 | 1.01 | +0.62 | 1.133 | 0.961 |
| MSFT | SELL PREMIUM | NORMAL | 12d | No | DANGER | STATE_MISMATCH | 0.267 | 1.18 | +0.92 | 1.113 | 0.909 |
| NFLX | AVOID | DANGER | 4d | No | DANGER | AGREE | 0.378 | 1.24 | +1.52 | 1.245 | 0.612 |
| NKE | NO EDGE | CAUTION | 62d | No | NORMAL | STATE_MISMATCH | 0.375 | 0.99 | -0.39 | 0.903 | 0.634 |
| NVDA | NO EDGE | NORMAL | 33d | No | CAUTION | STATE_MISMATCH | 0.451 | 0.81 | -0.71 | 0.986 | 1.157 |
| SBUX | REDUCE SIZE | CAUTION | 12d | No | DANGER | STATE_MISMATCH | 0.301 | 1.22 | +0.66 | 1.290 | 1.008 |
| TSLA | AVOID | DANGER | 5d | No | DANGER | AGREE | 0.477 | 0.95 | +1.02 | 1.099 | 0.699 |
| UBER | REDUCE SIZE | CAUTION | 18d | No | DANGER | STATE_MISMATCH | 0.409 | 1.06 | +1.42 | 1.164 | 0.889 |
| WMT | NO EDGE | NORMAL | 34d | No | NORMAL | AGREE | 0.286 | 0.89 | -0.99 | 0.959 | 0.503 |
| XLB | NO DATA | NORMAL | ETF | No | NORMAL | NODATA_SKEW | — | — | — | — | — |
| XLE | NO EDGE | NORMAL | ETF | No | DANGER | STATE_MISMATCH | 0.264 | 1.00 | +1.09 | 1.051 | 0.928 |
| XLF | NO EDGE | NORMAL | ETF | No | CAUTION | STATE_MISMATCH | 0.195 | 0.81 | -0.56 | 1.086 | 0.721 |
| XLI | NO DATA | NORMAL | ETF | No | DANGER | NODATA_SKEW | — | — | — | — | — |
| XLV | NO EDGE | NORMAL | ETF | No | DANGER | STATE_MISMATCH | 0.188 | 1.07 | +0.48 | 1.071 | 0.908 |
| XOM | NO EDGE | NORMAL | 14d | No | CAUTION | STATE_MISMATCH | 0.281 | 1.05 | +1.12 | 1.048 | 0.721 |

---

## 2026-10-15 (Thursday)

**Shadow summary:** Checked 330 / 52 agree / 137 V2_STRICTER / 0 V2_LOOSER / 138 state_mismatch / 3 nodata | index-gating v1 45% vs v2 100% | oscillation v1 1.15 vs v2 0.45 | warm 100% | day-flips v1 6/33 vs v2 1/33 | capture60 n=1932 mean +1 / v2-veto-neg 27% / v2-clear-neg 36% / σfwd-vs-rv30 MAE 0.28 vs 0.26 | veto-disagree 6%

| Ticker | v1 Action | v1 Regime | Earnings | v2 Eligible | v2 Gate | Divergence | sigma_fwd | FVRP | z | 1M/3M | accel_dn |
|--------|-----------|-----------|----------|-------------|---------|------------|-----------|------|------|-------|----------|
| GOOG | SELL PREMIUM | NORMAL | 13d | No | DANGER | V2_STRICTER | 0.309 | 1.18 | +1.07 | 1.122 | 0.767 |
| MCD | CONDITIONAL | NORMAL | 20d | No | CAUTION | V2_STRICTER | 0.205 | 1.26 | +1.81 | 1.072 | 0.640 |
| PLTR | SELL PREMIUM | NORMAL | 18d | No | DANGER | V2_STRICTER | 0.581 | 1.04 | +1.44 | 1.180 | 0.963 |
| QQQ | CONDITIONAL | NORMAL | ETF | No | NORMAL | V2_STRICTER | 0.210 | 0.97 | +0.03 | 0.994 | 1.293 |
| SPY | CONDITIONAL | NORMAL | ETF | No | NORMAL | V2_STRICTER | 0.146 | 0.91 | +0.04 | 0.921 | 1.170 |
| TLT | CONDITIONAL | NORMAL | ETF | No | CAUTION | V2_STRICTER | 0.135 | 1.01 | +1.20 | 0.993 | 0.663 |
| UBER | SELL PREMIUM | NORMAL | 19d | No | DANGER | V2_STRICTER | 0.419 | 1.07 | +1.43 | 1.215 | 0.955 |
| WMT | CONDITIONAL | NORMAL | 35d | No | NORMAL | V2_STRICTER | 0.246 | 1.08 | +0.14 | 1.000 | 0.540 |
| XLE | CONDITIONAL | NORMAL | ETF | No | CAUTION | V2_STRICTER | 0.247 | 1.11 | +2.07 | 1.077 | 0.526 |
| XLF | CONDITIONAL | NORMAL | ETF | No | CAUTION | V2_STRICTER | 0.194 | 0.87 | +0.00 | 1.012 | 0.775 |
| XOM | CONDITIONAL | NORMAL | 15d | No | CAUTION | V2_STRICTER | 0.260 | 1.19 | +2.34 | 1.096 | 0.467 |
| AAPL | CONDITIONAL | NORMAL | 14d | No | DANGER | STATE_MISMATCH | 0.280 | 0.96 | +0.69 | 1.097 | 0.607 |
| AMZN | REDUCE SIZE | CAUTION | 14d | No | DANGER | STATE_MISMATCH | 0.319 | 1.27 | +1.37 | 1.173 | 0.985 |
| CAT | NO EDGE | CAUTION | 14d | No | DANGER | STATE_MISMATCH | 0.397 | 1.18 | +0.81 | 1.192 | 1.278 |
| EEM | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.235 | 1.03 | -0.21 | 1.035 | 1.110 |
| GLD | NO EDGE | NORMAL | ETF | No | CAUTION | STATE_MISMATCH | 0.211 | 0.99 | -1.08 | 0.994 | 0.884 |
| GS | NO EDGE | NORMAL | 98d | No | DANGER | STATE_MISMATCH | 0.349 | 0.89 | -0.88 | 1.050 | 0.730 |
| HD | AVOID | DANGER | 33d | No | NORMAL | STATE_MISMATCH | 0.260 | 1.09 | +0.58 | 0.942 | 0.688 |
| HOOD | NO EDGE | NORMAL | 12d | No | DANGER | STATE_MISMATCH | 0.740 | 0.89 | +0.07 | 1.084 | 1.422 |
| IWM | NO EDGE | CAUTION | ETF | No | NORMAL | STATE_MISMATCH | 0.215 | 0.89 | -0.48 | 0.992 | 1.293 |
| JNJ | NO EDGE | CAUTION | 97d | No | CAUTION | AGREE | 0.265 | 0.86 | -1.64 | 0.975 | 1.627 |
| JPM | NO EDGE | NORMAL | 91d | No | CAUTION | STATE_MISMATCH | 0.278 | 0.85 | -0.52 | 1.020 | 0.714 |
| KO | REDUCE SIZE | CAUTION | 12d | No | DANGER | STATE_MISMATCH | 0.192 | 1.15 | +1.63 | 1.100 | 0.527 |
| META | AVOID | DANGER | 6d | No | DANGER | AGREE | 0.407 | 1.07 | +0.89 | 1.128 | 1.032 |
| MSFT | SELL PREMIUM | NORMAL | 13d | No | DANGER | STATE_MISMATCH | 0.270 | 1.15 | +0.76 | 1.107 | 0.976 |
| NFLX | AVOID | DANGER | 5d | No | DANGER | AGREE | 0.373 | 1.24 | +1.51 | 1.211 | 0.658 |
| NKE | NO EDGE | CAUTION | 63d | No | NORMAL | STATE_MISMATCH | 0.334 | 1.04 | -0.13 | 0.883 | 0.681 |
| NVDA | NO EDGE | NORMAL | 34d | No | NORMAL | AGREE | 0.412 | 0.86 | -0.21 | 0.964 | 1.149 |
| SBUX | NO EDGE | CAUTION | 13d | No | DANGER | STATE_MISMATCH | 0.297 | 1.30 | +0.92 | 1.406 | 1.083 |
| TSLA | AVOID | DANGER | 6d | No | DANGER | AGREE | 0.451 | 0.97 | +1.22 | 1.089 | 0.689 |
| XLB | NO DATA | NORMAL | ETF | No | DANGER | NODATA_SKEW | — | — | — | — | — |
| XLI | NO EDGE | CAUTION | ETF | No | DANGER | STATE_MISMATCH | 0.197 | 1.04 | +0.25 | 0.996 | 1.012 |
| XLV | NO EDGE | CAUTION | ETF | No | DANGER | STATE_MISMATCH | 0.174 | 1.09 | +0.60 | 1.032 | 0.976 |

---

## 2026-10-14 (Wednesday)

**Shadow summary:** Checked 330 / 55 agree / 138 V2_STRICTER / 0 V2_LOOSER / 135 state_mismatch / 2 nodata | index-gating v1 46% vs v2 99% | oscillation v1 1.12 vs v2 0.58 | warm 100% | day-flips v1 4/33 vs v2 1/33 | capture60 n=1932 mean -8 / v2-veto-neg 27% / v2-clear-neg 36% / σfwd-vs-rv30 MAE 0.28 vs 0.26 | veto-disagree 5%

| Ticker | v1 Action | v1 Regime | Earnings | v2 Eligible | v2 Gate | Divergence | sigma_fwd | FVRP | z | 1M/3M | accel_dn |
|--------|-----------|-----------|----------|-------------|---------|------------|-----------|------|------|-------|----------|
| AAPL | CONDITIONAL | NORMAL | 15d | No | DANGER | V2_STRICTER | 0.284 | 0.90 | +0.18 | 1.073 | 0.652 |
| AMZN | SELL PREMIUM | NORMAL | 15d | No | DANGER | V2_STRICTER | 0.298 | 1.34 | +1.62 | 1.157 | 0.852 |
| GOOG | SELL PREMIUM | NORMAL | 14d | No | DANGER | V2_STRICTER | 0.282 | 1.28 | +1.57 | 1.131 | 0.547 |
| IWM | CONDITIONAL | NORMAL | ETF | No | NORMAL | V2_STRICTER | 0.182 | 1.09 | +1.77 | 0.999 | 0.871 |
| MCD | CONDITIONAL | NORMAL | 21d | No | CAUTION | V2_STRICTER | 0.207 | 1.16 | +1.17 | 1.011 | 0.688 |
| PLTR | CONDITIONAL | NORMAL | 19d | No | DANGER | V2_STRICTER | 0.530 | 1.10 | +1.83 | 1.148 | 0.302 |
| QQQ | CONDITIONAL | NORMAL | ETF | No | NORMAL | V2_STRICTER | 0.189 | 1.07 | +1.06 | 0.986 | 0.869 |
| SPY | CONDITIONAL | NORMAL | ETF | No | NORMAL | V2_STRICTER | 0.120 | 1.14 | +1.88 | 0.932 | 0.610 |
| TLT | CONDITIONAL | NORMAL | ETF | No | CAUTION | V2_STRICTER | 0.123 | 1.10 | +1.87 | 0.997 | 0.712 |
| UBER | SELL PREMIUM | NORMAL | 20d | No | DANGER | V2_STRICTER | 0.371 | 1.24 | +2.36 | 1.265 | 0.490 |
| XLE | CONDITIONAL | NORMAL | ETF | No | CAUTION | V2_STRICTER | 0.255 | 1.04 | +1.46 | 1.021 | 0.565 |
| XLF | CONDITIONAL | NORMAL | ETF | No | CAUTION | V2_STRICTER | 0.185 | 0.92 | +0.55 | 1.067 | 0.738 |
| XOM | CONDITIONAL | NORMAL | 16d | No | CAUTION | V2_STRICTER | 0.262 | 1.08 | +1.43 | 1.023 | 0.501 |
| CAT | NO EDGE | CAUTION | 15d | No | DANGER | STATE_MISMATCH | 0.387 | 1.13 | +0.49 | 1.125 | 1.240 |
| EEM | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.222 | 1.01 | -0.31 | 0.967 | 0.915 |
| GLD | NO EDGE | NORMAL | ETF | No | CAUTION | STATE_MISMATCH | 0.185 | 1.12 | -0.16 | 1.000 | 0.781 |
| GS | NO EDGE | CAUTION | 99d | No | DANGER | STATE_MISMATCH | 0.342 | 0.91 | -0.67 | 1.040 | 0.617 |
| HD | NO EDGE | NORMAL | 34d | No | NORMAL | AGREE | 0.262 | 1.05 | +0.29 | 0.927 | 0.739 |
| HOOD | NO EDGE | NORMAL | 13d | No | DANGER | STATE_MISMATCH | 0.598 | 1.09 | +2.04 | 1.078 | 0.677 |
| JNJ | NO EDGE | CAUTION | 98d | No | DANGER | STATE_MISMATCH | 0.283 | 0.84 | -1.80 | 0.993 | 1.748 |
| JPM | NO EDGE | NORMAL | 92d | No | CAUTION | STATE_MISMATCH | 0.278 | 0.79 | -1.20 | 0.969 | 0.766 |
| KO | REDUCE SIZE | CAUTION | 13d | No | DANGER | STATE_MISMATCH | 0.184 | 1.25 | +2.29 | 1.178 | 0.566 |
| META | NO EDGE | NORMAL | 7d | No | DANGER | STATE_MISMATCH | 0.409 | 1.06 | +0.83 | 1.114 | 0.751 |
| MSFT | SELL PREMIUM | NORMAL | 14d | No | DANGER | STATE_MISMATCH | 0.264 | 1.16 | +0.81 | 1.106 | 0.616 |
| NFLX | AVOID | DANGER | 6d | No | DANGER | AGREE | 0.358 | 1.23 | +1.49 | 1.174 | 0.707 |
| NKE | NO EDGE | CAUTION | 64d | No | NORMAL | STATE_MISMATCH | 0.330 | 1.05 | -0.11 | 0.854 | 0.731 |
| NVDA | NO EDGE | NORMAL | 35d | No | NORMAL | AGREE | 0.382 | 0.84 | -0.40 | 0.910 | 0.851 |
| SBUX | NO EDGE | CAUTION | 14d | No | DANGER | STATE_MISMATCH | 0.305 | 1.27 | +0.82 | 1.312 | 1.163 |
| TSLA | NO EDGE | NORMAL | 7d | No | DANGER | STATE_MISMATCH | 0.442 | 0.98 | +1.26 | 1.086 | 0.539 |
| WMT | NO EDGE | NORMAL | 36d | No | NORMAL | AGREE | 0.234 | 0.95 | -0.59 | 0.852 | 0.580 |
| XLB | NO EDGE | NORMAL | ETF | No | DANGER | STATE_MISMATCH | 0.187 | 1.06 | -0.44 | 1.039 | 0.797 |
| XLI | NO EDGE | CAUTION | ETF | No | DANGER | STATE_MISMATCH | 0.183 | 1.16 | +0.96 | 1.085 | 0.960 |
| XLV | NO EDGE | CAUTION | ETF | No | DANGER | STATE_MISMATCH | 0.169 | 1.06 | +0.36 | 1.056 | 1.048 |

---

## 2026-10-13 (Tuesday)

**Shadow summary:** Checked 330 / 60 agree / 132 V2_STRICTER / 0 V2_LOOSER / 136 state_mismatch / 2 nodata | index-gating v1 49% vs v2 98% | oscillation v1 1.09 vs v2 0.58 | warm 100% | day-flips v1 3/33 vs v2 0/33 | capture60 n=1932 mean -17 / v2-veto-neg 27% / v2-clear-neg 36% / σfwd-vs-rv30 MAE 0.28 vs 0.26 | veto-disagree 5%

| Ticker | v1 Action | v1 Regime | Earnings | v2 Eligible | v2 Gate | Divergence | sigma_fwd | FVRP | z | 1M/3M | accel_dn |
|--------|-----------|-----------|----------|-------------|---------|------------|-----------|------|------|-------|----------|
| AAPL | CONDITIONAL | NORMAL | 16d | No | DANGER | V2_STRICTER | 0.288 | 0.92 | +0.33 | 1.088 | 0.700 |
| AMZN | SELL PREMIUM | NORMAL | 16d | No | DANGER | V2_STRICTER | 0.303 | 1.29 | +1.42 | 1.147 | 0.905 |
| GOOG | SELL PREMIUM | NORMAL | 15d | No | DANGER | V2_STRICTER | 0.278 | 1.27 | +1.52 | 1.107 | 0.588 |
| IWM | CONDITIONAL | NORMAL | ETF | No | NORMAL | V2_STRICTER | 0.180 | 1.03 | +1.19 | 0.967 | 0.894 |
| MCD | CONDITIONAL | NORMAL | 22d | No | CAUTION | V2_STRICTER | 0.210 | 1.16 | +1.18 | 1.028 | 0.739 |
| MSFT | SELL PREMIUM | NORMAL | 15d | No | DANGER | V2_STRICTER | 0.270 | 1.14 | +0.72 | 1.113 | 0.662 |
| PLTR | CONDITIONAL | NORMAL | 20d | No | DANGER | V2_STRICTER | 0.564 | 1.00 | +1.19 | 1.128 | 0.321 |
| QQQ | CONDITIONAL | NORMAL | ETF | No | NORMAL | V2_STRICTER | 0.185 | 1.01 | +0.46 | 0.943 | 0.910 |
| SPY | CONDITIONAL | NORMAL | ETF | No | NORMAL | V2_STRICTER | 0.127 | 0.99 | +0.73 | 0.904 | 0.655 |
| TLT | SELL PREMIUM | NORMAL | ETF | No | CAUTION | V2_STRICTER | 0.118 | 1.17 | +2.44 | 0.991 | 0.765 |
| UBER | SELL PREMIUM | NORMAL | 21d | No | DANGER | V2_STRICTER | 0.385 | 1.06 | +1.37 | 1.105 | 0.520 |
| XLB | CONDITIONAL | NORMAL | ETF | No | DANGER | V2_STRICTER | 0.187 | 1.26 | +0.32 | 1.194 | 0.856 |
| XLE | CONDITIONAL | NORMAL | ETF | No | CAUTION | V2_STRICTER | 0.267 | 1.00 | +1.15 | 1.059 | 0.607 |
| XLF | CONDITIONAL | NORMAL | ETF | No | CAUTION | V2_STRICTER | 0.166 | 1.03 | +1.48 | 1.041 | 0.737 |
| CAT | NO EDGE | CAUTION | 16d | No | DANGER | STATE_MISMATCH | 0.355 | 1.26 | +1.27 | 1.159 | 1.146 |
| EEM | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.216 | 1.02 | -0.25 | 1.003 | 0.953 |
| GLD | NO EDGE | NORMAL | ETF | No | CAUTION | STATE_MISMATCH | 0.193 | 1.08 | -0.40 | 0.994 | 0.838 |
| GS | AVOID | DANGER | 0d | No | DANGER | AGREE | 0.290 | 1.12 | +1.27 | 1.057 | 0.658 |
| HD | NO EDGE | NORMAL | 35d | No | NORMAL | AGREE | 0.246 | 1.09 | +0.59 | 0.919 | 0.794 |
| HOOD | NO EDGE | NORMAL | 14d | No | DANGER | STATE_MISMATCH | 0.617 | 1.04 | +1.57 | 1.085 | 0.727 |
| JNJ | AVOID | DANGER | 0d | No | DANGER | AGREE | 0.210 | 1.30 | +1.76 | 1.071 | 0.907 |
| JPM | AVOID | DANGER | 0d | No | CAUTION | STATE_MISMATCH | 0.226 | 1.13 | +1.91 | 1.067 | 0.713 |
| KO | REDUCE SIZE | CAUTION | 14d | No | DANGER | STATE_MISMATCH | 0.182 | 1.19 | +1.88 | 1.092 | 0.608 |
| META | WATCHLIST | NORMAL | 8d | No | DANGER | STATE_MISMATCH | 0.395 | 1.12 | +1.07 | 1.154 | 0.807 |
| NFLX | AVOID | DANGER | 7d | No | DANGER | AGREE | 0.379 | 1.15 | +1.19 | 1.179 | 0.757 |
| NKE | NO EDGE | CAUTION | 65d | No | NORMAL | STATE_MISMATCH | 0.346 | 0.99 | -0.36 | 0.848 | 0.786 |
| NVDA | NO EDGE | NORMAL | 36d | No | NORMAL | AGREE | 0.384 | 0.78 | -0.98 | 0.878 | 0.914 |
| SBUX | REDUCE SIZE | CAUTION | 15d | No | DANGER | STATE_MISMATCH | 0.319 | 1.12 | +0.32 | 1.158 | 1.245 |
| TSLA | NO EDGE | NORMAL | 8d | No | DANGER | STATE_MISMATCH | 0.441 | 0.96 | +1.07 | 1.062 | 0.552 |
| WMT | NO EDGE | CAUTION | 37d | No | NORMAL | STATE_MISMATCH | 0.218 | 1.03 | -0.12 | 0.856 | 0.578 |
| XLI | NO EDGE | CAUTION | ETF | No | CAUTION | AGREE | 0.177 | 1.34 | +1.87 | 1.271 | 1.020 |
| XLV | REDUCE SIZE | CAUTION | ETF | No | DANGER | STATE_MISMATCH | 0.166 | 1.37 | +2.25 | 1.459 | 0.731 |
| XOM | NO EDGE | NORMAL | 17d | No | CAUTION | STATE_MISMATCH | 0.271 | 1.05 | +1.16 | 1.036 | 0.538 |

---

## 2026-10-12 (Monday)

**Shadow summary:** Checked 330 / 64 agree / 128 V2_STRICTER / 1 V2_LOOSER / 135 state_mismatch / 2 nodata | index-gating v1 52% vs v2 98% | oscillation v1 1.06 vs v2 0.76 | warm 100% | day-flips v1 1/33 vs v2 1/33 | capture60 n=1932 mean -28 / v2-veto-neg 28% / v2-clear-neg 36% / σfwd-vs-rv30 MAE 0.28 vs 0.26 | veto-disagree 5%

| Ticker | v1 Action | v1 Regime | Earnings | v2 Eligible | v2 Gate | Divergence | sigma_fwd | FVRP | z | 1M/3M | accel_dn |
|--------|-----------|-----------|----------|-------------|---------|------------|-----------|------|------|-------|----------|
| AMZN | SELL PREMIUM | NORMAL | 17d | No | DANGER | V2_STRICTER | 0.317 | 1.23 | +1.17 | 1.133 | 0.886 |
| GOOG | SELL PREMIUM | NORMAL | 16d | No | DANGER | V2_STRICTER | 0.289 | 1.22 | +1.24 | 1.100 | 0.631 |
| IWM | CONDITIONAL | NORMAL | ETF | No | NORMAL | V2_STRICTER | 0.194 | 0.96 | +0.38 | 0.969 | 0.932 |
| MSFT | SELL PREMIUM | NORMAL | 16d | No | DANGER | V2_STRICTER | 0.287 | 1.08 | +0.45 | 1.090 | 0.711 |
| PLTR | CONDITIONAL | NORMAL | 21d | No | DANGER | V2_STRICTER | 0.590 | 0.95 | +0.88 | 1.114 | 0.345 |
| QQQ | CONDITIONAL | NORMAL | ETF | No | NORMAL | V2_STRICTER | 0.198 | 0.95 | -0.21 | 0.932 | 0.877 |
| SPY | CONDITIONAL | NORMAL | ETF | No | NORMAL | V2_STRICTER | 0.137 | 0.91 | +0.02 | 0.899 | 0.700 |
| TLT | SELL PREMIUM | NORMAL | ETF | No | CAUTION | V2_STRICTER | 0.128 | 1.09 | +1.83 | 0.995 | 0.822 |
| UBER | SELL PREMIUM | NORMAL | 22d | No | DANGER | V2_STRICTER | 0.377 | 1.08 | +1.54 | 1.129 | 0.558 |
| XLF | CONDITIONAL | NORMAL | ETF | No | CAUTION | V2_STRICTER | 0.175 | 0.96 | +0.88 | 1.013 | 0.792 |
| XOM | CONDITIONAL | NORMAL | 18d | No | CAUTION | V2_STRICTER | 0.277 | 1.02 | +0.89 | 1.009 | 0.578 |
| AAPL | NO EDGE | NORMAL | 17d | No | DANGER | STATE_MISMATCH | 0.310 | 0.84 | -0.42 | 1.055 | 0.752 |
| CAT | REDUCE SIZE | CAUTION | 17d | No | DANGER | STATE_MISMATCH | 0.373 | 1.16 | +0.69 | 1.112 | 1.231 |
| EEM | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.231 | 0.96 | -0.57 | 0.960 | 0.952 |
| GLD | NO EDGE | CAUTION | ETF | No | CAUTION | AGREE | 0.208 | 1.01 | -0.97 | 0.984 | 0.872 |
| GS | AVOID | DANGER | 1d | No | DANGER | AGREE | 0.303 | 1.09 | +1.03 | 1.063 | 0.705 |
| HD | NO EDGE | NORMAL | 36d | No | NORMAL | AGREE | 0.255 | 1.09 | +0.57 | 0.937 | 0.853 |
| HOOD | NO EDGE | NORMAL | 15d | No | DANGER | STATE_MISMATCH | 0.662 | 0.93 | +0.48 | 1.056 | 0.781 |
| JNJ | AVOID | DANGER | 1d | No | DANGER | AGREE | 0.220 | 1.16 | +0.84 | 1.035 | 0.974 |
| JPM | AVOID | DANGER | 1d | No | CAUTION | STATE_MISMATCH | 0.237 | 1.05 | +1.28 | 1.015 | 0.766 |
| KO | REDUCE SIZE | CAUTION | 15d | No | DANGER | STATE_MISMATCH | 0.191 | 1.09 | +1.27 | 1.060 | 0.653 |
| MCD | WATCHLIST | NORMAL | 23d | No | CAUTION | STATE_MISMATCH | 0.215 | 1.12 | +0.95 | 1.003 | 0.794 |
| META | WATCHLIST | NORMAL | 9d | No | DANGER | STATE_MISMATCH | 0.359 | 1.20 | +1.40 | 1.151 | 0.867 |
| NFLX | NO EDGE | NORMAL | 8d | No | DANGER | STATE_MISMATCH | 0.390 | 1.09 | +0.92 | 1.157 | 0.813 |
| NKE | NO EDGE | CAUTION | 66d | No | NORMAL | STATE_MISMATCH | 0.361 | 0.93 | -0.65 | 0.821 | 0.844 |
| NVDA | NO EDGE | NORMAL | 37d | No | NORMAL | AGREE | 0.404 | 0.75 | -1.30 | 0.878 | 0.905 |
| SBUX | REDUCE SIZE | CAUTION | 16d | No | DANGER | STATE_MISMATCH | 0.344 | 1.17 | +0.49 | 1.275 | 1.337 |
| TSLA | NO EDGE | NORMAL | 9d | No | DANGER | STATE_MISMATCH | 0.478 | 0.89 | +0.34 | 1.052 | 0.520 |
| WMT | NO EDGE | CAUTION | 38d | No | NORMAL | STATE_MISMATCH | 0.228 | 0.93 | -0.72 | 0.823 | 0.620 |
| XLB | NO EDGE | NORMAL | ETF | No | DANGER | STATE_MISMATCH | 0.187 | 1.11 | -0.24 | 1.052 | 0.920 |
| XLE | NO EDGE | NORMAL | ETF | No | CAUTION | STATE_MISMATCH | 0.272 | 0.94 | +0.60 | 1.015 | 0.652 |
| XLI | NO EDGE | CAUTION | ETF | No | CAUTION | AGREE | 0.188 | 1.01 | +0.08 | 0.887 | 1.095 |
| XLV | NO EDGE | NORMAL | ETF | No | DANGER | STATE_MISMATCH | 0.178 | 1.01 | +0.01 | 0.976 | 0.786 |

---

## 2026-10-09 (Friday)

**Shadow summary:** Checked 330 / 75 agree / 124 V2_STRICTER / 1 V2_LOOSER / 128 state_mismatch / 2 nodata | index-gating v1 53% vs v2 97% | oscillation v1 1.21 vs v2 0.91 | warm 100% | day-flips v1 5/33 vs v2 1/33 | capture60 n=1933 mean -38 / v2-veto-neg 28% / v2-clear-neg 36% / σfwd-vs-rv30 MAE 0.28 vs 0.26 | veto-disagree 5%

| Ticker | v1 Action | v1 Regime | Earnings | v2 Eligible | v2 Gate | Divergence | sigma_fwd | FVRP | z | 1M/3M | accel_dn |
|--------|-----------|-----------|----------|-------------|---------|------------|-----------|------|------|-------|----------|
| AAPL | CONDITIONAL | NORMAL | 20d | No | DANGER | V2_STRICTER | 0.262 | 1.04 | +1.27 | 1.083 | 0.665 |
| AMZN | SELL PREMIUM | NORMAL | 20d | No | DANGER | V2_STRICTER | 0.309 | 1.29 | +1.43 | 1.157 | 0.952 |
| GOOG | SELL PREMIUM | NORMAL | 19d | No | DANGER | V2_STRICTER | 0.298 | 1.22 | +1.23 | 1.089 | 0.678 |
| HD | CONDITIONAL | NORMAL | 39d | No | NORMAL | V2_STRICTER | 0.267 | 1.13 | +0.87 | 1.005 | 0.696 |
| IWM | SELL PREMIUM | NORMAL | ETF | No | CAUTION | V2_STRICTER | 0.202 | 0.95 | +0.21 | 0.979 | 1.001 |
| MSFT | SELL PREMIUM | NORMAL | 19d | No | DANGER | V2_STRICTER | 0.284 | 1.12 | +0.64 | 1.116 | 0.763 |
| PLTR | CONDITIONAL | NORMAL | 24d | No | DANGER | V2_STRICTER | 0.581 | 0.98 | +1.06 | 1.134 | 0.371 |
| QQQ | CONDITIONAL | NORMAL | ETF | No | NORMAL | V2_STRICTER | 0.205 | 0.93 | -0.33 | 0.941 | 0.942 |
| SPY | CONDITIONAL | NORMAL | ETF | No | NORMAL | V2_STRICTER | 0.142 | 0.88 | -0.28 | 0.898 | 0.752 |
| TLT | SELL PREMIUM | NORMAL | ETF | No | CAUTION | V2_STRICTER | 0.133 | 1.11 | +2.00 | 1.020 | 0.883 |
| UBER | SELL PREMIUM | NORMAL | 25d | No | DANGER | V2_STRICTER | 0.371 | 1.15 | +1.89 | 1.170 | 0.599 |
| XLV | SELL PREMIUM | NORMAL | ETF | No | DANGER | V2_STRICTER | 0.183 | 1.19 | +1.18 | 1.204 | 0.844 |
| CAT | REDUCE SIZE | CAUTION | 20d | No | DANGER | STATE_MISMATCH | 0.397 | 1.14 | +0.55 | 1.173 | 1.322 |
| EEM | WATCHLIST | NORMAL | ETF | No | NORMAL | AGREE | 0.237 | 0.92 | -0.78 | 0.960 | 1.023 |
| GLD | NO EDGE | NORMAL | ETF | No | CAUTION | STATE_MISMATCH | 0.204 | 1.03 | -0.83 | 0.993 | 0.936 |
| GS | AVOID | DANGER | 4d | No | DANGER | AGREE | 0.300 | 1.09 | +1.03 | 1.056 | 0.758 |
| HOOD | NO EDGE | NORMAL | 18d | No | DANGER | STATE_MISMATCH | 0.677 | 0.94 | +0.62 | 1.072 | 0.839 |
| JNJ | AVOID | DANGER | 4d | No | DANGER | AGREE | 0.227 | 1.15 | +0.73 | 1.045 | 1.046 |
| JPM | AVOID | DANGER | 4d | No | CAUTION | STATE_MISMATCH | 0.253 | 1.05 | +1.24 | 1.059 | 0.823 |
| KO | REDUCE SIZE | CAUTION | 18d | No | DANGER | STATE_MISMATCH | 0.197 | 1.11 | +1.36 | 1.082 | 0.701 |
| MCD | WATCHLIST | NORMAL | 26d | No | CAUTION | STATE_MISMATCH | 0.219 | 1.12 | +0.94 | 1.021 | 0.813 |
| META | WATCHLIST | NORMAL | 19d | No | DANGER | STATE_MISMATCH | 0.359 | 1.23 | +1.50 | 1.167 | 0.928 |
| NFLX | CONDITIONAL | NORMAL | 11d | No | DANGER | STATE_MISMATCH | 0.353 | 1.24 | +1.50 | 1.140 | 0.749 |
| NKE | NO EDGE | CAUTION | 69d | No | NORMAL | STATE_MISMATCH | 0.366 | 0.94 | -0.60 | 0.835 | 0.906 |
| NVDA | NO EDGE | NORMAL | 40d | No | NORMAL | AGREE | 0.407 | 0.77 | -1.09 | 0.902 | 0.960 |
| SBUX | REDUCE SIZE | CAUTION | 19d | No | DANGER | STATE_MISMATCH | 0.361 | 1.16 | +0.43 | 1.303 | 1.122 |
| TSLA | NO EDGE | NORMAL | 12d | No | DANGER | STATE_MISMATCH | 0.453 | 0.96 | +1.03 | 1.079 | 0.559 |
| WMT | NO EDGE | CAUTION | 41d | No | NORMAL | STATE_MISMATCH | 0.236 | 1.00 | -0.35 | 0.854 | 0.666 |
| XLB | NO DATA | NORMAL | ETF | No | DANGER | NODATA_SKEW | — | — | — | — | — |
| XLE | NO EDGE | NORMAL | ETF | No | CAUTION | STATE_MISMATCH | 0.283 | 0.90 | +0.20 | 0.989 | 0.689 |
| XLF | NO EDGE | NORMAL | ETF | No | CAUTION | STATE_MISMATCH | 0.182 | 0.95 | +0.82 | 0.988 | 0.850 |
| XLI | NO EDGE | CAUTION | ETF | No | CAUTION | AGREE | 0.197 | 1.06 | +0.39 | 1.039 | 1.177 |
| XOM | NO EDGE | NORMAL | 21d | No | CAUTION | STATE_MISMATCH | 0.290 | 0.98 | +0.53 | 0.996 | 0.621 |

---

## 2026-10-08 (Thursday)

**Shadow summary:** Checked 330 / 86 agree / 119 V2_STRICTER / 1 V2_LOOSER / 122 state_mismatch / 2 nodata | index-gating v1 55% vs v2 97% | oscillation v1 1.15 vs v2 0.91 | warm 100% | day-flips v1 4/33 vs v2 2/33 | capture60 n=1932 mean -46 / v2-veto-neg 28% / v2-clear-neg 38% / σfwd-vs-rv30 MAE 0.28 vs 0.26 | veto-disagree 5%

| Ticker | v1 Action | v1 Regime | Earnings | v2 Eligible | v2 Gate | Divergence | sigma_fwd | FVRP | z | 1M/3M | accel_dn |
|--------|-----------|-----------|----------|-------------|---------|------------|-----------|------|------|-------|----------|
| AAPL | CONDITIONAL | NORMAL | 21d | No | CAUTION | V2_STRICTER | 0.271 | 0.98 | +0.81 | 1.068 | 0.715 |
| AMZN | SELL PREMIUM | NORMAL | 21d | No | DANGER | V2_STRICTER | 0.315 | 1.27 | +1.36 | 1.157 | 0.576 |
| EEM | CONDITIONAL | NORMAL | ETF | No | NORMAL | V2_STRICTER | 0.228 | 1.02 | -0.27 | 0.978 | 0.820 |
| GOOG | SELL PREMIUM | NORMAL | 20d | No | DANGER | V2_STRICTER | 0.281 | 1.31 | +1.68 | 1.113 | 0.684 |
| HD | CONDITIONAL | NORMAL | 40d | No | NORMAL | V2_STRICTER | 0.239 | 1.13 | +0.93 | 0.914 | 0.747 |
| IWM | SELL PREMIUM | NORMAL | ETF | No | CAUTION | V2_STRICTER | 0.206 | 0.94 | +0.16 | 0.994 | 1.075 |
| MCD | CONDITIONAL | NORMAL | 27d | No | CAUTION | V2_STRICTER | 0.202 | 1.19 | +1.41 | 1.016 | 0.873 |
| MSFT | SELL PREMIUM | NORMAL | 20d | No | DANGER | V2_STRICTER | 0.267 | 1.21 | +1.04 | 1.126 | 0.501 |
| NKE | CONDITIONAL | NORMAL | 70d | No | NORMAL | V2_STRICTER | 0.379 | 0.91 | -0.75 | 0.858 | 0.973 |
| PLTR | CONDITIONAL | NORMAL | 25d | No | DANGER | V2_STRICTER | 0.513 | 1.10 | +1.84 | 1.121 | 0.398 |
| QQQ | CONDITIONAL | NORMAL | ETF | No | NORMAL | V2_STRICTER | 0.187 | 1.05 | +0.82 | 0.953 | 0.520 |
| SBUX | SELL PREMIUM | NORMAL | 20d | No | DANGER | V2_STRICTER | 0.282 | 1.45 | +1.35 | 1.365 | 1.197 |
| SPY | CONDITIONAL | NORMAL | ETF | No | NORMAL | V2_STRICTER | 0.140 | 0.95 | +0.34 | 0.924 | 0.666 |
| TLT | SELL PREMIUM | NORMAL | ETF | No | CAUTION | V2_STRICTER | 0.141 | 1.07 | +1.75 | 1.020 | 0.948 |
| UBER | SELL PREMIUM | NORMAL | 26d | No | DANGER | V2_STRICTER | 0.357 | 1.23 | +2.35 | 1.209 | 0.644 |
| XLB | CONDITIONAL | NORMAL | ETF | No | DANGER | V2_STRICTER | 0.199 | 1.10 | -0.26 | 1.014 | 1.061 |
| XLE | CONDITIONAL | NORMAL | ETF | No | CAUTION | V2_STRICTER | 0.270 | 0.96 | +0.81 | 1.004 | 0.740 |
| XLF | CONDITIONAL | NORMAL | ETF | No | CAUTION | V2_STRICTER | 0.182 | 0.89 | +0.22 | 0.950 | 0.913 |
| XLV | CONDITIONAL | NORMAL | ETF | No | DANGER | V2_STRICTER | 0.178 | 1.09 | +0.58 | 1.147 | 0.873 |
| XOM | CONDITIONAL | NORMAL | 22d | No | CAUTION | V2_STRICTER | 0.277 | 1.03 | +1.03 | 1.021 | 0.667 |
| CAT | REDUCE SIZE | CAUTION | 21d | No | DANGER | STATE_MISMATCH | 0.397 | 1.13 | +0.47 | 1.167 | 1.360 |
| GLD | NO EDGE | NORMAL | ETF | No | CAUTION | STATE_MISMATCH | 0.215 | 0.99 | -1.07 | 0.995 | 1.006 |
| GS | NO EDGE | CAUTION | 5d | No | DANGER | STATE_MISMATCH | 0.316 | 1.03 | +0.50 | 1.050 | 0.799 |
| HOOD | NO EDGE | NORMAL | 19d | No | DANGER | STATE_MISMATCH | 0.672 | 0.92 | +0.40 | 1.072 | 0.797 |
| JNJ | AVOID | DANGER | 5d | No | DANGER | AGREE | 0.214 | 1.20 | +1.14 | 1.051 | 1.076 |
| JPM | NO EDGE | CAUTION | 5d | No | CAUTION | AGREE | 0.250 | 1.03 | +1.09 | 1.037 | 0.884 |
| KO | SELL PREMIUM | NORMAL | 19d | No | DANGER | STATE_MISMATCH | 0.191 | 1.16 | +1.67 | 1.107 | 0.753 |
| META | WATCHLIST | NORMAL | 20d | No | DANGER | STATE_MISMATCH | 0.354 | 1.25 | +1.57 | 1.169 | 0.997 |
| NFLX | SELL PREMIUM | NORMAL | 12d | No | DANGER | STATE_MISMATCH | 0.340 | 1.35 | +1.87 | 1.200 | 0.804 |
| NVDA | NO EDGE | NORMAL | 41d | No | NORMAL | AGREE | 0.371 | 0.83 | -0.53 | 0.889 | 0.466 |
| TSLA | NO EDGE | NORMAL | 13d | No | DANGER | STATE_MISMATCH | 0.454 | 0.96 | +1.02 | 1.071 | 0.577 |
| WMT | NO EDGE | CAUTION | 42d | No | NORMAL | STATE_MISMATCH | 0.229 | 0.95 | -0.60 | 0.822 | 0.716 |
| XLI | NO EDGE | CAUTION | ETF | No | CAUTION | AGREE | 0.205 | 1.09 | +0.60 | 1.009 | 1.264 |

---

## 2026-10-07 (Wednesday)

**Shadow summary:** Checked 330 / 96 agree / 105 V2_STRICTER / 1 V2_LOOSER / 125 state_mismatch / 3 nodata | index-gating v1 61% vs v2 97% | oscillation v1 1.06 vs v2 1.03 | warm 100% | day-flips v1 4/33 vs v2 4/33 | capture60 n=1932 mean -53 / v2-veto-neg 29% / v2-clear-neg 38% / σfwd-vs-rv30 MAE 0.27 vs 0.26 | veto-disagree 5%

| Ticker | v1 Action | v1 Regime | Earnings | v2 Eligible | v2 Gate | Divergence | sigma_fwd | FVRP | z | 1M/3M | accel_dn |
|--------|-----------|-----------|----------|-------------|---------|------------|-----------|------|------|-------|----------|
| AAPL | CONDITIONAL | NORMAL | 22d | No | CAUTION | V2_STRICTER | 0.257 | 1.02 | +1.08 | 1.050 | 0.768 |
| AMZN | SELL PREMIUM | NORMAL | 22d | No | DANGER | V2_STRICTER | 0.318 | 1.24 | +1.23 | 1.149 | 0.619 |
| HD | CONDITIONAL | NORMAL | 41d | No | NORMAL | V2_STRICTER | 0.253 | 1.05 | +0.35 | 0.904 | 0.794 |
| IWM | CONDITIONAL | NORMAL | ETF | No | CAUTION | V2_STRICTER | 0.198 | 0.99 | +0.69 | 1.004 | 0.844 |
| MSFT | SELL PREMIUM | NORMAL | 21d | No | DANGER | V2_STRICTER | 0.283 | 1.14 | +0.71 | 1.134 | 0.538 |
| NKE | CONDITIONAL | NORMAL | 71d | No | CAUTION | V2_STRICTER | 0.408 | 0.85 | -1.02 | 0.879 | 1.026 |
| PLTR | CONDITIONAL | NORMAL | 26d | No | DANGER | V2_STRICTER | 0.530 | 1.06 | +1.64 | 1.127 | 0.428 |
| QQQ | CONDITIONAL | NORMAL | ETF | No | NORMAL | V2_STRICTER | 0.184 | 1.03 | +0.70 | 0.934 | 0.531 |
| SBUX | SELL PREMIUM | NORMAL | 21d | No | DANGER | V2_STRICTER | 0.275 | 1.42 | +1.25 | 1.352 | 0.720 |
| SPY | CONDITIONAL | NORMAL | ETF | No | NORMAL | V2_STRICTER | 0.140 | 0.93 | +0.19 | 0.915 | 0.666 |
| TLT | SELL PREMIUM | NORMAL | ETF | No | CAUTION | V2_STRICTER | 0.129 | 1.19 | +2.70 | 1.015 | 1.011 |
| UBER | SELL PREMIUM | NORMAL | 27d | No | DANGER | V2_STRICTER | 0.370 | 1.07 | +1.49 | 1.081 | 0.632 |
| XLE | CONDITIONAL | NORMAL | ETF | No | CAUTION | V2_STRICTER | 0.270 | 0.97 | +0.94 | 1.011 | 0.733 |
| XLF | CONDITIONAL | NORMAL | ETF | No | CAUTION | V2_STRICTER | 0.173 | 0.99 | +1.09 | 0.999 | 0.933 |
| XLV | CONDITIONAL | NORMAL | ETF | No | DANGER | V2_STRICTER | 0.178 | 1.00 | -0.00 | 0.937 | 0.938 |
| CAT | REDUCE SIZE | CAUTION | 22d | No | DANGER | STATE_MISMATCH | 0.365 | 1.21 | +0.98 | 1.121 | 0.518 |
| EEM | WATCHLIST | NORMAL | ETF | No | NORMAL | AGREE | 0.205 | 1.09 | +0.09 | 0.958 | 0.691 |
| GLD | NO EDGE | NORMAL | ETF | No | CAUTION | STATE_MISMATCH | 0.187 | 1.13 | -0.09 | 0.992 | 0.926 |
| GOOG | REDUCE SIZE | CAUTION | 21d | No | DANGER | STATE_MISMATCH | 0.283 | 1.26 | +1.38 | 1.114 | 0.735 |
| GS | NO EDGE | CAUTION | 6d | No | DANGER | STATE_MISMATCH | 0.289 | 1.18 | +1.76 | 1.069 | 0.792 |
| HOOD | NO EDGE | NORMAL | 20d | No | DANGER | STATE_MISMATCH | 0.660 | 0.93 | +0.50 | 1.058 | 0.751 |
| JNJ | REDUCE SIZE | CAUTION | 6d | No | DANGER | STATE_MISMATCH | 0.211 | 1.21 | +1.16 | 1.038 | 1.156 |
| JPM | REDUCE SIZE | CAUTION | 6d | No | CAUTION | AGREE | 0.232 | 1.13 | +1.90 | 1.052 | 0.923 |
| KO | SELL PREMIUM | NORMAL | 20d | No | DANGER | STATE_MISMATCH | 0.191 | 1.14 | +1.58 | 1.071 | 0.765 |
| MCD | NO EDGE | CAUTION | 28d | No | NORMAL | STATE_MISMATCH | 0.201 | 1.23 | +1.63 | 1.026 | 0.908 |
| META | WATCHLIST | NORMAL | 21d | No | DANGER | STATE_MISMATCH | 0.367 | 1.17 | +1.27 | 1.145 | 0.911 |
| NFLX | CONDITIONAL | NORMAL | 13d | No | DANGER | STATE_MISMATCH | 0.341 | 1.29 | +1.68 | 1.141 | 0.864 |
| NVDA | NO EDGE | NORMAL | 42d | No | NORMAL | AGREE | 0.393 | 0.75 | -1.38 | 0.864 | 0.435 |
| TSLA | NO EDGE | NORMAL | 14d | No | DANGER | STATE_MISMATCH | 0.470 | 0.91 | +0.56 | 1.070 | 0.597 |
| WMT | NO EDGE | CAUTION | 43d | No | NORMAL | STATE_MISMATCH | 0.240 | 0.97 | -0.48 | 0.868 | 0.769 |
| XLB | NO DATA | NORMAL | ETF | No | DANGER | NODATA_SKEW | — | — | — | — | — |
| XLI | NO EDGE | NORMAL | ETF | No | CAUTION | STATE_MISMATCH | 0.188 | 0.99 | -0.05 | 0.956 | 0.737 |
| XOM | NO EDGE | NORMAL | 23d | No | CAUTION | STATE_MISMATCH | 0.278 | 1.02 | +0.93 | 1.011 | 0.708 |

---

## 2026-10-06 (Tuesday)

**Shadow summary:** Checked 330 / 111 agree / 93 V2_STRICTER / 1 V2_LOOSER / 123 state_mismatch / 2 nodata | index-gating v1 65% vs v2 97% | oscillation v1 1.06 vs v2 1.00 | warm 100% | day-flips v1 7/33 vs v2 4/33 | capture60 n=1932 mean -60 / v2-veto-neg 29% / v2-clear-neg 38% / σfwd-vs-rv30 MAE 0.27 vs 0.25 | veto-disagree 5%

| Ticker | v1 Action | v1 Regime | Earnings | v2 Eligible | v2 Gate | Divergence | sigma_fwd | FVRP | z | 1M/3M | accel_dn |
|--------|-----------|-----------|----------|-------------|---------|------------|-----------|------|------|-------|----------|
| AAPL | CONDITIONAL | NORMAL | 23d | No | CAUTION | V2_STRICTER | 0.272 | 0.96 | +0.63 | 1.044 | 0.825 |
| AMZN | SELL PREMIUM | NORMAL | 23d | No | DANGER | V2_STRICTER | 0.318 | 1.24 | +1.22 | 1.163 | 0.665 |
| CAT | SELL PREMIUM | NORMAL | 23d | No | DANGER | V2_STRICTER | 0.380 | 1.16 | +0.64 | 1.163 | 0.556 |
| EEM | CONDITIONAL | NORMAL | ETF | No | NORMAL | V2_STRICTER | 0.223 | 1.07 | -0.02 | 0.986 | 0.687 |
| IWM | CONDITIONAL | NORMAL | ETF | No | CAUTION | V2_STRICTER | 0.206 | 0.93 | +0.06 | 0.987 | 0.776 |
| MSFT | SELL PREMIUM | NORMAL | 22d | No | DANGER | V2_STRICTER | 0.289 | 1.14 | +0.73 | 1.156 | 0.578 |
| NKE | CONDITIONAL | NORMAL | 72d | No | CAUTION | V2_STRICTER | 0.441 | 0.81 | -1.24 | 0.888 | 1.103 |
| PLTR | CONDITIONAL | NORMAL | 27d | No | NORMAL | V2_STRICTER | 0.546 | 1.00 | +1.27 | 1.103 | 0.459 |
| QQQ | CONDITIONAL | NORMAL | ETF | No | NORMAL | V2_STRICTER | 0.191 | 0.99 | +0.29 | 0.931 | 0.570 |
| SBUX | SELL PREMIUM | NORMAL | 22d | No | DANGER | V2_STRICTER | 0.253 | 1.39 | +1.17 | 1.193 | 0.774 |
| SPY | CONDITIONAL | NORMAL | ETF | No | NORMAL | V2_STRICTER | 0.145 | 0.88 | -0.31 | 0.912 | 0.715 |
| TLT | SELL PREMIUM | NORMAL | ETF | No | CAUTION | V2_STRICTER | 0.137 | 1.20 | +2.80 | 1.030 | 1.086 |
| UBER | SELL PREMIUM | NORMAL | 28d | No | NORMAL | V2_STRICTER | 0.383 | 1.03 | +1.27 | 1.065 | 0.657 |
| XLE | CONDITIONAL | NORMAL | ETF | No | CAUTION | V2_STRICTER | 0.280 | 0.91 | +0.29 | 0.977 | 0.788 |
| XLI | CONDITIONAL | NORMAL | ETF | No | CAUTION | V2_STRICTER | 0.196 | 1.05 | +0.32 | 1.043 | 0.792 |
| XLV | CONDITIONAL | NORMAL | ETF | No | DANGER | V2_STRICTER | 0.166 | 1.18 | +1.16 | 1.086 | 1.003 |
| GLD | NO EDGE | NORMAL | ETF | No | CAUTION | STATE_MISMATCH | 0.190 | 1.11 | -0.24 | 0.985 | 0.994 |
| GOOG | REDUCE SIZE | CAUTION | 22d | No | DANGER | STATE_MISMATCH | 0.303 | 1.14 | +0.79 | 1.080 | 0.789 |
| GS | NO EDGE | NORMAL | 7d | No | DANGER | STATE_MISMATCH | 0.299 | 1.12 | +1.28 | 1.062 | 0.851 |
| HD | NO EDGE | CAUTION | 42d | No | NORMAL | STATE_MISMATCH | 0.260 | 1.06 | +0.40 | 0.960 | 0.853 |
| HOOD | NO EDGE | NORMAL | 21d | No | CAUTION | STATE_MISMATCH | 0.690 | 0.91 | +0.29 | 1.073 | 0.730 |
| JNJ | REDUCE SIZE | CAUTION | 7d | No | DANGER | STATE_MISMATCH | 0.202 | 1.32 | +1.95 | 1.065 | 1.241 |
| JPM | NO EDGE | CAUTION | 7d | No | CAUTION | AGREE | 0.238 | 1.06 | +1.33 | 1.014 | 0.992 |
| KO | SELL PREMIUM | NORMAL | 21d | No | CAUTION | STATE_MISMATCH | 0.196 | 1.13 | +1.47 | 1.103 | 0.782 |
| MCD | NO EDGE | CAUTION | 29d | No | NORMAL | STATE_MISMATCH | 0.210 | 1.13 | +1.00 | 0.967 | 0.971 |
| META | WATCHLIST | NORMAL | 22d | No | DANGER | STATE_MISMATCH | 0.387 | 1.13 | +1.09 | 1.150 | 0.974 |
| NFLX | SELL PREMIUM | NORMAL | 14d | No | DANGER | STATE_MISMATCH | 0.344 | 1.31 | +1.73 | 1.149 | 0.928 |
| NVDA | NO EDGE | NORMAL | 43d | No | NORMAL | AGREE | 0.400 | 0.72 | -1.67 | 0.856 | 0.468 |
| TSLA | NO EDGE | NORMAL | 15d | No | DANGER | STATE_MISMATCH | 0.504 | 0.88 | +0.23 | 1.074 | 0.641 |
| WMT | NO EDGE | CAUTION | 44d | No | NORMAL | STATE_MISMATCH | 0.234 | 1.02 | -0.21 | 0.890 | 0.826 |
| XLB | NO EDGE | CAUTION | ETF | No | DANGER | STATE_MISMATCH | 0.210 | 1.05 | -0.46 | 1.128 | 0.814 |
| XLF | NO EDGE | NORMAL | ETF | No | CAUTION | STATE_MISMATCH | 0.181 | 0.83 | -0.41 | 0.894 | 1.002 |
| XOM | NO EDGE | NORMAL | 24d | No | CAUTION | STATE_MISMATCH | 0.285 | 1.03 | +0.96 | 1.042 | 0.761 |

---

## 2026-10-05 (Monday)

**Shadow summary:** Checked 33 / 5 agree / 11 V2_STRICTER / 0 V2_LOOSER / 17 state_mismatch / 0 nodata | index-gating v1 73% vs v2 100% | oscillation v1 — vs v2 — | warm 100% | day-flips v1 4/33 vs v2 1/33 | capture60 n=1932 mean -60 / v2-veto-neg 29% / v2-clear-neg 38% / σfwd-vs-rv30 MAE 0.27 vs 0.25 | veto-disagree 6%

| Ticker | v1 Action | v1 Regime | Earnings | v2 Eligible | v2 Gate | Divergence | sigma_fwd | FVRP | z | 1M/3M | accel_dn |
|--------|-----------|-----------|----------|-------------|---------|------------|-----------|------|------|-------|----------|
| AMZN | SELL PREMIUM | NORMAL | 24d | No | DANGER | V2_STRICTER | 0.324 | 1.18 | +1.00 | 1.142 | 0.714 |
| CAT | SELL PREMIUM | NORMAL | 24d | No | DANGER | V2_STRICTER | 0.364 | 1.20 | +0.92 | 1.136 | 0.598 |
| IWM | CONDITIONAL | NORMAL | ETF | No | CAUTION | V2_STRICTER | 0.209 | 0.89 | -0.48 | 0.970 | 0.834 |
| KO | SELL PREMIUM | NORMAL | 22d | No | CAUTION | V2_STRICTER | 0.190 | 1.08 | +1.10 | 1.041 | 0.840 |
| MSFT | SELL PREMIUM | NORMAL | 23d | No | DANGER | V2_STRICTER | 0.290 | 1.12 | +0.63 | 1.148 | 0.621 |
| NFLX | SELL PREMIUM | NORMAL | 15d | No | DANGER | V2_STRICTER | 0.353 | 1.25 | +1.54 | 1.159 | 0.997 |
| SBUX | SELL PREMIUM | NORMAL | 23d | No | DANGER | V2_STRICTER | 0.245 | 1.66 | +1.89 | 1.363 | 0.821 |
| UBER | CONDITIONAL | NORMAL | 29d | No | NORMAL | V2_STRICTER | 0.381 | 0.97 | +0.87 | 1.004 | 0.705 |
| XLE | CONDITIONAL | NORMAL | ETF | No | CAUTION | V2_STRICTER | 0.271 | 1.01 | +1.24 | 1.027 | 0.846 |
| XLI | CONDITIONAL | NORMAL | ETF | No | CAUTION | V2_STRICTER | 0.195 | 1.02 | +0.16 | 0.970 | 0.851 |
| XOM | CONDITIONAL | NORMAL | 25d | No | CAUTION | V2_STRICTER | 0.286 | 1.04 | +1.14 | 1.034 | 0.817 |
| AAPL | NO EDGE | NORMAL | 24d | No | CAUTION | STATE_MISMATCH | 0.281 | 0.91 | +0.24 | 1.021 | 0.881 |
| EEM | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.219 | 1.02 | -0.24 | 0.969 | 0.737 |
| GLD | NO EDGE | NORMAL | ETF | No | CAUTION | STATE_MISMATCH | 0.201 | 1.05 | -0.64 | 0.977 | 1.067 |
| GOOG | REDUCE SIZE | CAUTION | 30d | No | DANGER | STATE_MISMATCH | 0.321 | 1.09 | +0.45 | 1.080 | 0.848 |
| GS | NO EDGE | CAUTION | 8d | No | DANGER | STATE_MISMATCH | 0.300 | 1.14 | +1.40 | 1.039 | 0.868 |
| HD | REDUCE SIZE | CAUTION | 43d | No | NORMAL | STATE_MISMATCH | 0.275 | 1.08 | +0.56 | 0.974 | 0.893 |
| HOOD | NO EDGE | NORMAL | 22d | No | CAUTION | STATE_MISMATCH | 0.721 | 0.85 | -0.36 | 1.040 | 0.784 |
| JNJ | SELL PREMIUM | NORMAL | 8d | No | DANGER | STATE_MISMATCH | 0.207 | 1.22 | +1.27 | 0.979 | 1.249 |
| JPM | NO EDGE | CAUTION | 8d | No | DANGER | STATE_MISMATCH | 0.248 | 1.02 | +0.94 | 1.006 | 1.065 |
| MCD | NO EDGE | CAUTION | 31d | No | CAUTION | AGREE | 0.202 | 1.12 | +0.94 | 0.932 | 1.043 |
| META | NO EDGE | CAUTION | 23d | No | DANGER | STATE_MISMATCH | 0.394 | 1.08 | +0.87 | 1.125 | 1.046 |
| NKE | NO EDGE | NORMAL | 73d | No | DANGER | STATE_MISMATCH | 0.464 | 0.73 | -1.70 | — | 1.184 |
| NVDA | NO EDGE | NORMAL | 44d | No | NORMAL | AGREE | 0.411 | 0.70 | -1.96 | 0.845 | 0.502 |
| PLTR | NO EDGE | NORMAL | 28d | No | NORMAL | AGREE | 0.556 | 0.93 | +0.78 | 1.025 | 0.493 |
| QQQ | NO EDGE | CAUTION | ETF | No | NORMAL | STATE_MISMATCH | 0.203 | 0.92 | -0.46 | 0.924 | 0.613 |
| SPY | NO EDGE | CAUTION | ETF | No | NORMAL | STATE_MISMATCH | 0.151 | 0.83 | -0.72 | 0.904 | 0.768 |
| TLT | REDUCE SIZE | CAUTION | ETF | No | CAUTION | AGREE | 0.140 | 1.18 | +2.71 | 1.041 | 1.118 |
| TSLA | NO EDGE | NORMAL | 16d | No | DANGER | STATE_MISMATCH | 0.490 | 0.88 | +0.21 | 1.052 | 0.689 |
| WMT | NO EDGE | CAUTION | 45d | No | NORMAL | STATE_MISMATCH | 0.236 | 0.98 | -0.43 | 0.842 | 0.887 |
| XLB | NO EDGE | NORMAL | ETF | No | CAUTION | STATE_MISMATCH | 0.198 | 0.99 | -0.71 | 1.170 | 0.874 |
| XLF | NO EDGE | NORMAL | ETF | No | CAUTION | STATE_MISMATCH | 0.181 | 0.91 | +0.37 | 0.963 | 1.077 |
| XLV | NO EDGE | NORMAL | ETF | No | DANGER | STATE_MISMATCH | 0.165 | 1.06 | +0.37 | 0.947 | 1.077 |

---

## 2026-10-02 (Friday)

**Shadow summary:** Checked 330 / 137 agree / 79 V2_STRICTER / 1 V2_LOOSER / 111 state_mismatch / 2 nodata | index-gating v1 70% vs v2 97% | oscillation v1 1.00 vs v2 1.06 | warm 100% | day-flips v1 5/33 vs v2 5/33 | capture60 n=1933 mean -73 / v2-veto-neg 30% / v2-clear-neg 38% / σfwd-vs-rv30 MAE 0.26 vs 0.25 | veto-disagree 4%

| Ticker | v1 Action | v1 Regime | Earnings | v2 Eligible | v2 Gate | Divergence | sigma_fwd | FVRP | z | 1M/3M | accel_dn |
|--------|-----------|-----------|----------|-------------|---------|------------|-----------|------|------|-------|----------|
| AAPL | CONDITIONAL | NORMAL | 27d | No | CAUTION | V2_STRICTER | 0.291 | 0.90 | +0.12 | 1.027 | 0.947 |
| AMZN | SELL PREMIUM | NORMAL | 27d | No | DANGER | V2_STRICTER | 0.325 | 1.21 | +1.09 | 1.112 | 0.767 |
| CAT | SELL PREMIUM | NORMAL | 27d | No | DANGER | V2_STRICTER | 0.355 | 1.24 | +1.15 | 1.109 | 0.642 |
| IWM | CONDITIONAL | NORMAL | ETF | No | CAUTION | V2_STRICTER | 0.202 | 0.97 | +0.42 | 1.001 | 0.895 |
| KO | SELL PREMIUM | NORMAL | 25d | No | CAUTION | V2_STRICTER | 0.186 | 1.14 | +1.55 | 1.018 | 0.842 |
| MSFT | SELL PREMIUM | NORMAL | 26d | No | DANGER | V2_STRICTER | 0.292 | 1.14 | +0.72 | 1.104 | 0.667 |
| NFLX | CONDITIONAL | NORMAL | 18d | No | DANGER | V2_STRICTER | 0.361 | 1.24 | +1.49 | 1.161 | 1.039 |
| SBUX | SELL PREMIUM | NORMAL | 26d | No | CAUTION | V2_STRICTER | 0.254 | 1.35 | +1.04 | 1.078 | 0.879 |
| UBER | CONDITIONAL | NORMAL | 32d | No | NORMAL | V2_STRICTER | 0.384 | 0.94 | +0.66 | 0.949 | 0.758 |
| XLE | CONDITIONAL | NORMAL | ETF | No | CAUTION | V2_STRICTER | 0.265 | 1.00 | +1.19 | 1.008 | 0.909 |
| XLF | CONDITIONAL | NORMAL | ETF | No | CAUTION | V2_STRICTER | 0.186 | 0.93 | +0.59 | 0.973 | 1.157 |
| XLI | SELL PREMIUM | NORMAL | ETF | No | CAUTION | V2_STRICTER | 0.188 | 1.09 | +0.55 | 1.032 | 0.914 |
| XLV | CONDITIONAL | NORMAL | ETF | No | DANGER | V2_STRICTER | 0.171 | 1.22 | +1.38 | 1.166 | 1.157 |
| XOM | CONDITIONAL | NORMAL | 28d | No | CAUTION | V2_STRICTER | 0.281 | 1.05 | +1.24 | 1.010 | 0.878 |
| EEM | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.206 | 1.15 | +0.36 | 0.902 | 0.792 |
| GLD | NO EDGE | NORMAL | ETF | No | CAUTION | STATE_MISMATCH | 0.200 | 1.05 | -0.63 | 0.972 | 1.126 |
| GOOG | REDUCE SIZE | CAUTION | 33d | No | DANGER | STATE_MISMATCH | 0.343 | 1.04 | +0.19 | 1.061 | 0.911 |
| GS | CONDITIONAL | NORMAL | 11d | No | DANGER | STATE_MISMATCH | 0.297 | 1.14 | +1.40 | 1.045 | 0.932 |
| HD | NO EDGE | CAUTION | 46d | No | NORMAL | STATE_MISMATCH | 0.264 | 1.04 | +0.28 | 0.863 | 0.959 |
| HOOD | NO EDGE | NORMAL | 25d | No | CAUTION | STATE_MISMATCH | 0.708 | 0.87 | -0.21 | 1.013 | 0.843 |
| JNJ | SELL PREMIUM | NORMAL | 11d | No | DANGER | STATE_MISMATCH | 0.213 | 1.27 | +1.62 | 1.041 | 1.283 |
| JPM | REDUCE SIZE | CAUTION | 11d | No | DANGER | STATE_MISMATCH | 0.256 | 1.05 | +1.17 | 1.068 | 1.141 |
| MCD | NO EDGE | CAUTION | 34d | No | CAUTION | AGREE | 0.211 | 1.07 | +0.64 | 0.936 | 1.121 |
| META | NO EDGE | CAUTION | 26d | No | DANGER | STATE_MISMATCH | 0.398 | 1.13 | +1.08 | 1.120 | 1.124 |
| NKE | AVOID | DANGER | 76d | No | DANGER | AGREE | 0.338 | 1.52 | +1.51 | — | 0.765 |
| NVDA | NO EDGE | NORMAL | 47d | No | NORMAL | AGREE | 0.386 | 0.79 | -0.95 | 0.873 | 0.540 |
| PLTR | NO EDGE | NORMAL | 31d | No | NORMAL | AGREE | 0.548 | 0.89 | +0.44 | 0.901 | 0.502 |
| QQQ | NO EDGE | CAUTION | ETF | No | NORMAL | STATE_MISMATCH | 0.188 | 1.03 | +0.66 | 0.936 | 0.658 |
| SPY | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.142 | 0.94 | +0.28 | 0.934 | 0.825 |
| TLT | REDUCE SIZE | CAUTION | ETF | No | CAUTION | AGREE | 0.141 | 1.22 | +3.01 | 1.039 | 1.185 |
| TSLA | NO EDGE | NORMAL | 19d | No | DANGER | STATE_MISMATCH | 0.447 | 1.02 | +1.41 | 1.084 | 0.740 |
| WMT | NO EDGE | NORMAL | 48d | No | NORMAL | AGREE | 0.242 | 0.98 | -0.47 | 0.826 | 0.953 |
| XLB | NO EDGE | NORMAL | ETF | No | CAUTION | STATE_MISMATCH | 0.203 | 0.98 | -0.76 | 1.000 | 0.939 |

---

## 2026-09-30 (Wednesday)

**Shadow summary:** Checked 330 / 151 agree / 63 V2_STRICTER / 1 V2_LOOSER / 113 state_mismatch / 2 nodata | index-gating v1 75% vs v2 98% | oscillation v1 1.18 vs v2 0.94 | warm 100% | day-flips v1 2/33 vs v2 6/33 | capture60 n=1932 mean -83 / v2-veto-neg 30% / v2-clear-neg 38% / σfwd-vs-rv30 MAE 0.26 vs 0.25 | veto-disagree 5%

| Ticker | v1 Action | v1 Regime | Earnings | v2 Eligible | v2 Gate | Divergence | sigma_fwd | FVRP | z | 1M/3M | accel_dn |
|--------|-----------|-----------|----------|-------------|---------|------------|-----------|------|------|-------|----------|
| AMZN | SELL PREMIUM | NORMAL | 29d | No | DANGER | V2_STRICTER | 0.315 | 1.27 | +1.36 | 1.119 | 0.874 |
| CAT | SELL PREMIUM | NORMAL | 29d | No | DANGER | V2_STRICTER | 0.339 | 1.35 | +1.78 | 1.174 | 0.528 |
| IWM | CONDITIONAL | NORMAL | ETF | No | CAUTION | V2_STRICTER | 0.198 | 1.00 | +0.74 | 0.999 | 1.006 |
| KO | SELL PREMIUM | NORMAL | 27d | No | CAUTION | V2_STRICTER | 0.188 | 1.13 | +1.44 | 1.001 | 0.816 |
| NFLX | CONDITIONAL | NORMAL | 20d | No | DANGER | V2_STRICTER | 0.393 | 1.12 | +1.03 | 1.160 | 1.015 |
| SBUX | SELL PREMIUM | NORMAL | 28d | No | CAUTION | V2_STRICTER | 0.276 | 1.18 | +0.52 | 1.059 | 0.782 |
| XLF | CONDITIONAL | NORMAL | ETF | No | DANGER | V2_STRICTER | 0.181 | 1.03 | +1.41 | 1.071 | 1.187 |
| AAPL | NO EDGE | NORMAL | 29d | No | CAUTION | STATE_MISMATCH | 0.271 | 0.97 | +0.73 | 1.036 | 1.048 |
| EEM | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.217 | 1.08 | +0.03 | 0.949 | 0.847 |
| GLD | NO EDGE | NORMAL | ETF | No | CAUTION | STATE_MISMATCH | 0.234 | 0.94 | -1.50 | 0.992 | 1.291 |
| GOOG | REDUCE SIZE | CAUTION | 35d | No | DANGER | STATE_MISMATCH | 0.278 | 1.27 | +1.45 | 1.084 | 0.884 |
| GS | CONDITIONAL | NORMAL | 13d | No | DANGER | STATE_MISMATCH | 0.295 | 1.22 | +2.06 | 1.095 | 0.964 |
| HD | NO EDGE | NORMAL | 48d | No | CAUTION | STATE_MISMATCH | 0.256 | 1.09 | +0.62 | 0.913 | 1.002 |
| HOOD | NO EDGE | NORMAL | 35d | No | NORMAL | AGREE | 0.659 | 0.94 | +0.61 | 0.995 | 0.764 |
| JNJ | CONDITIONAL | NORMAL | 13d | No | DANGER | STATE_MISMATCH | 0.229 | 1.15 | +0.76 | 1.012 | 0.898 |
| JPM | NO EDGE | CAUTION | 13d | No | DANGER | STATE_MISMATCH | 0.246 | 1.08 | +1.41 | 1.037 | 1.237 |
| MCD | NO EDGE | CAUTION | 36d | No | CAUTION | AGREE | 0.226 | 1.00 | +0.09 | 0.948 | 1.237 |
| META | NO EDGE | CAUTION | 28d | No | DANGER | STATE_MISMATCH | 0.431 | 1.08 | +0.90 | 1.130 | 1.242 |
| MSFT | REDUCE SIZE | CAUTION | 28d | No | DANGER | STATE_MISMATCH | 0.307 | 1.11 | +0.59 | 1.123 | 0.769 |
| NKE | AVOID | DANGER | 1d | No | DANGER | AGREE | 0.330 | 1.51 | +1.48 | 1.115 | 0.765 |
| NVDA | NO EDGE | NORMAL | 49d | No | NORMAL | AGREE | 0.413 | 0.75 | -1.37 | 0.870 | 0.623 |
| PLTR | NO EDGE | NORMAL | 33d | No | NORMAL | AGREE | 0.545 | 0.84 | +0.07 | 0.845 | 0.580 |
| QQQ | NO EDGE | CAUTION | ETF | No | NORMAL | STATE_MISMATCH | 0.192 | 1.01 | +0.47 | 0.940 | 0.759 |
| SPY | NO EDGE | CAUTION | ETF | No | NORMAL | STATE_MISMATCH | 0.138 | 1.01 | +0.83 | 0.945 | 0.933 |
| TLT | AVOID | DANGER | ETF | No | CAUTION | STATE_MISMATCH | 0.133 | 1.24 | +3.34 | 1.055 | 1.320 |
| TSLA | NO EDGE | NORMAL | 21d | No | DANGER | STATE_MISMATCH | 0.476 | 0.94 | +0.70 | 1.070 | 0.853 |
| UBER | NO EDGE | NORMAL | 34d | No | NORMAL | AGREE | 0.390 | 0.89 | +0.34 | 0.900 | 0.755 |
| WMT | NO EDGE | NORMAL | 50d | No | NORMAL | AGREE | 0.259 | 0.87 | -1.15 | 0.804 | 0.822 |
| XLB | NO EDGE | NORMAL | ETF | No | DANGER | STATE_MISMATCH | 0.200 | 1.12 | -0.21 | 1.132 | 0.973 |
| XLE | NO EDGE | NORMAL | ETF | No | CAUTION | STATE_MISMATCH | 0.285 | 0.90 | +0.24 | 1.006 | 1.048 |
| XLI | SELL PREMIUM | NORMAL | ETF | Yes | NORMAL | AGREE | 0.189 | 1.30 | +1.67 | 1.091 | 0.782 |
| XLV | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.174 | 1.01 | +0.03 | 1.029 | 0.629 |
| XOM | NO EDGE | NORMAL | 30d | No | CAUTION | STATE_MISMATCH | 0.301 | 0.99 | +0.61 | 1.005 | 1.013 |

---

## 2026-09-29 (Tuesday)

**Shadow summary:** Checked 330 / 157 agree / 62 V2_STRICTER / 1 V2_LOOSER / 108 state_mismatch / 2 nodata | index-gating v1 75% vs v2 99% | oscillation v1 1.30 vs v2 0.82 | warm 100% | day-flips v1 6/33 vs v2 6/33 | capture60 n=1932 mean -89 / v2-veto-neg 30% / v2-clear-neg 33% / σfwd-vs-rv30 MAE 0.26 vs 0.25 | veto-disagree 5%

| Ticker | v1 Action | v1 Regime | Earnings | v2 Eligible | v2 Gate | Divergence | sigma_fwd | FVRP | z | 1M/3M | accel_dn |
|--------|-----------|-----------|----------|-------------|---------|------------|-----------|------|------|-------|----------|
| AAPL | CONDITIONAL | NORMAL | 30d | No | NORMAL | V2_STRICTER | 0.257 | 1.03 | +1.15 | 1.021 | 0.523 |
| CAT | SELL PREMIUM | NORMAL | 30d | No | NORMAL | V2_STRICTER | 0.345 | 1.26 | +1.27 | 1.104 | 0.567 |
| IWM | CONDITIONAL | NORMAL | ETF | No | CAUTION | V2_STRICTER | 0.198 | 0.99 | +0.66 | 0.995 | 1.061 |
| KO | CONDITIONAL | NORMAL | 28d | No | CAUTION | V2_STRICTER | 0.183 | 1.16 | +1.63 | 1.029 | 0.844 |
| NFLX | CONDITIONAL | NORMAL | 21d | No | DANGER | V2_STRICTER | 0.382 | 1.16 | +1.17 | 1.153 | 1.090 |
| SBUX | SELL PREMIUM | NORMAL | 29d | No | CAUTION | V2_STRICTER | 0.285 | 1.11 | +0.27 | 1.019 | 0.840 |
| UBER | CONDITIONAL | NORMAL | 35d | No | NORMAL | V2_STRICTER | 0.393 | 0.96 | +0.81 | 1.003 | 0.811 |
| XLB | CONDITIONAL | NORMAL | ETF | No | DANGER | V2_STRICTER | 0.205 | 1.22 | +0.17 | 1.194 | 0.964 |
| XLF | CONDITIONAL | NORMAL | ETF | No | DANGER | V2_STRICTER | 0.179 | 1.11 | +2.08 | 1.168 | 1.263 |
| XLI | CONDITIONAL | NORMAL | ETF | No | NORMAL | V2_STRICTER | 0.189 | 1.05 | +0.39 | 0.999 | 0.840 |
| GOOG | REDUCE SIZE | CAUTION | 36d | Yes | NORMAL | V2_LOOSER | 0.286 | 1.23 | +1.21 | 1.051 | 0.935 |
| AMZN | SELL PREMIUM | NORMAL | 30d | Yes | NORMAL | AGREE | 0.325 | 1.16 | +0.93 | 1.077 | 0.939 |
| EEM | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.232 | 1.01 | -0.30 | 0.991 | 0.909 |
| GLD | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.250 | 0.89 | -1.97 | 0.999 | 1.386 |
| GS | NO EDGE | NORMAL | 14d | No | DANGER | STATE_MISMATCH | 0.298 | 1.19 | +1.83 | 1.078 | 1.036 |
| HD | NO EDGE | NORMAL | 49d | No | CAUTION | STATE_MISMATCH | 0.267 | 1.07 | +0.49 | 0.942 | 1.058 |
| HOOD | NO EDGE | NORMAL | 36d | No | NORMAL | AGREE | 0.653 | 0.96 | +0.72 | 1.008 | 0.819 |
| JNJ | SELL PREMIUM | NORMAL | 14d | No | DANGER | STATE_MISMATCH | 0.205 | 1.32 | +2.00 | 1.065 | 0.454 |
| JPM | REDUCE SIZE | CAUTION | 14d | No | DANGER | STATE_MISMATCH | 0.243 | 1.13 | +1.83 | 1.081 | 1.318 |
| MCD | NO EDGE | CAUTION | 37d | No | CAUTION | AGREE | 0.229 | 0.95 | -0.31 | 0.919 | 1.329 |
| META | NO EDGE | CAUTION | 29d | No | DANGER | STATE_MISMATCH | 0.424 | 1.05 | +0.76 | 1.100 | 1.334 |
| MSFT | REDUCE SIZE | CAUTION | 29d | No | NORMAL | STATE_MISMATCH | 0.318 | 1.02 | +0.16 | 1.083 | 0.826 |
| NKE | AVOID | DANGER | 0d | No | DANGER | AGREE | 0.344 | 1.42 | +1.20 | 1.085 | 0.677 |
| NVDA | NO EDGE | NORMAL | 50d | No | NORMAL | AGREE | 0.420 | 0.76 | -1.27 | 0.884 | 0.635 |
| PLTR | NO EDGE | NORMAL | 34d | No | NORMAL | AGREE | 0.570 | 0.82 | -0.09 | 0.853 | 0.619 |
| QQQ | NO EDGE | CAUTION | ETF | No | NORMAL | STATE_MISMATCH | 0.198 | 0.98 | +0.10 | 0.935 | 0.815 |
| SPY | NO EDGE | CAUTION | ETF | No | NORMAL | STATE_MISMATCH | 0.143 | 0.96 | +0.44 | 0.937 | 0.987 |
| TLT | AVOID | DANGER | ETF | No | CAUTION | STATE_MISMATCH | 0.138 | 1.13 | +2.45 | 1.042 | 1.386 |
| TSLA | NO EDGE | NORMAL | 22d | No | DANGER | STATE_MISMATCH | 0.505 | 0.90 | +0.33 | 1.071 | 0.883 |
| WMT | NO EDGE | NORMAL | 51d | No | NORMAL | AGREE | 0.242 | 0.95 | -0.64 | 0.839 | 0.721 |
| XLE | AVOID | DANGER | ETF | No | CAUTION | STATE_MISMATCH | 0.275 | 1.16 | +2.58 | 1.225 | 1.060 |
| XLV | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.168 | 0.94 | -0.47 | 0.886 | 0.642 |
| XOM | NO EDGE | CAUTION | 31d | No | CAUTION | AGREE | 0.297 | 1.05 | +1.23 | 1.037 | 1.059 |

---

## 2026-09-28 (Monday)

**Shadow summary:** Checked 330 / 160 agree / 57 V2_STRICTER / 0 V2_LOOSER / 111 state_mismatch / 2 nodata | index-gating v1 76% vs v2 99% | oscillation v1 1.24 vs v2 0.82 | warm 100% | day-flips v1 3/33 vs v2 1/33 | capture60 n=1932 mean -95 / v2-veto-neg 30% / v2-clear-neg 33% / σfwd-vs-rv30 MAE 0.26 vs 0.25 | veto-disagree 5%

| Ticker | v1 Action | v1 Regime | Earnings | v2 Eligible | v2 Gate | Divergence | sigma_fwd | FVRP | z | 1M/3M | accel_dn |
|--------|-----------|-----------|----------|-------------|---------|------------|-----------|------|------|-------|----------|
| AMZN | CONDITIONAL | NORMAL | 31d | No | NORMAL | V2_STRICTER | 0.325 | 1.11 | +0.71 | 1.027 | 0.895 |
| CAT | CONDITIONAL | NORMAL | 31d | No | NORMAL | V2_STRICTER | 0.354 | 1.14 | +0.55 | 1.041 | 0.606 |
| IWM | CONDITIONAL | NORMAL | ETF | No | CAUTION | V2_STRICTER | 0.195 | 0.96 | +0.31 | 0.963 | 1.071 |
| JNJ | SELL PREMIUM | NORMAL | 15d | No | DANGER | V2_STRICTER | 0.209 | 1.24 | +1.49 | 1.026 | 0.487 |
| KO | SELL PREMIUM | NORMAL | 22d | No | NORMAL | V2_STRICTER | 0.191 | 1.11 | +1.35 | 1.026 | 0.795 |
| XLF | CONDITIONAL | NORMAL | ETF | No | CAUTION | V2_STRICTER | 0.185 | 1.03 | +1.48 | 1.084 | 1.189 |
| XLI | CONDITIONAL | NORMAL | ETF | No | NORMAL | V2_STRICTER | 0.186 | 1.02 | +0.17 | 0.984 | 0.711 |
| AAPL | NO EDGE | NORMAL | 31d | No | NORMAL | AGREE | 0.263 | 0.91 | +0.23 | 0.966 | 0.460 |
| EEM | NO EDGE | CAUTION | ETF | No | NORMAL | STATE_MISMATCH | 0.219 | 1.09 | +0.09 | 0.976 | 0.880 |
| GLD | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.186 | 1.10 | -0.32 | 0.955 | 0.820 |
| GOOG | REDUCE SIZE | CAUTION | 37d | No | NORMAL | STATE_MISMATCH | 0.293 | 1.16 | +0.89 | 1.027 | 0.991 |
| GS | NO EDGE | CAUTION | 15d | No | CAUTION | AGREE | 0.313 | 1.11 | +1.18 | 1.059 | 0.973 |
| HD | NO EDGE | CAUTION | 50d | No | CAUTION | AGREE | 0.270 | 1.02 | +0.10 | 0.925 | 1.080 |
| HOOD | NO EDGE | NORMAL | 37d | No | NORMAL | AGREE | 0.668 | 0.91 | +0.25 | 0.979 | 0.769 |
| JPM | REDUCE SIZE | CAUTION | 15d | No | DANGER | STATE_MISMATCH | 0.253 | 1.04 | +1.08 | 1.056 | 1.240 |
| MCD | NO EDGE | CAUTION | 38d | No | CAUTION | AGREE | 0.240 | 0.86 | -1.06 | 0.881 | 1.389 |
| META | NO EDGE | CAUTION | 30d | No | CAUTION | AGREE | 0.423 | 1.04 | +0.73 | 1.051 | 0.977 |
| MSFT | NO EDGE | CAUTION | 30d | No | NORMAL | STATE_MISMATCH | 0.307 | 1.00 | +0.06 | 1.023 | 0.683 |
| NFLX | NO EDGE | CAUTION | 22d | No | DANGER | STATE_MISMATCH | 0.356 | 1.21 | +1.36 | 1.135 | 1.013 |
| NKE | AVOID | DANGER | 1d | No | DANGER | AGREE | 0.352 | 1.35 | +0.98 | — | 0.727 |
| NVDA | NO EDGE | NORMAL | 51d | No | NORMAL | AGREE | 0.389 | 0.78 | -1.13 | 0.845 | 0.682 |
| PLTR | NO EDGE | NORMAL | 35d | No | NORMAL | AGREE | 0.567 | 0.82 | -0.09 | 0.849 | 0.611 |
| QQQ | NO EDGE | CAUTION | ETF | No | NORMAL | STATE_MISMATCH | 0.189 | 1.02 | +0.55 | 0.921 | 0.596 |
| SBUX | SELL PREMIUM | NORMAL | 30d | Yes | NORMAL | AGREE | 0.275 | 1.16 | +0.43 | 1.016 | 0.903 |
| SPY | NO EDGE | CAUTION | ETF | No | NORMAL | STATE_MISMATCH | 0.141 | 0.94 | +0.28 | 0.906 | 0.795 |
| TLT | NO EDGE | CAUTION | ETF | No | CAUTION | AGREE | 0.129 | 1.10 | +2.24 | 1.006 | 1.391 |
| TSLA | NO EDGE | NORMAL | 30d | No | DANGER | STATE_MISMATCH | 0.514 | 0.86 | +0.03 | 1.052 | 0.539 |
| UBER | NO EDGE | NORMAL | 36d | No | NORMAL | AGREE | 0.371 | 0.87 | +0.21 | 0.873 | 0.648 |
| WMT | NO EDGE | NORMAL | 52d | No | NORMAL | AGREE | 0.242 | 0.93 | -0.74 | 0.826 | 0.775 |
| XLB | CONDITIONAL | NORMAL | ETF | Yes | NORMAL | AGREE | 0.188 | 1.27 | +0.35 | 1.177 | 0.973 |
| XLE | NO EDGE | CAUTION | ETF | No | CAUTION | AGREE | 0.278 | 0.91 | +0.33 | 0.999 | 1.139 |
| XLV | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.172 | 0.94 | -0.48 | 0.893 | 0.690 |
| XOM | NO EDGE | CAUTION | 32d | No | CAUTION | AGREE | 0.297 | 0.96 | +0.39 | 0.966 | 1.137 |

---

## 2026-09-25 (Friday)

**Shadow summary:** Checked 330 / 159 agree / 55 V2_STRICTER / 0 V2_LOOSER / 114 state_mismatch / 2 nodata | index-gating v1 80% vs v2 100% | oscillation v1 1.33 vs v2 0.82 | warm 100% | day-flips v1 2/33 vs v2 6/33 | capture60 n=1932 mean -102 / v2-veto-neg 31% / v2-clear-neg 33% / σfwd-vs-rv30 MAE 0.26 vs 0.25 | veto-disagree 4%

| Ticker | v1 Action | v1 Regime | Earnings | v2 Eligible | v2 Gate | Divergence | sigma_fwd | FVRP | z | 1M/3M | accel_dn |
|--------|-----------|-----------|----------|-------------|---------|------------|-----------|------|------|-------|----------|
| CAT | CONDITIONAL | NORMAL | 34d | No | NORMAL | V2_STRICTER | 0.361 | 1.03 | -0.12 | 0.979 | 0.651 |
| IWM | CONDITIONAL | NORMAL | ETF | No | CAUTION | V2_STRICTER | 0.199 | 0.94 | +0.13 | 0.956 | 1.150 |
| JNJ | SELL PREMIUM | NORMAL | 18d | No | DANGER | V2_STRICTER | 0.222 | 1.21 | +1.24 | 1.046 | 0.523 |
| KO | CONDITIONAL | NORMAL | 25d | No | NORMAL | V2_STRICTER | 0.203 | 1.01 | +0.67 | 0.975 | 0.831 |
| MSFT | CONDITIONAL | NORMAL | 33d | No | NORMAL | V2_STRICTER | 0.299 | 0.89 | -0.54 | 0.910 | 0.733 |
| SBUX | CONDITIONAL | NORMAL | 33d | No | NORMAL | V2_STRICTER | 0.288 | 0.96 | -0.32 | 0.892 | 0.970 |
| XLI | SELL PREMIUM | NORMAL | ETF | No | NORMAL | V2_STRICTER | 0.190 | 1.20 | +1.18 | 0.957 | 0.764 |
| AAPL | NO EDGE | NORMAL | 34d | No | NORMAL | AGREE | 0.264 | 0.88 | +0.01 | 0.923 | 0.494 |
| AMZN | NO EDGE | NORMAL | 34d | No | NORMAL | AGREE | 0.344 | 0.93 | -0.17 | 0.908 | 0.961 |
| EEM | NO EDGE | CAUTION | ETF | No | NORMAL | STATE_MISMATCH | 0.219 | 1.07 | -0.01 | 0.970 | 0.945 |
| GLD | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.194 | 1.04 | -0.81 | 0.927 | 0.881 |
| GOOG | NO EDGE | CAUTION | 40d | No | NORMAL | STATE_MISMATCH | 0.306 | 1.05 | +0.20 | 0.946 | 1.065 |
| GS | NO EDGE | CAUTION | 18d | No | CAUTION | AGREE | 0.319 | 1.06 | +0.75 | 1.040 | 1.045 |
| HD | NO EDGE | CAUTION | 53d | No | CAUTION | AGREE | 0.278 | 0.96 | -0.31 | 0.910 | 1.161 |
| HOOD | NO EDGE | NORMAL | 40d | No | NORMAL | AGREE | 0.700 | 0.88 | -0.10 | 0.966 | 0.801 |
| JPM | REDUCE SIZE | CAUTION | 18d | No | DANGER | STATE_MISMATCH | 0.259 | 1.02 | +0.97 | 1.071 | 1.332 |
| MCD | NO EDGE | CAUTION | 41d | No | CAUTION | AGREE | 0.259 | 0.82 | -1.42 | 0.917 | 1.491 |
| META | NO EDGE | CAUTION | 33d | No | CAUTION | AGREE | 0.427 | 1.06 | +0.82 | 1.013 | 0.547 |
| NFLX | WATCHLIST | NORMAL | 25d | No | DANGER | STATE_MISMATCH | 0.381 | 1.16 | +1.18 | 1.172 | 1.074 |
| NKE | AVOID | DANGER | 4d | No | DANGER | AGREE | 0.335 | 1.42 | +1.21 | 1.065 | 0.755 |
| NVDA | NO EDGE | NORMAL | 54d | No | NORMAL | AGREE | 0.405 | 0.77 | -1.22 | 0.858 | 0.732 |
| PLTR | NO EDGE | NORMAL | 38d | No | NORMAL | AGREE | 0.599 | 0.80 | -0.25 | 0.854 | 0.559 |
| QQQ | NO EDGE | CAUTION | ETF | No | NORMAL | STATE_MISMATCH | 0.198 | 0.93 | -0.34 | 0.890 | 0.640 |
| SPY | NO EDGE | CAUTION | ETF | No | NORMAL | STATE_MISMATCH | 0.144 | 0.88 | -0.31 | 0.881 | 0.854 |
| TLT | AVOID | DANGER | ETF | No | CAUTION | STATE_MISMATCH | 0.133 | 1.15 | +2.70 | 1.036 | 1.493 |
| TSLA | NO EDGE | NORMAL | 33d | No | CAUTION | STATE_MISMATCH | 0.462 | 0.98 | +0.97 | 1.075 | 0.484 |
| UBER | NO EDGE | NORMAL | 39d | No | NORMAL | AGREE | 0.393 | 0.88 | +0.27 | 0.906 | 0.696 |
| WMT | NO EDGE | NORMAL | 55d | No | NORMAL | AGREE | 0.248 | 0.95 | -0.64 | 0.860 | 0.832 |
| XLB | NO DATA | NORMAL | ETF | No | NORMAL | NODATA_SKEW | — | — | — | — | — |
| XLE | NO EDGE | CAUTION | ETF | No | CAUTION | AGREE | 0.283 | 0.98 | +1.04 | 1.015 | 1.170 |
| XLF | NO EDGE | NORMAL | ETF | No | CAUTION | STATE_MISMATCH | 0.191 | 0.80 | -0.71 | 0.933 | 1.278 |
| XLV | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.177 | 1.00 | -0.03 | — | 0.741 |
| XOM | NO EDGE | CAUTION | 35d | No | CAUTION | AGREE | 0.305 | 0.98 | +0.53 | 0.992 | 1.181 |

---

## 2026-09-24 (Thursday)

**Shadow summary:** Checked 330 / 157 agree / 54 V2_STRICTER / 0 V2_LOOSER / 117 state_mismatch / 2 nodata | index-gating v1 80% vs v2 100% | oscillation v1 1.39 vs v2 0.70 | warm 100% | day-flips v1 3/33 vs v2 3/33 | capture60 n=1932 mean -110 / v2-veto-neg 31% / v2-clear-neg 33% / σfwd-vs-rv30 MAE 0.26 vs 0.25 | veto-disagree 4%

| Ticker | v1 Action | v1 Regime | Earnings | v2 Eligible | v2 Gate | Divergence | sigma_fwd | FVRP | z | 1M/3M | accel_dn |
|--------|-----------|-----------|----------|-------------|---------|------------|-----------|------|------|-------|----------|
| IWM | CONDITIONAL | NORMAL | ETF | No | NORMAL | V2_STRICTER | 0.201 | 0.91 | -0.24 | 0.942 | 1.234 |
| JNJ | SELL PREMIUM | NORMAL | 19d | No | DANGER | V2_STRICTER | 0.220 | 1.20 | +1.18 | 1.055 | 0.562 |
| KO | CONDITIONAL | NORMAL | 26d | No | NORMAL | V2_STRICTER | 0.199 | 0.96 | +0.24 | 0.923 | 0.892 |
| MSFT | CONDITIONAL | NORMAL | 34d | No | NORMAL | V2_STRICTER | 0.307 | 0.88 | -0.64 | 0.904 | 0.757 |
| XLF | CONDITIONAL | NORMAL | ETF | No | CAUTION | V2_STRICTER | 0.200 | 0.90 | +0.32 | 1.045 | 1.372 |
| XLI | CONDITIONAL | NORMAL | ETF | No | NORMAL | V2_STRICTER | 0.183 | 1.10 | +0.65 | 0.932 | 0.700 |
| AAPL | NO EDGE | NORMAL | 35d | No | NORMAL | AGREE | 0.272 | 0.87 | -0.12 | 0.923 | 0.514 |
| AMZN | NO EDGE | NORMAL | 35d | No | NORMAL | AGREE | 0.347 | 0.90 | -0.37 | 0.874 | 1.033 |
| CAT | NO EDGE | NORMAL | 35d | No | NORMAL | AGREE | 0.359 | 1.00 | -0.35 | 0.917 | 0.667 |
| EEM | NO EDGE | CAUTION | ETF | No | NORMAL | STATE_MISMATCH | 0.231 | 1.04 | -0.17 | 0.979 | 0.987 |
| GLD | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.203 | 1.00 | -1.10 | 0.925 | 0.940 |
| GOOG | NO EDGE | CAUTION | 41d | No | NORMAL | STATE_MISMATCH | 0.326 | 0.98 | -0.18 | 0.936 | 1.144 |
| GS | NO EDGE | CAUTION | 19d | No | CAUTION | AGREE | 0.330 | 1.02 | +0.37 | 1.018 | 1.065 |
| HD | NO EDGE | CAUTION | 54d | No | NORMAL | STATE_MISMATCH | 0.273 | 0.94 | -0.53 | 0.895 | 1.161 |
| HOOD | NO EDGE | NORMAL | 41d | No | NORMAL | AGREE | 0.696 | 0.90 | +0.14 | 0.962 | 0.821 |
| JPM | REDUCE SIZE | CAUTION | 19d | No | DANGER | STATE_MISMATCH | 0.274 | 0.98 | +0.63 | 1.089 | 1.431 |
| MCD | NO EDGE | CAUTION | 42d | No | NORMAL | STATE_MISMATCH | 0.273 | 0.83 | -1.31 | 0.943 | 1.597 |
| META | AVOID | DANGER | 34d | No | NORMAL | STATE_MISMATCH | 0.446 | 1.02 | +0.66 | 1.014 | 0.588 |
| NFLX | WATCHLIST | NORMAL | 26d | No | DANGER | STATE_MISMATCH | 0.407 | 1.09 | +0.91 | 1.170 | 1.153 |
| NKE | AVOID | DANGER | 5d | No | NORMAL | STATE_MISMATCH | 0.354 | 1.32 | +0.87 | 1.059 | 0.810 |
| NVDA | NO EDGE | NORMAL | 55d | No | NORMAL | AGREE | 0.393 | 0.79 | -0.94 | 0.859 | 0.778 |
| PLTR | NO EDGE | NORMAL | 39d | No | NORMAL | AGREE | 0.615 | 0.79 | -0.29 | 0.878 | 0.600 |
| QQQ | NO EDGE | CAUTION | ETF | No | NORMAL | STATE_MISMATCH | 0.194 | 0.95 | -0.13 | 0.885 | 0.688 |
| SBUX | NO EDGE | NORMAL | 34d | No | NORMAL | AGREE | 0.296 | 0.95 | -0.39 | 0.904 | 1.022 |
| SPY | NO EDGE | CAUTION | ETF | No | NORMAL | STATE_MISMATCH | 0.140 | 0.91 | +0.00 | 0.867 | 0.914 |
| TLT | NO EDGE | CAUTION | ETF | No | NORMAL | STATE_MISMATCH | 0.133 | 0.97 | +1.07 | 0.988 | 1.401 |
| TSLA | NO EDGE | NORMAL | 34d | No | CAUTION | STATE_MISMATCH | 0.473 | 0.94 | +0.69 | 1.044 | 0.506 |
| UBER | NO EDGE | NORMAL | 40d | No | NORMAL | AGREE | 0.410 | 0.86 | +0.11 | 0.922 | 0.744 |
| WMT | NO EDGE | NORMAL | 56d | No | NORMAL | AGREE | 0.237 | 0.99 | -0.44 | 0.872 | 0.451 |
| XLB | NO DATA | NORMAL | ETF | No | NORMAL | NODATA_SKEW | — | — | — | — | — |
| XLE | NO EDGE | CAUTION | ETF | No | CAUTION | AGREE | 0.284 | 0.99 | +1.14 | 1.026 | 1.257 |
| XLV | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.176 | 0.92 | -0.66 | 0.840 | 0.796 |
| XOM | NO EDGE | CAUTION | 36d | No | CAUTION | AGREE | 0.296 | 0.95 | +0.32 | 0.950 | 1.269 |

---

## 2026-09-23 (Wednesday)

**Shadow summary:** Checked 330 / 161 agree / 52 V2_STRICTER / 0 V2_LOOSER / 115 state_mismatch / 2 nodata | index-gating v1 82% vs v2 100% | oscillation v1 1.42 vs v2 0.70 | warm 100% | day-flips v1 2/33 vs v2 4/33 | capture60 n=1931 mean -118 / v2-veto-neg 31% / v2-clear-neg 36% / σfwd-vs-rv30 MAE 0.26 vs 0.25 | veto-disagree 5%

| Ticker | v1 Action | v1 Regime | Earnings | v2 Eligible | v2 Gate | Divergence | sigma_fwd | FVRP | z | 1M/3M | accel_dn |
|--------|-----------|-----------|----------|-------------|---------|------------|-----------|------|------|-------|----------|
| IWM | CONDITIONAL | NORMAL | ETF | No | NORMAL | V2_STRICTER | 0.202 | 0.90 | -0.40 | 0.926 | 0.780 |
| JNJ | SELL PREMIUM | NORMAL | 20d | No | DANGER | V2_STRICTER | 0.220 | 1.25 | +1.55 | 1.097 | 0.604 |
| XLI | CONDITIONAL | NORMAL | ETF | No | NORMAL | V2_STRICTER | 0.190 | 1.08 | +0.57 | 0.950 | 0.750 |
| AAPL | NO EDGE | NORMAL | 36d | No | NORMAL | AGREE | 0.276 | 0.84 | -0.39 | 0.898 | 0.453 |
| AMZN | NO EDGE | NORMAL | 36d | No | NORMAL | AGREE | 0.348 | 0.88 | -0.48 | 0.853 | 0.839 |
| CAT | NO EDGE | NORMAL | 36d | No | NORMAL | AGREE | 0.373 | 0.96 | -0.67 | 0.908 | 0.717 |
| EEM | NO EDGE | CAUTION | ETF | No | NORMAL | STATE_MISMATCH | 0.230 | 1.03 | -0.18 | 0.875 | 0.757 |
| GLD | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.195 | 1.06 | -0.61 | 0.918 | 0.757 |
| GOOG | NO EDGE | CAUTION | 42d | No | NORMAL | STATE_MISMATCH | 0.330 | 0.98 | -0.20 | 0.931 | 0.597 |
| GS | NO EDGE | CAUTION | 20d | No | CAUTION | AGREE | 0.336 | 1.02 | +0.37 | 1.052 | 1.089 |
| HD | NO EDGE | NORMAL | 55d | No | NORMAL | AGREE | 0.279 | 0.96 | -0.29 | 0.928 | 0.834 |
| HOOD | NO EDGE | NORMAL | 42d | No | NORMAL | AGREE | 0.723 | 0.84 | -0.51 | 0.930 | 0.858 |
| JPM | REDUCE SIZE | CAUTION | 20d | No | CAUTION | AGREE | 0.287 | 0.92 | +0.05 | 1.066 | 1.519 |
| KO | NO EDGE | NORMAL | 27d | No | NORMAL | AGREE | 0.198 | 0.94 | +0.11 | 0.903 | 0.897 |
| MCD | NO EDGE | CAUTION | 43d | No | NORMAL | STATE_MISMATCH | 0.214 | 1.12 | +0.93 | 0.972 | 0.842 |
| META | NO EDGE | CAUTION | 35d | No | NORMAL | STATE_MISMATCH | 0.462 | 0.92 | +0.16 | 0.964 | 0.631 |
| MSFT | NO EDGE | NORMAL | 35d | No | NORMAL | AGREE | 0.304 | 0.83 | -0.90 | 0.851 | 0.813 |
| NFLX | WATCHLIST | NORMAL | 27d | No | DANGER | STATE_MISMATCH | 0.436 | 1.02 | +0.63 | 1.148 | 1.219 |
| NKE | AVOID | DANGER | 6d | No | NORMAL | STATE_MISMATCH | 0.362 | 1.27 | +0.71 | 1.042 | 0.869 |
| NVDA | NO EDGE | NORMAL | 56d | No | NORMAL | AGREE | 0.392 | 0.82 | -0.70 | 0.873 | 0.737 |
| PLTR | NO EDGE | NORMAL | 40d | No | NORMAL | AGREE | 0.564 | 0.82 | -0.08 | 0.844 | 0.645 |
| QQQ | NO EDGE | CAUTION | ETF | No | NORMAL | STATE_MISMATCH | 0.198 | 0.92 | -0.46 | 0.877 | 0.546 |
| SBUX | NO EDGE | NORMAL | 35d | No | CAUTION | STATE_MISMATCH | 0.296 | 0.90 | -0.61 | 0.846 | 1.028 |
| SPY | NO EDGE | CAUTION | ETF | No | NORMAL | STATE_MISMATCH | 0.142 | 0.88 | -0.26 | 0.867 | 0.698 |
| TLT | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.118 | 0.94 | +0.78 | 0.925 | 0.849 |
| TSLA | NO EDGE | NORMAL | 35d | No | CAUTION | STATE_MISMATCH | 0.485 | 0.93 | +0.56 | 1.041 | 0.544 |
| UBER | NO EDGE | NORMAL | 41d | No | NORMAL | AGREE | 0.417 | 0.86 | +0.17 | 0.963 | 0.779 |
| WMT | NO EDGE | NORMAL | 57d | No | NORMAL | AGREE | 0.241 | 0.96 | -0.60 | 0.862 | 0.484 |
| XLB | NO EDGE | NORMAL | ETF | No | CAUTION | STATE_MISMATCH | 0.202 | 0.89 | -1.16 | 0.891 | 0.955 |
| XLE | NO EDGE | CAUTION | ETF | No | CAUTION | AGREE | 0.297 | 0.92 | +0.43 | 0.985 | 1.350 |
| XLF | NO EDGE | NORMAL | ETF | No | CAUTION | STATE_MISMATCH | 0.205 | 0.77 | -1.06 | 1.001 | 1.456 |
| XLV | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.174 | 0.90 | -0.83 | 0.810 | 0.756 |
| XOM | NO EDGE | CAUTION | 37d | No | CAUTION | AGREE | 0.311 | 0.96 | +0.40 | 1.004 | 1.363 |

---

## 2026-09-22 (Tuesday)

**Shadow summary:** Checked 330 / 166 agree / 51 V2_STRICTER / 1 V2_LOOSER / 110 state_mismatch / 2 nodata | index-gating v1 83% vs v2 100% | oscillation v1 1.42 vs v2 0.73 | warm 100% | day-flips v1 7/33 vs v2 3/33 | capture60 n=1931 mean -125 / v2-veto-neg 31% / v2-clear-neg 36% / σfwd-vs-rv30 MAE 0.26 vs 0.25 | veto-disagree 6%

| Ticker | v1 Action | v1 Regime | Earnings | v2 Eligible | v2 Gate | Divergence | sigma_fwd | FVRP | z | 1M/3M | accel_dn |
|--------|-----------|-----------|----------|-------------|---------|------------|-----------|------|------|-------|----------|
| IWM | CONDITIONAL | NORMAL | ETF | No | NORMAL | V2_STRICTER | 0.201 | 0.84 | -1.11 | 0.895 | 0.838 |
| JNJ | SELL PREMIUM | NORMAL | 21d | No | CAUTION | V2_STRICTER | 0.217 | 1.22 | +1.36 | 1.069 | 0.647 |
| JPM | CONDITIONAL | NORMAL | 21d | No | CAUTION | V2_STRICTER | 0.261 | 0.97 | +0.54 | 1.027 | 0.853 |
| SBUX | CONDITIONAL | NORMAL | 36d | No | CAUTION | V2_STRICTER | 0.306 | 0.98 | -0.28 | 0.963 | 1.104 |
| XLF | CONDITIONAL | NORMAL | ETF | No | CAUTION | V2_STRICTER | 0.189 | 0.87 | +0.02 | 0.990 | 1.100 |
| XLI | CONDITIONAL | NORMAL | ETF | No | DANGER | V2_STRICTER | 0.198 | 0.99 | +0.00 | 0.936 | 0.805 |
| AAPL | NO EDGE | NORMAL | 37d | No | NORMAL | AGREE | 0.275 | 0.84 | -0.40 | 0.899 | 0.486 |
| AMZN | NO EDGE | NORMAL | 37d | No | NORMAL | AGREE | 0.342 | 0.89 | -0.40 | 0.849 | 0.776 |
| CAT | NO EDGE | NORMAL | 37d | No | NORMAL | AGREE | 0.392 | 0.90 | -1.08 | 0.890 | 0.728 |
| EEM | NO EDGE | CAUTION | ETF | No | NORMAL | STATE_MISMATCH | 0.247 | 0.91 | -0.80 | 0.928 | 0.813 |
| GLD | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.203 | 1.03 | -0.90 | 0.920 | 0.814 |
| GOOG | NO EDGE | CAUTION | 43d | No | NORMAL | STATE_MISMATCH | 0.315 | 0.98 | -0.18 | 0.907 | 0.548 |
| GS | NO EDGE | CAUTION | 21d | No | CAUTION | AGREE | 0.333 | 1.04 | +0.50 | 1.038 | 1.141 |
| HD | NO EDGE | NORMAL | 56d | No | NORMAL | AGREE | 0.268 | 0.91 | -0.70 | 0.892 | 0.896 |
| HOOD | NO EDGE | NORMAL | 43d | No | NORMAL | AGREE | 0.778 | 0.81 | -0.91 | 0.951 | 0.921 |
| KO | NO EDGE | NORMAL | 28d | No | NORMAL | AGREE | 0.187 | 0.93 | +0.02 | 0.862 | 0.964 |
| MCD | NO EDGE | CAUTION | 44d | No | NORMAL | STATE_MISMATCH | 0.206 | 1.07 | +0.62 | 0.926 | 0.905 |
| META | NO EDGE | CAUTION | 36d | No | NORMAL | STATE_MISMATCH | 0.480 | 0.94 | +0.23 | 0.990 | 0.656 |
| MSFT | NO EDGE | NORMAL | 36d | No | NORMAL | AGREE | 0.286 | 0.90 | -0.52 | 0.854 | 0.825 |
| NFLX | WATCHLIST | NORMAL | 28d | No | CAUTION | STATE_MISMATCH | 0.461 | 0.93 | +0.20 | 1.109 | 1.269 |
| NKE | AVOID | DANGER | 7d | No | NORMAL | STATE_MISMATCH | 0.343 | 1.34 | +0.93 | — | 0.933 |
| NVDA | NO EDGE | NORMAL | 57d | No | NORMAL | AGREE | 0.416 | 0.75 | -1.45 | 0.865 | 0.791 |
| PLTR | NO EDGE | NORMAL | 41d | No | NORMAL | AGREE | 0.584 | 0.81 | -0.18 | 0.859 | 0.693 |
| QQQ | NO EDGE | CAUTION | ETF | No | NORMAL | STATE_MISMATCH | 0.213 | 0.82 | -1.63 | 0.863 | 0.587 |
| SPY | NO EDGE | CAUTION | ETF | No | NORMAL | STATE_MISMATCH | 0.154 | 0.81 | -0.95 | 0.871 | 0.749 |
| TLT | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.125 | 0.88 | +0.13 | 0.927 | 0.910 |
| TSLA | NO EDGE | NORMAL | 36d | No | NORMAL | AGREE | 0.503 | 0.88 | +0.19 | 1.022 | 0.584 |
| UBER | NO EDGE | NORMAL | 42d | No | NORMAL | AGREE | 0.386 | 0.86 | +0.15 | 0.881 | 0.759 |
| WMT | NO EDGE | NORMAL | 58d | No | NORMAL | AGREE | 0.232 | 0.96 | -0.57 | 0.840 | 0.520 |
| XLB | NO EDGE | NORMAL | ETF | No | CAUTION | STATE_MISMATCH | 0.201 | 0.97 | -0.81 | 1.000 | 1.026 |
| XLE | NO EDGE | NORMAL | ETF | No | CAUTION | STATE_MISMATCH | 0.286 | 0.93 | +0.57 | 0.981 | 1.400 |
| XLV | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.168 | 0.93 | -0.57 | 0.926 | 0.812 |
| XOM | NO EDGE | CAUTION | 38d | No | CAUTION | AGREE | 0.310 | 0.95 | +0.25 | 0.986 | 1.464 |

---

## 2026-09-21 (Monday)

**Shadow summary:** Checked 33 / 16 agree / 7 V2_STRICTER / 0 V2_LOOSER / 10 state_mismatch / 0 nodata | index-gating v1 73% vs v2 100% | oscillation v1 — vs v2 — | warm 100% | day-flips v1 9/33 vs v2 0/33 | capture60 n=1931 mean -125 / v2-veto-neg 31% / v2-clear-neg 36% / σfwd-vs-rv30 MAE 0.26 vs 0.25 | veto-disagree 0%

| Ticker | v1 Action | v1 Regime | Earnings | v2 Eligible | v2 Gate | Divergence | sigma_fwd | FVRP | z | 1M/3M | accel_dn |
|--------|-----------|-----------|----------|-------------|---------|------------|-----------|------|------|-------|----------|
| GS | CONDITIONAL | NORMAL | 22d | No | CAUTION | V2_STRICTER | 0.333 | 1.00 | +0.21 | 1.001 | 1.226 |
| IWM | CONDITIONAL | NORMAL | ETF | No | NORMAL | V2_STRICTER | 0.208 | 0.80 | -1.66 | 0.883 | 0.900 |
| JNJ | SELL PREMIUM | NORMAL | 22d | No | CAUTION | V2_STRICTER | 0.215 | 1.18 | +1.09 | 1.018 | 0.688 |
| JPM | SELL PREMIUM | NORMAL | 22d | No | CAUTION | V2_STRICTER | 0.266 | 0.93 | +0.14 | 1.008 | 0.917 |
| KO | CONDITIONAL | NORMAL | 29d | No | NORMAL | V2_STRICTER | 0.187 | 0.98 | +0.37 | 0.886 | 0.720 |
| XLF | CONDITIONAL | NORMAL | ETF | No | CAUTION | V2_STRICTER | 0.193 | 0.83 | -0.39 | 0.986 | 1.182 |
| XLI | CONDITIONAL | NORMAL | ETF | No | DANGER | V2_STRICTER | 0.202 | 1.06 | +0.44 | 1.047 | 0.865 |
| AAPL | NO EDGE | CAUTION | 38d | No | NORMAL | STATE_MISMATCH | 0.282 | 0.80 | -0.76 | 0.896 | 0.522 |
| AMZN | NO EDGE | NORMAL | 38d | No | NORMAL | AGREE | 0.339 | 0.85 | -0.64 | 0.824 | 0.834 |
| CAT | NO EDGE | NORMAL | 38d | No | NORMAL | AGREE | 0.389 | 0.88 | -1.30 | 0.869 | 0.782 |
| EEM | NO EDGE | CAUTION | ETF | No | NORMAL | STATE_MISMATCH | 0.231 | 0.93 | -0.72 | 0.903 | 0.873 |
| GLD | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.218 | 0.98 | -1.22 | 0.918 | 0.835 |
| GOOG | NO EDGE | CAUTION | 44d | No | NORMAL | STATE_MISMATCH | 0.331 | 0.91 | -0.65 | 0.906 | 0.589 |
| HD | NO EDGE | NORMAL | 57d | No | NORMAL | AGREE | 0.276 | 0.91 | -0.75 | 0.905 | 0.908 |
| HOOD | NO EDGE | NORMAL | 44d | No | NORMAL | AGREE | 0.793 | 0.78 | -1.23 | 0.936 | 0.989 |
| MCD | NO EDGE | NORMAL | 45d | No | NORMAL | AGREE | 0.202 | 1.05 | +0.45 | 0.884 | 0.970 |
| META | NO EDGE | CAUTION | 37d | No | NORMAL | STATE_MISMATCH | 0.419 | 0.95 | +0.33 | 0.976 | 0.705 |
| MSFT | NO EDGE | NORMAL | 37d | No | NORMAL | AGREE | 0.292 | 0.82 | -0.97 | 0.833 | 0.887 |
| NFLX | NO EDGE | CAUTION | 29d | No | CAUTION | AGREE | 0.499 | 0.80 | -0.51 | 1.039 | 1.363 |
| NKE | CONDITIONAL | NORMAL | 8d | No | DANGER | STATE_MISMATCH | 0.354 | 1.27 | +0.68 | — | 1.003 |
| NVDA | NO EDGE | NORMAL | 58d | No | NORMAL | AGREE | 0.417 | 0.73 | -1.64 | 0.858 | 0.850 |
| PLTR | NO EDGE | NORMAL | 42d | No | NORMAL | AGREE | 0.597 | 0.78 | -0.42 | 0.844 | 0.744 |
| QQQ | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.210 | 0.76 | -2.48 | 0.833 | 0.630 |
| SBUX | NO EDGE | NORMAL | 37d | No | CAUTION | STATE_MISMATCH | 0.287 | 0.96 | -0.35 | 0.881 | 1.133 |
| SPY | NO EDGE | CAUTION | ETF | No | NORMAL | STATE_MISMATCH | 0.155 | 0.74 | -1.79 | 0.836 | 0.805 |
| TLT | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.127 | 0.88 | +0.07 | 0.915 | 0.978 |
| TSLA | NO EDGE | NORMAL | 37d | No | NORMAL | AGREE | 0.509 | 0.83 | -0.27 | 0.974 | 0.627 |
| UBER | NO EDGE | NORMAL | 43d | No | NORMAL | AGREE | 0.384 | 0.86 | +0.15 | 0.914 | 0.815 |
| WMT | NO EDGE | NORMAL | 59d | No | NORMAL | AGREE | 0.236 | 0.96 | -0.59 | 0.842 | 0.559 |
| XLB | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.208 | 0.76 | -1.84 | 0.740 | 1.101 |
| XLE | NO EDGE | NORMAL | ETF | No | CAUTION | STATE_MISMATCH | 0.265 | 0.89 | +0.18 | 0.873 | 1.223 |
| XLV | NO EDGE | NORMAL | ETF | No | CAUTION | STATE_MISMATCH | 0.162 | 0.99 | -0.13 | 0.977 | 0.873 |
| XOM | NO EDGE | NORMAL | 39d | No | CAUTION | STATE_MISMATCH | 0.285 | 1.02 | +0.98 | 0.989 | 1.237 |

---

## 2026-09-18 (Friday)

**Shadow summary:** Checked 330 / 185 agree / 40 V2_STRICTER / 1 V2_LOOSER / 102 state_mismatch / 2 nodata | index-gating v1 88% vs v2 100% | oscillation v1 1.12 vs v2 0.73 | warm 100% | day-flips v1 5/33 vs v2 2/33 | capture60 n=1931 mean -138 / v2-veto-neg 32% / v2-clear-neg 40% / σfwd-vs-rv30 MAE 0.25 vs 0.25 | veto-disagree 8%

| Ticker | v1 Action | v1 Regime | Earnings | v2 Eligible | v2 Gate | Divergence | sigma_fwd | FVRP | z | 1M/3M | accel_dn |
|--------|-----------|-----------|----------|-------------|---------|------------|-----------|------|------|-------|----------|
| HD | CONDITIONAL | NORMAL | 60d | No | NORMAL | V2_STRICTER | 0.279 | 0.94 | -0.53 | 0.919 | 0.934 |
| IWM | CONDITIONAL | NORMAL | ETF | No | NORMAL | V2_STRICTER | 0.219 | 0.80 | -1.61 | 0.918 | 0.923 |
| JNJ | SELL PREMIUM | NORMAL | 25d | No | CAUTION | V2_STRICTER | 0.210 | 1.20 | +1.24 | 1.030 | 0.738 |
| KO | CONDITIONAL | NORMAL | 32d | No | NORMAL | V2_STRICTER | 0.194 | 0.94 | +0.06 | 0.890 | 0.773 |
| AAPL | NO EDGE | CAUTION | 41d | No | NORMAL | STATE_MISMATCH | 0.288 | 0.82 | -0.52 | 0.910 | 0.553 |
| AMZN | NO EDGE | NORMAL | 41d | No | NORMAL | AGREE | 0.354 | 0.82 | -0.82 | 0.827 | 0.896 |
| CAT | NO EDGE | NORMAL | 41d | No | NORMAL | AGREE | 0.421 | 0.84 | -1.59 | 0.888 | 0.840 |
| EEM | NO EDGE | CAUTION | ETF | No | NORMAL | STATE_MISMATCH | 0.248 | 0.93 | -0.71 | 0.929 | 0.938 |
| GLD | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.231 | 0.99 | -1.18 | 0.950 | 0.897 |
| GOOG | NO EDGE | CAUTION | 47d | No | NORMAL | STATE_MISMATCH | 0.306 | 0.94 | -0.47 | 0.872 | 0.632 |
| GS | NO EDGE | CAUTION | 25d | No | CAUTION | AGREE | 0.356 | 0.96 | -0.20 | 1.018 | 1.297 |
| HOOD | NO EDGE | CAUTION | 47d | No | NORMAL | STATE_MISMATCH | 0.786 | 0.77 | -1.43 | 0.941 | 1.063 |
| JPM | REDUCE SIZE | CAUTION | 25d | No | CAUTION | AGREE | 0.280 | 0.90 | -0.12 | 1.025 | 0.985 |
| MCD | NO EDGE | NORMAL | 48d | No | NORMAL | AGREE | 0.206 | 1.04 | +0.38 | 0.906 | 1.041 |
| META | NO EDGE | NORMAL | 40d | No | NORMAL | AGREE | 0.399 | 0.95 | +0.30 | 0.910 | 0.374 |
| MSFT | NO EDGE | CAUTION | 40d | No | NORMAL | STATE_MISMATCH | 0.307 | 0.80 | -1.14 | 0.832 | 0.903 |
| NFLX | NO EDGE | NORMAL | 32d | No | CAUTION | STATE_MISMATCH | 0.368 | 0.96 | +0.34 | 0.934 | 1.105 |
| NKE | SELL PREMIUM | NORMAL | 11d | No | DANGER | STATE_MISMATCH | 0.356 | 1.34 | +0.94 | 1.090 | 0.875 |
| NVDA | NO EDGE | NORMAL | 61d | No | NORMAL | AGREE | 0.436 | 0.71 | -1.99 | 0.854 | 0.913 |
| PLTR | NO EDGE | NORMAL | 45d | No | NORMAL | AGREE | 0.600 | 0.78 | -0.38 | 0.848 | 0.799 |
| QQQ | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.222 | 0.76 | -2.51 | 0.841 | 0.677 |
| SBUX | NO EDGE | NORMAL | 40d | No | CAUTION | STATE_MISMATCH | 0.299 | 0.94 | -0.41 | 0.887 | 1.177 |
| SPY | NO EDGE | CAUTION | ETF | No | NORMAL | STATE_MISMATCH | 0.166 | 0.76 | -1.54 | 0.866 | 0.864 |
| TLT | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.131 | 0.84 | -0.39 | 0.925 | 0.864 |
| TSLA | NO EDGE | CAUTION | 40d | No | NORMAL | STATE_MISMATCH | 0.526 | 0.80 | -0.59 | 0.955 | 0.667 |
| UBER | NO EDGE | NORMAL | 46d | No | NORMAL | AGREE | 0.402 | 0.84 | +0.03 | 0.894 | 0.866 |
| WMT | NO EDGE | NORMAL | 62d | No | NORMAL | AGREE | 0.229 | 0.99 | -0.41 | 0.847 | 0.600 |
| XLB | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.209 | 0.81 | -1.59 | 0.801 | 0.918 |
| XLE | NO EDGE | NORMAL | ETF | No | CAUTION | STATE_MISMATCH | 0.276 | 0.94 | +0.63 | 0.925 | 1.310 |
| XLF | NO EDGE | CAUTION | ETF | No | CAUTION | AGREE | 0.201 | 0.76 | -1.10 | 0.902 | 1.270 |
| XLI | NO EDGE | CAUTION | ETF | No | DANGER | STATE_MISMATCH | 0.217 | 0.87 | -0.79 | 1.112 | 0.930 |
| XLV | NO EDGE | NORMAL | ETF | No | CAUTION | STATE_MISMATCH | 0.166 | 1.01 | +0.04 | 1.032 | 0.927 |
| XOM | NO EDGE | NORMAL | 42d | No | CAUTION | STATE_MISMATCH | 0.296 | 0.96 | +0.43 | 0.949 | 1.329 |

---

## 2026-09-17 (Thursday)

**Shadow summary:** Checked 330 / 197 agree / 37 V2_STRICTER / 1 V2_LOOSER / 92 state_mismatch / 3 nodata | index-gating v1 89% vs v2 100% | oscillation v1 1.06 vs v2 0.73 | warm 100% | day-flips v1 6/33 vs v2 2/33 | capture60 n=1899 mean -138 / v2-veto-neg 32% / v2-clear-neg 33% / σfwd-vs-rv30 MAE 0.25 vs 0.25 | veto-disagree 8%

| Ticker | v1 Action | v1 Regime | Earnings | v2 Eligible | v2 Gate | Divergence | sigma_fwd | FVRP | z | 1M/3M | accel_dn |
|--------|-----------|-----------|----------|-------------|---------|------------|-----------|------|------|-------|----------|
| AMZN | CONDITIONAL | NORMAL | 42d | No | NORMAL | V2_STRICTER | 0.334 | 0.92 | -0.27 | 0.852 | 0.962 |
| IWM | CONDITIONAL | NORMAL | ETF | No | CAUTION | V2_STRICTER | 0.213 | 0.89 | -0.54 | 0.950 | 0.991 |
| JNJ | CONDITIONAL | NORMAL | 26d | No | CAUTION | V2_STRICTER | 0.220 | 1.19 | +1.19 | 1.033 | 0.793 |
| KO | CONDITIONAL | NORMAL | 33d | No | NORMAL | V2_STRICTER | 0.203 | 0.92 | -0.10 | 0.895 | 0.830 |
| QQQ | CONDITIONAL | NORMAL | ETF | No | NORMAL | V2_STRICTER | 0.213 | 0.84 | -1.46 | 0.871 | 0.727 |
| SBUX | CONDITIONAL | NORMAL | 41d | No | CAUTION | V2_STRICTER | 0.299 | 0.98 | -0.27 | 0.926 | 1.242 |
| AAPL | NO EDGE | CAUTION | 42d | No | NORMAL | STATE_MISMATCH | 0.272 | 0.90 | +0.16 | 0.923 | 0.594 |
| CAT | NO EDGE | NORMAL | 42d | No | NORMAL | AGREE | 0.396 | 0.95 | -0.76 | 0.934 | 0.902 |
| EEM | NO EDGE | CAUTION | ETF | No | NORMAL | STATE_MISMATCH | 0.249 | 0.95 | -0.59 | 0.939 | 1.008 |
| GLD | NO EDGE | NORMAL | ETF | No | CAUTION | STATE_MISMATCH | 0.225 | 1.07 | -0.60 | 0.969 | 0.964 |
| GOOG | NO EDGE | NORMAL | 48d | No | NORMAL | AGREE | 0.292 | 1.01 | -0.04 | 0.877 | 0.679 |
| GS | NO EDGE | CAUTION | 26d | No | CAUTION | AGREE | 0.356 | 1.02 | +0.34 | 1.042 | 1.393 |
| HD | NO EDGE | NORMAL | 61d | No | NORMAL | AGREE | 0.257 | 1.00 | -0.04 | 0.881 | 1.003 |
| HOOD | NO EDGE | CAUTION | 48d | No | NORMAL | STATE_MISMATCH | 0.762 | 0.81 | -0.96 | 0.941 | 1.142 |
| JPM | REDUCE SIZE | CAUTION | 26d | No | CAUTION | AGREE | 0.284 | 0.92 | +0.03 | 1.029 | 1.058 |
| MCD | NO EDGE | NORMAL | 49d | No | NORMAL | AGREE | 0.210 | 1.06 | +0.58 | 0.932 | 1.119 |
| META | NO EDGE | NORMAL | 41d | No | NORMAL | AGREE | 0.402 | 0.97 | +0.42 | 0.922 | 0.402 |
| MSFT | NO EDGE | NORMAL | 41d | No | NORMAL | AGREE | 0.300 | 0.85 | -0.80 | 0.851 | 0.970 |
| NFLX | NO EDGE | CAUTION | 33d | No | CAUTION | AGREE | 0.384 | 0.92 | +0.14 | 0.906 | 1.141 |
| NKE | SELL PREMIUM | NORMAL | 12d | No | DANGER | STATE_MISMATCH | 0.307 | 1.41 | +1.16 | — | 0.940 |
| NVDA | NO EDGE | NORMAL | 62d | No | NORMAL | AGREE | 0.429 | 0.77 | -1.19 | 0.885 | 0.981 |
| PLTR | NO EDGE | CAUTION | 46d | No | NORMAL | STATE_MISMATCH | 0.613 | 0.80 | -0.21 | 0.867 | 0.859 |
| SPY | REDUCE SIZE | CAUTION | ETF | No | NORMAL | STATE_MISMATCH | 0.158 | 0.85 | -0.59 | 0.912 | 0.929 |
| TLT | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.126 | 0.94 | +0.75 | 0.925 | 0.928 |
| TSLA | NO EDGE | CAUTION | 41d | No | NORMAL | STATE_MISMATCH | 0.490 | 0.87 | +0.06 | 0.956 | 0.716 |
| UBER | NO EDGE | NORMAL | 47d | No | NORMAL | AGREE | 0.401 | 0.87 | +0.23 | 0.882 | 0.930 |
| WMT | NO EDGE | NORMAL | 63d | No | NORMAL | AGREE | 0.230 | 1.02 | -0.26 | 0.857 | 0.600 |
| XLB | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.209 | 0.99 | -0.73 | 1.070 | 0.986 |
| XLE | NO EDGE | NORMAL | ETF | No | CAUTION | STATE_MISMATCH | 0.288 | 0.91 | +0.43 | 0.965 | 1.407 |
| XLF | NO EDGE | CAUTION | ETF | No | CAUTION | AGREE | 0.202 | 0.82 | -0.55 | 0.954 | 1.363 |
| XLI | NO EDGE | CAUTION | ETF | No | DANGER | STATE_MISMATCH | 0.209 | 1.10 | +0.65 | 1.031 | 0.998 |
| XLV | NO EDGE | NORMAL | ETF | No | CAUTION | STATE_MISMATCH | 0.172 | 1.04 | +0.24 | 1.000 | 0.995 |
| XOM | NO EDGE | CAUTION | 43d | No | CAUTION | AGREE | 0.311 | 0.96 | +0.39 | 0.971 | 1.428 |

---

## 2026-09-16 (Wednesday)

**Shadow summary:** Checked 330 / 208 agree / 32 V2_STRICTER / 1 V2_LOOSER / 86 state_mismatch / 3 nodata | index-gating v1 91% vs v2 100% | oscillation v1 1.00 vs v2 0.76 | warm 100% | day-flips v1 4/33 vs v2 6/33 | capture60 n=1899 mean -140 / v2-veto-neg 32% / v2-clear-neg 33% / σfwd-vs-rv30 MAE 0.25 vs 0.25 | veto-disagree 8%

| Ticker | v1 Action | v1 Regime | Earnings | v2 Eligible | v2 Gate | Divergence | sigma_fwd | FVRP | z | 1M/3M | accel_dn |
|--------|-----------|-----------|----------|-------------|---------|------------|-----------|------|------|-------|----------|
| AMZN | CONDITIONAL | NORMAL | 43d | No | NORMAL | V2_STRICTER | 0.346 | 0.91 | -0.31 | 0.867 | 0.987 |
| IWM | CONDITIONAL | NORMAL | ETF | No | CAUTION | V2_STRICTER | 0.196 | 1.00 | +0.70 | 0.980 | 1.035 |
| JNJ | CONDITIONAL | NORMAL | 27d | No | CAUTION | V2_STRICTER | 0.239 | 1.11 | +0.53 | 1.008 | 0.851 |
| KO | CONDITIONAL | NORMAL | 34d | No | NORMAL | V2_STRICTER | 0.216 | 0.89 | -0.29 | 0.905 | 0.698 |
| QQQ | CONDITIONAL | NORMAL | ETF | No | NORMAL | V2_STRICTER | 0.212 | 0.90 | -0.82 | 0.902 | 0.781 |
| SPY | CONDITIONAL | NORMAL | ETF | No | NORMAL | V2_STRICTER | 0.146 | 0.98 | +0.63 | 0.933 | 0.918 |
| AAPL | NO EDGE | CAUTION | 43d | No | NORMAL | STATE_MISMATCH | 0.281 | 0.88 | -0.02 | 0.926 | 0.638 |
| CAT | NO EDGE | NORMAL | 43d | No | NORMAL | AGREE | 0.405 | 0.89 | -1.20 | 0.900 | 0.969 |
| EEM | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.253 | 0.93 | -0.71 | 0.929 | 1.082 |
| GLD | NO EDGE | NORMAL | ETF | No | CAUTION | STATE_MISMATCH | 0.210 | 1.17 | +0.09 | 0.990 | 1.015 |
| GOOG | NO EDGE | NORMAL | 49d | No | NORMAL | AGREE | 0.294 | 1.01 | -0.05 | 0.882 | 0.705 |
| GS | NO EDGE | CAUTION | 27d | No | CAUTION | AGREE | 0.349 | 1.06 | +0.66 | 1.071 | 1.174 |
| HD | NO EDGE | NORMAL | 62d | No | NORMAL | AGREE | 0.259 | 0.98 | -0.19 | 0.878 | 1.030 |
| HOOD | NO EDGE | CAUTION | 49d | No | NORMAL | STATE_MISMATCH | 0.734 | 0.86 | -0.30 | 0.950 | 0.899 |
| JPM | REDUCE SIZE | CAUTION | 27d | No | CAUTION | AGREE | 0.282 | 0.92 | +0.05 | 1.031 | 1.025 |
| MCD | NO EDGE | NORMAL | 50d | No | NORMAL | AGREE | 0.200 | 1.11 | +0.92 | 0.929 | 1.015 |
| META | NO EDGE | NORMAL | 42d | No | NORMAL | AGREE | 0.419 | 0.92 | +0.17 | 0.916 | 0.431 |
| MSFT | NO EDGE | NORMAL | 42d | No | NORMAL | AGREE | 0.306 | 0.85 | -0.80 | 0.852 | 0.913 |
| NFLX | NO EDGE | CAUTION | 34d | No | CAUTION | AGREE | 0.412 | 0.81 | -0.44 | 0.858 | 1.148 |
| NKE | SELL PREMIUM | NORMAL | 13d | No | DANGER | STATE_MISMATCH | 0.313 | 1.51 | +1.46 | 1.096 | 0.958 |
| NVDA | NO EDGE | NORMAL | 63d | No | NORMAL | AGREE | 0.446 | 0.75 | -1.49 | 0.889 | 1.054 |
| PLTR | NO EDGE | NORMAL | 47d | No | NORMAL | AGREE | 0.639 | 0.78 | -0.43 | 0.877 | 0.922 |
| SBUX | NO EDGE | NORMAL | 42d | No | CAUTION | STATE_MISMATCH | 0.293 | 0.94 | -0.42 | 0.869 | 1.334 |
| TLT | NO EDGE | CAUTION | ETF | No | NORMAL | STATE_MISMATCH | 0.127 | 1.04 | +1.66 | 0.967 | 0.997 |
| TSLA | NO EDGE | CAUTION | 42d | No | NORMAL | STATE_MISMATCH | 0.495 | 0.84 | -0.25 | 0.933 | 0.769 |
| UBER | NO EDGE | NORMAL | 48d | No | NORMAL | AGREE | 0.411 | 0.86 | +0.11 | 0.887 | 0.987 |
| WMT | NO EDGE | NORMAL | 64d | No | NORMAL | AGREE | 0.227 | 1.05 | -0.06 | 0.869 | 0.619 |
| XLB | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.189 | 0.91 | -1.12 | 0.795 | 0.986 |
| XLE | AVOID | DANGER | ETF | No | CAUTION | STATE_MISMATCH | 0.274 | 1.00 | +1.26 | 1.004 | 0.726 |
| XLF | NO EDGE | CAUTION | ETF | No | CAUTION | AGREE | 0.183 | 0.92 | +0.42 | 0.972 | 1.019 |
| XLI | NO EDGE | CAUTION | ETF | No | DANGER | STATE_MISMATCH | 0.212 | 1.09 | +0.62 | 1.052 | 1.072 |
| XLV | NO EDGE | CAUTION | ETF | No | DANGER | STATE_MISMATCH | 0.185 | 0.99 | -0.12 | 0.955 | 1.069 |
| XOM | NO EDGE | CAUTION | 44d | No | NORMAL | STATE_MISMATCH | 0.296 | 1.07 | +1.42 | 1.007 | 0.732 |

---

## 2026-09-15 (Tuesday)

**Shadow summary:** Checked 330 / 218 agree / 26 V2_STRICTER / 1 V2_LOOSER / 82 state_mismatch / 3 nodata | index-gating v1 94% vs v2 100% | oscillation v1 0.94 vs v2 0.61 | warm 100% | day-flips v1 6/33 vs v2 2/33 | capture60 n=1898 mean -142 / v2-veto-neg 32% / v2-clear-neg 33% / σfwd-vs-rv30 MAE 0.25 vs 0.24 | veto-disagree 8%

| Ticker | v1 Action | v1 Regime | Earnings | v2 Eligible | v2 Gate | Divergence | sigma_fwd | FVRP | z | 1M/3M | accel_dn |
|--------|-----------|-----------|----------|-------------|---------|------------|-----------|------|------|-------|----------|
| IWM | CONDITIONAL | NORMAL | ETF | No | CAUTION | V2_STRICTER | 0.200 | 0.95 | +0.17 | 0.952 | 1.036 |
| JNJ | CONDITIONAL | NORMAL | 28d | No | NORMAL | V2_STRICTER | 0.238 | 1.05 | +0.13 | 1.013 | 0.915 |
| KO | CONDITIONAL | NORMAL | 35d | No | NORMAL | V2_STRICTER | 0.225 | 0.80 | -1.11 | 0.869 | 0.746 |
| QQQ | CONDITIONAL | NORMAL | ETF | No | NORMAL | V2_STRICTER | 0.225 | 0.86 | -1.20 | 0.909 | 0.765 |
| SPY | CONDITIONAL | NORMAL | ETF | No | NORMAL | V2_STRICTER | 0.154 | 0.91 | +0.01 | 0.908 | 0.899 |
| AAPL | NO EDGE | CAUTION | 44d | No | NORMAL | STATE_MISMATCH | 0.286 | 0.88 | -0.05 | 0.919 | 0.661 |
| AMZN | NO EDGE | NORMAL | 44d | No | NORMAL | AGREE | 0.344 | 0.90 | -0.36 | 0.852 | 0.844 |
| CAT | NO EDGE | NORMAL | 44d | No | NORMAL | AGREE | 0.429 | 0.83 | -1.71 | 0.866 | 1.041 |
| EEM | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.271 | 0.87 | -1.05 | 0.943 | 1.157 |
| GLD | NO EDGE | NORMAL | ETF | No | CAUTION | STATE_MISMATCH | 0.223 | 1.10 | -0.39 | 0.993 | 1.090 |
| GOOG | NO EDGE | NORMAL | 50d | No | NORMAL | AGREE | 0.296 | 1.01 | -0.02 | 0.889 | 0.656 |
| GS | NO EDGE | CAUTION | 28d | No | CAUTION | AGREE | 0.343 | 1.05 | +0.62 | 1.035 | 1.224 |
| HD | NO EDGE | NORMAL | 63d | No | NORMAL | AGREE | 0.257 | 1.00 | -0.00 | 0.898 | 0.949 |
| HOOD | NO EDGE | CAUTION | 50d | No | NORMAL | STATE_MISMATCH | 0.665 | 0.96 | +0.74 | 0.938 | 0.784 |
| JPM | REDUCE SIZE | CAUTION | 28d | No | NORMAL | STATE_MISMATCH | 0.259 | 0.98 | +0.61 | 1.028 | 1.101 |
| MCD | NO EDGE | NORMAL | 51d | No | NORMAL | AGREE | 0.201 | 1.07 | +0.66 | 0.905 | 0.772 |
| META | NO EDGE | NORMAL | 43d | No | NORMAL | AGREE | 0.420 | 0.90 | +0.08 | 0.903 | 0.463 |
| MSFT | NO EDGE | NORMAL | 43d | No | NORMAL | AGREE | 0.293 | 0.88 | -0.64 | 0.841 | 0.751 |
| NFLX | NO EDGE | CAUTION | 35d | No | CAUTION | AGREE | 0.412 | 0.83 | -0.35 | 0.878 | 1.007 |
| NKE | SELL PREMIUM | NORMAL | 14d | No | DANGER | STATE_MISMATCH | 0.316 | 1.60 | +1.71 | — | 0.830 |
| NVDA | NO EDGE | NORMAL | 64d | No | NORMAL | AGREE | 0.466 | 0.72 | -1.80 | 0.889 | 1.132 |
| PLTR | NO EDGE | NORMAL | 48d | No | CAUTION | STATE_MISMATCH | 0.619 | 0.78 | -0.41 | 0.862 | 0.988 |
| SBUX | NO EDGE | NORMAL | 43d | No | CAUTION | STATE_MISMATCH | 0.283 | 1.00 | -0.18 | 0.879 | 1.133 |
| TLT | NO EDGE | NORMAL | ETF | No | CAUTION | STATE_MISMATCH | 0.132 | 0.95 | +0.82 | 0.968 | 1.045 |
| TSLA | NO EDGE | CAUTION | 43d | No | NORMAL | STATE_MISMATCH | 0.509 | 0.79 | -0.67 | 0.918 | 0.819 |
| UBER | NO EDGE | NORMAL | 49d | No | CAUTION | STATE_MISMATCH | 0.432 | 0.81 | -0.27 | 0.883 | 0.989 |
| WMT | NO EDGE | NORMAL | 65d | No | NORMAL | AGREE | 0.240 | 0.97 | -0.54 | 0.864 | 0.648 |
| XLB | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.194 | 0.99 | -0.76 | 1.000 | 1.059 |
| XLE | AVOID | DANGER | ETF | No | NORMAL | STATE_MISMATCH | 0.283 | 0.95 | +0.77 | 1.004 | 0.780 |
| XLF | NO EDGE | CAUTION | ETF | No | CAUTION | AGREE | 0.188 | 0.85 | -0.23 | 0.922 | 1.070 |
| XLI | NO EDGE | NORMAL | ETF | No | DANGER | STATE_MISMATCH | 0.220 | 0.93 | -0.38 | 0.983 | 1.113 |
| XLV | NO EDGE | NORMAL | ETF | No | DANGER | STATE_MISMATCH | 0.191 | 0.92 | -0.63 | 1.114 | 1.148 |
| XOM | AVOID | DANGER | 45d | No | NORMAL | STATE_MISMATCH | 0.307 | 0.96 | +0.45 | 0.973 | 0.786 |

---

## 2026-09-14 (Monday)

**Shadow summary:** Checked 330 / 229 agree / 21 V2_STRICTER / 1 V2_LOOSER / 76 state_mismatch / 3 nodata | index-gating v1 96% vs v2 100% | oscillation v1 0.91 vs v2 0.61 | warm 100% | day-flips v1 4/33 vs v2 2/33 | capture60 n=1898 mean -144 / v2-veto-neg 32% / v2-clear-neg 33% / σfwd-vs-rv30 MAE 0.25 vs 0.24 | veto-disagree 9%

| Ticker | v1 Action | v1 Regime | Earnings | v2 Eligible | v2 Gate | Divergence | sigma_fwd | FVRP | z | 1M/3M | accel_dn |
|--------|-----------|-----------|----------|-------------|---------|------------|-----------|------|------|-------|----------|
| GS | CONDITIONAL | NORMAL | 29d | No | NORMAL | V2_STRICTER | 0.314 | 1.08 | +0.88 | 1.002 | 0.597 |
| JNJ | CONDITIONAL | NORMAL | 29d | No | NORMAL | V2_STRICTER | 0.224 | 1.05 | +0.12 | 0.952 | 0.982 |
| JPM | CONDITIONAL | NORMAL | 29d | No | NORMAL | V2_STRICTER | 0.253 | 0.95 | +0.35 | 0.989 | 0.808 |
| KO | CONDITIONAL | NORMAL | 36d | No | NORMAL | V2_STRICTER | 0.201 | 0.88 | -0.38 | 0.876 | 0.802 |
| NKE | SELL PREMIUM | NORMAL | 15d | No | DANGER | V2_STRICTER | 0.313 | 1.44 | +1.26 | 1.067 | 0.891 |
| AAPL | NO EDGE | NORMAL | 45d | No | NORMAL | AGREE | 0.300 | 0.80 | -0.70 | 0.906 | 0.710 |
| AMZN | NO EDGE | NORMAL | 45d | No | NORMAL | AGREE | 0.327 | 0.91 | -0.30 | 0.836 | 0.806 |
| CAT | NO EDGE | NORMAL | 45d | No | NORMAL | AGREE | 0.350 | 1.04 | -0.10 | 0.897 | 0.593 |
| EEM | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.237 | 0.99 | -0.40 | 0.933 | 0.825 |
| GLD | NO EDGE | NORMAL | ETF | No | CAUTION | STATE_MISMATCH | 0.216 | 1.07 | -0.56 | 0.969 | 1.068 |
| GOOG | NO EDGE | NORMAL | 51d | No | NORMAL | AGREE | 0.298 | 0.95 | -0.40 | 0.865 | 0.704 |
| HD | NO EDGE | NORMAL | 64d | No | NORMAL | AGREE | 0.257 | 0.94 | -0.45 | 0.846 | 1.020 |
| HOOD | NO EDGE | CAUTION | 51d | No | NORMAL | STATE_MISMATCH | 0.694 | 0.86 | -0.35 | 0.896 | 0.843 |
| IWM | NO EDGE | NORMAL | ETF | No | CAUTION | STATE_MISMATCH | 0.206 | 0.88 | -0.61 | 0.934 | 1.096 |
| MCD | NO EDGE | NORMAL | 52d | No | NORMAL | AGREE | 0.194 | 1.07 | +0.67 | 0.891 | 0.829 |
| META | NO EDGE | NORMAL | 44d | No | NORMAL | AGREE | 0.431 | 0.85 | -0.19 | 0.883 | 0.498 |
| MSFT | NO EDGE | NORMAL | 44d | No | NORMAL | AGREE | 0.277 | 0.85 | -0.78 | 0.811 | 0.807 |
| NFLX | NO EDGE | NORMAL | 36d | No | CAUTION | STATE_MISMATCH | 0.373 | 0.91 | +0.09 | 0.886 | 1.082 |
| NVDA | NO EDGE | NORMAL | 65d | No | NORMAL | AGREE | 0.405 | 0.80 | -0.86 | 0.874 | 0.932 |
| PLTR | NO EDGE | NORMAL | 49d | No | CAUTION | STATE_MISMATCH | 0.579 | 0.78 | -0.37 | 0.832 | 1.061 |
| QQQ | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.207 | 0.90 | -0.73 | 0.888 | 0.706 |
| SBUX | NO EDGE | NORMAL | 44d | No | CAUTION | STATE_MISMATCH | 0.294 | 0.88 | -0.70 | 0.819 | 1.217 |
| SPY | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.152 | 0.86 | -0.50 | 0.875 | 0.881 |
| TLT | NO EDGE | NORMAL | ETF | No | CAUTION | STATE_MISMATCH | 0.134 | 0.83 | -0.51 | 0.894 | 1.122 |
| TSLA | NO EDGE | CAUTION | 44d | No | NORMAL | STATE_MISMATCH | 0.497 | 0.79 | -0.72 | 0.894 | 0.828 |
| UBER | NO EDGE | NORMAL | 50d | No | CAUTION | STATE_MISMATCH | 0.455 | 0.75 | -0.71 | 0.880 | 1.062 |
| WMT | NO EDGE | NORMAL | 66d | No | NORMAL | AGREE | 0.241 | 0.90 | -0.96 | 0.816 | 0.654 |
| XLB | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.200 | 1.10 | -0.30 | 1.069 | 1.038 |
| XLE | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.270 | 0.96 | +0.94 | 0.967 | 0.647 |
| XLF | NO EDGE | CAUTION | ETF | No | CAUTION | AGREE | 0.190 | 0.80 | -0.69 | 0.917 | 1.116 |
| XLI | NO EDGE | NORMAL | ETF | No | DANGER | STATE_MISMATCH | 0.193 | 0.85 | -0.96 | 0.837 | 0.983 |
| XLV | WATCHLIST | NORMAL | ETF | No | CAUTION | STATE_MISMATCH | 0.174 | 1.09 | +0.55 | 1.153 | 1.233 |
| XOM | NO EDGE | NORMAL | 46d | No | NORMAL | AGREE | 0.292 | 1.01 | +0.89 | 0.966 | 0.806 |

---

## 2026-09-11 (Friday)

**Shadow summary:** Checked 330 / 237 agree / 16 V2_STRICTER / 2 V2_LOOSER / 71 state_mismatch / 4 nodata | index-gating v1 96% vs v2 99% | oscillation v1 0.91 vs v2 0.61 | warm 100% | day-flips v1 4/33 vs v2 2/33 | capture60 n=1898 mean -146 / v2-veto-neg 32% / v2-clear-neg 33% / σfwd-vs-rv30 MAE 0.24 vs 0.24 | veto-disagree 10%

| Ticker | v1 Action | v1 Regime | Earnings | v2 Eligible | v2 Gate | Divergence | sigma_fwd | FVRP | z | 1M/3M | accel_dn |
|--------|-----------|-----------|----------|-------------|---------|------------|-----------|------|------|-------|----------|
| JPM | CONDITIONAL | NORMAL | 32d | No | NORMAL | V2_STRICTER | 0.239 | 0.98 | +0.59 | 0.954 | 0.868 |
| KO | CONDITIONAL | NORMAL | 39d | No | NORMAL | V2_STRICTER | 0.206 | 0.90 | -0.24 | 0.872 | 0.862 |
| NKE | SELL PREMIUM | NORMAL | 18d | No | DANGER | V2_STRICTER | 0.330 | 1.45 | +1.27 | 1.087 | 0.957 |
| SBUX | CONDITIONAL | NORMAL | 47d | No | CAUTION | V2_STRICTER | 0.301 | 1.07 | +0.10 | 1.014 | 1.296 |
| SPY | CONDITIONAL | NORMAL | ETF | No | NORMAL | V2_STRICTER | 0.141 | 0.99 | +0.69 | 0.925 | 0.946 |
| XLI | SELL PREMIUM | NORMAL | ETF | No | DANGER | V2_STRICTER | 0.185 | 1.29 | +1.70 | 1.384 | 1.056 |
| AAPL | NO EDGE | NORMAL | 48d | No | NORMAL | AGREE | 0.294 | 0.86 | -0.14 | 0.927 | 0.763 |
| AMZN | NO EDGE | NORMAL | 48d | No | NORMAL | AGREE | 0.331 | 0.92 | -0.25 | 0.839 | 0.865 |
| CAT | NO EDGE | NORMAL | 48d | No | NORMAL | AGREE | 0.341 | 1.09 | +0.24 | 0.914 | 0.637 |
| EEM | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.235 | 0.97 | -0.52 | 0.931 | 0.886 |
| GLD | AVOID | DANGER | ETF | No | CAUTION | STATE_MISMATCH | 0.212 | 1.22 | +0.42 | 1.023 | 1.147 |
| GOOG | NO EDGE | NORMAL | 54d | No | NORMAL | AGREE | 0.295 | 1.00 | -0.07 | 0.871 | 0.756 |
| GS | NO EDGE | NORMAL | 32d | No | NORMAL | AGREE | 0.303 | 1.10 | +1.02 | 0.974 | 0.642 |
| HD | NO EDGE | NORMAL | 67d | No | NORMAL | AGREE | 0.254 | 1.00 | +0.04 | 0.879 | 1.095 |
| HOOD | NO EDGE | CAUTION | 54d | No | NORMAL | STATE_MISMATCH | 0.707 | 0.88 | -0.08 | 0.924 | 0.899 |
| IWM | NO EDGE | NORMAL | ETF | No | CAUTION | STATE_MISMATCH | 0.198 | 1.00 | +0.71 | 0.986 | 1.177 |
| JNJ | WATCHLIST | NORMAL | 32d | No | CAUTION | STATE_MISMATCH | 0.228 | 1.04 | +0.04 | 0.921 | 1.049 |
| MCD | NO EDGE | NORMAL | 55d | No | NORMAL | AGREE | 0.199 | 1.08 | +0.69 | 0.897 | 0.886 |
| META | NO EDGE | NORMAL | 47d | No | NORMAL | AGREE | 0.450 | 0.87 | -0.12 | 0.902 | 0.535 |
| MSFT | NO EDGE | NORMAL | 47d | No | NORMAL | AGREE | 0.282 | 0.92 | -0.38 | 0.848 | 0.867 |
| NFLX | NO EDGE | NORMAL | 39d | No | CAUTION | STATE_MISMATCH | 0.377 | 0.88 | -0.07 | 0.865 | 1.162 |
| NVDA | NO EDGE | CAUTION | 68d | No | NORMAL | STATE_MISMATCH | 0.409 | 0.82 | -0.69 | 0.878 | 1.001 |
| PLTR | NO EDGE | NORMAL | 52d | No | CAUTION | STATE_MISMATCH | 0.594 | 0.80 | -0.21 | 0.853 | 1.140 |
| QQQ | WATCHLIST | NORMAL | ETF | No | NORMAL | AGREE | 0.208 | 0.94 | -0.28 | 0.922 | 0.758 |
| TLT | NO EDGE | CAUTION | ETF | No | NORMAL | STATE_MISMATCH | 0.136 | 0.94 | +0.71 | 0.967 | 1.206 |
| TSLA | NO EDGE | CAUTION | 47d | No | NORMAL | STATE_MISMATCH | 0.530 | 0.76 | -0.96 | 0.908 | 0.889 |
| UBER | NO EDGE | NORMAL | 53d | No | CAUTION | STATE_MISMATCH | 0.479 | 0.78 | -0.48 | 0.949 | 1.109 |
| WMT | NO EDGE | NORMAL | 69d | No | NORMAL | AGREE | 0.233 | 0.99 | -0.39 | 0.832 | 0.703 |
| XLB | NO DATA | NORMAL | ETF | No | NORMAL | NODATA_SKEW | — | — | — | — | — |
| XLE | NO EDGE | CAUTION | ETF | No | NORMAL | STATE_MISMATCH | 0.284 | 0.90 | +0.32 | 0.957 | 0.695 |
| XLF | REDUCE SIZE | CAUTION | ETF | No | CAUTION | AGREE | 0.175 | 1.02 | +1.32 | 1.044 | 1.199 |
| XLV | NO EDGE | NORMAL | ETF | No | CAUTION | STATE_MISMATCH | 0.173 | 1.04 | +0.25 | 0.939 | 1.322 |
| XOM | NO EDGE | NORMAL | 49d | No | NORMAL | AGREE | 0.307 | 0.97 | +0.48 | 0.967 | 0.866 |

---

## 2026-09-10 (Thursday)

**Shadow summary:** Checked 330 / 248 agree / 10 V2_STRICTER / 2 V2_LOOSER / 67 state_mismatch / 3 nodata | index-gating v1 98% vs v2 99% | oscillation v1 0.85 vs v2 0.55 | warm 100% | day-flips v1 2/33 vs v2 5/33 | capture60 n=1898 mean -147 / v2-veto-neg 32% / v2-clear-neg 33% / σfwd-vs-rv30 MAE 0.24 vs 0.24 | veto-disagree 10%

| Ticker | v1 Action | v1 Regime | Earnings | v2 Eligible | v2 Gate | Divergence | sigma_fwd | FVRP | z | 1M/3M | accel_dn |
|--------|-----------|-----------|----------|-------------|---------|------------|-----------|------|------|-------|----------|
| JPM | CONDITIONAL | NORMAL | 33d | No | NORMAL | V2_STRICTER | 0.254 | 0.94 | +0.21 | 0.960 | 0.917 |
| KO | CONDITIONAL | NORMAL | 40d | No | NORMAL | V2_STRICTER | 0.187 | 1.03 | +0.72 | 0.910 | 0.925 |
| NKE | SELL PREMIUM | NORMAL | 19d | No | DANGER | V2_STRICTER | 0.336 | 1.44 | +1.25 | 1.113 | 0.889 |
| XLI | CONDITIONAL | NORMAL | ETF | No | NORMAL | V2_STRICTER | 0.184 | 1.19 | +1.21 | 1.078 | 1.081 |
| AAPL | NO EDGE | CAUTION | 49d | No | NORMAL | STATE_MISMATCH | 0.307 | 0.85 | -0.25 | 0.956 | 0.819 |
| AMZN | NO EDGE | NORMAL | 49d | No | NORMAL | AGREE | 0.341 | 0.91 | -0.27 | 0.854 | 0.927 |
| CAT | NO EDGE | NORMAL | 49d | No | NORMAL | AGREE | 0.345 | 1.10 | +0.33 | 0.911 | 0.612 |
| EEM | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.197 | 1.19 | +0.54 | 0.943 | 0.464 |
| GLD | NO EDGE | CAUTION | ETF | No | CAUTION | AGREE | 0.217 | 1.16 | +0.06 | 1.018 | 1.103 |
| GOOG | NO EDGE | NORMAL | 55d | No | NORMAL | AGREE | 0.311 | 0.93 | -0.52 | 0.850 | 0.812 |
| GS | NO EDGE | NORMAL | 33d | No | NORMAL | AGREE | 0.306 | 1.09 | +0.98 | 0.963 | 0.625 |
| HD | NO EDGE | NORMAL | 68d | No | NORMAL | AGREE | 0.258 | 1.00 | +0.02 | 0.902 | 1.075 |
| HOOD | NO EDGE | CAUTION | 55d | No | NORMAL | STATE_MISMATCH | 0.721 | 0.86 | -0.34 | 0.916 | 0.928 |
| IWM | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.191 | 1.00 | +0.72 | 0.972 | 1.139 |
| JNJ | NO EDGE | NORMAL | 33d | No | CAUTION | STATE_MISMATCH | 0.224 | 1.08 | +0.37 | 0.941 | 1.121 |
| MCD | NO EDGE | NORMAL | 56d | No | NORMAL | AGREE | 0.198 | 1.08 | +0.72 | 0.908 | 0.949 |
| META | NO EDGE | NORMAL | 48d | No | NORMAL | AGREE | 0.474 | 0.84 | -0.26 | 0.915 | 0.451 |
| MSFT | NO EDGE | NORMAL | 48d | No | NORMAL | AGREE | 0.278 | 0.92 | -0.38 | 0.835 | 0.931 |
| NFLX | NO EDGE | NORMAL | 40d | No | CAUTION | STATE_MISMATCH | 0.384 | 0.86 | -0.18 | 0.841 | 1.249 |
| NVDA | NO EDGE | CAUTION | 69d | No | NORMAL | STATE_MISMATCH | 0.405 | 0.85 | -0.37 | 0.874 | 0.926 |
| PLTR | NO EDGE | NORMAL | 53d | No | CAUTION | STATE_MISMATCH | 0.598 | 0.80 | -0.26 | 0.848 | 1.172 |
| QQQ | WATCHLIST | NORMAL | ETF | No | NORMAL | AGREE | 0.183 | 1.10 | +1.25 | 0.935 | 0.589 |
| SBUX | NO EDGE | NORMAL | 48d | No | CAUTION | STATE_MISMATCH | 0.291 | 0.88 | -0.73 | 0.803 | 1.364 |
| SPY | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.131 | 1.07 | +1.31 | 0.919 | 0.871 |
| TLT | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.122 | 0.95 | +0.77 | 0.952 | 0.802 |
| TSLA | NO EDGE | CAUTION | 48d | No | NORMAL | STATE_MISMATCH | 0.522 | 0.81 | -0.55 | 0.937 | 0.937 |
| UBER | NO EDGE | NORMAL | 54d | No | CAUTION | STATE_MISMATCH | 0.414 | 0.84 | +0.03 | 0.897 | 1.191 |
| WMT | NO EDGE | NORMAL | 70d | No | NORMAL | AGREE | 0.236 | 0.98 | -0.44 | 0.835 | 0.755 |
| XLB | NO DATA | NORMAL | ETF | No | NORMAL | NODATA_SKEW | — | — | — | — | — |
| XLE | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.271 | 0.97 | +1.04 | 0.987 | 0.671 |
| XLF | NO EDGE | CAUTION | ETF | No | CAUTION | AGREE | 0.183 | 0.82 | -0.49 | 0.875 | 1.269 |
| XLV | NO EDGE | NORMAL | ETF | No | CAUTION | STATE_MISMATCH | 0.185 | 0.93 | -0.54 | 0.968 | 1.399 |
| XOM | NO EDGE | NORMAL | 50d | No | NORMAL | AGREE | 0.295 | 1.00 | +0.77 | 0.960 | 0.930 |

---

## 2026-09-09 (Wednesday)

**Shadow summary:** Checked 330 / 256 agree / 6 V2_STRICTER / 2 V2_LOOSER / 64 state_mismatch / 2 nodata | index-gating v1 99% vs v2 99% | oscillation v1 0.91 vs v2 0.48 | warm 100% | day-flips v1 3/33 vs v2 1/33 | capture60 n=1898 mean -150 / v2-veto-neg 32% / v2-clear-neg 33% / σfwd-vs-rv30 MAE 0.24 vs 0.23 | veto-disagree 11%

| Ticker | v1 Action | v1 Regime | Earnings | v2 Eligible | v2 Gate | Divergence | sigma_fwd | FVRP | z | 1M/3M | accel_dn |
|--------|-----------|-----------|----------|-------------|---------|------------|-----------|------|------|-------|----------|
| NKE | SELL PREMIUM | NORMAL | 20d | No | DANGER | V2_STRICTER | 0.328 | 1.44 | +1.26 | 1.083 | 0.790 |
| XLE | CONDITIONAL | NORMAL | ETF | No | NORMAL | V2_STRICTER | 0.271 | 1.08 | +1.97 | 1.089 | 0.721 |
| GS | NO EDGE | NORMAL | 34d | Yes | NORMAL | V2_LOOSER | 0.288 | 1.15 | +1.49 | 0.951 | 0.624 |
| AAPL | NO EDGE | CAUTION | 50d | No | NORMAL | STATE_MISMATCH | 0.299 | 0.89 | +0.09 | 0.959 | 0.876 |
| AMZN | NO EDGE | NORMAL | 50d | No | NORMAL | AGREE | 0.323 | 0.97 | +0.03 | 0.855 | 0.821 |
| CAT | NO EDGE | NORMAL | 50d | No | NORMAL | AGREE | 0.352 | 1.09 | +0.29 | 0.928 | 0.628 |
| EEM | WATCHLIST | NORMAL | ETF | No | NORMAL | AGREE | 0.194 | 1.14 | +0.30 | 0.908 | 0.453 |
| GLD | NO EDGE | CAUTION | ETF | No | CAUTION | AGREE | 0.211 | 1.18 | +0.18 | 1.009 | 1.185 |
| GOOG | NO EDGE | NORMAL | 56d | No | NORMAL | AGREE | 0.292 | 1.02 | +0.03 | 0.866 | 0.628 |
| HD | NO EDGE | NORMAL | 69d | No | NORMAL | AGREE | 0.256 | 1.03 | +0.27 | 0.920 | 1.109 |
| HOOD | NO EDGE | CAUTION | 56d | No | NORMAL | STATE_MISMATCH | 0.738 | 0.86 | -0.35 | 0.935 | 0.960 |
| IWM | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.182 | 0.99 | +0.59 | 0.924 | 0.920 |
| JNJ | NO EDGE | NORMAL | 34d | No | NORMAL | AGREE | 0.239 | 1.00 | -0.34 | 0.915 | 1.170 |
| JPM | NO EDGE | NORMAL | 34d | No | NORMAL | AGREE | 0.248 | 0.93 | +0.14 | 0.927 | 0.985 |
| KO | NO EDGE | NORMAL | 41d | No | NORMAL | AGREE | 0.194 | 0.97 | +0.27 | 0.887 | 0.865 |
| MCD | NO EDGE | NORMAL | 57d | No | NORMAL | AGREE | 0.204 | 1.04 | +0.46 | 0.908 | 0.952 |
| META | NO EDGE | NORMAL | 49d | No | NORMAL | AGREE | 0.389 | 1.00 | +0.56 | 0.916 | 0.484 |
| MSFT | NO EDGE | NORMAL | 49d | No | NORMAL | AGREE | 0.299 | 0.86 | -0.70 | 0.843 | 0.986 |
| NFLX | NO EDGE | CAUTION | 41d | No | CAUTION | AGREE | 0.412 | 0.80 | -0.48 | 0.844 | 1.326 |
| NVDA | NO EDGE | CAUTION | 70d | No | NORMAL | STATE_MISMATCH | 0.438 | 0.78 | -1.09 | 0.878 | 0.970 |
| PLTR | NO EDGE | NORMAL | 54d | No | CAUTION | STATE_MISMATCH | 0.641 | 0.75 | -0.68 | 0.853 | 1.257 |
| QQQ | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.186 | 1.01 | +0.45 | 0.903 | 0.614 |
| SBUX | NO EDGE | NORMAL | 49d | No | NORMAL | AGREE | 0.282 | 1.09 | +0.15 | 0.954 | 1.303 |
| SPY | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.132 | 0.99 | +0.74 | 0.887 | 0.839 |
| TLT | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.113 | 1.02 | +1.50 | 0.981 | 0.642 |
| TSLA | NO EDGE | CAUTION | 49d | No | NORMAL | STATE_MISMATCH | 0.553 | 0.74 | -1.18 | 0.925 | 1.007 |
| UBER | NO EDGE | NORMAL | 55d | No | NORMAL | AGREE | 0.434 | 0.85 | +0.07 | 0.914 | 1.132 |
| WMT | NO EDGE | NORMAL | 71d | No | NORMAL | AGREE | 0.235 | 1.04 | -0.14 | 0.862 | 0.810 |
| XLB | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.198 | 0.99 | -0.76 | 0.964 | 0.933 |
| XLF | NO EDGE | CAUTION | ETF | No | NORMAL | STATE_MISMATCH | 0.187 | 0.85 | -0.17 | 0.951 | 1.337 |
| XLI | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.176 | 1.00 | +0.08 | 0.880 | 0.882 |
| XLV | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.202 | 0.87 | -1.00 | 0.890 | 1.497 |
| XOM | NO EDGE | CAUTION | 51d | No | NORMAL | STATE_MISMATCH | 0.297 | 0.99 | +0.76 | 0.999 | 0.999 |

---

## 2026-09-08 (Tuesday)

**Shadow summary:** Checked 330 / 259 agree / 4 V2_STRICTER / 1 V2_LOOSER / 64 state_mismatch / 2 nodata | index-gating v1 100% vs v2 99% | oscillation v1 0.88 vs v2 0.55 | warm 100% | day-flips v1 3/33 vs v2 2/33 | capture60 n=1899 mean -153 / v2-veto-neg 32% / v2-clear-neg 33% / σfwd-vs-rv30 MAE 0.23 vs 0.23 | veto-disagree 7%

| Ticker | v1 Action | v1 Regime | Earnings | v2 Eligible | v2 Gate | Divergence | sigma_fwd | FVRP | z | 1M/3M | accel_dn |
|--------|-----------|-----------|----------|-------------|---------|------------|-----------|------|------|-------|----------|
| NKE | SELL PREMIUM | NORMAL | 21d | No | DANGER | V2_STRICTER | 0.338 | 1.39 | +1.09 | 1.109 | 0.821 |
| AAPL | NO EDGE | NORMAL | 51d | No | NORMAL | AGREE | 0.302 | 0.82 | -0.49 | 0.926 | 0.870 |
| AMZN | NO EDGE | NORMAL | 51d | No | NORMAL | AGREE | 0.334 | 0.90 | -0.35 | 0.850 | 0.862 |
| CAT | WATCHLIST | NORMAL | 51d | No | NORMAL | AGREE | 0.357 | 1.03 | -0.15 | 0.913 | 0.674 |
| EEM | WATCHLIST | NORMAL | ETF | No | NORMAL | AGREE | 0.200 | 1.02 | -0.21 | 0.869 | 0.487 |
| GLD | NO EDGE | NORMAL | ETF | No | CAUTION | STATE_MISMATCH | 0.222 | 1.08 | -0.54 | 0.987 | 1.151 |
| GOOG | NO EDGE | NORMAL | 57d | No | NORMAL | AGREE | 0.287 | 0.98 | -0.20 | 0.857 | 0.675 |
| GS | WATCHLIST | NORMAL | 35d | No | NORMAL | AGREE | 0.301 | 1.03 | +0.50 | 0.929 | 0.668 |
| HD | NO EDGE | NORMAL | 70d | No | NORMAL | AGREE | 0.252 | 0.99 | -0.02 | 0.882 | 0.929 |
| HOOD | NO EDGE | CAUTION | 57d | No | NORMAL | STATE_MISMATCH | 0.762 | 0.80 | -0.96 | 0.922 | 0.825 |
| IWM | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.191 | 0.86 | -0.83 | 0.883 | 0.947 |
| JNJ | WATCHLIST | NORMAL | 35d | No | NORMAL | AGREE | 0.231 | 0.98 | -0.50 | 0.865 | 0.866 |
| JPM | NO EDGE | NORMAL | 35d | No | NORMAL | AGREE | 0.256 | 0.83 | -0.75 | 0.882 | 0.755 |
| KO | NO EDGE | NORMAL | 42d | No | NORMAL | AGREE | 0.198 | 0.90 | -0.24 | 0.876 | 0.929 |
| MCD | NO EDGE | NORMAL | 58d | No | NORMAL | AGREE | 0.213 | 0.94 | -0.30 | 0.875 | 1.023 |
| META | NO EDGE | NORMAL | 50d | No | NORMAL | AGREE | 0.401 | 0.88 | -0.01 | 0.875 | 0.504 |
| MSFT | NO EDGE | NORMAL | 50d | No | NORMAL | AGREE | 0.298 | 0.81 | -1.03 | 0.825 | 0.981 |
| NFLX | NO EDGE | CAUTION | 42d | No | NORMAL | STATE_MISMATCH | 0.425 | 0.76 | -0.70 | 0.851 | 1.372 |
| NVDA | NO EDGE | CAUTION | 71d | No | NORMAL | STATE_MISMATCH | 0.436 | 0.79 | -1.04 | 0.893 | 0.922 |
| PLTR | NO EDGE | NORMAL | 55d | No | CAUTION | STATE_MISMATCH | 0.678 | 0.68 | -1.28 | 0.850 | 1.303 |
| QQQ | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.190 | 0.92 | -0.52 | 0.873 | 0.659 |
| SBUX | NO EDGE | NORMAL | 50d | No | NORMAL | AGREE | 0.277 | 1.00 | -0.18 | 0.902 | 1.035 |
| SPY | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.136 | 0.90 | -0.06 | 0.857 | 0.752 |
| TLT | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.116 | 0.90 | +0.28 | 0.896 | 0.810 |
| TSLA | NO EDGE | CAUTION | 50d | No | NORMAL | STATE_MISMATCH | 0.587 | 0.68 | -1.86 | 0.918 | 1.081 |
| UBER | NO EDGE | NORMAL | 56d | No | NORMAL | AGREE | 0.436 | 0.82 | -0.13 | 0.913 | 0.906 |
| WMT | NO EDGE | NORMAL | 72d | No | NORMAL | AGREE | 0.247 | 0.90 | -0.93 | 0.827 | 0.869 |
| XLB | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.208 | 0.86 | -1.36 | 0.802 | 0.846 |
| XLE | WATCHLIST | NORMAL | ETF | No | NORMAL | AGREE | 0.267 | 0.93 | +0.60 | 0.966 | 0.774 |
| XLF | NO EDGE | CAUTION | ETF | No | NORMAL | STATE_MISMATCH | 0.188 | 0.80 | -0.74 | 0.873 | 1.072 |
| XLI | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.185 | 0.99 | +0.01 | 0.864 | 0.914 |
| XLV | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.183 | 0.86 | -1.08 | 0.880 | 1.009 |
| XOM | NO EDGE | NORMAL | 52d | No | NORMAL | AGREE | 0.279 | 0.95 | +0.37 | 0.926 | 1.073 |

---

## 2026-09-04 (Friday)

**Shadow summary:** Checked 330 / 258 agree / 4 V2_STRICTER / 1 V2_LOOSER / 65 state_mismatch / 2 nodata | index-gating v1 98% vs v2 98% | oscillation v1 0.88 vs v2 0.52 | warm 100% | day-flips v1 3/33 vs v2 2/33 | capture60 n=1905 mean -156 / v2-veto-neg 32% / v2-clear-neg 33% / σfwd-vs-rv30 MAE 0.23 vs 0.23 | veto-disagree 5%

| Ticker | v1 Action | v1 Regime | Earnings | v2 Eligible | v2 Gate | Divergence | sigma_fwd | FVRP | z | 1M/3M | accel_dn |
|--------|-----------|-----------|----------|-------------|---------|------------|-----------|------|------|-------|----------|
| NKE | SELL PREMIUM | NORMAL | 25d | No | CAUTION | V2_STRICTER | 0.332 | 1.38 | +1.06 | 1.092 | 0.843 |
| AAPL | NO EDGE | NORMAL | 55d | No | NORMAL | AGREE | 0.284 | 0.88 | +0.00 | 0.924 | 0.462 |
| AMZN | NO EDGE | NORMAL | 55d | No | NORMAL | AGREE | 0.323 | 0.90 | -0.36 | 0.813 | 0.925 |
| CAT | NO EDGE | NORMAL | 55d | No | NORMAL | AGREE | 0.365 | 0.98 | -0.45 | 0.896 | 0.724 |
| EEM | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.202 | 0.94 | -0.64 | 0.892 | 0.523 |
| GLD | NO EDGE | CAUTION | ETF | No | CAUTION | AGREE | 0.227 | 1.08 | -0.52 | 0.995 | 1.208 |
| GOOG | NO EDGE | NORMAL | 61d | No | NORMAL | AGREE | 0.290 | 0.94 | -0.43 | 0.823 | 0.659 |
| GS | NO EDGE | NORMAL | 39d | No | NORMAL | AGREE | 0.312 | 0.96 | -0.12 | 0.919 | 0.717 |
| HD | NO EDGE | NORMAL | 74d | No | NORMAL | AGREE | 0.257 | 0.94 | -0.40 | 0.900 | 0.998 |
| HOOD | NO EDGE | CAUTION | 61d | No | NORMAL | STATE_MISMATCH | 0.781 | 0.83 | -0.70 | 0.950 | 0.819 |
| IWM | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.196 | 0.84 | -1.09 | 0.902 | 1.017 |
| JNJ | WATCHLIST | NORMAL | 39d | No | NORMAL | AGREE | 0.235 | 0.94 | -0.80 | 0.874 | 0.770 |
| JPM | NO EDGE | NORMAL | 39d | No | NORMAL | AGREE | 0.250 | 0.83 | -0.81 | 0.897 | 0.620 |
| KO | NO EDGE | NORMAL | 46d | No | NORMAL | AGREE | 0.201 | 0.86 | -0.61 | 0.831 | 0.896 |
| MCD | NO EDGE | NORMAL | 62d | No | NORMAL | AGREE | 0.219 | 0.95 | -0.23 | 0.912 | 0.918 |
| META | NO EDGE | NORMAL | 54d | No | NORMAL | AGREE | 0.424 | 0.82 | -0.35 | 0.850 | 0.541 |
| MSFT | NO EDGE | NORMAL | 54d | No | NORMAL | AGREE | 0.308 | 0.78 | -1.19 | 0.801 | 0.738 |
| NFLX | NO EDGE | NORMAL | 46d | No | NORMAL | AGREE | 0.385 | 0.81 | -0.43 | 0.819 | 0.570 |
| NVDA | NO EDGE | CAUTION | 75d | No | CAUTION | AGREE | 0.444 | 0.75 | -1.52 | 0.872 | 0.990 |
| PLTR | NO EDGE | NORMAL | 59d | No | CAUTION | STATE_MISMATCH | 0.694 | 0.70 | -1.16 | 0.846 | 1.198 |
| QQQ | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.197 | 0.87 | -1.15 | 0.874 | 0.707 |
| SBUX | NO EDGE | CAUTION | 54d | No | NORMAL | STATE_MISMATCH | 0.281 | 0.99 | -0.21 | 0.884 | 0.950 |
| SPY | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.141 | 0.84 | -0.61 | 0.861 | 0.726 |
| TLT | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.120 | 0.93 | +0.63 | 0.976 | 0.870 |
| TSLA | NO EDGE | CAUTION | 54d | No | NORMAL | STATE_MISMATCH | 0.544 | 0.79 | -0.74 | 0.945 | 0.652 |
| UBER | NO EDGE | NORMAL | 60d | No | NORMAL | AGREE | 0.456 | 0.77 | -0.52 | 0.883 | 0.971 |
| WMT | NO EDGE | NORMAL | 76d | No | NORMAL | AGREE | 0.262 | 0.84 | -1.36 | 0.836 | 0.904 |
| XLB | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.210 | 0.98 | -0.82 | 0.935 | 0.888 |
| XLE | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.261 | 0.91 | +0.43 | 0.924 | 0.690 |
| XLF | NO EDGE | CAUTION | ETF | No | NORMAL | STATE_MISMATCH | 0.181 | 0.75 | -1.26 | 0.811 | 0.966 |
| XLI | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.195 | 1.05 | +0.38 | 1.109 | 0.981 |
| XLV | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.180 | 0.80 | -1.58 | 0.784 | 0.850 |
| XOM | NO EDGE | NORMAL | 56d | No | NORMAL | AGREE | 0.283 | 0.97 | +0.54 | 0.936 | 0.915 |

---

## 2026-09-03 (Thursday)

**Shadow summary:** Checked 330 / 254 agree / 3 V2_STRICTER / 1 V2_LOOSER / 70 state_mismatch / 2 nodata | index-gating v1 98% vs v2 98% | oscillation v1 1.00 vs v2 0.58 | warm 100% | day-flips v1 4/33 vs v2 3/33 | capture60 n=1906 mean -162 / v2-veto-neg 33% / v2-clear-neg 33% / σfwd-vs-rv30 MAE 0.23 vs 0.23 | veto-disagree 6%

| Ticker | v1 Action | v1 Regime | Earnings | v2 Eligible | v2 Gate | Divergence | sigma_fwd | FVRP | z | 1M/3M | accel_dn |
|--------|-----------|-----------|----------|-------------|---------|------------|-----------|------|------|-------|----------|
| NKE | SELL PREMIUM | NORMAL | 26d | No | CAUTION | V2_STRICTER | 0.321 | 1.41 | +1.18 | — | 0.906 |
| AAPL | NO EDGE | NORMAL | 56d | No | NORMAL | AGREE | 0.294 | 0.84 | -0.32 | 0.928 | 0.496 |
| AMZN | NO EDGE | NORMAL | 56d | No | NORMAL | AGREE | 0.344 | 0.83 | -0.72 | 0.810 | 0.993 |
| CAT | NO EDGE | NORMAL | 56d | No | NORMAL | AGREE | 0.358 | 0.99 | -0.41 | 0.873 | 0.778 |
| EEM | WATCHLIST | NORMAL | ETF | No | NORMAL | AGREE | 0.197 | 1.01 | -0.29 | 0.897 | 0.562 |
| GLD | NO EDGE | NORMAL | ETF | No | CAUTION | STATE_MISMATCH | 0.219 | 1.11 | -0.34 | 1.000 | 1.297 |
| GOOG | NO EDGE | NORMAL | 62d | No | NORMAL | AGREE | 0.299 | 0.91 | -0.65 | 0.823 | 0.707 |
| GS | NO EDGE | NORMAL | 40d | No | NORMAL | AGREE | 0.325 | 0.90 | -0.75 | 0.900 | 0.770 |
| HD | NO EDGE | NORMAL | 75d | No | NORMAL | AGREE | 0.254 | 0.99 | -0.07 | 0.904 | 1.072 |
| HOOD | NO EDGE | CAUTION | 62d | No | NORMAL | STATE_MISMATCH | 0.684 | 0.95 | +0.64 | 0.962 | 0.879 |
| IWM | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.193 | 0.90 | -0.47 | 0.932 | 1.092 |
| JNJ | NO EDGE | NORMAL | 40d | No | NORMAL | AGREE | 0.243 | 0.95 | -0.73 | 0.916 | 0.827 |
| JPM | NO EDGE | NORMAL | 40d | No | NORMAL | AGREE | 0.254 | 0.81 | -0.97 | 0.878 | 0.666 |
| KO | NO EDGE | NORMAL | 47d | No | NORMAL | AGREE | 0.208 | 0.86 | -0.57 | 0.869 | 0.963 |
| MCD | NO EDGE | NORMAL | 63d | No | NORMAL | AGREE | 0.200 | 1.01 | +0.22 | 0.909 | 0.965 |
| META | WATCHLIST | NORMAL | 55d | No | NORMAL | AGREE | 0.431 | 0.83 | -0.32 | 0.859 | 0.582 |
| MSFT | NO EDGE | NORMAL | 55d | No | NORMAL | AGREE | 0.297 | 0.80 | -1.08 | 0.801 | 0.793 |
| NFLX | NO EDGE | NORMAL | 47d | No | NORMAL | AGREE | 0.394 | 0.79 | -0.54 | 0.807 | 0.612 |
| NVDA | NO EDGE | CAUTION | 76d | No | CAUTION | AGREE | 0.467 | 0.70 | -2.09 | 0.884 | 1.063 |
| PLTR | NO EDGE | NORMAL | 60d | No | NORMAL | AGREE | 0.679 | 0.68 | -1.33 | 0.837 | 1.287 |
| QQQ | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.204 | 0.84 | -1.42 | 0.879 | 0.760 |
| SBUX | NO EDGE | CAUTION | 55d | No | NORMAL | STATE_MISMATCH | 0.280 | 0.92 | -0.53 | 0.809 | 0.943 |
| SPY | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.142 | 0.83 | -0.77 | 0.864 | 0.780 |
| TLT | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.122 | 0.93 | +0.57 | 0.978 | 0.935 |
| TSLA | NO EDGE | NORMAL | 55d | No | NORMAL | AGREE | 0.513 | 0.81 | -0.58 | 0.923 | 0.701 |
| UBER | NO EDGE | NORMAL | 61d | No | CAUTION | STATE_MISMATCH | 0.431 | 0.82 | -0.12 | 0.878 | 1.032 |
| WMT | NO EDGE | NORMAL | 77d | No | NORMAL | AGREE | 0.264 | 0.83 | -1.42 | 0.840 | 0.934 |
| XLB | NO DATA | NORMAL | ETF | No | NORMAL | NODATA_SKEW | — | — | — | — | — |
| XLE | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.274 | 0.89 | +0.24 | 0.950 | 0.624 |
| XLF | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.188 | 0.77 | -1.08 | 0.888 | 1.038 |
| XLI | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.192 | 0.71 | -2.11 | 0.641 | 1.054 |
| XLV | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.179 | 0.91 | -0.69 | 0.850 | 0.913 |
| XOM | NO EDGE | NORMAL | 57d | No | NORMAL | AGREE | 0.289 | 0.97 | +0.59 | 0.950 | 0.835 |

---

## 2026-09-02 (Wednesday)

**Shadow summary:** Checked 330 / 252 agree / 4 V2_STRICTER / 1 V2_LOOSER / 72 state_mismatch / 1 nodata | index-gating v1 96% vs v2 98% | oscillation v1 1.00 vs v2 0.52 | warm 100% | day-flips v1 2/33 vs v2 1/33 | capture60 n=1907 mean -173 / v2-veto-neg 34% / v2-clear-neg 33% / σfwd-vs-rv30 MAE 0.22 vs 0.22

| Ticker | v1 Action | v1 Regime | Earnings | v2 Eligible | v2 Gate | Divergence | sigma_fwd | FVRP | z | 1M/3M | accel_dn |
|--------|-----------|-----------|----------|-------------|---------|------------|-----------|------|------|-------|----------|
| NKE | CONDITIONAL | NORMAL | 27d | No | CAUTION | V2_STRICTER | 0.323 | 1.42 | +1.21 | 1.086 | 0.973 |
| AAPL | NO EDGE | NORMAL | 57d | No | NORMAL | AGREE | 0.307 | 0.81 | -0.66 | 0.927 | 0.533 |
| AMZN | NO EDGE | NORMAL | 57d | No | NORMAL | AGREE | 0.365 | 0.79 | -0.99 | 0.817 | 1.067 |
| CAT | NO EDGE | NORMAL | 57d | No | NORMAL | AGREE | 0.351 | 1.00 | -0.29 | 0.868 | 0.835 |
| EEM | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.209 | 1.03 | -0.17 | 0.954 | 0.604 |
| GLD | NO EDGE | CAUTION | ETF | No | CAUTION | AGREE | 0.233 | 0.99 | -1.17 | 0.969 | 1.393 |
| GOOG | NO EDGE | NORMAL | 63d | No | NORMAL | AGREE | 0.297 | 0.91 | -0.66 | 0.824 | 0.760 |
| GS | NO EDGE | NORMAL | 41d | No | NORMAL | AGREE | 0.330 | 0.92 | -0.53 | 0.933 | 0.827 |
| HD | NO EDGE | NORMAL | 76d | No | NORMAL | AGREE | 0.260 | 0.98 | -0.11 | 0.891 | 1.146 |
| HOOD | NO EDGE | CAUTION | 63d | No | NORMAL | STATE_MISMATCH | 0.678 | 0.89 | -0.05 | 0.924 | 0.945 |
| IWM | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.197 | 0.91 | -0.35 | 0.958 | 1.173 |
| JNJ | NO EDGE | NORMAL | 41d | No | NORMAL | AGREE | 0.232 | 0.94 | -0.86 | 0.886 | 0.889 |
| JPM | NO EDGE | NORMAL | 41d | No | NORMAL | AGREE | 0.235 | 0.90 | -0.11 | 0.893 | 0.716 |
| KO | NO EDGE | NORMAL | 48d | No | NORMAL | AGREE | 0.212 | 0.86 | -0.59 | 0.884 | 1.034 |
| MCD | NO EDGE | NORMAL | 64d | No | CAUTION | STATE_MISMATCH | 0.204 | 1.00 | +0.13 | 0.891 | 1.036 |
| META | NO EDGE | NORMAL | 56d | No | NORMAL | AGREE | 0.440 | 0.79 | -0.52 | 0.843 | 0.625 |
| MSFT | NO EDGE | NORMAL | 56d | No | NORMAL | AGREE | 0.313 | 0.79 | -1.19 | 0.810 | 0.792 |
| NFLX | NO EDGE | NORMAL | 48d | No | NORMAL | AGREE | 0.397 | 0.78 | -0.61 | 0.786 | 0.657 |
| NVDA | NO EDGE | CAUTION | 77d | No | CAUTION | AGREE | 0.467 | 0.68 | -2.37 | 0.861 | 1.142 |
| PLTR | NO EDGE | NORMAL | 61d | No | NORMAL | AGREE | 0.607 | 0.78 | -0.38 | 0.853 | 0.879 |
| QQQ | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.217 | 0.86 | -1.28 | 0.922 | 0.816 |
| SBUX | NO EDGE | CAUTION | 56d | No | NORMAL | STATE_MISMATCH | 0.269 | 0.89 | -0.65 | 0.739 | 1.013 |
| SPY | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.149 | 0.87 | -0.37 | 0.908 | 0.837 |
| TLT | NO EDGE | CAUTION | ETF | No | NORMAL | STATE_MISMATCH | 0.130 | 0.89 | +0.22 | 0.988 | 1.004 |
| TSLA | NO EDGE | NORMAL | 56d | No | NORMAL | AGREE | 0.512 | 0.80 | -0.69 | 0.920 | 0.753 |
| UBER | NO EDGE | NORMAL | 62d | No | CAUTION | STATE_MISMATCH | 0.418 | 0.82 | -0.18 | 0.881 | 1.108 |
| WMT | NO EDGE | CAUTION | 78d | No | CAUTION | AGREE | 0.243 | 0.92 | -0.84 | 0.822 | 1.003 |
| XLB | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.188 | 1.10 | -0.34 | 1.142 | 0.954 |
| XLE | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.284 | 0.84 | -0.33 | 0.881 | 0.671 |
| XLF | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.179 | 0.88 | +0.06 | 1.008 | 1.115 |
| XLI | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.197 | 0.91 | -0.51 | 0.876 | 1.132 |
| XLV | NO EDGE | CAUTION | ETF | No | CAUTION | AGREE | 0.183 | 0.78 | -1.83 | 0.869 | 0.981 |
| XOM | NO EDGE | NORMAL | 58d | No | NORMAL | AGREE | 0.303 | 0.97 | +0.54 | 0.980 | 0.891 |

---

## 2026-09-01 (Tuesday)

**Shadow summary:** Checked 330 / 249 agree / 3 V2_STRICTER / 1 V2_LOOSER / 76 state_mismatch / 1 nodata | index-gating v1 95% vs v2 97% | oscillation v1 1.12 vs v2 0.58 | warm 100% | day-flips v1 5/33 vs v2 2/33

| Ticker | v1 Action | v1 Regime | Earnings | v2 Eligible | v2 Gate | Divergence | sigma_fwd | FVRP | z | 1M/3M | accel_dn |
|--------|-----------|-----------|----------|-------------|---------|------------|-----------|------|------|-------|----------|
| AAPL | NO EDGE | NORMAL | 58d | No | NORMAL | AGREE | 0.298 | 0.81 | -0.66 | 0.924 | 0.572 |
| AMZN | NO EDGE | NORMAL | 58d | No | NORMAL | AGREE | 0.358 | 0.81 | -0.88 | 0.824 | 1.013 |
| CAT | NO EDGE | NORMAL | 58d | No | NORMAL | AGREE | 0.350 | 0.99 | -0.37 | 0.868 | 0.758 |
| EEM | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.209 | 1.01 | -0.28 | 0.894 | 0.634 |
| GLD | NO EDGE | CAUTION | ETF | No | CAUTION | AGREE | 0.207 | 1.04 | -0.81 | 0.936 | 1.229 |
| GOOG | NO EDGE | NORMAL | 64d | No | NORMAL | AGREE | 0.300 | 0.89 | -0.83 | 0.818 | 0.770 |
| GS | NO EDGE | NORMAL | 42d | No | NORMAL | AGREE | 0.273 | 1.07 | +0.78 | 0.921 | 0.709 |
| HD | NO EDGE | NORMAL | 77d | No | NORMAL | AGREE | 0.250 | 0.99 | -0.05 | 0.908 | 0.939 |
| HOOD | NO EDGE | CAUTION | 64d | No | NORMAL | STATE_MISMATCH | 0.699 | 0.83 | -0.62 | 0.909 | 0.998 |
| IWM | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.188 | 0.92 | -0.24 | 0.911 | 1.083 |
| JNJ | NO EDGE | CAUTION | 42d | No | NORMAL | STATE_MISMATCH | 0.200 | 1.11 | +0.61 | 0.897 | 0.954 |
| JPM | NO EDGE | NORMAL | 42d | No | NORMAL | AGREE | 0.230 | 0.89 | -0.18 | 0.875 | 0.752 |
| KO | NO EDGE | NORMAL | 49d | No | NORMAL | AGREE | 0.191 | 0.94 | +0.03 | 0.876 | 1.048 |
| MCD | NO EDGE | NORMAL | 65d | No | CAUTION | STATE_MISMATCH | 0.202 | 0.99 | +0.08 | 0.872 | 1.110 |
| META | NO EDGE | NORMAL | 57d | No | NORMAL | AGREE | 0.404 | 0.85 | -0.18 | 0.848 | 0.671 |
| MSFT | NO EDGE | NORMAL | 57d | No | NORMAL | AGREE | 0.288 | 0.86 | -0.74 | 0.819 | 0.713 |
| NFLX | NO EDGE | NORMAL | 49d | No | NORMAL | AGREE | 0.375 | 0.81 | -0.46 | 0.788 | 0.701 |
| NKE | NO EDGE | NORMAL | 28d | No | CAUTION | STATE_MISMATCH | 0.335 | 1.21 | +0.52 | 0.963 | 0.988 |
| NVDA | NO EDGE | CAUTION | 78d | No | CAUTION | AGREE | 0.481 | 0.67 | -2.50 | 0.869 | 1.184 |
| PLTR | NO EDGE | NORMAL | 62d | No | NORMAL | AGREE | 0.566 | 0.82 | -0.07 | 0.847 | 0.562 |
| QQQ | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.190 | 0.93 | -0.38 | 0.893 | 0.622 |
| SBUX | NO EDGE | CAUTION | 57d | No | NORMAL | STATE_MISMATCH | 0.268 | 1.05 | -0.01 | 0.894 | 1.088 |
| SPY | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.138 | 0.92 | +0.11 | 0.886 | 0.661 |
| TLT | NO EDGE | CAUTION | ETF | No | NORMAL | STATE_MISMATCH | 0.122 | 0.90 | +0.27 | 0.949 | 0.832 |
| TSLA | NO EDGE | NORMAL | 57d | No | NORMAL | AGREE | 0.503 | 0.82 | -0.44 | 0.922 | 0.594 |
| UBER | NO EDGE | NORMAL | 63d | No | NORMAL | AGREE | 0.435 | 0.79 | -0.38 | 0.890 | 1.185 |
| WMT | NO EDGE | CAUTION | 79d | No | CAUTION | AGREE | 0.249 | 0.87 | -1.15 | 0.830 | 1.077 |
| XLB | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.196 | 1.01 | -0.69 | 0.939 | 0.788 |
| XLE | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.289 | 0.84 | -0.29 | 0.964 | 0.721 |
| XLF | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.166 | 0.86 | -0.16 | 0.877 | 0.973 |
| XLI | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.185 | 0.99 | +0.02 | 0.893 | 1.028 |
| XLV | NO EDGE | CAUTION | ETF | No | CAUTION | AGREE | 0.168 | 0.94 | -0.49 | 0.955 | 1.054 |
| XOM | NO EDGE | CAUTION | 59d | No | NORMAL | STATE_MISMATCH | 0.307 | 0.92 | +0.05 | 0.976 | 0.957 |

---

## 2026-08-31 (Monday)

**Shadow summary:** Checked 330 / 249 agree / 4 V2_STRICTER / 2 V2_LOOSER / 74 state_mismatch / 1 nodata | index-gating v1 95% vs v2 96% | oscillation v1 1.09 vs v2 0.64 | warm 100% | day-flips v1 4/33 vs v2 2/33

| Ticker | v1 Action | v1 Regime | Earnings | v2 Eligible | v2 Gate | Divergence | sigma_fwd | FVRP | z | 1M/3M | accel_dn |
|--------|-----------|-----------|----------|-------------|---------|------------|-----------|------|------|-------|----------|
| AAPL | NO EDGE | NORMAL | 59d | No | NORMAL | AGREE | 0.292 | 0.83 | -0.47 | 0.919 | 0.546 |
| AMZN | NO EDGE | NORMAL | 59d | No | NORMAL | AGREE | 0.346 | 0.84 | -0.67 | 0.819 | 0.765 |
| CAT | NO EDGE | NORMAL | 59d | No | NORMAL | AGREE | 0.367 | 0.96 | -0.59 | 0.868 | 0.811 |
| EEM | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.219 | 0.96 | -0.49 | 0.894 | 0.678 |
| GLD | NO EDGE | CAUTION | ETF | No | NORMAL | STATE_MISMATCH | 0.223 | 1.02 | -0.98 | 0.927 | 1.319 |
| GOOG | NO EDGE | NORMAL | 65d | No | NORMAL | AGREE | 0.291 | 0.93 | -0.55 | 0.824 | 0.566 |
| GS | NO EDGE | NORMAL | 43d | No | NORMAL | AGREE | 0.292 | 0.98 | -0.02 | 0.906 | 0.725 |
| HD | NO EDGE | NORMAL | 78d | No | NORMAL | AGREE | 0.259 | 0.92 | -0.61 | 0.888 | 0.979 |
| HOOD | NO EDGE | CAUTION | 65d | No | NORMAL | STATE_MISMATCH | 0.713 | 0.82 | -0.84 | 0.911 | 1.072 |
| IWM | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.191 | 0.85 | -0.99 | 0.870 | 1.108 |
| JNJ | NO EDGE | CAUTION | 43d | No | NORMAL | STATE_MISMATCH | 0.209 | 1.04 | +0.02 | 0.875 | 0.967 |
| JPM | NO EDGE | NORMAL | 43d | No | NORMAL | AGREE | 0.238 | 0.85 | -0.56 | 0.864 | 0.775 |
| KO | NO EDGE | NORMAL | 50d | No | NORMAL | AGREE | 0.202 | 0.87 | -0.50 | 0.846 | 0.982 |
| MCD | NO EDGE | CAUTION | 66d | No | CAUTION | AGREE | 0.213 | 0.95 | -0.21 | 0.904 | 1.176 |
| META | NO EDGE | NORMAL | 58d | No | NORMAL | AGREE | 0.436 | 0.79 | -0.55 | 0.846 | 0.689 |
| MSFT | NO EDGE | NORMAL | 58d | No | NORMAL | AGREE | 0.301 | 0.82 | -0.95 | 0.819 | 0.609 |
| NFLX | NO EDGE | CAUTION | 50d | No | NORMAL | STATE_MISMATCH | 0.389 | 0.77 | -0.69 | 0.784 | 0.714 |
| NKE | NO EDGE | CAUTION | 29d | No | CAUTION | AGREE | 0.343 | 1.18 | +0.41 | 0.980 | 1.009 |
| NVDA | NO EDGE | CAUTION | 79d | No | CAUTION | AGREE | 0.518 | 0.63 | -3.15 | 0.871 | 1.271 |
| PLTR | NO EDGE | NORMAL | 63d | No | NORMAL | AGREE | 0.587 | 0.76 | -0.56 | 0.818 | 0.603 |
| QQQ | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.203 | 0.83 | -1.56 | 0.851 | 0.668 |
| SBUX | NO EDGE | CAUTION | 58d | No | NORMAL | STATE_MISMATCH | 0.276 | 0.88 | -0.69 | 0.778 | 0.965 |
| SPY | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.143 | 0.83 | -0.80 | 0.835 | 0.656 |
| TLT | NO EDGE | CAUTION | ETF | No | NORMAL | STATE_MISMATCH | 0.122 | 0.83 | -0.47 | 0.898 | 0.802 |
| TSLA | NO EDGE | NORMAL | 58d | No | NORMAL | AGREE | 0.501 | 0.76 | -1.02 | 0.885 | 0.638 |
| UBER | NO EDGE | NORMAL | 64d | No | NORMAL | AGREE | 0.424 | 0.79 | -0.43 | 0.854 | 0.851 |
| WMT | NO EDGE | CAUTION | 80d | No | CAUTION | AGREE | 0.247 | 0.88 | -1.07 | 0.849 | 1.157 |
| XLB | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.205 | 0.83 | -1.57 | 0.859 | 0.652 |
| XLE | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.263 | 0.99 | +1.19 | 1.047 | 0.774 |
| XLF | NO EDGE | CAUTION | ETF | No | NORMAL | STATE_MISMATCH | 0.172 | 0.82 | -0.51 | 0.885 | 0.879 |
| XLI | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.187 | 0.91 | -0.52 | 0.816 | 0.946 |
| XLV | NO EDGE | CAUTION | ETF | No | CAUTION | AGREE | 0.166 | 0.92 | -0.64 | 0.851 | 1.112 |
| XOM | NO EDGE | NORMAL | 60d | No | CAUTION | STATE_MISMATCH | 0.281 | 0.95 | +0.39 | 0.952 | 1.028 |

---

## 2026-08-28 (Friday)

**Shadow summary:** Checked 330 / 252 agree / 5 V2_STRICTER / 2 V2_LOOSER / 70 state_mismatch / 1 nodata | index-gating v1 94% vs v2 96% | oscillation v1 0.97 vs v2 0.58 | warm 100% | day-flips v1 2/33 vs v2 0/33

| Ticker | v1 Action | v1 Regime | Earnings | v2 Eligible | v2 Gate | Divergence | sigma_fwd | FVRP | z | 1M/3M | accel_dn |
|--------|-----------|-----------|----------|-------------|---------|------------|-----------|------|------|-------|----------|
| GLD | NO EDGE | NORMAL | ETF | Yes | NORMAL | V2_LOOSER | 0.196 | 1.24 | +0.51 | 0.952 | 0.789 |
| AAPL | NO EDGE | NORMAL | 62d | No | NORMAL | AGREE | 0.289 | 0.84 | -0.38 | 0.926 | 0.587 |
| AMZN | NO EDGE | NORMAL | 62d | No | NORMAL | AGREE | 0.319 | 0.88 | -0.47 | 0.811 | 0.821 |
| CAT | NO EDGE | NORMAL | 62d | No | NORMAL | AGREE | 0.385 | 0.94 | -0.77 | 0.882 | 0.761 |
| EEM | WATCHLIST | NORMAL | ETF | No | NORMAL | AGREE | 0.218 | 0.99 | -0.35 | 0.910 | 0.688 |
| GOOG | NO EDGE | NORMAL | 68d | No | NORMAL | AGREE | 0.285 | 0.95 | -0.42 | 0.829 | 0.608 |
| GS | NO EDGE | NORMAL | 46d | No | NORMAL | AGREE | 0.303 | 0.98 | -0.01 | 0.918 | 0.754 |
| HD | NO EDGE | NORMAL | 81d | No | NORMAL | AGREE | 0.269 | 0.89 | -0.76 | 0.894 | 1.052 |
| HOOD | NO EDGE | CAUTION | 68d | No | NORMAL | STATE_MISMATCH | 0.714 | 0.85 | -0.47 | 0.921 | 0.874 |
| IWM | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.180 | 0.95 | +0.05 | 0.886 | 0.845 |
| JNJ | NO EDGE | CAUTION | 46d | No | NORMAL | STATE_MISMATCH | 0.214 | 1.02 | -0.09 | 0.886 | 1.039 |
| JPM | NO EDGE | NORMAL | 46d | No | NORMAL | AGREE | 0.244 | 0.83 | -0.79 | 0.864 | 0.832 |
| KO | NO EDGE | NORMAL | 53d | No | NORMAL | AGREE | 0.212 | 0.84 | -0.79 | 0.879 | 1.055 |
| MCD | NO EDGE | NORMAL | 69d | No | NORMAL | AGREE | 0.211 | 0.98 | -0.02 | 0.925 | 1.263 |
| META | NO EDGE | NORMAL | 61d | No | NORMAL | AGREE | 0.458 | 0.76 | -0.72 | 0.850 | 0.741 |
| MSFT | NO EDGE | NORMAL | 61d | No | NORMAL | AGREE | 0.308 | 0.80 | -1.07 | 0.811 | 0.654 |
| NFLX | NO EDGE | NORMAL | 53d | No | NORMAL | AGREE | 0.375 | 0.80 | -0.50 | 0.786 | 0.767 |
| NKE | NO EDGE | CAUTION | 32d | No | CAUTION | AGREE | 0.345 | 1.09 | +0.07 | 0.887 | 1.084 |
| NVDA | NO EDGE | CAUTION | 82d | No | CAUTION | AGREE | 0.534 | 0.64 | -3.04 | 0.890 | 0.868 |
| PLTR | NO EDGE | NORMAL | 66d | No | NORMAL | AGREE | 0.625 | 0.75 | -0.66 | 0.833 | 0.648 |
| QQQ | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.204 | 0.89 | -0.89 | 0.882 | 0.645 |
| SBUX | NO EDGE | CAUTION | 61d | No | NORMAL | STATE_MISMATCH | 0.285 | 0.84 | -0.93 | 0.768 | 1.037 |
| SPY | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.139 | 0.86 | -0.47 | 0.840 | 0.675 |
| TLT | NO EDGE | CAUTION | ETF | No | NORMAL | STATE_MISMATCH | 0.114 | 0.94 | +0.69 | 0.926 | 0.817 |
| TSLA | NO EDGE | NORMAL | 61d | No | NORMAL | AGREE | 0.487 | 0.81 | -0.56 | 0.891 | 0.623 |
| UBER | NO EDGE | NORMAL | 67d | No | NORMAL | AGREE | 0.443 | 0.76 | -0.64 | 0.872 | 0.914 |
| WMT | NO EDGE | CAUTION | 83d | No | CAUTION | AGREE | 0.254 | 0.88 | -1.10 | 0.854 | 1.243 |
| XLB | NO DATA | NORMAL | ETF | No | NORMAL | NODATA_SKEW | — | — | — | — | — |
| XLE | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.284 | 0.86 | -0.04 | 0.971 | 0.831 |
| XLF | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.178 | 0.76 | -1.09 | 0.866 | 0.945 |
| XLI | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.185 | 0.92 | -0.43 | 0.906 | 0.895 |
| XLV | NO EDGE | CAUTION | ETF | No | NORMAL | STATE_MISMATCH | 0.178 | 0.81 | -1.55 | 0.738 | 1.186 |
| XOM | NO EDGE | NORMAL | 63d | No | CAUTION | STATE_MISMATCH | 0.296 | 0.91 | -0.03 | 0.936 | 1.104 |

---

## 2026-08-27 (Thursday)

**Shadow summary:** Checked 330 / 252 agree / 5 V2_STRICTER / 1 V2_LOOSER / 72 state_mismatch / 0 nodata | index-gating v1 94% vs v2 97% | oscillation v1 1.06 vs v2 0.70 | warm 100% | day-flips v1 4/33 vs v2 3/33

| Ticker | v1 Action | v1 Regime | Earnings | v2 Eligible | v2 Gate | Divergence | sigma_fwd | FVRP | z | 1M/3M | accel_dn |
|--------|-----------|-----------|----------|-------------|---------|------------|-----------|------|------|-------|----------|
| AAPL | NO EDGE | NORMAL | 63d | No | NORMAL | AGREE | 0.289 | 0.85 | -0.24 | 0.933 | 0.630 |
| AMZN | NO EDGE | NORMAL | 63d | No | NORMAL | AGREE | 0.317 | 0.91 | -0.27 | 0.825 | 0.731 |
| CAT | NO EDGE | NORMAL | 63d | No | NORMAL | AGREE | 0.388 | 0.96 | -0.58 | 0.908 | 0.809 |
| EEM | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.225 | 1.00 | -0.29 | 0.951 | 0.739 |
| GLD | NO EDGE | CAUTION | ETF | No | NORMAL | STATE_MISMATCH | 0.208 | 1.19 | +0.22 | 0.959 | 0.847 |
| GOOG | NO EDGE | NORMAL | 69d | No | NORMAL | AGREE | 0.290 | 0.96 | -0.34 | 0.839 | 0.644 |
| GS | NO EDGE | NORMAL | 47d | No | NORMAL | AGREE | 0.316 | 0.97 | -0.07 | 0.929 | 0.810 |
| HD | NO EDGE | NORMAL | 82d | No | NORMAL | AGREE | 0.261 | 0.97 | -0.16 | 0.919 | 0.944 |
| HOOD | NO EDGE | CAUTION | 69d | No | NORMAL | STATE_MISMATCH | 0.731 | 0.86 | -0.35 | 0.951 | 0.939 |
| IWM | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.187 | 0.90 | -0.46 | 0.889 | 0.908 |
| JNJ | NO EDGE | CAUTION | 47d | No | NORMAL | STATE_MISMATCH | 0.208 | 1.10 | +0.55 | 0.920 | 0.911 |
| JPM | NO EDGE | NORMAL | 47d | No | NORMAL | AGREE | 0.236 | 0.90 | -0.12 | 0.885 | 0.836 |
| KO | NO EDGE | NORMAL | 54d | No | NORMAL | AGREE | 0.212 | 0.83 | -0.83 | 0.880 | 0.983 |
| MCD | NO EDGE | NORMAL | 70d | No | NORMAL | AGREE | 0.199 | 1.00 | +0.15 | 0.883 | 0.959 |
| META | NO EDGE | NORMAL | 62d | No | NORMAL | AGREE | 0.481 | 0.75 | -0.80 | 0.862 | 0.775 |
| MSFT | NO EDGE | NORMAL | 62d | No | NORMAL | AGREE | 0.286 | 0.86 | -0.73 | 0.815 | 0.703 |
| NFLX | NO EDGE | NORMAL | 54d | No | NORMAL | AGREE | 0.371 | 0.86 | -0.19 | 0.823 | 0.596 |
| NKE | NO EDGE | CAUTION | 33d | No | CAUTION | AGREE | 0.367 | 0.95 | -0.54 | 0.821 | 1.161 |
| NVDA | AVOID | DANGER | 83d | No | CAUTION | STATE_MISMATCH | 0.406 | 1.03 | +1.23 | 1.050 | 0.933 |
| PLTR | NO EDGE | NORMAL | 67d | No | NORMAL | AGREE | 0.647 | 0.74 | -0.78 | 0.859 | 0.696 |
| QQQ | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.199 | 0.90 | -0.78 | 0.870 | 0.693 |
| SBUX | NO EDGE | CAUTION | 62d | No | NORMAL | STATE_MISMATCH | 0.298 | 0.90 | -0.64 | 0.831 | 0.991 |
| SPY | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.136 | 0.90 | -0.07 | 0.857 | 0.725 |
| TLT | NO EDGE | CAUTION | ETF | No | NORMAL | STATE_MISMATCH | 0.122 | 0.90 | +0.30 | 0.937 | 0.859 |
| TSLA | NO EDGE | NORMAL | 62d | No | NORMAL | AGREE | 0.515 | 0.78 | -0.80 | 0.903 | 0.669 |
| UBER | NO EDGE | NORMAL | 68d | No | NORMAL | AGREE | 0.462 | 0.75 | -0.71 | 0.894 | 0.848 |
| WMT | NO EDGE | CAUTION | 84d | No | CAUTION | AGREE | 0.271 | 0.82 | -1.50 | 0.838 | 1.335 |
| XLB | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.196 | 1.00 | -0.75 | 1.056 | 0.575 |
| XLE | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.295 | 0.84 | -0.26 | 0.989 | 0.887 |
| XLF | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.169 | 0.90 | +0.26 | 0.864 | 0.851 |
| XLI | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.190 | 1.05 | +0.39 | 1.045 | 0.849 |
| XLV | NO EDGE | CAUTION | ETF | No | NORMAL | STATE_MISMATCH | 0.170 | 1.00 | -0.12 | 0.721 | 1.096 |
| XOM | NO EDGE | NORMAL | 64d | No | CAUTION | STATE_MISMATCH | 0.318 | 0.84 | -0.74 | 0.917 | 1.106 |

---

## 2026-08-26 (Wednesday)

**Shadow summary:** Checked 330 / 250 agree / 5 V2_STRICTER / 1 V2_LOOSER / 74 state_mismatch / 0 nodata | index-gating v1 94% vs v2 97% | oscillation v1 1.03 vs v2 0.70 | warm 100% | day-flips v1 2/33 vs v2 3/33

| Ticker | v1 Action | v1 Regime | Earnings | v2 Eligible | v2 Gate | Divergence | sigma_fwd | FVRP | z | 1M/3M | accel_dn |
|--------|-----------|-----------|----------|-------------|---------|------------|-----------|------|------|-------|----------|
| AAPL | NO EDGE | NORMAL | 64d | No | NORMAL | AGREE | 0.287 | 0.83 | -0.45 | 0.915 | 0.677 |
| AMZN | NO EDGE | NORMAL | 64d | No | NORMAL | AGREE | 0.324 | 0.90 | -0.33 | 0.827 | 0.779 |
| CAT | NO EDGE | NORMAL | 64d | No | NORMAL | AGREE | 0.419 | 0.94 | -0.77 | 0.918 | 0.869 |
| EEM | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.244 | 0.95 | -0.56 | 0.910 | 0.793 |
| GLD | NO EDGE | NORMAL | ETF | No | CAUTION | STATE_MISMATCH | 0.205 | 1.24 | +0.53 | 0.973 | 0.606 |
| GOOG | NO EDGE | NORMAL | 70d | No | NORMAL | AGREE | 0.295 | 0.95 | -0.44 | 0.838 | 0.607 |
| GS | NO EDGE | NORMAL | 48d | No | NORMAL | AGREE | 0.329 | 0.94 | -0.36 | 0.929 | 0.711 |
| HD | NO EDGE | NORMAL | 83d | No | NORMAL | AGREE | 0.279 | 0.91 | -0.64 | 0.930 | 0.967 |
| HOOD | NO EDGE | CAUTION | 70d | No | NORMAL | STATE_MISMATCH | 0.774 | 0.83 | -0.68 | 0.957 | 0.886 |
| IWM | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.197 | 0.88 | -0.66 | 0.910 | 0.973 |
| JNJ | NO EDGE | NORMAL | 48d | No | NORMAL | AGREE | 0.214 | 1.04 | +0.04 | 0.873 | 0.844 |
| JPM | NO EDGE | NORMAL | 48d | No | NORMAL | AGREE | 0.247 | 0.86 | -0.53 | 0.886 | 0.898 |
| KO | NO EDGE | NORMAL | 55d | No | NORMAL | AGREE | 0.205 | 0.89 | -0.38 | 0.869 | 0.473 |
| MCD | NO EDGE | NORMAL | 71d | No | NORMAL | AGREE | 0.205 | 0.99 | +0.12 | 0.894 | 1.015 |
| META | NO EDGE | NORMAL | 63d | No | NORMAL | AGREE | 0.390 | 0.90 | +0.09 | 0.846 | 0.833 |
| MSFT | NO EDGE | NORMAL | 63d | No | NORMAL | AGREE | 0.282 | 0.89 | -0.54 | 0.820 | 0.755 |
| NFLX | NO EDGE | NORMAL | 55d | No | NORMAL | AGREE | 0.394 | 0.82 | -0.40 | 0.823 | 0.579 |
| NKE | NO EDGE | CAUTION | 34d | No | NORMAL | STATE_MISMATCH | 0.389 | 0.86 | -0.95 | 0.801 | 1.136 |
| NVDA | AVOID | DANGER | 0d | No | CAUTION | STATE_MISMATCH | 0.426 | 0.96 | +0.62 | 1.023 | 0.919 |
| PLTR | NO EDGE | NORMAL | 68d | No | NORMAL | AGREE | 0.645 | 0.72 | -0.96 | 0.838 | 0.748 |
| QQQ | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.212 | 0.90 | -0.73 | 0.904 | 0.744 |
| SBUX | NO EDGE | NORMAL | 63d | No | NORMAL | AGREE | 0.299 | 0.88 | -0.72 | 0.863 | 1.065 |
| SPY | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.143 | 0.89 | -0.14 | 0.866 | 0.779 |
| TLT | NO EDGE | CAUTION | ETF | No | NORMAL | STATE_MISMATCH | 0.131 | 0.85 | -0.29 | 0.952 | 0.905 |
| TSLA | NO EDGE | NORMAL | 63d | No | NORMAL | AGREE | 0.511 | 0.79 | -0.72 | 0.898 | 0.690 |
| UBER | NO EDGE | NORMAL | 69d | No | NORMAL | AGREE | 0.427 | 0.81 | -0.23 | 0.884 | 0.679 |
| WMT | NO EDGE | CAUTION | 85d | No | CAUTION | AGREE | 0.287 | 0.76 | -1.91 | 0.834 | 1.406 |
| XLB | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.207 | 0.82 | -1.63 | 0.813 | 0.617 |
| XLE | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.288 | 0.81 | -0.59 | 0.882 | 0.952 |
| XLF | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.178 | 0.80 | -0.69 | 0.853 | 0.911 |
| XLI | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.200 | 0.81 | -1.24 | 0.971 | 0.912 |
| XLV | NO EDGE | CAUTION | ETF | No | NORMAL | STATE_MISMATCH | 0.173 | 0.97 | -0.30 | 0.747 | 1.006 |
| XOM | NO EDGE | CAUTION | 65d | No | NORMAL | STATE_MISMATCH | 0.307 | 0.98 | +0.66 | 1.011 | 1.022 |

---

## 2026-08-25 (Tuesday)

**Shadow summary:** Checked 330 / 245 agree / 5 V2_STRICTER / 1 V2_LOOSER / 79 state_mismatch / 0 nodata | index-gating v1 94% vs v2 97% | oscillation v1 1.24 vs v2 0.64 | warm 100% | day-flips v1 3/33 vs v2 1/33

| Ticker | v1 Action | v1 Regime | Earnings | v2 Eligible | v2 Gate | Divergence | sigma_fwd | FVRP | z | 1M/3M | accel_dn |
|--------|-----------|-----------|----------|-------------|---------|------------|-----------|------|------|-------|----------|
| AAPL | NO EDGE | NORMAL | 65d | No | NORMAL | AGREE | 0.291 | 0.85 | -0.30 | 0.917 | 0.726 |
| AMZN | NO EDGE | NORMAL | 65d | No | NORMAL | AGREE | 0.332 | 0.89 | -0.37 | 0.831 | 0.828 |
| CAT | NO EDGE | NORMAL | 65d | No | NORMAL | AGREE | 0.394 | 0.93 | -0.82 | 0.880 | 0.933 |
| EEM | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.248 | 0.97 | -0.45 | 0.977 | 0.852 |
| GLD | NO EDGE | CAUTION | ETF | No | CAUTION | AGREE | 0.215 | 1.24 | +0.53 | 1.004 | 0.651 |
| GOOG | NO EDGE | NORMAL | 71d | No | NORMAL | AGREE | 0.312 | 0.92 | -0.60 | 0.853 | 0.645 |
| GS | NO EDGE | NORMAL | 49d | No | NORMAL | AGREE | 0.324 | 0.95 | -0.27 | 0.936 | 0.764 |
| HD | NO EDGE | NORMAL | 84d | No | CAUTION | STATE_MISMATCH | 0.291 | 0.90 | -0.70 | 0.951 | 1.038 |
| HOOD | NO EDGE | CAUTION | 71d | No | NORMAL | STATE_MISMATCH | 0.817 | 0.78 | -1.29 | 0.959 | 0.951 |
| IWM | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.201 | 0.87 | -0.77 | 0.915 | 1.045 |
| JNJ | NO EDGE | NORMAL | 49d | No | NORMAL | AGREE | 0.226 | 0.97 | -0.47 | 0.894 | 0.906 |
| JPM | NO EDGE | NORMAL | 49d | No | NORMAL | AGREE | 0.257 | 0.79 | -1.19 | 0.849 | 0.965 |
| KO | NO EDGE | NORMAL | 56d | No | NORMAL | AGREE | 0.217 | 0.82 | -0.96 | 0.879 | 0.454 |
| MCD | NO EDGE | NORMAL | 72d | No | NORMAL | AGREE | 0.212 | 0.97 | -0.06 | 0.887 | 0.854 |
| META | NO EDGE | NORMAL | 64d | No | NORMAL | AGREE | 0.406 | 0.88 | -0.04 | 0.849 | 0.894 |
| MSFT | NO EDGE | NORMAL | 64d | No | NORMAL | AGREE | 0.291 | 0.89 | -0.57 | 0.832 | 0.811 |
| NFLX | NO EDGE | NORMAL | 56d | No | NORMAL | AGREE | 0.390 | 0.83 | -0.33 | 0.833 | 0.622 |
| NKE | NO EDGE | CAUTION | 35d | No | NORMAL | STATE_MISMATCH | 0.339 | 1.03 | -0.16 | 0.831 | 0.953 |
| NVDA | AVOID | DANGER | 1d | No | NORMAL | STATE_MISMATCH | 0.425 | 0.97 | +0.68 | 1.030 | 0.987 |
| PLTR | NO EDGE | NORMAL | 69d | No | NORMAL | AGREE | 0.657 | 0.72 | -0.98 | 0.846 | 0.713 |
| QQQ | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.212 | 0.92 | -0.59 | 0.912 | 0.799 |
| SBUX | NO EDGE | NORMAL | 64d | No | NORMAL | AGREE | 0.311 | 0.84 | -0.93 | 0.828 | 0.874 |
| SPY | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.143 | 0.89 | -0.16 | 0.867 | 0.837 |
| TLT | NO EDGE | CAUTION | ETF | No | NORMAL | STATE_MISMATCH | 0.132 | 0.83 | -0.50 | 0.950 | 0.972 |
| TSLA | NO EDGE | NORMAL | 64d | No | NORMAL | AGREE | 0.543 | 0.75 | -1.19 | 0.903 | 0.741 |
| UBER | NO EDGE | NORMAL | 70d | No | NORMAL | AGREE | 0.450 | 0.77 | -0.55 | 0.884 | 0.729 |
| WMT | NO EDGE | CAUTION | 86d | No | CAUTION | AGREE | 0.306 | 0.74 | -2.07 | 0.876 | 1.501 |
| XLB | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.219 | 0.94 | -1.01 | 1.043 | 0.663 |
| XLE | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.276 | 0.89 | +0.22 | 0.953 | 0.631 |
| XLF | NO EDGE | NORMAL | ETF | No | CAUTION | STATE_MISMATCH | 0.186 | 0.79 | -0.79 | 0.892 | 0.979 |
| XLI | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.190 | 0.95 | -0.25 | 0.889 | 0.965 |
| XLV | NO EDGE | CAUTION | ETF | No | NORMAL | STATE_MISMATCH | 0.183 | 0.84 | -1.28 | 0.852 | 1.081 |
| XOM | NO EDGE | NORMAL | 66d | No | NORMAL | AGREE | 0.292 | 0.96 | +0.45 | 0.955 | 0.590 |

---

## 2026-08-24 (Monday)

**Shadow summary:** Checked 330 / 236 agree / 5 V2_STRICTER / 1 V2_LOOSER / 88 state_mismatch / 0 nodata | index-gating v1 94% vs v2 97% | oscillation v1 1.24 vs v2 0.67 | warm 100% | day-flips v1 7/33 vs v2 4/33

| Ticker | v1 Action | v1 Regime | Earnings | v2 Eligible | v2 Gate | Divergence | sigma_fwd | FVRP | z | 1M/3M | accel_dn |
|--------|-----------|-----------|----------|-------------|---------|------------|-----------|------|------|-------|----------|
| XLF | CONDITIONAL | NORMAL | ETF | No | CAUTION | V2_STRICTER | 0.188 | 0.86 | -0.11 | 1.023 | 1.052 |
| AAPL | NO EDGE | NORMAL | 66d | No | NORMAL | AGREE | 0.304 | 0.80 | -0.76 | 0.900 | 0.780 |
| AMZN | NO EDGE | NORMAL | 66d | No | NORMAL | AGREE | 0.342 | 0.84 | -0.67 | 0.819 | 0.890 |
| CAT | WATCHLIST | NORMAL | 66d | No | NORMAL | AGREE | 0.409 | 0.92 | -0.85 | 0.887 | 0.925 |
| EEM | WATCHLIST | NORMAL | ETF | No | NORMAL | AGREE | 0.250 | 1.00 | -0.32 | 0.951 | 0.779 |
| GLD | NO EDGE | NORMAL | ETF | No | CAUTION | STATE_MISMATCH | 0.219 | 1.18 | +0.13 | 0.996 | 0.699 |
| GOOG | NO EDGE | NORMAL | 72d | No | NORMAL | AGREE | 0.302 | 0.92 | -0.60 | 0.831 | 0.692 |
| GS | NO EDGE | NORMAL | 50d | No | NORMAL | AGREE | 0.343 | 0.91 | -0.65 | 0.924 | 0.817 |
| HD | NO EDGE | NORMAL | 85d | No | CAUTION | STATE_MISMATCH | 0.304 | 0.83 | -1.26 | 0.919 | 1.115 |
| HOOD | NO EDGE | CAUTION | 72d | No | NORMAL | STATE_MISMATCH | 0.862 | 0.74 | -1.78 | 0.947 | 0.793 |
| IWM | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.214 | 0.82 | -1.37 | 0.915 | 1.051 |
| JNJ | NO EDGE | NORMAL | 50d | No | NORMAL | AGREE | 0.232 | 0.92 | -0.87 | 0.853 | 0.974 |
| JPM | NO EDGE | NORMAL | 50d | No | NORMAL | AGREE | 0.263 | 0.75 | -1.62 | 0.843 | 1.036 |
| KO | NO EDGE | NORMAL | 57d | No | NORMAL | AGREE | 0.215 | 0.83 | -0.92 | 0.880 | 0.488 |
| MCD | WATCHLIST | NORMAL | 73d | No | NORMAL | AGREE | 0.220 | 0.97 | -0.03 | 0.931 | 0.917 |
| META | NO EDGE | NORMAL | 65d | No | NORMAL | AGREE | 0.408 | 0.85 | -0.17 | 0.838 | 0.961 |
| MSFT | NO EDGE | NORMAL | 65d | No | NORMAL | AGREE | 0.291 | 0.89 | -0.57 | 0.821 | 0.871 |
| NFLX | NO EDGE | CAUTION | 57d | No | NORMAL | STATE_MISMATCH | 0.397 | 0.79 | -0.57 | 0.819 | 0.668 |
| NKE | NO EDGE | CAUTION | 36d | No | CAUTION | AGREE | 0.354 | 0.94 | -0.57 | 0.787 | 1.024 |
| NVDA | AVOID | DANGER | 2d | No | NORMAL | STATE_MISMATCH | 0.403 | 0.99 | +0.88 | 0.991 | 0.755 |
| PLTR | NO EDGE | NORMAL | 70d | No | NORMAL | AGREE | 0.641 | 0.73 | -0.83 | 0.836 | 0.605 |
| QQQ | WATCHLIST | NORMAL | ETF | No | NORMAL | AGREE | 0.214 | 0.93 | -0.39 | 0.900 | 0.733 |
| SBUX | NO EDGE | CAUTION | 65d | No | NORMAL | STATE_MISMATCH | 0.327 | 0.78 | -1.22 | 0.821 | 0.939 |
| SPY | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.153 | 0.85 | -0.58 | 0.877 | 0.867 |
| TLT | NO EDGE | CAUTION | ETF | No | NORMAL | STATE_MISMATCH | 0.135 | 0.80 | -0.86 | 0.936 | 1.045 |
| TSLA | NO EDGE | NORMAL | 65d | No | NORMAL | AGREE | 0.556 | 0.74 | -1.31 | 0.897 | 0.503 |
| UBER | NO EDGE | NORMAL | 71d | No | NORMAL | AGREE | 0.479 | 0.72 | -1.01 | 0.882 | 0.783 |
| WMT | NO EDGE | CAUTION | 87d | No | CAUTION | AGREE | 0.329 | 0.68 | -2.66 | 0.855 | 1.605 |
| XLB | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.223 | 0.79 | -1.80 | 0.908 | 0.712 |
| XLE | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.268 | 0.89 | +0.25 | 0.925 | 0.523 |
| XLI | SELL PREMIUM | NORMAL | ETF | Yes | NORMAL | AGREE | 0.197 | 1.32 | +1.83 | 1.320 | 0.977 |
| XLV | NO EDGE | CAUTION | ETF | No | NORMAL | STATE_MISMATCH | 0.197 | 1.02 | +0.06 | 1.006 | 1.161 |
| XOM | NO EDGE | NORMAL | 67d | No | NORMAL | AGREE | 0.294 | 1.01 | +0.91 | 0.999 | 0.553 |

---

## 2026-08-21 (Friday)

**Shadow summary:** Checked 330 / 227 agree / 4 V2_STRICTER / 1 V2_LOOSER / 98 state_mismatch / 0 nodata | index-gating v1 95% vs v2 98% | oscillation v1 1.12 vs v2 0.67 | warm 100% | day-flips v1 4/33 vs v2 1/33

| Ticker | v1 Action | v1 Regime | Earnings | v2 Eligible | v2 Gate | Divergence | sigma_fwd | FVRP | z | 1M/3M | accel_dn |
|--------|-----------|-----------|----------|-------------|---------|------------|-----------|------|------|-------|----------|
| AAPL | NO EDGE | NORMAL | 69d | No | NORMAL | AGREE | 0.314 | 0.81 | -0.70 | 0.921 | 0.820 |
| AMZN | NO EDGE | NORMAL | 69d | No | NORMAL | AGREE | 0.353 | 0.84 | -0.68 | 0.830 | 0.941 |
| CAT | NO EDGE | NORMAL | 69d | No | NORMAL | AGREE | 0.403 | 0.90 | -1.04 | 0.863 | 0.994 |
| EEM | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.251 | 1.00 | -0.30 | 0.924 | 0.837 |
| GLD | NO EDGE | NORMAL | ETF | No | CAUTION | STATE_MISMATCH | 0.220 | 1.18 | +0.14 | 1.024 | 0.751 |
| GOOG | NO EDGE | NORMAL | 75d | No | NORMAL | AGREE | 0.296 | 0.95 | -0.41 | 0.841 | 0.744 |
| GS | NO EDGE | NORMAL | 53d | No | NORMAL | AGREE | 0.319 | 0.93 | -0.49 | 0.894 | 0.877 |
| HD | NO EDGE | NORMAL | 88d | No | NORMAL | AGREE | 0.320 | 0.79 | -1.62 | 0.938 | 1.198 |
| HOOD | NO EDGE | NORMAL | 75d | No | NORMAL | AGREE | 0.803 | 0.80 | -1.07 | 0.981 | 0.852 |
| IWM | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.214 | 0.82 | -1.44 | 0.901 | 1.129 |
| JNJ | NO EDGE | NORMAL | 53d | No | NORMAL | AGREE | 0.230 | 0.92 | -0.89 | 0.837 | 1.046 |
| JPM | NO EDGE | NORMAL | 53d | No | NORMAL | AGREE | 0.243 | 0.86 | -0.52 | 0.887 | 1.113 |
| KO | NO EDGE | NORMAL | 60d | No | NORMAL | AGREE | 0.226 | 0.81 | -1.04 | 0.873 | 0.524 |
| MCD | WATCHLIST | NORMAL | 76d | No | CAUTION | STATE_MISMATCH | 0.230 | 0.90 | -0.63 | 0.892 | 0.985 |
| META | WATCHLIST | NORMAL | 68d | No | CAUTION | STATE_MISMATCH | 0.419 | 0.86 | -0.15 | 0.839 | 1.032 |
| MSFT | NO EDGE | NORMAL | 68d | No | NORMAL | AGREE | 0.288 | 0.92 | -0.39 | 0.831 | 0.935 |
| NFLX | NO EDGE | NORMAL | 60d | No | NORMAL | AGREE | 0.416 | 0.78 | -0.59 | 0.824 | 0.693 |
| NKE | NO EDGE | NORMAL | 39d | No | CAUTION | STATE_MISMATCH | 0.367 | 0.91 | -0.71 | 0.790 | 1.100 |
| NVDA | AVOID | DANGER | 5d | No | NORMAL | STATE_MISMATCH | 0.413 | 0.97 | +0.68 | 0.988 | 0.768 |
| PLTR | NO EDGE | NORMAL | 73d | No | NORMAL | AGREE | 0.592 | 0.78 | -0.40 | 0.838 | 0.650 |
| QQQ | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.215 | 0.93 | -0.41 | 0.911 | 0.787 |
| SBUX | NO EDGE | NORMAL | 68d | No | NORMAL | AGREE | 0.318 | 0.83 | -0.97 | 0.843 | 1.008 |
| SPY | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.152 | 0.85 | -0.55 | 0.870 | 0.932 |
| TLT | NO EDGE | CAUTION | ETF | No | NORMAL | STATE_MISMATCH | 0.144 | 0.78 | -1.02 | 0.928 | 1.088 |
| TSLA | NO EDGE | NORMAL | 68d | No | NORMAL | AGREE | 0.524 | 0.79 | -0.77 | 0.899 | 0.540 |
| UBER | NO EDGE | CAUTION | 74d | No | NORMAL | STATE_MISMATCH | 0.481 | 0.70 | -1.13 | 0.864 | 0.841 |
| WMT | NO EDGE | CAUTION | 90d | No | CAUTION | AGREE | 0.358 | 0.62 | -3.21 | 0.861 | 1.724 |
| XLB | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.220 | 0.88 | -1.35 | 1.016 | 0.765 |
| XLE | NO EDGE | CAUTION | ETF | No | NORMAL | STATE_MISMATCH | 0.272 | 0.94 | +0.74 | 0.977 | 0.555 |
| XLF | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.184 | 0.78 | -0.96 | 0.900 | 1.130 |
| XLI | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.198 | 0.88 | -0.74 | 0.905 | 1.050 |
| XLV | NO EDGE | CAUTION | ETF | No | NORMAL | STATE_MISMATCH | 0.199 | 0.99 | -0.15 | 1.120 | 1.247 |
| XOM | NO EDGE | CAUTION | 70d | No | NORMAL | STATE_MISMATCH | 0.296 | 0.99 | +0.75 | 0.946 | 0.513 |

---

## 2026-08-20 (Thursday)

**Shadow summary:** Checked 330 / 219 agree / 6 V2_STRICTER / 1 V2_LOOSER / 103 state_mismatch / 1 nodata | index-gating v1 95% vs v2 98% | oscillation v1 1.09 vs v2 0.73 | warm 100% | day-flips v1 6/33 vs v2 3/33

| Ticker | v1 Action | v1 Regime | Earnings | v2 Eligible | v2 Gate | Divergence | sigma_fwd | FVRP | z | 1M/3M | accel_dn |
|--------|-----------|-----------|----------|-------------|---------|------------|-----------|------|------|-------|----------|
| XLF | CONDITIONAL | NORMAL | ETF | No | NORMAL | V2_STRICTER | 0.182 | 0.75 | -1.26 | 0.841 | 0.980 |
| XLI | CONDITIONAL | NORMAL | ETF | No | NORMAL | V2_STRICTER | 0.189 | 1.17 | +1.10 | 1.058 | 0.964 |
| AAPL | NO EDGE | NORMAL | 70d | No | NORMAL | AGREE | 0.303 | 0.83 | -0.48 | 0.924 | 0.740 |
| AMZN | NO EDGE | NORMAL | 70d | No | NORMAL | AGREE | 0.354 | 0.82 | -0.78 | 0.825 | 0.779 |
| CAT | NO EDGE | NORMAL | 70d | No | NORMAL | AGREE | 0.422 | 0.89 | -1.12 | 0.892 | 1.068 |
| EEM | WATCHLIST | NORMAL | ETF | No | NORMAL | AGREE | 0.269 | 0.92 | -0.70 | 0.964 | 0.899 |
| GLD | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.230 | 1.08 | -0.52 | 1.005 | 0.807 |
| GOOG | NO EDGE | NORMAL | 76d | No | NORMAL | AGREE | 0.295 | 0.96 | -0.36 | 0.849 | 0.758 |
| GS | NO EDGE | NORMAL | 54d | No | NORMAL | AGREE | 0.315 | 0.97 | -0.10 | 0.929 | 0.784 |
| HD | NO EDGE | NORMAL | 89d | No | NORMAL | AGREE | 0.301 | 0.83 | -1.30 | 0.906 | 0.890 |
| HOOD | NO EDGE | NORMAL | 76d | No | NORMAL | AGREE | 0.747 | 0.79 | -1.15 | 0.928 | 0.909 |
| IWM | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.205 | 0.85 | -1.12 | 0.898 | 0.898 |
| JNJ | NO EDGE | NORMAL | 54d | No | NORMAL | AGREE | 0.237 | 0.95 | -0.59 | 0.888 | 0.604 |
| JPM | NO EDGE | NORMAL | 54d | No | NORMAL | AGREE | 0.247 | 0.84 | -0.69 | 0.889 | 0.965 |
| KO | NO EDGE | NORMAL | 61d | No | NORMAL | AGREE | 0.219 | 0.85 | -0.69 | 0.928 | 0.563 |
| MCD | NO EDGE | NORMAL | 77d | No | CAUTION | STATE_MISMATCH | 0.231 | 0.90 | -0.57 | 0.913 | 1.059 |
| META | WATCHLIST | NORMAL | 69d | No | CAUTION | STATE_MISMATCH | 0.437 | 0.82 | -0.37 | 0.854 | 1.109 |
| MSFT | NO EDGE | NORMAL | 69d | No | NORMAL | AGREE | 0.305 | 0.85 | -0.78 | 0.835 | 0.994 |
| NFLX | NO EDGE | NORMAL | 61d | No | NORMAL | AGREE | 0.438 | 0.74 | -0.82 | 0.844 | 0.744 |
| NKE | NO EDGE | NORMAL | 40d | No | CAUTION | STATE_MISMATCH | 0.367 | 0.89 | -0.81 | 0.779 | 1.075 |
| NVDA | NO EDGE | CAUTION | 6d | No | NORMAL | STATE_MISMATCH | 0.425 | 0.94 | +0.37 | 1.003 | 0.821 |
| PLTR | NO EDGE | NORMAL | 74d | No | NORMAL | AGREE | 0.610 | 0.75 | -0.64 | 0.843 | 0.684 |
| QQQ | WATCHLIST | NORMAL | ETF | No | NORMAL | AGREE | 0.218 | 0.92 | -0.59 | 0.901 | 0.785 |
| SBUX | NO EDGE | NORMAL | 69d | No | NORMAL | AGREE | 0.315 | 0.79 | -1.16 | 0.800 | 0.997 |
| SPY | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.145 | 0.91 | -0.03 | 0.877 | 0.743 |
| TLT | NO EDGE | CAUTION | ETF | No | NORMAL | STATE_MISMATCH | 0.143 | 0.76 | -1.31 | 0.936 | 0.966 |
| TSLA | NO EDGE | NORMAL | 69d | No | NORMAL | AGREE | 0.526 | 0.79 | -0.73 | 0.906 | 0.513 |
| UBER | NO EDGE | CAUTION | 75d | No | NORMAL | STATE_MISMATCH | 0.505 | 0.68 | -1.33 | 0.871 | 0.904 |
| WMT | NO EDGE | CAUTION | 0d | No | CAUTION | AGREE | 0.383 | 0.76 | -2.07 | 1.030 | 1.852 |
| XLB | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.217 | 0.70 | -2.41 | — | 0.816 |
| XLE | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.262 | 1.01 | +1.36 | 1.016 | 0.596 |
| XLV | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.195 | 1.04 | +0.21 | 1.016 | 0.574 |
| XOM | NO EDGE | NORMAL | 71d | No | NORMAL | AGREE | 0.293 | 0.92 | +0.10 | 0.946 | 0.551 |

---

## 2026-08-19 (Wednesday)

**Shadow summary:** Checked 330 / 204 agree / 4 V2_STRICTER / 1 V2_LOOSER / 114 state_mismatch / 7 nodata | index-gating v1 97% vs v2 98% | oscillation v1 1.09 vs v2 0.76 | warm 100% | day-flips v1 4/33 vs v2 4/33

| Ticker | v1 Action | v1 Regime | Earnings | v2 Eligible | v2 Gate | Divergence | sigma_fwd | FVRP | z | 1M/3M | accel_dn |
|--------|-----------|-----------|----------|-------------|---------|------------|-----------|------|------|-------|----------|
| AAPL | NO EDGE | NORMAL | 71d | No | NORMAL | AGREE | 0.289 | 0.83 | -0.48 | 0.912 | 0.795 |
| AMZN | NO EDGE | NORMAL | 71d | No | NORMAL | AGREE | 0.342 | 0.83 | -0.69 | 0.826 | 0.837 |
| CAT | NO EDGE | NORMAL | 71d | No | NORMAL | AGREE | 0.408 | 0.94 | -0.72 | 0.915 | 1.020 |
| EEM | WATCHLIST | NORMAL | ETF | No | NORMAL | AGREE | 0.265 | 0.95 | -0.54 | 0.952 | 0.966 |
| GLD | NO EDGE | CAUTION | ETF | No | NORMAL | STATE_MISMATCH | 0.195 | 1.16 | +0.04 | 0.976 | 0.866 |
| GOOG | NO EDGE | NORMAL | 77d | No | NORMAL | AGREE | 0.293 | 0.97 | -0.28 | 0.871 | 0.814 |
| GS | NO EDGE | NORMAL | 55d | No | NORMAL | AGREE | 0.307 | 0.96 | -0.17 | 0.903 | 0.674 |
| HD | NO EDGE | NORMAL | 90d | No | DANGER | STATE_MISMATCH | 0.305 | 0.83 | -1.27 | 0.944 | 0.956 |
| HOOD | NO EDGE | NORMAL | 77d | No | NORMAL | AGREE | 0.691 | 0.81 | -0.98 | 0.901 | 0.976 |
| IWM | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.193 | 0.88 | -0.73 | 0.863 | 0.964 |
| JNJ | NO EDGE | NORMAL | 55d | No | NORMAL | AGREE | 0.241 | 0.92 | -0.88 | 0.871 | 0.648 |
| JPM | NO EDGE | NORMAL | 55d | No | NORMAL | AGREE | 0.237 | 0.86 | -0.53 | 0.866 | 0.646 |
| KO | NO EDGE | NORMAL | 62d | No | NORMAL | AGREE | 0.224 | 0.84 | -0.77 | 0.956 | 0.605 |
| MCD | NO EDGE | NORMAL | 78d | No | CAUTION | STATE_MISMATCH | 0.225 | 0.88 | -0.73 | 0.850 | 1.137 |
| META | NO EDGE | NORMAL | 70d | No | NORMAL | AGREE | 0.440 | 0.81 | -0.40 | 0.855 | 1.191 |
| MSFT | NO EDGE | NORMAL | 70d | No | NORMAL | AGREE | 0.304 | 0.86 | -0.70 | 0.839 | 1.068 |
| NFLX | NO EDGE | NORMAL | 62d | No | NORMAL | AGREE | 0.447 | 0.72 | -0.99 | 0.827 | 0.799 |
| NKE | NO EDGE | NORMAL | 41d | No | CAUTION | STATE_MISMATCH | 0.380 | 0.87 | -0.93 | 0.779 | 1.154 |
| NVDA | NO EDGE | NORMAL | 7d | No | NORMAL | AGREE | 0.425 | 0.92 | +0.23 | 0.989 | 0.845 |
| PLTR | NO EDGE | NORMAL | 75d | No | NORMAL | AGREE | 0.576 | 0.77 | -0.55 | 0.823 | 0.735 |
| QQQ | WATCHLIST | NORMAL | ETF | No | NORMAL | AGREE | 0.224 | 0.90 | -0.78 | 0.903 | 0.839 |
| SBUX | NO EDGE | NORMAL | 70d | No | NORMAL | AGREE | 0.295 | 0.86 | -0.83 | 0.829 | 0.976 |
| SPY | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.143 | 0.92 | +0.10 | 0.870 | 0.799 |
| TLT | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.118 | 0.88 | +0.04 | 0.919 | 1.037 |
| TSLA | NO EDGE | NORMAL | 70d | No | NORMAL | AGREE | 0.526 | 0.77 | -0.97 | 0.900 | 0.551 |
| UBER | NO EDGE | CAUTION | 76d | No | NORMAL | STATE_MISMATCH | 0.462 | 0.70 | -1.13 | 0.878 | 0.971 |
| WMT | AVOID | DANGER | 1d | No | CAUTION | STATE_MISMATCH | 0.256 | 1.15 | +0.43 | 1.039 | 0.572 |
| XLB | NO EDGE | NORMAL | ETF | No | CAUTION | STATE_MISMATCH | 0.178 | 1.07 | -0.51 | 0.976 | 0.877 |
| XLE | NO EDGE | CAUTION | ETF | No | NORMAL | STATE_MISMATCH | 0.271 | 0.97 | +1.00 | 0.950 | 0.636 |
| XLF | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.174 | 0.80 | -0.80 | 0.838 | 0.919 |
| XLI | SELL PREMIUM | NORMAL | ETF | Yes | NORMAL | AGREE | 0.184 | 1.38 | +2.15 | 1.043 | 0.936 |
| XLV | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.175 | 0.85 | -1.20 | 0.913 | 0.617 |
| XOM | NO EDGE | CAUTION | 72d | No | NORMAL | STATE_MISMATCH | 0.298 | 0.94 | +0.33 | 0.953 | 0.549 |

---

## 2026-08-18 (Tuesday)

**Shadow summary:** Checked 330 / 199 agree / 5 V2_STRICTER / 1 V2_LOOSER / 117 state_mismatch / 8 nodata | index-gating v1 98% vs v2 99% | oscillation v1 1.42 vs v2 0.91 | warm 100% | day-flips v1 0/33 vs v2 0/33

| Ticker | v1 Action | v1 Regime | Earnings | v2 Eligible | v2 Gate | Divergence | sigma_fwd | FVRP | z | 1M/3M | accel_dn |
|--------|-----------|-----------|----------|-------------|---------|------------|-----------|------|------|-------|----------|
| XLI | CONDITIONAL | NORMAL | ETF | No | NORMAL | V2_STRICTER | 0.173 | 1.09 | +0.67 | 0.808 | 0.623 |
| GLD | NO EDGE | NORMAL | ETF | Yes | NORMAL | V2_LOOSER | 0.183 | 1.25 | +0.60 | 0.979 | 0.625 |
| AAPL | NO EDGE | NORMAL | 72d | No | NORMAL | AGREE | 0.282 | 0.83 | -0.46 | 0.900 | 0.854 |
| AMZN | NO EDGE | NORMAL | 72d | No | NORMAL | AGREE | 0.356 | 0.80 | -0.91 | 0.838 | 0.874 |
| CAT | NO EDGE | NORMAL | 72d | No | NORMAL | AGREE | 0.379 | 1.00 | -0.30 | 0.893 | 0.604 |
| EEM | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.234 | 1.11 | +0.20 | 0.943 | 0.447 |
| GOOG | NO EDGE | NORMAL | 78d | No | NORMAL | AGREE | 0.298 | 0.92 | -0.64 | 0.846 | 0.875 |
| GS | NO EDGE | NORMAL | 56d | No | NORMAL | AGREE | 0.295 | 1.01 | +0.34 | 0.915 | 0.663 |
| HD | AVOID | DANGER | TBD | No | DANGER | AGREE | 0.279 | 1.04 | +0.32 | 1.008 | 1.026 |
| HOOD | NO EDGE | NORMAL | 78d | No | NORMAL | AGREE | 0.647 | 0.88 | -0.13 | 0.915 | 0.735 |
| IWM | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.181 | 0.97 | +0.27 | 0.884 | 0.602 |
| JNJ | NO EDGE | NORMAL | 56d | No | NORMAL | AGREE | 0.225 | 1.06 | +0.23 | 0.934 | 0.696 |
| JPM | NO EDGE | NORMAL | 56d | No | NORMAL | AGREE | 0.240 | 0.79 | -1.24 | 0.830 | 0.694 |
| KO | NO EDGE | NORMAL | 63d | No | NORMAL | AGREE | 0.203 | 0.91 | -0.18 | 0.966 | 0.650 |
| MCD | NO EDGE | NORMAL | 79d | No | NORMAL | AGREE | 0.232 | 0.87 | -0.82 | 0.900 | 1.221 |
| META | NO EDGE | NORMAL | 71d | No | NORMAL | AGREE | 0.420 | 0.81 | -0.43 | 0.839 | 1.024 |
| MSFT | NO EDGE | NORMAL | 71d | No | NORMAL | AGREE | 0.319 | 0.83 | -0.88 | 0.863 | 1.147 |
| NFLX | NO EDGE | NORMAL | 63d | No | NORMAL | AGREE | 0.430 | 0.75 | -0.76 | 0.841 | 0.858 |
| NKE | NO EDGE | NORMAL | 42d | No | NORMAL | AGREE | 0.367 | 0.92 | -0.68 | 0.795 | 1.240 |
| NVDA | NO EDGE | NORMAL | 8d | No | NORMAL | AGREE | 0.385 | 1.01 | +1.04 | 0.982 | 0.673 |
| PLTR | NO EDGE | CAUTION | 76d | No | NORMAL | STATE_MISMATCH | 0.588 | 0.76 | -0.58 | 0.843 | 0.781 |
| QQQ | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.193 | 1.03 | +0.64 | 0.893 | 0.497 |
| SBUX | NO EDGE | NORMAL | 71d | No | NORMAL | AGREE | 0.282 | 0.93 | -0.53 | 0.928 | 0.592 |
| SPY | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.133 | 1.01 | +0.88 | 0.854 | 0.655 |
| TLT | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.122 | 0.93 | +0.55 | 0.968 | 1.114 |
| TSLA | NO EDGE | NORMAL | 71d | No | NORMAL | AGREE | 0.525 | 0.74 | -1.32 | 0.881 | 0.582 |
| UBER | NO EDGE | CAUTION | 77d | No | CAUTION | AGREE | 0.464 | 0.72 | -0.95 | 0.892 | 1.038 |
| WMT | AVOID | DANGER | 2d | No | CAUTION | STATE_MISMATCH | 0.253 | 1.18 | +0.56 | 1.047 | 0.522 |
| XLB | NO EDGE | NORMAL | ETF | No | CAUTION | STATE_MISMATCH | 0.182 | 1.14 | -0.21 | 1.029 | 0.829 |
| XLE | NO EDGE | CAUTION | ETF | No | NORMAL | STATE_MISMATCH | 0.263 | 0.89 | +0.30 | 0.925 | 0.683 |
| XLF | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.180 | 0.74 | -1.34 | 0.827 | 0.987 |
| XLV | NO EDGE | NORMAL | ETF | No | DANGER | STATE_MISMATCH | 0.172 | 0.88 | -1.00 | 0.959 | 0.663 |
| XOM | NO EDGE | NORMAL | 73d | No | NORMAL | AGREE | 0.288 | 0.96 | +0.53 | 0.972 | 0.590 |

---

## 2026-08-17 (Monday)

**Shadow summary:** Checked 330 / 192 agree / 5 V2_STRICTER / 0 V2_LOOSER / 124 state_mismatch / 9 nodata | index-gating v1 99% vs v2 100% | oscillation v1 1.67 vs v2 0.97 | warm 100% | day-flips v1 5/33 vs v2 4/33

| Ticker | v1 Action | v1 Regime | Earnings | v2 Eligible | v2 Gate | Divergence | sigma_fwd | FVRP | z | 1M/3M | accel_dn |
|--------|-----------|-----------|----------|-------------|---------|------------|-----------|------|------|-------|----------|
| XLV | CONDITIONAL | NORMAL | ETF | No | DANGER | V2_STRICTER | 0.173 | 1.24 | +1.43 | 1.087 | 0.698 |
| AAPL | NO EDGE | NORMAL | 73d | No | NORMAL | AGREE | 0.285 | 0.79 | -0.87 | 0.883 | 0.917 |
| AMZN | NO EDGE | NORMAL | 73d | No | NORMAL | AGREE | 0.324 | 0.84 | -0.66 | 0.814 | 0.928 |
| CAT | NO EDGE | NORMAL | 73d | No | NORMAL | AGREE | 0.381 | 0.97 | -0.43 | 0.872 | 0.649 |
| EEM | WATCHLIST | NORMAL | ETF | No | NORMAL | AGREE | 0.228 | 1.06 | +0.01 | 0.950 | 0.481 |
| GLD | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.196 | 1.12 | -0.25 | 0.954 | 0.672 |
| GOOG | NO EDGE | NORMAL | 79d | No | NORMAL | AGREE | 0.308 | 0.86 | -1.06 | 0.827 | 0.930 |
| GS | NO EDGE | NORMAL | 57d | No | NORMAL | AGREE | 0.312 | 0.91 | -0.63 | 0.876 | 0.712 |
| HD | AVOID | DANGER | 1d | No | DANGER | AGREE | 0.273 | 1.07 | +0.56 | 1.032 | 1.098 |
| HOOD | NO EDGE | NORMAL | 79d | No | NORMAL | AGREE | 0.668 | 0.85 | -0.52 | 0.911 | 0.790 |
| IWM | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.189 | 0.88 | -0.76 | 0.867 | 0.600 |
| JNJ | WATCHLIST | NORMAL | 57d | No | NORMAL | AGREE | 0.218 | 0.96 | -0.53 | 0.862 | 0.748 |
| JPM | NO EDGE | NORMAL | 57d | No | NORMAL | AGREE | 0.241 | 0.80 | -1.15 | 0.842 | 0.698 |
| KO | NO EDGE | NORMAL | 64d | No | NORMAL | AGREE | 0.198 | 0.85 | -0.70 | 0.896 | 0.539 |
| MCD | NO EDGE | NORMAL | 80d | No | NORMAL | AGREE | 0.225 | 0.87 | -0.82 | 0.880 | 0.754 |
| META | NO EDGE | NORMAL | 72d | No | NORMAL | AGREE | 0.403 | 0.79 | -0.50 | 0.817 | 0.874 |
| MSFT | NO EDGE | NORMAL | 72d | No | NORMAL | AGREE | 0.286 | 0.87 | -0.62 | 0.829 | 0.761 |
| NFLX | NO EDGE | NORMAL | 64d | No | NORMAL | AGREE | 0.413 | 0.74 | -0.85 | 0.795 | 0.592 |
| NKE | NO EDGE | NORMAL | 43d | No | NORMAL | AGREE | 0.325 | 0.99 | -0.32 | 0.792 | 0.885 |
| NVDA | NO EDGE | NORMAL | 9d | No | NORMAL | AGREE | 0.407 | 0.93 | +0.30 | 0.962 | 0.723 |
| PLTR | NO EDGE | CAUTION | 77d | No | NORMAL | STATE_MISMATCH | 0.623 | 0.70 | -1.15 | 0.827 | 0.824 |
| QQQ | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.204 | 0.92 | -0.56 | 0.871 | 0.528 |
| SBUX | NO EDGE | NORMAL | 72d | No | NORMAL | AGREE | 0.280 | 0.88 | -0.74 | 0.860 | 0.636 |
| SPY | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.139 | 0.91 | -0.01 | 0.841 | 0.582 |
| TLT | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.127 | 0.89 | +0.09 | 0.963 | 0.993 |
| TSLA | NO EDGE | NORMAL | 72d | No | NORMAL | AGREE | 0.561 | 0.69 | -1.90 | 0.874 | 0.611 |
| UBER | NO EDGE | CAUTION | 78d | No | CAUTION | AGREE | 0.460 | 0.69 | -1.30 | 0.861 | 1.081 |
| WMT | AVOID | DANGER | 3d | No | CAUTION | STATE_MISMATCH | 0.234 | 1.21 | +0.70 | 1.010 | 0.560 |
| XLB | NO EDGE | NORMAL | ETF | No | CAUTION | STATE_MISMATCH | 0.186 | 1.02 | -0.73 | 1.000 | 0.843 |
| XLE | NO EDGE | CAUTION | ETF | No | NORMAL | STATE_MISMATCH | 0.269 | 0.89 | +0.23 | 0.962 | 0.734 |
| XLF | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.166 | 0.79 | -0.84 | 0.817 | 0.615 |
| XLI | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.184 | 1.05 | +0.42 | 0.952 | 0.666 |
| XOM | NO EDGE | NORMAL | 74d | No | NORMAL | AGREE | 0.286 | 0.95 | +0.35 | 0.951 | 0.634 |

---

## 2026-08-14 (Friday)

**Shadow summary:** Checked 330 / 178 agree / 5 V2_STRICTER / 0 V2_LOOSER / 137 state_mismatch / 10 nodata | index-gating v1 100% vs v2 100% | oscillation v1 1.79 vs v2 1.00 | warm 100% | day-flips v1 3/33 vs v2 3/33

| Ticker | v1 Action | v1 Regime | Earnings | v2 Eligible | v2 Gate | Divergence | sigma_fwd | FVRP | z | 1M/3M | accel_dn |
|--------|-----------|-----------|----------|-------------|---------|------------|-----------|------|------|-------|----------|
| AAPL | NO EDGE | CAUTION | 76d | No | CAUTION | AGREE | 0.304 | 0.76 | -1.11 | 0.908 | 0.985 |
| AMZN | NO EDGE | CAUTION | 76d | No | NORMAL | STATE_MISMATCH | 0.345 | 0.82 | -0.77 | 0.839 | 0.961 |
| CAT | WATCHLIST | NORMAL | 76d | No | NORMAL | AGREE | 0.396 | 0.96 | -0.56 | 0.894 | 0.697 |
| EEM | WATCHLIST | NORMAL | ETF | No | NORMAL | AGREE | 0.243 | 1.09 | +0.14 | 0.965 | 0.515 |
| GLD | NO EDGE | CAUTION | ETF | No | NORMAL | STATE_MISMATCH | 0.204 | 1.07 | -0.59 | 0.956 | 0.722 |
| GOOG | NO EDGE | CAUTION | 82d | No | CAUTION | AGREE | 0.312 | 0.89 | -0.85 | 0.854 | 0.998 |
| GS | NO EDGE | NORMAL | 60d | No | NORMAL | AGREE | 0.333 | 0.90 | -0.67 | 0.897 | 0.761 |
| HD | AVOID | DANGER | 4d | No | DANGER | AGREE | 0.290 | 1.06 | +0.49 | 1.058 | 1.150 |
| HOOD | NO EDGE | NORMAL | 82d | No | NORMAL | AGREE | 0.692 | 0.84 | -0.62 | 0.892 | 0.589 |
| IWM | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.201 | 0.80 | -1.77 | 0.849 | 0.645 |
| JNJ | WATCHLIST | NORMAL | 60d | No | NORMAL | AGREE | 0.229 | 0.98 | -0.31 | 0.895 | 0.752 |
| JPM | NO EDGE | NORMAL | 60d | No | NORMAL | AGREE | 0.245 | 0.80 | -1.12 | 0.835 | 0.749 |
| KO | NO EDGE | NORMAL | 67d | No | NORMAL | AGREE | 0.212 | 0.81 | -1.05 | 0.889 | 0.579 |
| MCD | NO EDGE | NORMAL | 83d | No | NORMAL | AGREE | 0.236 | 0.86 | -0.86 | 0.903 | 0.810 |
| META | NO EDGE | NORMAL | 75d | No | NORMAL | AGREE | 0.422 | 0.79 | -0.51 | 0.844 | 0.924 |
| MSFT | NO EDGE | NORMAL | 75d | No | NORMAL | AGREE | 0.301 | 0.86 | -0.71 | 0.848 | 0.811 |
| NFLX | NO EDGE | NORMAL | 67d | No | NORMAL | AGREE | 0.450 | 0.72 | -0.95 | 0.827 | 0.636 |
| NKE | NO EDGE | NORMAL | 46d | No | NORMAL | AGREE | 0.350 | 1.01 | -0.24 | 0.814 | 0.892 |
| NVDA | NO EDGE | NORMAL | 12d | No | CAUTION | STATE_MISMATCH | 0.434 | 0.90 | -0.01 | 0.977 | 0.776 |
| PLTR | NO EDGE | CAUTION | 80d | No | NORMAL | STATE_MISMATCH | 0.657 | 0.72 | -0.98 | 0.863 | 0.713 |
| QQQ | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.217 | 0.88 | -0.95 | 0.873 | 0.564 |
| SBUX | NO EDGE | NORMAL | 75d | No | NORMAL | AGREE | 0.297 | 0.81 | -1.07 | 0.784 | 0.673 |
| SPY | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.150 | 0.83 | -0.68 | 0.836 | 0.603 |
| TLT | NO EDGE | NORMAL | ETF | No | CAUTION | STATE_MISMATCH | 0.127 | 0.81 | -0.69 | 0.913 | 0.906 |
| TSLA | NO EDGE | NORMAL | 75d | No | NORMAL | AGREE | 0.540 | 0.70 | -1.75 | 0.872 | 0.657 |
| UBER | NO EDGE | CAUTION | 81d | No | CAUTION | AGREE | 0.454 | 0.75 | -0.76 | 0.910 | 1.161 |
| WMT | AVOID | DANGER | 6d | No | CAUTION | STATE_MISMATCH | 0.236 | 1.23 | +0.81 | 1.010 | 0.503 |
| XLB | NO EDGE | CAUTION | ETF | No | CAUTION | AGREE | 0.195 | 1.02 | -0.72 | 1.188 | 0.905 |
| XLE | NO EDGE | CAUTION | ETF | No | NORMAL | STATE_MISMATCH | 0.281 | 0.89 | +0.29 | 1.035 | 0.788 |
| XLF | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.180 | 0.76 | -1.24 | 0.838 | 0.642 |
| XLI | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.196 | 1.01 | +0.22 | 1.008 | 0.716 |
| XLV | NO EDGE | NORMAL | ETF | No | DANGER | STATE_MISMATCH | 0.181 | 0.89 | -0.90 | 0.930 | 0.616 |
| XOM | NO EDGE | NORMAL | 77d | No | NORMAL | AGREE | 0.299 | 0.93 | +0.15 | 0.973 | 0.681 |

---

## 2026-08-13 (Thursday)

**Shadow summary:** Checked 330 / 170 agree / 6 V2_STRICTER / 0 V2_LOOSER / 144 state_mismatch / 10 nodata | index-gating v1 100% vs v2 100% | oscillation v1 1.97 vs v2 1.03 | warm 100% | day-flips v1 9/33 vs v2 1/33

| Ticker | v1 Action | v1 Regime | Earnings | v2 Eligible | v2 Gate | Divergence | sigma_fwd | FVRP | z | 1M/3M | accel_dn |
|--------|-----------|-----------|----------|-------------|---------|------------|-----------|------|------|-------|----------|
| AAPL | NO EDGE | CAUTION | 77d | No | CAUTION | AGREE | 0.316 | 0.74 | -1.38 | 0.919 | 1.058 |
| AMZN | NO EDGE | CAUTION | 77d | No | NORMAL | STATE_MISMATCH | 0.353 | 0.80 | -0.85 | 0.838 | 1.009 |
| CAT | NO EDGE | NORMAL | 77d | No | NORMAL | AGREE | 0.425 | 0.90 | -0.90 | 0.902 | 0.749 |
| EEM | NO EDGE | NORMAL | ETF | No | CAUTION | STATE_MISMATCH | 0.262 | 0.96 | -0.46 | 0.930 | 0.553 |
| GLD | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.209 | 1.09 | -0.44 | 0.961 | 0.492 |
| GOOG | NO EDGE | CAUTION | 83d | No | CAUTION | AGREE | 0.329 | 0.85 | -1.15 | 0.855 | 1.072 |
| GS | NO EDGE | NORMAL | 61d | No | NORMAL | AGREE | 0.346 | 0.86 | -1.16 | 0.895 | 0.817 |
| HD | AVOID | DANGER | 5d | No | DANGER | AGREE | 0.295 | 1.08 | +0.60 | 1.084 | 1.226 |
| HOOD | NO EDGE | NORMAL | 83d | No | NORMAL | AGREE | 0.710 | 0.85 | -0.55 | 0.942 | 0.633 |
| IWM | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.206 | 0.81 | -1.66 | 0.869 | 0.692 |
| JNJ | NO EDGE | NORMAL | 61d | No | NORMAL | AGREE | 0.245 | 0.90 | -0.96 | 0.869 | 0.808 |
| JPM | NO EDGE | NORMAL | 61d | No | NORMAL | AGREE | 0.248 | 0.81 | -0.99 | 0.861 | 0.757 |
| KO | NO EDGE | NORMAL | 68d | No | NORMAL | AGREE | 0.223 | 0.78 | -1.33 | 0.885 | 0.622 |
| MCD | NO EDGE | NORMAL | 84d | No | NORMAL | AGREE | 0.241 | 0.83 | -1.12 | 0.881 | 0.662 |
| META | NO EDGE | NORMAL | 76d | No | NORMAL | AGREE | 0.447 | 0.76 | -0.71 | 0.858 | 0.993 |
| MSFT | NO EDGE | CAUTION | 76d | No | NORMAL | STATE_MISMATCH | 0.310 | 0.83 | -0.83 | 0.858 | 0.871 |
| NFLX | NO EDGE | NORMAL | 68d | No | NORMAL | AGREE | 0.405 | 0.80 | -0.46 | 0.852 | 0.683 |
| NKE | NO EDGE | NORMAL | 47d | No | NORMAL | AGREE | 0.352 | 0.94 | -0.53 | 0.791 | 0.958 |
| NVDA | NO EDGE | NORMAL | 13d | No | CAUTION | STATE_MISMATCH | 0.462 | 0.85 | -0.47 | 0.988 | 0.834 |
| PLTR | NO EDGE | CAUTION | 81d | No | NORMAL | STATE_MISMATCH | 0.673 | 0.67 | -1.43 | 0.855 | 0.765 |
| QQQ | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.226 | 0.81 | -1.77 | 0.864 | 0.606 |
| SBUX | NO EDGE | NORMAL | 76d | No | NORMAL | AGREE | 0.303 | 0.84 | -0.93 | 0.872 | 0.723 |
| SPY | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.152 | 0.78 | -1.19 | 0.826 | 0.647 |
| TLT | NO EDGE | NORMAL | ETF | No | CAUTION | STATE_MISMATCH | 0.118 | 0.89 | +0.12 | 0.988 | 0.973 |
| TSLA | NO EDGE | NORMAL | 76d | No | NORMAL | AGREE | 0.527 | 0.71 | -1.65 | 0.872 | 0.705 |
| UBER | NO EDGE | CAUTION | 82d | No | CAUTION | AGREE | 0.479 | 0.67 | -1.47 | 0.874 | 1.247 |
| WMT | AVOID | DANGER | 7d | No | DANGER | AGREE | 0.240 | 1.20 | +0.66 | 0.996 | 0.517 |
| XLB | NO EDGE | NORMAL | ETF | No | CAUTION | STATE_MISMATCH | 0.201 | 1.12 | -0.30 | 0.980 | 0.940 |
| XLE | NO EDGE | CAUTION | ETF | No | NORMAL | STATE_MISMATCH | 0.285 | 0.84 | -0.20 | 0.956 | 0.847 |
| XLF | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.169 | 0.80 | -0.81 | 0.679 | 0.689 |
| XLI | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.203 | 0.99 | +0.10 | 0.937 | 0.769 |
| XLV | NO EDGE | NORMAL | ETF | No | DANGER | STATE_MISMATCH | 0.189 | 0.84 | -1.25 | 1.058 | 0.661 |
| XOM | NO EDGE | NORMAL | 78d | No | CAUTION | STATE_MISMATCH | 0.300 | 0.92 | +0.15 | 0.967 | 0.666 |

---

## 2026-08-12 (Wednesday)

**Shadow summary:** Checked 330 / 167 agree / 9 V2_STRICTER / 0 V2_LOOSER / 142 state_mismatch / 12 nodata | index-gating v1 98% vs v2 100% | oscillation v1 2.12 vs v2 1.09 | warm 100% | day-flips v1 3/33 vs v2 2/33

| Ticker | v1 Action | v1 Regime | Earnings | v2 Eligible | v2 Gate | Divergence | sigma_fwd | FVRP | z | 1M/3M | accel_dn |
|--------|-----------|-----------|----------|-------------|---------|------------|-----------|------|------|-------|----------|
| AAPL | NO EDGE | CAUTION | 78d | No | CAUTION | AGREE | 0.337 | 0.71 | -1.68 | 0.935 | 1.119 |
| AMZN | NO EDGE | CAUTION | 78d | No | NORMAL | STATE_MISMATCH | 0.373 | 0.78 | -1.01 | 0.855 | 0.959 |
| CAT | NO EDGE | CAUTION | 78d | No | NORMAL | STATE_MISMATCH | 0.425 | 0.90 | -0.94 | 0.895 | 0.804 |
| EEM | NO EDGE | NORMAL | ETF | No | CAUTION | STATE_MISMATCH | 0.246 | 1.08 | +0.09 | 0.994 | 0.594 |
| GLD | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.213 | 1.12 | -0.23 | 0.985 | 0.529 |
| GOOG | NO EDGE | CAUTION | 84d | No | CAUTION | AGREE | 0.343 | 0.84 | -1.23 | 0.874 | 1.151 |
| GS | NO EDGE | NORMAL | 62d | No | NORMAL | AGREE | 0.317 | 0.99 | +0.12 | 0.926 | 0.878 |
| HD | AVOID | DANGER | 6d | No | DANGER | AGREE | 0.289 | 1.10 | +0.76 | 1.059 | 0.795 |
| HOOD | NO EDGE | NORMAL | 84d | No | NORMAL | AGREE | 0.681 | 0.85 | -0.47 | 0.892 | 0.680 |
| IWM | NO EDGE | CAUTION | ETF | No | NORMAL | STATE_MISMATCH | 0.199 | 0.87 | -0.88 | 0.894 | 0.744 |
| JNJ | WATCHLIST | NORMAL | 62d | No | NORMAL | AGREE | 0.237 | 0.97 | -0.41 | 0.930 | 0.868 |
| JPM | NO EDGE | CAUTION | 62d | No | NORMAL | STATE_MISMATCH | 0.253 | 0.79 | -1.17 | 0.858 | 0.813 |
| KO | NO EDGE | NORMAL | 69d | No | NORMAL | AGREE | 0.213 | 0.80 | -1.15 | 0.867 | 0.668 |
| MCD | NO EDGE | NORMAL | 85d | No | NORMAL | AGREE | 0.227 | 0.93 | -0.33 | 0.922 | 0.711 |
| META | NO EDGE | NORMAL | 77d | No | NORMAL | AGREE | 0.451 | 0.75 | -0.77 | 0.855 | 0.852 |
| MSFT | NO EDGE | CAUTION | 77d | No | NORMAL | STATE_MISMATCH | 0.308 | 0.86 | -0.65 | 0.872 | 0.500 |
| NFLX | NO EDGE | NORMAL | 69d | No | NORMAL | AGREE | 0.429 | 0.74 | -0.83 | 0.805 | 0.707 |
| NKE | NO EDGE | NORMAL | 48d | No | NORMAL | AGREE | 0.367 | 0.90 | -0.76 | 0.766 | 0.886 |
| NVDA | NO EDGE | NORMAL | 14d | No | CAUTION | STATE_MISMATCH | 0.475 | 0.81 | -0.90 | 0.982 | 0.896 |
| PLTR | NO EDGE | CAUTION | 82d | No | NORMAL | STATE_MISMATCH | 0.699 | 0.68 | -1.34 | 0.875 | 0.709 |
| QQQ | NO EDGE | CAUTION | ETF | No | NORMAL | STATE_MISMATCH | 0.216 | 0.89 | -0.81 | 0.889 | 0.651 |
| SBUX | NO EDGE | NORMAL | 77d | No | NORMAL | AGREE | 0.307 | 0.85 | -0.90 | 0.911 | 0.776 |
| SPY | NO EDGE | CAUTION | ETF | No | NORMAL | STATE_MISMATCH | 0.148 | 0.86 | -0.42 | 0.847 | 0.695 |
| TLT | NO EDGE | CAUTION | ETF | No | CAUTION | AGREE | 0.121 | 0.95 | +0.74 | 0.954 | 1.043 |
| TSLA | NO EDGE | NORMAL | 77d | No | NORMAL | AGREE | 0.515 | 0.74 | -1.35 | 0.873 | 0.725 |
| UBER | NO EDGE | CAUTION | 83d | No | CAUTION | AGREE | 0.461 | 0.71 | -1.10 | 0.898 | 1.019 |
| WMT | AVOID | DANGER | 8d | No | DANGER | AGREE | 0.252 | 1.20 | +0.66 | 1.048 | 0.547 |
| XLB | NO EDGE | CAUTION | ETF | No | CAUTION | AGREE | 0.203 | 1.07 | -0.52 | 1.000 | 0.807 |
| XLE | NO EDGE | CAUTION | ETF | No | NORMAL | STATE_MISMATCH | 0.299 | 0.83 | -0.40 | 0.963 | 0.910 |
| XLF | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.180 | 0.74 | -1.42 | 0.857 | 0.740 |
| XLI | NO EDGE | CAUTION | ETF | No | NORMAL | STATE_MISMATCH | 0.199 | 0.90 | -0.56 | 0.812 | 0.826 |
| XLV | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.182 | 0.89 | -0.85 | 1.131 | 0.710 |
| XOM | NO EDGE | CAUTION | 79d | No | CAUTION | AGREE | 0.310 | 0.96 | +0.47 | 1.028 | 0.715 |

---

## 2026-08-11 (Tuesday)

**Shadow summary:** Checked 330 / 168 agree / 13 V2_STRICTER / 0 V2_LOOSER / 137 state_mismatch / 12 nodata | index-gating v1 95% vs v2 100% | oscillation v1 2.24 vs v2 1.15 | warm 100% | day-flips v1 3/33 vs v2 4/33

| Ticker | v1 Action | v1 Regime | Earnings | v2 Eligible | v2 Gate | Divergence | sigma_fwd | FVRP | z | 1M/3M | accel_dn |
|--------|-----------|-----------|----------|-------------|---------|------------|-----------|------|------|-------|----------|
| AAPL | NO EDGE | CAUTION | 79d | No | CAUTION | AGREE | 0.351 | 0.70 | -1.80 | 0.923 | 1.178 |
| AMZN | NO EDGE | CAUTION | 79d | No | NORMAL | STATE_MISMATCH | 0.391 | 0.78 | -0.98 | 0.854 | 0.839 |
| CAT | NO EDGE | CAUTION | 79d | No | NORMAL | STATE_MISMATCH | 0.442 | 0.91 | -0.86 | 0.892 | 0.864 |
| EEM | NO EDGE | NORMAL | ETF | No | CAUTION | STATE_MISMATCH | 0.260 | 1.08 | +0.10 | 0.986 | 0.639 |
| GLD | NO EDGE | CAUTION | ETF | No | NORMAL | STATE_MISMATCH | 0.232 | 1.10 | -0.34 | 1.037 | 0.545 |
| GOOG | NO EDGE | NORMAL | 85d | No | CAUTION | STATE_MISMATCH | 0.339 | 0.88 | -0.94 | 0.882 | 0.978 |
| GS | NO EDGE | NORMAL | 63d | No | NORMAL | AGREE | 0.329 | 0.95 | -0.18 | 0.911 | 0.943 |
| HD | AVOID | DANGER | 7d | No | DANGER | AGREE | 0.295 | 1.12 | +0.88 | 1.085 | 0.854 |
| HOOD | NO EDGE | NORMAL | 85d | No | NORMAL | AGREE | 0.727 | 0.87 | -0.21 | 0.943 | 0.730 |
| IWM | NO EDGE | CAUTION | ETF | No | NORMAL | STATE_MISMATCH | 0.213 | 0.82 | -1.45 | 0.874 | 0.799 |
| JNJ | NO EDGE | NORMAL | 63d | No | NORMAL | AGREE | 0.231 | 0.96 | -0.45 | 0.846 | 0.880 |
| JPM | NO EDGE | CAUTION | 63d | No | NORMAL | STATE_MISMATCH | 0.262 | 0.79 | -1.22 | 0.870 | 0.873 |
| KO | NO EDGE | NORMAL | 70d | No | NORMAL | AGREE | 0.222 | 0.82 | -0.95 | 0.890 | 0.682 |
| MCD | NO EDGE | NORMAL | 86d | No | NORMAL | AGREE | 0.244 | 0.93 | -0.31 | 0.981 | 0.764 |
| META | NO EDGE | NORMAL | 78d | No | NORMAL | AGREE | 0.455 | 0.76 | -0.67 | 0.849 | 0.915 |
| MSFT | NO EDGE | CAUTION | 78d | No | NORMAL | STATE_MISMATCH | 0.331 | 0.84 | -0.79 | 0.856 | 0.512 |
| NFLX | NO EDGE | NORMAL | 70d | No | NORMAL | AGREE | 0.425 | 0.78 | -0.60 | 0.817 | 0.573 |
| NKE | NO EDGE | NORMAL | 49d | No | NORMAL | AGREE | 0.363 | 1.01 | -0.26 | 0.860 | 0.799 |
| NVDA | NO EDGE | NORMAL | 15d | No | CAUTION | STATE_MISMATCH | 0.465 | 0.87 | -0.28 | 0.983 | 0.962 |
| PLTR | NO EDGE | CAUTION | 83d | No | NORMAL | STATE_MISMATCH | 0.753 | 0.65 | -1.61 | 0.859 | 0.761 |
| QQQ | NO EDGE | CAUTION | ETF | No | NORMAL | STATE_MISMATCH | 0.224 | 0.93 | -0.43 | 0.920 | 0.685 |
| SBUX | NO EDGE | NORMAL | 78d | No | NORMAL | AGREE | 0.318 | 0.82 | -1.01 | 0.884 | 0.834 |
| SPY | NO EDGE | CAUTION | ETF | No | NORMAL | STATE_MISMATCH | 0.151 | 0.87 | -0.37 | 0.856 | 0.704 |
| TLT | NO EDGE | CAUTION | ETF | No | CAUTION | AGREE | 0.126 | 0.90 | +0.20 | 0.954 | 1.120 |
| TSLA | NO EDGE | NORMAL | 78d | No | NORMAL | AGREE | 0.535 | 0.74 | -1.30 | 0.874 | 0.778 |
| UBER | NO EDGE | CAUTION | 84d | No | CAUTION | AGREE | 0.494 | 0.69 | -1.26 | 0.897 | 1.095 |
| WMT | NO EDGE | CAUTION | 9d | No | DANGER | STATE_MISMATCH | 0.248 | 1.24 | +0.87 | 1.035 | 0.588 |
| XLB | NO EDGE | CAUTION | ETF | No | NORMAL | STATE_MISMATCH | 0.208 | 0.91 | -1.22 | 1.000 | 0.866 |
| XLE | NO EDGE | CAUTION | ETF | No | NORMAL | STATE_MISMATCH | 0.323 | 0.81 | -0.58 | 0.949 | 0.977 |
| XLF | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.191 | 0.71 | -1.71 | 0.865 | 0.795 |
| XLI | NO EDGE | CAUTION | ETF | No | DANGER | STATE_MISMATCH | 0.201 | 0.87 | -0.78 | 0.859 | 0.887 |
| XLV | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.190 | 0.86 | -1.11 | 0.955 | 0.743 |
| XOM | NO EDGE | CAUTION | 80d | No | CAUTION | AGREE | 0.333 | 0.87 | -0.35 | 0.981 | 0.768 |

---

## 2026-08-10 (Monday)

**Shadow summary:** Checked 330 / 174 agree / 17 V2_STRICTER / 0 V2_LOOSER / 126 state_mismatch / 13 nodata | index-gating v1 93% vs v2 100% | oscillation v1 2.36 vs v2 1.09 | warm 100% | day-flips v1 4/33 vs v2 3/33

| Ticker | v1 Action | v1 Regime | Earnings | v2 Eligible | v2 Gate | Divergence | sigma_fwd | FVRP | z | 1M/3M | accel_dn |
|--------|-----------|-----------|----------|-------------|---------|------------|-----------|------|------|-------|----------|
| AAPL | NO EDGE | CAUTION | 80d | No | CAUTION | AGREE | 0.345 | 0.70 | -1.78 | 0.901 | 1.222 |
| AMZN | NO EDGE | CAUTION | 80d | No | NORMAL | STATE_MISMATCH | 0.416 | 0.73 | -1.26 | 0.862 | 0.902 |
| CAT | NO EDGE | CAUTION | 80d | No | NORMAL | STATE_MISMATCH | 0.478 | 0.85 | -1.25 | 0.898 | 0.923 |
| EEM | NO EDGE | NORMAL | ETF | No | CAUTION | STATE_MISMATCH | 0.280 | 1.02 | -0.16 | 0.983 | 0.651 |
| GLD | NO EDGE | CAUTION | ETF | No | NORMAL | STATE_MISMATCH | 0.250 | 0.94 | -1.54 | 0.981 | 0.586 |
| GOOG | NO EDGE | NORMAL | 86d | No | CAUTION | STATE_MISMATCH | 0.367 | 0.78 | -1.71 | 0.847 | 1.050 |
| GS | WATCHLIST | NORMAL | 64d | No | CAUTION | STATE_MISMATCH | 0.349 | 0.93 | -0.43 | 0.925 | 1.006 |
| HD | NO EDGE | NORMAL | 8d | No | DANGER | STATE_MISMATCH | 0.291 | 1.11 | +0.79 | 1.067 | 0.763 |
| HOOD | NO EDGE | NORMAL | 86d | No | NORMAL | AGREE | 0.761 | 0.77 | -1.42 | 0.880 | 0.784 |
| IWM | NO EDGE | CAUTION | ETF | No | NORMAL | STATE_MISMATCH | 0.222 | 0.78 | -1.99 | 0.868 | 0.792 |
| JNJ | WATCHLIST | NORMAL | 64d | No | NORMAL | AGREE | 0.250 | 0.91 | -0.86 | 0.910 | 0.946 |
| JPM | NO EDGE | CAUTION | 64d | No | NORMAL | STATE_MISMATCH | 0.282 | 0.72 | -1.95 | 0.840 | 0.938 |
| KO | NO EDGE | NORMAL | 71d | No | NORMAL | AGREE | 0.232 | 0.78 | -1.33 | 0.893 | 0.726 |
| MCD | NO EDGE | NORMAL | 87d | No | NORMAL | AGREE | 0.250 | 0.84 | -1.05 | 0.909 | 0.812 |
| META | NO EDGE | NORMAL | 79d | No | CAUTION | STATE_MISMATCH | 0.458 | 0.76 | -0.69 | 0.844 | 0.983 |
| MSFT | NO EDGE | CAUTION | 79d | No | NORMAL | STATE_MISMATCH | 0.336 | 0.81 | -0.94 | 0.845 | 0.550 |
| NFLX | NO EDGE | NORMAL | 71d | No | NORMAL | AGREE | 0.437 | 0.75 | -0.80 | 0.802 | 0.616 |
| NKE | NO EDGE | NORMAL | 50d | No | NORMAL | AGREE | 0.363 | 0.93 | -0.59 | 0.782 | 0.858 |
| NVDA | NO EDGE | CAUTION | 16d | No | CAUTION | AGREE | 0.477 | 0.83 | -0.68 | 0.963 | 0.778 |
| PLTR | NO EDGE | CAUTION | 84d | No | NORMAL | STATE_MISMATCH | 0.799 | 0.63 | -1.91 | 0.867 | 0.817 |
| QQQ | NO EDGE | CAUTION | ETF | No | NORMAL | STATE_MISMATCH | 0.244 | 0.86 | -1.13 | 0.928 | 0.726 |
| SBUX | NO EDGE | NORMAL | 79d | No | NORMAL | AGREE | 0.341 | 0.72 | -1.57 | 0.837 | 0.799 |
| SPY | NO EDGE | CAUTION | ETF | No | NORMAL | STATE_MISMATCH | 0.161 | 0.79 | -1.13 | 0.856 | 0.756 |
| TLT | NO EDGE | CAUTION | ETF | No | CAUTION | AGREE | 0.126 | 0.87 | -0.13 | 0.920 | 0.997 |
| TSLA | NO EDGE | NORMAL | 79d | No | NORMAL | AGREE | 0.576 | 0.71 | -1.63 | 0.891 | 0.836 |
| UBER | NO EDGE | CAUTION | 85d | No | CAUTION | AGREE | 0.533 | 0.63 | -1.83 | 0.903 | 1.176 |
| WMT | CONDITIONAL | NORMAL | 10d | No | DANGER | STATE_MISMATCH | 0.270 | 1.14 | +0.37 | 1.040 | 0.631 |
| XLB | NO EDGE | CAUTION | ETF | No | NORMAL | STATE_MISMATCH | 0.221 | 0.97 | -0.97 | 1.310 | 0.931 |
| XLE | NO EDGE | CAUTION | ETF | No | CAUTION | AGREE | 0.327 | 0.70 | -1.96 | 0.893 | 1.050 |
| XLF | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.199 | 0.72 | -1.64 | 0.897 | 0.854 |
| XLI | NO EDGE | CAUTION | ETF | No | DANGER | STATE_MISMATCH | 0.214 | 1.04 | +0.38 | 1.088 | 0.941 |
| XLV | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.205 | 0.66 | -2.95 | 0.902 | 0.798 |
| XOM | NO EDGE | CAUTION | 81d | No | DANGER | STATE_MISMATCH | 0.339 | 0.86 | -0.51 | 0.982 | 0.825 |

---

## 2026-08-07 (Friday)

**Shadow summary:** Checked 330 / 177 agree / 20 V2_STRICTER / 0 V2_LOOSER / 120 state_mismatch / 13 nodata | index-gating v1 91% vs v2 100% | oscillation v1 2.55 vs v2 1.06 | warm 100% | day-flips v1 11/33 vs v2 5/33

| Ticker | v1 Action | v1 Regime | Earnings | v2 Eligible | v2 Gate | Divergence | sigma_fwd | FVRP | z | 1M/3M | accel_dn |
|--------|-----------|-----------|----------|-------------|---------|------------|-----------|------|------|-------|----------|
| HD | CONDITIONAL | NORMAL | 11d | No | DANGER | V2_STRICTER | 0.292 | 1.15 | +1.05 | 1.097 | 0.820 |
| SBUX | CONDITIONAL | NORMAL | 82d | No | NORMAL | V2_STRICTER | 0.341 | 0.88 | -0.75 | 0.963 | 0.859 |
| AAPL | NO EDGE | CAUTION | 83d | No | CAUTION | AGREE | 0.374 | 0.67 | -2.16 | 0.918 | 1.312 |
| AMZN | NO EDGE | CAUTION | 83d | No | NORMAL | STATE_MISMATCH | 0.448 | 0.69 | -1.53 | 0.866 | 0.968 |
| CAT | NO EDGE | NORMAL | 83d | No | NORMAL | AGREE | 0.512 | 0.83 | -1.40 | 0.915 | 0.943 |
| EEM | NO EDGE | CAUTION | ETF | No | CAUTION | AGREE | 0.284 | 1.05 | -0.02 | 0.940 | 0.699 |
| GLD | NO EDGE | CAUTION | ETF | No | NORMAL | STATE_MISMATCH | 0.238 | 0.97 | -1.30 | 0.994 | 0.629 |
| GOOG | NO EDGE | NORMAL | 89d | No | CAUTION | STATE_MISMATCH | 0.398 | 0.78 | -1.69 | 0.903 | 1.113 |
| GS | NO EDGE | NORMAL | 67d | No | CAUTION | STATE_MISMATCH | 0.371 | 0.91 | -0.64 | 0.944 | 1.081 |
| HOOD | NO EDGE | NORMAL | 89d | No | NORMAL | AGREE | 0.771 | 0.83 | -0.73 | 0.938 | 0.842 |
| IWM | NO EDGE | CAUTION | ETF | No | NORMAL | STATE_MISMATCH | 0.223 | 0.77 | -2.19 | 0.861 | 0.851 |
| JNJ | WATCHLIST | NORMAL | 67d | No | CAUTION | STATE_MISMATCH | 0.267 | 0.94 | -0.59 | 0.952 | 1.016 |
| JPM | NO EDGE | CAUTION | 67d | No | NORMAL | STATE_MISMATCH | 0.294 | 0.72 | -1.97 | 0.885 | 1.007 |
| KO | NO EDGE | NORMAL | 74d | No | NORMAL | AGREE | 0.248 | 0.78 | -1.39 | 0.921 | 0.780 |
| MCD | NO EDGE | NORMAL | 90d | No | DANGER | STATE_MISMATCH | 0.265 | 0.87 | -0.81 | 0.947 | 0.829 |
| META | NO EDGE | NORMAL | 82d | No | CAUTION | STATE_MISMATCH | 0.485 | 0.76 | -0.65 | 0.874 | 1.056 |
| MSFT | NO EDGE | CAUTION | 82d | No | NORMAL | STATE_MISMATCH | 0.365 | 0.81 | -0.91 | 0.884 | 0.591 |
| NFLX | NO EDGE | NORMAL | 74d | No | NORMAL | AGREE | 0.465 | 0.73 | -0.91 | 0.823 | 0.662 |
| NKE | NO EDGE | NORMAL | 53d | No | NORMAL | AGREE | 0.384 | 0.95 | -0.48 | 0.832 | 0.902 |
| NVDA | NO EDGE | CAUTION | 19d | No | CAUTION | AGREE | 0.506 | 0.83 | -0.76 | 0.990 | 0.836 |
| PLTR | NO EDGE | CAUTION | 87d | No | NORMAL | STATE_MISMATCH | 0.846 | 0.58 | -2.43 | 0.880 | 0.878 |
| QQQ | NO EDGE | CAUTION | ETF | No | NORMAL | STATE_MISMATCH | 0.255 | 0.82 | -1.66 | 0.926 | 0.780 |
| SPY | NO EDGE | CAUTION | ETF | No | NORMAL | STATE_MISMATCH | 0.169 | 0.75 | -1.62 | 0.862 | 0.812 |
| TLT | NO EDGE | CAUTION | ETF | No | CAUTION | AGREE | 0.128 | 0.86 | -0.15 | 1.007 | 1.071 |
| TSLA | NO EDGE | NORMAL | 82d | No | NORMAL | AGREE | 0.568 | 0.75 | -1.28 | 0.904 | 0.898 |
| UBER | NO EDGE | CAUTION | 88d | No | CAUTION | AGREE | 0.550 | 0.64 | -1.76 | 0.934 | 1.264 |
| WMT | SELL PREMIUM | NORMAL | 13d | No | DANGER | STATE_MISMATCH | 0.288 | 1.10 | +0.14 | 1.037 | 0.678 |
| XLB | NO DATA | NORMAL | ETF | No | NORMAL | NODATA_SKEW | — | — | — | — | — |
| XLE | NO EDGE | CAUTION | ETF | No | CAUTION | AGREE | 0.339 | 0.76 | -1.23 | 1.020 | 1.038 |
| XLF | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.209 | 0.68 | -2.13 | 0.854 | 0.870 |
| XLI | NO EDGE | CAUTION | ETF | No | CAUTION | AGREE | 0.225 | 0.94 | -0.27 | 1.055 | 1.010 |
| XLV | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.216 | 0.75 | -2.06 | 0.914 | 0.857 |
| XOM | NO EDGE | NORMAL | 84d | No | DANGER | STATE_MISMATCH | 0.350 | 0.77 | -1.47 | 0.918 | 0.761 |

---

## 2026-08-06 (Thursday)

**Shadow summary:** Checked 330 / 182 agree / 20 V2_STRICTER / 0 V2_LOOSER / 116 state_mismatch / 12 nodata | index-gating v1 90% vs v2 100% | oscillation v1 2.52 vs v2 0.94 | warm 100% | day-flips v1 20/33 vs v2 8/33

| Ticker | v1 Action | v1 Regime | Earnings | v2 Eligible | v2 Gate | Divergence | sigma_fwd | FVRP | z | 1M/3M | accel_dn |
|--------|-----------|-----------|----------|-------------|---------|------------|-----------|------|------|-------|----------|
| AAPL | NO EDGE | CAUTION | 84d | No | CAUTION | AGREE | 0.392 | 0.66 | -2.32 | 0.926 | 1.410 |
| AMZN | NO EDGE | CAUTION | 84d | No | NORMAL | STATE_MISMATCH | 0.490 | 0.66 | -1.81 | 0.886 | 1.040 |
| CAT | NO EDGE | NORMAL | 84d | No | DANGER | STATE_MISMATCH | 0.556 | 0.80 | -1.64 | 0.951 | 0.973 |
| EEM | NO EDGE | NORMAL | ETF | No | CAUTION | STATE_MISMATCH | 0.270 | 1.15 | +0.40 | 1.021 | 0.684 |
| GLD | NO EDGE | CAUTION | ETF | No | NORMAL | STATE_MISMATCH | 0.258 | 0.91 | -1.73 | 1.012 | 0.676 |
| GOOG | NO EDGE | CAUTION | 90d | No | CAUTION | AGREE | 0.432 | 0.77 | -1.82 | 0.921 | 1.180 |
| GS | NO EDGE | NORMAL | 68d | No | CAUTION | STATE_MISMATCH | 0.377 | 0.90 | -0.73 | 0.941 | 0.992 |
| HD | NO EDGE | NORMAL | 12d | No | DANGER | STATE_MISMATCH | 0.310 | 1.10 | +0.72 | 1.068 | 0.796 |
| HOOD | NO EDGE | NORMAL | 90d | No | NORMAL | AGREE | 0.799 | 0.84 | -0.56 | 0.963 | 0.848 |
| IWM | NO EDGE | CAUTION | ETF | No | NORMAL | STATE_MISMATCH | 0.228 | 0.81 | -1.74 | 0.911 | 0.861 |
| JNJ | NO EDGE | NORMAL | 68d | No | CAUTION | STATE_MISMATCH | 0.254 | 0.98 | -0.30 | 0.924 | 1.088 |
| JPM | NO EDGE | NORMAL | 68d | No | CAUTION | STATE_MISMATCH | 0.291 | 0.75 | -1.64 | 0.894 | 1.026 |
| KO | NO EDGE | NORMAL | 75d | No | NORMAL | AGREE | 0.247 | 0.78 | -1.31 | 0.918 | 0.838 |
| MCD | NO EDGE | CAUTION | 91d | No | DANGER | STATE_MISMATCH | 0.278 | 0.86 | -0.91 | 0.985 | 0.890 |
| META | NO EDGE | NORMAL | 83d | No | CAUTION | STATE_MISMATCH | 0.528 | 0.73 | -0.85 | 0.903 | 1.134 |
| MSFT | NO EDGE | CAUTION | 83d | No | NORMAL | STATE_MISMATCH | 0.394 | 0.75 | -1.27 | 0.895 | 0.635 |
| NFLX | NO EDGE | NORMAL | 75d | No | NORMAL | AGREE | 0.480 | 0.74 | -0.84 | 0.858 | 0.691 |
| NKE | NO EDGE | NORMAL | 54d | No | NORMAL | AGREE | 0.412 | 0.91 | -0.68 | 0.850 | 0.928 |
| NVDA | NO EDGE | CAUTION | 20d | No | CAUTION | AGREE | 0.525 | 0.81 | -0.89 | 1.006 | 0.898 |
| PLTR | NO EDGE | CAUTION | 88d | No | NORMAL | STATE_MISMATCH | 0.917 | 0.54 | -2.96 | 0.889 | 0.904 |
| QQQ | NO DATA | NORMAL | ETF | No | NORMAL | NODATA_SKEW | — | — | — | — | — |
| SBUX | NO EDGE | NORMAL | 83d | No | NORMAL | AGREE | 0.355 | 0.81 | -1.08 | 0.910 | 0.852 |
| SPY | NO DATA | NORMAL | ETF | No | NORMAL | NODATA_SKEW | — | — | — | — | — |
| TLT | NO DATA | NORMAL | ETF | No | CAUTION | NODATA_SKEW | — | — | — | — | — |
| TSLA | NO DATA | NORMAL | 83d | No | NORMAL | NODATA_SKEW | — | — | — | — | — |
| UBER | NO EDGE | CAUTION | 89d | No | DANGER | STATE_MISMATCH | 0.572 | 0.61 | -2.13 | 0.911 | 1.357 |
| WMT | NO EDGE | NORMAL | 14d | No | DANGER | STATE_MISMATCH | 0.301 | 1.03 | -0.26 | 1.018 | 0.725 |
| XLB | NO EDGE | CAUTION | ETF | No | CAUTION | AGREE | 0.239 | 0.78 | -1.96 | 0.841 | 0.994 |
| XLE | NO EDGE | NORMAL | ETF | No | CAUTION | STATE_MISMATCH | 0.337 | 0.75 | -1.25 | 1.013 | 1.115 |
| XLF | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.206 | 0.68 | -2.22 | 0.763 | 0.897 |
| XLI | NO DATA | NORMAL | ETF | No | CAUTION | NODATA_SKEW | — | — | — | — | — |
| XLV | NO DATA | NORMAL | ETF | No | CAUTION | NODATA_SKEW | — | — | — | — | — |
| XOM | NO EDGE | CAUTION | 85d | No | DANGER | STATE_MISMATCH | 0.354 | 0.90 | -0.12 | 1.069 | 0.817 |

---

## 2026-08-05 (Wednesday)

**Shadow summary:** Checked 330 / 188 agree / 22 V2_STRICTER / 0 V2_LOOSER / 113 state_mismatch / 7 nodata | index-gating v1 89% vs v2 100% | oscillation v1 2.36 vs v2 0.82 | warm 100% | day-flips v1 8/33 vs v2 2/33

| Ticker | v1 Action | v1 Regime | Earnings | v2 Eligible | v2 Gate | Divergence | sigma_fwd | FVRP | z | 1M/3M | accel_dn |
|--------|-----------|-----------|----------|-------------|---------|------------|-----------|------|------|-------|----------|
| WMT | SELL PREMIUM | NORMAL | 15d | No | DANGER | V2_STRICTER | 0.290 | 1.19 | +0.60 | 1.123 | 0.774 |
| AAPL | NO EDGE | CAUTION | 85d | No | CAUTION | AGREE | 0.419 | 0.63 | -2.66 | 0.943 | 1.514 |
| AMZN | NO EDGE | CAUTION | 85d | No | CAUTION | AGREE | 0.511 | 0.66 | -1.80 | 0.918 | 1.020 |
| CAT | NO EDGE | CAUTION | 85d | No | DANGER | STATE_MISMATCH | 0.594 | 0.78 | -1.83 | 0.986 | 1.040 |
| EEM | AVOID | DANGER | ETF | No | CAUTION | STATE_MISMATCH | 0.290 | 1.06 | +0.03 | 0.989 | 0.725 |
| GLD | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.214 | 1.03 | -0.79 | 0.989 | 0.726 |
| GOOG | NO EDGE | CAUTION | 91d | No | CAUTION | AGREE | 0.395 | 0.86 | -1.12 | 0.937 | 0.920 |
| GS | NO EDGE | CAUTION | 69d | No | CAUTION | AGREE | 0.393 | 0.91 | -0.57 | 0.998 | 1.065 |
| HD | AVOID | DANGER | 13d | No | DANGER | AGREE | 0.324 | 1.09 | +0.67 | 1.109 | 0.855 |
| HOOD | NO EDGE | CAUTION | 91d | No | DANGER | STATE_MISMATCH | 0.844 | 0.80 | -1.11 | 0.957 | 0.904 |
| IWM | NO EDGE | CAUTION | ETF | No | NORMAL | STATE_MISMATCH | 0.238 | 0.81 | -1.67 | 0.931 | 0.840 |
| JNJ | NO EDGE | CAUTION | 69d | No | CAUTION | AGREE | 0.262 | 1.07 | +0.38 | 1.062 | 1.169 |
| JPM | NO EDGE | CAUTION | 69d | No | CAUTION | AGREE | 0.306 | 0.68 | -2.41 | 0.874 | 1.103 |
| KO | NO EDGE | CAUTION | 76d | No | NORMAL | STATE_MISMATCH | 0.259 | 0.82 | -1.04 | 0.963 | 0.900 |
| MCD | AVOID | DANGER | 92d | No | DANGER | AGREE | 0.282 | 0.92 | -0.40 | 1.051 | 0.956 |
| META | NO EDGE | NORMAL | 84d | No | CAUTION | STATE_MISMATCH | 0.537 | 0.72 | -0.90 | 0.907 | 1.218 |
| MSFT | NO EDGE | CAUTION | 84d | No | CAUTION | AGREE | 0.417 | 0.75 | -1.26 | 0.912 | 0.576 |
| NFLX | NO EDGE | NORMAL | 76d | No | NORMAL | AGREE | 0.458 | 0.82 | -0.40 | 0.898 | 0.743 |
| NKE | NO EDGE | NORMAL | 55d | No | NORMAL | AGREE | 0.436 | 0.89 | -0.79 | 0.879 | 0.997 |
| NVDA | NO EDGE | CAUTION | 21d | No | DANGER | STATE_MISMATCH | 0.522 | 0.83 | -0.70 | 1.016 | 0.964 |
| PLTR | AVOID | DANGER | 89d | No | DANGER | AGREE | 0.980 | 0.56 | -2.72 | 0.953 | 0.864 |
| QQQ | NO EDGE | CAUTION | ETF | No | NORMAL | STATE_MISMATCH | 0.268 | 0.88 | -0.95 | 0.963 | 0.818 |
| SBUX | NO EDGE | CAUTION | 84d | No | DANGER | STATE_MISMATCH | 0.369 | 0.78 | -1.25 | 0.899 | 0.916 |
| SPY | NO EDGE | CAUTION | ETF | No | NORMAL | STATE_MISMATCH | 0.185 | 0.77 | -1.33 | 0.906 | 0.919 |
| TLT | NO EDGE | CAUTION | ETF | No | CAUTION | AGREE | 0.134 | 0.83 | -0.56 | 1.015 | 1.132 |
| TSLA | NO EDGE | CAUTION | 84d | No | CAUTION | AGREE | 0.582 | 0.79 | -0.82 | 0.948 | 1.011 |
| UBER | AVOID | DANGER | 0d | No | DANGER | AGREE | 0.432 | 1.09 | +1.63 | 1.084 | 0.824 |
| XLB | NO DATA | NORMAL | ETF | No | CAUTION | NODATA_SKEW | — | — | — | — | — |
| XLE | AVOID | DANGER | ETF | No | DANGER | AGREE | 0.342 | 0.75 | -1.29 | 1.011 | 0.865 |
| XLF | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.204 | 0.77 | -1.08 | 0.952 | 0.964 |
| XLI | NO EDGE | CAUTION | ETF | No | CAUTION | AGREE | 0.247 | 0.91 | -0.46 | 0.830 | 1.088 |
| XLV | NO EDGE | NORMAL | ETF | No | CAUTION | STATE_MISMATCH | 0.198 | 0.95 | -0.45 | 0.997 | 0.989 |
| XOM | NO EDGE | CAUTION | 86d | No | DANGER | STATE_MISMATCH | 0.369 | 0.88 | -0.24 | 1.106 | 0.645 |

---

## 2026-08-04 (Tuesday)

**Shadow summary:** Checked 330 / 187 agree / 23 V2_STRICTER / 0 V2_LOOSER / 114 state_mismatch / 6 nodata | index-gating v1 88% vs v2 100% | oscillation v1 2.30 vs v2 0.76 | warm 100% | day-flips v1 11/33 vs v2 5/33

| Ticker | v1 Action | v1 Regime | Earnings | v2 Eligible | v2 Gate | Divergence | sigma_fwd | FVRP | z | 1M/3M | accel_dn |
|--------|-----------|-----------|----------|-------------|---------|------------|-----------|------|------|-------|----------|
| WMT | CONDITIONAL | NORMAL | 16d | No | DANGER | V2_STRICTER | 0.301 | 1.06 | -0.07 | 1.097 | 0.832 |
| AAPL | NO EDGE | CAUTION | 86d | No | CAUTION | AGREE | 0.454 | 0.60 | -3.09 | 1.010 | 1.627 |
| AMZN | NO EDGE | CAUTION | 86d | No | CAUTION | AGREE | 0.541 | 0.62 | -2.11 | 1.005 | 0.889 |
| CAT | AVOID | DANGER | TBD | No | DANGER | AGREE | 0.474 | 1.07 | +0.22 | 1.095 | 1.117 |
| EEM | NO EDGE | CAUTION | ETF | No | CAUTION | AGREE | 0.299 | 1.03 | -0.09 | 1.011 | 0.778 |
| GLD | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.224 | 0.95 | -1.41 | 0.973 | 0.780 |
| GOOG | NO EDGE | CAUTION | 92d | No | CAUTION | AGREE | 0.410 | 0.82 | -1.48 | 0.991 | 0.989 |
| GS | NO EDGE | CAUTION | 70d | No | CAUTION | AGREE | 0.387 | 0.88 | -0.90 | 0.988 | 1.144 |
| HD | NO EDGE | NORMAL | 14d | No | DANGER | STATE_MISMATCH | 0.337 | 1.05 | +0.42 | 1.145 | 0.919 |
| HOOD | NO EDGE | CAUTION | 92d | No | DANGER | STATE_MISMATCH | 0.850 | 0.83 | -0.69 | 1.043 | 0.972 |
| IWM | NO EDGE | CAUTION | ETF | No | NORMAL | STATE_MISMATCH | 0.244 | 0.71 | -3.24 | 0.919 | 0.903 |
| JNJ | NO EDGE | NORMAL | 70d | No | CAUTION | STATE_MISMATCH | 0.274 | 0.92 | -0.74 | 0.974 | 1.255 |
| JPM | NO EDGE | CAUTION | 70d | No | CAUTION | AGREE | 0.290 | 0.73 | -1.85 | 0.904 | 1.184 |
| KO | NO EDGE | NORMAL | 77d | No | NORMAL | AGREE | 0.263 | 0.81 | -1.13 | 1.015 | 0.955 |
| MCD | AVOID | DANGER | TBD | No | DANGER | AGREE | 0.272 | 1.05 | +0.50 | 1.079 | 1.027 |
| META | NO EDGE | NORMAL | 85d | No | CAUTION | STATE_MISMATCH | 0.576 | 0.68 | -1.18 | 1.010 | 1.307 |
| MSFT | NO EDGE | CAUTION | 85d | No | CAUTION | AGREE | 0.441 | 0.69 | -1.66 | 0.990 | 0.619 |
| NFLX | NO EDGE | NORMAL | 77d | No | NORMAL | AGREE | 0.483 | 0.74 | -0.87 | 0.927 | 0.798 |
| NKE | NO EDGE | NORMAL | 56d | No | NORMAL | AGREE | 0.407 | 0.95 | -0.50 | 0.859 | 0.829 |
| NVDA | NO EDGE | CAUTION | 22d | No | DANGER | STATE_MISMATCH | 0.538 | 0.82 | -0.81 | 1.064 | 1.036 |
| PLTR | AVOID | DANGER | 90d | No | DANGER | AGREE | 0.705 | 1.31 | +3.03 | 1.286 | 0.928 |
| QQQ | NO EDGE | CAUTION | ETF | No | NORMAL | STATE_MISMATCH | 0.270 | 0.77 | -2.28 | 0.900 | 0.878 |
| SBUX | NO EDGE | CAUTION | 85d | No | DANGER | STATE_MISMATCH | 0.381 | 0.76 | -1.32 | 1.041 | 0.984 |
| SPY | NO EDGE | CAUTION | ETF | No | CAUTION | AGREE | 0.186 | 0.65 | -2.80 | 0.832 | 0.987 |
| TLT | NO EDGE | NORMAL | ETF | No | CAUTION | STATE_MISMATCH | 0.133 | 0.89 | +0.13 | 1.028 | 1.216 |
| TSLA | NO EDGE | CAUTION | 85d | No | CAUTION | AGREE | 0.607 | 0.75 | -1.28 | 0.992 | 1.086 |
| UBER | AVOID | DANGER | 1d | No | DANGER | AGREE | 0.455 | 0.98 | +0.93 | 1.119 | 0.885 |
| XLB | NO DATA | NORMAL | ETF | No | CAUTION | NODATA_SKEW | — | — | — | — | — |
| XLE | NO EDGE | CAUTION | ETF | No | DANGER | STATE_MISMATCH | 0.329 | 0.77 | -1.13 | 0.963 | 0.909 |
| XLF | NO EDGE | NORMAL | ETF | No | CAUTION | STATE_MISMATCH | 0.209 | 0.72 | -1.71 | 0.972 | 1.036 |
| XLI | NO EDGE | CAUTION | ETF | No | CAUTION | AGREE | 0.236 | 0.81 | -1.24 | 0.756 | 1.169 |
| XLV | NO EDGE | NORMAL | ETF | No | CAUTION | STATE_MISMATCH | 0.213 | 0.89 | -0.91 | 0.935 | 1.061 |
| XOM | AVOID | DANGER | 87d | No | DANGER | AGREE | 0.347 | 0.90 | -0.03 | 1.055 | 0.632 |

---

## 2026-08-03 (Monday)

**Shadow summary:** Checked 330 / 187 agree / 24 V2_STRICTER / 0 V2_LOOSER / 114 state_mismatch / 5 nodata | index-gating v1 88% vs v2 100% | oscillation v1 2.18 vs v2 0.73 | warm 100% | day-flips v1 10/33 vs v2 4/33

| Ticker | v1 Action | v1 Regime | Earnings | v2 Eligible | v2 Gate | Divergence | sigma_fwd | FVRP | z | 1M/3M | accel_dn |
|--------|-----------|-----------|----------|-------------|---------|------------|-----------|------|------|-------|----------|
| WMT | CONDITIONAL | NORMAL | 17d | No | DANGER | V2_STRICTER | 0.304 | 1.09 | +0.03 | 1.135 | 0.893 |
| AAPL | NO EDGE | CAUTION | 87d | No | DANGER | STATE_MISMATCH | 0.485 | 0.55 | -3.95 | 1.000 | 1.727 |
| AMZN | NO EDGE | CAUTION | 87d | No | DANGER | STATE_MISMATCH | 0.574 | 0.55 | -2.75 | 0.998 | 0.955 |
| CAT | AVOID | DANGER | TBD | No | DANGER | AGREE | 0.497 | 1.00 | -0.27 | 1.044 | 1.200 |
| EEM | NO EDGE | NORMAL | ETF | No | CAUTION | STATE_MISMATCH | 0.314 | 1.01 | -0.20 | 1.029 | 0.836 |
| GLD | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.237 | 0.88 | -2.03 | 0.963 | 0.838 |
| GOOG | NO EDGE | CAUTION | 93d | No | CAUTION | AGREE | 0.397 | 0.80 | -1.64 | 0.968 | 1.062 |
| GS | NO EDGE | NORMAL | 71d | No | CAUTION | STATE_MISMATCH | 0.400 | 0.86 | -1.09 | 0.976 | 1.229 |
| HD | NO EDGE | NORMAL | TBD | No | DANGER | STATE_MISMATCH | 0.296 | 1.14 | +0.95 | 1.093 | 0.987 |
| HOOD | NO EDGE | NORMAL | 93d | No | DANGER | STATE_MISMATCH | 0.831 | 0.82 | -0.85 | 1.014 | 1.044 |
| IWM | NO EDGE | CAUTION | ETF | No | CAUTION | AGREE | 0.251 | 0.70 | -3.36 | 0.933 | 0.970 |
| JNJ | WATCHLIST | NORMAL | 71d | No | CAUTION | STATE_MISMATCH | 0.270 | 0.90 | -0.90 | 0.937 | 1.327 |
| JPM | NO EDGE | NORMAL | 71d | No | CAUTION | STATE_MISMATCH | 0.295 | 0.74 | -1.84 | 0.912 | 1.272 |
| KO | NO EDGE | NORMAL | 78d | No | NORMAL | AGREE | 0.270 | 0.77 | -1.44 | 0.979 | 0.965 |
| MCD | AVOID | DANGER | TBD | No | DANGER | AGREE | 0.242 | 1.10 | +0.88 | 1.085 | 0.761 |
| META | NO EDGE | NORMAL | 86d | No | DANGER | STATE_MISMATCH | 0.594 | 0.65 | -1.42 | 0.998 | 1.404 |
| MSFT | NO EDGE | CAUTION | 86d | No | CAUTION | AGREE | 0.462 | 0.62 | -2.16 | 0.990 | 0.664 |
| NFLX | NO EDGE | NORMAL | 78d | No | NORMAL | AGREE | 0.490 | 0.69 | -1.15 | 0.890 | 0.857 |
| NKE | NO EDGE | NORMAL | 57d | No | NORMAL | AGREE | 0.381 | 0.98 | -0.36 | 0.857 | 0.891 |
| NVDA | NO EDGE | NORMAL | 23d | No | DANGER | STATE_MISMATCH | 0.515 | 0.85 | -0.55 | 1.051 | 1.113 |
| PLTR | AVOID | DANGER | 0d | No | DANGER | AGREE | 0.682 | 0.97 | +0.98 | 1.128 | 0.997 |
| QQQ | WATCHLIST | NORMAL | ETF | No | CAUTION | STATE_MISMATCH | 0.280 | 0.79 | -2.09 | 0.938 | 0.943 |
| SBUX | CONDITIONAL | NORMAL | 1d | No | DANGER | STATE_MISMATCH | 0.364 | 0.81 | -1.07 | 1.039 | 0.709 |
| SPY | NO EDGE | CAUTION | ETF | No | CAUTION | AGREE | 0.193 | 0.63 | -3.14 | 0.825 | 1.060 |
| TLT | NO EDGE | NORMAL | ETF | No | CAUTION | STATE_MISMATCH | 0.135 | 0.95 | +0.71 | 0.981 | 1.307 |
| TSLA | NO EDGE | CAUTION | 86d | No | CAUTION | AGREE | 0.616 | 0.73 | -1.47 | 0.984 | 1.166 |
| UBER | AVOID | DANGER | 2d | No | DANGER | AGREE | 0.459 | 0.97 | +0.87 | 1.081 | 0.951 |
| XLB | NO EDGE | CAUTION | ETF | No | CAUTION | AGREE | 0.248 | 0.92 | -1.21 | 1.000 | 1.232 |
| XLE | NO EDGE | NORMAL | ETF | No | DANGER | STATE_MISMATCH | 0.316 | 0.83 | -0.44 | 1.011 | 0.811 |
| XLF | NO EDGE | NORMAL | ETF | No | CAUTION | STATE_MISMATCH | 0.206 | 0.67 | -2.33 | 0.906 | 1.112 |
| XLI | NO DATA | NORMAL | ETF | No | CAUTION | NODATA_SKEW | — | — | — | — | — |
| XLV | NO EDGE | NORMAL | ETF | No | CAUTION | STATE_MISMATCH | 0.210 | 0.87 | -1.10 | 1.018 | 1.135 |
| XOM | NO EDGE | NORMAL | 4d | No | DANGER | STATE_MISMATCH | 0.355 | 0.86 | -0.49 | 1.041 | 0.672 |

---

## 2026-07-31 (Friday)

**Shadow summary:** Checked 330 / 186 agree / 27 V2_STRICTER / 0 V2_LOOSER / 113 state_mismatch / 4 nodata | index-gating v1 88% vs v2 100% | oscillation v1 2.24 vs v2 0.70 | warm 100% | day-flips v1 15/33 vs v2 3/33

| Ticker | v1 Action | v1 Regime | Earnings | v2 Eligible | v2 Gate | Divergence | sigma_fwd | FVRP | z | 1M/3M | accel_dn |
|--------|-----------|-----------|----------|-------------|---------|------------|-----------|------|------|-------|----------|
| WMT | CONDITIONAL | NORMAL | 20d | No | DANGER | V2_STRICTER | 0.294 | 1.08 | -0.00 | 1.115 | 0.950 |
| AAPL | NO EDGE | NORMAL | 90d | No | DANGER | STATE_MISMATCH | 0.308 | 0.99 | +0.77 | 1.035 | 0.788 |
| AMZN | AVOID | DANGER | 90d | No | DANGER | AGREE | 0.415 | 1.70 | +2.82 | 1.555 | 1.025 |
| CAT | AVOID | DANGER | 4d | No | DANGER | AGREE | 0.474 | 1.10 | +0.38 | 1.071 | 1.289 |
| EEM | NO EDGE | NORMAL | ETF | No | CAUTION | STATE_MISMATCH | 0.304 | 1.02 | -0.14 | 1.013 | 0.898 |
| GLD | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.221 | 1.02 | -0.89 | 0.983 | 0.740 |
| GOOG | NO EDGE | CAUTION | 96d | No | CAUTION | AGREE | 0.358 | 0.87 | -1.11 | 0.994 | 1.141 |
| GS | NO EDGE | NORMAL | 74d | No | CAUTION | STATE_MISMATCH | 0.400 | 0.88 | -0.93 | 0.990 | 1.314 |
| HD | NO EDGE | NORMAL | 18d | No | DANGER | STATE_MISMATCH | 0.302 | 1.12 | +0.83 | 1.090 | 1.051 |
| HOOD | NO EDGE | NORMAL | 96d | No | DANGER | STATE_MISMATCH | 0.797 | 0.85 | -0.45 | 1.028 | 1.121 |
| IWM | NO EDGE | CAUTION | ETF | No | CAUTION | AGREE | 0.237 | 0.84 | -1.39 | 0.983 | 1.007 |
| JNJ | NO EDGE | NORMAL | 74d | No | NORMAL | AGREE | 0.276 | 0.88 | -1.04 | 0.977 | 1.426 |
| JPM | NO EDGE | NORMAL | 74d | No | CAUTION | STATE_MISMATCH | 0.296 | 0.75 | -1.64 | 0.922 | 1.367 |
| KO | NO EDGE | CAUTION | 81d | No | CAUTION | AGREE | 0.277 | 0.74 | -1.80 | 0.962 | 0.944 |
| MCD | AVOID | DANGER | 4d | No | DANGER | AGREE | 0.239 | 1.10 | +0.85 | 1.062 | 0.817 |
| META | NO EDGE | CAUTION | 89d | No | DANGER | STATE_MISMATCH | 0.626 | 0.62 | -1.59 | 1.032 | 1.508 |
| MSFT | NO EDGE | CAUTION | 89d | No | DANGER | STATE_MISMATCH | 0.488 | 0.64 | -2.05 | 1.007 | 0.714 |
| NFLX | NO EDGE | CAUTION | 81d | No | NORMAL | STATE_MISMATCH | 0.490 | 0.74 | -0.85 | 0.959 | 0.809 |
| NKE | NO EDGE | NORMAL | 60d | No | NORMAL | AGREE | 0.394 | 0.92 | -0.60 | 0.839 | 0.887 |
| NVDA | NO EDGE | NORMAL | 26d | No | DANGER | STATE_MISMATCH | 0.490 | 0.91 | +0.04 | 1.069 | 1.195 |
| PLTR | AVOID | DANGER | 3d | No | DANGER | AGREE | 0.696 | 0.97 | +0.97 | 1.148 | 1.071 |
| QQQ | NO EDGE | NORMAL | ETF | No | CAUTION | STATE_MISMATCH | 0.270 | 0.90 | -0.74 | 0.996 | 1.013 |
| SBUX | REDUCE SIZE | CAUTION | 89d | No | DANGER | STATE_MISMATCH | 0.365 | 0.92 | -0.55 | 1.243 | 0.715 |
| SPY | NO EDGE | CAUTION | ETF | No | CAUTION | AGREE | 0.185 | 0.74 | -1.83 | 0.891 | 1.139 |
| TLT | NO EDGE | CAUTION | ETF | No | CAUTION | AGREE | 0.128 | 0.94 | +0.63 | 1.014 | 1.327 |
| TSLA | NO EDGE | CAUTION | 89d | No | CAUTION | AGREE | 0.588 | 0.78 | -0.92 | 0.996 | 1.253 |
| UBER | AVOID | DANGER | 5d | No | DANGER | AGREE | 0.474 | 0.98 | +0.91 | 1.140 | 1.021 |
| XLB | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.228 | 1.06 | -0.57 | 1.000 | 0.797 |
| XLE | NO EDGE | NORMAL | ETF | No | DANGER | STATE_MISMATCH | 0.316 | 0.86 | -0.06 | 1.028 | 0.872 |
| XLF | NO EDGE | NORMAL | ETF | No | CAUTION | STATE_MISMATCH | 0.210 | 0.68 | -2.22 | 0.892 | 1.193 |
| XLI | NO EDGE | CAUTION | ETF | No | CAUTION | AGREE | 0.237 | 0.86 | -0.80 | 1.064 | 1.349 |
| XLV | NO EDGE | NORMAL | ETF | No | CAUTION | STATE_MISMATCH | 0.210 | 0.85 | -1.23 | 0.818 | 1.177 |
| XOM | AVOID | DANGER | 7d | No | DANGER | AGREE | 0.335 | 0.90 | -0.06 | 1.037 | 0.613 |

---

## 2026-07-30 (Thursday)

**Shadow summary:** Checked 330 / 186 agree / 31 V2_STRICTER / 0 V2_LOOSER / 108 state_mismatch / 5 nodata | index-gating v1 88% vs v2 100% | oscillation v1 2.03 vs v2 0.67 | warm 100% | day-flips v1 6/33 vs v2 4/33

| Ticker | v1 Action | v1 Regime | Earnings | v2 Eligible | v2 Gate | Divergence | sigma_fwd | FVRP | z | 1M/3M | accel_dn |
|--------|-----------|-----------|----------|-------------|---------|------------|-----------|------|------|-------|----------|
| IWM | CONDITIONAL | NORMAL | ETF | No | CAUTION | V2_STRICTER | 0.232 | 0.91 | -0.52 | 1.010 | 1.082 |
| SPY | CONDITIONAL | NORMAL | ETF | No | CAUTION | V2_STRICTER | 0.181 | 0.85 | -0.65 | 0.915 | 1.223 |
| WMT | CONDITIONAL | NORMAL | 21d | No | DANGER | V2_STRICTER | 0.302 | 1.07 | -0.07 | 1.101 | 1.020 |
| AAPL | AVOID | DANGER | 0d | No | DANGER | AGREE | 0.298 | 0.99 | +0.83 | 1.036 | 0.666 |
| AMZN | AVOID | DANGER | 0d | No | DANGER | AGREE | 0.371 | 1.17 | +0.97 | 1.143 | 1.101 |
| CAT | AVOID | DANGER | TBD | No | DANGER | AGREE | 0.479 | 1.13 | +0.52 | 1.084 | 1.384 |
| EEM | NO EDGE | CAUTION | ETF | No | CAUTION | AGREE | 0.302 | 0.94 | -0.51 | 0.901 | 0.965 |
| GLD | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.233 | 0.95 | -1.44 | 0.997 | 0.795 |
| GOOG | NO EDGE | CAUTION | 97d | No | CAUTION | AGREE | 0.378 | 0.88 | -1.04 | 1.021 | 1.219 |
| GS | NO EDGE | CAUTION | 75d | No | CAUTION | AGREE | 0.388 | 0.95 | -0.24 | 0.992 | 1.412 |
| HD | NO EDGE | CAUTION | TBD | No | DANGER | STATE_MISMATCH | 0.313 | 1.11 | +0.80 | 1.109 | 1.027 |
| HOOD | AVOID | DANGER | 97d | No | DANGER | AGREE | 0.799 | 0.84 | -0.65 | 0.978 | 1.122 |
| JNJ | NO EDGE | CAUTION | 75d | No | NORMAL | STATE_MISMATCH | 0.247 | 1.05 | +0.23 | 0.995 | 0.786 |
| JPM | NO EDGE | NORMAL | 75d | No | NORMAL | AGREE | 0.299 | 0.75 | -1.75 | 0.927 | 1.468 |
| KO | NO EDGE | CAUTION | 82d | No | CAUTION | AGREE | 0.291 | 0.72 | -1.96 | 0.993 | 0.975 |
| MCD | AVOID | DANGER | TBD | No | DANGER | AGREE | 0.239 | 1.12 | +0.94 | 1.092 | 0.741 |
| META | AVOID | DANGER | 90d | No | DANGER | AGREE | 0.429 | 1.39 | +2.07 | 1.221 | 0.896 |
| MSFT | AVOID | DANGER | 90d | No | DANGER | AGREE | 0.333 | 1.37 | +1.62 | — | 0.767 |
| NFLX | NO EDGE | NORMAL | 82d | No | NORMAL | AGREE | 0.456 | 0.76 | -0.73 | 0.907 | 0.859 |
| NKE | NO EDGE | NORMAL | 61d | No | NORMAL | AGREE | 0.377 | 0.99 | -0.32 | 0.849 | 0.761 |
| NVDA | NO EDGE | NORMAL | 27d | No | DANGER | STATE_MISMATCH | 0.478 | 0.97 | +0.56 | 1.057 | 1.284 |
| PLTR | AVOID | DANGER | 4d | No | DANGER | AGREE | 0.735 | 0.96 | +0.89 | 1.144 | 1.147 |
| QQQ | NO EDGE | CAUTION | ETF | No | CAUTION | AGREE | 0.258 | 0.97 | +0.02 | 0.969 | 1.088 |
| SBUX | NO EDGE | NORMAL | 5d | No | DANGER | STATE_MISMATCH | 0.315 | 0.13 | -10.06 | 0.496 | 0.768 |
| TLT | NO EDGE | CAUTION | ETF | No | NORMAL | STATE_MISMATCH | 0.136 | 0.89 | +0.09 | 1.035 | 1.425 |
| TSLA | NO EDGE | CAUTION | 90d | No | CAUTION | AGREE | 0.605 | 0.79 | -0.80 | 1.022 | 1.346 |
| UBER | AVOID | DANGER | 6d | No | DANGER | AGREE | 0.479 | 0.94 | +0.69 | 1.149 | 1.061 |
| XLB | NO DATA | NORMAL | ETF | No | NORMAL | NODATA_SKEW | — | — | — | — | — |
| XLE | NO EDGE | CAUTION | ETF | No | DANGER | STATE_MISMATCH | 0.334 | 0.85 | -0.22 | 1.051 | 0.936 |
| XLF | NO EDGE | NORMAL | ETF | No | CAUTION | STATE_MISMATCH | 0.207 | 0.75 | -1.43 | 0.871 | 1.281 |
| XLI | NO DATA | NORMAL | ETF | No | CAUTION | NODATA_SKEW | — | — | — | — | — |
| XLV | NO EDGE | NORMAL | ETF | No | DANGER | STATE_MISMATCH | 0.191 | 0.89 | -0.89 | 1.000 | 0.834 |
| XOM | AVOID | DANGER | 8d | No | DANGER | AGREE | 0.353 | 0.91 | -0.02 | 1.061 | 0.658 |

---

## 2026-07-29 (Wednesday)

**Shadow summary:** Checked 330 / 182 agree / 32 V2_STRICTER / 0 V2_LOOSER / 113 state_mismatch / 3 nodata | index-gating v1 90% vs v2 100% | oscillation v1 2.15 vs v2 0.61 | warm 100% | day-flips v1 7/33 vs v2 3/33

| Ticker | v1 Action | v1 Regime | Earnings | v2 Eligible | v2 Gate | Divergence | sigma_fwd | FVRP | z | 1M/3M | accel_dn |
|--------|-----------|-----------|----------|-------------|---------|------------|-----------|------|------|-------|----------|
| IWM | CONDITIONAL | NORMAL | ETF | No | NORMAL | V2_STRICTER | 0.223 | 0.98 | +0.31 | 1.026 | 0.670 |
| SPY | SELL PREMIUM | NORMAL | ETF | No | NORMAL | V2_STRICTER | 0.172 | 1.00 | +0.76 | 1.039 | 0.863 |
| WMT | CONDITIONAL | NORMAL | 22d | No | DANGER | V2_STRICTER | 0.275 | 1.14 | +0.30 | 1.117 | 0.646 |
| XLI | SELL PREMIUM | NORMAL | ETF | No | CAUTION | V2_STRICTER | 0.199 | 1.31 | +1.85 | 1.127 | 0.555 |
| AAPL | AVOID | DANGER | 1d | No | DANGER | AGREE | 0.297 | 0.97 | +0.63 | 1.039 | 0.685 |
| AMZN | AVOID | DANGER | 1d | No | DANGER | AGREE | 0.360 | 1.18 | +1.02 | 1.152 | 1.088 |
| CAT | NO EDGE | CAUTION | 6d | No | DANGER | STATE_MISMATCH | 0.432 | 1.30 | +1.43 | 1.112 | 0.993 |
| EEM | NO EDGE | CAUTION | ETF | No | CAUTION | AGREE | 0.296 | 1.14 | +0.39 | 0.995 | 0.893 |
| GLD | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.214 | 1.04 | -0.75 | 0.994 | 0.854 |
| GOOG | NO EDGE | CAUTION | 98d | No | CAUTION | AGREE | 0.375 | 0.83 | -1.42 | 0.986 | 1.309 |
| GS | AVOID | DANGER | 76d | No | CAUTION | STATE_MISMATCH | 0.381 | 0.99 | +0.14 | 1.013 | 1.052 |
| HD | AVOID | DANGER | 20d | No | DANGER | AGREE | 0.309 | 1.12 | +0.85 | 1.111 | 0.923 |
| HOOD | AVOID | DANGER | 0d | No | DANGER | AGREE | 0.820 | 0.96 | +0.64 | 1.117 | 1.143 |
| JNJ | AVOID | DANGER | 76d | No | NORMAL | STATE_MISMATCH | 0.257 | 0.99 | -0.15 | 0.973 | 0.821 |
| JPM | NO EDGE | NORMAL | 76d | No | NORMAL | AGREE | 0.267 | 0.87 | -0.45 | 0.929 | 0.583 |
| KO | NO EDGE | CAUTION | 83d | No | DANGER | STATE_MISMATCH | 0.307 | 0.67 | -2.60 | 1.011 | 1.048 |
| MCD | AVOID | DANGER | 6d | No | DANGER | AGREE | 0.254 | 1.04 | +0.45 | 1.094 | 0.763 |
| META | AVOID | DANGER | 0d | No | DANGER | AGREE | 0.427 | 1.19 | +1.34 | 1.166 | 0.921 |
| MSFT | AVOID | DANGER | 0d | No | DANGER | AGREE | 0.327 | 1.35 | +1.54 | 1.182 | 0.795 |
| NFLX | NO EDGE | NORMAL | 83d | No | NORMAL | AGREE | 0.477 | 0.71 | -1.02 | 0.924 | 0.922 |
| NKE | NO EDGE | NORMAL | 62d | No | NORMAL | AGREE | 0.368 | 1.02 | -0.18 | 0.855 | 0.817 |
| NVDA | NO EDGE | NORMAL | 28d | No | DANGER | STATE_MISMATCH | 0.483 | 0.98 | +0.71 | 1.086 | 1.194 |
| PLTR | AVOID | DANGER | 5d | No | DANGER | AGREE | 0.770 | 0.88 | +0.31 | 1.136 | 1.230 |
| QQQ | NO EDGE | CAUTION | ETF | No | CAUTION | AGREE | 0.252 | 1.09 | +1.23 | 1.077 | 0.938 |
| SBUX | AVOID | DANGER | 6d | No | DANGER | AGREE | 0.327 | 1.09 | +0.09 | 1.123 | 0.825 |
| TLT | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.118 | 0.86 | -0.25 | 0.981 | 0.735 |
| TSLA | NO EDGE | CAUTION | 91d | No | CAUTION | AGREE | 0.629 | 0.75 | -1.24 | 1.014 | 1.418 |
| UBER | AVOID | DANGER | 7d | No | DANGER | AGREE | 0.483 | 1.00 | +1.03 | 1.180 | 1.140 |
| XLB | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.222 | 0.85 | -1.59 | — | 0.704 |
| XLE | NO EDGE | CAUTION | ETF | No | DANGER | STATE_MISMATCH | 0.311 | 0.85 | -0.23 | 0.994 | 1.006 |
| XLF | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.191 | 0.90 | +0.14 | 1.006 | 0.699 |
| XLV | NO EDGE | NORMAL | ETF | No | DANGER | STATE_MISMATCH | 0.197 | 0.94 | -0.50 | 0.812 | 0.805 |
| XOM | AVOID | DANGER | 2d | No | DANGER | AGREE | 0.326 | 1.07 | +1.48 | 1.165 | 0.707 |

---

## 2026-07-28 (Tuesday)

**Shadow summary:** Checked 329 / 175 agree / 31 V2_STRICTER / 0 V2_LOOSER / 120 state_mismatch / 3 nodata | index-gating v1 93% vs v2 100% | oscillation v1 2.15 vs v2 0.55 | warm 100% | day-flips v1 9/33 vs v2 2/33

| Ticker | v1 Action | v1 Regime | Earnings | v2 Eligible | v2 Gate | Divergence | sigma_fwd | FVRP | z | 1M/3M | accel_dn |
|--------|-----------|-----------|----------|-------------|---------|------------|-----------|------|------|-------|----------|
| IWM | SELL PREMIUM | NORMAL | ETF | No | NORMAL | V2_STRICTER | 0.232 | 0.90 | -0.68 | 0.997 | 0.720 |
| SPY | CONDITIONAL | NORMAL | ETF | No | NORMAL | V2_STRICTER | 0.180 | 0.85 | -0.56 | 0.961 | 0.927 |
| WMT | CONDITIONAL | NORMAL | 23d | No | DANGER | V2_STRICTER | 0.286 | 1.08 | -0.03 | 1.101 | 0.694 |
| XLI | CONDITIONAL | NORMAL | ETF | No | CAUTION | V2_STRICTER | 0.210 | 1.12 | +0.88 | 1.012 | 0.550 |
| AAPL | AVOID | DANGER | 2d | No | DANGER | AGREE | 0.288 | 1.02 | +0.98 | 1.039 | 0.736 |
| AMZN | AVOID | DANGER | 2d | No | DANGER | AGREE | 0.370 | 1.15 | +0.87 | 1.144 | 1.167 |
| CAT | AVOID | DANGER | TBD | No | DANGER | AGREE | 0.429 | 1.27 | +1.31 | 1.091 | 0.789 |
| EEM | NO EDGE | CAUTION | ETF | No | CAUTION | AGREE | 0.275 | 1.20 | +0.64 | 0.994 | 0.808 |
| GLD | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.200 | 1.11 | -0.29 | 0.986 | 0.790 |
| GOOG | NO EDGE | CAUTION | 99d | No | CAUTION | AGREE | 0.387 | 0.81 | -1.57 | 0.986 | 1.407 |
| GS | NO EDGE | CAUTION | 77d | No | CAUTION | AGREE | 0.390 | 0.92 | -0.53 | 0.993 | 1.075 |
| HD | NO EDGE | CAUTION | TBD | No | DANGER | STATE_MISMATCH | 0.302 | 1.12 | +0.84 | 1.104 | 0.992 |
| HOOD | AVOID | DANGER | 1d | No | DANGER | AGREE | 0.800 | 1.02 | +1.17 | 1.099 | 1.173 |
| JNJ | NO EDGE | CAUTION | 77d | No | NORMAL | STATE_MISMATCH | 0.238 | 1.05 | +0.22 | 0.964 | 0.882 |
| JPM | NO EDGE | NORMAL | 77d | No | NORMAL | AGREE | 0.277 | 0.84 | -0.70 | 0.943 | 0.626 |
| KO | AVOID | DANGER | 0d | No | DANGER | AGREE | 0.228 | 1.00 | +0.46 | 1.071 | 1.125 |
| MCD | AVOID | DANGER | TBD | No | DANGER | AGREE | 0.223 | 1.21 | +1.48 | 1.100 | 0.819 |
| META | AVOID | DANGER | 1d | No | DANGER | AGREE | 0.443 | 1.14 | +1.16 | 1.157 | 0.989 |
| MSFT | AVOID | DANGER | 1d | No | DANGER | AGREE | 0.333 | 1.31 | +1.39 | 1.152 | 0.854 |
| NFLX | NO EDGE | NORMAL | 84d | No | CAUTION | STATE_MISMATCH | 0.453 | 0.75 | -0.81 | 0.888 | 0.991 |
| NKE | NO EDGE | NORMAL | 63d | No | NORMAL | AGREE | 0.373 | 1.01 | -0.19 | 0.870 | 0.878 |
| NVDA | NO EDGE | NORMAL | 29d | No | NORMAL | AGREE | 0.495 | 0.93 | +0.28 | 1.058 | 1.283 |
| PLTR | AVOID | DANGER | 6d | No | DANGER | AGREE | 0.669 | 1.01 | +1.22 | 1.131 | 0.920 |
| QQQ | WATCHLIST | NORMAL | ETF | No | CAUTION | STATE_MISMATCH | 0.254 | 1.05 | +0.84 | 1.038 | 0.947 |
| SBUX | AVOID | DANGER | 7d | No | DANGER | AGREE | 0.300 | 1.32 | +1.04 | 1.190 | 0.857 |
| TLT | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.124 | 0.80 | -0.82 | 0.944 | 0.790 |
| TSLA | NO EDGE | CAUTION | 92d | No | CAUTION | AGREE | 0.661 | 0.72 | -1.59 | 1.007 | 1.522 |
| UBER | AVOID | DANGER | 8d | No | DANGER | AGREE | 0.498 | 0.91 | +0.46 | 1.080 | 1.225 |
| XLB | NO DATA | NORMAL | ETF | No | CAUTION | NODATA_SKEW | — | — | — | — | — |
| XLE | AVOID | DANGER | ETF | No | DANGER | AGREE | 0.315 | 0.89 | +0.20 | 1.069 | 0.937 |
| XLF | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.195 | 0.73 | -1.66 | 0.874 | 0.751 |
| XLV | NO EDGE | NORMAL | ETF | No | DANGER | STATE_MISMATCH | 0.176 | 0.97 | -0.32 | 1.087 | 0.865 |
| XOM | AVOID | DANGER | 10d | No | DANGER | AGREE | 0.328 | 0.93 | +0.20 | 1.002 | 0.635 |

---

## 2026-07-27 (Monday)

**Shadow summary:** Checked 329 / 166 agree / 29 V2_STRICTER / 1 V2_LOOSER / 131 state_mismatch / 2 nodata | index-gating v1 95% vs v2 99% | oscillation v1 2.12 vs v2 0.55 | warm 100% | day-flips v1 6/33 vs v2 1/33

| Ticker | v1 Action | v1 Regime | Earnings | v2 Eligible | v2 Gate | Divergence | sigma_fwd | FVRP | z | 1M/3M | accel_dn |
|--------|-----------|-----------|----------|-------------|---------|------------|-----------|------|------|-------|----------|
| IWM | CONDITIONAL | NORMAL | ETF | No | NORMAL | V2_STRICTER | 0.221 | 0.91 | -0.51 | 0.977 | 0.773 |
| WMT | CONDITIONAL | NORMAL | 24d | No | DANGER | V2_STRICTER | 0.254 | 1.20 | +0.58 | 1.081 | 0.746 |
| XLI | CONDITIONAL | NORMAL | ETF | No | NORMAL | V2_STRICTER | 0.199 | 1.15 | +1.05 | 1.000 | 0.590 |
| AAPL | NO EDGE | CAUTION | 3d | No | DANGER | STATE_MISMATCH | 0.302 | 0.96 | +0.49 | 1.020 | 0.791 |
| AMZN | AVOID | DANGER | 3d | No | DANGER | AGREE | 0.384 | 1.08 | +0.57 | 1.121 | 1.252 |
| CAT | NO EDGE | CAUTION | 8d | No | DANGER | STATE_MISMATCH | 0.386 | 1.38 | +1.88 | 1.075 | 0.772 |
| EEM | NO EDGE | NORMAL | ETF | No | CAUTION | STATE_MISMATCH | 0.266 | 1.22 | +0.71 | 0.976 | 0.868 |
| GLD | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.213 | 1.03 | -0.87 | 0.969 | 0.849 |
| GOOG | NO EDGE | CAUTION | 100d | No | CAUTION | AGREE | 0.410 | 0.73 | -2.22 | 0.942 | 1.511 |
| GS | NO EDGE | CAUTION | 78d | No | CAUTION | AGREE | 0.353 | 0.97 | -0.05 | 0.967 | 1.116 |
| HD | WATCHLIST | NORMAL | 22d | No | DANGER | STATE_MISMATCH | 0.296 | 1.13 | +0.88 | 1.073 | 1.065 |
| HOOD | AVOID | DANGER | 2d | No | DANGER | AGREE | 0.789 | 0.96 | +0.67 | 1.027 | 1.260 |
| JNJ | NO EDGE | NORMAL | 78d | No | NORMAL | AGREE | 0.231 | 1.04 | +0.18 | 0.954 | 0.947 |
| JPM | NO EDGE | NORMAL | 78d | No | NORMAL | AGREE | 0.260 | 0.86 | -0.50 | 0.923 | 0.672 |
| KO | AVOID | DANGER | 1d | No | DANGER | AGREE | 0.223 | 0.99 | +0.40 | 1.070 | 1.209 |
| MCD | NO EDGE | NORMAL | 8d | No | DANGER | STATE_MISMATCH | 0.219 | 1.21 | +1.50 | 1.058 | 0.880 |
| META | AVOID | DANGER | 2d | No | DANGER | AGREE | 0.444 | 1.11 | +1.03 | 1.126 | 1.061 |
| MSFT | AVOID | DANGER | 2d | No | DANGER | AGREE | 0.328 | 1.28 | +1.31 | 1.130 | 0.918 |
| NFLX | NO EDGE | NORMAL | 85d | No | CAUTION | STATE_MISMATCH | 0.478 | 0.71 | -1.04 | 0.902 | 1.064 |
| NKE | NO EDGE | NORMAL | 64d | No | NORMAL | AGREE | 0.381 | 0.98 | -0.33 | 0.872 | 0.943 |
| NVDA | NO EDGE | NORMAL | 30d | No | NORMAL | AGREE | 0.472 | 0.97 | +0.61 | 1.030 | 0.812 |
| PLTR | NO EDGE | CAUTION | 7d | No | DANGER | STATE_MISMATCH | 0.639 | 1.02 | +1.27 | 1.096 | 0.989 |
| QQQ | WATCHLIST | NORMAL | ETF | No | CAUTION | STATE_MISMATCH | 0.246 | 1.07 | +1.05 | 1.027 | 1.011 |
| SBUX | AVOID | DANGER | 2d | No | DANGER | AGREE | 0.306 | 1.29 | +0.93 | 1.200 | 0.921 |
| SPY | WATCHLIST | NORMAL | ETF | No | NORMAL | AGREE | 0.175 | 0.89 | -0.23 | 0.955 | 0.995 |
| TLT | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.119 | 0.85 | -0.31 | 0.939 | 0.848 |
| TSLA | NO EDGE | CAUTION | 93d | No | CAUTION | AGREE | 0.709 | 0.68 | -2.08 | 1.007 | 1.632 |
| UBER | NO EDGE | CAUTION | 9d | No | DANGER | STATE_MISMATCH | 0.509 | 0.96 | +0.74 | 1.087 | 1.315 |
| XLB | NO EDGE | NORMAL | ETF | No | CAUTION | STATE_MISMATCH | 0.213 | 1.10 | -0.42 | 1.000 | 0.812 |
| XLE | NO EDGE | CAUTION | ETF | No | DANGER | STATE_MISMATCH | 0.284 | 0.93 | +0.67 | 1.095 | 0.389 |
| XLF | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.188 | 0.82 | -0.60 | 0.971 | 0.807 |
| XLV | NO EDGE | NORMAL | ETF | No | CAUTION | STATE_MISMATCH | 0.178 | 1.05 | +0.24 | 1.063 | 0.929 |
| XOM | AVOID | DANGER | 4d | No | DANGER | AGREE | 0.297 | 1.10 | +1.80 | 1.058 | 0.430 |

---

## 2026-07-24 (Friday)

**Shadow summary:** Checked 329 / 161 agree / 28 V2_STRICTER / 2 V2_LOOSER / 136 state_mismatch / 2 nodata | index-gating v1 97% vs v2 98% | oscillation v1 2.18 vs v2 0.58 | warm 100% | day-flips v1 9/33 vs v2 3/33

| Ticker | v1 Action | v1 Regime | Earnings | v2 Eligible | v2 Gate | Divergence | sigma_fwd | FVRP | z | 1M/3M | accel_dn |
|--------|-----------|-----------|----------|-------------|---------|------------|-----------|------|------|-------|----------|
| IWM | CONDITIONAL | NORMAL | ETF | No | NORMAL | V2_STRICTER | 0.225 | 0.94 | -0.17 | 0.998 | 0.809 |
| WMT | SELL PREMIUM | NORMAL | 27d | No | DANGER | V2_STRICTER | 0.256 | 1.23 | +0.72 | 1.090 | 0.801 |
| AAPL | AVOID | DANGER | 6d | No | DANGER | AGREE | 0.294 | 0.98 | +0.70 | 1.032 | 0.849 |
| AMZN | AVOID | DANGER | 6d | No | DANGER | AGREE | 0.412 | 1.07 | +0.50 | 1.143 | 1.336 |
| CAT | NO EDGE | CAUTION | 11d | No | DANGER | STATE_MISMATCH | 0.401 | 1.34 | +1.68 | 1.084 | 0.820 |
| EEM | WATCHLIST | NORMAL | ETF | No | CAUTION | STATE_MISMATCH | 0.269 | 1.29 | +0.96 | 1.078 | 0.778 |
| GLD | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.226 | 1.01 | -1.05 | 0.981 | 0.912 |
| GOOG | NO EDGE | CAUTION | 103d | No | CAUTION | AGREE | 0.439 | 0.74 | -2.20 | 0.991 | 1.623 |
| GS | NO EDGE | CAUTION | 81d | No | CAUTION | AGREE | 0.367 | 0.92 | -0.52 | 0.944 | 1.161 |
| HD | NO EDGE | NORMAL | 25d | No | DANGER | STATE_MISMATCH | 0.299 | 1.10 | +0.71 | 1.072 | 1.144 |
| HOOD | AVOID | DANGER | 5d | No | DANGER | AGREE | 0.767 | 1.03 | +1.32 | 1.056 | 1.086 |
| JNJ | NO EDGE | NORMAL | 81d | No | CAUTION | STATE_MISMATCH | 0.232 | 1.06 | +0.30 | 0.964 | 1.017 |
| JPM | NO EDGE | NORMAL | 81d | No | NORMAL | AGREE | 0.258 | 0.88 | -0.32 | 0.926 | 0.722 |
| KO | AVOID | DANGER | 4d | No | DANGER | AGREE | 0.220 | 1.04 | +0.75 | 1.077 | 1.298 |
| MCD | WATCHLIST | NORMAL | 11d | No | DANGER | STATE_MISMATCH | 0.220 | 1.24 | +1.69 | 1.068 | 0.945 |
| META | AVOID | DANGER | 5d | No | DANGER | AGREE | 0.466 | 1.15 | +1.20 | 1.172 | 1.085 |
| MSFT | AVOID | DANGER | 5d | No | DANGER | AGREE | 0.330 | 1.34 | +1.51 | 1.144 | 0.986 |
| NFLX | NO EDGE | NORMAL | 88d | No | CAUTION | STATE_MISMATCH | 0.479 | 0.71 | -1.05 | 0.885 | 1.143 |
| NKE | NO EDGE | NORMAL | 67d | No | NORMAL | AGREE | 0.382 | 0.97 | -0.39 | 0.849 | 1.013 |
| NVDA | NO EDGE | CAUTION | 33d | No | NORMAL | STATE_MISMATCH | 0.466 | 0.89 | -0.14 | 0.948 | 0.842 |
| PLTR | CONDITIONAL | NORMAL | 10d | No | DANGER | STATE_MISMATCH | 0.661 | 1.02 | +1.21 | 1.107 | 1.060 |
| QQQ | NO EDGE | CAUTION | ETF | No | CAUTION | AGREE | 0.257 | 1.06 | +0.92 | 1.044 | 1.017 |
| SBUX | AVOID | DANGER | 5d | No | DANGER | AGREE | 0.309 | 1.30 | +0.95 | 1.225 | 0.989 |
| SPY | WATCHLIST | NORMAL | ETF | No | NORMAL | AGREE | 0.182 | 0.86 | -0.48 | 0.961 | 1.069 |
| TLT | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.121 | 0.88 | -0.02 | 0.950 | 0.911 |
| TSLA | NO EDGE | CAUTION | 96d | No | CAUTION | AGREE | 0.749 | 0.63 | -2.67 | 1.016 | 1.746 |
| UBER | WATCHLIST | NORMAL | 12d | No | DANGER | STATE_MISMATCH | 0.458 | 1.04 | +1.24 | 1.145 | 1.007 |
| XLB | NO EDGE | NORMAL | ETF | No | CAUTION | STATE_MISMATCH | 0.219 | 1.08 | -0.52 | 1.000 | 0.872 |
| XLE | AVOID | DANGER | ETF | No | DANGER | AGREE | 0.293 | 0.97 | +1.00 | 1.072 | 0.417 |
| XLF | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.188 | 0.87 | -0.14 | 0.986 | 0.867 |
| XLI | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.205 | 1.07 | +0.62 | 0.992 | 0.634 |
| XLV | NO EDGE | NORMAL | ETF | No | CAUTION | STATE_MISMATCH | 0.177 | 0.93 | -0.60 | 0.984 | 0.998 |
| XOM | AVOID | DANGER | 7d | No | DANGER | AGREE | 0.302 | 1.09 | +1.72 | 1.069 | 0.462 |

---

## 2026-07-23 (Thursday)

**Shadow summary:** Checked 329 / 153 agree / 30 V2_STRICTER / 2 V2_LOOSER / 141 state_mismatch / 3 nodata | index-gating v1 97% vs v2 98% | oscillation v1 2.03 vs v2 0.55 | warm 100% | day-flips v1 6/33 vs v2 0/33

| Ticker | v1 Action | v1 Regime | Earnings | v2 Eligible | v2 Gate | Divergence | sigma_fwd | FVRP | z | 1M/3M | accel_dn |
|--------|-----------|-----------|----------|-------------|---------|------------|-----------|------|------|-------|----------|
| IWM | CONDITIONAL | NORMAL | ETF | No | NORMAL | V2_STRICTER | 0.215 | 0.93 | -0.28 | 0.978 | 0.801 |
| WMT | CONDITIONAL | NORMAL | 28d | No | DANGER | V2_STRICTER | 0.271 | 1.15 | +0.33 | 1.081 | 0.861 |
| AAPL | NO EDGE | CAUTION | 7d | No | DANGER | STATE_MISMATCH | 0.293 | 1.01 | +0.90 | 1.031 | 0.798 |
| AMZN | CONDITIONAL | NORMAL | 7d | No | DANGER | STATE_MISMATCH | 0.341 | 1.25 | +1.30 | 1.131 | 0.765 |
| CAT | NO EDGE | CAUTION | TBD | No | DANGER | STATE_MISMATCH | 0.420 | 1.26 | +1.30 | 1.065 | 0.881 |
| EEM | NO EDGE | CAUTION | ETF | No | CAUTION | AGREE | 0.281 | 1.22 | +0.72 | 1.044 | 0.821 |
| GLD | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.212 | 1.05 | -0.69 | 0.971 | 0.732 |
| GOOG | NO EDGE | NORMAL | 104d | No | DANGER | STATE_MISMATCH | 0.327 | 0.69 | -2.69 | 0.679 | 1.141 |
| GS | NO EDGE | CAUTION | 82d | No | CAUTION | AGREE | 0.352 | 0.97 | -0.06 | 0.954 | 1.139 |
| HD | NO EDGE | NORMAL | TBD | No | DANGER | STATE_MISMATCH | 0.283 | 1.19 | +1.30 | 1.125 | 1.050 |
| HOOD | AVOID | DANGER | 6d | No | DANGER | AGREE | 0.761 | 1.02 | +1.19 | 1.030 | 1.110 |
| JNJ | NO EDGE | CAUTION | 82d | No | CAUTION | AGREE | 0.240 | 1.00 | -0.07 | 0.915 | 1.093 |
| JPM | NO EDGE | NORMAL | 82d | No | NORMAL | AGREE | 0.273 | 0.82 | -0.94 | 0.909 | 0.776 |
| KO | AVOID | DANGER | 5d | No | DANGER | AGREE | 0.229 | 1.01 | +0.58 | 1.047 | 1.327 |
| MCD | WATCHLIST | NORMAL | TBD | No | DANGER | STATE_MISMATCH | 0.225 | 1.23 | +1.63 | 1.091 | 1.010 |
| META | AVOID | DANGER | 6d | No | DANGER | AGREE | 0.428 | 1.24 | +1.54 | 1.162 | 0.945 |
| MSFT | AVOID | DANGER | 6d | No | DANGER | AGREE | 0.323 | 1.42 | +1.83 | 1.160 | 0.858 |
| NFLX | NO EDGE | NORMAL | 89d | No | CAUTION | STATE_MISMATCH | 0.516 | 0.67 | -1.31 | 0.903 | 1.228 |
| NKE | NO EDGE | NORMAL | 68d | No | NORMAL | AGREE | 0.379 | 0.98 | -0.32 | 0.871 | 0.814 |
| NVDA | NO EDGE | CAUTION | 34d | No | NORMAL | STATE_MISMATCH | 0.483 | 0.82 | -0.85 | 0.923 | 0.816 |
| PLTR | CONDITIONAL | NORMAL | 11d | No | DANGER | STATE_MISMATCH | 0.662 | 1.03 | +1.31 | 1.121 | 1.130 |
| QQQ | WATCHLIST | NORMAL | ETF | No | CAUTION | STATE_MISMATCH | 0.245 | 1.07 | +1.06 | 1.037 | 0.860 |
| SBUX | AVOID | DANGER | 12d | No | DANGER | AGREE | 0.317 | 1.23 | +0.69 | 1.167 | 1.023 |
| SPY | WATCHLIST | NORMAL | ETF | No | NORMAL | AGREE | 0.162 | 0.97 | +0.55 | 0.976 | 0.770 |
| TLT | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.112 | 0.96 | +0.78 | 1.017 | 0.931 |
| TSLA | AVOID | DANGER | 97d | No | CAUTION | STATE_MISMATCH | 0.521 | 1.19 | +2.53 | — | 0.892 |
| UBER | WATCHLIST | NORMAL | 13d | No | DANGER | STATE_MISMATCH | 0.423 | 1.09 | +1.58 | 1.136 | 0.946 |
| XLB | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.210 | 1.03 | -0.70 | 1.000 | 0.791 |
| XLE | NO EDGE | CAUTION | ETF | No | CAUTION | AGREE | 0.280 | 0.99 | +1.19 | 1.054 | 0.448 |
| XLF | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.184 | 0.86 | -0.21 | 0.972 | 0.877 |
| XLI | NO DATA | NORMAL | ETF | No | NORMAL | NODATA_SKEW | — | — | — | — | — |
| XLV | NO EDGE | NORMAL | ETF | No | CAUTION | STATE_MISMATCH | 0.183 | 1.10 | +0.55 | 1.160 | 1.072 |
| XOM | NO EDGE | CAUTION | 15d | No | DANGER | STATE_MISMATCH | 0.300 | 1.13 | +2.02 | 1.109 | 0.496 |

---

## 2026-07-22 (Wednesday)

**Shadow summary:** Checked 329 / 148 agree / 31 V2_STRICTER / 3 V2_LOOSER / 145 state_mismatch / 2 nodata | index-gating v1 98% vs v2 98% | oscillation v1 2.03 vs v2 0.70 | warm 100% | day-flips v1 5/33 vs v2 4/33

| Ticker | v1 Action | v1 Regime | Earnings | v2 Eligible | v2 Gate | Divergence | sigma_fwd | FVRP | z | 1M/3M | accel_dn |
|--------|-----------|-----------|----------|-------------|---------|------------|-----------|------|------|-------|----------|
| IWM | CONDITIONAL | NORMAL | ETF | No | NORMAL | V2_STRICTER | 0.223 | 0.88 | -0.89 | 0.966 | 0.658 |
| WMT | CONDITIONAL | NORMAL | 29d | No | DANGER | V2_STRICTER | 0.259 | 1.19 | +0.54 | 1.065 | 0.887 |
| AAPL | WATCHLIST | NORMAL | 8d | No | DANGER | STATE_MISMATCH | 0.306 | 0.98 | +0.64 | 1.044 | 0.835 |
| AMZN | CONDITIONAL | NORMAL | 8d | No | DANGER | STATE_MISMATCH | 0.344 | 1.24 | +1.24 | 1.140 | 0.746 |
| CAT | AVOID | DANGER | TBD | No | DANGER | AGREE | 0.436 | 1.25 | +1.26 | 1.102 | 0.946 |
| EEM | NO EDGE | CAUTION | ETF | No | CAUTION | AGREE | 0.301 | 1.15 | +0.46 | 0.991 | 0.871 |
| GLD | WATCHLIST | NORMAL | ETF | No | NORMAL | AGREE | 0.209 | 1.04 | -0.83 | 0.948 | 0.786 |
| GOOG | AVOID | DANGER | 0d | No | DANGER | AGREE | 0.340 | 1.15 | +0.63 | 1.112 | 1.188 |
| GS | NO EDGE | CAUTION | 83d | No | CAUTION | AGREE | 0.370 | 0.90 | -0.64 | 0.956 | 1.223 |
| HD | NO EDGE | NORMAL | TBD | No | DANGER | STATE_MISMATCH | 0.294 | 1.11 | +0.80 | 1.071 | 1.127 |
| HOOD | AVOID | DANGER | 7d | No | DANGER | AGREE | 0.816 | 0.99 | +0.88 | 1.078 | 1.172 |
| JNJ | NO EDGE | NORMAL | 83d | No | CAUTION | STATE_MISMATCH | 0.245 | 0.98 | -0.16 | 0.953 | 1.174 |
| JPM | NO EDGE | NORMAL | 83d | No | NORMAL | AGREE | 0.293 | 0.78 | -1.38 | 0.922 | 0.833 |
| KO | AVOID | DANGER | 6d | No | DANGER | AGREE | 0.233 | 0.96 | +0.17 | 1.063 | 1.425 |
| MCD | NO EDGE | NORMAL | TBD | No | DANGER | STATE_MISMATCH | 0.225 | 1.22 | +1.59 | 1.059 | 1.084 |
| META | AVOID | DANGER | 7d | No | DANGER | AGREE | 0.432 | 1.25 | +1.57 | 1.177 | 0.851 |
| MSFT | AVOID | DANGER | 7d | No | DANGER | AGREE | 0.314 | 1.45 | +1.94 | 1.174 | 0.746 |
| NFLX | NO EDGE | NORMAL | 90d | No | CAUTION | STATE_MISMATCH | 0.554 | 0.62 | -1.65 | 0.892 | 1.319 |
| NKE | NO EDGE | NORMAL | 69d | No | NORMAL | AGREE | 0.359 | 1.05 | -0.03 | 0.893 | 0.744 |
| NVDA | NO EDGE | CAUTION | 35d | No | NORMAL | STATE_MISMATCH | 0.488 | 0.77 | -1.34 | 0.900 | 0.876 |
| PLTR | CONDITIONAL | NORMAL | 12d | No | DANGER | STATE_MISMATCH | 0.626 | 1.09 | +1.65 | 1.133 | 0.602 |
| QQQ | WATCHLIST | NORMAL | ETF | No | CAUTION | STATE_MISMATCH | 0.261 | 0.94 | -0.29 | 0.991 | 0.906 |
| SBUX | AVOID | DANGER | 7d | No | DANGER | AGREE | 0.313 | 1.26 | +0.79 | 1.176 | 1.086 |
| SPY | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.173 | 0.82 | -0.96 | 0.915 | 0.822 |
| TLT | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.118 | 0.87 | -0.16 | 0.948 | 0.971 |
| TSLA | AVOID | DANGER | 0d | No | CAUTION | STATE_MISMATCH | 0.547 | 0.88 | -0.01 | 1.041 | 0.931 |
| UBER | NO EDGE | NORMAL | 14d | No | DANGER | STATE_MISMATCH | 0.444 | 1.05 | +1.30 | 1.134 | 0.909 |
| XLB | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.220 | 1.15 | -0.23 | — | 0.850 |
| XLE | NO EDGE | NORMAL | ETF | No | CAUTION | STATE_MISMATCH | 0.273 | 0.98 | +1.11 | 1.008 | 0.482 |
| XLF | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.196 | 0.83 | -0.54 | 0.959 | 0.939 |
| XLI | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.218 | 0.93 | -0.29 | 0.880 | 0.732 |
| XLV | NO EDGE | NORMAL | ETF | No | CAUTION | STATE_MISMATCH | 0.193 | 0.82 | -1.50 | 0.842 | 1.117 |
| XOM | AVOID | DANGER | 16d | No | DANGER | AGREE | 0.298 | 1.08 | +1.63 | 1.083 | 0.533 |

---

## 2026-07-21 (Tuesday)

**Shadow summary:** Checked 329 / 140 agree / 32 V2_STRICTER / 3 V2_LOOSER / 151 state_mismatch / 3 nodata | index-gating v1 99% vs v2 98% | oscillation v1 2.03 vs v2 0.64 | warm 100% | day-flips v1 11/33 vs v2 3/33

| Ticker | v1 Action | v1 Regime | Earnings | v2 Eligible | v2 Gate | Divergence | sigma_fwd | FVRP | z | 1M/3M | accel_dn |
|--------|-----------|-----------|----------|-------------|---------|------------|-----------|------|------|-------|----------|
| AMZN | CONDITIONAL | NORMAL | 9d | No | DANGER | V2_STRICTER | 0.372 | 1.15 | +0.88 | 1.147 | 0.741 |
| PLTR | CONDITIONAL | NORMAL | 13d | No | DANGER | V2_STRICTER | 0.661 | 1.04 | +1.31 | 1.135 | 0.568 |
| AAPL | WATCHLIST | NORMAL | 9d | No | DANGER | STATE_MISMATCH | 0.308 | 0.99 | +0.74 | 1.063 | 0.897 |
| CAT | AVOID | DANGER | TBD | No | DANGER | AGREE | 0.448 | 1.22 | +1.09 | 1.113 | 1.016 |
| EEM | NO EDGE | CAUTION | ETF | No | CAUTION | AGREE | 0.299 | 1.13 | +0.36 | 1.005 | 0.936 |
| GLD | WATCHLIST | NORMAL | ETF | No | NORMAL | AGREE | 0.203 | 1.12 | -0.26 | 0.958 | 0.845 |
| GOOG | AVOID | DANGER | 1d | No | DANGER | AGREE | 0.372 | 1.06 | +0.09 | 1.125 | 1.225 |
| GS | NO EDGE | CAUTION | 84d | No | CAUTION | AGREE | 0.387 | 0.88 | -0.89 | 0.972 | 1.314 |
| HD | NO EDGE | NORMAL | TBD | No | CAUTION | STATE_MISMATCH | 0.307 | 1.07 | +0.54 | 1.097 | 1.204 |
| HOOD | AVOID | DANGER | 8d | No | DANGER | AGREE | 0.832 | 0.96 | +0.60 | 1.102 | 1.259 |
| IWM | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.232 | 0.82 | -1.70 | 0.946 | 0.707 |
| JNJ | NO EDGE | CAUTION | 84d | No | CAUTION | AGREE | 0.251 | 1.00 | -0.02 | 0.971 | 1.261 |
| JPM | NO EDGE | NORMAL | 84d | No | NORMAL | AGREE | 0.304 | 0.76 | -1.57 | 0.920 | 0.895 |
| KO | AVOID | DANGER | 7d | No | DANGER | AGREE | 0.249 | 0.91 | -0.23 | 1.082 | 1.530 |
| MCD | NO EDGE | NORMAL | TBD | No | DANGER | STATE_MISMATCH | 0.240 | 1.17 | +1.31 | 1.080 | 1.057 |
| META | NO EDGE | CAUTION | 8d | No | DANGER | STATE_MISMATCH | 0.460 | 1.18 | +1.29 | 1.174 | 0.911 |
| MSFT | AVOID | DANGER | 8d | No | DANGER | AGREE | 0.332 | 1.38 | +1.71 | 1.190 | 0.730 |
| NFLX | NO EDGE | NORMAL | 91d | No | CAUTION | STATE_MISMATCH | 0.607 | 0.58 | -1.98 | 0.910 | 1.417 |
| NKE | NO EDGE | NORMAL | 70d | No | NORMAL | AGREE | 0.367 | 1.03 | -0.13 | 0.895 | 0.737 |
| NVDA | NO EDGE | NORMAL | 36d | No | NORMAL | AGREE | 0.499 | 0.78 | -1.22 | 0.915 | 0.941 |
| QQQ | WATCHLIST | NORMAL | ETF | No | CAUTION | STATE_MISMATCH | 0.266 | 0.93 | -0.40 | 0.986 | 0.973 |
| SBUX | AVOID | DANGER | 8d | No | DANGER | AGREE | 0.336 | 1.18 | +0.48 | 1.212 | 1.159 |
| SPY | WATCHLIST | NORMAL | ETF | No | NORMAL | AGREE | 0.180 | 0.81 | -1.05 | 0.930 | 0.883 |
| TLT | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.124 | 0.80 | -0.83 | 0.959 | 1.014 |
| TSLA | AVOID | DANGER | 1d | No | CAUTION | STATE_MISMATCH | 0.556 | 0.89 | +0.08 | 1.064 | 1.000 |
| UBER | NO EDGE | NORMAL | 15d | No | DANGER | STATE_MISMATCH | 0.466 | 1.02 | +1.16 | 1.156 | 0.950 |
| WMT | CONDITIONAL | NORMAL | 30d | Yes | NORMAL | AGREE | 0.270 | 1.16 | +0.41 | 1.072 | 0.908 |
| XLB | NO EDGE | NORMAL | ETF | No | CAUTION | STATE_MISMATCH | 0.219 | 0.90 | -1.35 | 0.886 | 0.913 |
| XLE | NO EDGE | CAUTION | ETF | No | NORMAL | STATE_MISMATCH | 0.289 | 0.94 | +0.75 | 1.021 | 0.517 |
| XLF | NO EDGE | CAUTION | ETF | No | NORMAL | STATE_MISMATCH | 0.200 | 0.89 | +0.05 | 1.013 | 1.008 |
| XLI | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.227 | 0.79 | -1.30 | 0.771 | 0.786 |
| XLV | NO EDGE | NORMAL | ETF | No | CAUTION | STATE_MISMATCH | 0.189 | 1.08 | +0.42 | 1.282 | 1.200 |
| XOM | AVOID | DANGER | 17d | No | DANGER | AGREE | 0.314 | 1.06 | +1.43 | 1.093 | 0.573 |

---

## 2026-07-20 (Monday)

**Shadow summary:** Checked 329 / 139 agree / 31 V2_STRICTER / 7 V2_LOOSER / 149 state_mismatch / 3 nodata | index-gating v1 99% vs v2 97% | oscillation v1 2.06 vs v2 1.00 | warm 100% | day-flips v1 8/33 vs v2 2/33

| Ticker | v1 Action | v1 Regime | Earnings | v2 Eligible | v2 Gate | Divergence | sigma_fwd | FVRP | z | 1M/3M | accel_dn |
|--------|-----------|-----------|----------|-------------|---------|------------|-----------|------|------|-------|----------|
| AMZN | SELL PREMIUM | NORMAL | 10d | No | DANGER | V2_STRICTER | 0.382 | 1.12 | +0.73 | 1.130 | 0.796 |
| MSFT | CONDITIONAL | NORMAL | 9d | No | DANGER | V2_STRICTER | 0.334 | 1.36 | +1.64 | 1.162 | 0.784 |
| PLTR | CONDITIONAL | NORMAL | 14d | No | DANGER | V2_STRICTER | 0.682 | 0.98 | +0.91 | 1.114 | 0.610 |
| WMT | CONDITIONAL | NORMAL | 31d | No | NORMAL | V2_STRICTER | 0.282 | 1.05 | -0.16 | 0.986 | 0.843 |
| AAPL | WATCHLIST | NORMAL | 10d | No | CAUTION | STATE_MISMATCH | 0.288 | 1.09 | +1.44 | 1.064 | 0.630 |
| CAT | NO EDGE | CAUTION | 15d | No | DANGER | STATE_MISMATCH | 0.463 | 1.20 | +1.01 | 1.112 | 1.054 |
| EEM | WATCHLIST | NORMAL | ETF | No | CAUTION | STATE_MISMATCH | 0.312 | 1.12 | +0.35 | 1.037 | 1.005 |
| GLD | WATCHLIST | NORMAL | ETF | No | NORMAL | AGREE | 0.213 | 1.10 | -0.38 | 0.973 | 0.905 |
| GOOG | AVOID | DANGER | 2d | No | DANGER | AGREE | 0.372 | 1.04 | -0.00 | 1.102 | 1.316 |
| GS | NO EDGE | CAUTION | 85d | No | CAUTION | AGREE | 0.393 | 0.89 | -0.80 | 0.995 | 1.397 |
| HD | NO EDGE | NORMAL | 29d | No | CAUTION | STATE_MISMATCH | 0.313 | 0.98 | -0.05 | 1.043 | 1.184 |
| HOOD | NO EDGE | CAUTION | 9d | No | DANGER | STATE_MISMATCH | 0.861 | 0.94 | +0.40 | 1.087 | 1.350 |
| IWM | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.237 | 0.86 | -1.18 | 0.979 | 0.675 |
| JNJ | NO EDGE | NORMAL | 85d | No | CAUTION | STATE_MISMATCH | 0.252 | 0.95 | -0.35 | 0.951 | 1.221 |
| JPM | NO EDGE | NORMAL | 85d | No | NORMAL | AGREE | 0.311 | 0.75 | -1.72 | 0.914 | 0.913 |
| KO | NO EDGE | CAUTION | 8d | No | DANGER | STATE_MISMATCH | 0.262 | 0.90 | -0.38 | 1.094 | 1.643 |
| MCD | WATCHLIST | NORMAL | 15d | No | DANGER | STATE_MISMATCH | 0.244 | 1.14 | +1.11 | 1.057 | 1.136 |
| META | WATCHLIST | NORMAL | 9d | No | DANGER | STATE_MISMATCH | 0.473 | 1.15 | +1.20 | 1.159 | 0.979 |
| NFLX | NO EDGE | NORMAL | 92d | No | DANGER | STATE_MISMATCH | 0.643 | 0.56 | -2.17 | 0.913 | 1.493 |
| NKE | NO EDGE | NORMAL | 71d | No | NORMAL | AGREE | 0.368 | 1.01 | -0.19 | 0.874 | 0.773 |
| NVDA | NO EDGE | NORMAL | 37d | No | NORMAL | AGREE | 0.506 | 0.82 | -0.86 | 0.943 | 1.011 |
| QQQ | WATCHLIST | NORMAL | ETF | No | CAUTION | STATE_MISMATCH | 0.271 | 0.96 | -0.02 | 1.023 | 1.045 |
| SBUX | NO EDGE | CAUTION | 9d | No | DANGER | STATE_MISMATCH | 0.319 | 1.22 | +0.63 | 1.177 | 1.225 |
| SPY | WATCHLIST | NORMAL | ETF | No | NORMAL | AGREE | 0.183 | 0.85 | -0.64 | 0.959 | 0.942 |
| TLT | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.123 | 0.77 | -1.25 | 0.922 | 0.847 |
| TSLA | AVOID | DANGER | 2d | No | CAUTION | STATE_MISMATCH | 0.551 | 0.89 | +0.06 | 1.048 | 0.952 |
| UBER | WATCHLIST | NORMAL | 16d | No | DANGER | STATE_MISMATCH | 0.469 | 0.99 | +0.98 | 1.156 | 1.015 |
| XLB | NO EDGE | NORMAL | ETF | No | CAUTION | STATE_MISMATCH | 0.219 | 0.99 | -0.92 | 1.000 | 0.868 |
| XLE | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.294 | 0.91 | +0.44 | 0.996 | 0.556 |
| XLF | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.207 | 0.85 | -0.35 | 0.925 | 1.045 |
| XLI | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.223 | 1.05 | +0.50 | 1.079 | 0.758 |
| XLV | NO EDGE | NORMAL | ETF | No | CAUTION | STATE_MISMATCH | 0.194 | 0.85 | -1.22 | 1.005 | 1.136 |
| XOM | NO EDGE | CAUTION | 11d | No | CAUTION | AGREE | 0.321 | 1.02 | +1.12 | 1.080 | 0.615 |

---

## 2026-07-17 (Friday)

**Shadow summary:** Checked 329 / 142 agree / 28 V2_STRICTER / 8 V2_LOOSER / 148 state_mismatch / 3 nodata | index-gating v1 99% vs v2 97% | oscillation v1 2.00 vs v2 1.21 | warm 90% | day-flips v1 10/33 vs v2 2/33

| Ticker | v1 Action | v1 Regime | Earnings | v2 Eligible | v2 Gate | Divergence | sigma_fwd | FVRP | z | 1M/3M | accel_dn |
|--------|-----------|-----------|----------|-------------|---------|------------|-----------|------|------|-------|----------|
| AMZN | CONDITIONAL | NORMAL | 13d | No | DANGER | V2_STRICTER | 0.367 | 1.18 | +1.02 | 1.145 | 0.793 |
| PLTR | CONDITIONAL | NORMAL | 17d | No | DANGER | V2_STRICTER | 0.691 | 0.96 | +0.79 | 1.125 | 0.591 |
| SBUX | SELL PREMIUM | NORMAL | 18d | No | DANGER | V2_STRICTER | 0.306 | 1.29 | +0.89 | 1.214 | 0.811 |
| UBER | CONDITIONAL | NORMAL | 19d | No | DANGER | V2_STRICTER | 0.483 | 0.97 | +0.85 | 1.162 | 0.941 |
| WMT | CONDITIONAL | NORMAL | 34d | No | NORMAL | V2_STRICTER | 0.291 | 0.92 | -0.92 | 0.958 | 0.711 |
| AAPL | WATCHLIST | NORMAL | 13d | No | CAUTION | STATE_MISMATCH | 0.294 | 1.00 | +0.81 | 1.042 | 0.676 |
| CAT | NO EDGE | CAUTION | TBD | No | DANGER | STATE_MISMATCH | 0.431 | 1.22 | +1.13 | 1.096 | 1.132 |
| EEM | NO EDGE | CAUTION | ETF | No | CAUTION | AGREE | 0.281 | 1.26 | +0.91 | 0.950 | 1.030 |
| GLD | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.226 | 1.07 | -0.59 | 0.988 | 0.972 |
| GOOG | AVOID | DANGER | 5d | No | DANGER | AGREE | 0.369 | 1.08 | +0.23 | 1.119 | 1.322 |
| GS | NO EDGE | CAUTION | 88d | No | CAUTION | AGREE | 0.382 | 0.89 | -0.79 | 0.955 | 1.384 |
| HD | NO EDGE | NORMAL | TBD | No | CAUTION | STATE_MISMATCH | 0.288 | 1.00 | +0.09 | 0.987 | 0.927 |
| HOOD | NO EDGE | NORMAL | 12d | No | DANGER | STATE_MISMATCH | 0.756 | 1.04 | +1.37 | 1.086 | 1.287 |
| IWM | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.216 | 0.90 | -0.71 | 0.954 | 0.656 |
| JNJ | NO EDGE | CAUTION | 88d | No | CAUTION | AGREE | 0.264 | 0.88 | -0.81 | 0.925 | 1.312 |
| JPM | NO EDGE | NORMAL | 88d | No | NORMAL | AGREE | 0.297 | 0.78 | -1.40 | 0.928 | 0.943 |
| KO | NO EDGE | CAUTION | 11d | No | DANGER | STATE_MISMATCH | 0.220 | 1.07 | +0.96 | 1.105 | 0.992 |
| MCD | NO EDGE | CAUTION | TBD | No | DANGER | STATE_MISMATCH | 0.233 | 1.18 | +1.35 | 1.083 | 0.962 |
| META | NO EDGE | NORMAL | 12d | No | DANGER | STATE_MISMATCH | 0.437 | 1.25 | +1.57 | 1.168 | 0.875 |
| MSFT | NO EDGE | CAUTION | 12d | No | DANGER | STATE_MISMATCH | 0.333 | 1.37 | +1.69 | 1.178 | 0.657 |
| NFLX | AVOID | DANGER | 95d | No | DANGER | AGREE | 0.397 | 1.55 | +2.53 | 1.259 | 0.747 |
| NKE | NO EDGE | NORMAL | 74d | No | NORMAL | AGREE | 0.362 | 1.01 | -0.21 | 0.880 | 0.682 |
| NVDA | NO EDGE | NORMAL | 40d | No | NORMAL | AGREE | 0.469 | 0.87 | -0.35 | 0.943 | 0.960 |
| QQQ | WATCHLIST | NORMAL | ETF | No | NORMAL | AGREE | 0.243 | 1.07 | +1.07 | 1.024 | 1.002 |
| SPY | WATCHLIST | NORMAL | ETF | No | NORMAL | AGREE | 0.160 | 0.93 | +0.18 | 0.953 | 0.735 |
| TLT | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.120 | 0.74 | -1.60 | 0.875 | 0.909 |
| TSLA | AVOID | DANGER | 5d | No | CAUTION | STATE_MISMATCH | 0.529 | 0.94 | +0.54 | 1.056 | 0.920 |
| XLB | NO DATA | NORMAL | ETF | No | CAUTION | NODATA_SKEW | — | — | — | — | — |
| XLE | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.275 | 0.90 | +0.38 | 0.979 | 0.597 |
| XLF | NO EDGE | NORMAL | ETF | No | CAUTION | STATE_MISMATCH | 0.198 | 0.83 | -0.59 | 0.961 | 0.918 |
| XLI | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.207 | 0.97 | -0.04 | 1.000 | 0.787 |
| XLV | NO EDGE | CAUTION | ETF | No | CAUTION | AGREE | 0.195 | 0.88 | -1.03 | 1.123 | 1.197 |
| XOM | NO EDGE | CAUTION | 21d | No | CAUTION | AGREE | 0.296 | 0.97 | +0.60 | 0.993 | 0.661 |

---

## 2026-07-16 (Thursday)

**Shadow summary:** Checked 296 / 125 agree / 23 V2_STRICTER / 8 V2_LOOSER / 138 state_mismatch / 2 nodata | index-gating v1 99% vs v2 97% | oscillation v1 1.70 vs v2 1.15 | warm 89% | day-flips v1 7/32 vs v2 1/32

| Ticker | v1 Action | v1 Regime | Earnings | v2 Eligible | v2 Gate | Divergence | sigma_fwd | FVRP | z | 1M/3M | accel_dn |
|--------|-----------|-----------|----------|-------------|---------|------------|-----------|------|------|-------|----------|
| AMZN | CONDITIONAL | NORMAL | 14d | No | DANGER | V2_STRICTER | 0.340 | 1.30 | +1.47 | 1.156 | 0.587 |
| MSFT | CONDITIONAL | NORMAL | 13d | No | DANGER | V2_STRICTER | 0.329 | 1.41 | +1.85 | 1.185 | 0.706 |
| PLTR | CONDITIONAL | NORMAL | 18d | No | DANGER | V2_STRICTER | 0.699 | 0.93 | +0.60 | 1.107 | 0.635 |
| SBUX | SELL PREMIUM | NORMAL | 13d | No | DANGER | V2_STRICTER | 0.303 | 1.22 | +0.62 | 1.203 | 0.871 |
| AAPL | WATCHLIST | NORMAL | 14d | No | CAUTION | STATE_MISMATCH | 0.303 | 0.92 | +0.16 | 1.035 | 0.726 |
| CAT | WATCHLIST | NORMAL | 19d | No | DANGER | STATE_MISMATCH | 0.424 | 1.23 | +1.17 | 1.087 | 0.992 |
| EEM | WATCHLIST | NORMAL | ETF | No | CAUTION | STATE_MISMATCH | 0.276 | 1.30 | +1.04 | 1.027 | 0.991 |
| GLD | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.223 | 1.07 | -0.61 | 0.996 | 0.854 |
| GOOG | AVOID | DANGER | 6d | No | DANGER | AGREE | 0.326 | 1.23 | +1.05 | 1.131 | 0.704 |
| GS | NO EDGE | CAUTION | 89d | No | CAUTION | AGREE | 0.369 | 0.91 | -0.55 | 0.987 | 0.694 |
| HD | NO EDGE | NORMAL | 33d | No | CAUTION | STATE_MISMATCH | 0.287 | 0.95 | -0.28 | 0.948 | 0.996 |
| HOOD | NO EDGE | CAUTION | 13d | No | DANGER | STATE_MISMATCH | 0.720 | 1.11 | +1.91 | 1.115 | 0.696 |
| IWM | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.214 | 0.86 | -1.21 | 0.917 | 0.703 |
| JNJ | NO EDGE | CAUTION | 89d | No | DANGER | STATE_MISMATCH | 0.270 | 0.93 | -0.52 | 1.007 | 1.409 |
| JPM | NO EDGE | NORMAL | 89d | No | NORMAL | AGREE | 0.309 | 0.72 | -2.10 | 0.918 | 0.885 |
| KO | NO EDGE | NORMAL | 12d | No | DANGER | STATE_MISMATCH | 0.206 | 1.04 | +0.75 | 1.053 | 1.066 |
| MCD | NO EDGE | NORMAL | 19d | No | DANGER | STATE_MISMATCH | 0.234 | 1.12 | +0.99 | 1.038 | 1.033 |
| META | NO EDGE | CAUTION | 13d | No | DANGER | STATE_MISMATCH | 0.449 | 1.25 | +1.56 | 1.169 | 0.772 |
| NFLX | AVOID | DANGER | 0d | No | DANGER | AGREE | 0.407 | 1.24 | +1.51 | 1.149 | 0.802 |
| NKE | NO EDGE | NORMAL | 75d | No | NORMAL | AGREE | 0.375 | 0.91 | -0.63 | 0.848 | 0.733 |
| NVDA | NO EDGE | NORMAL | 41d | No | NORMAL | AGREE | 0.485 | 0.84 | -0.65 | 0.938 | 0.859 |
| QQQ | WATCHLIST | NORMAL | ETF | No | NORMAL | AGREE | 0.244 | 1.00 | +0.39 | 0.989 | 0.910 |
| SPY | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.157 | 0.87 | -0.44 | 0.893 | 0.682 |
| TLT | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.113 | 0.82 | -0.71 | 0.907 | 0.976 |
| TSLA | NO EDGE | CAUTION | 6d | No | CAUTION | AGREE | 0.546 | 0.90 | +0.21 | 1.042 | 0.977 |
| UBER | WATCHLIST | NORMAL | 20d | No | DANGER | STATE_MISMATCH | 0.464 | 1.02 | +1.10 | 1.146 | 1.011 |
| WMT | NO EDGE | NORMAL | 35d | No | NORMAL | AGREE | 0.263 | 0.98 | -0.57 | 0.933 | 0.738 |
| XLB | NO EDGE | NORMAL | ETF | No | CAUTION | STATE_MISMATCH | 0.218 | 1.06 | -0.60 | 1.009 | 0.938 |
| XLE | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.291 | 0.89 | +0.26 | 1.018 | 0.641 |
| XLF | NO EDGE | CAUTION | ETF | No | CAUTION | AGREE | 0.208 | 0.77 | -1.17 | 1.063 | 0.986 |
| XLI | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.213 | 1.14 | +1.00 | 1.110 | 0.845 |
| XLV | NO EDGE | NORMAL | ETF | No | CAUTION | STATE_MISMATCH | 0.184 | 0.73 | -2.34 | 0.627 | 1.286 |
| XOM | NO EDGE | CAUTION | 15d | No | DANGER | STATE_MISMATCH | 0.306 | 0.95 | +0.48 | 1.018 | 0.710 |

---

## 2026-07-15 (Wednesday)

**Shadow summary:** Checked 263 / 109 agree / 19 V2_STRICTER / 8 V2_LOOSER / 125 state_mismatch / 2 nodata | index-gating v1 99% vs v2 97% | oscillation v1 1.48 vs v2 1.12 | warm 87% | day-flips v1 8/32 vs v2 2/32

| Ticker | v1 Action | v1 Regime | Earnings | v2 Eligible | v2 Gate | Divergence | sigma_fwd | FVRP | z | 1M/3M | accel_dn |
|--------|-----------|-----------|----------|-------------|---------|------------|-----------|------|------|-------|----------|
| AMZN | SELL PREMIUM | NORMAL | 15d | No | DANGER | V2_STRICTER | 0.339 | 1.28 | +1.40 | 1.136 | 0.631 |
| MSFT | CONDITIONAL | NORMAL | 14d | No | DANGER | V2_STRICTER | 0.335 | 1.36 | +1.70 | 1.180 | 0.758 |
| PLTR | CONDITIONAL | NORMAL | 19d | No | DANGER | V2_STRICTER | 0.748 | 0.90 | +0.36 | 1.134 | 0.682 |
| AAPL | WATCHLIST | NORMAL | 15d | No | CAUTION | STATE_MISMATCH | 0.296 | 0.92 | +0.14 | 1.030 | 0.780 |
| CAT | WATCHLIST | NORMAL | 20d | No | DANGER | STATE_MISMATCH | 0.418 | 1.24 | +1.25 | 1.059 | 1.000 |
| EEM | NO EDGE | CAUTION | ETF | No | CAUTION | AGREE | 0.283 | 1.17 | +0.57 | 1.001 | 1.064 |
| GLD | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.236 | 0.98 | -1.26 | 0.967 | 0.917 |
| GOOG | AVOID | DANGER | 7d | No | DANGER | AGREE | 0.303 | 1.30 | +1.40 | 1.133 | 0.757 |
| GS | NO EDGE | CAUTION | 90d | No | CAUTION | AGREE | 0.382 | 0.88 | -0.94 | 0.984 | 0.746 |
| HD | NO EDGE | NORMAL | 34d | No | CAUTION | STATE_MISMATCH | 0.277 | 0.99 | +0.01 | 0.947 | 1.070 |
| HOOD | NO EDGE | NORMAL | 14d | No | DANGER | STATE_MISMATCH | 0.733 | 1.01 | +1.02 | 1.024 | 0.748 |
| IWM | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.218 | 0.87 | -1.12 | 0.931 | 0.756 |
| JNJ | AVOID | DANGER | 0d | No | DANGER | AGREE | 0.227 | 1.20 | +1.11 | 1.048 | 1.171 |
| JPM | NO EDGE | NORMAL | 90d | No | NORMAL | AGREE | 0.322 | 0.75 | -1.72 | 0.977 | 0.951 |
| KO | NO EDGE | NORMAL | 13d | No | DANGER | STATE_MISMATCH | 0.212 | 1.08 | +0.98 | 1.075 | 1.081 |
| MCD | NO EDGE | NORMAL | 20d | No | DANGER | STATE_MISMATCH | 0.226 | 1.22 | +1.61 | 1.094 | 0.966 |
| META | NO EDGE | CAUTION | 14d | No | DANGER | STATE_MISMATCH | 0.453 | 1.19 | +1.37 | 1.158 | 0.829 |
| NFLX | AVOID | DANGER | 1d | No | DANGER | AGREE | 0.413 | 1.19 | +1.32 | 1.117 | 0.862 |
| NKE | NO EDGE | NORMAL | 76d | No | NORMAL | AGREE | 0.387 | 0.92 | -0.56 | 0.899 | 0.785 |
| NVDA | NO EDGE | NORMAL | 42d | No | NORMAL | AGREE | 0.492 | 0.82 | -0.82 | 0.934 | 0.923 |
| QQQ | WATCHLIST | NORMAL | ETF | No | NORMAL | AGREE | 0.242 | 0.99 | +0.24 | 0.977 | 0.973 |
| SBUX | AVOID | DANGER | 14d | No | DANGER | AGREE | 0.296 | 1.35 | +1.14 | 1.258 | 0.833 |
| SPY | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.156 | 0.86 | -0.50 | 0.895 | 0.732 |
| TLT | NO EDGE | NORMAL | ETF | No | CAUTION | STATE_MISMATCH | 0.119 | 0.84 | -0.51 | 0.942 | 1.049 |
| TSLA | NO EDGE | NORMAL | 7d | No | CAUTION | STATE_MISMATCH | 0.516 | 0.93 | +0.47 | 1.032 | 1.047 |
| UBER | NO EDGE | NORMAL | 21d | No | DANGER | STATE_MISMATCH | 0.479 | 0.90 | +0.32 | 1.059 | 1.086 |
| WMT | NO EDGE | CAUTION | 36d | No | NORMAL | STATE_MISMATCH | 0.264 | 0.95 | -0.77 | 0.913 | 0.793 |
| XLE | NO EDGE | CAUTION | ETF | No | NORMAL | STATE_MISMATCH | 0.287 | 0.89 | +0.27 | 0.995 | 0.611 |
| XLF | NO EDGE | CAUTION | ETF | No | CAUTION | AGREE | 0.219 | 0.73 | -1.71 | 0.957 | 1.059 |
| XLI | NO EDGE | NORMAL | ETF | No | NORMAL | AGREE | 0.209 | 0.91 | -0.40 | 0.820 | 0.902 |
| XLV | NO EDGE | NORMAL | ETF | No | CAUTION | STATE_MISMATCH | 0.186 | 0.94 | -0.59 | 1.060 | 1.381 |
| XOM | NO EDGE | CAUTION | 16d | No | DANGER | STATE_MISMATCH | 0.308 | 0.96 | +0.53 | 1.035 | 0.751 |

---

## 2026-07-14 (Tuesday)

**Shadow summary:** Checked 231 / 94 agree / 16 V2_STRICTER / 8 V2_LOOSER / 111 state_mismatch / 2 nodata | index-gating v1 99% vs v2 96% | oscillation v1 1.24 vs v2 1.06 | warm 86%

| Ticker | v1 Action | v1 Regime | v2 Eligible | v2 Gate | Divergence | sigma_fwd | FVRP | z | 1M/3M | accel_dn |
|--------|-----------|-----------|-------------|---------|------------|-----------|------|------|-------|----------|
| AMZN | SELL PREMIUM | NORMAL | No | DANGER | V2_STRICTER | 0.350 | 1.26 | +1.35 | 1.150 | 0.678 |
| SBUX | SELL PREMIUM | NORMAL | No | DANGER | V2_STRICTER | 0.304 | 1.31 | +0.99 | 1.229 | 0.759 |
| EEM | AVOID | DANGER | Yes | NORMAL | V2_LOOSER | 0.292 | 1.20 | +0.69 | 1.007 | 1.143 |
| AAPL | WATCHLIST | NORMAL | No | CAUTION | STATE_MISMATCH | 0.302 | 0.95 | +0.39 | 1.044 | 0.800 |
| CAT | NO EDGE | NORMAL | No | DANGER | STATE_MISMATCH | 0.396 | 1.30 | +1.55 | 1.083 | 1.074 |
| GLD | NO EDGE | NORMAL | No | NORMAL | AGREE | 0.222 | 1.11 | -0.30 | 1.009 | 0.985 |
| GOOG | AVOID | DANGER | No | DANGER | AGREE | 0.314 | 1.24 | +1.13 | 1.120 | 0.813 |
| GS | NO EDGE | NORMAL | No | CAUTION | STATE_MISMATCH | 0.325 | 1.07 | +0.86 | — | 0.801 |
| HD | NO EDGE | CAUTION | No | CAUTION | AGREE | 0.286 | 1.01 | +0.13 | 0.999 | 1.149 |
| HOOD | NO EDGE | NORMAL | No | DANGER | STATE_MISMATCH | 0.772 | 1.00 | +1.00 | 1.086 | 0.803 |
| IWM | NO EDGE | NORMAL | No | NORMAL | AGREE | 0.222 | 0.92 | -0.42 | 0.983 | 0.812 |
| JNJ | AVOID | DANGER | No | DANGER | AGREE | 0.225 | 1.23 | +1.31 | 1.036 | 1.091 |
| JPM | AVOID | DANGER | No | CAUTION | STATE_MISMATCH | 0.262 | 0.94 | +0.19 | 0.968 | 1.022 |
| KO | WATCHLIST | NORMAL | No | DANGER | STATE_MISMATCH | 0.215 | 1.08 | +1.02 | 1.048 | 0.908 |
| MCD | NO EDGE | NORMAL | No | DANGER | STATE_MISMATCH | 0.227 | 1.18 | +1.34 | 1.043 | 0.903 |
| META | NO EDGE | CAUTION | No | DANGER | STATE_MISMATCH | 0.486 | 1.14 | +1.18 | 1.180 | 0.891 |
| MSFT | WATCHLIST | NORMAL | No | DANGER | STATE_MISMATCH | 0.320 | 1.40 | +1.85 | 1.160 | 0.688 |
| NFLX | AVOID | DANGER | No | DANGER | AGREE | 0.413 | 1.22 | +1.43 | 1.157 | 0.921 |
| NKE | NO EDGE | NORMAL | No | NORMAL | AGREE | 0.368 | 0.99 | -0.25 | 0.910 | 0.664 |
| NVDA | NO EDGE | NORMAL | No | NORMAL | AGREE | 0.460 | 0.86 | -0.44 | 0.924 | 0.991 |
| PLTR | WATCHLIST | NORMAL | No | DANGER | STATE_MISMATCH | 0.651 | 1.00 | +1.06 | 1.123 | 0.733 |
| QQQ | WATCHLIST | NORMAL | No | NORMAL | AGREE | 0.239 | 1.00 | +0.40 | 0.982 | 1.045 |
| SPY | NO EDGE | NORMAL | No | NORMAL | AGREE | 0.161 | 0.87 | -0.44 | 0.908 | 0.787 |
| TLT | NO EDGE | NORMAL | No | CAUTION | STATE_MISMATCH | 0.118 | 0.90 | +0.15 | 0.968 | 1.126 |
| TSLA | NO EDGE | CAUTION | No | CAUTION | AGREE | 0.537 | 0.90 | +0.19 | 1.030 | 1.125 |
| UBER | WATCHLIST | NORMAL | No | DANGER | STATE_MISMATCH | 0.460 | 1.04 | +1.21 | 1.179 | 0.890 |
| WMT | NO EDGE | CAUTION | No | NORMAL | STATE_MISMATCH | 0.254 | 1.01 | -0.38 | 0.947 | 0.793 |
| XLB | NO EDGE | NORMAL | No | CAUTION | STATE_MISMATCH | 0.218 | 1.03 | -0.74 | 1.000 | 1.075 |
| XLE | AVOID | DANGER | No | NORMAL | STATE_MISMATCH | 0.297 | 0.94 | +0.75 | 1.080 | 0.657 |
| XLF | NO EDGE | CAUTION | No | CAUTION | AGREE | 0.202 | 0.89 | +0.10 | 1.060 | 1.138 |
| XLI | NO EDGE | NORMAL | No | NORMAL | AGREE | 0.206 | 1.03 | +0.34 | 0.855 | 0.969 |
| XLV | NO EDGE | NORMAL | No | CAUTION | STATE_MISMATCH | 0.174 | 1.05 | +0.21 | 0.837 | 1.060 |
| XOM | AVOID | DANGER | No | DANGER | AGREE | 0.325 | 0.99 | +0.80 | 1.092 | 0.807 |

---

## 2026-07-13 (Monday)

**Shadow summary:** Checked 198 / 80 agree / 14 V2_STRICTER / 7 V2_LOOSER / 95 state_mismatch / 2 nodata | index-gating v1 98% vs v2 97% | oscillation v1 1.00 vs v2 1.00 | warm 83%

| Ticker | v1 Action | v1 Regime | v2 Eligible | v2 Gate | Divergence | sigma_fwd | FVRP | z | 1M/3M | accel_dn |
|--------|-----------|-----------|-------------|---------|------------|-----------|------|------|-------|----------|
| AMZN | CONDITIONAL | NORMAL | No | DANGER | V2_STRICTER | 0.366 | 1.16 | +0.93 | 1.112 | 0.728 |
| SBUX | SELL PREMIUM | NORMAL | No | DANGER | V2_STRICTER | 0.316 | 1.16 | +0.40 | 1.146 | 0.816 |
| EEM | NO EDGE | NORMAL | Yes | NORMAL | V2_LOOSER | 0.254 | 1.27 | +0.96 | 0.910 | 0.897 |
| AAPL | WATCHLIST | NORMAL | No | CAUTION | STATE_MISMATCH | 0.297 | 0.91 | +0.06 | 1.014 | 0.859 |
| CAT | WATCHLIST | NORMAL | No | DANGER | STATE_MISMATCH | 0.410 | 1.22 | +1.14 | 1.066 | 1.091 |
| GLD | WATCHLIST | NORMAL | No | NORMAL | AGREE | 0.213 | 1.06 | -0.65 | 0.997 | 0.683 |
| GOOG | NO EDGE | NORMAL | No | DANGER | STATE_MISMATCH | 0.331 | 1.15 | +0.64 | 1.085 | 0.784 |
| GS | AVOID | DANGER | No | CAUTION | STATE_MISMATCH | 0.342 | 1.03 | +0.53 | 0.999 | 0.817 |
| HD | NO EDGE | NORMAL | No | CAUTION | STATE_MISMATCH | 0.286 | 0.97 | -0.13 | 0.948 | 1.087 |
| HOOD | WATCHLIST | NORMAL | No | DANGER | STATE_MISMATCH | 0.818 | 0.88 | -0.24 | 1.016 | 0.811 |
| IWM | NO EDGE | NORMAL | No | NORMAL | AGREE | 0.230 | 0.84 | -1.44 | 0.947 | 0.739 |
| JNJ | AVOID | DANGER | No | DANGER | AGREE | 0.238 | 1.08 | +0.45 | 1.006 | 1.172 |
| JPM | AVOID | DANGER | No | CAUTION | STATE_MISMATCH | 0.260 | 0.98 | +0.53 | 0.993 | 1.070 |
| KO | NO EDGE | CAUTION | No | DANGER | STATE_MISMATCH | 0.226 | 0.94 | -0.06 | 1.056 | 0.975 |
| MCD | NO EDGE | NORMAL | No | DANGER | STATE_MISMATCH | 0.237 | 1.08 | +0.72 | 1.032 | 0.929 |
| META | NO EDGE | CAUTION | No | DANGER | STATE_MISMATCH | 0.514 | 1.08 | +0.91 | 1.162 | 0.875 |
| MSFT | WATCHLIST | NORMAL | No | DANGER | STATE_MISMATCH | 0.331 | 1.30 | +1.49 | 1.125 | 0.739 |
| NFLX | AVOID | DANGER | No | DANGER | AGREE | 0.429 | 1.10 | +0.94 | 1.084 | 0.989 |
| NKE | NO EDGE | NORMAL | No | NORMAL | AGREE | 0.385 | 0.93 | -0.50 | 0.911 | 0.621 |
| NVDA | NO EDGE | NORMAL | No | NORMAL | AGREE | 0.440 | 0.89 | -0.10 | 0.919 | 0.630 |
| PLTR | WATCHLIST | NORMAL | No | DANGER | STATE_MISMATCH | 0.693 | 0.89 | +0.33 | 1.101 | 0.787 |
| QQQ | WATCHLIST | NORMAL | No | NORMAL | AGREE | 0.235 | 1.01 | +0.50 | 0.961 | 0.914 |
| SPY | NO EDGE | NORMAL | No | NORMAL | AGREE | 0.163 | 0.83 | -0.82 | 0.896 | 0.647 |
| TLT | NO EDGE | NORMAL | No | CAUTION | STATE_MISMATCH | 0.115 | 0.82 | -0.70 | 0.920 | 1.106 |
| TSLA | NO EDGE | CAUTION | No | CAUTION | AGREE | 0.543 | 0.87 | -0.09 | 1.013 | 1.101 |
| UBER | NO EDGE | NORMAL | No | DANGER | STATE_MISMATCH | 0.455 | 0.97 | +0.78 | 1.112 | 0.951 |
| WMT | NO EDGE | CAUTION | No | NORMAL | STATE_MISMATCH | 0.258 | 0.89 | -1.13 | 0.865 | 0.804 |
| XLB | NO EDGE | NORMAL | No | CAUTION | STATE_MISMATCH | 0.212 | 0.89 | -1.41 | 0.895 | 1.128 |
| XLE | NO EDGE | NORMAL | No | NORMAL | AGREE | 0.289 | 0.76 | -1.18 | 0.906 | 0.705 |
| XLF | NO EDGE | CAUTION | No | CAUTION | AGREE | 0.208 | 0.81 | -0.76 | 1.038 | 1.222 |
| XLI | NO EDGE | NORMAL | No | CAUTION | STATE_MISMATCH | 0.214 | 0.93 | -0.25 | 0.956 | 0.965 |
| XLV | NO EDGE | CAUTION | No | CAUTION | AGREE | 0.180 | 0.97 | -0.31 | 0.837 | 1.139 |
| XOM | NO EDGE | NORMAL | No | NORMAL | AGREE | 0.305 | 1.03 | +1.26 | 1.133 | 0.867 |

---

## 2026-07-10 (Friday)

**Shadow summary:** Checked 165 / 67 agree / 12 V2_STRICTER / 6 V2_LOOSER / 78 state_mismatch / 2 nodata | index-gating v1 98% vs v2 98% | oscillation v1 0.88 vs v2 0.91 | warm 80%

| Ticker | v1 Action | v1 Regime | v2 Eligible | v2 Gate | Divergence | sigma_fwd | FVRP | z | 1M/3M | accel_dn |
|--------|-----------|-----------|-------------|---------|------------|-----------|------|------|-------|----------|
| AMZN | CONDITIONAL | NORMAL | No | DANGER | V2_STRICTER | 0.374 | 1.18 | +1.00 | 1.146 | 0.756 |
| GOOG | CONDITIONAL | NORMAL | No | DANGER | V2_STRICTER | 0.353 | 1.11 | +0.42 | 1.121 | 0.835 |
| SBUX | SELL PREMIUM | NORMAL | No | DANGER | V2_STRICTER | 0.333 | 1.15 | +0.35 | 1.191 | 0.862 |
| XLE | CONDITIONAL | NORMAL | No | NORMAL | V2_STRICTER | 0.296 | 1.02 | +1.54 | 1.304 | 0.758 |
| AAPL | NO EDGE | CAUTION | No | CAUTION | AGREE | 0.310 | 0.90 | -0.03 | 1.032 | 0.919 |
| CAT | NO EDGE | CAUTION | No | DANGER | STATE_MISMATCH | 0.435 | 1.15 | +0.76 | 1.073 | 1.172 |
| EEM | NO EDGE | NORMAL | No | CAUTION | STATE_MISMATCH | 0.268 | 1.64 | +2.17 | — | 0.964 |
| GLD | NO EDGE | NORMAL | No | NORMAL | AGREE | 0.220 | 1.05 | -0.73 | 0.999 | 0.727 |
| GS | AVOID | DANGER | No | CAUTION | STATE_MISMATCH | 0.362 | 1.02 | +0.45 | 1.049 | 0.877 |
| HD | NO EDGE | NORMAL | No | CAUTION | STATE_MISMATCH | 0.300 | 0.88 | -0.78 | 0.926 | 1.168 |
| HOOD | WATCHLIST | NORMAL | No | DANGER | STATE_MISMATCH | 0.748 | 1.00 | +0.99 | 1.042 | 0.757 |
| IWM | NO EDGE | NORMAL | No | NORMAL | AGREE | 0.230 | 0.86 | -1.22 | 0.941 | 0.761 |
| JNJ | AVOID | DANGER | No | DANGER | AGREE | 0.243 | 1.11 | +0.67 | 1.061 | 1.216 |
| JPM | AVOID | DANGER | No | CAUTION | STATE_MISMATCH | 0.272 | 1.00 | +0.70 | 1.051 | 1.150 |
| KO | NO EDGE | NORMAL | No | DANGER | STATE_MISMATCH | 0.240 | 0.91 | -0.30 | 1.035 | 1.048 |
| MCD | NO EDGE | CAUTION | No | DANGER | STATE_MISMATCH | 0.239 | 1.08 | +0.77 | 1.044 | 0.965 |
| META | NO EDGE | CAUTION | No | DANGER | STATE_MISMATCH | 0.506 | 1.08 | +0.90 | 1.201 | 0.940 |
| MSFT | WATCHLIST | NORMAL | No | DANGER | STATE_MISMATCH | 0.336 | 1.28 | +1.40 | 1.141 | 0.794 |
| NFLX | AVOID | DANGER | No | DANGER | AGREE | 0.415 | 1.17 | +1.23 | 1.127 | 0.848 |
| NKE | NO EDGE | NORMAL | No | NORMAL | AGREE | 0.376 | 0.92 | -0.56 | 0.900 | 0.667 |
| NVDA | NO EDGE | NORMAL | No | NORMAL | AGREE | 0.457 | 0.86 | -0.37 | 0.932 | 0.676 |
| PLTR | WATCHLIST | NORMAL | No | DANGER | STATE_MISMATCH | 0.711 | 0.90 | +0.36 | 1.114 | 0.796 |
| QQQ | WATCHLIST | NORMAL | No | CAUTION | STATE_MISMATCH | 0.245 | 0.97 | +0.10 | 0.966 | 0.982 |
| SPY | NO EDGE | NORMAL | No | NORMAL | AGREE | 0.165 | 0.78 | -1.37 | 0.874 | 0.696 |
| TLT | NO EDGE | NORMAL | No | CAUTION | STATE_MISMATCH | 0.120 | 0.81 | -0.81 | 0.946 | 1.188 |
| TSLA | NO EDGE | CAUTION | No | CAUTION | AGREE | 0.558 | 0.86 | -0.22 | 1.024 | 1.183 |
| UBER | NO EDGE | NORMAL | No | DANGER | STATE_MISMATCH | 0.465 | 0.96 | +0.73 | 1.099 | 1.021 |
| WMT | NO EDGE | CAUTION | No | NORMAL | STATE_MISMATCH | 0.268 | 0.92 | -0.95 | 0.894 | 0.863 |
| XLB | NO DATA | NORMAL | No | CAUTION | NODATA_SKEW | — | — | — | — | — |
| XLF | NO EDGE | CAUTION | No | CAUTION | AGREE | 0.198 | 0.86 | -0.21 | 1.048 | 1.313 |
| XLI | NO EDGE | NORMAL | No | CAUTION | STATE_MISMATCH | 0.224 | 1.06 | +0.58 | 0.993 | 1.036 |
| XLV | NO EDGE | CAUTION | No | CAUTION | AGREE | 0.184 | 0.98 | -0.30 | 0.922 | 1.122 |
| XOM | NO EDGE | NORMAL | No | NORMAL | AGREE | 0.325 | 0.85 | -0.58 | 0.996 | 0.931 |

---

## 2026-07-09 (Thursday)

**Shadow summary:** Checked 132 / 55 agree / 8 V2_STRICTER / 6 V2_LOOSER / 62 state_mismatch / 1 nodata | index-gating v1 100% vs v2 98% | oscillation v1 0.70 vs v2 0.79 | warm 75%

| Ticker | v1 Action | v1 Regime | v2 Eligible | v2 Gate | Divergence | sigma_fwd | FVRP | z | 1M/3M | accel_dn |
|--------|-----------|-----------|-------------|---------|------------|-----------|------|------|-------|----------|
| AMZN | CONDITIONAL | NORMAL | No | DANGER | V2_STRICTER | 0.358 | 1.21 | +1.14 | 1.140 | 0.812 |
| GOOG | CONDITIONAL | NORMAL | No | DANGER | V2_STRICTER | 0.341 | 1.17 | +0.72 | 1.133 | 0.873 |
| SBUX | SELL PREMIUM | NORMAL | No | DANGER | V2_STRICTER | 0.331 | 1.16 | +0.40 | 1.223 | 0.926 |
| JNJ | AVOID | DANGER | Yes | NORMAL | V2_LOOSER | 0.241 | 1.17 | +0.99 | 1.079 | 1.118 |
| AAPL | NO EDGE | CAUTION | No | CAUTION | AGREE | 0.309 | 0.90 | +0.02 | 1.050 | 0.987 |
| CAT | NO EDGE | CAUTION | No | DANGER | STATE_MISMATCH | 0.419 | 1.24 | +1.25 | 1.082 | 1.248 |
| EEM | AVOID | DANGER | No | CAUTION | STATE_MISMATCH | 0.289 | 1.26 | +0.93 | 1.017 | 1.035 |
| GLD | NO EDGE | CAUTION | No | NORMAL | STATE_MISMATCH | 0.228 | 1.07 | -0.61 | 1.017 | 0.781 |
| GS | AVOID | DANGER | No | CAUTION | STATE_MISMATCH | 0.346 | 1.05 | +0.63 | 1.034 | 0.942 |
| HD | NO EDGE | CAUTION | No | NORMAL | STATE_MISMATCH | 0.320 | 0.87 | -0.85 | 0.976 | 1.254 |
| HOOD | NO EDGE | NORMAL | No | DANGER | STATE_MISMATCH | 0.758 | 1.03 | +1.25 | 1.088 | 0.814 |
| IWM | NO EDGE | NORMAL | No | NORMAL | AGREE | 0.240 | 0.83 | -1.59 | 0.954 | 0.817 |
| JPM | AVOID | DANGER | No | CAUTION | STATE_MISMATCH | 0.279 | 0.94 | +0.24 | 1.039 | 1.235 |
| KO | NO EDGE | NORMAL | No | DANGER | STATE_MISMATCH | 0.239 | 0.98 | +0.26 | 1.069 | 1.022 |
| MCD | NO EDGE | CAUTION | No | DANGER | STATE_MISMATCH | 0.244 | 1.08 | +0.75 | 1.111 | 1.010 |
| META | NO EDGE | CAUTION | No | DANGER | STATE_MISMATCH | 0.452 | 1.09 | +0.95 | 1.172 | 1.010 |
| MSFT | WATCHLIST | NORMAL | No | DANGER | STATE_MISMATCH | 0.316 | 1.36 | +1.71 | 1.136 | 0.853 |
| NFLX | AVOID | DANGER | No | DANGER | AGREE | 0.420 | 1.15 | +1.15 | 1.151 | 0.911 |
| NKE | NO EDGE | NORMAL | No | NORMAL | AGREE | 0.397 | 0.93 | -0.53 | 0.958 | 0.713 |
| NVDA | NO EDGE | NORMAL | No | NORMAL | AGREE | 0.472 | 0.88 | -0.18 | 0.954 | 0.708 |
| PLTR | NO EDGE | NORMAL | No | DANGER | STATE_MISMATCH | 0.714 | 0.91 | +0.45 | 1.136 | 0.759 |
| QQQ | WATCHLIST | NORMAL | No | CAUTION | STATE_MISMATCH | 0.250 | 0.96 | -0.07 | 0.966 | 1.055 |
| SPY | NO EDGE | NORMAL | No | NORMAL | AGREE | 0.173 | 0.78 | -1.41 | 0.901 | 0.747 |
| TLT | NO EDGE | CAUTION | No | CAUTION | AGREE | 0.126 | 0.77 | -1.24 | 0.951 | 1.276 |
| TSLA | NO EDGE | CAUTION | No | CAUTION | AGREE | 0.572 | 0.85 | -0.33 | 1.033 | 1.271 |
| UBER | NO EDGE | CAUTION | No | DANGER | STATE_MISMATCH | 0.477 | 0.95 | +0.68 | 1.092 | 1.097 |
| WMT | NO EDGE | CAUTION | No | NORMAL | STATE_MISMATCH | 0.287 | 0.87 | -1.27 | 0.879 | 0.927 |
| XLB | NO EDGE | NORMAL | No | NORMAL | AGREE | 0.233 | 0.96 | -1.05 | 0.969 | 1.301 |
| XLE | NO EDGE | NORMAL | No | NORMAL | AGREE | 0.310 | 0.82 | -0.46 | 1.002 | 0.619 |
| XLF | NO EDGE | CAUTION | No | NORMAL | STATE_MISMATCH | 0.201 | 0.84 | -0.52 | 0.914 | 1.410 |
| XLI | NO EDGE | NORMAL | No | DANGER | STATE_MISMATCH | 0.228 | 1.18 | +1.23 | 0.917 | 1.113 |
| XLV | NO EDGE | CAUTION | No | CAUTION | AGREE | 0.192 | 0.79 | -1.85 | 1.001 | 1.205 |
| XOM | NO EDGE | CAUTION | No | NORMAL | STATE_MISMATCH | 0.328 | 1.06 | +1.52 | 1.156 | 0.598 |

---

## 2026-07-08 (Wednesday)

**Shadow summary:** Checked 99 / 44 agree / 5 V2_STRICTER / 5 V2_LOOSER / 44 state_mismatch / 1 nodata | index-gating v1 100% vs v2 97% | oscillation v1 0.55 vs v2 0.73 | warm 67%

| Ticker | v1 Action | v1 Regime | v2 Eligible | v2 Gate | Divergence | sigma_fwd | FVRP | z | 1M/3M | accel_dn |
|--------|-----------|-----------|-------------|---------|------------|-----------|------|------|-------|----------|
| AMZN | CONDITIONAL | NORMAL | No | DANGER | V2_STRICTER | 0.371 | 1.18 | +1.00 | 1.143 | 0.831 |
| GOOG | CONDITIONAL | NORMAL | No | DANGER | V2_STRICTER | 0.336 | 1.17 | +0.74 | 1.114 | 0.846 |
| SBUX | SELL PREMIUM | NORMAL | No | DANGER | V2_STRICTER | 0.342 | 1.10 | +0.12 | 1.187 | 0.994 |
| AAPL | NO EDGE | CAUTION | No | CAUTION | AGREE | 0.302 | 0.93 | +0.23 | 1.047 | 1.060 |
| CAT | NO EDGE | CAUTION | No | DANGER | STATE_MISMATCH | 0.439 | 1.16 | +0.85 | 1.079 | 1.341 |
| EEM | AVOID | DANGER | No | CAUTION | STATE_MISMATCH | 0.306 | 1.21 | +0.69 | 1.058 | 1.112 |
| GLD | NO EDGE | NORMAL | No | NORMAL | AGREE | 0.221 | 1.07 | -0.58 | 0.995 | 0.802 |
| GS | AVOID | DANGER | No | NORMAL | STATE_MISMATCH | 0.325 | 1.13 | +1.29 | 1.031 | 0.944 |
| HD | NO EDGE | CAUTION | No | NORMAL | STATE_MISMATCH | 0.303 | 0.95 | -0.30 | 0.975 | 1.047 |
| HOOD | NO EDGE | CAUTION | No | DANGER | STATE_MISMATCH | 0.769 | 1.00 | +0.93 | 1.076 | 0.874 |
| IWM | NO EDGE | NORMAL | No | NORMAL | AGREE | 0.230 | 0.89 | -0.82 | 0.982 | 0.731 |
| JNJ | AVOID | DANGER | No | NORMAL | STATE_MISMATCH | 0.254 | 1.15 | +0.89 | 1.045 | 1.017 |
| JPM | AVOID | DANGER | No | CAUTION | STATE_MISMATCH | 0.278 | 0.93 | +0.08 | 1.021 | 0.741 |
| KO | NO EDGE | NORMAL | No | DANGER | STATE_MISMATCH | 0.251 | 0.94 | -0.02 | 1.082 | 1.024 |
| MCD | NO EDGE | CAUTION | No | CAUTION | AGREE | 0.254 | 1.04 | +0.47 | 1.094 | 0.954 |
| META | NO EDGE | CAUTION | No | DANGER | STATE_MISMATCH | 0.477 | 1.02 | +0.66 | 1.160 | 1.011 |
| MSFT | NO EDGE | NORMAL | No | DANGER | STATE_MISMATCH | 0.325 | 1.33 | +1.61 | 1.131 | 0.840 |
| NFLX | AVOID | DANGER | No | DANGER | AGREE | 0.440 | 1.14 | +1.08 | 1.173 | 0.963 |
| NKE | NO EDGE | NORMAL | No | NORMAL | AGREE | 0.407 | 0.86 | -0.83 | 0.898 | 0.745 |
| NVDA | NO EDGE | NORMAL | No | NORMAL | AGREE | 0.474 | 0.86 | -0.43 | 0.957 | 0.760 |
| PLTR | NO EDGE | NORMAL | No | DANGER | STATE_MISMATCH | 0.696 | 0.94 | +0.68 | 1.139 | 0.773 |
| QQQ | WATCHLIST | NORMAL | No | CAUTION | STATE_MISMATCH | 0.258 | 0.97 | +0.09 | 0.998 | 1.133 |
| SPY | NO EDGE | NORMAL | No | NORMAL | AGREE | 0.168 | 0.83 | -0.84 | 0.913 | 0.775 |
| TLT | NO EDGE | CAUTION | No | CAUTION | AGREE | 0.128 | 0.77 | -1.27 | 0.941 | 1.361 |
| TSLA | NO EDGE | CAUTION | No | CAUTION | AGREE | 0.606 | 0.80 | -0.74 | 1.040 | 1.330 |
| UBER | NO EDGE | CAUTION | No | DANGER | STATE_MISMATCH | 0.470 | 0.94 | +0.60 | 1.078 | 1.155 |
| WMT | NO EDGE | CAUTION | No | NORMAL | STATE_MISMATCH | 0.297 | 0.87 | -1.28 | 0.922 | 1.045 |
| XLB | NO DATA | NORMAL | No | NORMAL | NODATA_SKEW | — | — | — | — | — |
| XLE | NO EDGE | CAUTION | No | NORMAL | STATE_MISMATCH | 0.286 | 0.94 | +0.80 | 1.080 | 0.665 |
| XLF | NO EDGE | CAUTION | No | NORMAL | STATE_MISMATCH | 0.194 | 0.95 | +0.59 | 1.064 | 0.528 |
| XLI | NO EDGE | CAUTION | No | DANGER | STATE_MISMATCH | 0.226 | 1.32 | +1.96 | 1.354 | 1.104 |
| XLV | NO EDGE | NORMAL | No | CAUTION | STATE_MISMATCH | 0.200 | 0.99 | -0.18 | 1.034 | 1.024 |
| XOM | NO EDGE | CAUTION | No | NORMAL | STATE_MISMATCH | 0.314 | 0.72 | -2.19 | 0.772 | 0.630 |

---

## 2026-07-07 (Tuesday)

**Shadow summary:** Checked 66 / 34 agree / 2 V2_STRICTER / 5 V2_LOOSER / 25 state_mismatch / 0 nodata | index-gating v1 100% vs v2 95% | oscillation v1 0.18 vs v2 0.27 | warm 50%

| Ticker | v1 Action | v1 Regime | v2 Eligible | v2 Gate | Divergence | sigma_fwd | FVRP | z | 1M/3M | accel_dn |
|--------|-----------|-----------|-------------|---------|------------|-----------|------|------|-------|----------|
| SBUX | CONDITIONAL | NORMAL | No | NORMAL | V2_STRICTER | 0.343 | 1.06 | -0.04 | 1.178 | 1.068 |
| AMZN | NO EDGE | CAUTION | Yes | NORMAL | V2_LOOSER | 0.370 | 1.17 | +0.97 | 1.142 | 0.893 |
| JNJ | AVOID | DANGER | Yes | NORMAL | V2_LOOSER | 0.242 | 1.19 | +1.14 | 1.078 | 1.092 |
| MSFT | NO EDGE | CAUTION | Yes | NORMAL | V2_LOOSER | 0.329 | 1.33 | +1.62 | 1.148 | 0.903 |
| XLI | NO EDGE | NORMAL | Yes | NORMAL | V2_LOOSER | 0.212 | 1.23 | +1.54 | 1.112 | 0.895 |
| AAPL | NO EDGE | CAUTION | No | CAUTION | AGREE | 0.317 | 0.90 | -0.04 | 1.043 | 1.126 |
| CAT | NO EDGE | CAUTION | No | CAUTION | AGREE | 0.422 | 1.20 | +1.05 | 1.083 | 1.367 |
| EEM | AVOID | DANGER | No | CAUTION | STATE_MISMATCH | 0.301 | 1.27 | +0.88 | 0.961 | 1.016 |
| GLD | NO EDGE | NORMAL | No | NORMAL | AGREE | 0.222 | 1.01 | -0.98 | 0.986 | 0.779 |
| GOOG | NO EDGE | CAUTION | No | NORMAL | STATE_MISMATCH | 0.346 | 1.14 | +0.56 | 1.107 | 0.903 |
| GS | NO EDGE | CAUTION | No | NORMAL | STATE_MISMATCH | 0.341 | 1.09 | +0.99 | 1.051 | 0.959 |
| HD | NO EDGE | CAUTION | No | NORMAL | STATE_MISMATCH | 0.306 | 0.96 | -0.21 | 1.046 | 0.978 |
| HOOD | NO EDGE | NORMAL | No | NORMAL | AGREE | 0.789 | 1.00 | +1.01 | 1.114 | 0.715 |
| IWM | NO EDGE | NORMAL | No | NORMAL | AGREE | 0.232 | 0.88 | -1.04 | 0.967 | 0.611 |
| JPM | NO EDGE | CAUTION | No | NORMAL | STATE_MISMATCH | 0.286 | 0.93 | +0.07 | 1.047 | 0.796 |
| KO | NO EDGE | NORMAL | No | NORMAL | AGREE | 0.232 | 0.95 | +0.06 | 1.096 | 1.099 |
| MCD | NO EDGE | CAUTION | No | CAUTION | AGREE | 0.250 | 0.99 | +0.16 | 1.021 | 1.025 |
| META | NO EDGE | CAUTION | No | NORMAL | STATE_MISMATCH | 0.500 | 0.96 | +0.36 | 1.181 | 1.086 |
| NFLX | AVOID | DANGER | No | NORMAL | STATE_MISMATCH | 0.431 | 1.11 | +0.96 | 1.121 | 1.034 |
| NKE | NO EDGE | CAUTION | No | NORMAL | STATE_MISMATCH | 0.433 | 0.85 | -0.86 | 0.903 | 0.798 |
| NVDA | NO EDGE | NORMAL | No | NORMAL | AGREE | 0.459 | 0.86 | -0.43 | 0.947 | 0.817 |
| PLTR | NO EDGE | CAUTION | No | NORMAL | STATE_MISMATCH | 0.695 | 0.90 | +0.40 | 1.111 | 0.830 |
| QQQ | WATCHLIST | NORMAL | No | CAUTION | STATE_MISMATCH | 0.255 | 1.00 | +0.37 | 1.015 | 1.059 |
| SPY | NO EDGE | NORMAL | No | NORMAL | AGREE | 0.177 | 0.77 | -1.54 | 0.895 | 0.769 |
| TLT | NO EDGE | CAUTION | No | CAUTION | AGREE | 0.128 | 0.77 | -1.34 | 0.989 | 1.216 |
| TSLA | NO EDGE | CAUTION | No | CAUTION | AGREE | 0.640 | 0.75 | -1.28 | 1.036 | 1.311 |
| UBER | NO EDGE | CAUTION | No | CAUTION | AGREE | 0.474 | 0.97 | +0.83 | 1.121 | 1.241 |
| WMT | NO EDGE | CAUTION | No | CAUTION | AGREE | 0.297 | 0.85 | -1.43 | 0.885 | 1.045 |
| XLB | NO EDGE | NORMAL | No | NORMAL | AGREE | 0.214 | 0.96 | -1.06 | 0.879 | 0.834 |
| XLE | NO EDGE | NORMAL | No | NORMAL | AGREE | 0.276 | 0.84 | -0.26 | 0.984 | 0.714 |
| XLF | NO EDGE | NORMAL | No | NORMAL | AGREE | 0.201 | 0.83 | -0.53 | 1.025 | 0.547 |
| XLV | NO EDGE | NORMAL | No | NORMAL | AGREE | 0.189 | 0.94 | -0.54 | 1.008 | 1.100 |
| XOM | WATCHLIST | NORMAL | No | NORMAL | AGREE | 0.290 | 0.93 | +0.25 | 0.995 | 0.677 |

---

## 2026-07-06 (Monday)

**Shadow summary:** Checked 33 / 16 agree / 1 V2_STRICTER / 1 V2_LOOSER / 15 state_mismatch / 0 nodata | index-gating v1 100% vs v2 100% | oscillation v1 — vs v2 — | warm 0%

| Ticker | v1 Action | v1 Regime | v2 Eligible | v2 Gate | Divergence | sigma_fwd | FVRP | z | 1M/3M | accel_dn |
|--------|-----------|-----------|-------------|---------|------------|-----------|------|------|-------|----------|
| SBUX | SELL PREMIUM | NORMAL | No | NORMAL | V2_STRICTER | 0.380 | 0.94 | +0.00 | 1.131 | 0.809 |
| MSFT | NO EDGE | CAUTION | Yes | NORMAL | V2_LOOSER | 0.359 | 1.16 | +0.00 | 1.107 | 0.940 |
| AAPL | NO EDGE | CAUTION | No | NORMAL | STATE_MISMATCH | 0.299 | 0.92 | +0.00 | 1.041 | 1.210 |
| AMZN | NO EDGE | CAUTION | No | NORMAL | STATE_MISMATCH | 0.396 | 1.03 | +0.00 | 1.090 | 0.961 |
| CAT | NO EDGE | CAUTION | No | NORMAL | STATE_MISMATCH | 0.453 | 1.11 | +0.00 | 1.044 | 1.471 |
| EEM | NO EDGE | CAUTION | No | NORMAL | STATE_MISMATCH | 0.323 | 1.10 | +0.00 | 0.968 | 1.092 |
| GLD | NO EDGE | NORMAL | No | NORMAL | AGREE | 0.388 | 0.61 | +0.00 | 1.032 | 0.839 |
| GOOG | NO EDGE | CAUTION | No | NORMAL | STATE_MISMATCH | 0.385 | 0.98 | +0.00 | 1.072 | 0.972 |
| GS | NO EDGE | NORMAL | No | NORMAL | AGREE | 0.390 | 0.91 | +0.00 | 1.019 | 1.031 |
| HD | NO EDGE | CAUTION | No | NORMAL | STATE_MISMATCH | 0.348 | 0.76 | +0.00 | 0.966 | 0.705 |
| HOOD | NO EDGE | NORMAL | No | NORMAL | AGREE | 0.794 | 0.93 | +0.00 | 1.037 | 0.771 |
| IWM | NO EDGE | NORMAL | No | NORMAL | AGREE | 0.255 | 0.77 | +0.00 | 0.959 | 0.659 |
| JNJ | NO EDGE | CAUTION | No | NORMAL | STATE_MISMATCH | 0.247 | 1.11 | +0.00 | 1.025 | 0.980 |
| JPM | NO EDGE | NORMAL | No | NORMAL | AGREE | 0.308 | 0.84 | +0.00 | 1.024 | 0.859 |
| KO | NO EDGE | NORMAL | No | NORMAL | AGREE | 0.224 | 0.93 | +0.00 | 1.048 | 0.935 |
| MCD | NO EDGE | CAUTION | No | NORMAL | STATE_MISMATCH | 0.226 | 1.11 | +0.00 | 1.078 | 1.094 |
| META | NO EDGE | CAUTION | No | NORMAL | STATE_MISMATCH | 0.488 | 0.94 | +0.00 | 1.140 | 1.169 |
| NFLX | NO EDGE | CAUTION | No | NORMAL | STATE_MISMATCH | 0.447 | 1.01 | +0.00 | 1.076 | 1.018 |
| NKE | NO EDGE | CAUTION | No | NORMAL | STATE_MISMATCH | 0.505 | 0.73 | +0.00 | 0.903 | 0.766 |
| NVDA | NO EDGE | NORMAL | No | NORMAL | AGREE | 0.405 | 0.97 | +0.00 | 0.945 | 0.874 |
| PLTR | NO EDGE | CAUTION | No | NORMAL | STATE_MISMATCH | 0.656 | 0.91 | +0.00 | 1.056 | 0.890 |
| QQQ | WATCHLIST | NORMAL | No | NORMAL | AGREE | 0.230 | 1.08 | +0.00 | 0.982 | 1.138 |
| SPY | NO EDGE | NORMAL | No | NORMAL | AGREE | 0.163 | 0.81 | +0.00 | 0.890 | 0.829 |
| TLT | NO EDGE | CAUTION | No | NORMAL | STATE_MISMATCH | 0.109 | 0.83 | +0.00 | 0.902 | 1.302 |
| TSLA | NO EDGE | CAUTION | No | NORMAL | STATE_MISMATCH | 0.496 | 0.94 | +0.00 | 1.012 | 1.412 |
| UBER | NO EDGE | CAUTION | No | NORMAL | STATE_MISMATCH | 0.412 | 0.99 | +0.00 | 1.026 | 1.186 |
| WMT | NO EDGE | NORMAL | No | NORMAL | AGREE | 0.321 | 0.77 | +0.00 | 0.889 | 1.123 |
| XLB | NO EDGE | NORMAL | No | NORMAL | AGREE | 0.231 | 0.73 | +0.00 | 1.000 | 0.898 |
| XLE | NO EDGE | NORMAL | No | NORMAL | AGREE | 0.303 | 0.77 | +0.00 | 0.980 | 0.767 |
| XLF | NO EDGE | NORMAL | No | NORMAL | AGREE | 0.216 | 0.73 | +0.00 | 1.010 | 0.591 |
| XLI | NO EDGE | NORMAL | No | NORMAL | AGREE | 0.221 | 0.94 | +0.00 | 1.000 | 0.964 |
| XLV | NO EDGE | NORMAL | No | NORMAL | AGREE | 0.185 | 0.93 | +0.00 | 1.059 | 0.940 |
| XOM | NO EDGE | NORMAL | No | NORMAL | AGREE | 0.344 | 0.84 | +0.00 | 1.010 | 0.714 |

---
