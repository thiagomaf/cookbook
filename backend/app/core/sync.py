"""
Sync service: clone/pull a user's GitHub repo and import new recipes into the DB.

Only recipes whose slug doesn't already exist in the DB are imported (DB wins).
"""
import logging
from dataclasses import dataclass, field
from pathlib import Path

import yaml
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.core import git as git_svc
from app.core.security import decrypt_secret
from app.crud.recipe import _sync_labels
from app.models.recipe import Recipe, RecipeVersion
from app.schemas.recipe import RecipeContent

log = logging.getLogger(__name__)


@dataclass
class SyncResult:
    imported: list[str] = field(default_factory=list)   # slugs of newly imported recipes
    skipped: list[str] = field(default_factory=list)    # slugs already in DB
    failed: list[dict] = field(default_factory=list)    # {"file": ..., "error": ...}
    error: str | None = None                            # fatal error (clone failed, etc.)

    def to_dict(self) -> dict:
        return {
            "imported": self.imported,
            "skipped": self.skipped,
            "failed": self.failed,
            "error": self.error,
        }


def sync_from_github(
    db: Session,
    user_id: int,
    repo_url: str,
    encrypted_token: str,
) -> SyncResult:
    """
    Clone or pull the user's GitHub repo and import new recipes.
    Returns a SyncResult describing what happened.
    """
    result = SyncResult()

    # Decrypt token
    try:
        token = decrypt_secret(encrypted_token)
    except Exception as exc:
        result.error = f"Token decryption failed: {exc}"
        return result

    # Clone or pull
    try:
        repo = git_svc.clone_or_pull(user_id, repo_url, token)
    except Exception as exc:
        result.error = f"Git clone/pull failed: {exc}"
        return result

    # Enumerate recipes/*.yaml
    recipes_dir = git_svc._repo_path(user_id) / "recipes"
    if not recipes_dir.exists():
        return result

    yaml_files = sorted(recipes_dir.glob("*.yaml"))
    if not yaml_files:
        return result

    # Import each file
    for yaml_file in yaml_files:
        slug = yaml_file.stem  # filename without .yaml
        _import_single_recipe(db, user_id, slug, yaml_file, repo, result)

    db.commit()
    return result


def _import_single_recipe(
    db: Session,
    user_id: int,
    slug: str,
    yaml_file: Path,
    repo,
    result: SyncResult,
) -> None:
    """Parse one YAML file and import it if the recipe doesn't already exist."""
    # Check if recipe already exists for this user (including soft-deleted to avoid constraint clash)
    existing = db.query(Recipe).filter(
        Recipe.owner_id == user_id,
        Recipe.slug == slug,
    ).first()

    if existing:
        result.skipped.append(slug)
        return

    # Parse YAML
    try:
        raw = yaml.safe_load(yaml_file.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            result.failed.append({"file": yaml_file.name, "error": "Not a YAML mapping"})
            return
    except yaml.YAMLError as exc:
        result.failed.append({"file": yaml_file.name, "error": f"YAML parse error: {exc}"})
        return

    # Validate against RecipeContent schema
    try:
        content = RecipeContent(**raw)
    except (ValidationError, Exception) as exc:
        result.failed.append({"file": yaml_file.name, "error": f"Schema validation: {exc}"})
        return

    # Get commit hash for this file from git log
    commit_hash = _get_file_commit_hash(repo, f"recipes/{slug}.yaml")

    # Create Recipe
    recipe = Recipe(
        slug=slug,
        title=content.title,
        owner_id=user_id,
        has_draft=False,
    )
    db.add(recipe)
    db.flush()

    # Create RecipeVersion (version 1, already on GitHub so push_status=pushed)
    version = RecipeVersion(
        recipe_id=recipe.id,
        version_number=1,
        content=content.model_dump(),
        commit_hash=commit_hash,
        push_status="pushed",
    )
    db.add(version)

    # Sync categories and tags
    _sync_labels(db, recipe, content.categories, content.tags, user_id)

    result.imported.append(slug)
    log.info("Imported recipe %r for user %s", slug, user_id)


def _get_file_commit_hash(repo, file_path: str) -> str | None:
    """Get the latest commit hash that touched a specific file."""
    try:
        commits = list(repo.iter_commits(paths=file_path, max_count=1))
        return commits[0].hexsha if commits else None
    except Exception:
        return None
