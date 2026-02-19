<template>
  <div style="display: flex; flex-direction: column; height: 100%; background: var(--p-surface-0)">
    <div style="padding: 1rem; border-bottom: 1px solid var(--p-surface-200)">
      <h3 style="margin: 0; font-size: 0.9rem; font-weight: 600; color: var(--p-text-muted-color); text-transform: uppercase; letter-spacing: 0.05em">
        Version History
      </h3>
    </div>

    <div v-if="!sortedVersions.length" style="padding: 1.5rem; text-align: center; color: var(--p-text-muted-color); font-size: 0.875rem">
      No saved versions yet.<br>Click "Save Version" to create one.
    </div>

    <div style="flex: 1; overflow-y: auto; padding: 0.5rem">
      <div
        v-for="v in sortedVersions"
        :key="v.id"
        style="
          border: 1px solid var(--p-surface-200);
          border-radius: 8px;
          padding: 0.75rem;
          margin-bottom: 0.4rem;
          cursor: pointer;
          transition: background 0.1s;
        "
        :style="selectedVersions.includes(v.version_number)
          ? { background: 'var(--p-primary-50)', borderColor: 'var(--p-primary-200)' }
          : {}"
        @click="selectVersion(v.version_number)"
      >
        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 0.3rem">
          <span style="font-weight: 600; font-size: 0.875rem">v{{ v.version_number }}</span>
          <!-- Push status icon -->
          <div style="display: flex; align-items: center; gap: 0.4rem">
            <i v-if="ratingVersion === v.version_number" class="pi pi-spin pi-spinner" style="font-size: 0.75rem" />
            <i
              v-if="v.push_status === 'pushed'" class="pi pi-github"
              style="font-size: 0.75rem; color: #22c55e"
              v-tooltip.left="'Pushed to GitHub'"
            />
            <i
              v-else-if="v.push_status === 'failed'" class="pi pi-exclamation-triangle"
              style="font-size: 0.75rem; color: #f59e0b"
              v-tooltip.left="'GitHub push failed'"
            />
            <i
              v-else class="pi pi-clock"
              style="font-size: 0.75rem; color: var(--p-text-muted-color)"
              v-tooltip.left="'Push pending'"
            />
          </div>
        </div>

        <!-- Interactive rating -->
        <div
          style="margin-bottom: 0.25rem"
          @click.stop
          v-tooltip.top="currentRating(v.version_number) ? `${currentRating(v.version_number)}/5 — click to change` : 'Rate after cooking'"
        >
          <Rating
            :modelValue="currentRating(v.version_number) ?? undefined"
            :stars="5"
            @update:modelValue="(r) => rate(v.version_number, r)"
          />
        </div>
        <div v-if="!currentRating(v.version_number)" style="font-size: 0.75rem; color: var(--p-text-muted-color); font-style: italic; margin-bottom: 0.25rem">
          Not rated yet
        </div>

        <div style="font-size: 0.775rem; color: var(--p-text-muted-color)">{{ formatDate(v.created_at) }}</div>
        <div style="font-size: 0.75rem; margin-top: 0.3rem; color: var(--p-text-muted-color); font-family: monospace" v-if="v.commit_hash">
          {{ v.commit_hash.slice(0, 7) }}
        </div>

        <!-- Restore button -->
        <Button
          v-if="emit"
          label="Restore"
          text
          size="small"
          icon="pi pi-history"
          style="margin-top: 0.25rem; padding: 0"
          @click.stop="loadAndRestore(v.version_number)"
          :loading="restoringVersion === v.version_number"
        />
      </div>
    </div>

    <!-- Diff controls (when 2 versions selected) -->
    <div v-if="sortedVersions.length >= 2" style="padding: 0.75rem; border-top: 1px solid var(--p-surface-200)">
      <p style="font-size: 0.78rem; color: var(--p-text-muted-color); margin: 0 0 0.5rem">
        Click 2 versions to compare:
        <strong v-if="selectedVersions.length">v{{ selectedVersions.join(' vs v') }}</strong>
      </p>
      <Button
        label="Compare"
        icon="pi pi-arrows-h"
        size="small"
        fluid
        :disabled="selectedVersions.length !== 2"
        @click="showDiff = true"
      />
    </div>
  </div>

  <!-- Diff dialog -->
  <Dialog v-model:visible="showDiff" header="Version Diff" modal style="width: min(680px, 95vw); max-height: 85vh">
    <DiffViewer
      v-if="selectedVersions.length === 2"
      :recipeId="recipe.id"
      :v1="Math.min(...selectedVersions)"
      :v2="Math.max(...selectedVersions)"
    />
  </Dialog>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import type { RecipeDetailOut, RecipeContent } from '@/types'
import { recipesApi } from '@/api/recipes'
import DiffViewer from './DiffViewer.vue'
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import Rating from 'primevue/rating'

const props = defineProps<{ recipe: RecipeDetailOut }>()
const emit = defineEmits<{ restore: [RecipeContent] }>()

const sortedVersions = computed(() =>
  [...props.recipe.versions].sort((a, b) => b.version_number - a.version_number)
)

const selectedVersions = ref<number[]>([])
const showDiff = ref(false)
const restoringVersion = ref<number | null>(null)
const ratingVersion = ref<number | null>(null)

// Local rating overrides — updated optimistically after API call
const localRatings = ref<Record<number, number | null>>({})

function currentRating(versionNumber: number): number | null {
  return versionNumber in localRatings.value
    ? localRatings.value[versionNumber]
    : (props.recipe.versions.find(v => v.version_number === versionNumber)?.rating ?? null)
}

async function rate(versionNumber: number, rating: number) {
  ratingVersion.value = versionNumber
  try {
    const updated = await recipesApi.rateVersion(props.recipe.id, versionNumber, rating)
    localRatings.value[versionNumber] = updated.rating
  } finally {
    ratingVersion.value = null
  }
}

function selectVersion(n: number) {
  const idx = selectedVersions.value.indexOf(n)
  if (idx !== -1) {
    selectedVersions.value.splice(idx, 1)
  } else if (selectedVersions.value.length < 2) {
    selectedVersions.value.push(n)
  } else {
    selectedVersions.value = [selectedVersions.value[1]!, n]
  }
}

async function loadAndRestore(versionNumber: number) {
  restoringVersion.value = versionNumber
  try {
    const vd = await recipesApi.getVersion(props.recipe.id, versionNumber)
    emit('restore', vd.content)
  } finally {
    restoringVersion.value = null
  }
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })
}
</script>
