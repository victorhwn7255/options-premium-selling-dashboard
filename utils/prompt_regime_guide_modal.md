# Add Regime Guide Modal — Triggered from Regime Banner

## Overview

Add a modal overlay that explains all four market regimes. It opens when the user clicks the regime name on the RegimeBanner (e.g., clicking "GARBAGE TIME"). The modal has a darkened backdrop, scrollable content, and a close button.

No new routes. No new nav tabs. No new dependencies. Just a modal component and a click handler on the existing banner.

**Stack:** Next.js 14 (App Router), React 18, TypeScript, Tailwind CSS, `clsx` for conditional classes.

## Before Writing Any Code

Read the codebase to understand:

1. **RegimeBanner component** — find the regime label element that will become the click trigger. Understand its current props and state.
2. **`tailwind.config.ts`** — find the custom color tokens (error, warning, secondary, accent), font families (serif, sans, mono), and any backdrop/overlay utilities
3. **Existing modal or overlay patterns** — check if the app already has any modal, dialog, or overlay component. If yes, extend it. If not, build a minimal one.
4. **Component file conventions** — where do components live? What naming pattern is used?
5. **`app/globals.css`** — check for any CSS custom properties the Tailwind classes reference

## Implementation

### 1. Make the regime name clickable

In the RegimeBanner component, wrap the regime name text in a `button` or clickable `div` with:
- `cursor-pointer` 
- Subtle hover effect (underline or slight brightness change)
- `onClick` handler that opens the modal
- A small "?" icon or "Learn more" hint text next to the regime name so users know it's interactive

### 2. Build the modal

Create a `RegimeGuideModal.tsx` component. Structure:

```
Backdrop (fixed inset-0, bg-black/60, backdrop-blur-sm, z-50)
└── Modal container (centered, max-w-3xl, max-h-[85vh], overflow-y-auto, rounded-2xl, bg-surface)
    ├── Header (sticky top-0, regime name + close button)
    ├── Scrollable content
    │   ├── RegimeSection × 4 (with dividers between)
    │   ├── Quick Reference: Key Metrics
    │   └── Footer text
    └── Close button (X in top-right corner)
```

**Behavior:**
- Click backdrop to close
- Press `Escape` to close
- Trap focus inside modal when open (basic a11y)
- Prevent body scroll when modal is open
- Smooth fade-in on open

### 3. Build inner components

Keep these inside the modal file or a `regime-guide/` subfolder — match existing conventions:

#### `RegimeSection`
Each regime block inside the modal. Props:

```typescript
interface RegimeSectionProps {
  index: number
  name: string
  tagline: string
  colorClass: string      // read from tailwind config
  triggers: { metric: string; value: string }[]
  triggerLogic: string    // "either condition" | "both required" | "all conditions (default)"
  explanation: string[]   // paragraphs
  dos: string[]
  donts: string[]
  example: {
    tag: string
    metrics: { label: string; value: string }[]
    narrative: string
  }
}
```

**Read tailwind.config.ts first** to find the actual class names for colors — don't guess.

#### Layout inside each section:
- **Regime banner** — colored left border, gradient tint bg, large serif title, italic tagline
- **Trigger grid** — 2-col grid (stacks on mobile) showing metric thresholds + logic label
- **DOs / DON'Ts** — 2-col grid (stacks on mobile), success-colored checkmarks / error-colored X marks
- **Example trade** — card with 4-col (2×2 mobile) metric pills + italic narrative

### 4. Scroll to current regime

When the modal opens, auto-scroll to the section matching the currently active regime. Add `id` attributes to each regime section and use `scrollIntoView({ behavior: 'smooth', block: 'start' })` after the modal mounts.

### 5. Highlight current regime

The regime section matching the current active regime should have a subtle visual distinction — slightly brighter border or a small "CURRENT" badge — so the user immediately sees which section is relevant to today's market.

## Regime Color Mapping

| Regime | Color Token | Tailwind Usage |
|--------|------------|----------------|
| GARBAGE TIME | error (red) | Border, title, bg tint |
| CLUTCH Q4 | warning (gold) | Border, title, bg tint |
| SHOOTAROUND | secondary (sage) | Border, title, bg tint |
| HEAT CHECK | accent (purple) | Border, title, bg tint |

**Find the actual class names in tailwind.config.ts** — they might be `text-error`, `text-[var(--color-error)]`, or something else entirely.

## Content

All copy below is final — use it verbatim.

---

### GARBAGE TIME (Error Red)

**Tagline:** "Game's out of reach — sit on the bench, protect your capital"

**Triggers (either):**
- Term Slope > 1.02 (backwardation)
- Backwardation Count ≥ 3 tickers

**What's happening:**

The volatility term structure is inverted — front-month implied volatility exceeds back-month, meaning the market expects more turbulence now than later. This typically happens during broad selloffs, macro shocks, or cascading uncertainty (tariff escalations, credit events, pandemic scares). Multiple tickers are showing the same pattern, confirming this isn't a single-name event — it's systemic.

Premium selling in backwardation is like picking up pennies in front of a bulldozer that's already moving. The options market is telling you that realized volatility will likely exceed implied — meaning you'll collect less premium than the losses your short options generate.

**DOs:**
- Go to cash or stay fully hedged
- Review and tighten stops on any existing positions
- Study the leaderboard for post-regime opportunities — high pre-gate scores signal tickers to watch
- Use the time to research and plan entries for when the regime clears

**DON'Ts:**
- Open any new short premium positions
- Sell "cheap" puts because they look like bargains — they're cheap for a reason
- Try to catch the bottom by selling into the spike
- Assume it's temporary — regimes can persist for weeks

**Example:** (tag: "Feb 13, 2026")
- Avg VRP: 1.1
- Term Slope: 1.09
- RV Accel: 1.17
- Tradeable: 1 / 25

Narrative: "Broad market in backwardation with near-zero VRP. Gold surging (GLD term slope 1.20), multiple tech names with negative VRP after selloff. Only 1 of 25 tickers passes any scoring threshold. The dashboard locks to read-only mode — the correct action is no action."

---

### CLUTCH Q4 (Warning Gold)

**Tagline:** "Every possession counts — play tight, no turnovers"

**Triggers (either):**
- RV Accel > 1.12
- Backwardation Count ≥ 1 ticker

**What's happening:**

The market is playable but stressed. Either short-term realized volatility is accelerating (recent moves are bigger than the trailing average) or at least one ticker has flipped into backwardation — an early warning that broader stress may be building.

Think of it as the fourth quarter of a tight playoff game. You can still score, but every play needs to be high-percentage. No hero ball. This is where defined-risk structures (spreads, iron condors) earn their keep — they cap your downside if the regime deteriorates to Garbage Time.

**DOs:**
- Use defined-risk only — credit spreads, iron condors, iron butterflies
- Cut position size to Half or Quarter of normal
- Tighten DTE — 21-30 days max to reduce time exposure
- Focus on the highest-scoring tickers only (65+)
- Set hard exit rules before entering

**DON'Ts:**
- Sell naked options — undefined risk in accelerating vol is how accounts blow up
- Sell in tickers showing backwardation individually, even if the market-level regime is only CLUTCH Q4
- Add to losing positions — if a trade goes against you, take the loss
- Ignore the sizing chip — if it says Quarter, trade Quarter

**Example:** (tag: "Hypothetical")
- Ticker: AAPL
- Structure: Put Spread
- DTE: 25 days
- Sizing: Half

Narrative: "AAPL scores 68 with a VRP of 9.2 and contango term structure (0.88). But RV accel is 1.14, so the regime is CLUTCH Q4. You sell a 25-DTE put credit spread at the 15-delta strike instead of a naked put, at half your normal contract count. Max loss is defined at entry."

---

### SHOOTAROUND (Secondary Sage)

**Tagline:** "Running your sets — nothing weird, execute the playbook"

**Triggers (all conditions — this is the default regime):**
- Term Slope ≤ 1.02 (contango)
- RV Accel ≤ 1.12
- Backwardation Count = 0
- Not favorable (VRP < 8 or slope ≥ 0.90)

**What's happening:**

Normal conditions. The volatility term structure is in contango (back months more expensive than front months, as expected), realized vol isn't spiking, and no individual tickers are flashing warnings. The VRP exists but isn't unusually wide.

This is where you spend most of your time as a premium seller — roughly 60-70% of trading days. Run your standard playbook: sell premium on high-scoring tickers at normal sizing, using whatever structures your system calls for. Nothing to get excited about, nothing to worry about.

**DOs:**
- Execute your standard strategy on tickers scoring ≥ 50
- Use Full or Half sizing as indicated by the sizing chip
- Mix structures — strangles, spreads, and iron condors are all appropriate
- Target 30-45 DTE for optimal theta decay
- Manage winners at 50% of max profit

**DON'Ts:**
- Get complacent — SHOOTAROUND can transition to CLUTCH Q4 quickly
- Over-concentrate in one sector — spread across at least 3-4 sectors
- Ignore the scoring — just because the regime is normal doesn't mean every ticker is tradeable
- Size up beyond what the system recommends just because conditions are calm

**Example:** (tag: "Hypothetical")
- Ticker: QQQ
- Structure: Strangle
- DTE: 38 days
- Sizing: Full

Narrative: "QQQ scores 72 with VRP of 10.4, deep contango (term slope 0.82), and stable RV accel (1.03). The regime is SHOOTAROUND with 12 of 25 tickers tradeable. You sell a 38-DTE strangle at 16-delta on both sides, Full size. Textbook premium harvest — collect theta, manage at 50% profit."

---

### HEAT CHECK (Accent Purple)

**Tagline:** "You're on fire — wide VRP in contango, keep shooting"

**Triggers (both required):**
- Avg VRP > 8 vol points
- Term Slope < 0.90 (deep contango)

**What's happening:**

This is the sweet spot. The options market is significantly overpricing future volatility relative to what's actually being realized — and the term structure confirms it with deep contango. The variance risk premium is fat and the market structure supports harvesting it.

HEAT CHECK typically appears after a vol spike has started to resolve — IV is still elevated from the fear but realized vol has already started dropping. This is when premium sellers have the biggest statistical edge. The VRP of 8+ means implied vol is overshooting realized by 8 or more annualized vol points across the universe — historically, that level of mispricing resolves in the seller's favor roughly 85% of the time.

**DOs:**
- Be more aggressive — this is the regime where edge is widest
- Use Full sizing on tickers scoring ≥ 50
- Consider wider strangles to capture elevated premium at further OTM strikes
- Extend DTE to 35-50 days to ride the IV mean-reversion
- Trade more tickers — when VRP is broad, diversification amplifies edge

**DON'Ts:**
- Go full Kelly — even in the best regime, cap at Half Kelly for ergodicity
- Ignore individual ticker scores — regime is favorable but not every name has edge
- Forget your exits — set profit targets (50-65% of max) before entering
- Assume it lasts forever — HEAT CHECK often transitions to SHOOTAROUND within 1-2 weeks as IV normalizes

**Example:** (tag: "Hypothetical")
- Ticker: AMZN
- Structure: Strangle
- DTE: 45 days
- Sizing: Full

Narrative: "Market regime flips to HEAT CHECK after a vol spike subsides — avg VRP jumps to 11.2 with term slope at 0.84. AMZN scores 81 with VRP 14.8 and deep contango. You sell a 45-DTE strangle at 20-delta (wider than usual to capture the elevated premium at further strikes), Full size. The statistical edge is at its fattest — this is why you stay patient during Garbage Time."

---

### Quick Reference: Key Metrics (after all four regimes)

**AVG VRP** — Volatility Risk Premium — the gap between what the options market thinks volatility will be (implied vol) and what it actually is (realized vol). Positive = options are overpriced, you have edge selling them. Negative = options are underpriced, selling them loses money. Measured in annualized vol points.

**TERM SLOPE** — IV Term Structure — the ratio of front-month IV to back-month IV. Below 1.0 = contango (normal, favorable for selling). Above 1.0 = backwardation (stressed, market expects near-term trouble). Think of it like the yield curve — inversion is a warning sign.

**RV ACCEL** — Realized Vol Acceleration — the ratio of short-term RV (10-day) to longer-term RV (30-day). Above 1.0 = vol is increasing. Below 1.0 = vol is decelerating. High acceleration means the market hasn't settled — even if VRP looks attractive, the ground is still shifting.

**TRADEABLE** — Tradeable Count — how many tickers in the non-earnings universe score above the minimum threshold. The denominator excludes earnings-gated tickers (within 14 days of reporting). A low ratio like 1/25 confirms a hostile environment; a high ratio like 18/25 signals broad opportunity.

### Footer text

"Option Harvest uses these regimes as the first decision layer — 'Should I trade today?' — before evaluating individual tickers. The regime system is designed to keep you out of the market during the conditions that cause the worst losses in premium selling strategies. Patience during Garbage Time is what makes Heat Check profitable."

---

## Visual Reference

The file `regime_guide.html` is available as a design-only mockup for layout, spacing, and visual hierarchy. Rebuild everything as React components with Tailwind. Do not copy any raw CSS from it.

## What NOT to Change

- Don't add new routes or nav tabs
- Don't modify scoring logic or regime detection code
- Don't change regime names on the main dashboard banner (that's a separate task)
- Don't add new npm dependencies
