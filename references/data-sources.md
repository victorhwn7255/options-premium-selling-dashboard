# Data Sources & Phase 0 Decision Record

Phase 0 (v2 build) artifact. Two parts: **A** locks the four human decisions D1–D4; **B** is the
endpoint-probe checklist (0.1–0.3) that needs a live `MARKETDATA_TOKEN` — staged ready-to-run so no
API credits are spent until you (or a token-holding session) execute them.

Authority reminder: the **spec** (`theta-harvest-v2-spec.md`) wins on any number; **CONFIG**
(`theta_harvest_core.py`) is the single home for every `[PROVISIONAL]` constant (prohibition **P3**).

---

## A. Decisions D1–D4

| # | Decision | Chosen | Home / status |
|---|----------|--------|---------------|
| **D1** | `margin_alpha` (initial-margin coefficient) | **0.20 (Reg-T)** | ✅ in `CONFIG["margin_alpha"]` (already present). Switch to `0.15` only on an IBKR portfolio-margin account. |
| **D2** | Kelly fraction φ | **0.25 (quarter-Kelly)** | ✅ in `CONFIG["kelly_fraction"]`. Default holds until the trade log contains a genuine vol event; revisit is a Phase F decision, not a silent edit. |
| **D3** | T2 exit-pricing mode | **Model-priced (BSM) first pass** | Recorded. Historical-chain pricing is the later, more expensive validation; the model-priced pass is cheap and unblocks T2 in Phase F. No CONFIG constant — it is a measurement-harness mode (Phase D/F). |
| **D4** | Earnings-verification fallback | **Option B — degrade the single-name sleeve to index-only when earnings data is genuinely stale/unverifiable (scoped)** | Rule lands in **strategy_v2.md §3.4 + a backend `CONFIG` flag, same commit, in Phase B** (where the earnings-eligibility code lives). See the spec-text below. |

### D4 — the rule to implement in Phase B (verbatim intent)

**Why B over A (FMP+Yahoo-authoritative):** the risk is extremely asymmetric. Missing one earnings
date on a naked put is an overnight-gap loss that can end the account; skipping a few single-name
trades on a degraded-data day is a tiny, recoverable cost — and single-name VRP is the *weak* sleeve
(diluted vs. the index; ~70% measured). The return engine (index/ETF book) has **no earnings risk**
(ETFs are exempt), so B costs the engine nothing; it only pauses the low-value satellite sleeve when
the data can't be trusted. B is also the faithful reading of §3.4's own "unverified = gated" stance.

**Scoping (so B doesn't over-gate):** a single name degrades to ineligible only when **(a)** its next
earnings date cannot be freshly verified (FMP down / stale cache / FMP↔Yahoo disagreement) **AND
(b)** the name is within a plausible earnings window (≈ within a quarter of its known cadence). A name
whose next earnings is confidently far out is **not** gated on a transient feed hiccup. When data is
fresh, the existing FMP-primary + Yahoo-cross-check path (Option A's mechanism) is used as today.

**Phase B deliverable (same commit, per Fix 7):**
- `strategy_v2.md §3.4` — add the fallback paragraph above.
- backend `CONFIG` — add the governing flag, e.g. `earnings_fallback = "degrade_to_index_when_stale"`
  (enum: `degrade_to_index_when_stale` | `fmp_yahoo_authoritative`), plus a staleness horizon constant.
- The flag is **not** added to `theta_harvest_core.py` now: that file is the pure-math golden master and
  has no earnings module, so a flag there would be dead config. It enters with the earnings code in B.

> Background: MarketData's earnings endpoint (`/v1/stocks/earnings/`) is premium-gated (402) and does
> not store historical dates, which is why FMP is the primary and Yahoo the cross-check. See CLAUDE.md
> memory and `_get()`'s 402 short-circuit.

### 0.7 — dependency decision (recorded here for traceability)

**Decision: add `pandas>=2.2.2` + `scipy>=1.13.0` to `backend/requirements.txt`** (done) rather than
port the reference's ~5 call sites to numpy + `math.erf`.

- **scipy** usage is only `norm.cdf` / `norm.ppf(0.95)` (BSM + PSR) — trivially portable and exact via
  `math.erf`; kept as a dependency for now (porting is a later, optional image-size optimization, not
  worth the risk in Phase 0 — YAGNI).
- **pandas** usage is the block-bootstrap `groupby` (`kelly_base`) and the **bias-corrected sample
  skew/kurt** feeding PSR (`psr`). A naive numpy re-implementation of skew/kurt would silently diverge
  from pandas' adjusted Fisher–Pearson formulas — exactly the kind of drift that breaks the "1e-9
  fixture" gate (0.5). Keeping pandas preserves golden-master fidelity 1:1.
- Rationale: **Simplicity First + zero divergence risk** beats shaving a Docker layer on a Lightsail
  backend that already ships numpy. Revisit only if image size becomes a real constraint.

---

## B. Endpoint probes — 0.1 ✅ / 0.3 ✅ run · 0.2 pending

**Token status (2026-07-05, RESOLVED):** confirmed with the user — the `~/Projects/option-harvest/.env`
token (prefix `S3dOUG…`) is an **intentional MarketData Free/Trial token**, and that's the accepted
operating model. It gives **100,000 requests/day** (plenty) but a **1-year historical cap** (402 on older
data) and **no indices** (`no_data`). The user **rotates the trial token ~monthly** so it stays valid.
Implications for v2:
- **Request volume** is a non-issue (100k/day ≫ the ~100–200/day the scan needs).
- **Indices** are moot — VIX-family comes from yfinance (`regime_overlay`); the Cboe **PUT** benchmark comes
  from the weekly Cboe CSV.
- **Deep history** (>1yr) is unavailable, so the forecaster's *initial* backfill is limited to ~1yr — but
  Phase A persists OHLC into **our own store** and captures forward, so accumulated history grows past the
  trial's rolling 1-year window over time, independent of any token swap. A paid plan is an optional later
  boost for a stronger initial calibration, not a requirement.
- ⚠ **Ops:** the monthly rotation must also update the **prod (Lightsail) env + reload the backend** (the
  token the live daily scan uses), or the production scan will 402 mid-cycle when the old trial lapses.

These are **metered** MarketData.app calls; results recorded in the tables below.

Auth (either form): header `Authorization: Bearer $MARKETDATA_TOKEN`, or `?token=$MARKETDATA_TOKEN`.

### 0.1 — `/v1/indices/` availability (VIX confirmed; probe the rest)

Drives the Phase D benchmark plan (Cboe PUT) and any VVIX/VIX-term regime inputs.

```bash
set -a; . ./.env; set +a          # load MARKETDATA_TOKEN from repo-root .env
for S in VIX VIX3M VVIX VIX9D PUT; do
  echo "== $S =="
  curl -s "https://api.marketdata.app/v1/indices/quotes/$S/?token=$MARKETDATA_TOKEN" | head -c 400; echo
done
```

| Symbol | Available? | Notes |
|--------|-----------|-------|
| VIX    | ❌ `no_data` | on the local `.env` token |
| VIX3M  | ❌ `no_data` | " |
| VVIX   | ❌ `no_data` | " |
| VIX9D  | ❌ `no_data` | " |
| PUT (Cboe PutWrite) | ❌ `no_data` | → use the weekly Cboe CSV import in Phase D |

**Finding (2026-07-05, ran via local `.env`):** every index returned `{"s":"no_data"}`, and the 0.3
candles probe revealed this token is **Free/Trial** (`"Free/Trial users can only access up to 1 year of
data"`) — so `/v1/indices/` simply isn't entitled here. Two consequences: (1) the app already sources
**VIX / VIX3M / VVIX from yfinance** (`regime_overlay`), so MarketData indices are **not needed** for the
regime inputs; (2) the **Cboe PUT** benchmark for Phase D should come from the **weekly Cboe CSV import**,
not this endpoint. ⚠ **Re-verify against the production token** — if prod runs a paid plan with indices
entitlement this could change, but the yfinance + CSV path makes it moot either way.

### 0.2 — chain-endpoint billing (credits per contract returned)

**Measured live (2026-07-05) via the `x-api-ratelimit-consumed` header** — no dashboard needed:

```bash
curl -sD /tmp/h -o /dev/null -H "Authorization: Bearer $MARKETDATA_TOKEN" \
  "https://api.marketdata.app/v1/options/chain/SPY/?dte=45"; grep -i ratelimit-consumed /tmp/h
```

| Call | Cost | Detail |
|------|------|--------|
| Quote | **0 credits** | free |
| Daily candles | **1 credit / call** | returns up to 1 yr of bars for 1 credit |
| Option chain | **1 credit per contract returned** | metering is per-contract |
| SPY ~45 DTE chain | 490 credits | 490 contracts |
| SPY full 12-mo chain | ~10,375 credits | ~10,600 contracts |

**Implications:** (1) Phase E's ≤110-DTE narrowing is a real, **linear** per-contract saving. (2) Chains
dominate quota; candles/quotes are ~free — fetch candles for a wide universe cheaply. (3) With a 100k/day
trial limit, a **surplus-quota daily capture** is viable: bounded chains (≤120 DTE, ±20% strikes) for the
33-name universe (~13k credits) + full 6–12-mo chains for the liquid core (~20–45k) ≈ 35–60k/day, stored
forward into our own chain-snapshot store (deep history is uncapturable retroactively, so forward-accumulate
what's expensive to buy). Folded into Phase A as "OHLC **+ chain-snapshot** store." Guard: storage grows
~12M rows/yr — store efficiently; skip the deep-OTM/far-dated tail unless wanted for research.

### 0.3 — daily candles honor `adjustsplits=true`

Regression check that split adjustment is applied, so RV/Yang-Zhang aren't corrupted by raw split
jumps. Use a known post-split ticker (NVDA 10:1 2024-06, AAPL 4:1 2020-08) with NFLX as the
no-recent-split control.

```bash
# fetch a tight window SPANNING each split; adjusted => continuous, unadjusted => Nx cliff
curl -s -H "Authorization: Bearer $MARKETDATA_TOKEN" \
  "https://api.marketdata.app/v1/stocks/candles/D/AAPL/?from=2020-08-24&to=2020-09-04&adjustsplits=true"
# (NVDA 2024-06 / NFLX blocked below by the 1-yr Free/Trial history cap)
```

| Ticker | Split-adjusted? | Notes |
|--------|-----------------|-------|
| AAPL   | ✅ **yes** | across the 4:1 on 2020-08-31 closes stay ~121–131 (max day/day ratio 1.04, min 0.92) — no 4× cliff |
| NVDA   | — not fetched | 1-yr Free/Trial history cap (2024-06 > 1yr old) — a history limit, **not** a split problem |
| NFLX   | — not fetched | same cap; control unneeded once AAPL confirmed adjustment |

**Finding:** `adjustsplits=true` **works** — AAPL's series is continuous through its 4:1 split (a raw
series would jump ~4×). Split adjustment is a data-formatting feature, not plan-gated, so this holds for
the prod token too. Phase A's Yang-Zhang RV can trust the candle OHLC as split-adjusted.
