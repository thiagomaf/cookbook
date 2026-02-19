from datetime import datetime, timezone

from slugify import slugify
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.recipe import Category, Recipe, RecipeDraft, RecipeVersion, Tag
from app.schemas.recipe import RecipeCreate, RecipeDraftUpdate, RecipeSaveVersion


# ── Helpers ───────────────────────────────────────────────────────────────────

def _unique_slug(db: Session, owner_id: int, title: str) -> str:
    base = slugify(title) or "recipe"
    slug, counter = base, 1
    while db.query(Recipe).filter(
        Recipe.owner_id == owner_id,
        Recipe.slug == slug,
        Recipe.is_deleted.is_(False),
    ).first():
        slug = f"{base}-{counter}"
        counter += 1
    return slug


def _sync_labels(
    db: Session,
    recipe: Recipe,
    category_names: list[str],
    tag_names: list[str],
    owner_id: int,
) -> None:
    """Upsert Category/Tag rows and update the recipe's many-to-many associations."""
    cats = []
    for raw in category_names:
        name = raw.strip()
        if not name:
            continue
        cat = db.query(Category).filter(
            Category.owner_id == owner_id, Category.name == name
        ).first()
        if not cat:
            cat = Category(name=name, owner_id=owner_id)
            db.add(cat)
            db.flush()
        cats.append(cat)
    recipe.categories = cats

    tags = []
    for raw in tag_names:
        name = raw.strip()
        if not name:
            continue
        tag = db.query(Tag).filter(
            Tag.owner_id == owner_id, Tag.name == name
        ).first()
        if not tag:
            tag = Tag(name=name, owner_id=owner_id)
            db.add(tag)
            db.flush()
        tags.append(tag)
    recipe.tags = tags


# ── Queries ───────────────────────────────────────────────────────────────────

def get_recipe(db: Session, recipe_id: int, user_id: int) -> Recipe | None:
    """Return a recipe the user may read (owns it, or it is shared)."""
    return db.query(Recipe).filter(
        Recipe.id == recipe_id,
        Recipe.is_deleted.is_(False),
        or_(Recipe.owner_id == user_id, Recipe.is_shared.is_(True)),
    ).first()


def get_own_recipe(db: Session, recipe_id: int, owner_id: int) -> Recipe | None:
    """Return a recipe owned by the given user (for write operations)."""
    return db.query(Recipe).filter(
        Recipe.id == recipe_id,
        Recipe.owner_id == owner_id,
        Recipe.is_deleted.is_(False),
    ).first()


def list_recipes(
    db: Session,
    owner_id: int,
    search: str | None = None,
    category: str | None = None,
    tag: str | None = None,
    page: int = 1,
    limit: int = 20,
) -> tuple[list[Recipe], int]:
    q = db.query(Recipe).filter(
        Recipe.owner_id == owner_id,
        Recipe.is_deleted.is_(False),
    )
    if search:
        q = q.filter(Recipe.title.ilike(f"%{search}%"))
    if category:
        q = q.join(Recipe.categories).filter(Category.name.ilike(category))
    if tag:
        q = q.join(Recipe.tags).filter(Tag.name.ilike(tag))

    total = q.count()
    items = q.order_by(Recipe.updated_at.desc()).offset((page - 1) * limit).limit(limit).all()
    return items, total


def list_shared(
    db: Session,
    user_id: int,
    search: str | None = None,
    page: int = 1,
    limit: int = 20,
) -> tuple[list[Recipe], int]:
    q = db.query(Recipe).filter(
        Recipe.is_shared.is_(True),
        Recipe.is_deleted.is_(False),
        Recipe.owner_id != user_id,
    )
    if search:
        q = q.filter(Recipe.title.ilike(f"%{search}%"))
    total = q.count()
    items = q.order_by(Recipe.updated_at.desc()).offset((page - 1) * limit).limit(limit).all()
    return items, total


def get_version(db: Session, recipe_id: int, version_number: int) -> RecipeVersion | None:
    return db.query(RecipeVersion).filter(
        RecipeVersion.recipe_id == recipe_id,
        RecipeVersion.version_number == version_number,
    ).first()


def get_categories(db: Session, owner_id: int) -> list[Category]:
    return db.query(Category).filter(Category.owner_id == owner_id).order_by(Category.name).all()


def get_tags(db: Session, owner_id: int) -> list[Tag]:
    return db.query(Tag).filter(Tag.owner_id == owner_id).order_by(Tag.name).all()


# ── Mutations ─────────────────────────────────────────────────────────────────

def create_recipe(db: Session, owner_id: int, body: RecipeCreate) -> Recipe:
    slug = _unique_slug(db, owner_id, body.content.title)
    recipe = Recipe(slug=slug, title=body.content.title, owner_id=owner_id, has_draft=True)
    db.add(recipe)
    db.flush()

    draft = RecipeDraft(recipe_id=recipe.id, content=body.content.model_dump())
    db.add(draft)
    _sync_labels(db, recipe, body.content.categories, body.content.tags, owner_id)

    db.commit()
    db.refresh(recipe)
    return recipe


def update_draft(db: Session, recipe: Recipe, body: RecipeDraftUpdate) -> Recipe:
    if recipe.draft:
        recipe.draft.content = body.content.model_dump()
        recipe.draft.updated_at = datetime.now(timezone.utc)
    else:
        db.add(RecipeDraft(recipe_id=recipe.id, content=body.content.model_dump()))

    recipe.title = body.content.title
    recipe.has_draft = True
    recipe.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(recipe)
    return recipe


def save_version(db: Session, recipe: Recipe, body: RecipeSaveVersion) -> RecipeVersion:
    last = (
        db.query(RecipeVersion)
        .filter(RecipeVersion.recipe_id == recipe.id)
        .order_by(RecipeVersion.version_number.desc())
        .first()
    )
    next_num = (last.version_number + 1) if last else 1

    version = RecipeVersion(
        recipe_id=recipe.id,
        version_number=next_num,
        rating=None,
        content=body.content.model_dump(),
        push_status="pending",
    )
    db.add(version)
    db.flush()

    recipe.title = body.content.title
    recipe.updated_at = datetime.now(timezone.utc)
    _sync_labels(db, recipe, body.content.categories, body.content.tags, recipe.owner_id)

    if recipe.draft:
        db.delete(recipe.draft)
    recipe.has_draft = False

    db.commit()
    db.refresh(version)
    return version


def rate_version(
    db: Session, recipe_id: int, version_number: int, owner_id: int, rating: int
) -> RecipeVersion | None:
    """Set or update the rating of a version. Only the recipe owner may rate."""
    v = (
        db.query(RecipeVersion)
        .join(Recipe, Recipe.id == RecipeVersion.recipe_id)
        .filter(
            RecipeVersion.recipe_id == recipe_id,
            RecipeVersion.version_number == version_number,
            Recipe.owner_id == owner_id,
            Recipe.is_deleted.is_(False),
        )
        .first()
    )
    if not v:
        return None
    v.rating = rating
    db.commit()
    db.refresh(v)
    return v


def update_version_after_commit(
    db: Session, version_id: int, commit_hash: str | None, push_status: str
) -> None:
    v = db.get(RecipeVersion, version_id)
    if v:
        if commit_hash:
            v.commit_hash = commit_hash
        v.push_status = push_status
        db.commit()


def update_meta(db: Session, recipe: Recipe, is_shared: bool | None) -> Recipe:
    if is_shared is not None:
        recipe.is_shared = is_shared
    db.commit()
    db.refresh(recipe)
    return recipe


def soft_delete(db: Session, recipe: Recipe) -> None:
    recipe.is_deleted = True
    db.commit()


def fork_recipe(db: Session, source: Recipe, new_owner_id: int) -> Recipe:
    """Create a copy of a shared recipe owned by new_owner_id."""
    # Pick the best content to fork: draft first, then latest version
    if source.draft:
        raw_content = source.draft.content
    elif source.versions:
        raw_content = sorted(source.versions, key=lambda v: v.version_number)[-1].content
    else:
        raise ValueError("Source recipe has no content to fork")

    from app.schemas.recipe import RecipeContent, RecipeCreate
    body = RecipeCreate(content=RecipeContent(**raw_content))
    new_recipe = create_recipe(db, new_owner_id, body)

    attribution = f"@{source.owner.username}/{source.slug}"
    new_recipe.forked_from_id = source.id
    new_recipe.forked_from_attribution = attribution
    db.commit()
    db.refresh(new_recipe)
    return new_recipe
