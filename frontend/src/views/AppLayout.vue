<template>
  <div class="app-layout">
    <!-- Required by the sharing flow (another feature) — do not remove -->
    <ConfirmDialog />

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
import ConfirmDialog from 'primevue/confirmdialog'

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
