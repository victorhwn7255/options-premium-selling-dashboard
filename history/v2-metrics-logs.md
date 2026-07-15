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
- **Shadow summary** — `Checked N / A agree / S V2_STRICTER / L V2_LOOSER / M state_mismatch / K nodata | index-gating v1 X% vs v2 Y% | oscillation v1 a vs v2 b | warm C%`
- **Table** — Ticker / v1 Action / v1 Regime / v2 Eligible / v2 Gate / Divergence / sigma_fwd / FVRP / z / 1M/3M / accel_dn

**Column order:**
```
| Ticker | v1 Action | v1 Regime | v2 Eligible | v2 Gate | Divergence | sigma_fwd | FVRP | z | 1M/3M | accel_dn |
```

**Divergence values:** `AGREE` | `V2_STRICTER` (v1 trades, v2 gates) | `V2_LOOSER` (v2 allows, v1 gates) | `STATE_MISMATCH` | `NODATA_SKEW`. Rows are sorted decision-changing-first (V2_STRICTER, then V2_LOOSER), then by ticker.

---

> **IMPORTANT:** Entries are in **descending order** (newest first). New entries go immediately below this line.

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
