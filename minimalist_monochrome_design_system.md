# Minimalist Monochrome — Design System for Option Harvest

> **Audience for this document:** Claude Code agent implementing UI changes.
> **What this is:** A complete design system specification for reskinning the Option Harvest dashboard (theta.thevixguy.com) from the current "Anthropic Warm Humanist" theme to a Minimalist Monochrome editorial style.
> **How to use it:** Read Section 1 (Philosophy) first — it contains the constraints that override any ambiguous decision. Then reference Section 2 (Tokens) for exact values, Section 3 (Component Patterns) for reusable primitives, and Section 4 (Dashboard Component Map) for Option Harvest-specific translations.
> **Companion file:** `minimalist_monochrome_theme.json` contains the same design tokens in structured JSON format for programmatic reference. This MD file is the primary source of truth — if anything conflicts between the two files, follow this MD.

---

## 1. Design Philosophy

### Core Principle

**Reduction to Essence.** This design strips everything down to black, white, and typography. There are no accent colors to hide behind, no gradients to soften edges, no shadows to create false depth. Every design decision must stand on its own merit. This is design as discipline — where restraint becomes the ultimate form of expression.

### Emotional Tone

Austere. Authoritative. Timeless. Editorial. Intellectual. Dramatic. Refined. Stark. Confident. Uncompromising.

Think: high-end fashion editorial (Vogue, Harper's Bazaar), architectural monographs, luxury brand identity (Chanel, Celine, Bottega Veneta), gallery exhibition materials.

### The 7 DNA Rules

These are non-negotiable. Every implementation decision must pass through these:

1. **Pure Black & White Palette** — Use `#000000` and `#FFFFFF` for all primary elements. Gray is reserved ONLY for secondary text (`#525252`) and subtle dividers (`#E5E5E5`). No other colors. Ever.
2. **Serif Typography as Hero** — Classical serif typefaces (Playfair Display for headlines, Source Serif 4 for body). Typography is the primary visual element, not decoration.
3. **Oversized Type Scale** — Headlines dominate. 8xl, 9xl sizes. Words become graphic elements.
4. **Line-Based Visual System** — Lines create structure: hairlines, thick rules, borders. No filled shapes, no shadows, no colored backgrounds (except inversions).
5. **Sharp Geometric Precision** — Zero border radius everywhere. 0px. No exceptions. Perfect 90-degree corners.
6. **Dramatic Negative Space** — Generous margins and padding. Whitespace is active, not empty.
7. **Inversion for Emphasis** — Instead of accent colors, swap black/white (black bg, white text) to highlight important elements.

### What This Design Is NOT

Never do any of these:

- ❌ Use any color other than black, white, and the two grays (#525252, #E5E5E5)
- ❌ Use rounded corners (border-radius > 0) on anything
- ❌ Use drop shadows on anything
- ❌ Use gradients on anything
- ❌ Use slow animations (> 100ms) except for image filter transitions
- ❌ Use bouncy, springy, or parallax animations
- ❌ Use colored status indicators (green/yellow/red) — use text labels, border weight, and inversion instead
- ❌ Use the old terracotta/sage/purple palette anywhere
- ❌ Use filled colored backgrounds for badges or chips — use borders and text contrast
- ❌ Default to "friendly" or "approachable" UI patterns — this is editorial and commanding

### How Emphasis Works Without Color

Since we have no color, the system uses these four tools for hierarchy:

| Tool | Low emphasis | Medium emphasis | High emphasis | Maximum emphasis |
|------|-------------|----------------|---------------|-----------------|
| **Border weight** | 1px `#E5E5E5` | 1px `#000` | 2px `#000` | 4–8px `#000` |
| **Type scale** | xs–sm (mono) | base–lg (body serif) | 3xl–5xl (display serif) | 7xl–9xl (display serif) |
| **Inversion** | — | — | Black border on white | Full black bg, white text |
| **Spacing** | 8–16px | 24–32px | 48–64px | 96–160px |

---

## 2. Design Tokens

### 2.1 Colors

```css
:root {
  --background: #FFFFFF;
  --foreground: #000000;
  --muted: #F5F5F5;
  --muted-foreground: #525252;
  --border: #000000;
  --border-light: #E5E5E5;
  --card: #FFFFFF;
  --card-foreground: #000000;
  --ring: #000000;
}
```

**Inverted variant** (for emphasis sections):
```css
.inverted {
  --background: #000000;
  --foreground: #FFFFFF;
  --muted: #1A1A1A;
  --muted-foreground: #A3A3A3;
  --border: #FFFFFF;
  --border-light: rgba(255, 255, 255, 0.2);
  --card: #000000;
  --card-foreground: #FFFFFF;
  --ring: #FFFFFF;
}
```

**CRITICAL:** Remove all references to the old palette — no `#C47B5A` (terracotta), `#7D8C6E` (sage), `#8B8FC7` (purple), or any warm tones. The entire palette is now five values: `#000`, `#FFF`, `#F5F5F5`, `#E5E5E5`, `#525252`.

### 2.2 Typography

**Font Stack:**
```css
--font-display: 'Playfair Display', Georgia, serif;
--font-body: 'Source Serif 4', Georgia, serif;
--font-mono: 'JetBrains Mono', monospace;
```

**Google Fonts import** (add to `layout.tsx` or `globals.css`):
```
https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,500;0,600;0,700;0,800;0,900;1,400;1,500;1,600;1,700;1,800;1,900&family=Source+Serif+4:ital,opsz,wght@0,8..60,300;0,8..60,400;0,8..60,500;0,8..60,600;0,8..60,700;1,8..60,300;1,8..60,400;1,8..60,500&family=JetBrains+Mono:wght@300;400;500&display=swap
```

**Font usage rules:**
- `font-display` (Playfair Display): ALL headlines, section titles, regime names, the logo wordmark, pull-quote style elements, score numbers when displayed large
- `font-body` (Source Serif 4): Body text, descriptions, recommendation text, longer explanatory content
- `font-mono` (JetBrains Mono): ALL data values (VRP, IV, RV, scores in tables, term slope numbers), labels, metadata, dates, column headers, ticker symbols, Greek letters display, small caps categories

**Type Scale:**

| Token | Size | Rem | Usage |
|-------|------|-----|-------|
| `xs` | 12px | 0.75rem | Fine metadata, timestamps |
| `sm` | 14px | 0.875rem | Column headers, chip labels, captions |
| `base` | 16px | 1rem | Body text minimum |
| `lg` | 18px | 1.125rem | Preferred body text |
| `xl` | 20px | 1.25rem | Lead paragraphs, metric values |
| `2xl` | 24px | 1.5rem | Section intro text |
| `3xl` | 32px | 2rem | Subheadings |
| `4xl` | 40px | 2.5rem | Section titles |
| `5xl` | 56px | 3.5rem | Page title |
| `6xl` | 72px | 4.5rem | Hero subheading |
| `7xl` | 96px | 6rem | Hero headline |
| `8xl` | 128px | 8rem | Display statement |
| `9xl` | 160px | 10rem | Oversized statement |

**Letter spacing rules:**
- Headlines (5xl+): `tracking-tight` (-0.025em) or `tracking-tighter` (-0.05em)
- Body text: `tracking-normal` (0)
- Labels, column headers, button text, metadata: `tracking-widest` (0.1em) + `uppercase`

**Line height rules:**
- Display headlines (7xl+): `leading-none` (1.0)
- Standard headlines: `leading-tight` (1.1)
- Body text: `leading-relaxed` (1.625)

### 2.3 Spacing

```
Base unit: 4px

Spacing scale:
1: 4px    5: 20px    9: 48px
2: 8px    6: 24px   10: 64px
3: 12px   7: 32px   11: 96px
4: 16px   8: 40px   12: 128px
```

**Section padding:** `py-24 md:py-32 lg:py-40` (96px / 128px / 160px)

### 2.4 Border Radius

```
ALL: 0px
```

Override Tailwind defaults — force every `rounded-*` class to resolve to 0. In `tailwind.config.js`:

```js
borderRadius: {
  none: '0px',
  DEFAULT: '0px',
  sm: '0px',
  md: '0px',
  lg: '0px',
  xl: '0px',
  '2xl': '0px',
  full: '0px',
}
```

### 2.5 Borders

| Token | Value | Usage |
|-------|-------|-------|
| `hairline` | `1px solid #E5E5E5` | Subtle dividers within cards |
| `thin` | `1px solid #000000` | Standard borders, card outlines |
| `medium` | `2px solid #000000` | Emphasis borders, table header underline |
| `thick` | `4px solid #000000` | Section dividers between major page areas |
| `ultra` | `8px solid #000000` | Hero decorative rules, maximum impact |

**Rule:** Heavy horizontal rules (`4px solid #000`) BETWEEN every major section of the dashboard. This is non-negotiable.

### 2.6 Shadows

```
ALL: none
```

Override Tailwind defaults — force every `shadow-*` class to resolve to `none`.

```js
boxShadow: {
  none: 'none',
  DEFAULT: 'none',
  sm: 'none',
  md: 'none',
  lg: 'none',
  xl: 'none',
}
```

Remove all `box-shadow`, `drop-shadow`, and elevation effects from every component.

### 2.7 Textures

These subtle background patterns are **required** to prevent the design from feeling flat. Apply them as pseudo-elements or overlay divs with `pointer-events-none`.

**IMPORTANT:** Any element using a texture class MUST have `position: relative` and `overflow: hidden` set on it, so the pseudo-element stays contained.

**Noise texture** (global — apply to body or main container):
```css
.texture-noise::after {
  content: '';
  position: absolute;
  inset: 0;
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.8' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)'/%3E%3C/svg%3E");
  opacity: 0.02;
  pointer-events: none;
  z-index: 0;
}
```

**Horizontal lines** (for light background sections):
```css
.texture-lines::before {
  content: '';
  position: absolute;
  inset: 0;
  background-image: repeating-linear-gradient(
    0deg, transparent, transparent 1px, #000 1px, #000 2px
  );
  background-size: 100% 4px;
  opacity: 0.015;
  pointer-events: none;
  z-index: 0;
}
```

**Grid pattern** (for data-heavy sections like Leaderboard):
```css
.texture-grid::before {
  content: '';
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(#00000008 1px, transparent 1px),
    linear-gradient(90deg, #00000008 1px, transparent 1px);
  background-size: 40px 40px;
  opacity: 0.015;
  pointer-events: none;
  z-index: 0;
}
```

**Diagonal lines** (for process or timeline sections):
```css
.texture-diagonal::before {
  content: '';
  position: absolute;
  inset: 0;
  background-image: repeating-linear-gradient(
    45deg, transparent, transparent 40px, #00000008 40px, #00000008 42px
  );
  opacity: 0.01;
  pointer-events: none;
  z-index: 0;
}
```

**Inverted vertical lines** (for black-background sections like regime banner in HOSTILE):
```css
.texture-inverted-lines::before {
  content: '';
  position: absolute;
  inset: 0;
  background-image: repeating-linear-gradient(
    90deg, transparent, transparent 1px, #fff 1px, #fff 2px
  );
  background-size: 4px 100%;
  opacity: 0.03;
  pointer-events: none;
  z-index: 0;
}
```

**Inverted radial glow** (for dark CTA sections — subtle light bloom at top):
```css
.texture-inverted-radial::before {
  content: '';
  position: absolute;
  inset: 0;
  background-image: radial-gradient(
    circle at top center, #ffffff, transparent 70%
  );
  opacity: 0.05;
  pointer-events: none;
  z-index: 0;
}
```

**Usage note:** Texture pseudo-elements use `z-index: 0`. All interactive content within a textured container should have `position: relative; z-index: 1;` to sit above the texture layer.
```

### 2.8 Motion

**Philosophy:** Minimal and instant. Favor stillness and instant state changes.

| Interaction | Duration | Notes |
|-------------|----------|-------|
| Button hover | 0ms | `transition-none` — instant inversion |
| Card hover | 100ms | `transition-colors duration-100` |
| Row hover | 100ms | Background/text swap |
| Link hover | 0ms | Underline appears instantly |
| Image filter | 300ms | Only exception — grayscale removal |
| Everything else | 0ms | No animation |

**Forbidden:**
- Any `duration-200` or higher (except image filters)
- `ease-in-out`, `ease-out`, spring/bounce easing
- Parallax, floating, or continuous animations
- Staggered entrance animations (except initial page load)

### 2.9 Layout

```
Container max-width: 1152px (72rem / max-w-6xl)
Container padding: px-6 md:px-8 lg:px-12
Grid: CSS Grid, 12-column base
```

**Breakpoints:** sm: 640px, md: 768px, lg: 1024px, xl: 1280px

---

## 3. Component Patterns

### 3.1 Buttons

**Primary (CTA):**
```
bg-black text-white border-2 border-black
px-8 py-4
font-mono text-sm font-medium uppercase tracking-widest
hover:bg-white hover:text-black hover:border-black
transition-none
focus-visible:outline focus-visible:outline-[3px] focus-visible:outline-black focus-visible:outline-offset-[3px]
```
Append `→` arrow for CTAs. Note: default state uses `border-2 border-black` (invisible against black bg) to prevent 2px layout shift on hover.

**Secondary (Outline):**
```
bg-transparent text-black border-2 border-black
px-8 py-4
font-mono text-sm font-medium uppercase tracking-widest
hover:bg-black hover:text-white
transition-none
focus-visible:outline focus-visible:outline-[3px] focus-visible:outline-black focus-visible:outline-offset-[3px]
```

**Ghost (Text link style):**
```
bg-transparent text-black border-0
font-mono text-sm font-medium uppercase tracking-widest
hover:underline
focus-visible:outline focus-visible:outline-[3px] focus-visible:outline-black focus-visible:outline-offset-[3px]
```

### 3.2 Cards

**Standard (bordered):**
```
bg-white border border-black p-6 md:p-8
no shadow, no radius
```

**Hover-invertible card:**
```
group bg-white border border-black p-6 md:p-8
transition-colors duration-100
hover:bg-black hover:text-white
[child elements use group-hover:text-white, group-hover:border-white]
```

**Inverted card (always dark):**
```
bg-black text-white p-6 md:p-8
```

### 3.3 Data Labels

Used for column headers, metadata, section labels:
```
font-mono text-xs font-medium uppercase tracking-widest text-[#525252]
```

### 3.4 Data Values

Used for metric numbers (VRP, IV, scores, etc.):
```
font-mono text-base tabular-nums
```

For large featured data values:
```
font-display text-3xl md:text-4xl font-bold tracking-tight
```

### 3.5 Horizontal Rules

Between major dashboard sections:
```html
<hr class="border-0 border-t-4 border-black" />
```

### 3.6 Section Dividers Within Components

Subtle internal dividers:
```html
<hr class="border-0 border-t border-[#E5E5E5]" />
```

### 3.7 Tables

```
Header row: font-mono text-xs uppercase tracking-widest text-[#525252] border-b-2 border-black
Body rows: font-body text-base border-b border-[#E5E5E5]
Numeric cells: font-mono text-right tabular-nums
Row hover: bg-[#F5F5F5] transition-colors duration-100
Selected row: bg-black text-white (full inversion)
```

### 3.8 Input Fields

```
bg-white border-0 border-b-2 border-black
px-0 py-3
font-body text-base
placeholder:text-[#525252] placeholder:italic
focus:border-b-4 focus:outline-none
```

### 3.9 Tooltips

```
bg-black text-white
px-3 py-2
font-mono text-xs
no radius, no shadow
```

### 3.10 Focus States (Accessibility)

All interactive elements MUST have visible focus states using `focus-visible`:

```
Buttons:     focus-visible:outline focus-visible:outline-[3px] focus-visible:outline-black focus-visible:outline-offset-[3px]
Inputs:      focus:border-b-4 focus:outline-none
Links:       focus-visible:underline focus-visible:outline-none
Table rows:  focus-visible:outline focus-visible:outline-2 focus-visible:outline-black focus-visible:outline-offset-[-2px]
```

**Note on Tailwind outline sizes:** Tailwind v3 only includes `outline-0`, `outline-1`, `outline-2`, `outline-4`, `outline-8` as built-in utilities. For 3px values, use bracket notation: `outline-[3px]`, `outline-offset-[3px]`.

---

## 4. Dashboard Component Map — Option Harvest Specific

This section maps every existing Option Harvest component to its monochrome equivalent. Use this as your implementation checklist.

### 4.1 Navbar (`Navbar.tsx`)

**Current:** Terracotta-accented top bar with Source Serif logo, General Sans nav items, theme toggle.

**Monochrome translation:**

```
Container: bg-white border-b border-black px-6 md:px-8 h-[72px] md:h-[56px]
Logo "Theta Harvest": font-display text-xl font-bold text-black tracking-tight
Nav items: font-mono text-xs uppercase tracking-widest text-black
  hover:underline
Refresh button: Secondary button style (outlined)
Date display: font-mono text-xs text-[#525252] uppercase tracking-widest
```

**Remove:** Theme toggle (no dark mode in this system — the design IS black and white). If dark mode switching is still desired as a feature, keep it but implement it as an inverted scheme where the base is black with white text, maintaining the same monochrome constraint.

**Key change:** Replace the colored "Market Closed" / "Market Open" badge with a text-only indicator using border weight:
```
Market Open: font-mono text-xs uppercase tracking-widest, border-b-2 border-black
Market Closed: font-mono text-xs uppercase tracking-widest text-[#525252]
```

### 4.2 Regime Banner (`RegimeBanner.tsx`)

**Current:** Left-border colored by regime severity (sage/yellow/red), large serif regime name, four metric indicators with color-coded thresholds.

**Monochrome translation by regime:**

| Regime | Container Style | Name Style |
|--------|----------------|------------|
| **FAVORABLE** | `bg-white border-2 border-black p-6` | `font-display text-4xl font-bold` |
| **NORMAL** | `bg-white border border-black p-6` | `font-display text-4xl font-bold` |
| **CAUTION** | `bg-white border-l-8 border-black p-6` | `font-display text-4xl font-bold italic` |
| **HOSTILE** | `bg-black text-white p-6` + inverted line texture | `font-display text-4xl font-bold uppercase tracking-tight` |

**Metric indicators (Avg VRP, Term Slope, RV Accel, Tradeable Count):**
```
Label: font-mono text-xs uppercase tracking-widest text-[#525252]
Value: font-mono text-xl font-medium text-black
```

Instead of color-coding good/bad thresholds, use these visual cues:
- **Good value:** Normal weight, regular style
- **Warning value:** Bold weight + italic
- **Bad value:** Bold weight + underline (2px black) or inverted chip (`bg-black text-white px-2`)

**Regime message (the subtitle text):**
```
font-body text-lg text-[#525252] italic
```

### 4.3 Leaderboard (`Leaderboard.tsx`)

**Current:** Main data table with colored VRP bars, colored score pills, colored action/sizing chips.

**Monochrome translation:**

**Table container:**
```
bg-white border border-black
relative (for texture overlay)
Apply .texture-grid
```

**Column headers:**
```
font-mono text-xs uppercase tracking-widest text-[#525252]
border-b-2 border-black
py-3 px-4
```

**Data rows:**
```
border-b border-[#E5E5E5]
py-3 px-4
hover:bg-[#F5F5F5] transition-colors duration-100
cursor-pointer
```

**Selected row (when ticker is clicked):**
```
bg-black text-white
[all child text becomes white]
[borders within row become white or transparent]
```

**Ticker symbol column:**
```
font-mono text-sm font-bold tracking-wide uppercase
```

**Score display:**
Replace the colored pill with a typographic treatment:

| Score Range | Style |
|-------------|-------|
| ≥ 70 (SELL territory) | `font-display text-2xl font-bold` inside `bg-black text-white px-3 py-1` inverted box |
| 50–69 (CONDITIONAL) | `font-display text-2xl font-bold` inside `border-2 border-black px-3 py-1` outlined box |
| 1–49 (NO EDGE) | `font-mono text-lg text-[#525252]` plain text |
| 0 (SKIP) | `font-mono text-lg text-[#525252] line-through` struck through |

**VRP bar visualization:**
Replace the colored horizontal bar with a monochrome bar:
```
Track: bg-[#E5E5E5] h-[6px] w-full
Fill: bg-black h-[6px]
Width: proportional to VRP value (0–20 range or dynamic max)
```
No color gradients. The bar is always black on light gray.

**Action chip:**
Replace colored chips with bordered text labels:

| Action | Style |
|--------|-------|
| SELL PREMIUM | `bg-black text-white font-mono text-xs uppercase tracking-widest px-3 py-1` |
| CONDITIONAL | `border border-black text-black font-mono text-xs uppercase tracking-widest px-3 py-1` |
| NO EDGE | `text-[#525252] font-mono text-xs uppercase tracking-widest` (no container) |
| SKIP | `text-[#525252] font-mono text-xs uppercase tracking-widest line-through` |
| AVOID | `bg-black text-white font-mono text-xs uppercase tracking-widest px-3 py-1 border-l-4 border-white` (inverted with heavy left mark) |

**Sizing chip:**
Replace colored chips:

| Sizing | Style |
|--------|-------|
| Full | `font-mono text-xs font-bold uppercase` |
| Half | `font-mono text-xs uppercase text-[#525252]` |
| Quarter | `font-mono text-xs uppercase text-[#525252] italic` |

**Regime per-ticker indicator** (GARBAGE TIME / SHOOTAROUND / HEAT CHECK / CLUTCH Q4):

| Regime | Style |
|--------|-------|
| CLUTCH Q4 | `bg-black text-white font-mono text-[10px] uppercase tracking-widest px-2 py-0.5` |
| HEAT CHECK | `border border-black font-mono text-[10px] uppercase tracking-widest px-2 py-0.5` |
| SHOOTAROUND | `font-mono text-[10px] uppercase tracking-widest text-[#525252]` (no box) |
| GARBAGE TIME | `font-mono text-[10px] uppercase tracking-widest text-[#525252] line-through` |
| DANGER | `bg-black text-white font-mono text-[10px] uppercase tracking-widest px-2 py-0.5` + `border-l-4 border-white` |
| CAUTION | `bg-black text-white font-mono text-[10px] uppercase tracking-widest px-2 py-0.5 italic` |
| AVOID | `bg-black text-white font-mono text-[10px] uppercase tracking-widest px-2 py-0.5` + `line-through decoration-white` |

**Key design principle for the Leaderboard:** The table should feel like a financial newspaper's market data page — dense, precise, and confident. Mono typography for all numbers. Perfect column alignment. Generous column spacing. The selected row's full inversion (black bg) is the primary interaction affordance.

### 4.4 Detail Panel (`DetailPanel.tsx`)

**Current:** 2×4 metrics grid, position construction hints, flags, two Recharts charts. Uses terracotta/sage colors.

**Monochrome translation:**

**Panel container:**
```
bg-white border-l-4 border-black p-6 md:p-8
OR
bg-white border border-black p-6 md:p-8
```

**Ticker title (selected ticker):**
```
font-display text-4xl md:text-5xl font-bold tracking-tight text-black
```

**Ticker name subtitle:**
```
font-body text-lg text-[#525252]
```

**2×4 Metrics Grid:**

Each metric cell:
```
Container: border border-[#E5E5E5] p-4
  hover:border-black transition-colors duration-100
Label: font-mono text-xs uppercase tracking-widest text-[#525252] mb-2
Value: font-mono text-xl font-medium text-black tabular-nums
Unit/context: font-mono text-xs text-[#525252] ml-1
```

Metric cells for the 8 values: VRP, Term Slope, RV Accel, IV Percentile, Skew, θ/ν (Theta/Vega), ATR14, Earnings

**Metric value emphasis rules** (replaces color-coding):

| Condition | Value styling |
|-----------|--------------|
| Good/favorable | Normal weight |
| Neutral | Normal weight, `text-[#525252]` |
| Warning | `font-bold italic` |
| Bad/dangerous | `font-bold underline decoration-2 decoration-black` |

For example:
- VRP > 8: normal (good)
- VRP 3–8: normal
- VRP < 3: bold italic
- VRP < 0: bold, underline, inverted inline chip

**Position Construction Hints:**

```
Container: bg-[#F5F5F5] p-6 border-t-4 border-black
Section label: font-mono text-xs uppercase tracking-widest text-[#525252] mb-4
```

| Hint | Style |
|------|-------|
| Delta | `font-mono text-base font-medium` |
| Structure | `font-body text-base` |
| DTE | `font-mono text-base tabular-nums` |
| Sizing | `font-mono text-base font-bold uppercase` |

**Flags display (warning badges):**
Replace colored warning badges with:
```
Container: border-l-4 border-black bg-[#F5F5F5] px-4 py-3 mt-2
Text: font-mono text-sm text-black
Icon prefix: "⚠" or "—" character, not a colored icon
```

For DANGER-level flags:
```
Container: bg-black text-white px-4 py-3 mt-2
Text: font-mono text-sm text-white
```

### 4.5 Charts (Recharts in DetailPanel)

**Current:** IV vs RV 120-day line chart and Term Structure curve using terracotta/sage/purple stroke colors.

**Monochrome Recharts configuration:**

**IV vs RV History Chart:**
```tsx
// Line colors — use only black and gray, differentiate with stroke style
<Line
  dataKey="iv"
  stroke="#000000"
  strokeWidth={2}
  dot={false}
/>
<Line
  dataKey="rv"
  stroke="#000000"
  strokeWidth={1}
  strokeDasharray="6 4"  // Dashed line to differentiate from IV
  dot={false}
/>
// Optional: VRP area between the two lines
<Area
  dataKey="vrp"
  fill="#000000"
  fillOpacity={0.05}
  stroke="none"
/>

// Axes
<XAxis
  tick={{ fontFamily: 'JetBrains Mono', fontSize: 11, fill: '#525252' }}
  axisLine={{ stroke: '#000000', strokeWidth: 1 }}
  tickLine={{ stroke: '#E5E5E5' }}
/>
<YAxis
  tick={{ fontFamily: 'JetBrains Mono', fontSize: 11, fill: '#525252' }}
  axisLine={{ stroke: '#000000', strokeWidth: 1 }}
  tickLine={false}
/>

// Grid
<CartesianGrid
  stroke="#E5E5E5"
  strokeDasharray="1 4"
  vertical={false}
/>

// Tooltip
<Tooltip
  contentStyle={{
    backgroundColor: '#000000',
    border: 'none',
    borderRadius: '0px',
    fontFamily: 'JetBrains Mono',
    fontSize: '12px',
    color: '#FFFFFF',
    padding: '8px 12px',
  }}
  labelStyle={{ color: '#FFFFFF', fontFamily: 'JetBrains Mono' }}
  itemStyle={{ color: '#FFFFFF' }}
/>

// Legend — use text labels, not colored squares
// Custom legend component with:
// "— IV (solid)" and "--- RV (dashed)" text
```

**Differentiation strategy for chart lines WITHOUT color:**
- IV line: solid, 2px weight
- RV line: dashed, 1px weight
- VRP area: 5% opacity black fill between IV and RV
- Term structure front: solid, 2px
- Term structure back: dotted, 1px

**Term Structure Chart:**
```tsx
<Line
  dataKey="iv"
  stroke="#000000"
  strokeWidth={2}
  dot={{ fill: '#000000', r: 3 }}
/>

// Reference line at slope = 1.0 (contango/backwardation boundary)
<ReferenceLine
  y={referenceValue}
  stroke="#000000"
  strokeDasharray="4 4"
  strokeWidth={1}
  label={{
    value: "Contango / Backwardation",
    fontFamily: 'JetBrains Mono',
    fontSize: 10,
    fill: '#525252',
  }}
/>
```

**Critical:** Update the `useCssColors()` hook. Since all chart colors are now `#000000` or `#525252`, the hook may simplify significantly. The differentiation is via stroke width, dash pattern, and opacity — not color.

### 4.6 Theme System Changes

**Current:** `useTheme.ts` toggles between light/dark via `data-theme` attribute. `globals.css` has `:root` and `[data-theme="dark"]` variable sets.

**Options for monochrome:**

**Option A — Remove dark mode entirely:**
Strip the theme toggle, the `useTheme` hook, the `data-theme` attribute, and the dark CSS variables. The system is inherently high-contrast (21:1 ratio). Simplest approach.

**Option B — Invert the entire page as "dark mode":**
Keep the toggle but make dark mode a full page inversion:
```css
[data-theme="dark"] {
  --background: #000000;
  --foreground: #FFFFFF;
  --muted: #1A1A1A;
  --muted-foreground: #A3A3A3;
  --border: #FFFFFF;
  --border-light: #333333;
  --card: #000000;
  --card-foreground: #FFFFFF;
  --ring: #FFFFFF;
}
```
This preserves the monochrome constraint while offering a genuine dark option.

**Recommendation:** Option B — it's a natural extension of the inversion principle and maintains the existing architecture.

### 4.7 Tailwind Config Updates

Replace the current `tailwind.config.js` theme extension:

```js
// tailwind.config.js
module.exports = {
  theme: {
    extend: {
      fontFamily: {
        display: ["'Playfair Display'", 'Georgia', 'serif'],
        body: ["'Source Serif 4'", 'Georgia', 'serif'],
        mono: ["'JetBrains Mono'", 'monospace'],
      },
      borderRadius: {
        none: '0px',
        DEFAULT: '0px',
        sm: '0px',
        md: '0px',
        lg: '0px',
        xl: '0px',
        '2xl': '0px',
        full: '0px',
      },
      boxShadow: {
        none: 'none',
        DEFAULT: 'none',
        sm: 'none',
        md: 'none',
        lg: 'none',
        xl: 'none',
        '2xl': 'none',
      },
      borderWidth: {
        hairline: '1px',
        thin: '1px',
        medium: '2px',
        thick: '4px',
        ultra: '8px',
      },
      transitionDuration: {
        instant: '0ms',
        snap: '100ms',
      },
    },
  },
}
```

### 4.8 globals.css Rewrite

Replace all CSS custom properties. Remove:
- All `color-mix()` utilities (`.bg-primary-subtle`, `.border-success-30`, etc.)
- The risograph grain texture (replace with monochrome noise texture)
- All warm shadow definitions
- All color variables beyond the five monochrome values

Keep:
- CSS variable structure (`:root` + `[data-theme="dark"]`)
- The `useCssColors` hook pattern (still needed for Recharts, just with new values)

### 4.9 `scoring.ts` and `types.ts` — Visual Mapping

No logic changes needed. The scoring formula stays identical. Only the **visual representation** of score values changes (as defined in Section 4.3 above).

Ensure that `DashboardTicker` type still works — the frontend scoring output maps to the same action labels (SELL PREMIUM, CONDITIONAL, NO EDGE, SKIP), they just render differently.

### 4.10 Responsive Behavior

**Mobile adaptations specific to Option Harvest:**

- Leaderboard on mobile: Show only Ticker, Score, Action columns. Hide VRP bar, sizing, term slope columns.
- Detail Panel on mobile: Full-width below leaderboard (not side panel). Metrics grid becomes 2×4 → 1×8 vertical stack.
- Regime Banner: Stack metrics vertically. Regime name stays large (text-3xl minimum).
- Charts: Full-width, reduce height. Hide legend on mobile — label directly on chart lines.
- Section dividers: Maintain 4px thick black rules.
- Typography: Reduce hero-scale text but keep it impactful (5xl minimum on mobile for page title).

---

## 5. Implementation Checklist

Use this to track progress when implementing the reskin:

### Phase 1 — Foundation (do first)
- [ ] Update `tailwind.config.js` with monochrome overrides (radius, shadow, fonts, borders)
- [ ] Rewrite `globals.css` custom properties (remove all color, add monochrome tokens)
- [ ] Add Google Fonts import for Playfair Display + Source Serif 4 + JetBrains Mono
- [ ] Update `layout.tsx` font loading
- [ ] Add texture utility classes (`.texture-noise`, `.texture-grid`, `.texture-lines`, `.texture-diagonal`, `.texture-inverted-lines`, `.texture-inverted-radial`)

### Phase 2 — Core Components
- [ ] Navbar: Strip colors, apply monochrome typography, remove or adapt theme toggle
- [ ] Regime Banner: Implement the four regime visual states (FAVORABLE/NORMAL/CAUTION/HOSTILE)
- [ ] Leaderboard table: New header styles, row styles, selected-row inversion
- [ ] Score display: Typographic treatment replacing colored pills
- [ ] Action chips: Border/inversion based labels replacing colored chips
- [ ] VRP bar: Black on gray replacing colored gradient
- [ ] Regime badges: Monochrome versions of CLUTCH Q4 / HEAT CHECK / etc.

### Phase 3 — Detail Panel
- [ ] Panel container and header typography
- [ ] 2×4 metrics grid with monochrome emphasis rules
- [ ] Position construction hints section
- [ ] Flags display (warning badges)
- [ ] Charts: Update all Recharts stroke/fill colors, implement dash-pattern differentiation
- [ ] Update `useCssColors()` hook for new palette

### Phase 4 — Polish
- [ ] Apply textures to appropriate sections
- [ ] Verify all focus states (accessibility)
- [ ] Add 4px thick section dividers between Navbar / Regime / Leaderboard / Detail
- [ ] Test responsive behavior at all breakpoints
- [ ] Verify 0px radius on every single element (search codebase for `rounded` classes)
- [ ] Verify no shadows remain anywhere (search for `shadow` classes)
- [ ] Verify no old palette colors remain (search for `#C47B5A`, `#7D8C6E`, `#8B8FC7`, `terracotta`, `sage`, `purple`)

---

## 6. Quick Reference Card

When in doubt during implementation, check this:

| Question | Answer |
|----------|--------|
| What color should this be? | Black (`#000`) or white (`#FFF`). For secondary: `#525252`. For subtle borders: `#E5E5E5`. For muted backgrounds: `#F5F5F5`. **Nothing else.** |
| How do I show emphasis? | Invert it (black bg, white text). Or make the border thicker. Or make the type bigger. |
| How do I show a warning? | Bold + italic text. Or inverted chip. Or heavy left border. **Not color.** |
| How do I show danger? | Full inversion (bg-black text-white). Heavy border. Uppercase. |
| Should this have rounded corners? | No. 0px. Always. |
| Should this have a shadow? | No. Never. |
| What font for this number? | JetBrains Mono. Always mono for data. |
| What font for this heading? | Playfair Display. Always serif display for headings. |
| What font for this body text? | Source Serif 4. Always serif for body. |
| What font for this label/metadata? | JetBrains Mono, uppercase, tracking-widest. |
| Should this button animate on hover? | Instant inversion. 0ms transition. |
| Should this have a transition? | Probably not. 100ms max if yes. |
| Should I add color to make this more clear? | No. Use typography weight, scale, inversion, or border weight instead. |
