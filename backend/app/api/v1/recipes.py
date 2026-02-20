import logging

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core import git as git_svc
from app.core.security import decrypt_secret
from app.crud import recipe as crud
from app.models.recipe import Recipe, RecipeVersion
from app.models.user import User
from app.schemas.diff import DiffOut
from app.schemas.recipe import (
    RateVersion,
    RecipeContent,
    RecipeCreate,
    RecipeDetailOut,
    RecipeDraftUpdate,
    RecipeMetaUpdate,
    RecipeOut,
    RecipeSaveVersion,
    RecipeVersionDetail,
    RecipeVersionOut,
)

log = logging.getLogger(__name__)
router = APIRouter()


# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_readable_or_404(db: Session, recipe_id: int, user: User) -> Recipe:
    r = crud.get_recipe(db, recipe_id, user.id)
    if not r:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return r


def _get_own_or_404(db: Session, recipe_id: int, user: User) -> Recipe:
    r = crud.get_own_recipe(db, recipe_id, user.id)
    if not r:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return r


def _build_detail(recipe: Recipe) -> RecipeDetailOut:
    versions = sorted(recipe.versions, key=lambda v: v.version_number)
    latest = versions[-1] if versions else None
    draft_content = RecipeContent(**recipe.draft.content) if recipe.draft else None
    return RecipeDetailOut(
        id=recipe.id,
        slug=recipe.slug,
        title=recipe.title,
        owner_id=recipe.owner_id,
        owner_username=recipe.owner.username,
        is_shared=recipe.is_shared,
        has_draft=recipe.has_draft,
        forked_from_attribution=recipe.forked_from_attribution,
        created_at=recipe.created_at,
        updated_at=recipe.updated_at,
        draft_content=draft_content,
        latest_version=RecipeVersionOut.model_validate(latest) if latest else None,
        versions=[RecipeVersionOut.model_validate(v) for v in versions],
    )


async def _push_background(
    version_id: int,
    user_id: int,
    repo_url: str,
    encrypted_token: str,
    db: Session,
) -> None:
    try:
        token = decrypt_secret(encrypted_token)
        success = git_svc.push_to_github(user_id, repo_url, token)
        crud.update_version_after_commit(db, version_id, None, "pushed" if success else "failed")
    except Exception as exc:
        log.warning("Push background task failed: %s", exc)
        crud.update_version_after_commit(db, version_id, None, "failed")


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/", response_model=list[RecipeDetailOut])
def list_recipes(
    search: str | None = Query(default=None),
    category: str | None = Query(default=None),
    tag: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    items, _ = crud.list_recipes(db, current_user.id, search, category, tag, page, limit)
    return [_build_detail(r) for r in items]


@router.get("/shared", response_model=list[RecipeDetailOut])
def list_shared_recipes(
    search: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    items, _ = crud.list_shared(db, current_user.id, search, page, limit)
    return [_build_detail(r) for r in items]


@router.post("/", response_model=RecipeDetailOut, status_code=status.HTTP_201_CREATED)
def create_recipe(
    body: RecipeCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    recipe = crud.create_recipe(db, current_user.id, body)
    return _build_detail(recipe)


@router.get("/{recipe_id}", response_model=RecipeDetailOut)
def get_recipe(
    recipe_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return _build_detail(_get_readable_or_404(db, recipe_id, current_user))


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


@router.delete("/{recipe_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_recipe(
    recipe_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    recipe = _get_own_or_404(db, recipe_id, current_user)
    crud.soft_delete(db, recipe)
    # Best-effort: also remove from local git repo
    try:
        git_svc.delete_recipe(current_user.id, recipe.slug)
    except Exception:
        pass


@router.patch("/{recipe_id}/draft", response_model=RecipeDetailOut)
def update_draft(
    recipe_id: int,
    body: RecipeDraftUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    recipe = _get_own_or_404(db, recipe_id, current_user)
    crud.update_draft(db, recipe, body)
    db.refresh(recipe)
    return _build_detail(recipe)


@router.post("/{recipe_id}/versions", response_model=RecipeVersionOut)
def save_version(
    recipe_id: int,
    body: RecipeSaveVersion,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    recipe = _get_own_or_404(db, recipe_id, current_user)
    version = crud.save_version(db, recipe, body)

    # Local git commit (synchronous — failure must not break the save)
    try:
        commit_hash = git_svc.commit_recipe(
            user_id=current_user.id,
            slug=recipe.slug,
            content=body.content.model_dump(),
            version_number=version.version_number,
        )
        crud.update_version_after_commit(db, version.id, commit_hash, "pending")
    except Exception as exc:
        log.warning("Local git commit failed for recipe %s: %s", recipe.slug, exc)

    # Async GitHub push
    if current_user.github_repo_url and current_user.github_token_encrypted:
        background_tasks.add_task(
            _push_background,
            version.id,
            current_user.id,
            current_user.github_repo_url,
            current_user.github_token_encrypted,
            db,
        )

    db.refresh(version)
    return RecipeVersionOut.model_validate(version)


@router.get("/{recipe_id}/versions/{version_number}", response_model=RecipeVersionDetail)
def get_version(
    recipe_id: int,
    version_number: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _get_readable_or_404(db, recipe_id, current_user)
    v = crud.get_version(db, recipe_id, version_number)
    if not v:
        raise HTTPException(status_code=404, detail="Version not found")
    return RecipeVersionDetail(
        id=v.id,
        version_number=v.version_number,
        rating=v.rating,
        commit_hash=v.commit_hash,
        push_status=v.push_status,
        created_at=v.created_at,
        content=RecipeContent(**v.content),
    )


@router.patch("/{recipe_id}/versions/{version_number}/rating", response_model=RecipeVersionOut)
def rate_version(
    recipe_id: int,
    version_number: int,
    body: RateVersion,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    v = crud.rate_version(db, recipe_id, version_number, current_user.id, body.rating)
    if not v:
        raise HTTPException(status_code=404, detail="Version not found")
    return RecipeVersionOut.model_validate(v)


@router.get("/{recipe_id}/diff", response_model=DiffOut)
def get_diff(
    recipe_id: int,
    v1: int = Query(..., description="First version number"),
    v2: int = Query(..., description="Second version number"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _get_readable_or_404(db, recipe_id, current_user)
    va = crud.get_version(db, recipe_id, v1)
    vb = crud.get_version(db, recipe_id, v2)
    if not va or not vb:
        raise HTTPException(status_code=404, detail="One or both versions not found")

    diff = git_svc.compute_diff(va.content, vb.content)
    return DiffOut(recipe_id=recipe_id, v1=v1, v2=v2, **diff)


@router.post("/{recipe_id}/fork", response_model=RecipeDetailOut, status_code=status.HTTP_201_CREATED)
def fork_recipe(
    recipe_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    source = _get_readable_or_404(db, recipe_id, current_user)
    if not source.is_shared:
        raise HTTPException(status_code=403, detail="Can only fork shared recipes")
    if source.owner_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot fork your own recipe")
    new_recipe = crud.fork_recipe(db, source, current_user.id)
    return _build_detail(new_recipe)
