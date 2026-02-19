export interface UserPublic {
  id: number
  username: string
  email: string
  github_repo_url: string | null
  tweak_percentage: number
  has_github_token: boolean
  created_at: string
}

export interface Ingredient {
  name: string
  quantity: number
  unit: string
}

export interface RecipeContent {
  title: string
  description: string
  servings: number | null
  prep_time: number | null
  cook_time: number | null
  categories: string[]
  tags: string[]
  notes: string
  photos: string[]
  ingredients: Ingredient[]
  preparations: string[]
  steps: string[]
}

export function emptyContent(): RecipeContent {
  return {
    title: '',
    description: '',
    servings: null,
    prep_time: null,
    cook_time: null,
    categories: [],
    tags: [],
    notes: '',
    photos: [],
    ingredients: [],
    preparations: [],
    steps: []
  }
}

export interface RecipeVersionOut {
  id: number
  version_number: number
  rating: number | null
  commit_hash: string | null
  push_status: 'pending' | 'pushed' | 'failed'
  created_at: string
}

export interface RecipeVersionDetail extends RecipeVersionOut {
  content: RecipeContent
}

export interface RecipeOut {
  id: number
  slug: string
  title: string
  owner_id: number
  is_shared: boolean
  has_draft: boolean
  forked_from_attribution: string | null
  created_at: string
  updated_at: string
}

export interface RecipeDetailOut extends RecipeOut {
  draft_content: RecipeContent | null
  latest_version: RecipeVersionOut | null
  versions: RecipeVersionOut[]
}

export interface CategoryOut { id: number; name: string }
export interface TagOut { id: number; name: string }

export interface IngredientDiff {
  name: string
  from_: Ingredient
  to: Ingredient
}

export interface DiffOut {
  v1: number
  v2: number
  recipe_id: number
  metadata_changes: Record<string, { from_: unknown; to: unknown }>
  ingredients: { added: Ingredient[]; removed: Ingredient[]; changed: IngredientDiff[] }
  steps: { added: string[]; removed: string[] }
  preparations: { added: string[]; removed: string[] }
}
