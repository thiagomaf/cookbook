from datetime import datetime
from typing import Optional

from pydantic import BaseModel, field_validator


# ── Recipe content (mirrors the YAML structure) ───────────────────────────────

class Ingredient(BaseModel):
    name: str
    quantity: float
    unit: str


class RecipeContent(BaseModel):
    """Full recipe payload — stored as JSON in DB, serialised to YAML for git."""

    title: str
    description: Optional[str] = None
    servings: Optional[int] = None
    prep_time: Optional[int] = None   # minutes
    cook_time: Optional[int] = None   # minutes
    categories: list[str] = []
    tags: list[str] = []
    notes: Optional[str] = None
    photos: list[str] = []
    ingredients: list[Ingredient] = []
    preparations: list[str] = []
    steps: list[str] = []

    @field_validator("title")
    @classmethod
    def title_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Title cannot be empty")
        return v.strip()


# ── Request bodies ────────────────────────────────────────────────────────────

class RecipeCreate(BaseModel):
    content: RecipeContent


class RecipeSaveVersion(BaseModel):
    content: RecipeContent


class RecipeDraftUpdate(BaseModel):
    content: RecipeContent


class RateVersion(BaseModel):
    rating: int

    @field_validator("rating")
    @classmethod
    def validate_rating(cls, v: int) -> int:
        if not (1 <= v <= 5):
            raise ValueError("Rating must be between 1 and 5")
        return v


# ── Response schemas ──────────────────────────────────────────────────────────

class RecipeVersionOut(BaseModel):
    id: int
    version_number: int
    rating: Optional[int]
    commit_hash: Optional[str]
    push_status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class RecipeOut(BaseModel):
    id: int
    slug: str
    title: str
    owner_id: int
    is_shared: bool
    has_draft: bool
    forked_from_attribution: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class RecipeDetailOut(RecipeOut):
    """Full recipe response including draft content and version history."""

    draft_content: Optional[RecipeContent] = None
    latest_version: Optional[RecipeVersionOut] = None
    versions: list[RecipeVersionOut] = []


class RecipeVersionDetail(RecipeVersionOut):
    """Version with full content — returned when fetching a specific version."""

    content: RecipeContent


class RecipeMetaUpdate(BaseModel):
    """Fields that can be patched on a recipe without touching content."""

    is_shared: Optional[bool] = None


# ── Category / Tag response schemas ──────────────────────────────────────────

class CategoryOut(BaseModel):
    id: int
    name: str
    model_config = {"from_attributes": True}


class TagOut(BaseModel):
    id: int
    name: str
    model_config = {"from_attributes": True}
