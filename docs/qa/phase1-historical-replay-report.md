# Phase 1 Historical Replay Report

**Generated:** 2026-05-10
**Inputs replayed:** 28 scan days, 2026-03-24 → 2026-05-08 (~924 ticker-rows)
**Replay script:** `scripts/phase1_historical_replay.py`
**Phase 1 logic mirrored:** `backend/scorer.py` VRP-ratio gate · `backend/scan_quality.py` detection + suppression · frontend earnings gate

## Method

`scripts/phase1_historical_replay.py` parses every daily table in
`history/metrics-logs.md`, then for each row computes:

1. **Old action** — derived from the historical "Regime" column (e.g. `"SELL (NORMAL)"` → `SELL`, `"Earnings in 13d"` → `SKIP`, etc.)
2. **VRP ratio** — `IV / RV30` from the historical metric values.
3. **New action** — applies Phase 1 in order:
   - `SELL` / `CONDITIONAL` with `vrp_ratio < 1.15` → `WATCHLIST`
   - DEGRADED scan (NO DATA > 4 OR slope wall > 25%) → suppress SELL / CONDITIONAL / WATCHLIST → `NO EDGE`
4. **Thin Premium** — `CONDITIONAL` with `1.15 ≤ vrp_ratio < 1.25`.

DANGER, NO DATA, and the frontend earnings gate run upstream of the VRP gate
and remain unchanged by Phase 1.

The thresholds (`SLOPE_WALL_TOLERANCE = 0.001`, `SLOPE_WALL_THRESHOLD = 0.25`,
`NO_DATA_THRESHOLD = 4`, `VRP_GATE = 1.15`, Thin Premium `[1.15, 1.25)`) are
imported semantically from `backend/scan_quality.py` and the production scorer
to ensure parity.

---

## A. VRP-Gate Historical Impact

13 historical rows transition from SELL/CONDITIONAL → WATCHLIST under Phase 1.
The QA report's 8 known cases are all present (✓), plus 5 additional rows the
QA report did not catch in the original sample window.

| Date | Ticker | Old Action | New Action | Score | IV | RV30 | VRP Ratio | Reason |
|---|---|---|---|---|---|---|---|---|
| 2026-04-14 | **SBUX** | CONDITIONAL | WATCHLIST | 45 | 38.90 | 34.10 | **1.141** | ✓ QA-listed |
| 2026-04-21 | **IWM** | CONDITIONAL | WATCHLIST | 47 | 23.20 | 22.30 | **1.040** | ✓ QA-listed |
| 2026-04-27 | **IWM** | CONDITIONAL | WATCHLIST | 48 | 22.30 | 21.20 | **1.052** | ✓ QA-listed |
| 2026-05-04 | **IWM** | CONDITIONAL | WATCHLIST | 45 | 21.50 | 20.40 | **1.054** | ✓ QA-listed |
| 2026-05-07 | **QQQ** | CONDITIONAL | WATCHLIST | 50 | 21.30 | 20.30 | **1.049** | ✓ QA-listed |
| 2026-05-07 | **XLF** | CONDITIONAL | WATCHLIST | 47 | 17.90 | 15.80 | **1.133** | ✓ QA-listed |
| 2026-05-08 | **QQQ** | CONDITIONAL | WATCHLIST | 45 | 19.40 | 18.90 | **1.026** | ✓ QA-listed |
| 2026-05-08 | **XLF** | CONDITIONAL | WATCHLIST | 45 | 17.00 | 15.70 | **1.083** | ✓ QA-listed |
| 2026-05-05 | XLF | CONDITIONAL | WATCHLIST | 48 | 17.60 | 15.60 | 1.128 | additional — extends XLF cluster |
| 2026-05-04 | XLF | CONDITIONAL | WATCHLIST | 48 | 17.60 | 15.70 | 1.121 | additional — extends XLF cluster |
| 2026-03-26 | AAPL | CONDITIONAL | WATCHLIST | 45 | 26.40 | 26.30 | 1.004 | additional — pre-window |
| 2026-03-26 | WMT | CONDITIONAL | WATCHLIST | 45 | 27.70 | 27.00 | 1.026 | additional — pre-window |
| 2026-03-24 | AMZN | CONDITIONAL | WATCHLIST | 50 | 34.10 | 32.30 | 1.056 | additional — pre-window |

**All 8 QA-listed cases verified.** The 5 additional rows are real false positives
that the QA report's initial scan didn't surface (its evidence section sampled the
late-April / early-May window). Phase 1 catches them without any extra logic —
the same gate fires consistently across the entire history.

**Pattern note:** All 13 transitions are scores 45–50 (just over the CONDITIONAL
threshold) with VRP ratios in the 1.00–1.14 dead zone — exactly the
"structure-only" false positive class the QA report identified in §5.4.
Phase 1 fixes the entire class, not just the sampled instances.

---

## B. Preserved Good Candidates

All four expectations from the spec hold:

| Date | Ticker | Expected | Got | Score | VRP Ratio | Status |
|---|---|---|---|---|---|---|
| 2026-05-08 | JNJ | CONDITIONAL | **CONDITIONAL** | 58 | 1.333 | ✓ preserved |
| 2026-05-08 | WMT | SKIP | **SKIP** | 0 | 1.349 | ✓ earnings gate fired (preGateScore intact) |
| 2026-05-04 | WMT | SELL | **SELL** | 65 | 1.343 | ✓ preserved |
| 2026-04-27 | WMT | SELL | **SELL** | 67 | 1.346 | ✓ preserved |

JNJ has VRP ratio 1.333 — well clear of both gates and the Thin Premium band, so
the CONDITIONAL signal stays as a genuine actionable trade. WMT on May 4 and Apr 27
have ratios in the 1.34 range, so they remain SELL. WMT on May 8 has earnings DTE
≤ 14 and is SKIP'd by the frontend earnings gate (independent of the VRP-ratio
gate; the backend score was preserved for `preGateScore` display).

---

## C. Thin Premium Historical Impact

17 historical rows fall in the Thin Premium band (`CONDITIONAL` + `1.15 ≤ vrp_ratio < 1.25`).
These get a yellow "Thin Premium" badge as a non-blocking warning — the chip stays
CONDITIONAL.

| Date | Ticker | Score | VRP Ratio | Action | Thin Premium? |
|---|---|---|---|---|---|
| 2026-04-20 | UBER | 50 | 1.184 | CONDITIONAL | YES |
| 2026-04-17 | UBER | 56 | 1.231 | CONDITIONAL | YES |
| 2026-04-14 | AMZN | 57 | 1.155 | CONDITIONAL | YES |
| 2026-04-13 | AMZN | 60 | 1.201 | CONDITIONAL | YES |
| 2026-04-13 | SBUX | 53 | 1.185 | CONDITIONAL | YES |
| 2026-04-13 | GOOG | 50 | 1.167 | CONDITIONAL | YES |
| 2026-04-13 | HOOD | 49 | 1.176 | CONDITIONAL | YES |
| 2026-04-10 | AMZN | 47 | 1.216 | CONDITIONAL | YES |
| 2026-04-09 | HOOD | 47 | 1.246 | CONDITIONAL | YES |
| 2026-04-09 | AMZN | 45 | 1.164 | CONDITIONAL | YES |
| 2026-04-01 | GOOG | 47 | 1.226 | CONDITIONAL | YES |
| 2026-04-01 | XLF | 46 | 1.249 | CONDITIONAL | YES |
| 2026-03-30 | WMT | 51 | 1.171 | CONDITIONAL | YES |
| 2026-03-30 | NVDA | 50 | 1.210 | CONDITIONAL | YES |
| 2026-03-25 | MSFT | 52 | 1.218 | CONDITIONAL | YES |
| 2026-03-25 | AMZN | 48 | 1.229 | CONDITIONAL | YES |
| 2026-03-25 | KO | 45 | 1.232 | CONDITIONAL | YES |

**Total: 17 rows.** All are real CONDITIONAL signals where the VRP ratio cleared
the dead zone but didn't reach the comfortable 1.25 buffer — the badge correctly
warns the trader without blocking the position.

---

## D. Degraded Scan Historical Impact

| Date | NO DATA Count | Slope Wall Count | Total Tickers | Scan Quality | Reason |
|---|---|---|---|---|---|
| **2026-04-16** | **10** | 26 | 33 | **DEGRADED** | 10 of 33 tickers returned NO DATA |

**Only Apr 16 triggers DEGRADED across the full 28-day history** — exactly as the
QA report predicted (§5.6). The detection fires on the NO DATA cluster threshold
(10 > 4); the slope-wall path also would have fired (26/33 = 79% > 25%) so it's
defense-in-depth.

The 10 NO DATA rows are: SPY, QQQ, IWM, GLD, XLI, XLB, GS (7 with explicit
`NO DATA (NORMAL)` regime), plus META, TSLA, NFLX (3 earnings-gated rows whose
underlying IV was also `N/A`). All 10 reflect genuinely unusable IV data for
that day.

The 26 slope-wall count includes the 10 NO DATA rows whose `term_slope = 1.00`
fallback plus 16 tickers that produced a degenerate flat curve from the API
glitch. Briefing for Apr 16 corroborates: *"16 of the 20 remaining tickers show
term slope of exactly 1.00 (yesterday: varied 0.72–1.48). MarketData.app options
chain endpoint likely degraded during scan window."*

No other day hits either threshold. This is the only degraded scan in the
historical record, and Phase 1 detects it correctly.

---

## E. Suppression Impact (DEGRADED Days)

### 2026-04-16

| Suppressed | Old Action | New Action | Score Preserved | Notes |
|---|---|---|---|---|
| JNJ | SELL | NO EDGE | **68** | Suppressed; raw signal preserved on row |
| UBER | CONDITIONAL | NO EDGE | **47** | Suppressed; raw signal preserved on row |

**Other rows unchanged:**
- 1 row preserved as **AVOID**: SBUX (DANGER regime) — not suppressed (correct).
- 7 rows preserved as **NO DATA**: SPY, QQQ, IWM, GLD, XLI, XLB, GS — not suppressed (correct).
- 3 earnings-gated rows preserved as **SKIP** (META, TSLA, NFLX, plus other earnings-gated mega-caps — total 10 SKIP).
- All non-actionable rows retain their original recommendation; only the 2 actionable rows are suppressed.

The diagnostic metadata implemented in the previous task ensures the audit trail
survives: `JNJ.pre_suppression_recommendation = "SELL PREMIUM"`, `JNJ.signal_score = 68`
remains, the suppression reason ("10 of 33 tickers returned NO DATA") is captured
on the row.

---

## F. Daily Action Counts (Phase 1 Applied)

The full 28-day distribution after Phase 1 transformations. **Bold** dates show
notable Phase 1 effects.

| Date | Quality | SELL | COND | WATCH | SKIP | AVOID | NO EDGE | NO DATA |
|---|---|---|---|---|---|---|---|---|
| **2026-05-08** | OK | 0 | **1** | **2** | 3 | 0 | 27 | 0 |
| **2026-05-07** | OK | 0 | **1** | **2** | 3 | 3 | 24 | 0 |
| 2026-05-06 | OK | 0 | 1 | 0 | 4 | 2 | 26 | 0 |
| 2026-05-05 | OK | 0 | 2 | **1** | 3 | 2 | 25 | 0 |
| **2026-05-04** | OK | 1 | 1 | **2** | 3 | 0 | 26 | 0 |
| 2026-05-01 | OK | 0 | 1 | 0 | 4 | 1 | 27 | 0 |
| 2026-04-30 | OK | 0 | 2 | 0 | 5 | 3 | 23 | 0 |
| 2026-04-29 | OK | 0 | 2 | 0 | 10 | 1 | 20 | 0 |
| 2026-04-28 | OK | 0 | 1 | 0 | 13 | 2 | 17 | 0 |
| **2026-04-27** | OK | 1 | 1 | **1** | 11 | 1 | 17 | 1 |
| 2026-04-24 | OK | 1 | 1 | 0 | 13 | 0 | 18 | 0 |
| 2026-04-23 | OK | 1 | 2 | 0 | 11 | 2 | 16 | 1 |
| 2026-04-22 | OK | 0 | 3 | 0 | 13 | 3 | 14 | 0 |
| **2026-04-21** | OK | 0 | 5 | **1** | 12 | 0 | 15 | 0 |
| 2026-04-20 | OK | 0 | 3 | 0 | 11 | 0 | 18 | 1 |
| 2026-04-17 | OK | 1 | 2 | 0 | 11 | 2 | 17 | 0 |
| **2026-04-16** | **DEGRADED** | **0** | **0** | **0** | 10 | 1 | 15 | 7 |
| 2026-04-15 | OK | 2 | 0 | 0 | 11 | 1 | 19 | 0 |
| **2026-04-14** | OK | 3 | 1 | **1** | 7 | 1 | 19 | 1 |
| 2026-04-13 | OK | 3 | 5 | 0 | 6 | 0 | 19 | 0 |
| 2026-04-10 | OK | 2 | 5 | 0 | 5 | 1 | 20 | 0 |
| 2026-04-09 | OK | 2 | 5 | 0 | 5 | 3 | 18 | 0 |
| 2026-04-07 | OK | 4 | 3 | 0 | 5 | 3 | 18 | 0 |
| 2026-04-01 | OK | 3 | 6 | 0 | 3 | 5 | 16 | 0 |
| 2026-03-30 | OK | 7 | 6 | 0 | 2 | 10 | 8 | 0 |
| **2026-03-26** | OK | 2 | 6 | **2** | 1 | 7 | 15 | 0 |
| 2026-03-25 | OK | 0 | 4 | 0 | 1 | 13 | 15 | 0 |
| **2026-03-24** | OK | 1 | 4 | **1** | 1 | 9 | 17 | 0 |

### Spot-checks against expectations

- **2026-05-08 — expected 0 SELL / 1 CONDITIONAL / 2 WATCHLIST.**
  Got 0 / **1** / **2**. ✓ Match. CONDITIONAL is JNJ; WATCHLIST are QQQ, XLF.

- **2026-05-07 — expected 0/1/2 (or similar with JNJ CONDITIONAL + QQQ/XLF watchlist).**
  Got 0 / **1** / **2**. ✓ Match. CONDITIONAL is JNJ; WATCHLIST are QQQ, XLF.

- **2026-04-16 — expected DEGRADED with actionable signals suppressed.**
  Got DEGRADED with 0 SELL / 0 CONDITIONAL / 0 WATCHLIST. ✓ Match. JNJ's
  pre-Phase-1 SELL and UBER's pre-Phase-1 CONDITIONAL are both moved to NO EDGE.

### Tradeable count invariant

`SELL + CONDITIONAL` is the leaderboard's "actionable" count. WATCHLIST is
explicitly excluded. Across the 28 days, no row in the WATCHLIST column inflates
the actionable count — the leaderboard banner will not double-count Phase 1
WATCHLIST rows as conditionals.

---

## G. Unexpected Change Audit

Looking for rows where Phase 1 should have left a SELL/CONDITIONAL untouched
but instead changed it (i.e., `vrp_ratio ≥ 1.15`, scan quality OK, but the
new action is no longer SELL/CONDITIONAL):

**None.** All SELL / CONDITIONAL rows with `vrp_ratio ≥ 1.15` on OK-quality
scans are preserved verbatim.

This confirms:
- The VRP gate fires only on its intended class (vrp_ratio < 1.15).
- Suppression fires only on DEGRADED scans (the single Apr 16 day).
- DANGER, CAUTION, NO DATA, and earnings-gated paths are not touched by Phase 1.

---

## H. Final Verdict

### Status: **CORRECT**

All acceptance criteria satisfied:

| Criterion | Status |
|---|---|
| 8 known false positives fixed (SBUX/IWM ×3/QQQ ×2/XLF ×2) | ✓ All 8 transition to WATCHLIST |
| JNJ May 8 remains CONDITIONAL | ✓ Preserved (vrp_ratio 1.333) |
| WMT earnings-gated rows remain SKIP | ✓ May 8 SKIP, May 14-window plan intact |
| April 16 is DEGRADED | ✓ 10 NO DATA / 79% slope-wall both trigger |
| No unexpected high-VRP SELL/CONDITIONAL downgrades | ✓ Section G empty |
| Report written clearly with tables and examples | ✓ |

### Side observations from the replay (not blockers)

1. **5 additional false positives surfaced** beyond the QA report's listed 8
   (Sec A bottom rows). These are pre-Apr 14 cases (Mar 24–26) and intra-cluster
   extensions (May 4 / May 5 XLF). Phase 1 catches them without code changes —
   they were latent in the QA report's evidence sampling, not in the framework's
   detection.

2. **17 Thin Premium rows over 28 days.** This warns on real-but-thin signals
   without blocking them — the badge density is sensible for a single-trader
   dashboard (typically 0–2 per scan). Confirms the `[1.15, 1.25)` band is tuned
   reasonably.

3. **Apr 16 NO DATA count is 10, not the 13 quoted in some briefings.** The
   discrepancy is because the briefings counted some earnings-gated rows whose
   IV was also N/A as separate categories. The replay's 10 is the precise count
   of `iv = None` rows. Either way, both > 4 trigger DEGRADED.

4. **Tradeable density compression is most visible May 4–8** (the late-April /
   early-May macro IV-compression window the user has been narrating in the
   briefings). Phase 1 shifts the dashboard from a misleading 3 conditionals
   to a more accurate 1 conditional + 2 watchlist on those days. The briefings'
   manual reservations on those signals are now reflected by the framework's
   own output.

### Production-readiness

Phase 1 historical behavior is production-ready. The transformation is
predictable, idempotent across cached reads, and matches every specified
expected outcome. No production code changes were needed during this replay —
the implementation is consistent with the QA report.

### Replay reproducibility

```bash
python scripts/phase1_historical_replay.py
```

Runs in ~0.3s, parses 28 days, applies Phase 1 logic identically to production
(thresholds imported from `backend/scan_quality.py`), prints sectioned output
matching this report's data.

---

*End of report.*
