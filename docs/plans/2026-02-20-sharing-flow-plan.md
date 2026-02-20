# Sharing Flow Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Complete the recipe sharing UX — owner username display, bug fixes, confirmation dialog, share toggle on recipe cards, and fork button on shared recipe cards.

**Architecture:** Backend adds `owner_username` to `RecipeOut` (populated via the already-loaded `owner` relationship). Frontend `RecipeCard` gets two optional action-button props (`showShareToggle`, `showForkButton`); parent views wire the emitted events. Three bugs in `RecipeDetailView` are fixed as a separate task.

**Tech Stack:** FastAPI + Pydantic v2 (backend), Vue 3 + PrimeVue 4 + TypeScript (frontend). No test infrastructure exists — verification is manual via browser / curl.

---

## Task 1: Backend — add `owner_username` to `RecipeOut`

**Files:**
- Modify: `backend/app/schemas/recipe.py`
- Modify: `backend/app/api/v1/recipes.py`

**Step 1: Add `owner_username` field to `RecipeOut`**

In `backend/app/schemas/recipe.py`, add `owner_username: str` to `RecipeOut`:

```python
class RecipeOut(BaseModel):
    id: int
    slug: str
    title: str
    owner_id: int
    owner_username: str          # ← ADD THIS LINE
    is_shared: bool
    has_draft: bool
    forked_from_attribution: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
```

**Step 2: Populate `owner_username` in `_build_detail()`**

`_build_detail()` in `backend/app/api/v1/recipes.py` already constructs `RecipeDetailOut` with explicit kwargs (lines 50–63). Add `owner_username=recipe.owner.username` to that call:

```python
def _build_detail(recipe: Recipe) -> RecipeDetailOut:
    versions = sorted(recipe.versions, key=lambda v: v.version_number)
    latest = versions[-1] if versions else None
    draft_content = RecipeContent(**recipe.draft.content) if recipe.draft else None
    return RecipeDetailOut(
        id=recipe.id,
        slug=recipe.slug,
        title=recipe.title,
        owner_id=recipe.owner_id,
        owner_username=recipe.owner.username,   # ← ADD THIS LINE
        is_shared=recipe.is_shared,
        has_draft=recipe.has_draft,
        forked_from_attribution=recipe.forked_from_attribution,
        created_at=recipe.created_at,
        updated_at=recipe.updated_at,
        draft_content=draft_content,
        latest_version=RecipeVersionOut.model_validate(latest) if latest else None,
        versions=[RecipeVersionOut.model_validate(v) for v in versions],
    )
```

**Step 3: Fix `update_recipe_meta` endpoint**

The `update_recipe_meta` endpoint (line 129–137) currently returns `RecipeOut.model_validate(recipe)`. `model_validate` with `from_attributes=True` reads attributes directly off the ORM object — `owner_username` is not a column so it won't be found. Switch to explicit construction:

```python
@router.patch("/{recipe_id}", response_model=RecipeOut)
def update_recipe_meta(
    recipe_id: int,
    body: RecipeMetaUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    recipe = _get_own_or_404(db, recipe_id, current_user)
    updated = crud.update_meta(db, recipe, body.is_shared)
    return RecipeOut(
        id=updated.id,
        slug=updated.slug,
        title=updated.title,
        owner_id=updated.owner_id,
        owner_username=updated.owner.username,
        is_shared=updated.is_shared,
        has_draft=updated.has_draft,
        forked_from_attribution=updated.forked_from_attribution,
        created_at=updated.created_at,
        updated_at=updated.updated_at,
    )
```

**Step 4: Verify**

Start the dev server (`uvicorn app.main:app --reload` from `backend/`) and run:

```bash
curl -s -X POST http://localhost:8000/api/v1/auth/token \
  -d "username=<user>&password=<pass>" | jq '.access_token'

curl -s http://localhost:8000/api/v1/recipes/ \
  -H "Authorization: Bearer <token>" | jq '.[0].owner_username'
```

Expected: a string like `"alice"`, not `null` or error.

**Step 5: Commit**

```bash
git add backend/app/schemas/recipe.py backend/app/api/v1/recipes.py
git commit -m "feat: add owner_username to RecipeOut response"
```

---

## Task 2: Frontend — update TypeScript type + RecipeCard owner display

**Files:**
- Modify: `frontend/src/types/index.ts`
- Modify: `frontend/src/components/RecipeCard.vue`

**Step 1: Add `owner_username` to `RecipeOut` interface**

In `frontend/src/types/index.ts`, add the field to `RecipeOut`:

```typescript
export interface RecipeOut {
  id: number
  slug: string
  title: string
  owner_id: number
  owner_username: string      // ← ADD THIS LINE
  is_shared: boolean
  has_draft: boolean
  forked_from_attribution: string | null
  created_at: string
  updated_at: string
}
```

**Step 2: Use `owner_username` in `RecipeCard`**

In `frontend/src/components/RecipeCard.vue`, line 41 currently reads:

```html
<span v-if="showOwner">by user {{ recipe.owner_id }}</span>
```

Change it to:

```html
<span v-if="showOwner">by @{{ recipe.owner_username }}</span>
```

**Step 3: Verify**

Open the browser, navigate to Shared Recipes (`/shared`). Cards should now show `by @alice` (real username) instead of `by user 1`.

**Step 4: Commit**

```bash
git add frontend/src/types/index.ts frontend/src/components/RecipeCard.vue
git commit -m "feat: show owner username on shared recipe cards"
```

---

## Task 3: `AppLayout.vue` — register `ConfirmDialog`

**Files:**
- Modify: `frontend/src/views/AppLayout.vue`

`ConfirmationService` is already registered in `main.ts`. We just need `<ConfirmDialog />` placed once in the component tree so PrimeVue knows where to render confirmation prompts.

**Step 1: Add `<ConfirmDialog />` to `AppLayout`**

Import and place it right after the opening `<div>` in the template:

```vue
<template>
  <div style="display: flex; height: 100vh; overflow: hidden; background: var(--p-surface-50)">
    <ConfirmDialog />    <!-- ← ADD THIS LINE -->
    <!-- Sidebar -->
    ...
```

Add the import at the top of the `<script setup>`:

```typescript
import ConfirmDialog from 'primevue/confirmdialog'
```

**Step 2: Verify**

No visual change expected — this is plumbing. The component mounts silently until a `confirm.require()` is called. Verify by opening the app and confirming no console errors.

**Step 3: Commit**

```bash
git add frontend/src/views/AppLayout.vue
git commit -m "feat: register ConfirmDialog in AppLayout for global confirm prompts"
```

---

## Task 4: `RecipeDetailView.vue` — three bug fixes

**Files:**
- Modify: `frontend/src/views/RecipeDetailView.vue`

**Step 1: Fix the inverted toast message**

Find the `toggleShare` function (around line 173). The `detail` string in the toast is wrong — after `load()`, `recipe.value` holds the *new* state. The condition must match that:

```typescript
// Change (line ~178):
detail: recipe.value.is_shared ? 'Now private' : 'Now shared'
// To:
detail: recipe.value.is_shared ? 'Now shared' : 'Now private'
```

**Step 2: Fix the breadcrumb for non-owners**

The breadcrumb is at lines 10–14. Change the static link to a conditional:

```html
<!-- Before -->
<RouterLink to="/recipes" style="color: var(--p-primary-color); text-decoration: none">My Recipes</RouterLink>

<!-- After -->
<RouterLink
  :to="isOwner ? '/recipes' : '/shared'"
  style="color: var(--p-primary-color); text-decoration: none"
>{{ isOwner ? 'My Recipes' : 'Shared Recipes' }}</RouterLink>
```

**Step 3: Add confirmation before unsharing**

Add `useConfirm` import at the top of `<script setup>` alongside the existing imports:

```typescript
import { useConfirm } from 'primevue/useconfirm'
const confirm = useConfirm()
```

Refactor `toggleShare` to split the actual API call into a helper `doToggleShare`, and wrap the "make private" path in a confirm dialog:

```typescript
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
```

**Step 4: Verify**

1. Open a recipe you own that is currently shared → click "Make Private" → confirm dialog should appear.
2. Confirm → recipe becomes private → toast says "Now private".
3. Click "Share" → no dialog, recipe becomes shared → toast says "Now shared".
4. Open a shared recipe you do NOT own → breadcrumb should say "Shared Recipes" and link to `/shared`.

**Step 5: Commit**

```bash
git add frontend/src/views/RecipeDetailView.vue
git commit -m "fix: toast message, breadcrumb, and unshare confirmation in recipe detail"
```

---

## Task 5: `RecipeCard.vue` — share toggle and fork action buttons

**Files:**
- Modify: `frontend/src/components/RecipeCard.vue`

**Step 1: Update props and emits**

Replace the existing `defineProps` and `defineEmits` with:

```typescript
import { ref } from 'vue'
import { useAuthStore } from '@/stores/auth'
import type { RecipeDetailOut } from '@/types'
import Tag from 'primevue/tag'
import Rating from 'primevue/rating'
import Button from 'primevue/button'

const props = defineProps<{
  recipe: RecipeDetailOut
  showOwner?: boolean
  showShareToggle?: boolean
  showForkButton?: boolean
}>()

const emit = defineEmits<{
  click: []
  'toggle-share': [recipe: RecipeDetailOut]
  fork: [recipe: RecipeDetailOut]
}>()

const hovered = ref(false)
const auth = useAuthStore()
```

**Step 2: Add the share toggle button to the header row**

The header row is the `<div>` at lines 16–25 (title + draft tag). Add the share toggle button right after the existing draft `<Tag>`:

```html
<div style="display: flex; align-items: flex-start; justify-content: space-between; margin-bottom: 0.5rem">
  <h3 style="margin: 0; font-size: 0.95rem; font-weight: 600; line-height: 1.35; flex: 1">{{ recipe.title }}</h3>
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
```

**Step 3: Add the fork button to the footer row**

The footer row is the `<div>` at lines 40–47 (owner/date + shared/fork indicators). Add the fork button at the end:

```html
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
      @click.stop="emit('fork', recipe)"
    />
  </div>
</div>
```

**Step 4: Verify**

- In My Recipes: each card should have a globe/lock icon in the top-right. Clicking it should stop card navigation (no route change).
- In Shared Recipes: each card should have a "Fork" button in the bottom-right (not visible for your own shared recipes).

**Step 5: Commit**

```bash
git add frontend/src/components/RecipeCard.vue
git commit -m "feat: add share toggle and fork action buttons to RecipeCard"
```

---

## Task 6: `RecipeListView.vue` — wire the share toggle

**Files:**
- Modify: `frontend/src/views/RecipeListView.vue`

**Step 1: Add imports**

In `<script setup>`, add these imports alongside the existing ones:

```typescript
import { useConfirm } from 'primevue/useconfirm'
const confirm = useConfirm()
```

**Step 2: Add `handleToggleShare` handler**

Add these two functions after `createRecipe`:

```typescript
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
```

Note: `detail` uses `recipe.is_shared` (the *old* value before the flip) — which is the correct description of what we just did.

**Step 3: Wire the event on `RecipeCard`**

In the template, update the `RecipeCard` usage:

```html
<RecipeCard
  v-for="recipe in recipes"
  :key="recipe.id"
  :recipe="recipe"
  :showShareToggle="true"
  @click="router.push(`/recipes/${recipe.id}`)"
  @toggle-share="handleToggleShare"
/>
```

**Step 4: Verify**

1. Open My Recipes — each card has a globe (private) or lock (shared) icon.
2. Click the globe on a private recipe → recipe is shared immediately (icon flips to lock, no dialog).
3. Click the lock on a shared recipe → confirm dialog appears.
4. Confirm → recipe becomes private (icon flips to globe).
5. Cancel → nothing changes.

**Step 5: Commit**

```bash
git add frontend/src/views/RecipeListView.vue
git commit -m "feat: share/unshare toggle from recipe list with confirm dialog"
```

---

## Task 7: `SharedRecipesView.vue` — wire the fork button

**Files:**
- Modify: `frontend/src/views/SharedRecipesView.vue`

**Step 1: Add imports and state**

Add to `<script setup>`:

```typescript
import { useRouter } from 'vue-router'
import { useToast } from 'primevue/usetoast'

const router = useRouter()   // already exists — check before adding
const toast = useToast()

const forking = ref<number | null>(null)
```

**Step 2: Add `handleFork` function**

```typescript
async function handleFork(recipe: RecipeDetailOut) {
  forking.value = recipe.id
  try {
    const forked = await recipesApi.fork(recipe.id)
    toast.add({ severity: 'success', summary: 'Forked!', detail: 'Added to your cookbook', life: 3000 })
    router.push(`/recipes/${forked.id}/edit`)
  } catch {
    toast.add({ severity: 'error', summary: 'Error', detail: 'Failed to fork', life: 3000 })
  } finally {
    forking.value = null
  }
}
```

**Step 3: Wire the event on `RecipeCard`**

Update the `RecipeCard` in the template:

```html
<RecipeCard
  v-for="recipe in recipes"
  :key="recipe.id"
  :recipe="recipe"
  :showOwner="true"
  :showForkButton="true"
  @click="router.push(`/recipes/${recipe.id}`)"
  @fork="handleFork"
/>
```

**Step 4: Check existing imports in `SharedRecipesView`**

The view already imports `useRouter` — do NOT add a duplicate. Only add `useToast` and `useRouter` if they're missing. The existing `router` const is declared at line 43 (`const router = useRouter()`). Add only `useToast`.

**Step 5: Verify**

1. Open Shared Recipes — cards for recipes you don't own show a "Fork" button.
2. Cards for your own shared recipes do NOT show the Fork button.
3. Click Fork → spinner while forking → toast "Added to your cookbook" → navigate to the forked recipe's edit view.

**Step 6: Commit**

```bash
git add frontend/src/views/SharedRecipesView.vue
git commit -m "feat: fork button on shared recipe cards"
```

---

## Final verification checklist

- [ ] `GET /recipes/` response includes `owner_username` string field
- [ ] Shared recipe cards show `by @username` (not `by user 1`)
- [ ] Clicking "Share" from recipe detail — no confirm, toast says "Now shared"
- [ ] Clicking "Make Private" from recipe detail — confirm dialog appears, toast says "Now private"
- [ ] My Recipes cards have globe/lock icon; clicking it toggles sharing (with confirm for unshare)
- [ ] Shared Recipes cards have Fork button (hidden for own recipes)
- [ ] Forking navigates to the new recipe's edit view
- [ ] Breadcrumb on a non-owned shared recipe says "Shared Recipes" and links to `/shared`
- [ ] No TypeScript errors in the frontend (run `npm run build` from `frontend/`)
