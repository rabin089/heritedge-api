from fastapi import APIRouter, Depends, HTTPException, Body
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
