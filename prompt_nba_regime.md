# Rename Market Regime Labels to NBA Theme + Fix FAVORABLE Color

## Overview

Two changes in one:
1. Replace the current market regime labels and messages with NBA-themed equivalents
2. Fix a pre-existing bug where NORMAL and FAVORABLE share the same color (both sage) — FAVORABLE should use the accent purple to visually distinguish "conditions are good" from "conditions are fine"

This is a frontend-only change — the underlying logic, thresholds, and triggers stay exactly the same.

## Before Writing Any Code

Read the codebase to find:

1. **RegimeBanner component** — where regime names, messages, and colors are rendered
2. **Any constants or enums** that define the regime names (HOSTILE, CAUTION, NORMAL, FAVORABLE)
3. **The regime detection logic** in the frontend — confirm the four regime tiers and their trigger conditions so you don't accidentally break them
4. **Any other components** that reference regime names or regime colors (tooltips, detail panel, etc.)
5. **The CSS custom properties / theme tokens** — find where colors like `--color-error`, `--color-warning`, `--color-secondary`, `--color-accent` are defined so you use the correct variables

## Name and Color Mapping

| Current | New Name | Message | Color |
|---------|----------|---------|-------|
| HOSTILE | **GARBAGE TIME** | "Game's out of reach — sit on the bench, no premium selling today" | Error red (`#C45A5A` / `var(--color-error)`) — unchanged |
| CAUTION | **CLUTCH Q4** | "Every possession counts — small positions, defined risk, no turnovers" | Warning gold (`#C49A5A` / `var(--color-warning)`) — unchanged |
| NORMAL | **SHOOTAROUND** | "Running your sets — standard conditions, execute the playbook" | Secondary sage (`#7D8C6E` / `var(--color-secondary)`) — unchanged |
| FAVORABLE | **HEAT CHECK** | "You're on fire — wide VRP in contango, keep shooting" | **Accent purple (`#9B9FD7` / `var(--color-accent)`) — CHANGED from secondary** |

## What to Change

1. **Regime display names** — replace the label text shown in the banner (the large serif font text)
2. **Regime messages** — replace the descriptive text next to the label
3. **FAVORABLE / HEAT CHECK color** — change from secondary (sage) to accent (purple) in both the left border, the regime name text color, and any metric indicator colors tied to this regime
4. **Read-only mode message** (shown during GARBAGE TIME) — update to: "Bench players only. No premium selling until the game resets."
5. **Keep everything else identical** — metric displays (AVG VRP, AVG TERM SLOPE, RV ACCEL, TRADEABLE), thresholds, trigger logic, and the red alert overlay for GARBAGE TIME

## Edge Cases

- Search the entire frontend codebase for any hardcoded references to "HOSTILE", "CAUTION", "NORMAL", "FAVORABLE" as display strings — update them all consistently
- If the backend returns regime names that get displayed anywhere, map them to NBA names at the frontend layer only — don't change backend strings
- If there are any aria-labels or accessibility attributes referencing regime names, update those too
- Make sure the HEAT CHECK purple works in both light and dark mode — use `#8B8FC7` for light mode and `#9B9FD7` for dark mode (matching the existing accent token in the theme)
