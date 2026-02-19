from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.security import encrypt_secret
from app.models.user import User
from app.schemas.user import UserPublic, UserUpdate

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
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
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
    return _to_public(current_user)
