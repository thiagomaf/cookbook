<template>
  <div v-if="loading" style="display: flex; justify-content: center; padding: 2rem">
    <ProgressSpinner />
  </div>

  <div v-else-if="diff" style="display: flex; flex-direction: column; gap: 1rem; max-height: 60vh; overflow-y: auto; padding: 0.25rem">
    <div v-if="!hasAnyChanges" style="text-align: center; color: var(--p-text-muted-color); padding: 2rem">
      No differences found between v{{ diff.v1 }} and v{{ diff.v2 }}.
    </div>

    <!-- Metadata -->
    <div v-if="Object.keys(diff.metadata_changes).length" style="border: 1px solid var(--p-surface-200); border-radius: 8px; overflow: hidden">
      <div style="background: var(--p-surface-100); padding: 0.5rem 0.75rem; font-size: 0.75rem; font-weight: 700; text-transform: uppercase; color: var(--p-text-muted-color)">
        Metadata
      </div>
      <div v-for="(change, field) in diff.metadata_changes" :key="field as string"
        style="padding: 0.5rem 0.75rem; border-top: 1px solid var(--p-surface-100); font-size: 0.875rem">
        <span style="font-weight: 600; margin-right: 0.5rem">{{ field }}:</span>
        <span style="text-decoration: line-through; color: #ef4444; margin-right: 0.5rem">{{ change.from_ ?? 'none' }}</span>
        <span style="color: #22c55e">{{ change.to ?? 'none' }}</span>
      </div>
    </div>

    <!-- Ingredients -->
    <div v-if="hasIngredientChanges" style="border: 1px solid var(--p-surface-200); border-radius: 8px; overflow: hidden">
      <div style="background: var(--p-surface-100); padding: 0.5rem 0.75rem; font-size: 0.75rem; font-weight: 700; text-transform: uppercase; color: var(--p-text-muted-color)">
        Ingredients
      </div>
      <div v-for="ing in diff.ingredients.added" :key="`add-${ing.name}`"
        style="padding: 0.5rem 0.75rem; border-top: 1px solid var(--p-surface-100); background: #f0fdf4; font-size: 0.875rem; color: #15803d">
        + {{ ing.name }}: {{ ing.quantity }} {{ ing.unit }}
      </div>
      <div v-for="ing in diff.ingredients.removed" :key="`rm-${ing.name}`"
        style="padding: 0.5rem 0.75rem; border-top: 1px solid var(--p-surface-100); background: #fef2f2; font-size: 0.875rem; color: #dc2626">
        − {{ ing.name }}: {{ ing.quantity }} {{ ing.unit }}
      </div>
      <div v-for="ch in diff.ingredients.changed" :key="`ch-${ch.name}`"
        style="padding: 0.5rem 0.75rem; border-top: 1px solid var(--p-surface-100); font-size: 0.875rem">
        <span style="font-weight: 600">{{ ch.name }}: </span>
        <span style="text-decoration: line-through; color: #ef4444; margin-right: 0.5rem">{{ ch.from_.quantity }} {{ ch.from_.unit }}</span>
        <span style="color: #22c55e">{{ ch.to.quantity }} {{ ch.to.unit }}</span>
      </div>
    </div>

    <!-- Steps -->
    <div v-if="diff.steps.added.length || diff.steps.removed.length" style="border: 1px solid var(--p-surface-200); border-radius: 8px; overflow: hidden">
      <div style="background: var(--p-surface-100); padding: 0.5rem 0.75rem; font-size: 0.75rem; font-weight: 700; text-transform: uppercase; color: var(--p-text-muted-color)">
        Steps
      </div>
      <div v-for="(s, i) in diff.steps.removed" :key="`srm-${i}`"
        style="padding: 0.5rem 0.75rem; border-top: 1px solid var(--p-surface-100); background: #fef2f2; font-size: 0.875rem; color: #dc2626">
        − {{ s }}
      </div>
      <div v-for="(s, i) in diff.steps.added" :key="`sadd-${i}`"
        style="padding: 0.5rem 0.75rem; border-top: 1px solid var(--p-surface-100); background: #f0fdf4; font-size: 0.875rem; color: #15803d">
        + {{ s }}
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { recipesApi } from '@/api/recipes'
import type { DiffOut } from '@/types'
import ProgressSpinner from 'primevue/progressspinner'

const props = defineProps<{ recipeId: number; v1: number; v2: number }>()
const diff = ref<DiffOut | null>(null)
const loading = ref(true)

const hasIngredientChanges = computed(() =>
  diff.value
    ? diff.value.ingredients.added.length + diff.value.ingredients.removed.length + diff.value.ingredients.changed.length > 0
    : false
)

const hasAnyChanges = computed(() =>
  diff.value
    ? Object.keys(diff.value.metadata_changes).length > 0
      || hasIngredientChanges.value
      || diff.value.steps.added.length > 0
      || diff.value.steps.removed.length > 0
    : false
)

onMounted(async () => {
  try {
    diff.value = await recipesApi.getDiff(props.recipeId, props.v1, props.v2)
  } finally {
    loading.value = false
  }
})
</script>
