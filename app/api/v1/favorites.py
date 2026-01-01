from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.database import SessionLocal
from app.schemas.heritage_site import HeritageSiteOut
from app.crud import favorites as crud
from app.api.v1.auth import get_current_user
from app.models.user import User
from uuid import UUID

router = APIRouter(prefix="/favorites", tags=["favorites"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/{site_id}")
def add_favorite(site_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    ok = crud.add_favorite(db, current_user.id, site_id)
    if not ok:
        raise HTTPException(status_code=400, detail="Failed to add favorite")
    return {"message": "Added to favorites"}


@router.delete("/{site_id}")
def remove_favorite(site_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    ok = crud.remove_favorite(db, current_user.id, site_id)
    if not ok:
        raise HTTPException(status_code=400, detail="Failed to remove favorite")
    return {"message": "Removed from favorites"}


@router.get("", response_model=List[HeritageSiteOut])
def list_favorites(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return crud.list_favorites(db, current_user.id)
