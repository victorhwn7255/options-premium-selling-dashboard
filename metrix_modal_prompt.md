# Implement: Explain Metrics Modal

## Overview

Add an "Explain Metrics" modal to the Theta Harvest dashboard (`frontend/`). The modal is an educational reference that explains every metric, formula, and scoring rule in the dashboard using ELI12-level language with NBA-themed analogies. Users open it from a help button in the Navbar.

## Tech Stack (already installed — do NOT add dependencies)

- Next.js 14, React 18, TypeScript
- Tailwind CSS 3.4 (with custom theme tokens via CSS variables)
- No UI library (no shadcn, radix, headless-ui). Build the modal from scratch.

## Design System

The app uses CSS custom properties for all colors, defined in `frontend/src/app/globals.css` under `:root` (light) and `[data-theme="dark"]` (dark). Always use the existing Tailwind utility classes that map to these variables (e.g. `bg-surface`, `text-txt`, `border-border`, `text-txt-tertiary`). See `frontend/tailwind.config.js` for the full mapping.

Fonts: `font-primary` (sans), `font-secondary` (serif — Source Serif 4), `font-mono` (JetBrains Mono).

## Files to Create / Modify

### 1. Create `frontend/src/components/ExplainMetricsModal.tsx`

A single self-contained component. No separate CSS file — use Tailwind classes + inline styles referencing CSS variables where Tailwind doesn't cover it (e.g. `style={{ borderLeftColor: 'var(--color-primary)' }}`).

### 2. Create `frontend/src/lib/metrics-content.ts`

A data file exporting a typed array of metric definitions. This keeps content out of the component. Structure:

```typescript
export interface MetricReading {
  label: string;
  color: 'good' | 'ok' | 'bad' | 'neutral';
}

export interface MetricDefinition {
  id: string;
  emoji: string;
  name: string;
  tag: string;
  section: 'volatility' | 'structure' | 'trade' | 'scoring';
  explain: string;        // HTML string (supports <strong>, <em>)
  analogy: string;
  formulaLabel: string;   // e.g. "Formula" or "How we calculate it" or "Rule"
  formulas: string[];     // array of code lines
  readings: MetricReading[];
}

export const METRICS: MetricDefinition[] = [ ... ];
```

### 3. Modify `frontend/src/components/Navbar.tsx`

Add a `?` help button before the date display that opens the modal. Use local state `useState<boolean>` for open/close. Render `<ExplainMetricsModal>` conditionally via a portal or inline.

### 4. Modify `frontend/src/app/page.tsx`

Alternative approach if you prefer lifting state: manage `showMetricsModal` in page.tsx and pass it down to Navbar + render the modal at page level. Either approach is fine — pick whichever is cleaner.

---

## Component Spec: `ExplainMetricsModal`

### Props

```typescript
interface ExplainMetricsModalProps {
  open: boolean;
  onClose: () => void;
}
```

### Behavior

- **Backdrop**: Fixed overlay, semi-transparent black (`bg-black/60`) with `backdrop-blur-sm`. Clicking the backdrop calls `onClose`.
- **Animation**: Fade in the backdrop, slide the modal up slightly on open. Use CSS transitions or Tailwind `animate-fade-in`. No spring physics needed.
- **Scroll**: The modal body scrolls internally (`overflow-y-auto`, `max-h-[85vh]`). The header is sticky within the scroll container.
- **Close**: Close button (✕) in top-right of header. Also close on `Escape` key (`useEffect` with `keydown` listener).
- **Portal**: Render via `createPortal` to `document.body` to escape any parent stacking contexts. Guard with `typeof window !== 'undefined'` for SSR.
- **Body scroll lock**: When open, add `overflow: hidden` to `document.body`. Remove on close/unmount.

### Layout Structure

```
┌─ Backdrop (fixed, full screen) ────────────────────┐
│  ┌─ Modal (centered, max-w-[720px]) ─────────────┐ │
│  │  ┌─ Header (sticky) ────────────────────────┐  │ │
│  │  │  Title + subtitle          Close button   │  │ │
│  │  └───────────────────────────────────────────┘  │ │
│  │  ┌─ Body (scrollable) ──────────────────────┐  │ │
│  │  │  Section Label: "📊 Volatility Metrics"   │  │ │
│  │  │  MetricCard                               │  │ │
│  │  │  MetricCard                               │  │ │
│  │  │  ...                                      │  │ │
│  │  │  Section Label: "📐 Structure Metrics"    │  │ │
│  │  │  MetricCard                               │  │ │
│  │  │  ...                                      │  │ │
│  │  └───────────────────────────────────────────┘  │ │
│  │  ┌─ Footer ─────────────────────────────────┐  │ │
│  │  │  Disclaimer text                          │  │ │
│  │  └───────────────────────────────────────────┘  │ │
│  └────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────┘
```

### MetricCard Sub-component (inline, not a separate file)

Each card has:
1. **Left accent bar**: 4px wide, `var(--color-primary)`, absolute positioned on the left edge.
2. **Header row**: emoji (24px) + name (font-secondary, 19px, semibold) + tag pill (font-mono, 10px, uppercase, bg-surface-alt).
3. **Explanation**: 15px, `text-txt-secondary`, line-height 1.7. Supports `<strong>` (text-txt, font-medium) and `<em>` (font-secondary, italic, text-primary). Render HTML with `dangerouslySetInnerHTML`.
4. **Analogy box**: Inset callout with `bg-surface-alt`, `border-l-[3px]` with accent color, label "🏀 Think of it like" in uppercase accent color.
5. **Formula block**: `bg-bg-alt`, `border border-border`, each formula line in `font-mono text-xs` with primary color.
6. **Reading pills**: Horizontal flex-wrap row of status pills. Each pill has a colored dot + label. Colors map to: `good` → success, `ok` → warning, `bad` → error, `neutral` → accent. Use the existing `-subtle` background variants.

---

## Metric Content (for `metrics-content.ts`)

### Section: Volatility Metrics (`volatility`)

**1. Realized Volatility (RV)**
- emoji: 🎢
- tag: "RV10 · RV20 · RV30"
- explain: How much the stock price has **actually been bouncing around** recently. We measure this over different windows — the last 10 days (RV10), 20 days (RV20), and 30 days (RV30). A high number means the stock has been moving a lot. A low number means it's been chill.
- analogy: A basketball player's shooting stats from the last few games. RV10 is their stats from the last 2 games (hot streak or cold streak), RV30 is their stats from the last month (more reliable average). Both matter, but for different reasons.
- formulaLabel: "Formula"
- formulas:
  - `log_returns = ln(close[today] / close[yesterday])`
  - `RV = stdev(log_returns, N days, ddof=1) × √252 × 100`
- readings: [neutral "Low RV = calm market", neutral "High RV = wild market"]

**2. Implied Volatility (IV)**
- emoji: 🔮
- tag: "30-day ATM"
- explain: How much the options market **thinks** the stock will bounce around over the next 30 days. It's baked into the price of options — when people are scared, they pay more for options, which pushes IV up. When things are calm, IV drops. It's basically the market's *fear gauge* for each stock.
- analogy: The Vegas odds before a game. It's a prediction — it might be right, it might be wrong. Our whole strategy is betting that this prediction is usually *too high*.
- formulaLabel: "How we calculate it"
- formulas:
  - `1. Find options closest to 30 days until expiry`
  - `2. Find strikes within 3% of current price (ATM)`
  - `3. Average the put + call IV at the nearest strike`
  - `4. Interpolate between two expirations for exact 30-day value`
- readings: [good "High IV = expensive options (good to sell)", bad "Low IV = cheap options (not worth selling)"]

**3. Volatility Risk Premium (VRP)**
- emoji: 💰
- tag: "Core metric"
- explain: **The whole reason this strategy works.** VRP is the gap between what the market *thinks* will happen (IV) and what *actually* happens (RV). Most of the time, IV is higher than RV — meaning people overpay for options. That overpayment is the premium we're harvesting. The bigger the gap, the more money we make selling options.
- analogy: Imagine the weather app says there's an 80% chance of a thunderstorm, so everyone buys umbrellas for $20. But it only drizzles. The umbrella sellers made bank because people *overpaid for protection*. VRP is the difference between the predicted storm and the actual drizzle.
- formulaLabel: "Formula"
- formulas:
  - `VRP = IV(30-day) − RV(30-day)`
  - `VRP Ratio = IV(30-day) / RV(30-day)`
- readings: [good "VRP > 8 = fat premium, strong edge", ok "VRP 3–8 = decent edge", bad "VRP < 0 = no edge, stay away"]

**4. IV Percentile & IV Rank**
- emoji: 📏
- tag: "1-year lookback"
- explain: Is today's IV high or low **compared to the last year?** IV Percentile tells you what percentage of days over the past year had *lower* IV than today. If it's 80, that means today's IV is higher than 80% of the past year — options are expensive. IV Rank does something similar but uses the min and max instead.
- analogy: Your height percentile at school. If you're in the 80th percentile, you're taller than 80% of kids. Same thing — if IV percentile is 80, today's volatility is higher than 80% of days this past year. We want to sell options when they're "tall" (expensive).
- formulaLabel: "Formulas"
- formulas:
  - `IV Percentile = (# days where IV < current) / total days × 100`
  - `IV Rank = (current − min) / (max − min) × 100`
  - `Lookback: 252 trading days (1 year)`
- readings: [good "≥ 80 = options are expensive (sell!)", ok "40–80 = mid-range", bad "< 40 = options are cheap (skip)"]

### Section: Structure Metrics (`structure`)

**5. Term Structure (Slope)**
- emoji: ⛰️
- tag: "Front IV / Back IV"
- explain: Compares IV of **near-term** options vs. **further-out** options. Normally, further-out options have higher IV (because more time = more uncertainty). That's called *contango* and it's the healthy state — the slope is below 1.0. When near-term IV becomes HIGHER than further-out IV, that's *backwardation* — the slope goes above 1.0, meaning the market is panicking about something happening **right now**.
- analogy: Renting an umbrella. Normally, renting one for a whole week costs more than renting for just today — more time covered, higher price. That's contango. But if renting for *just today* suddenly costs more than a whole week, it means a huge storm is expected right now and everyone's desperate for immediate protection. That's backwardation — and it's a warning sign.
- formulaLabel: "Formula"
- formulas:
  - `slope = shortest_tenor_IV / longest_tenor_IV`
- readings: [good "< 0.90 = deep contango (great)", ok "0.90–1.00 = normal contango", bad "> 1.00 = backwardation (danger)"]

**6. RV Acceleration**
- emoji: 🚀
- tag: "Speed gauge"
- explain: Is volatility **speeding up or slowing down?** We compare recent volatility (last 10 days) to the longer average (last 30 days). If the ratio is above 1.0, the market is getting *more* wild lately. If below 1.0, it's calming down. This drives both a **scoring penalty** (−6 pts above 1.05, −15 pts above 1.15) and **position sizing** (how big your bets should be).
- analogy: A car's speedometer vs. average speed. If you're doing 90mph right now but your trip average is 60mph, you're accelerating — things are getting riskier. We shrink our bets when acceleration is high because the road ahead might be bumpy.
- formulaLabel: "Formula"
- formulas:
  - `RV Acceleration = RV10 / RV30`
- readings: [good "≤ 1.10 = stable → Full size", ok "1.10–1.20 = accelerating → Half size", bad "> 1.20 = spiking → Quarter size"]

**7. 25-Delta Skew**
- emoji: ⚖️
- tag: "Put protection demand"
- explain: Measures how much more expensive **downside protection** (puts) is compared to at-the-money options. When big institutions are scared of a crash, they buy more puts, which pushes skew higher. A little bit of skew is normal and healthy — it means there's steady demand for insurance, which is premium we can sell. But if skew is extreme, the smart money might know something you don't.
- analogy: Home insurance pricing. If insurance companies suddenly charge 3x more for flood insurance in your neighborhood, maybe they know something about the flood risk that you don't. Skew tells you how much the "insurance" costs relative to normal.
- formulaLabel: "Formula"
- formulas:
  - `skew = IV(25-delta put) − IV(ATM)`
  - `Measured at nearest-to-30-DTE expiration`
- readings: [good "4–7 = healthy demand (good premium)", ok "7–10 = elevated (more premium, more caution)", bad "> 10 = extreme (institutions hedging hard)"]

### Section: Trade-Level Metrics (`trade`)

**8. ATM Greeks: Theta & Vega**
- emoji: ⏳
- tag: "θ daily · ν per 1% IV"
- explain: Two numbers that tell you what's powering an option's price day to day. **Theta (θ)** is how much money an option loses each day just from time passing — this is the premium we're collecting as sellers. **Vega (ν)** is how much the option's price moves when IV changes by 1 point — this is our risk. We want *high theta* (more daily income) and *manageable vega* (less sensitivity to vol swings).
- analogy: Theta is the interest you earn on a savings account — money that trickles in every day just for holding the position. Vega is how much your account balance swings when the interest rate changes. You want steady drip income (theta) without wild balance swings (vega).
- formulaLabel: "What we show"
- formulas:
  - `θ (theta) = daily time decay in $ from the ATM option`
  - `ν (vega)  = price change per 1% IV move from the ATM option`
  - `Both measured at nearest-to-30-DTE expiration`
- readings: [good "High θ = more daily premium collected", ok "High ν = more exposure to IV swings"]

**9. ATR-14 (Average True Range)**
- emoji: 📐
- tag: "Dollar movement"
- explain: The average amount (in dollars) a stock moves in a single day, measured over the last 14 days. Unlike RV which speaks in percentages, ATR speaks in **actual dollars**. If NVDA has an ATR of $8.50, that means it typically moves about $8.50 per day. Useful for setting stop losses and picking strike widths for credit spreads.
- analogy: How many points a team typically scores per game. If the Lakers average 112 points, you'd be surprised if they scored 150 or 70. ATR is the "normal scoring range" for a stock's daily movement.
- formulaLabel: "Formula"
- formulas:
  - `True Range = max(high − low, |high − prev_close|, |low − prev_close|)`
  - `ATR-14 = average(last 14 true ranges)`
- readings: [] (no pills for ATR)

### Section: Scoring & Safety (`scoring`)

**10. Composite Score**
- emoji: 🏆
- tag: "0 – 100"
- explain: The **final grade** for each ticker — a single number from 0 to 100 that combines all the metrics above. It answers the question: *"Is this a good ticker to sell premium on right now?"* Higher is better. The score is built from VRP (is there edge?), term structure (is the market structure favorable?), IV percentile (are options expensive?), and RV acceleration (is it safe?).
- analogy: A player's overall rating in a video game (like NBA 2K). It combines offense, defense, speed, and shooting into one number. A 90 is a superstar. A 40 rides the bench. Same here — a score of 75 means everything lines up, a score of 30 means something's off.
- formulaLabel: "Formula (frontend scoring)"
- formulas:
  - `VRP Score     = min(40, VRP × 2.5)            ← 0 to 40 pts`
  - `Term Score    = slope < 0.85 → 25 | < 0.90 → 18 | < 0.95 → 12 | else → 5`
  - `IV Pctl Score = ≥ 80 → 20 | ≥ 60 → 14 | ≥ 40 → 8 | else → 3`
  - `RV Penalty    = > 1.15 → −15 | > 1.05 → −6 | else → 0`
  - `──────────────────────────────────────────────`
  - `Total Score   = VRP + Term + IV Pctl + RV Penalty   (clamped 0–100)`
- readings: [good "≥ 70 = SELL — strong edge", ok "≥ 50 = CONDITIONAL — decent edge", bad "< 50 = NO EDGE — skip it"]

**11. Earnings Gate**
- emoji: 🚧
- tag: "Safety filter"
- explain: A hard safety rule that **overrides everything else.** If a stock has earnings coming up within 14 days, the score is forced to 0 and the action is SKIP — no matter how good the other metrics look. Why? Because earnings announcements are like coin flips on steroids. The stock could gap 10% in either direction overnight, and that kind of move can wipe out weeks of premium-selling profits in one session.
- analogy: The coach benching a star player before the playoffs to avoid injury. Doesn't matter if they're playing great — the risk of losing them for the whole season isn't worth one regular-season game. Earnings are the same: the risk of one massive loss isn't worth the premium.
- formulaLabel: "Rule"
- formulas:
  - `if days_to_earnings ≤ 14:`
  - `    score = 0`
  - `    action = "Earnings in {N}d"`
  - `    (skip this ticker, no exceptions)`
- readings: [bad "≤ 14 days = gated out, score forced to 0", good "> 14 days = safe, score computed normally"]

**12. Position Sizing**
- emoji: 🎚️
- tag: "Full · Half · Quarter"
- explain: How much to bet, based on how wild the market is *right now*. When recent vol is stable, you can go Full size. When it's accelerating, you shrink to Half or Quarter. This is your **seatbelt** — it doesn't tell you *what* to trade, it tells you *how much*.
- analogy: How hard you push in a race. Dry road? Full throttle. Wet road? Ease off. Icy road? Crawl. You still want to get there, but you adjust speed for conditions. Same thing — same trades, just different amounts.
- formulaLabel: "Logic (based on RV Acceleration)"
- formulas:
  - `if RV Acceleration > 1.20 → Quarter  (vol spiking)`
  - `if RV Acceleration > 1.10 → Half     (vol rising)`
  - `otherwise                → Full     (vol stable)`
- readings: [] (no pills)

---

## Modal Header Content

- Title: "Key Metrics for Premium Selling" (font-secondary, ~28px, semibold)
- Subtitle: "Explain the key metrics like I'm 12." (font-secondary, italic, 14px, text-txt-tertiary)

## Section Labels

Render as small uppercase dividers between card groups:
- `📊 Volatility Metrics` — before metrics 1–4
- `📐 Structure Metrics` — before metrics 5–7
- `🔬 Trade-Level Metrics` — before metrics 8–9
- `🎯 Scoring & Safety` — before metrics 10–12

## Footer Content

Below the last card, in the modal footer area:

> All metrics update daily after market close (~6:30 PM ET). The scoring engine combines these metrics into a single 0–100 score per ticker, filtered by the earnings gate and adjusted by the market regime. When in doubt, trust the score — it's doing the math so you don't have to.

Style: 13px, italic, `text-txt-tertiary`.

---

## Navbar Help Button Spec

Add a `?` button to `Navbar.tsx`, positioned between the earnings refresh button and the date display. Style:

```
- 28px × 28px circle
- bg-surface-alt on hover
- text-txt-tertiary, hover → text-txt
- font-secondary, italic, 15px (the "?" character)
- border: 1px solid var(--color-border)
- tooltip on hover: "Explain metrics" (use the same tooltip pattern as the existing navbar buttons)
- onClick: toggle modal open state
```

---

## Implementation Notes

- **No new dependencies.** Use `createPortal` from `react-dom` for the modal. Use `useEffect` for Escape key and body scroll lock.
- **Theme-aware.** All colors must work in both light and dark mode. Use the CSS variable tokens from the design system — never hardcode hex colors.
- **HTML in explanations.** The `explain` field contains `<strong>` and `<em>` tags. Render with `dangerouslySetInnerHTML`. This is safe since the content is hardcoded in our own data file.
- **Keep the accent bar color consistent.** All metric cards use `var(--color-primary)` (terracotta) for the left border accent, matching the demo.
- **Analogy box accent.** The left border of the analogy callout uses `var(--color-accent)` (the purple/lavender).
- **Formula code color.** Formula text uses `var(--color-primary)` on a `bg-bg-alt` background.
- **Reading pill colors.** Map `good` → `bg-success-subtle text-success`, `ok` → `bg-warning-subtle text-warning`, `bad` → `bg-error-subtle text-error`, `neutral` → `bg-accent-subtle text-accent`. Each pill has a small 8px dot matching its text color.
- **Responsive.** On mobile (< 640px), the modal should go full-width with reduced padding (px-4 instead of px-8). Reading pills should wrap naturally via `flex-wrap`.
- **Keyboard accessible.** Focus trap is nice-to-have but not required. At minimum: close on Escape, close button is focusable.

## Testing

After implementation, verify:
1. Modal opens from Navbar `?` button
2. Modal closes on: ✕ button, backdrop click, Escape key
3. All 12 metric cards render with correct content
4. Scrolling works within modal (body doesn't scroll behind it)
5. Light and dark themes both look correct
6. No hydration errors (portal guard for SSR)
