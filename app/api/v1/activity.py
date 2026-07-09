from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from sqlalchemy.orm import Session
import uuid

from app.core.database import get_db
from app.api.v1.auth import get_current_user
from app.schemas.activity import ActivityCreate, ActivityResponse
from app.services.activity_service import record_activity

router = APIRouter(prefix="/activity", tags=["activity"])

@router.post("/", response_model=ActivityResponse, status_code=status.HTTP_201_CREATED)
def create_activity(
    activity_in: ActivityCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Record user interaction with a heritage item (site, festival, intangible).
    Usually called for 'view', 'share', 'search' events directly from the frontend.
    """
    activity = record_activity(
        db=db,
        user_id=current_user.id,
        item_id=activity_in.item_id,
        item_type=activity_in.item_type,
        action_type=activity_in.action_type,
        background_tasks=background_tasks
    )
    return activity
