<template>
  <div class="min-h-screen flex items-center justify-center" style="background: var(--p-surface-50)">
    <div style="width: 100%; max-width: 420px; padding: 1rem">
      <Card>
        <template #header>
          <div style="text-align: center; padding: 2rem 0 1rem">
            <i class="pi pi-book" style="font-size: 3rem; color: var(--p-primary-color)"></i>
            <h1 style="margin: 0.75rem 0 0.25rem; font-size: 1.5rem">Cookbook</h1>
            <p style="margin: 0; color: var(--p-text-muted-color); font-size: 0.9rem">Sign in to your account</p>
          </div>
        </template>
        <template #content>
          <form @submit.prevent="handleLogin" style="display: flex; flex-direction: column; gap: 1rem">
            <div class="flex flex-col gap-1">
              <label class="font-medium text-sm">Username</label>
              <InputText v-model="form.username" placeholder="username" autocomplete="username" fluid required />
            </div>
            <div class="flex flex-col gap-1">
              <label class="font-medium text-sm">Password</label>
              <Password v-model="form.password" :feedback="false" toggleMask fluid autocomplete="current-password" required />
            </div>
            <Message v-if="error" severity="error" :closable="false" size="small">{{ error }}</Message>
            <Button type="submit" label="Sign In" fluid :loading="loading" />
            <p style="text-align: center; font-size: 0.85rem; color: var(--p-text-muted-color); margin: 0">
              No account?
              <RouterLink to="/register" style="color: var(--p-primary-color); font-weight: 500">Register</RouterLink>
            </p>
          </form>
        </template>
      </Card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import Card from 'primevue/card'
import InputText from 'primevue/inputtext'
import Password from 'primevue/password'
import Button from 'primevue/button'
import Message from 'primevue/message'

const router = useRouter()
const auth = useAuthStore()
const form = ref({ username: '', password: '' })
const loading = ref(false)
const error = ref('')

async function handleLogin() {
  error.value = ''
  loading.value = true
  try {
    await auth.login(form.value.username, form.value.password)
    router.push('/recipes')
  } catch (e: unknown) {
    const err = e as { response?: { data?: { detail?: string } } }
    error.value = err.response?.data?.detail || 'Login failed. Check your credentials.'
  } finally {
    loading.value = false
  }
}
</script>
