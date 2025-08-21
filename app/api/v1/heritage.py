from fastapi import APIRouter, Depends, HTTPException
from typing import Optional, List
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.schemas.heritage_site import HeritageSiteCreate, HeritageSiteOut
from app.crud import heritage_site as crud
from app.api.v1.auth import get_current_user
from app.models.user import User
from ._role import is_admin  # or define locally

router = APIRouter(prefix="/heritage-sites", tags=["heritage-sites"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# PUBLIC: list all approved sites with filters
@router.get("", response_model=List[HeritageSiteOut])
def get_sites(
    region: Optional[str] = None,
    category: Optional[str] = None,
    tag: Optional[str] = None,
    db: Session = Depends(get_db),
):
    return crud.get_filtered_sites(db, region, category, tag)


# ADMIN: secured list with filters (same as public but requires admin)
@router.get("/secured", response_model=List[HeritageSiteOut])
def get_sites_secured(
    region: Optional[str] = None,
    category: Optional[str] = None,
    tag: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not is_admin(current_user):
        raise HTTPException(status_code=403, detail="Admin only")
    return crud.get_filtered_sites(db, region, category, tag)


# PUBLIC: get by id
@router.get("/{site_id}", response_model=HeritageSiteOut)
def get_site_by_id(
    site_id: int,
    db: Session = Depends(get_db),
):
    site = crud.get_site_by_id(db, site_id)
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    return site


# PUBLIC: get by public UUID (opaque id)
@router.get("/by-public/{public_id}", response_model=HeritageSiteOut)
def get_site_by_public_id(
    public_id: str,
    db: Session = Depends(get_db),
):
    site = crud.get_site_by_public_id(db, public_id)
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    return site


# ADMIN: update site
@router.put("/{site_id}", response_model=HeritageSiteOut)
def update_site(
    site_id: int,
    site_data: HeritageSiteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not is_admin(current_user):
        raise HTTPException(status_code=403, detail="Admin only")
    site = crud.update_heritage_site(db, site_id, site_data)
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    return site


# ADMIN: delete site
@router.delete("/{site_id}")
def delete_site(
    site_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not is_admin(current_user):
        raise HTTPException(status_code=403, detail="Admin only")
    site = crud.delete_site(db, site_id)
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    return {"message": "Heritage site deleted successfully."}
