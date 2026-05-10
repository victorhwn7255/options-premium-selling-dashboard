# Phase 1 — Manual UI QA Checklist

The frontend has no installed test framework (no Jest / RTL in
`frontend/package.json`), so these manual browser-side checks cover what
component tests would otherwise assert. Run after any change to:

- `frontend/src/lib/scoring.ts` (action mapping, gate, thinPremium derivation)
- `frontend/src/lib/types.ts` (action union, diagnostic fields)
- `frontend/src/components/Leaderboard.tsx` (chips, badges, tooltips, mobile cards)
- `frontend/src/components/DetailPanel.tsx` (action chip, warning blocks, position construction)
- `frontend/src/app/page.tsx` (DEGRADED scan banner)
- `frontend/src/app/globals.css` (utility classes used by the chips)

Cross-references:
- Backend regression suite: `backend/test_qa_phase1_regression.py` (17 tests)
- Backend functional suite: `backend/test_qa_phase1.py` (13 tests)
- Source of truth: `references/dashboard-behavior-qa-report.md`

---

## 1. May 8 JNJ / QQQ / XLF behavior

Open the dashboard with the latest scan loaded (May 8 metrics, or any scan
where these tickers are present in similar config).

### JNJ — CONDITIONAL preserved (vrp_ratio ≥ 1.15)

- [ ] Action chip on the leaderboard row reads **CONDITIONAL** (yellow).
- [ ] No "Thin Premium" badge appears next to the chip (vrp_ratio 1.333 is
      ≥ 1.25, outside the badge range).
- [ ] Click the row → DetailPanel expands inline.
- [ ] DetailPanel header shows the **CONDITIONAL** chip.
- [ ] **Position Construction** block (Target Delta / Structure / DTE / Sizing)
      is rendered.
- [ ] No "Watchlist — structure clean…" block appears.

### QQQ — WATCHLIST (vrp_ratio < 1.15)

- [ ] Action chip on the leaderboard row reads **WATCHLIST**, dusty-purple
      styling, visually distinct from CONDITIONAL (yellow) and NO EDGE (gray).
- [ ] No "Thin Premium" badge (it only applies to CONDITIONAL).
- [ ] Score pill shows the raw score (e.g., 45 / 50) — *not* zeroed.
- [ ] Click the row → DetailPanel header shows the **WATCHLIST** chip.
- [ ] DetailPanel **Position Construction block is hidden**.
- [ ] Accent-purple "Watchlist — structure clean, but premium too thin" block
      appears between the metrics grid and the IV/RV chart.
- [ ] The block prose includes the actual VRP ratio
      (e.g., "VRP ratio 1.03 is below the 1.15 dead zone").
- [ ] DetailPanel does NOT include the red Skip / Avoid / NoData blocks.

### XLF — same as QQQ

- [ ] Same checklist as QQQ. XLF (vrp_ratio 1.083 < 1.15) should display as
      WATCHLIST with the same UI treatment.

### A CONDITIONAL with vrp_ratio between 1.15 and 1.25 (Thin Premium)

If the scan happens to contain such a row (or stage one — see "Producing test
scans" below):

- [ ] **Yellow "Thin Premium" badge** appears next to the CONDITIONAL chip on
      the leaderboard row (and on the DetailPanel header).
- [ ] Tooltip on hover reads "VRP ratio just above 1.15 dead zone — premium is
      thin" (or similar).
- [ ] Action chip remains **CONDITIONAL**, NOT downgraded — Thin Premium is a
      warning, not a block.
- [ ] DetailPanel still renders Position Construction.

---

## 2. Apr 16 — Degraded scan behavior

To stage a degraded scan locally, temporarily lower the threshold in
`backend/scan_quality.py`:

```python
NO_DATA_THRESHOLD = -1   # any positive count triggers DEGRADED
```

Restart the backend, refresh the dashboard. **Restore the constant when done.**
Alternatively, a real scan with ≥5 NO DATA rows or > 25% slope ≈ 1.00 will
trigger DEGRADED naturally.

### Scan-quality banner

- [ ] Red **DEGRADED SCAN** banner appears above the regime banner.
- [ ] Banner contains the suppression reason (e.g.,
      "13 of 33 tickers returned NO DATA" or
      "16 of 20 tickers show term slope ≈ 1.00 (80%) — likely degenerate term structure").
- [ ] Banner prose warns: "Actionable recommendations have been suppressed for
      this scan — no SELL or CONDITIONAL signals will display…"

### Suppressed rows in the leaderboard

- [ ] No row in the leaderboard shows **SELL**, **CONDITIONAL**, or **WATCHLIST**.
      All actionable rows display as **NO EDGE**.
- [ ] The `actionable / conditional` count in the leaderboard header shows
      `0 actionable · 0 conditional` (or similar).
- [ ] Rows that were AVOID (slope > 1.15) still display as **AVOID** —
      not downgraded.
- [ ] Rows that were NO DATA still display as **NO DATA**.
- [ ] Rows that were earnings-gated still display **SKIP** (the frontend
      earnings gate is independent of the suppression).

### Audit trail per suppressed row

- [ ] Hover the action-chip cell on a suppressed desktop-table row → tooltip
      reads "Suppressed by degraded scan (was SELL)" (or COND / WATCHLIST).
- [ ] Resize browser to mobile breakpoint (< 640 px). Suppressed rows show a
      tiny italic gray line "Suppressed by degraded scan · was SELL" between
      the metrics line and the action chips.
- [ ] Click a suppressed row → DetailPanel shows a red diagnostic block:
      "Raw signal suppressed because scan data is degraded.
       Raw signal before suppression: **SELL** (score 70).
       No Position Construction is shown.
       Suppression reason: *<reason>*."
- [ ] Position Construction block is **not** rendered on the suppressed row's
      DetailPanel.
- [ ] The score pill on the leaderboard still shows the raw score (e.g., 70) —
      `signal_score` is preserved.

---

## 3. Thin Premium badge

(Already partially covered in §1. Standalone checks here.)

- [ ] Badge color: yellow (warning-subtle background, warning-30 border).
- [ ] Label text: **"Thin Premium"**.
- [ ] Tooltip on hover: "VRP ratio just above 1.15 dead zone — premium is thin".
- [ ] Visible when: `action === 'CONDITIONAL'` AND `1.15 ≤ vrp_ratio < 1.25`.
- [ ] **Hidden when:**
  - [ ] action is SELL (no badge — premium is fat by definition)
  - [ ] action is WATCHLIST (no badge — already a stronger warning)
  - [ ] action is NO EDGE / AVOID / SKIP / NO DATA
  - [ ] vrp_ratio < 1.15 (would be WATCHLIST, not CONDITIONAL)
  - [ ] vrp_ratio ≥ 1.25 (premium fat enough)
- [ ] Renders in BOTH the desktop table row AND mobile card.
- [ ] Renders in the DetailPanel header next to the action chip.

---

## 4. WATCHLIST state

- [ ] Chip label: **"WATCHLIST"** in caps.
- [ ] Chip color: dusty purple (accent / `--color-accent`), `bg-accent-subtle`
      with `border-accent-30`.
- [ ] Visually distinct from:
  - [ ] CONDITIONAL (yellow / warning)
  - [ ] NO EDGE (light gray / surface-alt)
  - [ ] AVOID (red / error)
  - [ ] SELL (green / success)
- [ ] Score pill on a WATCHLIST row displays the raw score (e.g., 45 / 50) —
      not zeroed.
- [ ] The leaderboard `actionable / conditional` count does NOT include
      WATCHLIST rows.
  - Reproduce: a scan with `JNJ CONDITIONAL`, `QQQ WATCHLIST`, `XLF WATCHLIST`,
    `WMT SKIP` should show `0 actionable · 1 conditional`. The banner must NOT
    say "3 conditional".
- [ ] DetailPanel header on a WATCHLIST row shows the WATCHLIST chip.
- [ ] DetailPanel Position Construction block is hidden.
- [ ] DetailPanel renders the accent-purple Watchlist explanation block
      ("structure clean, but premium too thin").
- [ ] The IV/RV chart and Term Structure chart still render normally on a
      WATCHLIST row (the row remains informational, just not actionable).

---

## 5. Position Construction suppression

- [ ] **Visible** for: SELL, CONDITIONAL (NORMAL regime), with vrp_ratio ≥ 1.15.
- [ ] **Hidden** for: WATCHLIST, NO EDGE, AVOID (any regime), SKIP, NO DATA,
      and any row with `suppressedByScanQuality === true`.
- [ ] When hidden because of WATCHLIST: the watchlist explanation block
      replaces it.
- [ ] When hidden because of AVOID + DANGER: the red Avoid prose block
      replaces it.
- [ ] When hidden because of SKIP (earnings gate): the red Skip prose block
      replaces it, and the preGateScore is shown for monitoring.
- [ ] When hidden because of suppression: the red suppression diagnostic
      block replaces it.

---

## 6. ETF earnings exemption

(Defense-in-depth; no current production data violates this, but the guard
must exist.)

- [ ] In a normal scan, ETFs (SPY, QQQ, IWM, GLD, etc.) display in the
      `Earnings` column as "ETF", **never** as "Xd" or "TBD".
- [ ] An ETF with action SELL/CONDITIONAL/WATCHLIST is NEVER displayed as SKIP.
- [ ] If you manually patch the API response to include `earnings_dte: 5,
      is_etf: true` for an ETF row (e.g., via DevTools → Network → Override
      response), the ETF row STILL does not show as SKIP. This verifies the
      `!t.is_etf` guard added to `scoring.ts:35` after the regression test
      revealed the gap.

---

## Producing test scans

When the live API doesn't exhibit a state you need to verify:

### Force WATCHLIST on a non-WATCHLIST row

Backend response can be edited via DevTools → Network → "Override response":
- Change `vrp_ratio` to `1.05` and `recommendation` to `"WATCHLIST"`.
- The frontend should re-render with the WATCHLIST chip + explanation block.

### Force DEGRADED scan

Either:
- Lower `backend/scan_quality.py:NO_DATA_THRESHOLD` to `-1` and restart backend
  (revert when done).
- Or override the API response to include `scan_quality: "DEGRADED"` and
  `scan_quality_reason: "test reason"`.

### Force Thin Premium

Override response: set `vrp_ratio: 1.20` and `recommendation: "CONDITIONAL"`
on any ticker. The "Thin Premium" badge should appear next to its action chip.

---

## Acceptance criteria summary

A pass on this checklist (and the backend test suites) means:

1. WATCHLIST never appears as tradeable (banner counts and leaderboard
   header counts both exclude it).
2. Earnings / DANGER / NO DATA precedence is unchanged from pre-Phase-1.
3. Degraded scans cannot display actionable trades — the suppression banner
   is prominent and SELL/CONDITIONAL/WATCHLIST are visually downgraded.
4. Suppressed rows preserve their pre-suppression context for audit.
5. Position Construction is hidden whenever the row is non-tradeable.
6. ETFs are exempt from the earnings gate at all layers.
