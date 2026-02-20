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
    @click="emit('click')"
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
      <Button
        v-if="showShareToggle"
        :icon="recipe.is_shared ? 'pi pi-lock' : 'pi pi-globe'"
        text
        rounded
        size="small"
        :severity="recipe.is_shared ? 'secondary' : 'info'"
        style="margin-left: 0.25rem; flex-shrink: 0; width: 1.75rem; height: 1.75rem"
        v-tooltip.top="recipe.is_shared ? 'Make private' : 'Share'"
        @click.stop="emit('toggle-share', recipe)"
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
      <div style="display: flex; gap: 0.3rem; align-items: center">
        <Tag v-if="recipe.is_shared" icon="pi pi-users" severity="info" style="font-size: 0.7rem" v-tooltip.top="'Shared'" />
        <Tag v-if="recipe.forked_from_attribution" icon="pi pi-code-branch" severity="secondary" style="font-size: 0.7rem" v-tooltip.top="`Forked from ${recipe.forked_from_attribution}`" />
        <Button
          v-if="showForkButton && recipe.owner_id !== auth.user?.id"
          label="Fork"
          icon="pi pi-code-branch"
          text
          size="small"
          severity="secondary"
          style="font-size: 0.75rem; padding: 0.2rem 0.4rem"
          :loading="forkLoading"
          :disabled="forkLoading"
          @click.stop="emit('fork', recipe)"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useAuthStore } from '@/stores/auth'
import type { RecipeDetailOut } from '@/types'
import Tag from 'primevue/tag'
import Rating from 'primevue/rating'
import Button from 'primevue/button'

defineProps<{
  recipe: RecipeDetailOut
  showOwner?: boolean
  showShareToggle?: boolean
  showForkButton?: boolean
  forkLoading?: boolean
}>()

const emit = defineEmits<{
  click: []
  'toggle-share': [recipe: RecipeDetailOut]
  fork: [recipe: RecipeDetailOut]
}>()

const hovered = ref(false)
const auth = useAuthStore()

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })
}
</script>
