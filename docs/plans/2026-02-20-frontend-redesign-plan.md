# Frontend Redesign — Foundation Phase Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Establish a custom visual foundation for the cookbook app: teal accent, warm-gray
surfaces, Cormorant + Plus Jakarta Sans typography, light/dark mode toggle, and a responsive
layout shell (sidebar on desktop, bottom tab bar on mobile).

**Architecture:** Extend PrimeVue 4's Aura preset via `definePreset()` so all components
inherit the new tokens automatically. A module-level `useTheme()` composable manages
dark-mode state and persistence. `AppLayout.vue` is redesigned with CSS media queries to
hide the sidebar and show a bottom nav on small screens.

**Tech Stack:** Vue 3, PrimeVue 4 (`@primeuix/themes` v2), TypeScript, CSS scoped styles,
Google Fonts (no new npm packages).

**Branch:** `frontend-redesign`

**Design doc:** `docs/plans/2026-02-20-frontend-redesign-design.md`

---

## Before you start

Run the dev server and keep it open in a browser for visual verification:

```bash
cd frontend
npm run dev
```

Open `http://localhost:5173` — you should see the app in its current state.

---

## Task 1: Google Fonts + Base Typography

**Files:**
- Modify: `frontend/index.html`
- Modify: `frontend/src/style.css`

### Step 1: Add Google Fonts preload to `index.html`

Replace the entire `<head>` block with:

```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Cookbook</title>
    <link rel="preconnect" href="https://fonts.googleapis.com" />
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
    <link
      href="https://fonts.googleapis.com/css2?family=Cormorant:ital,wght@0,400;0,600;0,700;1,400&family=Plus+Jakarta+Sans:wght@400;500;600&display=swap"
      rel="stylesheet"
    />
  </head>
  <body>
    <div id="app"></div>
    <script type="module" src="/src/main.ts"></script>
  </body>
</html>
```

### Step 2: Replace `style.css` with app-appropriate base styles

The current file has Vite scaffold boilerplate (dark background, centred `#app`, etc.) that
conflicts with the app layout. Replace the entire file:

```css
/* Base reset and typography */
*,
*::before,
*::after {
  box-sizing: border-box;
}

:root {
  --font-body: 'Plus Jakarta Sans', system-ui, sans-serif;
  --font-display: 'Cormorant', Georgia, serif;

  font-family: var(--font-body);
  font-size: 16px;
  line-height: 1.5;
  font-synthesis: none;
  text-rendering: optimizeLegibility;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

body {
  margin: 0;
  min-height: 100vh;
  background: var(--p-surface-50);
  color: var(--p-text-color);
}

#app {
  height: 100vh;
  display: flex;
  flex-direction: column;
}

h1, h2, h3, h4 {
  font-family: var(--font-display);
  font-weight: 600;
  line-height: 1.2;
  margin: 0;
}

a {
  color: var(--p-primary-color);
  text-decoration: none;
}

a:hover {
  text-decoration: underline;
}
```

### Step 3: Verify visually

In the browser at `http://localhost:5173`:
- The app should still render correctly (layout unchanged for now)
- Open DevTools → Network → filter by "fonts" — the Google Fonts CSS should load
- Body text should use Plus Jakarta Sans (check in DevTools → Elements → Computed)

### Step 4: Commit

```bash
git add frontend/index.html frontend/src/style.css
git commit -m "feat: add Google Fonts and replace style.css boilerplate"
```

---

## Task 2: Custom PrimeVue Preset

**Files:**
- Create: `frontend/src/theme.ts`

### Step 1: Create `frontend/src/theme.ts`

```typescript
import { definePreset } from '@primeuix/themes'
import Aura from '@primeuix/themes/aura'

/**
 * CookbookPreset — extends Aura with:
 * - Primary: teal (replaces default emerald)
 * - Surface: stone warm-gray (replaces slate in light, zinc in dark)
 * - Border radius: slightly larger (md = 10px, lg = 14px)
 */
export const CookbookPreset = definePreset(Aura, {
  primitive: {
    borderRadius: {
      none: '0',
      xs:   '4px',
      sm:   '6px',
      md:   '10px',
      lg:   '14px',
      xl:   '20px',
    },
  },
  semantic: {
    primary: {
      50:  '{teal.50}',
      100: '{teal.100}',
      200: '{teal.200}',
      300: '{teal.300}',
      400: '{teal.400}',
      500: '{teal.500}',
      600: '{teal.600}',
      700: '{teal.700}',
      800: '{teal.800}',
      900: '{teal.900}',
      950: '{teal.950}',
    },
    colorScheme: {
      light: {
        surface: {
          0:   '#ffffff',
          50:  '{stone.50}',
          100: '{stone.100}',
          200: '{stone.200}',
          300: '{stone.300}',
          400: '{stone.400}',
          500: '{stone.500}',
          600: '{stone.600}',
          700: '{stone.700}',
          800: '{stone.800}',
          900: '{stone.900}',
          950: '{stone.950}',
        },
      },
      dark: {
        surface: {
          0:   '#ffffff',
          50:  '{stone.50}',
          100: '{stone.100}',
          200: '{stone.200}',
          300: '{stone.300}',
          400: '{stone.400}',
          500: '{stone.500}',
          600: '{stone.600}',
          700: '{stone.700}',
          800: '{stone.800}',
          900: '{stone.900}',
          950: '{stone.950}',
        },
      },
    },
  },
})
```

**What this does:**
- `primary → teal`: buttons, links, active states, focus rings become teal instead of blue
- `surface → stone`: all background/card/border colors use warm-gray tones instead of cool slate/zinc
- `borderRadius.md = 10px, lg = 14px`: inputs, cards, dialogs get slightly rounder corners

### Step 2: Register the preset in `main.ts`

Replace line 4 (`import Aura from '@primeuix/themes/aura'`) and lines 15-20 with:

```typescript
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import PrimeVue from 'primevue/config'
import ToastService from 'primevue/toastservice'
import ConfirmationService from 'primevue/confirmationservice'
import Tooltip from 'primevue/tooltip'
import App from './App.vue'
import router from './router'
import { CookbookPreset } from './theme'
import 'primeicons/primeicons.css'

const app = createApp(App)
app.use(createPinia())
app.use(router)
app.use(PrimeVue, {
  theme: {
    preset: CookbookPreset,
    options: { darkModeSelector: '.dark' }
  }
})
app.use(ToastService)
app.use(ConfirmationService)
app.directive('tooltip', Tooltip)
app.mount('#app')
```

### Step 3: Verify visually

In the browser:
- Buttons should now be **teal** (not blue)
- Card borders and backgrounds should have a slightly warmer tone
- Form inputs should have slightly rounder corners
- Everything should still work — no broken layouts

### Step 4: Commit

```bash
git add frontend/src/theme.ts frontend/src/main.ts
git commit -m "feat: add custom CookbookPreset (teal primary, stone surfaces, rounder radius)"
```

---

## Task 3: Dark Mode Composable

**Files:**
- Create: `frontend/src/composables/useTheme.ts`
- Modify: `frontend/src/main.ts` (add `initTheme` call)

### Step 1: Create `frontend/src/composables/useTheme.ts`

```typescript
import { ref, readonly } from 'vue'

/**
 * Module-level ref — shared across all useTheme() calls.
 * Tracks whether dark mode is currently active.
 */
const _isDark = ref(false)

const STORAGE_KEY = 'cookbook-theme'

export function useTheme() {
  function applyTheme(dark: boolean) {
    document.documentElement.classList.toggle('dark', dark)
    _isDark.value = dark
    localStorage.setItem(STORAGE_KEY, dark ? 'dark' : 'light')
  }

  function toggleTheme() {
    applyTheme(!_isDark.value)
  }

  /**
   * Call once at app startup (main.ts, before mount).
   * Reads saved preference; falls back to OS preference.
   */
  function initTheme() {
    const saved = localStorage.getItem(STORAGE_KEY)
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
    applyTheme(saved === 'dark' || (!saved && prefersDark))
  }

  return {
    isDark: readonly(_isDark),
    toggleTheme,
    initTheme,
  }
}
```

### Step 2: Call `initTheme()` in `main.ts` before mount

Add the import and call before `app.mount('#app')`:

```typescript
import { useTheme } from './composables/useTheme'

// ... existing imports and app setup ...

// Apply saved theme before mounting to avoid flash of wrong theme
const { initTheme } = useTheme()
initTheme()

app.mount('#app')
```

The full `main.ts` should now look like:

```typescript
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import PrimeVue from 'primevue/config'
import ToastService from 'primevue/toastservice'
import ConfirmationService from 'primevue/confirmationservice'
import Tooltip from 'primevue/tooltip'
import App from './App.vue'
import router from './router'
import { CookbookPreset } from './theme'
import { useTheme } from './composables/useTheme'
import 'primeicons/primeicons.css'

const app = createApp(App)
app.use(createPinia())
app.use(router)
app.use(PrimeVue, {
  theme: {
    preset: CookbookPreset,
    options: { darkModeSelector: '.dark' }
  }
})
app.use(ToastService)
app.use(ConfirmationService)
app.directive('tooltip', Tooltip)

const { initTheme } = useTheme()
initTheme()

app.mount('#app')
```

### Step 3: Verify

Open DevTools Console. Run:
```javascript
document.documentElement.classList.toggle('dark')
```
The entire app should switch to a dark warm-gray theme with lighter teal accents. Toggle it back. Then:
```javascript
localStorage.setItem('cookbook-theme', 'dark')
location.reload()
```
The app should reload directly in dark mode.

### Step 4: Commit

```bash
git add frontend/src/composables/useTheme.ts frontend/src/main.ts
git commit -m "feat: add useTheme composable with localStorage persistence"
```

---

## Task 4: AppLayout — Responsive Shell + Theme Toggle

**Files:**
- Modify: `frontend/src/views/AppLayout.vue`

This is the largest change. The sidebar gets a Cormorant logo and a theme toggle, and a
bottom tab bar appears on screens narrower than 768px.

### Step 1: Replace `AppLayout.vue` entirely

```vue
<template>
  <div class="app-layout">
    <!-- Sidebar (desktop only) -->
    <aside class="app-sidebar">
      <!-- Logo -->
      <div class="sidebar-logo">
        <i class="pi pi-book sidebar-logo-icon" />
        <span class="sidebar-logo-text">Cookbook</span>
      </div>

      <!-- Nav -->
      <nav class="sidebar-nav">
        <RouterLink
          v-for="item in navItems"
          :key="item.to"
          :to="item.to"
          class="sidebar-nav-item"
          :class="{ active: isActive(item.to) }"
        >
          <i :class="item.icon" class="sidebar-nav-icon" />
          {{ item.label }}
        </RouterLink>
      </nav>

      <!-- Footer -->
      <div class="sidebar-footer">
        <Button
          :icon="isDark ? 'pi pi-sun' : 'pi pi-moon'"
          text
          rounded
          size="small"
          @click="toggleTheme"
          v-tooltip.top="isDark ? 'Light mode' : 'Dark mode'"
        />
        <span class="sidebar-username">{{ auth.user?.username }}</span>
        <Button
          icon="pi pi-sign-out"
          text
          rounded
          size="small"
          @click="handleLogout"
          v-tooltip.top="'Logout'"
        />
      </div>
    </aside>

    <!-- Main content -->
    <main class="app-main">
      <RouterView />
    </main>

    <!-- Mobile bottom nav -->
    <nav class="mobile-nav">
      <RouterLink
        v-for="item in navItems"
        :key="item.to"
        :to="item.to"
        class="mobile-nav-item"
        :class="{ active: isActive(item.to) }"
      >
        <i :class="item.icon" />
        <span>{{ item.label }}</span>
      </RouterLink>
      <button class="mobile-nav-item mobile-theme-btn" @click="toggleTheme">
        <i :class="isDark ? 'pi pi-sun' : 'pi pi-moon'" />
        <span>Theme</span>
      </button>
    </nav>
  </div>
</template>

<script setup lang="ts">
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useTheme } from '@/composables/useTheme'
import Button from 'primevue/button'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const { isDark, toggleTheme } = useTheme()

const navItems = [
  { to: '/recipes', icon: 'pi pi-list',  label: 'My Recipes' },
  { to: '/shared',  icon: 'pi pi-users', label: 'Shared' },
  { to: '/profile', icon: 'pi pi-cog',   label: 'Settings' },
]

function isActive(to: string) {
  if (to === '/recipes') return route.path === '/recipes' || route.path.startsWith('/recipes/')
  return route.path === to
}

function handleLogout() {
  auth.logout()
  router.push('/login')
}
</script>

<style scoped>
/* ── Layout shell ──────────────────────────────────────────────── */

.app-layout {
  display: flex;
  height: 100vh;
  overflow: hidden;
  background: var(--p-surface-50);
}

.app-main {
  flex: 1;
  overflow-y: auto;
}

/* ── Desktop sidebar ───────────────────────────────────────────── */

.app-sidebar {
  width: 240px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  background: var(--p-surface-0);
  border-right: 1px solid var(--p-surface-200);
}

.sidebar-logo {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  padding: 1.25rem 1rem;
  border-bottom: 1px solid var(--p-surface-200);
}

.sidebar-logo-icon {
  font-size: 1.4rem;
  color: var(--p-primary-color);
}

.sidebar-logo-text {
  font-family: var(--font-display);
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--p-text-color);
  letter-spacing: -0.02em;
  line-height: 1;
}

.sidebar-nav {
  flex: 1;
  padding: 0.75rem 0.5rem;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.sidebar-nav-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.6rem 0.75rem;
  border-radius: 8px;
  text-decoration: none;
  color: var(--p-text-color);
  font-size: 0.9rem;
  font-family: var(--font-body);
  transition: background 0.15s, color 0.15s;
}

.sidebar-nav-item:hover {
  background: var(--p-surface-100);
  text-decoration: none;
}

.sidebar-nav-item.active {
  background: var(--p-primary-50);
  color: var(--p-primary-color);
  font-weight: 600;
}

.sidebar-nav-icon {
  font-size: 1rem;
  width: 1rem;
}

.sidebar-footer {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem;
  border-top: 1px solid var(--p-surface-200);
}

.sidebar-username {
  flex: 1;
  font-size: 0.85rem;
  font-family: var(--font-body);
  color: var(--p-text-muted-color);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* ── Mobile bottom nav ─────────────────────────────────────────── */

.mobile-nav {
  display: none;
}

@media (max-width: 768px) {
  .app-sidebar {
    display: none;
  }

  .app-main {
    /* leave room for the fixed bottom bar */
    padding-bottom: 80px;
  }

  .mobile-nav {
    display: flex;
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    height: 60px;
    background: var(--p-surface-0);
    border-top: 1px solid var(--p-surface-200);
    z-index: 100;
    align-items: center;
    justify-content: space-around;
    padding: 0 0.5rem;
  }
}

.mobile-nav-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  padding: 0.4rem 0.75rem;
  border-radius: 8px;
  text-decoration: none;
  color: var(--p-text-muted-color);
  font-size: 0.68rem;
  font-family: var(--font-body);
  font-weight: 500;
  transition: color 0.15s;
  border: none;
  background: none;
  cursor: pointer;
  -webkit-tap-highlight-color: transparent;
}

.mobile-nav-item i {
  font-size: 1.2rem;
}

.mobile-nav-item:hover,
.mobile-nav-item.active {
  color: var(--p-primary-color);
  text-decoration: none;
}

.mobile-theme-btn {
  /* inherits .mobile-nav-item; reset button defaults already done above */
}
</style>
```

### Step 2: Verify on desktop

- Sidebar logo text should be in **Cormorant** serif (larger, more elegant)
- Active nav items: teal highlight instead of blue
- Sun/moon icon appears in sidebar footer (clicking toggles dark mode)

### Step 3: Verify on mobile

Open DevTools → toggle device toolbar → set width to 375px (iPhone SE):
- Sidebar should be hidden
- Bottom bar with 4 items (My Recipes / Shared / Settings / Theme) should appear
- Tapping nav items should navigate correctly
- Theme button toggles dark mode

### Step 4: Commit

```bash
git add frontend/src/views/AppLayout.vue
git commit -m "feat: responsive AppLayout with mobile bottom nav and theme toggle"
```

---

## Task 5: RecipeCard Typography

**Files:**
- Modify: `frontend/src/components/RecipeCard.vue`

### Step 1: Update the recipe title to use Cormorant

In the `<template>`, find the `<h3>` tag (line 17 in current file) and update its inline style:

**Before:**
```html
<h3 style="margin: 0; font-size: 0.95rem; font-weight: 600; line-height: 1.35; flex: 1">{{ recipe.title }}</h3>
```

**After:**
```html
<h3 style="margin: 0; font-size: 1.15rem; font-weight: 600; line-height: 1.3; flex: 1; font-family: var(--font-display); letter-spacing: -0.01em">{{ recipe.title }}</h3>
```

Changes:
- `font-family: var(--font-display)` — Cormorant serif
- `font-size: 1.15rem` — slightly larger (Cormorant has more presence, works better at a larger size)
- `letter-spacing: -0.01em` — slight tightening typical for display serifs

### Step 2: Verify visually

On the Recipe List page, recipe titles should now render in Cormorant — a distinct serif font
that gives each card more personality and visual hierarchy.

### Step 3: Commit

```bash
git add frontend/src/components/RecipeCard.vue
git commit -m "feat: use Cormorant display font for recipe card titles"
```

---

## Final Verification

With all tasks done:

1. **Desktop:** Open app at full width
   - Sidebar visible, Cormorant logo, teal active states, warm-gray surfaces
   - Sun/moon button in sidebar footer switches dark mode
   - Recipe cards show Cormorant titles
   - All pages (detail, editor, profile) passively look improved from token changes

2. **Mobile:** DevTools → 375px width
   - Sidebar hidden, bottom tab bar visible
   - Navigation works from the bottom bar
   - Theme toggle works from the bottom bar
   - Content scrolls without overlapping the bar

3. **Dark mode persistence:**
   - Toggle to dark, reload page → stays dark
   - Toggle to light, reload page → stays light

4. **Build check** (make sure nothing broke):
   ```bash
   cd frontend && npm run build
   ```
   Should complete with no errors.

---

## Rollup commit (optional)

After all tasks pass:

```bash
git log --oneline -5
# Should show 5 clean commits for this feature
```

The branch `frontend-redesign` is ready to review and merge into `main`.
