<template>
  <div style="padding: 1.5rem; max-width: 640px">
    <h1 style="margin: 0 0 1.5rem; font-size: 1.5rem; font-weight: 700">Profile & Settings</h1>

    <!-- Account -->
    <Card style="margin-bottom: 1.25rem">
      <template #title><span style="font-size: 1rem"><i class="pi pi-user" style="margin-right: 0.5rem"></i>Account</span></template>
      <template #content>
        <div style="display: flex; flex-direction: column; gap: 1rem">
          <div>
            <label class="font-medium text-sm block mb-1">Username</label>
            <div style="font-family: monospace; background: var(--p-surface-50); padding: 0.5rem 0.75rem; border-radius: 6px; font-size: 0.9rem">
              {{ auth.user?.username }}
            </div>
          </div>
          <div>
            <label class="font-medium text-sm block mb-1">Email</label>
            <div style="display: flex; gap: 0.5rem">
              <InputText v-model="email" fluid />
              <Button label="Update" outlined @click="saveEmail" :loading="savingEmail" />
            </div>
          </div>
        </div>
      </template>
    </Card>

    <!-- GitHub Integration -->
    <Card style="margin-bottom: 1.25rem">
      <template #title><span style="font-size: 1rem"><i class="pi pi-github" style="margin-right: 0.5rem"></i>GitHub Integration</span></template>
      <template #content>
        <p style="font-size: 0.875rem; color: var(--p-text-muted-color); margin: 0 0 1rem">
          Connect your GitHub repo to automatically commit recipe versions.
          The repo must already exist on GitHub.
        </p>
        <div style="display: flex; flex-direction: column; gap: 1rem">
          <div>
            <label class="font-medium text-sm block mb-1">Repository URL</label>
            <InputText v-model="githubRepoUrl" placeholder="https://github.com/username/my-cookbook" fluid />
          </div>
          <div>
            <label class="font-medium text-sm block mb-1">Personal Access Token</label>
            <Password v-model="githubToken" :feedback="false" toggleMask fluid placeholder="ghp_xxxxx (leave blank to keep existing)" />
            <div style="display: flex; align-items: center; gap: 0.4rem; margin-top: 0.4rem">
              <i v-if="auth.user?.has_github_token" class="pi pi-check-circle" style="color: #22c55e; font-size: 0.85rem"></i>
              <i v-else class="pi pi-times-circle" style="color: var(--p-text-muted-color); font-size: 0.85rem"></i>
              <span style="font-size: 0.8rem; color: var(--p-text-muted-color)">
                {{ auth.user?.has_github_token ? 'Token stored (encrypted at rest)' : 'No token configured' }}
              </span>
            </div>
          </div>
          <Button label="Save GitHub Settings" icon="pi pi-save" outlined @click="saveGitHub" :loading="savingGitHub" />
        </div>
      </template>
    </Card>

    <!-- Preferences -->
    <Card>
      <template #title><span style="font-size: 1rem"><i class="pi pi-sliders-h" style="margin-right: 0.5rem"></i>Preferences</span></template>
      <template #content>
        <div style="display: flex; flex-direction: column; gap: 0.75rem">
          <label class="font-medium text-sm">
            Ingredient Tweak Step: <strong>{{ tweakPct }}%</strong>
          </label>
          <Slider v-model="tweakPct" :min="1" :max="50" style="max-width: 300px" />
          <p style="font-size: 0.8rem; color: var(--p-text-muted-color); margin: 0">
            How much the ±&nbsp;buttons adjust ingredient quantities (default: 10%)
          </p>
          <Button label="Save Preferences" outlined style="width: fit-content" @click="savePrefs" :loading="savingPrefs" />
        </div>
      </template>
    </Card>

    <Message v-if="successMsg" severity="success" style="margin-top: 1rem" :closable="false">{{ successMsg }}</Message>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { authApi } from '@/api/auth'
import Card from 'primevue/card'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import Password from 'primevue/password'
import Slider from 'primevue/slider'
import Message from 'primevue/message'

const auth = useAuthStore()

const email = ref(auth.user?.email ?? '')
const githubRepoUrl = ref(auth.user?.github_repo_url ?? '')
const githubToken = ref('')
const tweakPct = ref(auth.user?.tweak_percentage ?? 10)
const successMsg = ref('')
const savingEmail = ref(false)
const savingGitHub = ref(false)
const savingPrefs = ref(false)

function flash(msg: string) { successMsg.value = msg; setTimeout(() => successMsg.value = '', 3000) }

async function saveEmail() {
  savingEmail.value = true
  try { auth.user = await authApi.updateMe({ email: email.value }); flash('Email updated') }
  finally { savingEmail.value = false }
}

async function saveGitHub() {
  savingGitHub.value = true
  try {
    auth.user = await authApi.updateMe({
      github_repo_url: githubRepoUrl.value || undefined,
      github_token: githubToken.value || undefined
    })
    githubToken.value = ''
    flash('GitHub settings saved')
  } finally { savingGitHub.value = false }
}

async function savePrefs() {
  savingPrefs.value = true
  try { auth.user = await authApi.updateMe({ tweak_percentage: tweakPct.value }); flash('Preferences saved') }
  finally { savingPrefs.value = false }
}
</script>
