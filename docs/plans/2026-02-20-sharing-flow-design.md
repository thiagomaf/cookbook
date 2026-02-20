# Sharing Flow Design

**Date:** 2026-02-20
**Status:** Approved

## Overview

Complete the recipe sharing UX. The data model, backend endpoints, and basic frontend
wiring all exist. This design fills the remaining gaps:

1. Owner username missing from API responses (shared cards show `user 1` instead of `@alice`)
2. Toast message condition is inverted in `toggleShare()`
3. Breadcrumb shows "My Recipes" even when a non-owner views a shared recipe
4. No confirmation guard before unsharing a recipe
5. No fork button on the shared-recipe card (must navigate in to fork)
6. No share/unshare toggle on the recipe-list card (must open detail view to toggle)

---

## Backend changes

### `RecipeOut` schema — add `owner_username`

Add `owner_username: str` to `RecipeOut` (and by inheritance `RecipeDetailOut`).
The `Recipe.owner` relationship is already eager-loaded by SQLAlchemy, so no extra
query is needed. No DB migration required.

**Files:** `backend/app/schemas/recipe.py`, `backend/app/api/v1/recipes.py`

Changes in `recipes.py`:
- `_build_detail()` — pass `owner_username=recipe.owner.username`
- `update_recipe_meta` endpoint — currently returns `RecipeOut.model_validate(recipe)`
  which won't auto-populate `owner_username` from the ORM object; switch to an explicit
  constructor or use `from_orm` with the relationship available.

---

## Frontend changes

### Bug fix — inverted toast in `toggleShare()`

In `RecipeDetailView.vue`, after `await load()` the recipe is refreshed to its **new**
state. The detail string must read the new `is_shared` value correctly:

```
// before (wrong)
detail: recipe.value.is_shared ? 'Now private' : 'Now shared'

// after (correct)
detail: recipe.value.is_shared ? 'Now shared' : 'Now private'
```

### Bug fix — breadcrumb for non-owner shared recipe

In `RecipeDetailView.vue`, conditionally render the breadcrumb based on ownership:

- Owner → `My Recipes` → `/recipes` (current behaviour)
- Non-owner → `Shared Recipes` → `/shared`

### Confirmation dialog — "Make Private"

Use PrimeVue `useConfirm()` / `ConfirmDialog`. Trigger only when unsharing
(i.e. `recipe.value.is_shared === true`). Message:

> Make this recipe private? Other users will no longer be able to view or fork it.

Sharing (going public) requires no confirmation.

**New import needed:** `ConfirmDialog` component added once in `AppLayout.vue` (global
placement), `useConfirm` composable in `RecipeDetailView.vue`.

### `RecipeCard.vue` — two new optional action buttons

New props (both default `false`):

| Prop | Type | Purpose |
|---|---|---|
| `showShareToggle` | `boolean` | Globe/lock icon button in top-right of header row |
| `showForkButton` | `boolean` | Fork icon button at bottom of card |

New emits:

| Event | Payload | Triggered by |
|---|---|---|
| `toggle-share` | `recipe: RecipeDetailOut` | Share toggle button click |
| `fork` | `recipe: RecipeDetailOut` | Fork button click |

Both button click handlers call `event.stopPropagation()` to prevent card navigation.

**Share toggle button** — rendered inside the existing header `<div>` alongside the
draft `Tag`. Shows `pi-globe` (private state) or `pi-lock` (shared state). Uses
`severity="secondary"` ghost style, small size.

**Fork button** — rendered at the bottom right of the card footer row. Icon
`pi-code-branch`, ghost/outlined, small. Hidden if `recipe.owner_id === currentUser.id`
(can't fork your own recipe) — read `useAuthStore()` inside the card for this guard.

### `RecipeListView.vue` — share toggle wiring

- Pass `:showShareToggle="true"` to each `RecipeCard`
- Handle `@toggle-share`:
  - If toggling **off** (making private): show `useConfirm()` dialog first
  - On confirm: call `recipesApi.updateMeta(recipe.id, { is_shared: !recipe.is_shared })`
  - Toast success, then reload the list (or optimistically update the single item)
  - Toast error on failure

### `SharedRecipesView.vue` — fork button wiring

- Pass `:showForkButton="true"` to each `RecipeCard`
- Handle `@fork`:
  - Set a per-recipe loading state so the button shows a spinner
  - Call `recipesApi.fork(recipe.id)`
  - Toast "Added to your cookbook"
  - `router.push(`/recipes/${forked.id}/edit`)`
  - Toast error on failure

### `frontend/src/types/index.ts`

Add `owner_username: string` to `RecipeOut` interface.

---

## What is NOT changing

- No new routes or navigation items
- No changes to the Shared Recipes page layout
- No changes to backend auth/permissions logic
- `ConfirmDialog` is already available in PrimeVue 4 — no new dependency

---

## File change summary

| File | Change |
|---|---|
| `backend/app/schemas/recipe.py` | Add `owner_username: str` to `RecipeOut` |
| `backend/app/api/v1/recipes.py` | Populate `owner_username` in `_build_detail()` and `update_recipe_meta` |
| `frontend/src/types/index.ts` | Add `owner_username: string` to `RecipeOut` |
| `frontend/src/components/RecipeCard.vue` | Add `showShareToggle`, `showForkButton` props + action buttons |
| `frontend/src/views/RecipeDetailView.vue` | Fix toast, fix breadcrumb, add confirm dialog for unshare |
| `frontend/src/views/RecipeListView.vue` | Wire `@toggle-share` with confirm + API call |
| `frontend/src/views/SharedRecipesView.vue` | Wire `@fork` with API call + toast + navigate |
| `frontend/src/views/AppLayout.vue` | Add `<ConfirmDialog />` once (global placement) |
