---
last_verified: 2026-07-04
verified_against: c203544 (working tree — ships with the 2026-07 scoring update)
status: active
---

# ADR-012: RV Acceleration Is an Independent CAUTION Trigger (> 1.10)

## Context

The RV Acceleration status table (Excellent / Good / Acceptable / Caution / Avoid·Wait) has
always labeled accel 1.10–1.20 "Caution" and > 1.20 "Avoid/Wait", but the scorer only enforced
rising RV as a regime trigger when paired with IV Rank > 90. A ticker with strong VRP, high IV
percentile, and contango could therefore print SELL PREMIUM while its realized vol was spiking —
observed live on NFLX 2026-06-26 (score 67, SELL, accel 1.284).

Two independent backtests flagged the same hole: the 2026-06 quotes-based study
(`docs/qa/naked-put-backtest-report.md`) and the 2026-07 16-month study
(`docs/strategy-backtest-2026-07.md`), where SELL entries with accel > 1.10 ran PF ≈ 0.8
(negative average P/L) vs PF 1.8–4.3 for calmer entries. Mechanically this is expected: rising
realized vol is precisely what closes the VRP gap being sold.

## Decision

In `scorer.py` regime detection: `rv_accel > 1.10` forces **CAUTION** on its own (DANGER still
takes precedence). Effect: score ≥ 55 → REDUCE SIZE, else NO EDGE — a rising-RV name can no
longer print SELL. The threshold matches the status table's Acceptable/Caution boundary and the
existing `> 1.1` comparison style of the IV-Rank path.

## Alternatives Considered

**Gate at 1.20 (the Avoid/Wait line).** Backtest showed 1.10–1.20 entries were just as bad as
> 1.20 (PF 0.79 vs 0.81); gating only at 1.20 leaves half the identified leak open.

**Force AVOID (DANGER) instead of CAUTION.** Overreach — DANGER semantically means term-structure
inversion (systemic stress). CAUTION already blocks SELL and demands defined risk, which is the
documented intent of the Caution tier.

**Score-only fix (steepen the RV Stability component).** The component already zeroes at 1.15;
the problem is that 15 points of a 100-point additive score cannot veto. Regime is the veto layer.

## Consequences

**Makes easy:** The scanner now enforces its own documented guidance; the RV-Accel chip and the
recommendation can no longer contradict each other.

**Makes hard:** Slightly fewer SELL signals (~16% of SELL signal-days in the 2025–26 window).
Score continuity: recommendations shift from 2026-07-04 (logged in `references/change-logs.md`).

## Revisit If

- A full bear-market cycle shows the gate rejecting profitable recovery entries (fear-overshoot
  phase can have elevated accel while VRP is widest — the 2026-07 backtest could not test this).
- The RV-Accel status tier boundaries change — keep the trigger aligned with the
  Acceptable/Caution boundary.
