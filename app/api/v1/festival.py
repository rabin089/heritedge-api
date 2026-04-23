from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from uuid import UUID

from app.core.database import SessionLocal
from app.crud.festival import festival_crud, festival_heritage_site_crud
from app.schemas.festival import (
    FestivalCreate, FestivalUpdate, FestivalOut,
    FestivalListResponse, FestivalApproval, FestivalHeritageSiteCreate,
    FestivalHeritageSiteOut
)
from app.models.festival import Festival, FestivalStatus, FestivalCategory
from app.api.v1._role import is_admin, is_reviewer
from app.api.v1.auth import get_current_user
from app.models.user import User

router = APIRouter(tags=["festival"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Public endpoints (no authentication required)
@router.get("/festivals", response_model=FestivalListResponse)
def list_festivals(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    region: Optional[str] = Query(None, description="Filter by region"),
    category: Optional[FestivalCategory] = Query(None, description="Filter by category"),
    status: Optional[FestivalStatus] = Query(None, description="Filter by status"),
    tag: Optional[str] = Query(None, description="Filter by tag"),
    q: Optional[str] = Query(None, description="Search query"),
    db: Session = Depends(get_db)
):
    """List public approved festivals with filters and pagination"""
    skip = (page - 1) * page_size
    
    # helper to default to approved if no status given for public?
    # Original logic: is_approved=True default.
    # New logic: status=approved default if not specified? 
    # The CRUD handles is_approved legacy param, but better to be explicit.
    
    query_status = status
    if not query_status:
        query_status = FestivalStatus.approved
        
    festivals, total = festival_crud.get_multi(
        db=db,
        skip=skip,
        limit=page_size,
        region=region,
        category=category,
        status=query_status,
        tag=tag,
        q=q
    )
    
    return FestivalListResponse(
        items=festivals,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/festivals/upcoming", response_model=List[FestivalOut])
def list_upcoming_festivals(
    limit: int = Query(10, ge=1, le=50, description="Maximum number of festivals"),
    db: Session = Depends(get_db)
):
    """Get upcoming approved festivals"""
    return festival_crud.get_upcoming_festivals(db, limit=limit)


@router.get("/festivals/ongoing", response_model=List[FestivalOut])
def list_ongoing_festivals(
    db: Session = Depends(get_db)
):
    """Get currently ongoing approved festivals"""
    return festival_crud.get_ongoing_festivals(db)


@router.get("/festivals/{festival_id}", response_model=FestivalOut)
def get_festival(
    festival_id: UUID,
    db: Session = Depends(get_db)
):
    """Get a specific festival by ID"""
    festival = festival_crud.get(db, festival_id)
    if not festival or festival.status != FestivalStatus.approved:
        # If admin, maybe allow? Stick to basic logic first.
        raise HTTPException(status_code=404, detail="Festival not found")
    return festival


# Protected endpoints (authentication required)
@router.post("/festivals", response_model=FestivalOut)
def create_festival(
    festival_in: FestivalCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new festival (requires authentication)"""
    # Auto-approve if created by admin/superadmin
    status = FestivalStatus.pending
    if is_admin(current_user):
        status = FestivalStatus.approved
        
    festival = festival_crud.create(db, festival_in, str(current_user.id), status=status)
    return festival


@router.get("/festivals/me", response_model=FestivalListResponse)
def list_my_festivals(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[FestivalStatus] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List festivals created by the current user"""
    skip = (page - 1) * page_size
    
    festivals, total = festival_crud.get_multi(
        db=db,
        skip=skip,
        limit=page_size,
        status=status,
        created_by=str(current_user.id),
        include_unapproved=True
    )
    
    return FestivalListResponse(
        items=festivals,
        total=total,
        page=page,
        page_size=page_size
    )


@router.put("/festivals/{festival_id}", response_model=FestivalOut)
def update_festival(
    festival_id: UUID,
    festival_in: FestivalUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a festival (only by creator or admin)"""
    festival = festival_crud.get(db, festival_id)
    if not festival:
        raise HTTPException(status_code=404, detail="Festival not found")
    
    # Check if user is creator or admin
    if str(festival.created_by) != str(current_user.id) and current_user.role not in ["admin", "superadmin"]:
        raise HTTPException(status_code=403, detail="Not authorized to update this festival")
    
    return festival_crud.update(db, festival, festival_in, str(current_user.id))


@router.delete("/festivals/{festival_id}")
def delete_festival(
    festival_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a festival (only by creator or admin)"""
    festival = festival_crud.get(db, festival_id)
    if not festival:
        raise HTTPException(status_code=404, detail="Festival not found")
    
    # Check if user is creator or admin
    if str(festival.created_by) != str(current_user.id) and current_user.role not in ["admin", "superadmin"]:
        raise HTTPException(status_code=403, detail="Not authorized to delete this festival")
    
    if festival_crud.delete(db, festival_id):
        return {"message": "Festival deleted successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to delete festival")


# Admin endpoints (admin/superadmin only)
@router.get("/admin/festivals", response_model=FestivalListResponse)
def admin_list_festivals(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    region: Optional[str] = Query(None),
    category: Optional[FestivalCategory] = Query(None),
    status: Optional[FestivalStatus] = Query(None),
    tag: Optional[str] = Query(None),
    q: Optional[str] = Query(None),
    is_approved: Optional[bool] = Query(None), # Legacy
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Admin endpoint to list all festivals"""
    if not is_admin(current_user):
        raise HTTPException(status_code=403, detail="Admin only")
    skip = (page - 1) * page_size
    
    festivals, total = festival_crud.get_multi(
        db=db,
        skip=skip,
        limit=page_size,
        region=region,
        category=category,
        status=status,
        tag=tag,
        q=q,
        is_approved=is_approved,
        include_unapproved=True
    )
    
    return FestivalListResponse(
        items=festivals,
        total=total,
        page=page,
        page_size=page_size
    )


@router.post("/admin/festivals/{festival_id}/approve")
def approve_festival(
    festival_id: UUID,
    approval: FestivalApproval,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Approve or reject a festival (Admin only)"""
    if not is_admin(current_user):
        raise HTTPException(status_code=403, detail="Admin or Super Admin only")
    
    # We use status primarily now, but keep is_approved for legacy
    status = approval.status
    if not status:
        status = FestivalStatus.approved if approval.is_approved else FestivalStatus.rejected
        
    if status == FestivalStatus.approved:
        festival = festival_crud.approve(db, festival_id, str(current_user.id), approval.rejection_reason)
        if festival:
            return {"message": "Festival approved successfully", "festival_id": str(festival_id), "status": "approved"}
    elif status == FestivalStatus.rejected:
        # Rejection reason is mandatory for rejection
        reason = approval.rejection_reason or "Rejected by moderator"
        festival = festival_crud.reject(db, festival_id, str(current_user.id), reason)
        if festival:
            return {"message": "Festival rejected successfully", "festival_id": str(festival_id), "status": "rejected"}
    elif status == FestivalStatus.pending:
         # Optionally set back to pending
         festival = festival_crud.get(db, festival_id)
         if festival:
             festival.status = FestivalStatus.pending
             festival.moderation_note = approval.rejection_reason
             db.commit()
             return {"message": "Festival set to pending", "festival_id": str(festival_id)}
            
    raise HTTPException(status_code=404, detail="Festival not found or invalid status provided")


# Festival-Heritage Site relationship endpoints
@router.post("/festivals/{festival_id}/heritage-sites", response_model=FestivalHeritageSiteOut)
def add_heritage_site_to_festival(
    festival_id: UUID,
    relationship: FestivalHeritageSiteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Associate a heritage site with a festival"""
    # Verify festival exists and user has permission
    festival = festival_crud.get(db, festival_id)
    if not festival:
        raise HTTPException(status_code=404, detail="Festival not found")
    
    if str(festival.created_by) != str(current_user.id) and current_user.role not in ["admin", "superadmin"]:
        raise HTTPException(status_code=403, detail="Not authorized to modify this festival")
    
    relationship.festival_id = festival_id
    return festival_heritage_site_crud.create(db, relationship, str(current_user.id))


@router.get("/festivals/{festival_id}/heritage-sites", response_model=List[FestivalHeritageSiteOut])
def get_festival_heritage_sites(
    festival_id: UUID,
    db: Session = Depends(get_db)
):
    """Get all heritage sites associated with a festival"""
    return festival_heritage_site_crud.get_by_festival(db, festival_id)


@router.delete("/festivals/{festival_id}/heritage-sites/{heritage_site_id}")
def remove_heritage_site_from_festival(
    festival_id: UUID,
    heritage_site_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Remove a heritage site from a festival"""
    # Verify festival exists and user has permission
    festival = festival_crud.get(db, festival_id)
    if not festival:
        raise HTTPException(status_code=404, detail="Festival not found")
    
    if str(festival.created_by) != str(current_user.id) and current_user.role not in ["admin", "superadmin"]:
        raise HTTPException(status_code=403, detail="Not authorized to modify this festival")
    
    if festival_heritage_site_crud.remove(db, festival_id, heritage_site_id):
        return {"message": "Heritage site removed from festival successfully"}
    else:
        raise HTTPException(status_code=404, detail="Festival-heritage site relationship not found")
