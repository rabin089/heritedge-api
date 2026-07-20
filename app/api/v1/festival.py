from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from fastapi.responses import JSONResponse
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
from app.schemas.admin_detail import (
    AdminFestivalListResponse, AdminFestivalDetail, AdminUserDetail
)
from app.crud import contributions as contrib_crud
from app.schemas.contribution import ContributionCreate, ContributionOut
from app.models.contribution import ContributionType

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
    latitude: Optional[float] = Query(None, ge=-90, le=90, description="Current latitude for nearby search"),
    longitude: Optional[float] = Query(None, ge=-180, le=180, description="Current longitude for nearby search"),
    radius_km: Optional[float] = Query(None, gt=0, description="Maximum distance in kilometers"),
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
        q=q,
        latitude=latitude,
        longitude=longitude,
        radius_km=radius_km
    )
    
    return FestivalListResponse(
        items=festivals,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/festivals/calendar", response_model=List[FestivalOut])
def get_festival_calendar(
    year: Optional[int] = Query(None, description="Year to fetch festivals for"),
    month: Optional[int] = Query(None, ge=1, le=12, description="Month to fetch festivals for (1-12)"),
    db: Session = Depends(get_db)
):
    """
    Get all approved festivals suitable for rendering in a global calendar.
    Can be optionally filtered by year and month.
    """
    return festival_crud.get_calendar_festivals(db, year=year, month=month)


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
@router.post("/festivals", response_model=FestivalOut, responses={202: {"model": ContributionOut}})
def create_festival(
    festival_in: FestivalCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Submit a festival.
    - **Admin/Superadmin**: Festival is created directly and marked as approved.
    - **Regular user**: Festival is queued as a pending Contribution. It will
      appear in the Admin review list under GET /admin/contributions/pending
      (type=festival). Once approved, it will be published to the festivals table.
    """
    # Admin: create directly and mark approved
    if is_admin(current_user):
        festival = festival_crud.create(db, festival_in, str(current_user.id), status=FestivalStatus.approved)
        return festival

    # Regular user: go through contribution review queue
    contrib_payload = ContributionCreate(
        type=ContributionType.festival,
        name=festival_in.name,
        description=festival_in.description,
        category=festival_in.category.value if festival_in.category else None,
        region=festival_in.region,
        start_date=festival_in.start_date,
        end_date=festival_in.end_date,
        significance=festival_in.significance,
        nepali_date=festival_in.nepali_date,
        is_annual=festival_in.is_annual,
        image_url=festival_in.main_image,
        secondary_images=festival_in.gallery,
        tags=festival_in.tags,
        latitude=festival_in.latitude if festival_in.latitude is not None else (festival_in.locations[0].lat if festival_in.locations else None),
        longitude=festival_in.longitude if festival_in.longitude is not None else (festival_in.locations[0].lng if festival_in.locations else None),
        location=festival_in.location_name,
        contributor_name=current_user.display_name or current_user.name,
        contributor_email=current_user.email,
    )
    contrib = contrib_crud.create_contribution(db, contrib_payload, user_id=current_user.email)

    # Return a 202 Accepted with the contribution details so the frontend knows
    # the festival is under review, not yet published.
    return JSONResponse(
        status_code=202,
        content={
            "message": "Festival submitted for review. It will be published once an admin approves it.",
            "contribution_id": str(contrib.id),
            "status": contrib.status,
            "type": contrib.type,
        }
    )


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
@router.get("/admin/festivals", response_model=AdminFestivalListResponse)
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
    """Admin endpoint to list all festivals with full metadata and creator details"""
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
    
    admin_items = []
    for fest in festivals:
        item = AdminFestivalDetail.model_validate(fest)
        if fest.user:
            item.creator_details = AdminUserDetail.model_validate(fest.user)
        # Assuming story_count and reaction_count properties don't exist by default in model,
        # fallback to 0 or calculate if needed, but for list view this is enough
        admin_items.append(item)
    
    return AdminFestivalListResponse(
        items=admin_items,
        total=total,
        page=page,
        page_size=page_size
    )


@router.post("/admin/festivals/{festival_id}/approve")
def approve_festival(
    festival_id: UUID,
    approval: Optional[FestivalApproval] = Body(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Approve or reject a festival (Admin only). Body is optional — no body = approve."""
    if not is_admin(current_user):
        raise HTTPException(status_code=403, detail="Admin or Super Admin only")
    
    # Default to approve if no body is sent
    if approval is None:
        approval = FestivalApproval()  # uses defaults: is_approved=True, status=approved

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


@router.post("/festivals/{festival_id}/view")
def increment_festival_views(
    festival_id: UUID,
    db: Session = Depends(get_db),
):
    """Increment the view count for a festival"""
    festival = festival_crud.get(db, festival_id)
    if not festival:
        raise HTTPException(status_code=404, detail="Festival not found")
    
    festival.views_count += 1
    db.commit()
    return {"message": "View count incremented", "views_count": festival.views_count}
