import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi } from '@/api/auth'
import type { UserPublic } from '@/types'

export const useAuthStore = defineStore('auth', () => {
  const accessToken = ref<string | null>(localStorage.getItem('access_token'))
  const user = ref<UserPublic | null>(null)

  const isAuthenticated = computed(() => !!accessToken.value)

  function setTokens(access: string, refresh: string) {
    accessToken.value = access
    localStorage.setItem('access_token', access)
    localStorage.setItem('refresh_token', refresh)
  }

  function clearTokens() {
    accessToken.value = null
    user.value = null
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
  }

  async function fetchUser() {
    try {
      user.value = await authApi.getMe()
    } catch {
      clearTokens()
    }
  }

  async function login(username: string, password: string) {
    const tokens = await authApi.login(username, password)
    setTokens(tokens.access_token, tokens.refresh_token)
    await fetchUser()
  }

  async function register(username: string, email: string, password: string) {
    const tokens = await authApi.register(username, email, password)
    setTokens(tokens.access_token, tokens.refresh_token)
    await fetchUser()
  }

  function logout() {
    clearTokens()
  }

  return { user, isAuthenticated, setTokens, clearTokens, fetchUser, login, register, logout }
})
