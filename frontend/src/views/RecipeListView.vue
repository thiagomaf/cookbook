<template>
  <div style="padding: 1.5rem">
    <!-- Header -->
    <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 1.5rem">
      <h1 style="margin: 0; font-size: 1.5rem; font-weight: 700">My Recipes</h1>
      <Button label="New Recipe" icon="pi pi-plus" @click="showNewDialog = true" />
    </div>

    <!-- Filters -->
    <div style="display: flex; gap: 0.75rem; margin-bottom: 1.25rem; flex-wrap: wrap">
      <IconField style="flex: 1; min-width: 200px">
        <InputIcon class="pi pi-search" />
        <InputText v-model="searchQuery" placeholder="Search recipes..." fluid @input="debouncedSearch" />
      </IconField>
      <Select
        v-model="filterCategory"
        :options="categoryOptions"
        optionLabel="name"
        optionValue="name"
        placeholder="Category"
        showClear
        style="width: 160px"
        @change="loadRecipes"
      />
      <Select
        v-model="filterTag"
        :options="tagOptions"
        optionLabel="name"
        optionValue="name"
        placeholder="Tag"
        showClear
        style="width: 140px"
        @change="loadRecipes"
      />
    </div>

    <!-- Loading skeletons -->
    <div v-if="loading" style="display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 1rem">
      <Skeleton v-for="i in 6" :key="i" height="150px" style="border-radius: 12px" />
    </div>

    <!-- Empty state -->
    <div v-else-if="recipes.length === 0" style="text-align: center; padding: 4rem 0; color: var(--p-text-muted-color)">
      <i class="pi pi-book" style="font-size: 4rem; display: block; margin-bottom: 1rem"></i>
      <p style="font-size: 1.1rem; font-weight: 500; margin: 0 0 0.5rem">No recipes yet</p>
      <p style="margin: 0; font-size: 0.9rem">Click "New Recipe" to get started</p>
    </div>

    <!-- Recipe grid -->
    <div v-else style="display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 1rem">
      <RecipeCard
        v-for="recipe in recipes"
        :key="recipe.id"
        :recipe="recipe"
        :showShareToggle="true"
        @click="router.push(`/recipes/${recipe.id}`)"
        @toggle-share="handleToggleShare"
      />
    </div>
  </div>

  <!-- New Recipe Dialog -->
  <Dialog v-model:visible="showNewDialog" header="New Recipe" modal style="width: min(420px, 95vw)">
    <div style="display: flex; flex-direction: column; gap: 0.75rem; padding-top: 0.5rem">
      <label class="font-medium text-sm">Recipe Title</label>
      <InputText v-model="newTitle" placeholder="e.g. Pasta Carbonara" fluid autofocus @keyup.enter="createRecipe" />
    </div>
    <template #footer>
      <Button label="Cancel" text @click="showNewDialog = false; newTitle = ''" />
      <Button label="Create & Edit" icon="pi pi-arrow-right" :disabled="!newTitle.trim()" :loading="creating" @click="createRecipe" />
    </template>
  </Dialog>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useToast } from 'primevue/usetoast'
import { useConfirm } from 'primevue/useconfirm'
import { recipesApi } from '@/api/recipes'
import type { RecipeDetailOut } from '@/types'
import { emptyContent } from '@/types'
import RecipeCard from '@/components/RecipeCard.vue'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import Select from 'primevue/select'
import Dialog from 'primevue/dialog'
import Skeleton from 'primevue/skeleton'
import IconField from 'primevue/iconfield'
import InputIcon from 'primevue/inputicon'

const router = useRouter()
const toast = useToast()
const confirm = useConfirm()

const recipes = ref<RecipeDetailOut[]>([])
const loading = ref(false)
const searchQuery = ref('')
const filterCategory = ref<string | null>(null)
const filterTag = ref<string | null>(null)
const categoryOptions = ref<{ name: string }[]>([])
const tagOptions = ref<{ name: string }[]>([])
const showNewDialog = ref(false)
const newTitle = ref('')
const creating = ref(false)

let searchTimer: ReturnType<typeof setTimeout>
function debouncedSearch() {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(loadRecipes, 400)
}

async function loadRecipes() {
  loading.value = true
  try {
    recipes.value = await recipesApi.list({
      search: searchQuery.value || undefined,
      category: filterCategory.value || undefined,
      tag: filterTag.value || undefined
    })
  } finally {
    loading.value = false
  }
}

async function loadFilters() {
  const [cats, tags] = await Promise.all([recipesApi.getCategories(), recipesApi.getTags()])
  categoryOptions.value = cats
  tagOptions.value = tags
}

async function createRecipe() {
  creating.value = true
  try {
    const content = emptyContent()
    content.title = newTitle.value.trim()
    const recipe = await recipesApi.create(content)
    showNewDialog.value = false
    newTitle.value = ''
    router.push(`/recipes/${recipe.id}/edit`)
  } catch {
    toast.add({ severity: 'error', summary: 'Error', detail: 'Failed to create recipe', life: 3000 })
  } finally {
    creating.value = false
  }
}

function handleToggleShare(recipe: RecipeDetailOut) {
  if (recipe.is_shared) {
    confirm.require({
      message: 'Make this recipe private? Other users will no longer be able to view or fork it.',
      header: 'Make Private',
      icon: 'pi pi-lock',
      acceptLabel: 'Make Private',
      rejectLabel: 'Cancel',
      accept: () => doToggleShare(recipe),
    })
  } else {
    doToggleShare(recipe)
  }
}

async function doToggleShare(recipe: RecipeDetailOut) {
  try {
    await recipesApi.updateMeta(recipe.id, { is_shared: !recipe.is_shared })
    // Optimistic update — flip the flag in the local list
    const idx = recipes.value.findIndex(r => r.id === recipe.id)
    if (idx !== -1) {
      recipes.value[idx] = { ...recipes.value[idx], is_shared: !recipe.is_shared }
    }
    toast.add({
      severity: 'success',
      summary: 'Updated',
      detail: recipe.is_shared ? 'Now private' : 'Now shared',
      life: 2500,
    })
  } catch {
    toast.add({ severity: 'error', summary: 'Error', detail: 'Failed to update', life: 3000 })
  }
}

onMounted(() => {
  loadRecipes()
  loadFilters()
})
</script>
