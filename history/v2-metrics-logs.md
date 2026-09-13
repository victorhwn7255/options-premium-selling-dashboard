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
