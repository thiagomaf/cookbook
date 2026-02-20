<template>
  <div v-if="loading" style="display: flex; justify-content: center; align-items: center; height: 50vh">
    <ProgressSpinner />
  </div>

  <div v-else-if="recipe" style="display: flex; height: 100%; overflow: hidden">
    <!-- Main content -->
    <div style="flex: 1; overflow-y: auto; padding: 1.5rem">
      <!-- Breadcrumb -->
      <div style="font-size: 0.85rem; color: var(--p-text-muted-color); margin-bottom: 1rem; display: flex; align-items: center; gap: 0.4rem">
        <RouterLink
          :to="isOwner ? '/recipes' : '/shared'"
          style="color: var(--p-primary-color); text-decoration: none"
        >{{ isOwner ? 'My Recipes' : 'Shared Recipes' }}</RouterLink>
        <i class="pi pi-angle-right" style="font-size: 0.75rem"></i>
        <span>{{ recipe.title }}</span>
      </div>

      <!-- Header -->
      <div style="display: flex; align-items: flex-start; justify-content: space-between; gap: 1rem; margin-bottom: 1.25rem; flex-wrap: wrap">
        <div>
          <h1 style="margin: 0 0 0.5rem; font-size: 1.75rem; font-weight: 700">{{ recipe.title }}</h1>
          <div style="display: flex; align-items: center; gap: 0.75rem; flex-wrap: wrap">
            <Tag v-if="recipe.has_draft" value="Unsaved changes" severity="warn" icon="pi pi-pencil" />
            <Tag v-if="recipe.is_shared" value="Shared" severity="info" icon="pi pi-users" />
            <Tag v-if="recipe.forked_from_attribution" :value="`Forked from ${recipe.forked_from_attribution}`" severity="secondary" />
            <div v-if="recipe.latest_version" style="display: flex; align-items: center; gap: 0.4rem">
              <Rating :modelValue="recipe.latest_version.rating ?? undefined" readonly :stars="5" />
              <span style="font-size: 0.85rem; color: var(--p-text-muted-color)">v{{ recipe.latest_version.version_number }}</span>
            </div>
          </div>
        </div>
        <div style="display: flex; gap: 0.5rem; flex-shrink: 0">
          <Button v-if="isOwner" label="Edit" icon="pi pi-pencil" outlined @click="router.push(`/recipes/${recipe.id}/edit`)" />
          <Button
            v-if="!isOwner && recipe.is_shared"
            label="Fork"
            icon="pi pi-code-branch"
            outlined
            @click="forkRecipe"
            :loading="forking"
          />
          <Button
            v-if="isOwner"
            :label="recipe.is_shared ? 'Make Private' : 'Share'"
            :icon="recipe.is_shared ? 'pi pi-lock' : 'pi pi-globe'"
            outlined
            :severity="recipe.is_shared ? 'secondary' : 'primary'"
            @click="toggleShare"
          />
        </div>
      </div>

      <!-- Content (from draft or latest version) -->
      <template v-if="displayContent">
        <!-- Meta row -->
        <div style="
          display: flex; flex-wrap: wrap; gap: 1rem; font-size: 0.875rem;
          color: var(--p-text-muted-color); padding: 1rem;
          background: var(--p-surface-50); border-radius: 10px; margin-bottom: 1.25rem;
        ">
          <span v-if="displayContent.description" style="width: 100%; color: var(--p-text-color)">{{ displayContent.description }}</span>
          <span v-if="displayContent.servings"><i class="pi pi-users" style="margin-right: 0.3rem"></i>{{ displayContent.servings }} servings</span>
          <span v-if="displayContent.prep_time"><i class="pi pi-clock" style="margin-right: 0.3rem"></i>Prep: {{ displayContent.prep_time }} min</span>
          <span v-if="displayContent.cook_time"><i class="pi pi-hourglass" style="margin-right: 0.3rem"></i>Cook: {{ displayContent.cook_time }} min</span>
          <div v-if="displayContent.categories.length" style="display: flex; gap: 0.4rem; flex-wrap: wrap">
            <Tag v-for="c in displayContent.categories" :key="c" :value="c" severity="secondary" />
          </div>
          <div v-if="displayContent.tags.length" style="display: flex; gap: 0.4rem; flex-wrap: wrap">
            <Tag v-for="t in displayContent.tags" :key="t" :value="t" />
          </div>
        </div>

        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1.25rem">
          <!-- Ingredients -->
          <Card>
            <template #title><span style="font-size: 1rem"><i class="pi pi-list" style="margin-right: 0.5rem"></i>Ingredients</span></template>
            <template #content>
              <div v-for="ing in displayContent.ingredients" :key="ing.name"
                style="display: flex; justify-content: space-between; padding: 0.4rem 0; border-bottom: 1px solid var(--p-surface-100)">
                <span>{{ ing.name }}</span>
                <strong>{{ ing.quantity }} {{ ing.unit }}</strong>
              </div>
              <p v-if="!displayContent.ingredients.length" style="color: var(--p-text-muted-color); font-size: 0.9rem; margin: 0">No ingredients listed</p>
            </template>
          </Card>

          <!-- Steps -->
          <Card>
            <template #title><span style="font-size: 1rem"><i class="pi pi-list-check" style="margin-right: 0.5rem"></i>Steps</span></template>
            <template #content>
              <div v-for="(prep, i) in displayContent.preparations" :key="`prep-${i}`"
                style="display: flex; gap: 0.75rem; margin-bottom: 0.75rem; font-style: italic; font-size: 0.9rem; color: var(--p-text-muted-color)">
                <span style="font-weight: 700; flex-shrink: 0">Prep</span>{{ prep }}
              </div>
              <div v-for="(step, i) in displayContent.steps" :key="i"
                style="display: flex; gap: 0.75rem; margin-bottom: 0.75rem; font-size: 0.9rem">
                <span style="
                  flex-shrink: 0; width: 1.4rem; height: 1.4rem; border-radius: 50%;
                  background: var(--p-primary-100); color: var(--p-primary-color);
                  display: flex; align-items: center; justify-content: center;
                  font-size: 0.75rem; font-weight: 700; margin-top: 0.1rem
                ">{{ i + 1 }}</span>
                {{ step }}
              </div>
              <p v-if="!displayContent.steps.length" style="color: var(--p-text-muted-color); font-size: 0.9rem; margin: 0">No steps listed</p>
            </template>
          </Card>
        </div>

        <div v-if="displayContent.notes" style="
          margin-top: 1rem; padding: 1rem;
          background: #fef9c3; border-radius: 10px;
          border-left: 3px solid #eab308; font-size: 0.9rem
        ">
          <strong>Notes:</strong> {{ displayContent.notes }}
        </div>
      </template>

      <div v-else style="color: var(--p-text-muted-color); text-align: center; padding: 3rem">
        <p>No content yet. <RouterLink :to="`/recipes/${recipe.id}/edit`">Start editing</RouterLink></p>
      </div>
    </div>

    <!-- Version history sidebar (owner only) -->
    <VersionHistoryPanel v-if="isOwner && recipe" :recipe="recipe" style="width: 270px; border-left: 1px solid var(--p-surface-200)" />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useToast } from 'primevue/usetoast'
import { useConfirm } from 'primevue/useconfirm'
import { useAuthStore } from '@/stores/auth'
import { recipesApi } from '@/api/recipes'
import type { RecipeDetailOut, RecipeContent } from '@/types'
import VersionHistoryPanel from '@/components/VersionHistoryPanel.vue'
import Button from 'primevue/button'
import Card from 'primevue/card'
import Tag from 'primevue/tag'
import Rating from 'primevue/rating'
import ProgressSpinner from 'primevue/progressspinner'

const route = useRoute()
const router = useRouter()
const toast = useToast()
const confirm = useConfirm()
const auth = useAuthStore()

const recipe = ref<RecipeDetailOut | null>(null)
const versionContent = ref<RecipeContent | null>(null)
const loading = ref(true)
const forking = ref(false)

const isOwner = computed(() => recipe.value?.owner_id === auth.user?.id)

const displayContent = computed<RecipeContent | null>(() => {
  if (!recipe.value) return null
  if (recipe.value.draft_content) return recipe.value.draft_content
  return versionContent.value
})

async function load() {
  loading.value = true
  try {
    recipe.value = await recipesApi.get(Number(route.params.id))
    // If no draft but has a latest version, fetch its full content
    if (!recipe.value.draft_content && recipe.value.latest_version) {
      const vd = await recipesApi.getVersion(recipe.value.id, recipe.value.latest_version.version_number)
      versionContent.value = vd.content
    }
  } finally {
    loading.value = false
  }
}

async function doToggleShare() {
  if (!recipe.value) return
  try {
    await recipesApi.updateMeta(recipe.value.id, { is_shared: !recipe.value.is_shared })
    await load()
    toast.add({
      severity: 'success',
      summary: 'Updated',
      detail: recipe.value.is_shared ? 'Now shared' : 'Now private',
      life: 2500,
    })
  } catch {
    toast.add({ severity: 'error', summary: 'Error', detail: 'Failed to update', life: 3000 })
  }
}

async function toggleShare() {
  if (!recipe.value) return
  if (recipe.value.is_shared) {
    confirm.require({
      message: 'Make this recipe private? Other users will no longer be able to view or fork it.',
      header: 'Make Private',
      icon: 'pi pi-lock',
      acceptLabel: 'Make Private',
      rejectLabel: 'Cancel',
      accept: doToggleShare,
    })
  } else {
    await doToggleShare()
  }
}

async function forkRecipe() {
  if (!recipe.value) return
  forking.value = true
  try {
    const forked = await recipesApi.fork(recipe.value.id)
    toast.add({ severity: 'success', summary: 'Forked!', detail: 'Added to your cookbook', life: 3000 })
    router.push(`/recipes/${forked.id}/edit`)
  } catch {
    toast.add({ severity: 'error', summary: 'Error', detail: 'Failed to fork', life: 3000 })
  } finally {
    forking.value = false
  }
}

onMounted(load)
</script>
