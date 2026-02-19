import logging

from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.security import encrypt_secret
from app.models.user import User
from app.schemas.user import UserPublic, UserUpdate

log = logging.getLogger(__name__)
router = APIRouter()


def _to_public(user: User) -> UserPublic:
    return UserPublic(
        id=user.id,
        username=user.username,
        email=user.email,
        github_repo_url=user.github_repo_url,
        tweak_percentage=user.tweak_percentage,
        has_github_token=user.github_token_encrypted is not None,
        created_at=user.created_at,
    )


@router.get("/me", response_model=UserPublic)
def get_me(current_user: User = Depends(get_current_user)):
    return _to_public(current_user)


@router.patch("/me", response_model=UserPublic)
def update_me(
    update: UserUpdate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    old_repo_url = current_user.github_repo_url

    if update.email is not None:
        current_user.email = update.email
    if update.github_repo_url is not None:
        current_user.github_repo_url = update.github_repo_url or None
    if update.github_token is not None:
        current_user.github_token_encrypted = (
            encrypt_secret(update.github_token) if update.github_token else None
        )
    if update.tweak_percentage is not None:
        current_user.tweak_percentage = update.tweak_percentage

    db.commit()
    db.refresh(current_user)

    # Trigger import when the repo URL changes or a token is newly added,
    # as long as both repo URL and token are now configured.
    repo_url_changed = current_user.github_repo_url != old_repo_url
    token_just_added = bool(update.github_token and current_user.github_token_encrypted)
    should_sync = (repo_url_changed or token_just_added) and bool(
        current_user.github_repo_url and current_user.github_token_encrypted
    )

    if should_sync:
        background_tasks.add_task(
            _background_sync,
            current_user.id,
            current_user.github_repo_url,
            current_user.github_token_encrypted,
        )

    return _to_public(current_user)


def _background_sync(user_id: int, repo_url: str, encrypted_token: str) -> None:
    """Run sync in a background task with its own DB session."""
    from app.core.sync import sync_from_github
    from app.database import SessionLocal

    db = SessionLocal()
    try:
        result = sync_from_github(db, user_id, repo_url, encrypted_token)
        if result.error:
            log.warning("Background sync failed for user %s: %s", user_id, result.error)
        else:
            log.info(
                "Background sync for user %s: imported=%d, skipped=%d, failed=%d",
                user_id,
                len(result.imported),
                len(result.skipped),
                len(result.failed),
            )
    except Exception:
        log.exception("Background sync crashed for user %s", user_id)
    finally:
        db.close()
