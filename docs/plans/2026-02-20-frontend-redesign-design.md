# Frontend Redesign — Foundation Phase Design

**Date:** 2026-02-20
**Branch:** `frontend-redesign`
**Status:** Approved

## Overview

The current frontend works well functionally but has no distinct visual identity, no mobile
navigation, and no design system — all styles are applied inline using PrimeVue's default
Aura theme. This design establishes the foundation:

1. A custom PrimeVue preset (fonts, colors, radii, shadows)
2. A light/dark mode toggle with localStorage persistence
3. A responsive layout shell (sidebar on desktop, bottom tab bar on mobile)
4. Applying the new tokens to `RecipeCard.vue` (the most visible component)

Everything else (RecipeDetailView, RecipeEditorView, etc.) gets a passive visual upgrade
from the new preset — no manual changes needed to those files in this phase.

---

## Design Decisions

### Approach: PrimeVue Preset Extension

Extend PrimeVue 4's Aura preset using `definePreset()`. Two presets are registered:
`lightPreset` and `darkPreset`. A `useTheme()` composable handles switching and persistence.
This ensures all PrimeVue components (Button, InputText, Dialog, etc.) inherit the new
design automatically.

### Typography

| Role | Font | Weights |
|---|---|---|
| Display / headings | Cormorant (serif, variable) | 400, 600, 700 |
| Body / UI | Plus Jakarta Sans (sans-serif, variable) | 400, 500, 600 |

Both imported from Google Fonts. Cormorant is used for recipe titles, page titles, and the
sidebar logo. Plus Jakarta Sans is used for all labels, descriptions, buttons, and UI text.

### Color Palette

| Token | Light | Dark |
|---|---|---|
| Background | `#FAFAF9` | `#111110` |
| Surface (cards) | `#FFFFFF` | `#1C1B19` |
| Surface secondary | `#F5F4F2` | `#242321` |
| Border | `#E8E6E3` | `#333230` |
| Text | `#1C1B19` | `#F2F0EC` |
| Text muted | `#6B6763` | `#9A9491` |
| Primary accent | `#0D7C6B` | `#2DC4A7` |
| Primary surface | `#E6F4F1` | `#0D2E2A` |

Primary is **deep teal** (not PrimeVue's default blue) — fresh, food-adjacent, and
distinctive. The warm-gray neutrals (not pure black/white) reduce eye strain.

### Border Radius

All components use `10px` base radius, slightly larger than Aura's default. Cards
and dialogs get `14px`. This gives a refined but not toy-like appearance.

---

## Layout Shell

### Desktop (≥ 768px)

- Sidebar: `240px` fixed left, contains logo, nav links, and a theme toggle button in the footer
- Main area: `flex: 1`, scrollable, `max-width: 1100px` centered with horizontal padding
- No changes to routing or AppLayout logic

### Mobile (< 768px)

- Sidebar: hidden (`display: none`)
- Bottom tab bar: `60px` fixed at bottom of viewport, 3 tabs: Recipes / Shared / Profile
- Content area: full width, `padding-bottom: 80px` to avoid overlap with the bar
- Active tab: teal accent color; inactive tabs: muted text

The mobile bottom bar replaces the sidebar navigation only — routing and state are unchanged.

---

## Theme System

### Files

- `frontend/src/theme.ts` — defines `lightPreset` and `darkPreset` via `definePreset(Aura, { ... })`
- `frontend/src/composables/useTheme.ts` — composable: `isDark`, `toggleTheme()`, `initTheme()`

### Switching Mechanism

PrimeVue 4 responds to the `.dark` class on `<html>`. The composable:
1. Reads saved preference from `localStorage` (key: `cookbook-theme`)
2. On `toggleTheme()`: flips the class, calls `usePrimeVue().changeTheme()`, writes to localStorage
3. `initTheme()` is called once in `App.vue` on mount

The toggle button (sun/moon icon) lives in the sidebar footer on desktop and as a small
button in the bottom bar or Profile tab on mobile.

---

## Files Changed in This Phase

| File | Change |
|---|---|
| `frontend/src/theme.ts` | **New** — custom light + dark PrimeVue preset |
| `frontend/src/composables/useTheme.ts` | **New** — theme toggle composable |
| `frontend/src/style.css` | Google Fonts import, base typography scale, body/heading font-family |
| `frontend/src/main.ts` | Register custom preset, call `initTheme()` |
| `frontend/src/views/AppLayout.vue` | Mobile bottom nav, dark mode toggle, responsive sidebar |
| `frontend/src/components/RecipeCard.vue` | Typography updates (Cormorant for title, Jakarta Sans for metadata) |

---

## What Is NOT Changing in This Phase

- No changes to any view logic or API calls
- No changes to routing
- No changes to stores, types, or backend
- RecipeDetailView, RecipeEditorView, ProfileView, LoginView, RegisterView — passive
  visual upgrade only from the preset; no manual edits
- No new dependencies (Google Fonts via `<link>` in `index.html`, no npm packages)

---

## File Change Summary

| File | Type |
|---|---|
| `frontend/src/theme.ts` | Create |
| `frontend/src/composables/useTheme.ts` | Create |
| `frontend/src/style.css` | Modify |
| `frontend/src/main.ts` | Modify |
| `frontend/index.html` | Modify (add Google Fonts `<link>`) |
| `frontend/src/views/AppLayout.vue` | Modify |
| `frontend/src/components/RecipeCard.vue` | Modify |
| `README.md` | Create |
