"""
Git integration layer.

Each user gets their own local git repo at data/repos/{user_id}/.
Recipe YAML files live at recipes/{slug}.yaml within that repo.
On Save Version: write YAML → local commit (synchronous).
GitHub push: best-effort, runs as a background task.
"""

import logging
import os
from pathlib import Path
from urllib.parse import urlparse

import git as gitpython
import yaml

log = logging.getLogger(__name__)

_REPOS_BASE = Path(os.getenv("REPOS_BASE_DIR", "data/repos"))
_BOT_ACTOR = gitpython.Actor("Cookbook App", "cookbook@app.local")


# ── Internal helpers ──────────────────────────────────────────────────────────

def _repo_path(user_id: int) -> Path:
    return _REPOS_BASE / str(user_id)


def _ensure_repo(user_id: int) -> gitpython.Repo:
    """Return the user's local git repo, initialising it on first call."""
    path = _repo_path(user_id)
    path.mkdir(parents=True, exist_ok=True)
    (path / "recipes").mkdir(exist_ok=True)

    if (path / ".git").exists():
        return gitpython.Repo(path)

    repo = gitpython.Repo.init(path)
    readme = path / "README.md"
    readme.write_text("# My Cookbook\n\nManaged by Cookbook App.\n", encoding="utf-8")
    repo.index.add(["README.md"])
    repo.index.commit("Initial commit", author=_BOT_ACTOR, committer=_BOT_ACTOR)
    return repo


def _relative(slug: str) -> str:
    return f"recipes/{slug}.yaml"


# ── Public API ────────────────────────────────────────────────────────────────

def content_to_yaml(content: dict) -> str:
    """Serialise a recipe content dict to a human-readable YAML string."""
    return yaml.dump(content, allow_unicode=True, sort_keys=False, default_flow_style=False)


def commit_recipe(
    user_id: int,
    slug: str,
    content: dict,
    version_number: int,
) -> str:
    """Write the recipe YAML and create a local git commit. Returns the commit hash."""
    repo = _ensure_repo(user_id)
    recipe_file = _repo_path(user_id) / _relative(slug)
    recipe_file.write_text(content_to_yaml(content), encoding="utf-8")

    repo.index.add([_relative(slug)])
    title = content.get("title", slug)
    commit = repo.index.commit(
        f"v{version_number}: {title}",
        author=_BOT_ACTOR,
        committer=_BOT_ACTOR,
    )
    return commit.hexsha


def delete_recipe(user_id: int, slug: str) -> str | None:
    """Remove the recipe YAML from git and commit. Returns hash or None."""
    path = _repo_path(user_id)
    recipe_file = path / _relative(slug)
    if not recipe_file.exists():
        return None

    repo = gitpython.Repo(path)
    repo.index.remove([_relative(slug)])
    commit = repo.index.commit(
        f"Delete recipe: {slug}",
        author=_BOT_ACTOR,
        committer=_BOT_ACTOR,
    )
    return commit.hexsha


def push_to_github(user_id: int, repo_url: str, github_token: str) -> bool:
    """
    Push local commits to GitHub using a Personal Access Token.
    Returns True on success, False on any error.

    The PAT is injected into the URL as:
      https://x-access-token:{token}@github.com/{user}/{repo}
    This avoids storing credentials in git config.
    """
    try:
        repo = gitpython.Repo(_repo_path(user_id))

        # Strip trailing .git and trailing slash for consistency
        clean_url = repo_url.rstrip("/").removesuffix(".git")
        parsed = urlparse(clean_url)
        auth_url = f"https://x-access-token:{github_token}@{parsed.netloc}{parsed.path}.git"

        if "origin" in [r.name for r in repo.remotes]:
            repo.remote("origin").set_url(auth_url)
        else:
            repo.create_remote("origin", auth_url)

        repo.remote("origin").push(refspec="HEAD:refs/heads/main", set_upstream=True)
        return True
    except Exception as exc:
        log.warning("GitHub push failed for user %s: %s", user_id, exc)
        return False


# ── Diff ──────────────────────────────────────────────────────────────────────

def compute_diff(content_a: dict, content_b: dict) -> dict:
    """
    Compare two recipe content dicts and return a structured diff dict
    matching the DiffOut schema.
    """
    metadata_changes: dict = {}
    for field in ("title", "description", "servings", "prep_time", "cook_time", "notes"):
        va, vb = content_a.get(field), content_b.get(field)
        if va != vb:
            metadata_changes[field] = {"from_": va, "to": vb}

    # Ingredients — keyed by name
    ings_a: dict = {i["name"]: i for i in content_a.get("ingredients", [])}
    ings_b: dict = {i["name"]: i for i in content_b.get("ingredients", [])}

    added = [i for name, i in ings_b.items() if name not in ings_a]
    removed = [i for name, i in ings_a.items() if name not in ings_b]
    changed = [
        {"name": name, "from_": ings_a[name], "to": ing}
        for name, ing in ings_b.items()
        if name in ings_a and ings_a[name] != ing
    ]

    # Steps — simple set-based diff (order-insensitive)
    steps_a_set = set(content_a.get("steps", []))
    steps_b_set = set(content_b.get("steps", []))
    steps_diff = {
        "added": [s for s in content_b.get("steps", []) if s not in steps_a_set],
        "removed": [s for s in content_a.get("steps", []) if s not in steps_b_set],
    }

    preps_a_set = set(content_a.get("preparations", []))
    preps_b_set = set(content_b.get("preparations", []))
    preps_diff = {
        "added": [s for s in content_b.get("preparations", []) if s not in preps_a_set],
        "removed": [s for s in content_a.get("preparations", []) if s not in preps_b_set],
    }

    return {
        "metadata_changes": metadata_changes,
        "ingredients": {"added": added, "removed": removed, "changed": changed},
        "steps": steps_diff,
        "preparations": preps_diff,
    }
