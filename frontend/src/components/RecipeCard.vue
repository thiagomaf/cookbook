<template>
  <div
    style="
      background: var(--p-surface-0);
      border: 1px solid var(--p-surface-200);
      border-radius: 12px;
      padding: 1rem;
      cursor: pointer;
      transition: box-shadow 0.15s, border-color 0.15s;
    "
    @mouseenter="hovered = true"
    @mouseleave="hovered = false"
    :style="hovered ? { boxShadow: '0 4px 16px rgba(0,0,0,0.08)', borderColor: 'var(--p-primary-200)' } : {}"
    @click="$emit('click')"
  >
    <div style="display: flex; align-items: flex-start; justify-content: space-between; margin-bottom: 0.5rem">
      <h3 style="margin: 0; font-size: 1.15rem; font-weight: 600; line-height: 1.3; flex: 1; font-family: var(--font-display); letter-spacing: -0.01em">{{ recipe.title }}</h3>
      <Tag
        v-if="recipe.has_draft"
        icon="pi pi-pencil"
        severity="warn"
        style="margin-left: 0.5rem; flex-shrink: 0; font-size: 0.7rem"
        v-tooltip.top="'Has unsaved changes'"
      />
    </div>

    <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.75rem">
      <Rating
        v-if="recipe.latest_version"
        :modelValue="recipe.latest_version.rating ?? undefined"
        readonly
        :stars="5"
      />
      <span v-if="recipe.latest_version" style="font-size: 0.8rem; color: var(--p-text-muted-color)">
        v{{ recipe.latest_version.version_number }}
      </span>
      <span v-else style="font-size: 0.8rem; color: var(--p-text-muted-color); font-style: italic">No versions yet</span>
    </div>

    <div style="display: flex; align-items: center; justify-content: space-between; font-size: 0.8rem; color: var(--p-text-muted-color)">
      <span v-if="showOwner">by @{{ recipe.owner_username }}</span>
      <span v-else>{{ formatDate(recipe.updated_at) }}</span>
      <div style="display: flex; gap: 0.3rem">
        <Tag v-if="recipe.is_shared" icon="pi pi-users" severity="info" style="font-size: 0.7rem" v-tooltip.top="'Shared'" />
        <Tag v-if="recipe.forked_from_attribution" icon="pi pi-code-branch" severity="secondary" style="font-size: 0.7rem" v-tooltip.top="`Forked from ${recipe.forked_from_attribution}`" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import type { RecipeDetailOut } from '@/types'
import Tag from 'primevue/tag'
import Rating from 'primevue/rating'

defineProps<{ recipe: RecipeDetailOut; showOwner?: boolean }>()
defineEmits<{ click: [] }>()
const hovered = ref(false)

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })
}
</script>
