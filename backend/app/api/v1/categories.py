from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.crud.recipe import get_categories
from app.models.user import User
from app.schemas.recipe import CategoryOut

router = APIRouter()


@router.get("/", response_model=list[CategoryOut])
def list_categories(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return get_categories(db, current_user.id)
