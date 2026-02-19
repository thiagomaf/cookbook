<template>
  <div style="display: flex; height: 100vh; overflow: hidden; background: var(--p-surface-50)">
    <!-- Sidebar -->
    <aside style="
      width: 220px;
      flex-shrink: 0;
      display: flex;
      flex-direction: column;
      background: var(--p-surface-0);
      border-right: 1px solid var(--p-surface-200);
    ">
      <!-- Logo -->
      <div style="padding: 1.25rem 1rem; border-bottom: 1px solid var(--p-surface-200); display: flex; align-items: center; gap: 0.6rem">
        <i class="pi pi-book" style="font-size: 1.4rem; color: var(--p-primary-color)"></i>
        <span style="font-size: 1.1rem; font-weight: 700">Cookbook</span>
      </div>

      <!-- Nav -->
      <nav style="flex: 1; padding: 0.75rem 0.5rem; display: flex; flex-direction: column; gap: 0.25rem">
        <RouterLink
          v-for="item in navItems"
          :key="item.to"
          :to="item.to"
          style="
            display: flex; align-items: center; gap: 0.75rem;
            padding: 0.6rem 0.75rem; border-radius: 8px;
            text-decoration: none; color: var(--p-text-color);
            font-size: 0.9rem; transition: background 0.15s;
          "
          :style="isActive(item.to) ? { background: 'var(--p-primary-50)', color: 'var(--p-primary-color)', fontWeight: '600' } : {}"
        >
          <i :class="item.icon" style="font-size: 1rem; width: 1rem"></i>
          {{ item.label }}
        </RouterLink>
      </nav>

      <!-- User footer -->
      <div style="padding: 0.75rem; border-top: 1px solid var(--p-surface-200); display: flex; align-items: center; gap: 0.5rem">
        <i class="pi pi-user" style="color: var(--p-text-muted-color)"></i>
        <span style="flex: 1; font-size: 0.85rem; overflow: hidden; text-overflow: ellipsis; white-space: nowrap">
          {{ auth.user?.username }}
        </span>
        <Button icon="pi pi-sign-out" text rounded size="small" @click="handleLogout" v-tooltip.top="'Logout'" />
      </div>
    </aside>

    <!-- Main -->
    <main style="flex: 1; overflow-y: auto">
      <RouterView />
    </main>
  </div>
</template>

<script setup lang="ts">
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import Button from 'primevue/button'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const navItems = [
  { to: '/recipes', icon: 'pi pi-list', label: 'My Recipes' },
  { to: '/shared', icon: 'pi pi-users', label: 'Shared' },
  { to: '/profile', icon: 'pi pi-cog', label: 'Settings' }
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
