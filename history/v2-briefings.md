# v2 Briefings — Shadow Divergence Analysis (Claude-written)

Narrative analysis of the v2-vs-v1 shadow divergence for the Theta Harvest v1→v2 build. Sister log to `daily-briefings.md` (v1 narrative) — this is its v2 analog, oriented toward the eventual Phase-B calibration of the FVRP dead-zone. One entry per trading day, descending order (newest first).

Written automatically by headless Claude in `automation/` — **advisory only**, Phase A of the v2 arc, changing no live decision. The deterministic data it reads lives in `v2-metrics-logs.md`.

---

## Update Protocol

**Trigger:** After `v2-metrics-logs.md` has the day's deterministic table, headless Claude writes the analysis (best-effort — a failure here never blocks the v1 history).

**Entry format:**
```
## YYYY-MM-DD (Day of week)

**Shadow summary:** [the deterministic summary line from v2-metrics-logs.md, reproduced VERBATIM]

[1 dense paragraph: which V2_STRICTER / V2_LOOSER cases matter (named, with FVRP/z/slope),
whether v2 is correctly vetoing or at risk of missing tradeable premium, and the FVRP /
index-gating / oscillation trend vs recent days]

**Calibration read:** [what the day implies for the Phase-B FVRP dead-zone quantile-match]
```

**Analysis should cover:**
- Whether v2's vetoes (V2_STRICTER) are saving bad sells or blocking good ones
- Any V2_LOOSER cases where v2 would allow what v1 gates
- FVRP / index-gating-rate / oscillation trend and warm coverage
- A concrete `**Calibration read:**` on whether the FVRP dead-zone bounds look too tight / too loose vs v1's realized eligibility

**Tone:** Concise, data-driven, opinionated. Reference specific tickers and numbers. The first line MUST match the deterministic shadow summary verbatim.

---

> **IMPORTANT:** Entries are in **descending order** (newest first). New entries go immediately below this line.

---
