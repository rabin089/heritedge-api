from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.v1.auth import get_current_user
from app.models.user import User
from app.schemas.user_settings import UserSettingsOut, UserSettingsUpdate
from app.crud import user_settings as crud

router = APIRouter(prefix="/me/settings", tags=["user-settings"])

@router.get("", response_model=UserSettingsOut)
def get_settings(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Get the current user's settings."""
    return crud.get_user_settings(db, current_user.email)

@router.patch("", response_model=UserSettingsOut)
def update_settings(
    settings_in: UserSettingsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update the current user's settings."""
    return crud.update_user_settings(db, current_user.email, settings_in)
