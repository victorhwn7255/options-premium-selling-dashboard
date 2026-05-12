# Credit Put Spreads Build Plan — Updated Correct Version

## Status

**Phases 1–5 complete (2026-05-12).** Shipped as MVP:

| Phase | Scope | Status |
|---|---|---|
| 1 | Product spec & data contract — config constants, models, types, canonical reference doc | ✅ |
| 2 | Backend logic — `spread_builder.py`, `regime_overlay.py`, `spread_exit_evaluator.py` + 58 unit tests | ✅ |
| 3 | API + persistence — `cps_candidate_history` + `cps_scan_responses` tables, `GET /api/credit-put-spreads/latest`, scan-loop integration + 19 tests | ✅ |
| 4 | Frontend — `TabBar`, `CreditPutSpreadsTab`, table + detail panel + economics card + action badge + Journal placeholder; `page.tsx` integration | ✅ |
| 5 | Docs, QA, release notes (this section) | ✅ |

Acceptance summary: 115 / 115 backend tests passing, frontend `tsc --noEmit` clean, production `npm run build` succeeds, historical replay byte-stable (Section G empty — no Naked Puts regression). See [`references/phase5-credit-put-spreads-completion-report.md`](./phase5-credit-put-spreads-completion-report.md) for the full release report.

The original plan that follows below is the canonical design document. All five phases were executed against it without scope creep. Phase 6 follow-ups (Journal trade entry, portfolio vega, universe expansion, historical replay tuning) remain open and listed in §Optional Phase 6 below.

---

## Project

**Options Premium Selling Dashboard**  
Feature: Add a new **Credit Put Spreads** tab alongside the existing **Naked Puts** workflow.

Recommended tab structure:

```text
Naked Puts | Credit Put Spreads | Journal (Coming Soon)
```

The **Market Regime** should remain a persistent banner/context component above the tabs, not a separate tab.

---

## Version Notes

This is the revised build plan. It updates the original plan with the following corrections:

1. Constrain the Credit Put Spreads MVP universe to index ETFs: **SPY, QQQ, IWM**.
2. Treat Credit Put Spreads as a **defined-risk expression of the same edge**, not a separate edge engine.
3. Replace the arbitrary `60/30/10` CPS scoring formula with **binary construction/execution filters**, then rank passing candidates by the existing **Base Edge Score**.
4. Move **ATR / expected-move-based width selection** into MVP instead of deferring it.
5. Add explicit **exit and management rules** before shipping the tab.
6. Add **multi-day SELL confirmation** to avoid noisy one-day signals.
7. Add **market regime overlays** such as VIX/VIX3M and VVIX as environment filters.
8. Rename quote-spread fields to avoid ambiguity: use `bid_ask_ratio`, not `spread_ratio`.
9. Keep position sizing out of the dashboard recommendation language.
10. Defer full portfolio-level vega tracking to the optional phase unless Journal / open-position tracking already exists.

---

## 0. Product Principle

The application is primarily a **naked/cash-secured put selling dashboard**.

The Credit Put Spreads feature should not replace, weaken, or clutter the existing Naked Puts workflow.

The correct architecture is:

```text
Existing daily scan engine
    ↓
Existing volatility edge score
    ↓
Existing hard gates and regime logic
    ↓
New spread-construction layer
    ↓
Credit Put Spreads tab
```

The existing volatility edge engine remains the source of truth.

Credit Put Spreads are a **defined-risk expression of the same put-selling edge**, not a separate unrelated strategy.

Defined risk does **not** rescue a bad volatility regime.

If the underlying fails the base edge gates, the system should not recommend a Credit Put Spread just because the loss is capped.

---

## 1. Strategic Intent

### Primary Strategy

The primary strategy remains:

> Sell naked/cash-secured puts on high-quality, liquid stocks and ETFs that we do not mind owning.

### Secondary Strategy

Credit Put Spreads should be used when:

- The same volatility edge exists.
- The underlying belongs to the approved CPS universe.
- The broad regime is not hostile.
- A defined-risk expression is preferable.
- Spread economics pass strict hard filters.
- Execution quality is strong enough to avoid losing the edge to slippage.

### Non-goals for MVP

Do **not** add the following in the initial implementation:

- Iron condors
- Jade lizards
- Short strangles
- Calendar spreads
- Diagonal spreads
- Complex multi-leg optimizers
- Kelly sizing
- Automated position sizing recommendations
- Broker integration
- Full portfolio risk engine
- Full trade journal implementation

Keep the app focused:

```text
Naked Puts first.
Credit Put Spreads second.
Journal later.
```

---

## 2. Existing System Assumptions

The current app already has most of the infrastructure required for Credit Put Spreads.

| Existing capability | Needed for CPS? | Notes |
|---|---:|---|
| Stock snapshot fetch | Yes | Needed for spot price |
| Daily bars | Yes | Needed for RV, ATR, expected-move context |
| Options chain fetch | Yes | Needed for short and long put legs |
| IV calculation | Yes | Base edge input |
| RV calculation | Yes | Base edge input |
| VRP calculation | Yes | Core edge input |
| Term structure | Yes | Regime / danger gate |
| RV Acceleration | Yes | Volatility environment cleanliness |
| Skew | Yes | Put demand / tail-risk signal |
| Earnings date | Yes | Hard event-risk gate |
| Liquidity filter | Yes | Needed per leg for CPS |
| Composite score | Yes | Base Edge Score |
| Regime detection | Yes | Used to allow/watch/avoid |
| FastAPI backend | Yes | Add CPS builder + endpoint |
| Next.js frontend | Yes | Add new tab and table |

---

## 3. Core Design Decision: Filter First, Rank Second

### Do not create a separate volatility edge engine

The existing score remains the **Base Edge Score**:

```text
Base Edge Score =
  VRP Quality
+ IV Percentile
+ Term Structure
+ RV Stability
+ Skew
```

Credit Put Spread candidates should be generated only after:

1. the ticker passes base hard gates,
2. the ticker belongs to the CPS universe,
3. the spread construction passes hard filters,
4. execution quality passes hard filters,
5. multi-day SELL confirmation is satisfied for final SELL labeling.

### Updated ranking method

Do **not** use the original arbitrary formula:

```text
CPS Score = 60% Base Edge Score
          + 30% Spread Construction Score
          + 10% Execution Quality Score
```

Instead:

```text
1. Apply hard gates.
2. Apply construction filters.
3. Apply execution filters.
4. Rank passing candidates by Base Edge Score.
5. Use credit/width, RV Accel status, and bid/ask quality as tie-breakers.
```

### Rationale

The volatility edge comes from the same structural source as Naked Puts: **implied volatility being rich relative to realized volatility under supportive market structure**.

Spread construction and execution quality do not create the edge. They only decide whether the edge can be expressed cleanly as a defined-risk spread.

Therefore, construction and execution should mostly be **hard pass/fail filters**, not a separate weighted scoring engine.

---

## 4. MVP Universe Constraint

### Required MVP universe

Add a configurable CPS universe:

```python
CPS_UNIVERSE = ["SPY", "QQQ", "IWM"]
```

This should be defined in a config file or constants file, not hardcoded inside UI components.

Suggested locations:

```text
backend/config.py
backend/settings.py
backend/spread_builder.py  # acceptable for first pass, but config is preferred
```

### Why constrain the MVP universe?

Credit Put Spreads require stronger liquidity than Naked Puts because both legs must be tradable:

- short put leg must be liquid,
- long put leg must be liquid,
- net spread must be fillable near mid,
- slippage must not destroy credit/width economics.

For MVP, index ETFs are preferred because:

- options chains are deeper,
- strike grids are denser,
- long-leg execution is more reliable,
- two-leg slippage is lower,
- defined-risk execution is more justified where notional / buying-power effects are more meaningful.

### Optional later expansion

Only after data quality is verified, consider expanding to:

```python
CPS_UNIVERSE_EXTENDED = ["SPY", "QQQ", "IWM", "EEM", "TLT", "XLE"]
```

Do not run CPS construction across the full 33-name Naked Puts universe in MVP.

---

# Phase 1 — Product Spec and Data Contract

## Goal

Define the Credit Put Spreads feature clearly before touching calculation logic or UI.

This phase creates the shared contract for backend, frontend, and coding agents.

---

## 1.1 UI Information Architecture

Implement the tab structure:

```text
Naked Puts | Credit Put Spreads | Journal (Coming Soon)
```

### Tab behavior

| Tab | Purpose |
|---|---|
| Naked Puts | Existing main dashboard for naked/cash-secured put candidates |
| Credit Put Spreads | New defined-risk spread candidate board |
| Journal (Coming Soon) | Disabled or placeholder tab for future trade tracking |

### Market Regime

Do not create a separate Market Regime tab.

Market Regime should remain a banner above the tabs.

Suggested layout:

```text
--------------------------------------------------
Market Regime Banner
THE PLAYOFFS | Avg VRP | Avg Term Slope | RV Accel Status | Tradeable Count
--------------------------------------------------

[Naked Puts] [Credit Put Spreads] [Journal (Coming Soon)]
```

---

## 1.2 CPS Candidate Model

Add or plan new models in:

```text
backend/models.py
```

### Important naming rule

Do not use `spread_ratio` for bid/ask quote width.

Use:

```python
bid_ask_ratio
```

or:

```python
quote_spread_ratio
```

Preferred: `bid_ask_ratio`.

This avoids confusion with:

- put spread width,
- credit spread,
- term spread,
- volatility spread.

### Suggested backend model shape

```python
from typing import Optional, List
from pydantic import BaseModel


class CreditPutSpreadLeg(BaseModel):
    strike: float
    expiration: str
    dte: int
    delta: Optional[float] = None
    bid: float
    ask: float
    mid: float
    iv: Optional[float] = None
    theta: Optional[float] = None
    vega: Optional[float] = None
    open_interest: Optional[int] = None
    volume: Optional[int] = None
    bid_ask_ratio: Optional[float] = None


class CreditPutSpreadCandidate(BaseModel):
    ticker: str
    spot: float

    action: str
    base_score: float
    rank_score: float  # usually same as base_score after hard filters
    regime: str

    expiration: str
    dte: int

    short_put: CreditPutSpreadLeg
    long_put: CreditPutSpreadLeg

    width: float
    net_credit: float
    max_loss: float
    credit_to_width: float
    breakeven: float

    atr14: Optional[float] = None
    expected_move: Optional[float] = None
    expected_move_lower: Optional[float] = None
    width_to_atr: Optional[float] = None
    width_to_expected_move: Optional[float] = None

    vrp: Optional[float] = None
    vrp_ratio: Optional[float] = None
    vrp_zscore_60d: Optional[float] = None
    iv_percentile: Optional[float] = None
    term_slope: Optional[float] = None
    rv_accel: Optional[float] = None
    rv_accel_status: Optional[str] = None
    skew: Optional[float] = None
    earnings_dte: Optional[int] = None

    consecutive_sell_days: int = 0

    vix: Optional[float] = None
    vix3m: Optional[float] = None
    vvix: Optional[float] = None
    regime_overlay_status: Optional[str] = None

    notes: List[str] = []
    warnings: List[str] = []
    rejection_reasons: List[str] = []
```

---

## 1.3 Frontend Types

Add corresponding TypeScript interfaces in:

```text
frontend/src/lib/types.ts
```

Suggested shape:

```ts
export interface CreditPutSpreadLeg {
  strike: number;
  expiration: string;
  dte: number;
  delta?: number;
  bid: number;
  ask: number;
  mid: number;
  iv?: number;
  theta?: number;
  vega?: number;
  openInterest?: number;
  volume?: number;
  bidAskRatio?: number;
}

export type CreditPutSpreadAction =
  | "SELL_CPS"
  | "WATCH_CPS"
  | "WAIT"
  | "AVOID"
  | "NO_EDGE"
  | "NO_DATA";

export interface CreditPutSpreadCandidate {
  ticker: string;
  spot: number;
  action: CreditPutSpreadAction;
  baseScore: number;
  rankScore: number;
  regime: string;

  expiration: string;
  dte: number;

  shortPut: CreditPutSpreadLeg;
  longPut: CreditPutSpreadLeg;

  width: number;
  netCredit: number;
  maxLoss: number;
  creditToWidth: number;
  breakeven: number;

  atr14?: number;
  expectedMove?: number;
  expectedMoveLower?: number;
  widthToAtr?: number;
  widthToExpectedMove?: number;

  vrp?: number;
  vrpRatio?: number;
  vrpZscore60d?: number;
  ivPercentile?: number;
  termSlope?: number;
  rvAccel?: number;
  rvAccelStatus?: string;
  skew?: number;
  earningsDte?: number;

  consecutiveSellDays: number;

  vix?: number;
  vix3m?: number;
  vvix?: number;
  regimeOverlayStatus?: string;

  notes: string[];
  warnings: string[];
  rejectionReasons: string[];
}
```

---

## 1.4 CPS Action Labels

Use structure-specific labels.

| Action | Meaning |
|---|---|
| `SELL_CPS` | Candidate passes all gates, construction filters, execution filters, and confirmation requirement |
| `WATCH_CPS` | Candidate is close but not yet confirmed or not clean enough for SELL |
| `WAIT` | Setup has some edge but environment is not clean enough |
| `AVOID` | Hard gate failed |
| `NO_EDGE` | Base volatility edge is insufficient |
| `NO_DATA` | Required chain / quote data is unavailable |

### Recommended thresholds

| Label | Required condition |
|---|---|
| `SELL_CPS` | Base Score ≥65, all filters pass, consecutive SELL days ≥2 |
| `WATCH_CPS` | Base Score ≥60, construction/execution filters pass or nearly pass, no hard gate failure |
| `NO_EDGE` | Base Score <60 |
| `AVOID` | Hard gate failure |
| `WAIT` | Regime overlay or RV Accel says wait, but not full avoid |

Do not show marginal low-quality WATCH candidates just because the tab has space.

---

## 1.5 Display Convention

Be explicit about per-share versus per-contract values.

| Field | Display convention |
|---|---|
| Net credit | Per share, e.g. `$1.25` |
| Width | Per share, e.g. `$5.00` |
| Max loss | Per share by default, with optional per contract tooltip |
| Credit / width | Percentage, e.g. `25%` |
| Breakeven | Per share price |
| P/L rules | Per spread contract when referencing dollars |

Example:

```text
Sell 500P / Buy 495P
Width: $5.00
Credit: $1.25
Max Loss: $3.75 per share / $375 per 1-lot
Credit/Width: 25%
Breakeven: $498.75
```

---

## Phase 1 Acceptance Criteria

- Tab structure is agreed: `Naked Puts | Credit Put Spreads | Journal (Coming Soon)`.
- CPS MVP universe is explicitly constrained to `SPY`, `QQQ`, `IWM`.
- CPS candidate data model is defined.
- `bid_ask_ratio` naming is used instead of `spread_ratio`.
- CPS labels are structure-specific.
- CPS rank is defined as Base Edge Score after binary filters, not arbitrary 60/30/10 scoring.
- Per-share versus per-contract display convention is documented.

---

# Phase 2 — Backend CPS Builder, Filters, Regime Overlays, and Exit Rules

## Goal

Create the backend logic that builds, filters, ranks, and manages Credit Put Spread candidates.

This phase should produce a reliable candidate list before any frontend work begins.

---

## 2.1 Add CPS Configuration

Add configuration constants:

```python
CPS_UNIVERSE = ["SPY", "QQQ", "IWM"]

CPS_TARGET_DTE = 35
CPS_MIN_DTE = 30
CPS_MAX_DTE = 45

CPS_TARGET_SHORT_DELTA = 0.20
CPS_MIN_SHORT_DELTA = 0.15
CPS_MAX_SHORT_DELTA = 0.25

CPS_MIN_CREDIT_TO_WIDTH = 0.25
CPS_WATCH_MIN_CREDIT_TO_WIDTH = 0.20

CPS_MAX_BID_ASK_RATIO = 0.20
CPS_PREFERRED_BID_ASK_RATIO = 0.15

CPS_MIN_OPEN_INTEREST = 100
CPS_PREFERRED_OPEN_INTEREST = 500

CPS_SELL_CONFIRMATION_DAYS = 2
```

These should be easy to tune later.

---

## 2.2 Add `spread_builder.py`

Create:

```text
backend/spread_builder.py
```

Primary responsibility:

> Construct Credit Put Spread candidates from existing scan results and option-chain data.

Suggested top-level functions:

```python
def build_credit_put_spread_candidates(scan_results, option_chains, regime_overlay=None):
    """Return ranked CPS candidates for eligible tickers."""


def build_candidate_for_ticker(ticker_result, option_chain, regime_overlay=None):
    """Return one best CPS candidate for a ticker, or a rejected candidate with reasons."""


def select_cps_expiration(option_chain, target_dte=35):
    """Select expiration in the 30-45 DTE window closest to target."""


def select_short_put(puts, target_delta=0.20):
    """Select short put closest to target delta inside 0.15-0.25 range."""


def select_long_put(puts, short_put, spot, atr14, expected_move):
    """Select long put using ATR / expected-move-aware width."""


def compute_spread_economics(short_put, long_put):
    """Compute credit, width, max loss, credit/width, breakeven."""
```

Do not put this logic into `calculator.py` or `scorer.py`.

---

## 2.3 Apply MVP Universe Filter First

At the top of the builder:

```python
if ticker not in CPS_UNIVERSE:
    return None
```

This should happen before expensive spread construction.

The tab should not show full 33-name universe candidates in MVP.

---

## 2.4 Inherit Base Hard Gates

A ticker should not receive a sellable CPS candidate if any of these fail:

| Gate | Rule | Result |
|---|---|---|
| Earnings | `earnings_dte <= 14` | `AVOID` |
| DANGER regime | `term_slope > 1.15` or ticker regime = DANGER | `AVOID` |
| Negative VRP | `vrp < 0` | `NO_EDGE` or `AVOID` |
| Weak VRP ratio | `vrp_ratio < 1.15` | `NO_EDGE` |
| No data | IV / chain unavailable | `NO_DATA` |
| RV shock | `rv_accel > 1.20` | `WAIT` or `AVOID` |
| Extreme skew | `skew > 20` | `AVOID` or manual review |

Credit Put Spreads are defined-risk, but they should not override hostile volatility regimes.

---

## 2.5 Add Regime Overlay Module

Create:

```text
backend/regime_overlay.py
```

Purpose:

> Apply market-wide volatility regime overlays that affect both Naked Puts and Credit Put Spreads.

### Inputs

At minimum:

- VIX
- VIX3M
- VVIX
- optional 60-day VRP history for z-score

### Suggested overlay rules

| Overlay | Rule | Result |
|---|---|---|
| VIX/VIX3M backwardation | `VIX > VIX3M` | Market-wide caution / avoid new CPS entries |
| VVIX caution | `VVIX > 110` | Vol-of-vol caution; require stronger setup |
| VVIX danger | `VVIX > 130` | Avoid new CPS entries |
| VRP z-score floor | `VRP z-score 60d < +0.5` | Downgrade SELL to WATCH or NO_EDGE |

### Important language

Do not describe VVIX as a position-sizing signal.

Use environment language:

| VVIX | Status |
|---:|---|
| ≤110 | Normal |
| 110–130 | Caution: vol-of-vol elevated |
| >130 | Avoid / wait: vol-of-vol extreme |

### Integration

`regime_overlay.py` should be callable from:

- existing market-regime banner logic,
- `spread_builder.py`,
- possibly `scorer.py` later.

For MVP, it is acceptable for the overlay to affect only the CPS tab, but the architecture should allow reuse.

---

## 2.6 Expiration Selection

Target:

```text
30–45 DTE, closest to 35 DTE
```

Rules:

1. Group put contracts by expiration.
2. Compute DTE.
3. Keep expirations between 30 and 45 DTE.
4. Select expiration closest to 35 DTE.
5. If no valid expiration exists, return `NO_DATA` or `WATCH_CPS` with rejection reason.

Do not use ultra-short DTE spreads in MVP.

---

## 2.7 Short Put Selection

Target:

```text
Short put delta: 0.15–0.25
Preferred: closest to 0.20 delta
```

Rules:

1. Use put contracts only.
2. Require bid/ask/mid valid.
3. Require contract liquidity to pass minimum thresholds.
4. Filter to absolute delta between 0.15 and 0.25.
5. Pick contract closest to 0.20 absolute delta.

If no contract is available:

- do not immediately broaden to poor strikes,
- return `NO_DATA` or `WATCH_CPS` with clear rejection reason.

The MVP should prioritize clean candidates over forcing a spread.

---

## 2.8 Long Put Selection — ATR / Expected-Move-Aware Width

Do not use a crude fixed-width table only.

Width selection belongs in MVP because it materially changes risk/reward.

### Inputs

- Spot price
- ATR14
- Current IV
- DTE
- Available strikes
- Short put strike

### Expected move formula

Use a simple annualized-IV approximation:

```python
expected_move = spot * (iv_current / 100) * sqrt(dte / 365)
expected_move_lower = spot - expected_move
```

### Width target

Use a hybrid target:

```python
target_width = max(
    nearest_valid_strike_width,
    0.75 * atr14
)
```

Then constrain:

```text
Preferred width ≈ 0.75x–1.50x ATR14
Avoid width that is too narrow to matter or too wide for the credit received.
```

### Long put selection rules

1. Long strike must be below short strike.
2. Width should be close to target width after rounding to available strikes.
3. Long leg must pass liquidity filters.
4. Net credit must be positive.
5. Credit/width must pass threshold.

### Candidate construction

For each short put, evaluate several possible lower long puts around the target width.

Pick the best candidate that passes:

- credit/width threshold,
- liquidity threshold,
- max loss sanity check,
- width sanity check.

---

## 2.9 Compute Spread Economics

For each candidate:

```python
short_mid = (short_bid + short_ask) / 2
long_mid = (long_bid + long_ask) / 2

net_credit = short_mid - long_mid
width = short_strike - long_strike
max_loss = width - net_credit
credit_to_width = net_credit / width
breakeven = short_strike - net_credit
```

Reject if:

- `net_credit <= 0`,
- `width <= 0`,
- `max_loss <= 0`,
- `credit_to_width < 0.20`,
- either leg has invalid bid/ask/mid.

For `SELL_CPS`, require:

```text
credit_to_width >= 0.25
```

For `WATCH_CPS`, allow:

```text
credit_to_width >= 0.20
```

but only if all other hard filters pass.

### Warning for unusually high credit/width

If:

```text
credit_to_width > 0.35
```

then add warning:

```text
High credit/width may indicate elevated tail risk. Verify regime, skew, and RV Accel before acting.
```

This warning must be an explicit `warnings[]` entry, not an undefined scoring adjustment.

---

## 2.10 Execution Quality Filters

Both legs must pass execution filters.

Suggested minimums:

| Metric | Minimum | Preferred |
|---|---:|---:|
| Bid > 0 | Required | Required |
| Ask > bid | Required | Required |
| Bid/ask ratio | <20% | <15% |
| Open interest | >100 | >500 |
| Volume | >25 | >100 |
| Mid price | valid | valid |

Use:

```python
bid_ask_ratio = (ask - bid) / mid
```

Reject or downgrade if:

- either leg has zero bid,
- either leg has stale or invalid quote,
- either leg has bid/ask ratio above threshold,
- long leg liquidity is poor.

Credit spreads are more sensitive to execution slippage than naked puts because both entry and exit require two legs.

---

## 2.11 Binary Filter Structure

The following should be hard filters, not weighted score components:

| Filter | SELL_CPS requirement |
|---|---|
| Universe | Ticker in `CPS_UNIVERSE` |
| Base Score | ≥65 |
| Confirmation | ≥2 consecutive SELL_CPS-qualified days |
| DTE | 30–45 |
| Short delta | 0.15–0.25 |
| Credit/width | ≥25% |
| Term structure | Not DANGER |
| RV Accel | ≤1.20; preferably ≤1.10 |
| Skew | <20 |
| VIX/VIX3M | Not backwardated for SELL |
| VVIX | ≤130; caution above 110 |
| Liquidity | Both legs pass |
| Earnings | >14 days if relevant |

Candidate ranking after filters:

```text
Primary rank: Base Edge Score
Tie-breaker 1: higher credit/width
Tie-breaker 2: better bid/ask quality
Tie-breaker 3: better RV Accel status
Tie-breaker 4: cleaner term slope
```

---

## 2.12 Multi-day SELL Confirmation

Add a confirmation mechanism consistent with the Naked Puts tab if Tab 1 already uses consecutive SELL confirmation.

Add field:

```python
consecutive_sell_days: int
```

Rules:

| Condition | Label |
|---|---|
| Passes all SELL filters today, but confirmation <2 days | `WATCH_CPS` |
| Passes all SELL filters and confirmation ≥2 days | `SELL_CPS` |
| Fails hard gate | `AVOID` |
| Fails edge threshold | `NO_EDGE` |

Implementation options:

1. Store daily CPS candidate status in SQLite, or
2. derive from previous scan snapshots if CPS candidates are persisted, or
3. start with current-day `WATCH_CPS` only until persistence is implemented.

Do not label a one-day spike as `SELL_CPS`.

---

## 2.13 Exit Logic Module

Even if the Journal is not fully implemented, exit rules must be specified now.

Create or plan:

```text
backend/spread_exit_evaluator.py
```

Purpose:

> Evaluate open Credit Put Spread positions and return management actions.

### Suggested action enum

```python
class SpreadExitAction(str, Enum):
    HOLD = "HOLD"
    CLOSE_PROFIT_TARGET = "CLOSE_PROFIT_TARGET"
    CLOSE_DEFENSIVE = "CLOSE_DEFENSIVE"
    CLOSE_TIME = "CLOSE_TIME"
    CLOSE_PIN_RISK = "CLOSE_PIN_RISK"
    CLOSE_EVENT_RISK = "CLOSE_EVENT_RISK"
```

### Required exit rules

| Exit rule | Trigger | Action |
|---|---|---|
| Profit target | Current mark ≤ 50% of original credit | Close spread |
| Defensive mark | Current mark ≥ 2x original credit | Close or defensive review |
| Short-strike breach | Underlying trades below short strike | Close / review urgently |
| Time exit | DTE ≤21 | Close or reassess; do not let tested spread decay unattended |
| Pin risk | Final 2 trading days and spot within $0.50 of short strike | Close to avoid pin/assignment risk |
| Event risk | Earnings or known binary event enters danger window | Close before event |
| Regime flip | Ticker or market flips to DANGER | Close or reduce exposure |

### MVP without full Journal

If full Journal is not ready, add one of the following:

1. A minimal manual **Open CPS Positions** panel, or
2. Document exit rules in the strategy references and defer automated evaluation to Journal phase.

Do not ship CPS docs without exit rules.

---

## 2.14 Pin-Risk Auto-Close Rule

Pin risk must be explicit because Credit Put Spreads are multi-leg defined-risk positions.

Rule:

```text
If DTE <= 2 trading days and spot is within $0.50 of the short strike, flag CLOSE_PIN_RISK.
```

For higher-priced index ETFs, optionally scale the threshold:

```python
pin_threshold = max(0.50, 0.001 * spot)
```

The frontend should display a clear warning:

```text
Pin Risk: underlying is close to the short strike near expiration. Close before expiry to avoid assignment/settlement complexity.
```

---

## Phase 2 Acceptance Criteria

- `CPS_UNIVERSE` exists and defaults to `SPY`, `QQQ`, `IWM`.
- `spread_builder.py` generates CPS candidates only for the CPS universe.
- Base hard gates are inherited.
- VIX/VIX3M and VVIX overlays are available or stubbed with clear TODOs.
- Expiration selection targets 30–45 DTE.
- Short strike selection targets 0.15–0.25 delta.
- Width selection uses ATR and/or expected move, not only fixed spot tiers.
- Credit/width, liquidity, DTE, delta, and execution quality are binary filters.
- `SELL_CPS` requires at least 2 consecutive qualified days.
- Exit rules are documented and/or implemented in `spread_exit_evaluator.py`.
- Pin-risk rule is explicitly defined.
- No position-sizing recommendation is introduced.

---

# Phase 3 — API, Persistence, and Daily Scan Integration

## Goal

Expose Credit Put Spread candidates to the frontend and persist enough state to support confirmation and future journal integration.

---

## 3.1 API Endpoint

Add endpoint:

```text
GET /api/credit-put-spreads/latest
```

Suggested response:

```json
{
  "scan_date": "2026-05-11",
  "market_regime": "THE_PLAYOFFS",
  "cps_universe": ["SPY", "QQQ", "IWM"],
  "regime_overlay": {
    "vix": 18.2,
    "vix3m": 20.1,
    "vvix": 104.5,
    "status": "NORMAL",
    "warnings": []
  },
  "candidates": [
    {
      "ticker": "SPY",
      "action": "SELL_CPS",
      "base_score": 78,
      "rank_score": 78,
      "consecutive_sell_days": 2,
      "spread": "500/495P",
      "dte": 35,
      "net_credit": 1.25,
      "width": 5.00,
      "credit_to_width": 0.25,
      "max_loss": 3.75,
      "breakeven": 498.75,
      "notes": ["Passed construction filters", "Passed execution filters"],
      "warnings": [],
      "rejection_reasons": []
    }
  ]
}
```

---

## 3.2 Persistence for Consecutive SELL Days

To support multi-day confirmation, persist candidate status by ticker and date.

Possible table:

```sql
CREATE TABLE IF NOT EXISTS cps_candidate_history (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  scan_date TEXT NOT NULL,
  ticker TEXT NOT NULL,
  action TEXT NOT NULL,
  base_score REAL,
  credit_to_width REAL,
  dte INTEGER,
  short_strike REAL,
  long_strike REAL,
  expiration TEXT,
  passed_filters INTEGER,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(scan_date, ticker, expiration, short_strike, long_strike)
);
```

Minimum viable alternative:

- include CPS candidates in existing scan snapshots,
- derive consecutive status from the last two scan results.

Preferred:

- add the small `cps_candidate_history` table because it keeps confirmation logic explicit.

---

## 3.3 Daily Scan Integration

Add CPS generation after existing ticker scoring:

```text
Fetch data
  ↓
Compute base metrics
  ↓
Score naked-put opportunity
  ↓
Apply base gates/regime
  ↓
Build CPS candidate if ticker in CPS_UNIVERSE
  ↓
Apply construction/execution filters
  ↓
Persist candidate status
  ↓
Return latest candidates through API
```

Do not change the existing Naked Puts score.

---

## 3.4 Empty State Behavior

The endpoint should gracefully return an empty candidate list when no spreads pass filters.

Example:

```json
{
  "scan_date": "2026-05-11",
  "market_regime": "REGULAR_SEASON",
  "cps_universe": ["SPY", "QQQ", "IWM"],
  "candidates": [],
  "message": "No Credit Put Spread candidates passed today's filters."
}
```

---

## Phase 3 Acceptance Criteria

- `/api/credit-put-spreads/latest` exists.
- Endpoint returns stable JSON even when no candidates pass.
- Candidate history is persisted or derived reliably for 2-day confirmation.
- Existing Naked Puts endpoint behavior remains unchanged.
- Backend score weights remain unchanged.
- CPS tab does not alter existing scan recommendations.
- Errors are handled cleanly.

---

# Phase 4 — Frontend Credit Put Spreads Tab

## Goal

Add the new Credit Put Spreads tab to the dashboard without disrupting the existing Naked Puts workflow.

---

## 4.1 Frontend Files

Likely additions:

```text
frontend/src/components/CreditPutSpreadsTab.tsx
frontend/src/components/CreditPutSpreadTable.tsx
frontend/src/components/CreditPutSpreadDetailPanel.tsx
frontend/src/components/CreditPutSpreadActionBadge.tsx
frontend/src/components/CreditPutSpreadEconomicsCard.tsx
```

Likely edits:

```text
frontend/src/app/page.tsx
frontend/src/lib/api.ts
frontend/src/lib/types.ts
```

---

## 4.2 Tab Navigation

Implement:

```text
[Naked Puts] [Credit Put Spreads] [Journal (Coming Soon)]
```

Behavior:

| Tab | Behavior |
|---|---|
| Naked Puts | Existing dashboard content |
| Credit Put Spreads | Fetch and show CPS candidates |
| Journal (Coming Soon) | Disabled tab or placeholder panel |

The Journal placeholder can say:

```text
Journal coming soon.
Track actual trades, exits, P/L, assignment outcomes, and setup quality at entry.
```

---

## 4.3 CPS Table Columns

Recommended columns:

| Column | Purpose |
|---|---|
| Rank | Prioritization |
| Ticker | Underlying |
| Action | SELL_CPS / WATCH_CPS / WAIT / AVOID |
| Base Score | Existing volatility edge score |
| Consecutive Days | Confirms signal persistence |
| Regime | Existing ticker regime |
| RV Status | RV Accel interpretation |
| Spread | Example: `500/495P` |
| DTE | Expiration quality |
| Credit | Net credit per share |
| Width | Spread width |
| Credit/Width | Key spread economics |
| Max Loss | Defined max loss |
| Breakeven | Downside buffer |
| Warnings | High credit/width, VVIX caution, etc. |

---

## 4.4 CPS Detail Panel

When selecting a row, show:

### Base edge context

- Base Score
- VRP
- VRP Ratio
- VRP z-score if available
- IV Percentile
- Term Slope
- RV Accel
- RV Accel Status
- Skew
- Market Regime
- Regime Overlay Status

### Spread construction

- Expiration
- DTE
- Short put strike / delta / bid / ask / mid / IV / OI / volume
- Long put strike / delta / bid / ask / mid / IV / OI / volume
- Width
- Net credit
- Credit/width
- Max loss
- Breakeven
- ATR14
- Expected move
- Width/ATR
- Expected-move lower bound

### Notes and warnings

- Passed filters
- Rejection reasons if not sellable
- High credit/width warning
- VVIX warning
- VIX/VIX3M warning
- Pin-risk guidance if applicable

---

## 4.5 Visual Language

Use clear labels:

| Action | UI color semantics |
|---|---|
| SELL_CPS | Positive / actionable |
| WATCH_CPS | Neutral / watchlist |
| WAIT | Caution |
| AVOID | Danger |
| NO_EDGE | Muted |
| NO_DATA | Muted / unavailable |

Do not use:

- Full size
- Half size
- Quarter size
- Position sizing recommendation

RV Accel should be shown as environment cleanliness:

| RV Accel | Status |
|---:|---|
| ≤0.85 | Excellent |
| 0.85–1.00 | Good |
| 1.00–1.10 | Acceptable |
| 1.10–1.20 | Caution |
| >1.20 | Avoid / Wait |

---

## 4.6 Empty and Loading States

If no CPS candidates pass:

```text
No Credit Put Spread candidates passed today's filters.
This usually means the edge, construction quality, or execution quality is not clean enough today.
```

If only WATCH candidates exist:

```text
No confirmed SELL_CPS candidates yet.
Watch candidates need another qualifying day or stronger spread economics.
```

---

## Phase 4 Acceptance Criteria

- Tab navigation works.
- Existing Naked Puts view is preserved.
- Credit Put Spreads tab fetches new endpoint.
- CPS table renders candidates correctly.
- CPS detail panel shows base edge + spread economics.
- Journal placeholder is present and clearly marked as coming soon.
- No full/half/quarter sizing language appears.
- Empty states are clear.
- UI distinguishes SELL, WATCH, WAIT, AVOID, NO_EDGE, NO_DATA.

---

# Phase 5 — Tests, Documentation, QA, and Release

## Goal

Validate calculations, protect existing Naked Puts behavior, and document the new CPS system so future coding agents can maintain it.

---

## 5.1 Backend Unit Tests

Add tests for `spread_builder.py`.

Required tests:

| Test | Expected behavior |
|---|---|
| Ticker not in CPS universe | no candidate generated |
| Earnings ≤14 days | candidate avoided/skipped |
| DANGER regime | candidate avoided |
| Negative VRP | no sellable candidate |
| RV Accel >1.20 | WAIT or AVOID |
| Skew >20 | AVOID or manual-review warning |
| Valid 30–45 DTE expiration | selected |
| Invalid DTE | no candidate |
| Short put delta 0.15–0.25 | selected correctly |
| Missing short delta | handled gracefully |
| Long strike below short strike | required |
| ATR/expected-move width logic | selects reasonable width |
| Credit/width <20% | rejected |
| Credit/width 20–25% | WATCH only |
| Credit/width ≥25% | eligible for SELL if other filters pass |
| High credit/width >35% | warning added |
| Bad long-leg liquidity | rejected |
| Bad short-leg liquidity | rejected |
| Bid/ask ratio naming | uses `bid_ask_ratio` |
| 1-day qualified signal | WATCH_CPS |
| 2-day qualified signal | SELL_CPS |
| Candidate ranking | sorts by Base Edge Score after filters |

---

## 5.2 Exit Evaluator Tests

If `spread_exit_evaluator.py` is implemented, add tests:

| Test | Expected behavior |
|---|---|
| Mark ≤50% of credit | CLOSE_PROFIT_TARGET |
| Mark ≥2x credit | CLOSE_DEFENSIVE |
| Spot below short strike | CLOSE_DEFENSIVE |
| DTE ≤21 | CLOSE_TIME |
| DTE ≤2 and spot near short strike | CLOSE_PIN_RISK |
| Earnings enters danger window | CLOSE_EVENT_RISK |
| Regime flips to DANGER | CLOSE_DEFENSIVE or CLOSE_EVENT_RISK |
| None triggered | HOLD |

---

## 5.3 API Tests

Test:

- `/api/credit-put-spreads/latest` returns valid JSON.
- Empty candidate list returns clean response.
- Candidates include expected fields.
- Action labels are valid.
- No candidate outside `CPS_UNIVERSE` appears.
- Endpoint does not mutate existing scan endpoint.
- Error cases do not crash frontend.

---

## 5.4 Frontend Checks

Run:

```bash
npm run typecheck
npm run lint
npm test
```

or the repo's actual equivalent commands.

Validate:

- tab switching,
- loading state,
- empty state,
- CPS table,
- detail panel,
- action badges,
- Journal placeholder,
- no old sizing labels.

---

## 5.5 Documentation Updates

Update:

```text
references/metrics.md
references/strategy.md
README.md
```

Add documentation for:

- CPS universe constraint,
- CPS candidate construction,
- base-score ranking after binary filters,
- DTE selection,
- short-delta selection,
- ATR/expected-move width selection,
- credit/width thresholds,
- execution filters,
- action labels,
- multi-day confirmation,
- regime overlays,
- exit rules,
- pin-risk rule,
- per-share/per-contract display convention.

### Important documentation language

Credit Put Spreads should be described as:

```text
A defined-risk expression of the same volatility edge used by the Naked Puts tab.
```

Do not describe them as:

```text
A way to rescue bad premium-selling setups.
```

---

## 5.6 Release Checklist

Before merging:

```bash
grep -R "Full size" .
grep -R "Half size" .
grep -R "Quarter size" .
grep -R "Position Sizing" .
grep -R "spread_ratio" .
```

Expected:

- no dashboard-facing Full/Half/Quarter size language,
- no old `spread_ratio` field for quote spread,
- no accidental mutation of base score weights.

Also verify:

- CPS candidates are only SPY, QQQ, IWM in MVP,
- Naked Puts tab still works,
- Market Regime banner still works,
- no CPS candidate appears during DANGER regime,
- no `SELL_CPS` appears without 2-day confirmation,
- no candidate with credit/width below 20% appears as actionable,
- no candidate with credit/width below 25% appears as `SELL_CPS`,
- no candidate with RV Accel >1.20 appears as `SELL_CPS`,
- no candidate appears with invalid long-leg data.

---

## Phase 5 Acceptance Criteria

- Backend tests pass.
- Frontend typecheck passes.
- Existing Naked Puts behavior is unchanged.
- CPS docs are updated.
- Release checklist passes.
- Feature is safe to ship as an MVP.

---

# Optional Phase 6 — Advanced Enhancements

Do not block MVP on these.

Add only after the basic CPS tab is stable.

---

## 6.1 Portfolio State and Cross-Tab Vega Tracking

Create:

```text
backend/portfolio_state.py
```

Purpose:

> Track aggregate risk across Naked Puts and Credit Put Spreads once Journal / Open Positions exists.

Potential fields:

- aggregate delta,
- aggregate vega,
- aggregate theta,
- gross assignment notional,
- defined max loss,
- sector / underlying concentration,
- percent of NAV exposed to 1-vol-point move.

Example rule:

```text
Max short vega exposure: configurable cap, e.g. 0.5% of NAV per 1-vol-point move.
```

Frontend could show a portfolio risk banner beside Market Regime.

This likely requires Journal / manual open-position entry, so it should not block CPS MVP.

---

## 6.2 Expand CPS Universe

After MVP quality is verified, consider:

```python
CPS_UNIVERSE_EXTENDED = ["SPY", "QQQ", "IWM", "EEM", "TLT", "XLE"]
```

Only expand if:

- long-leg liquidity is consistently strong,
- candidate quality is not noisy,
- execution filters are consistently passed,
- historical replays show value.

Do not automatically include the full 33-name Naked Puts universe.

---

## 6.3 Multi-Expiration Ranking

Allow ranking across several expirations:

- 30–35 DTE,
- 36–45 DTE,
- 46–60 DTE.

Keep default simple.

Avoid overwhelming the user with many near-duplicate spreads.

---

## 6.4 Long-Leg Delta Optimizer

Instead of ATR-only width, optimize long leg by:

- target long delta 0.05–0.12,
- credit/width threshold,
- liquidity,
- expected-move buffer,
- max loss efficiency.

This can improve construction quality after MVP.

---

## 6.5 Historical Replay / Backtest

Replay historical scans to answer:

- How many CPS candidates appear per month?
- How often do candidates pass 2-day confirmation?
- Does credit/width ≥25% produce enough candidates?
- Do RV Accel caution candidates underperform?
- Does VIX/VIX3M filtering reduce bad signals?

Use this to tune filters.

---

## 6.6 Journal Integration

When Journal is implemented, support:

- manual CPS position entry,
- imported candidate-to-trade conversion,
- exit evaluation,
- P/L tracking,
- close reason,
- score-at-entry snapshots,
- assignment / settlement notes.

Journal should eventually store:

| Field | Purpose |
|---|---|
| Structure | Naked Put or Credit Put Spread |
| Ticker | Underlying |
| Entry date | Trade timing |
| Expiration | DTE and exit rules |
| Short strike | Risk level |
| Long strike | Defined-risk leg |
| Credit | Premium |
| Exit debit | Realized P/L |
| Base score at entry | Signal quality |
| RV Accel at entry | Environment quality |
| Regime at entry | Market context |
| Exit reason | Process discipline |
| P/L | Outcome |

---

## 6.7 Broker Integration

Do not add until much later.

Potential future capabilities:

- import open positions,
- live marks,
- realized P/L,
- portfolio Greeks,
- assignment alerts.

---

# Implementation Guardrails for Coding Agents

## Do not change these

- Existing Naked Puts base scoring weights.
- Existing earnings gate.
- Existing negative VRP logic.
- Existing DANGER regime logic.
- Existing Market Regime banner behavior, except to add overlays if requested.
- Existing scan pipeline behavior for non-CPS tickers.

## Do add these

- `CPS_UNIVERSE = ["SPY", "QQQ", "IWM"]`.
- `spread_builder.py`.
- CPS candidate models.
- Binary construction/execution filters.
- ATR / expected-move width logic.
- `bid_ask_ratio` naming.
- 2-day SELL confirmation.
- CPS endpoint.
- Credit Put Spreads frontend tab.
- Exit rule documentation and preferably `spread_exit_evaluator.py`.

## Do not add these in MVP

- Full portfolio vega cap unless Journal/open positions already exist.
- Kelly sizing.
- Automated position sizing labels.
- Iron condors.
- Jade lizards.
- Strangles.
- Complex optimizer.
- Broker integration.

---

# Recommended Implementation Order

```text
1. Update docs/spec with CPS universe and binary-filter model.
2. Add backend models and frontend types.
3. Add CPS config constants.
4. Add spread_builder.py.
5. Add unit tests for spread economics and filters.
6. Add ATR / expected-move width selection.
7. Add regime_overlay.py or stubs for VIX/VIX3M and VVIX.
8. Add consecutive SELL confirmation persistence.
9. Add /api/credit-put-spreads/latest.
10. Add frontend tab navigation.
11. Add CPS table.
12. Add CPS detail panel.
13. Add Journal placeholder.
14. Add exit rules to docs and optionally spread_exit_evaluator.py.
15. Run tests, typecheck, grep release checklist.
```

---

# Final MVP Definition

The MVP is complete when:

1. The dashboard has tabs:

```text
Naked Puts | Credit Put Spreads | Journal (Coming Soon)
```

2. Credit Put Spreads tab only evaluates:

```text
SPY, QQQ, IWM
```

3. CPS candidates inherit base gates.

4. CPS candidates pass binary filters for:

- DTE,
- short delta,
- credit/width,
- liquidity,
- width sanity,
- regime,
- RV Accel,
- skew,
- VIX/VIX3M / VVIX overlays if available.

5. `SELL_CPS` requires:

- Base Score ≥65,
- all filters pass,
- credit/width ≥25%,
- 2 consecutive qualifying days.

6. Candidate ranking is by Base Edge Score after filters.

7. The UI clearly shows:

- spread strikes,
- DTE,
- credit,
- width,
- credit/width,
- max loss,
- breakeven,
- warnings,
- reasons.

8. Exit rules are documented.

9. No position-sizing recommendations are shown.

10. Existing Naked Puts workflow remains unchanged.

---

# Final Principle

Credit Put Spreads should make the app more disciplined, not more active.

The new tab should not create more trades by lowering standards.

It should only surface cases where:

```text
The same volatility edge exists,
the broad regime is acceptable,
the index ETF has sufficient liquidity,
the spread construction is clean,
and the defined-risk expression is actually worth taking.
```

If those conditions are not met, the correct output is:

```text
No Credit Put Spread candidates today.
```
