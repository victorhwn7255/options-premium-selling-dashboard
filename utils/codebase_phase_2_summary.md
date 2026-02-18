# Theta Harvest — Codebase Phase 2 Summary

> Phase 2 (v1.0.2): Educational modals, mobile responsiveness, market holiday awareness, data repair tooling, and UX polish.

---

## Table of Contents

1. [Phase 2 Overview](#1-phase-2-overview)
2. [Architecture Changes](#2-architecture-changes)
3. [New Frontend Components](#3-new-frontend-components)
4. [Modified Frontend Components](#4-modified-frontend-components)
5. [Backend Changes](#5-backend-changes)
6. [New Backend Scripts](#6-new-backend-scripts)
7. [Mobile Responsiveness](#7-mobile-responsiveness)
8. [Market Holiday Detection](#8-market-holiday-detection)
9. [Updated Scoring & Display](#9-updated-scoring--display)
10. [Updated API Behavior](#10-updated-api-behavior)
11. [File Inventory](#11-file-inventory)
12. [Known Issues & Tech Debt](#12-known-issues--tech-debt)
13. [Testing Checklist](#13-testing-checklist)

---

## 1. Phase 2 Overview

**Branch:** `v1.0.2` (single commit `14385f7` off `main`)

**What changed:** 15 files, +2,637 lines, −187 lines. All changes are additive — no breaking changes, no new dependencies, no schema migrations.

**Key deliverables:**

| Feature | Files | Impact |
|---------|-------|--------|
| Explain Metrics modal | `ExplainMetricsModal.tsx`, `metrics-content.ts` | Educational UX — plain-language metric definitions with analogies, formulas, and color-coded readings |
| Regime Guide modal | `RegimeGuideModal.tsx`, `RegimeSection.tsx` | Deep-dive into 4 market regimes with triggers, DOs/DON'Ts, and example trades |
| Mobile hamburger menu | `Navbar.tsx` | All navbar actions collapse into a dropdown on `< sm` screens |
| Mobile card leaderboard | `Leaderboard.tsx` | Card-based layout replaces table on `< sm`, with expandable inline detail |
| Inline detail panel | `Leaderboard.tsx`, `page.tsx` | DetailPanel now expands below selected row instead of in a separate zone |
| Market holiday awareness | `Navbar.tsx`, `main.py` | Frontend + backend detect weekends and 10 US market holidays |
| Stock-split data repair | `repair_rv.py` | CLI script to fix corrupted RV30/VRP from stock splits |
| Leaderboard number sizing | `Leaderboard.tsx` | All numeric data bumped to `text-sm` (14px) for readability |
| Signal column chip order | `Leaderboard.tsx` | SizingChip (Half/Quarter) now appears before ActionChip (SELL/NO EDGE) |

---

## 2. Architecture Changes

### No structural changes to the two-service stack.

```
┌─────────────────────┐      ┌─────────────────────┐
│   Next.js Frontend  │      │   FastAPI Backend    │
│   (port 3000)       │─────▶│   (port 8000/8030)  │
│                     │ /api │                     │
│  + Educational      │proxy │  + Holiday detection │
│    modals           │      │  + Repair scripts    │
│  + Mobile UX        │      │  + Scan gating       │
│  + Holiday display  │      │                      │
└─────────────────────┘      └─────────────────────┘
```

**What moved:**
- **DetailPanel** no longer renders in a separate zone in `page.tsx`. It now renders inline inside `Leaderboard.tsx` via `ExpandableDetail` wrapper (smooth height transition with `ResizeObserver`).
- **Regime computation** (`computeRegime`) is now exported from `RegimeBanner.tsx` so `page.tsx` can pass the current regime to `RegimeGuideModal`.

**New component tree:**

```
page.tsx
├── Navbar
│   └── ExplainMetricsModal (portal to document.body)
├── RegimeBanner
├── Leaderboard
│   ├── MobileTickerCard (< sm)
│   │   └── ExpandableDetail → DetailPanel
│   └── Desktop table row (≥ sm)
│       └── ExpandableDetail → DetailPanel
└── RegimeGuideModal (portal to document.body)
    └── RegimeSection (×4 regimes)
```

---

## 3. New Frontend Components

### 3.1 ExplainMetricsModal (`frontend/src/components/ExplainMetricsModal.tsx`)

**Lines:** 182 | **Purpose:** Educational modal explaining all dashboard metrics

**Features:**
- Portal-rendered to `document.body` with backdrop blur
- Escape-to-close, click-outside-to-close
- Focus trap (Tab/Shift+Tab cycles through focusable elements)
- Scroll lock on body when open
- 4 sections: Volatility, Structure, Trade, Scoring

**Content per metric card:**
- Emoji + name + category tag
- Plain-language explanation
- Analogy (basketball-themed)
- Formula in monospace
- Color-coded reading pills (good / ok / bad / neutral)

**Data source:** Imports `METRICS` and `SECTIONS` from `metrics-content.ts`.

**Props:**
```typescript
{ open: boolean; onClose: () => void }
```

---

### 3.2 RegimeGuideModal (`frontend/src/components/RegimeGuideModal.tsx`)

**Lines:** 352 | **Purpose:** In-depth guide to the 4 market regimes

**Regimes covered:**

| Regime | Color | Basketball Analogy |
|--------|-------|--------------------|
| GARBAGE TIME | Error (red) | Backwardation — no premium selling |
| CLUTCH Q4 | Warning (orange) | Rising vol — defined-risk only |
| SHOOTAROUND | Secondary (sage) | Normal contango — execute playbook |
| HEAT CHECK | Accent (purple) | Wide VRP — aggressive sizing |

**Per-regime content:**
- Tagline + trigger conditions (with numeric thresholds)
- Multi-paragraph explanation
- DOs / DON'Ts lists
- Example trade (ticker, structure, DTE, sizing, narrative)
- "CURRENT" badge if matches active regime

**Footer:** Quick reference for VRP, Term Slope, RV Accel, Tradeable count.

**Auto-scroll:** On open, scrolls to current regime section.

**Props:**
```typescript
{ open: boolean; onClose: () => void; currentRegime: string }
```

---

### 3.3 RegimeSection (`frontend/src/components/RegimeSection.tsx`)

**Lines:** 167 | **Purpose:** Reusable section for each regime in the guide modal

**Layout:** Trigger grid → explanation → DOs/DON'Ts side-by-side → example trade box.

**Color system:** `COLOR_MAP` maps tokens (`error`, `warning`, `secondary`, `accent`) to CSS variable tuples for border, background, text, and bullet styling.

**Props:**
```typescript
{
  regime: string; tagline: string; colorToken: string;
  triggers: { label: string; value: string }[];
  triggerLogic: string; explanation: string[];
  dos: string[]; donts: string[];
  example: { ticker: string; structure: string; dte: string; sizing: string; narrative: string };
  isCurrent: boolean;
}
```

---

### 3.4 metrics-content.ts (`frontend/src/lib/metrics-content.ts`)

**Lines:** 279 | **Purpose:** Centralized content data for ExplainMetricsModal

**Exports:**

```typescript
interface MetricDefinition {
  id: string; emoji: string; name: string; tag: string;
  section: string; explain: string; analogy: string;
  formulaLabel: string; formulas: string[];
  readings: { label: string; color: string; text: string }[];
}

const METRICS: MetricDefinition[]  // 12 metrics
const SECTIONS: { id: string; emoji: string; label: string }[]  // 4 sections
```

**Metrics covered:** Realized Volatility, Implied Volatility, VRP, IV Percentile, Term Structure, RV Acceleration, 25Δ Put Skew, Theta/Vega Ratio, ATR-14, Composite Score, Earnings Gate, Position Sizing.

---

## 4. Modified Frontend Components

### 4.1 Navbar.tsx (MAJOR REFACTOR — 147 → 357 lines)

**Changes:**

| Feature | Before | After |
|---------|--------|-------|
| Explain Metrics | `?` circle icon with hover tooltip | Text button "Explain Metrics" next to "Explain Market Regime" |
| Mobile layout | All items visible, cramped | Hamburger menu collapses all actions except logo + ThemeToggle |
| Market closed | Not detected | "zzz" icon with tooltip showing last scan date |
| Scan freshness | Not shown | Green checkmark with tooltip when scanned today (ET) |
| Earnings tooltip | "3 of 3 remaining" | "1 of 1 remaining" |

**New state:**
```typescript
const [menuOpen, setMenuOpen] = useState(false);
```

**New prop:** `onOpenRegimeGuide: () => void`

**Desktop layout (≥ sm):**
```
[Logo Theta Harvest] [Explain Market Regime] [Explain Metrics] ··· [Live Data] [status] [earnings] [date] [ThemeToggle]
```

**Mobile layout (< sm):**
```
Closed: [θ]                    [🌙] [☰]
Open:   [θ]                    [🌙] [✕]
        ┌─────────────────────────────┐
        │ [Explain Market Regime]     │
        │ [Explain Metrics]           │
        │ ● Live Data    [↻] [📅]    │
        │ Sat, Feb 15, 2026           │
        └─────────────────────────────┘
```

**Market holiday logic:** Full US market holiday calendar (10 holidays + observation rules + Easter via Gregorian algorithm). See [Section 8](#8-market-holiday-detection).

---

### 4.2 Leaderboard.tsx (MAJOR REFACTOR — 203 → 390 lines)

**Changes:**

| Feature | Before | After |
|---------|--------|-------|
| Detail panel | Separate zone in page.tsx | Inline expandable row below selected ticker |
| Mobile view | Responsive table (columns hidden) | Full card-based layout with expandable detail |
| Number font size | `text-xs md:text-sm` (12px→14px) | `text-sm` (14px) consistently |
| Signal column | ActionChip only, SizingChip in RV Accel column | SizingChip + ActionChip together in Signal column |
| Pre-gate score | Not shown | `(preGateScore)` displayed next to score pill |

**New sub-components (inline):**

| Component | Purpose |
|-----------|---------|
| `MobileTickerCard` | Card layout for `< sm` — ticker + metrics + chips |
| `ExpandableDetail` | Height-animated wrapper around DetailPanel |
| `VRPBar` | Horizontal bar (green ≥10, blue ≥5, gray <5) |
| `ScorePill` | Circular score badge (green/yellow/gray/red) |
| `ActionChip` | Signal label (SELL PREMIUM / CONDITIONAL / NO EDGE / SKIP) |
| `SizingChip` | Position size indicator (Half / Quarter) |

**New props:** `selectedData: DashboardTicker | null`

**ExpandableDetail mechanics:**
- `maxHeight` CSS transition (0.3s ease-in-out)
- `ResizeObserver` watches content for async chart loading
- Re-measures on ticker change

**Desktop row hover:** Rounded background highlight via inline style manipulation (avoids re-renders).

**Chip order in Signal column (desktop + mobile):**
```
[↓ Half] [SELL PREMIUM]     ← SizingChip first, then ActionChip
```

---

### 4.3 DetailPanel.tsx (minor — 365 → 392 lines)

**Changes:**
- **Top border:** Conditional color — red for SKIP'd tickers, terracotta otherwise
- **Skip reason box:** Shows pre-gate score with monitoring hint: `"Score without earnings gate: {preGateScore} — monitor post-earnings"`
- **Responsive padding:** `px-4 sm:px-6`, `py-4 sm:py-5` for mobile breathing room

---

### 4.4 RegimeBanner.tsx (minor — 89 → 116 lines)

**Changes:**
- **`computeRegime()` exported** — used by `page.tsx` to pass current regime to `RegimeGuideModal`
- **Responsive layout:** `flex-col sm:flex-row` for mobile stacking
- **Metrics grid:** `grid grid-cols-2 gap-x-6 gap-y-2 sm:flex` for mobile 2-column layout
- **HOSTILE alert:** "No premium selling today. Let's be disciplined and wait for better days."

---

### 4.5 page.tsx (refactored — 168 → 192 lines)

**Changes:**
- **Removed** standalone DetailPanel zone (Zone 3) — detail now lives inside Leaderboard
- **Added** `RegimeGuideModal` import + `regimeGuideOpen` state
- **Added** `currentRegime` via `computeRegime(scoredData).regime`
- **Earnings default:** Changed from `3` → `1`
- **Responsive padding:** `px-4 sm:px-6`

**New props passed:**
```typescript
<Navbar onOpenRegimeGuide={() => setRegimeGuideOpen(true)} ... />
<Leaderboard selectedData={selectedData} ... />
<RegimeGuideModal open={regimeGuideOpen} onClose={...} currentRegime={currentRegime} />
```

---

## 5. Backend Changes

### 5.1 main.py (672 → 733 lines, +61)

**New helpers:**

```python
def _us_market_holidays(year: int) -> set[date]:
    """Returns set of observed US market holiday dates for a given year."""
    # New Year's, MLK, Presidents', Good Friday, Memorial,
    # Juneteenth, Independence, Labor, Thanksgiving, Christmas
    # Observation: Sat → Fri, Sun → Mon
    # Easter via anonymous Gregorian algorithm

def _is_trading_day(d: date) -> bool:
    """True if d is a weekday AND not a US market holiday."""
```

**Scheduler upgrade:**
```python
# Before:
while candidate.weekday() >= 5:
    candidate += timedelta(days=1)

# After:
while not _is_trading_day(candidate.date()):
    candidate += timedelta(days=1)
```

**Scan endpoint gating:**
- `POST /api/scan` returns cached result with message on non-trading days
- `POST /api/earnings/refresh` blocks on non-trading days

**Earnings limit:** `_EARNINGS_REFRESH_LIMIT` changed from `3` → `1`.

---

## 6. New Backend Scripts

### 6.1 repair_rv.py (365 lines) — NEW

**Purpose:** Fix stock-split-corrupted RV30/VRP values in `daily_iv` table.

**Problem:** Stock splits (e.g., NFLX 10:1 on Nov 17 2025) leave stale unadjusted prices, producing absurd RV30 spikes (657% instead of ~30%).

**Algorithm:**
1. Fetch fresh adjusted daily bars from MarketData.app
2. Detect splits via log-return threshold (> 0.5 = ~65% move)
3. Adjust all pre-split bars to post-split scale
4. Recompute RV30 from adjusted closes
5. Recompute VRP = atm_iv − rv30
6. Update SQLite `daily_iv` table + rewrite daily CSV

**Usage:**
```bash
python repair_rv.py --tickers NFLX              # Fix one ticker
python repair_rv.py --tickers NFLX,AMZN         # Fix multiple
python repair_rv.py --all                        # Fix entire universe
python repair_rv.py --tickers NFLX --dry-run    # Preview changes
```

**Key functions:**
- `detect_and_adjust_splits(bars)` — split detection + retroactive adjustment
- `repair_ticker(client, ticker, dry_run)` — full per-ticker repair flow
- `_rewrite_daily_csv(ticker, bar_by_date, updates)` — CSV file correction

---

## 7. Mobile Responsiveness

### Breakpoint Strategy

All responsive changes use the `sm` (640px) breakpoint:

| Element | `< sm` (mobile) | `≥ sm` (desktop) |
|---------|-----------------|-------------------|
| Navbar | Logo + ThemeToggle + hamburger | Full inline layout |
| Navbar actions | Inside hamburger dropdown | Inline in header |
| Leaderboard | Card list (`MobileTickerCard`) | Table with columns |
| Detail panel | Expands below card | Expands below table row |
| Regime banner | Vertical stack, 2-col metrics grid | Horizontal flex |
| Modals | Full-width, scrollable | Max-width centered |

### Touch targets

Mobile buttons use `py-2 px-3` (minimum 44px touch target) vs desktop `py-1.5`.

### Hamburger menu behavior

- All buttons inside the menu call `setMenuOpen(false)` on click
- Menu uses `absolute top-[56px]` positioning below the header
- `bg-bg` inherits theme correctly in both light and dark modes
- `z-40` sits below modals (`z-50`) but above content

---

## 8. Market Holiday Detection

Implemented in both frontend (`Navbar.tsx`) and backend (`main.py`) with identical logic:

### 10 US Market Holidays

| Holiday | Rule |
|---------|------|
| New Year's Day | Jan 1 (observed) |
| MLK Day | 3rd Monday in January |
| Presidents' Day | 3rd Monday in February |
| Good Friday | Easter − 2 days (Gregorian algorithm) |
| Memorial Day | Last Monday in May |
| Juneteenth | Jun 19 (observed) |
| Independence Day | Jul 4 (observed) |
| Labor Day | 1st Monday in September |
| Thanksgiving | 4th Thursday in November |
| Christmas | Dec 25 (observed) |

### Observation rules

- Holiday falls on Saturday → observed Friday
- Holiday falls on Sunday → observed Monday

### Easter calculation

Anonymous Gregorian algorithm (no dependencies) — computes Easter Sunday for any year, then subtracts 2 days for Good Friday.

### Frontend behavior (Navbar)

- Non-trading day → pink "zzz" icon + tooltip: "Market closed — Showing data from {lastScanDate}"
- Prevents visual confusion when data appears stale on weekends/holidays

### Backend behavior (main.py)

- Cron scheduler skips non-trading days (was weekends-only before)
- `POST /api/scan` returns cached result with message on non-trading days
- `POST /api/earnings/refresh` blocks with "Market is closed today"

---

## 9. Updated Scoring & Display

### Leaderboard number sizing

All numeric data in the leaderboard upgraded from `text-xs md:text-sm` (12→14px responsive) to `text-sm` (14px) consistently:

| Element | Before | After |
|---------|--------|-------|
| VRP bar value | `text-xs md:text-sm` | `text-sm` |
| Term slope | `text-xs md:text-sm` | `text-sm` |
| RV acceleration | `text-xs md:text-sm` | `text-sm` |
| Earnings DTE | `text-xs md:text-sm` | `text-sm` |
| Score pill | `text-xs md:text-sm` | `text-sm` |
| Pre-gate score | `text-xs md:text-sm` | `text-sm` |
| Mobile card metrics | `text-2xs` | `text-sm` |

### Signal column chip order

**Before:** SizingChip in RV Accel column, ActionChip alone in Signal column.

**After:** Both chips in Signal column — SizingChip first (left), ActionChip second (right):

```
Desktop:  ... | RV Accel | ... | [↓ Half] [SELL PREMIUM] |
Mobile:   [↓ Half] [SELL PREMIUM]   (bottom of card)
```

### Earnings limit

Reduced from 3 refreshes/day to 1 refresh/day (both frontend default state and backend `_EARNINGS_REFRESH_LIMIT`).

---

## 10. Updated API Behavior

### POST /api/scan — non-trading day gating

```
Request:  POST /api/scan
Response (non-trading day):
{
  "timestamp": "...",
  "regime": { ... },
  "tickers": [ ... ],
  "cached": true,
  "message": "Market is closed today. Showing last available scan."
}
```

### POST /api/earnings/refresh — non-trading day gating

```
Request:  POST /api/earnings/refresh
Response (non-trading day):
{
  "status": "skipped",
  "message": "Market is closed today"
}
```

### Cron scheduler

- **Before:** Skips Saturday/Sunday only
- **After:** Skips all non-trading days (weekends + 10 US market holidays)

---

## 11. File Inventory

### New files (6)

| File | Lines | Purpose |
|------|-------|---------|
| `frontend/src/components/ExplainMetricsModal.tsx` | 182 | Metrics education modal |
| `frontend/src/components/RegimeGuideModal.tsx` | 352 | Regime guide modal |
| `frontend/src/components/RegimeSection.tsx` | 167 | Reusable regime section component |
| `frontend/src/lib/metrics-content.ts` | 279 | Metric definitions data |
| `backend/repair_rv.py` | 365 | Stock-split RV repair script |
| `utils/codebase_phase_2_summary.md` | this file | Phase 2 documentation |

### Modified files (9)

| File | Delta | Key changes |
|------|-------|-------------|
| `frontend/src/components/Navbar.tsx` | +210 | Hamburger menu, explain buttons, holiday detection |
| `frontend/src/components/Leaderboard.tsx` | +186 | Mobile cards, inline detail, font bump, chip swap |
| `frontend/src/components/DetailPanel.tsx` | +27 | Responsive padding, skip reason, conditional border |
| `frontend/src/components/RegimeBanner.tsx` | +27 | Export computeRegime, responsive layout |
| `frontend/src/app/page.tsx` | +24 | Remove Zone 3, add regime modal, pass new props |
| `backend/main.py` | +61 | Holiday detection, scan gating, earnings limit |
| `backend/backfill.py` | +1 | Minor constant formatting |

### Prompt/planning files (removed from working tree)

These scratch docs were used during development and deleted post-implementation:

- `bug_prompt.md`, `metrix_modal_prompt.md`
- `utils/prompt_regime_guide_modal.md`, `utils/prompt_nba_regime.md`
- `utils/prompt_pregate_score.md`, `utils/earnings_gated_prompt.md`

---

## 12. Known Issues & Tech Debt

### Carried from Phase 1
- `.env` committed to git with real API keys (security risk)
- No test suite (manual testing only, no CI)
- In-memory earnings counter resets on restart
- CSV `append_daily_csv` rewrites entire file (race condition)
- Silent API error handling on frontend (no user feedback)

### New in Phase 2
- **Duplicate components** — `ActionChip` and `SizingChip` are defined in both `Leaderboard.tsx` and `DetailPanel.tsx`. Should be extracted to shared module.
- **Duplicate holiday logic** — Market holiday calculation exists in both `Navbar.tsx` (JavaScript) and `main.py` (Python). Should expose a `/api/is-trading-day` endpoint instead.
- **Earnings limit hardcoded** — Changed from 3 → 1 in two places (frontend default, backend constant). Should be an env var or fetched from backend.
- **No automated tests for modals** — ExplainMetricsModal and RegimeGuideModal have no test coverage.

---

## 13. Testing Checklist

### Frontend

- [ ] "Explain Metrics" button opens modal (desktop: left nav, mobile: hamburger menu)
- [ ] "Explain Market Regime" button opens modal with current regime highlighted
- [ ] Mobile hamburger menu shows/hides all actions
- [ ] Hamburger + ThemeToggle pinned to right, no logo overlap
- [ ] Leaderboard: mobile card view renders correctly on 375px screen
- [ ] Leaderboard: clicking row/card expands DetailPanel inline with smooth animation
- [ ] Leaderboard: SizingChip appears before ActionChip in Signal column
- [ ] Leaderboard: all numbers render at `text-sm` (14px)
- [ ] Market closed: "zzz" icon visible on weekends/holidays
- [ ] Dark mode: hamburger dropdown, modals, and all new components theme correctly
- [ ] Modals: Escape closes, click-outside closes, focus trap works

### Backend

- [ ] Cron scheduler skips all 10 US market holidays (not just weekends)
- [ ] `POST /api/scan` returns cached result with message on non-trading days
- [ ] `POST /api/earnings/refresh` returns "Market is closed today" on non-trading days
- [ ] `repair_rv.py --tickers NFLX --dry-run` detects splits without writing
- [ ] `repair_rv.py --all` updates database and CSVs correctly

### Build

- [ ] `npm run build` passes with no errors
- [ ] `docker compose up --build` starts both services
- [ ] No TypeScript errors, no ESLint warnings in new files

---

*Generated from source code analysis of branch `v1.0.2` (commit `14385f7`) plus uncommitted working-tree changes. Cross-referenced against Phase 1 summary for delta identification.*
