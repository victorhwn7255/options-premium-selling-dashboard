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
