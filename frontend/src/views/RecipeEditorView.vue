<template>
  <div v-if="loading" style="display: flex; justify-content: center; align-items: center; height: 50vh">
    <ProgressSpinner />
  </div>

  <div v-else-if="content" style="display: flex; height: 100%; overflow: hidden">
    <!-- Editor -->
    <div style="flex: 1; overflow-y: auto; padding: 1.5rem">
      <!-- Header bar -->
      <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 1.5rem; flex-wrap: wrap; gap: 0.75rem">
        <div style="display: flex; align-items: center; gap: 0.75rem">
          <Button icon="pi pi-arrow-left" text rounded @click="router.push(`/recipes/${recipeId}`)" />
          <h1 style="margin: 0; font-size: 1.25rem; font-weight: 700">Edit Recipe</h1>
          <Tag v-if="isDirty" value="Unsaved" severity="warn" icon="pi pi-pencil" />
          <span v-if="saving" style="font-size: 0.8rem; color: var(--p-text-muted-color); display: flex; align-items: center; gap: 0.3rem">
            <i class="pi pi-spin pi-spinner" style="font-size: 0.75rem"></i> Saving...
          </span>
        </div>
        <Button label="Save Version" icon="pi pi-check-circle" @click="showVersionDialog = true" />
      </div>

      <!-- Title & meta -->
      <Card style="margin-bottom: 1rem">
        <template #content>
          <div style="display: flex; flex-direction: column; gap: 1rem">
            <div class="flex flex-col gap-1">
              <label class="font-medium text-sm">Title *</label>
              <InputText v-model="content.title" fluid @input="scheduleSave" />
            </div>
            <div class="flex flex-col gap-1">
              <label class="font-medium text-sm">Description</label>
              <Textarea v-model="content.description" rows="2" fluid @input="scheduleSave" />
            </div>
            <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem">
              <div class="flex flex-col gap-1">
                <label class="font-medium text-sm">Servings</label>
                <InputNumber v-model="content.servings" :min="1" fluid @update:modelValue="scheduleSave" />
              </div>
              <div class="flex flex-col gap-1">
                <label class="font-medium text-sm">Prep (min)</label>
                <InputNumber v-model="content.prep_time" :min="0" fluid @update:modelValue="scheduleSave" />
              </div>
              <div class="flex flex-col gap-1">
                <label class="font-medium text-sm">Cook (min)</label>
                <InputNumber v-model="content.cook_time" :min="0" fluid @update:modelValue="scheduleSave" />
              </div>
            </div>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem">
              <div class="flex flex-col gap-1">
                <label class="font-medium text-sm">Categories</label>
                <InputChips v-model="content.categories" placeholder="Italian, Pasta..." fluid @update:modelValue="scheduleSave" />
              </div>
              <div class="flex flex-col gap-1">
                <label class="font-medium text-sm">Tags</label>
                <InputChips v-model="content.tags" placeholder="vegetarian, quick..." fluid @update:modelValue="scheduleSave" />
              </div>
            </div>
          </div>
        </template>
      </Card>

      <!-- Ingredients -->
      <Card style="margin-bottom: 1rem">
        <template #title>
          <div style="display: flex; align-items: center; justify-content: space-between">
            <span style="font-size: 1rem">Ingredients</span>
            <Button label="Add" icon="pi pi-plus" text size="small" @click="addIngredient" />
          </div>
        </template>
        <template #content>
          <div style="display: flex; flex-direction: column; gap: 0.5rem">
            <IngredientRow
              v-for="(_, i) in content.ingredients"
              :key="i"
              v-model="content.ingredients[i]"
              :tweakPct="tweakPct"
              @remove="removeIngredient(i)"
              @change="scheduleSave"
            />
            <p v-if="!content.ingredients.length" style="color: var(--p-text-muted-color); font-size: 0.9rem; margin: 0">No ingredients yet</p>
          </div>
        </template>
      </Card>

      <!-- Steps -->
      <Card style="margin-bottom: 1rem">
        <template #title>
          <div style="display: flex; align-items: center; justify-content: space-between">
            <span style="font-size: 1rem">Steps</span>
            <Button label="Add Step" icon="pi pi-plus" text size="small" @click="addStep" />
          </div>
        </template>
        <template #content>
          <div style="display: flex; flex-direction: column; gap: 0.75rem">
            <div v-for="(_, i) in content.steps" :key="i" style="display: flex; gap: 0.75rem; align-items: flex-start">
              <span style="
                flex-shrink: 0; width: 1.5rem; height: 1.5rem; border-radius: 50%;
                background: var(--p-primary-100); color: var(--p-primary-color);
                display: flex; align-items: center; justify-content: center;
                font-size: 0.75rem; font-weight: 700; margin-top: 0.5rem
              ">{{ i + 1 }}</span>
              <Textarea v-model="content.steps[i]" rows="2" fluid @input="scheduleSave" style="flex: 1" />
              <Button icon="pi pi-trash" text rounded severity="danger" size="small" style="margin-top: 0.3rem" @click="removeStep(i)" />
            </div>
          </div>
        </template>
      </Card>

      <!-- Notes -->
      <Card style="margin-bottom: 1rem">
        <template #content>
          <div class="flex flex-col gap-1">
            <label class="font-medium text-sm">Notes</label>
            <Textarea v-model="content.notes" rows="3" placeholder="Any tips, substitutions, or observations..." fluid @input="scheduleSave" />
          </div>
        </template>
      </Card>
    </div>

    <!-- Version history sidebar -->
    <VersionHistoryPanel
      v-if="recipe"
      :recipe="recipe"
      style="width: 270px; border-left: 1px solid var(--p-surface-200)"
      @restore="restoreVersion"
    />
  </div>

  <!-- Save Version Dialog -->
  <SaveVersionDialog v-model:visible="showVersionDialog" :saving="versioning" @save="handleSaveVersion" />
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useToast } from 'primevue/usetoast'
import { useAuthStore } from '@/stores/auth'
import { recipesApi } from '@/api/recipes'
import type { RecipeDetailOut, RecipeContent } from '@/types'
import { emptyContent } from '@/types'
import IngredientRow from '@/components/IngredientRow.vue'
import VersionHistoryPanel from '@/components/VersionHistoryPanel.vue'
import SaveVersionDialog from '@/components/SaveVersionDialog.vue'
import Button from 'primevue/button'
import Card from 'primevue/card'
import InputText from 'primevue/inputtext'
import Textarea from 'primevue/textarea'
import InputNumber from 'primevue/inputnumber'
import InputChips from 'primevue/inputchips'
import Tag from 'primevue/tag'
import ProgressSpinner from 'primevue/progressspinner'

const route = useRoute()
const router = useRouter()
const toast = useToast()
const auth = useAuthStore()

const recipeId = computed(() => Number(route.params.id))
const recipe = ref<RecipeDetailOut | null>(null)
const content = ref<RecipeContent | null>(null)
const loading = ref(true)
const saving = ref(false)
const isDirty = ref(false)
const showVersionDialog = ref(false)
const versioning = ref(false)

const tweakPct = computed(() => auth.user?.tweak_percentage ?? 10)

let saveTimer: ReturnType<typeof setTimeout>
function scheduleSave() {
  isDirty.value = true
  clearTimeout(saveTimer)
  saveTimer = setTimeout(saveDraft, 2000)
}

async function saveDraft() {
  if (!content.value || !isDirty.value || !content.value.title.trim()) return
  saving.value = true
  try {
    recipe.value = await recipesApi.updateDraft(recipeId.value, content.value)
    isDirty.value = false
  } catch {
    // silent auto-save failure
  } finally {
    saving.value = false
  }
}

function addIngredient() {
  content.value?.ingredients.push({ name: '', quantity: 100, unit: 'g' })
  scheduleSave()
}
function removeIngredient(i: number) {
  content.value?.ingredients.splice(i, 1)
  scheduleSave()
}
function addStep() {
  content.value?.steps.push('')
  scheduleSave()
}
function removeStep(i: number) {
  content.value?.steps.splice(i, 1)
  scheduleSave()
}

function restoreVersion(vContent: RecipeContent) {
  content.value = { ...vContent }
  isDirty.value = true
  scheduleSave()
  toast.add({ severity: 'info', summary: 'Restored', detail: 'Version content loaded into draft', life: 3000 })
}

async function handleSaveVersion() {
  if (!content.value) return
  clearTimeout(saveTimer)
  versioning.value = true
  try {
    await recipesApi.saveVersion(recipeId.value, content.value)
    recipe.value = await recipesApi.get(recipeId.value)
    isDirty.value = false
    showVersionDialog.value = false
    toast.add({ severity: 'success', summary: 'Version saved!', detail: 'Rate it after you cook it!', life: 3000 })
  } catch {
    toast.add({ severity: 'error', summary: 'Error', detail: 'Failed to save version', life: 3000 })
  } finally {
    versioning.value = false
  }
}

onMounted(async () => {
  try {
    recipe.value = await recipesApi.get(recipeId.value)
    if (recipe.value.draft_content) {
      content.value = { ...recipe.value.draft_content }
    } else if (recipe.value.latest_version) {
      const vd = await recipesApi.getVersion(recipeId.value, recipe.value.latest_version.version_number)
      content.value = { ...vd.content }
    } else {
      content.value = emptyContent()
    }
  } finally {
    loading.value = false
  }
})
</script>
