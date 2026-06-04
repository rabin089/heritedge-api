from fastapi import APIRouter, Depends, HTTPException, Body, status
from typing import List
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.api.v1.auth import get_current_user
from app.models.user import User
from app.schemas.notification import NotificationOut
from app.crud import notifications as crud

router = APIRouter(prefix="/notifications", tags=["notifications"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("", response_model=List[NotificationOut])
def list_my_notifications(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return crud.list_my_notifications(db, current_user.email)


@router.post("/read")
def mark_read(
    ids: List[int] = Body(..., embed=True),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    updated = crud.mark_read(db, current_user.email, ids)
    return {"updated": updated}


@router.get("/unread-count")
def unread_count(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    count = crud.count_unread(db, current_user.email)
    return {"count": count}


@router.post("/read-all")
def mark_all_read(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    updated = crud.mark_all_read(db, current_user.email)
    return {"updated": updated}


@router.post("/test-push")
def test_push_notification(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    from app.models.user_settings import UserSettings
    from app.models.user_device import UserDevice
    from app.services.notification_service import notify_user, send_multicast_notification

    # 1. Check if user settings has notifications enabled (defaults to True if not present)
    settings = db.query(UserSettings).filter(UserSettings.user_email == current_user.email).first()
    if settings and not settings.push_notifications_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Push notifications are disabled in your user settings."
        )

    # 1. Find all active device tokens for users whose notifications are enabled
    tokens_query = (
        db.query(UserDevice.fcm_token)
        .join(UserSettings, UserSettings.user_email == UserDevice.user_email)
        .filter(UserSettings.push_notifications_enabled == True, UserDevice.is_active == True)
    )
    tokens = [t[0] for t in tokens_query.all()]
    if not tokens:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active device tokens found for any user with notifications enabled."
        )

    # 2. Send the multicast notification
    result = send_multicast_notification(
        tokens=tokens,
        title="Test Broadcast Notification",
        body="This is a test broadcast notification sent to all enabled users.",
        data={"type": "test_broadcast"}
    )
    if result.get("success", 0) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to send broadcast notification via Firebase."
        )
    return {"message": "Test broadcast notification sent.", "result": result}
