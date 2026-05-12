# Credit Put Spreads — Canonical Reference

> A defined-risk expression of the same volatility edge used by the Naked Puts tab.

This document is the single source of truth for the Credit Put Spreads (CPS) feature. It documents the **MVP universe, hard gates, construction filters, execution filters, ranking rule, action labels, multi-day confirmation, regime overlay, exit rules, and display conventions** that govern the CPS tab.

For the full build narrative (rationale, phasing, non-goals), see [`credit_put_spreads_build_plan.md`](./credit_put_spreads_build_plan.md).

---

## 1. Architectural principle

```text
Existing daily scan engine
    ↓
Existing volatility edge score (Base Edge Score)
    ↓
Existing hard gates and regime logic
    ↓
New spread-construction layer  ←  CPS adds only this
    ↓
Credit Put Spreads tab
```

- The existing volatility edge engine (`backend/scorer.py`, `backend/calculator.py`) is the source of truth.
- CPS does **not** introduce a separate scoring engine. There is no `60/30/10` weighting.
- Defined risk does **not** rescue a bad volatility regime — failing tickers do not get a CPS recommendation just because losses are capped.

---

## 2. MVP universe

```python
CPS_UNIVERSE = ["SPY", "QQQ", "IWM"]
```

Defined in [`backend/config.py`](../backend/config.py). The CPS pipeline filters to this list **before** any expensive construction runs.

Index ETFs only at MVP because:

- options chains are deep,
- strike grids are dense,
- both legs (short + long) execute reliably near mid,
- two-leg slippage is acceptable,
- defined-risk expression is most justified where notional/buying-power effects matter.

Extended universe (`CPS_UNIVERSE_EXTENDED = ["SPY", "QQQ", "IWM", "EEM", "TLT", "XLE"]`) is reserved for Phase 6 after replay confirms candidate quality.

The full 33-ticker Naked Puts universe (`NAKED_PUT_UNIVERSE`) is **not** used for CPS in MVP.

---

## 3. Filter first, rank second

CPS candidates are produced by:

1. **Universe filter** — ticker must be in `CPS_UNIVERSE`.
2. **Inherited base hard gates** — earnings, DANGER regime, negative VRP, weak VRP ratio, NO_DATA, RV shock, extreme skew.
3. **Construction filters** — DTE window, short delta band, long-leg below short, width sanity (ATR / expected-move aware), positive credit, credit-to-width minimum.
4. **Execution filters** — bid > 0, ask > bid, bid/ask ratio, open interest, volume on both legs.
5. **Regime overlay** (Phase 2) — VIX / VIX3M / VVIX, 60-day VRP z-score.
6. **Multi-day confirmation** — ticker-level eligibility streak ≥ 2 days for `SELL_CPS`.

Passing candidates are then **ranked by Base Edge Score**, with these tie-breakers:

| Tie-break order | Field |
|---|---|
| 1 | Higher `credit_to_width` |
| 2 | Better bid/ask quality (lower `bid_ask_ratio` average across legs) |
| 3 | Better RV Accel status (Excellent > Good > Acceptable > Caution > Avoid/Wait) |
| 4 | Cleaner term slope (further below 1.0) |

Construction and execution quality determine **whether** the edge can be expressed cleanly — they do not create the edge.

---

## 4. Inherited base hard gates

A ticker cannot receive a sellable CPS candidate if any of these fail (mirrors the Naked Puts engine; see [`scoring-and-strategy.md`](../context/1-domain/scoring-and-strategy.md)):

| Gate | Rule | Result |
|---|---|---|
| Earnings | `earnings_dte <= 14` (non-ETF) | `AVOID` |
| DANGER regime | `term_slope > 1.15` or ticker regime = DANGER | `AVOID` |
| Negative VRP | `vrp < 0` | `NO_EDGE` |
| Weak VRP ratio | `vrp_ratio < 1.15` | `NO_EDGE` |
| No data | IV or chain unavailable | `NO_DATA` |
| RV shock | `rv_accel > 1.20` | `WAIT` |
| Extreme skew | `skew > 20` | `AVOID` |

ETFs are exempt from the earnings gate. Since all MVP universe members are ETFs (SPY, QQQ, IWM), the earnings gate effectively never bites in MVP — but the rule is kept for the extended universe.

---

## 5. Construction targets

| Knob | Value | Constant |
|---|---:|---|
| Target DTE | 35 | `CPS_TARGET_DTE` |
| Min / max DTE | 30 / 45 | `CPS_MIN_DTE`, `CPS_MAX_DTE` |
| Target short delta | 0.20 | `CPS_TARGET_SHORT_DELTA` |
| Short delta band | 0.15 – 0.25 | `CPS_MIN_SHORT_DELTA`, `CPS_MAX_SHORT_DELTA` |
| Min credit-to-width for SELL | 25% | `CPS_MIN_CREDIT_TO_WIDTH` |
| Min credit-to-width for WATCH | 20% | `CPS_WATCH_MIN_CREDIT_TO_WIDTH` |
| High-credit-to-width warning | > 35% | `CPS_HIGH_CREDIT_TO_WIDTH_WARNING` |
| Width ATR multiplier | 0.75 | `CPS_WIDTH_ATR_MULTIPLIER` |
| Width / ATR sanity band | 0.75 – 1.50 | `CPS_MIN_WIDTH_ATR_RATIO`, `CPS_MAX_WIDTH_ATR_RATIO` |

### 5.1 Expiration selection

```text
Window:   30 ≤ DTE ≤ 45
Target:   closest to 35 DTE
```

If no expiration in window: `NO_DATA` (or `WATCH_CPS` with rejection reason if extending to the extended universe later).

### 5.2 Short put selection

```text
Band:     0.15 ≤ |delta| ≤ 0.25
Target:   closest to 0.20 |delta|
```

If no contract in band passes the liquidity filter: do not broaden — return `NO_DATA` with a clear rejection reason. MVP prioritises clean candidates over forcing spreads.

### 5.3 Long put selection — ATR / expected-move-aware width

```python
expected_move = spot * (iv_current / 100) * sqrt(dte / 365)
expected_move_lower = spot - expected_move

target_width = max(
    nearest_valid_strike_width,
    0.75 * atr14,
)
```

Constraints:

- long strike < short strike,
- net credit > 0,
- credit-to-width ≥ `CPS_WATCH_MIN_CREDIT_TO_WIDTH` (20%) — anything below is rejected,
- width-to-ATR within 0.75 – 1.50 sanity band,
- long leg passes execution filters.

For each short put, evaluate a handful of lower long puts around target width and pick the best candidate that passes all filters.

### 5.4 Spread economics

```python
short_mid = (short_bid + short_ask) / 2
long_mid  = (long_bid + long_ask) / 2
net_credit       = short_mid - long_mid
width            = short_strike - long_strike
max_loss         = width - net_credit
credit_to_width  = net_credit / width
breakeven        = short_strike - net_credit
```

Reject if any of:

- `net_credit <= 0`
- `width <= 0`
- `max_loss <= 0`
- `credit_to_width < CPS_WATCH_MIN_CREDIT_TO_WIDTH` (0.20)

For `SELL_CPS`: require `credit_to_width >= 0.25`.
For `WATCH_CPS`: allow `credit_to_width >= 0.20` if all other hard filters pass.

If `credit_to_width > 0.35`, attach this warning (explicit `warnings[]` entry, never an undefined score adjustment):

> *High credit/width may indicate elevated tail risk. Verify regime, skew, and RV Accel before acting.*

---

## 6. Execution quality filters (both legs)

| Metric | Hard reject | Preferred |
|---|---:|---:|
| Bid > 0 | required | required |
| Ask > bid | required | required |
| `bid_ask_ratio = (ask - bid) / mid` | < 20% | < 15% |
| Open interest | > 100 | > 500 |
| Volume | > 25 | > 100 |
| Mid price | finite | finite |

Credit spreads are more sensitive to execution slippage than naked puts because both entry **and** exit require two legs. A bad long leg silently destroys the credit/width economics on exit. **Never** use `spread_ratio` for the bid/ask field — it conflicts with put-spread width, credit spread, term spread, and vol-spread terminology.

---

## 7. Action labels

| Action | Meaning |
|---|---|
| `SELL_CPS` | Passes all gates + construction + execution + 2-day ticker-level confirmation |
| `WATCH_CPS` | Close but unconfirmed or marginally clean (e.g. 20–25% credit/width, 1-day eligibility) |
| `WAIT` | Setup has some edge but environment (RV shock, regime overlay) is not clean enough |
| `AVOID` | Hard gate failed |
| `NO_EDGE` | Base volatility edge insufficient (Base Score < 60) |
| `NO_DATA` | Chain or quote data unavailable |

Marginal `WATCH_CPS` candidates should **not** be shown just to fill the table. If nothing passes today, the correct output is an empty list.

---

## 8. Multi-day SELL confirmation

Multi-day confirmation is tracked on **two independent axes**:

| Field | Purpose | Used as a gate? |
|---|---|---|
| `consecutive_sell_days` | Ticker-level eligibility streak — did the ticker pass all CPS filters today, and yesterday? | **YES.** `SELL_CPS` requires `consecutive_sell_days >= 2`. |
| `exact_spread_consecutive_days` | Same strike pair (short + long) eligible for ≥ N consecutive days | Display-only context. **Never** the sole gate. |

Strikes shift day-to-day with the chain (delta-target may snap to a different strike as the underlying moves). Requiring exact-spread persistence would produce false negatives — a ticker can be reliably CPS-eligible while the specific 500/495P pair rotates to 502/497P overnight. Ticker-level tracking captures the underlying signal stability; exact-spread tracking lets the trader see when one strike pair is unusually persistent.

Implementation (Phase 3):
- `cps_candidate_history` table records `(scan_date, ticker, expiration, short_strike, long_strike, passed_filters)` per scan.
- `get_consecutive_sell_days(ticker)` walks back from the latest scan and counts consecutive days where any spread on that ticker passed all SELL filters.
- `get_consecutive_exact_spread_days(ticker, expiration, short_strike, long_strike)` does the same for the exact key.

Until persistence ships, all candidates render as `WATCH_CPS` (today qualified, no prior history).

---

## 9. Regime overlay (VIX / VIX3M / VVIX)

Implementation: `backend/regime_overlay.py` (Phase 2). Data source: yfinance (`^VIX`, `^VIX3M`, `^VVIX`).

| Overlay rule | Trigger | Effect |
|---|---|---|
| VIX/VIX3M backwardation | `vix > vix3m` | Market-wide caution; downgrade `SELL_CPS` → `WATCH_CPS` |
| VVIX caution | `110 < vvix ≤ 130` | Caution; warning surfaced, candidates still pass |
| VVIX danger | `vvix > 130` | Avoid new `SELL_CPS` entries; downgrade to `WATCH_CPS` |
| VRP z-score floor | 60-day VRP z-score < +0.5 | Downgrade `SELL_CPS` → `WATCH_CPS` |

### 9.1 UNKNOWN status

If yfinance cannot fetch any of the three feeds (weekend, API failure, network), the overlay returns:

```python
RegimeOverlay(status="UNKNOWN", vix=None, vix3m=None, vvix=None,
              warnings=["VIX/VIX3M/VVIX data unavailable — overlay disabled."])
```

`UNKNOWN` does **not** block candidates. It surfaces a warning in the API response and in the frontend banner so the trader can apply their own judgement. The other CPS filters still gate as normal.

### 9.2 Status language

| VVIX | Status |
|---:|---|
| ≤ 110 | Normal |
| 110 – 130 | Caution: vol-of-vol elevated |
| > 130 | Avoid / wait: vol-of-vol extreme |

Never describe VVIX as a position-sizing signal. It is an **environment** signal — same framing as RV Accel Status (Phase 2C).

---

## 10. Exit rules

Pure backend logic in `backend/spread_exit_evaluator.py` (Phase 2). Even without a full Journal module, the rules must ship now because anyone trading a CPS recommendation needs an exit recipe.

| Exit | Trigger | Action |
|---|---|---|
| Profit target | Current mark ≤ 50% of original credit (`CPS_PROFIT_TARGET_FRAC`) | `CLOSE_PROFIT_TARGET` |
| Defensive mark | Current mark ≥ 2× original credit (`CPS_DEFENSIVE_MARK_MULTIPLE`) | `CLOSE_DEFENSIVE` |
| Short-strike breach | Spot trades below short strike | `CLOSE_DEFENSIVE` |
| Time exit | DTE ≤ 21 (`CPS_TIME_EXIT_DTE`) | `CLOSE_TIME` |
| Pin risk | DTE ≤ 2 AND `|spot - short_strike| ≤ max(0.50, 0.001 × spot)` | `CLOSE_PIN_RISK` |
| Event risk | Earnings or known binary event ≤ 14 DTE for non-ETF | `CLOSE_EVENT_RISK` |
| Regime flip | Ticker or market flips to DANGER | `CLOSE_DEFENSIVE` |
| None of above | — | `HOLD` |

### 10.1 Pin-risk rule (explicit)

Credit Put Spreads are multi-leg defined-risk positions. Pin risk at expiry can produce uncovered short stock if only one leg assigns. The threshold scales with spot:

```python
pin_threshold = max(CPS_PIN_RISK_MIN_DISTANCE, CPS_PIN_RISK_SPOT_PCT * spot)
                # max(0.50, 0.001 * spot)
```

For a $500 underlying, that's $0.50. For a $1000 underlying, that's $1.00. The frontend renders:

> *Pin Risk: underlying is close to the short strike near expiration. Close before expiry to avoid assignment/settlement complexity.*

---

## 11. Display conventions

Be explicit about per-share vs per-contract values everywhere in the UI:

| Field | Display convention |
|---|---|
| Net credit | Per share, e.g. `$1.25` |
| Width | Per share, e.g. `$5.00` |
| Max loss | Per share by default, per-contract tooltip optional |
| Credit / width | Percentage, e.g. `25%` |
| Breakeven | Per-share price |
| P/L dollar amounts | Per spread contract (×100) when shown in dollars |

Example detail-panel block:

```text
Sell 500P / Buy 495P
Width:           $5.00
Credit:          $1.25
Max Loss:        $3.75 per share / $375 per 1-lot
Credit/Width:    25%
Breakeven:       $498.75
```

---

## 12. What CPS is not

- Not a separate edge engine. Same VRP / IV percentile / term / RV / skew score.
- Not a rescue for hostile regimes. DANGER blocks CPS the same way it blocks naked puts.
- Not a position-sizing prescription. The dashboard never says "Full / Half / Quarter." Position size is the trader's decision (record in the trade journal, when it exists).
- Not for the full 33-ticker universe. MVP is SPY / QQQ / IWM only.
- Not iron condors, strangles, jade lizards, calendars, or diagonals. Phase 6 may add structures — MVP does not.

---

## 13. Field reference (canonical names)

| Concept | Field name | Notes |
|---|---|---|
| Bid/ask quote width | `bid_ask_ratio` | **Never** `spread_ratio` |
| Put-spread economics | `credit_to_width` | Per-share ratio, 0–1 |
| Width sanity | `width_to_atr` / `width_to_expected_move` | ATR / EM relative |
| Ticker-level streak | `consecutive_sell_days` | Gates `SELL_CPS` |
| Exact-spread streak | `exact_spread_consecutive_days` | Display only |
| Regime overlay | `regime_overlay_status` | `NORMAL` / `CAUTION` / `DANGER` / `UNKNOWN` |

Pydantic models: [`backend/models.py`](../backend/models.py) — `CreditPutSpreadLeg`, `CreditPutSpreadCandidate`, `RegimeOverlay`, `CreditPutSpreadsResponse`, `SpreadExitDecision`.

TypeScript types: [`frontend/src/lib/types.ts`](../frontend/src/lib/types.ts) — matching interfaces with camelCase field names.

---

## 14. Final principle

> Credit Put Spreads should make the app more disciplined, not more active.
>
> If the volatility edge, regime, liquidity, and spread economics do not all align cleanly, the correct output is *"No Credit Put Spread candidates today."*
