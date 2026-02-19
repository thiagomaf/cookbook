from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.crud.recipe import get_tags
from app.models.user import User
from app.schemas.recipe import TagOut

router = APIRouter()


@router.get("/", response_model=list[TagOut])
def list_tags(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return get_tags(db, current_user.id)
