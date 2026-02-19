import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.sync import sync_from_github
from app.models.user import User
from app.schemas.sync import SyncResultOut

log = logging.getLogger(__name__)
router = APIRouter()


@router.post("/", response_model=SyncResultOut)
def trigger_sync(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Pull latest from the user's GitHub repo and import new recipes."""
    if not current_user.github_repo_url or not current_user.github_token_encrypted:
        raise HTTPException(
            status_code=400,
            detail="GitHub repo URL and token must be configured before syncing",
        )

    result = sync_from_github(
        db=db,
        user_id=current_user.id,
        repo_url=current_user.github_repo_url,
        encrypted_token=current_user.github_token_encrypted,
    )

    if result.error:
        raise HTTPException(status_code=502, detail=result.error)

    return result.to_dict()
