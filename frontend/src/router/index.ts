import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      component: () => import('@/views/LoginView.vue'),
      meta: { public: true }
    },
    {
      path: '/register',
      component: () => import('@/views/RegisterView.vue'),
      meta: { public: true }
    },
    {
      path: '/',
      component: () => import('@/views/AppLayout.vue'),
      children: [
        { path: '', redirect: '/recipes' },
        { path: 'recipes', component: () => import('@/views/RecipeListView.vue') },
        { path: 'recipes/:id', component: () => import('@/views/RecipeDetailView.vue') },
        { path: 'recipes/:id/edit', component: () => import('@/views/RecipeEditorView.vue') },
        { path: 'shared', component: () => import('@/views/SharedRecipesView.vue') },
        { path: 'profile', component: () => import('@/views/ProfileView.vue') }
      ]
    },
    { path: '/:pathMatch(.*)*', redirect: '/recipes' }
  ]
})

router.beforeEach(async (to) => {
  const auth = useAuthStore()
  if (!to.meta.public && !auth.isAuthenticated) return '/login'
  if (to.meta.public && auth.isAuthenticated) return '/recipes'
  // After a page refresh the token is restored from localStorage but user
  // data is not — re-fetch it so profile fields and guards have current data.
  if (auth.isAuthenticated && !auth.user) await auth.fetchUser()
})

export default router
