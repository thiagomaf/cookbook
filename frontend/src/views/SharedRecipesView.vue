<template>
  <div style="padding: 1.5rem">
    <h1 style="margin: 0 0 1.25rem; font-size: 1.5rem; font-weight: 700">Shared Recipes</h1>

    <IconField style="margin-bottom: 1.25rem; max-width: 400px">
      <InputIcon class="pi pi-search" />
      <InputText v-model="search" placeholder="Search shared recipes..." fluid @input="debouncedLoad" />
    </IconField>

    <div v-if="loading" style="display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 1rem">
      <Skeleton v-for="i in 6" :key="i" height="150px" style="border-radius: 12px" />
    </div>

    <div v-else-if="recipes.length === 0" style="text-align: center; padding: 4rem 0; color: var(--p-text-muted-color)">
      <i class="pi pi-users" style="font-size: 4rem; display: block; margin-bottom: 1rem"></i>
      <p style="font-size: 1.1rem; font-weight: 500; margin: 0">No shared recipes yet</p>
    </div>

    <div v-else style="display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 1rem">
      <RecipeCard
        v-for="recipe in recipes"
        :key="recipe.id"
        :recipe="recipe"
        :showOwner="true"
        @click="router.push(`/recipes/${recipe.id}`)"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { recipesApi } from '@/api/recipes'
import type { RecipeDetailOut } from '@/types'
import RecipeCard from '@/components/RecipeCard.vue'
import InputText from 'primevue/inputtext'
import Skeleton from 'primevue/skeleton'
import IconField from 'primevue/iconfield'
import InputIcon from 'primevue/inputicon'

const router = useRouter()
const recipes = ref<RecipeDetailOut[]>([])
const loading = ref(false)
const search = ref('')

let timer: ReturnType<typeof setTimeout>
function debouncedLoad() { clearTimeout(timer); timer = setTimeout(load, 400) }

async function load() {
  loading.value = true
  try {
    recipes.value = await recipesApi.listShared({ search: search.value || undefined })
  } finally {
    loading.value = false
  }
}
onMounted(load)
</script>
