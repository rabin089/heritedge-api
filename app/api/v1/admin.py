from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timezone
from uuid import UUID

from app.core.database import SessionLocal
from app.api.v1.auth import get_current_user
from app.models.user import User
from app.core.security import hash_password
from app.schemas.users import UserOut, AdminCreate, RoleUpdate
from ._role import is_superadmin, is_admin, is_reviewer
from app.schemas.contribution import ContributionOut
from app.models.contribution import ContributionStatus
from app.crud import contributions as contrib_crud
from app.crud import heritage_site as heritage_crud
from app.schemas.heritage_site import HeritageSiteCreate, HeritageSiteOut
from app.schemas.site_review import (
    AdminReviewUpdate, AdminRatingUpdate, AdminAuditInfo,
    AdminReviewUpdateResponse, AdminRatingUpdateResponse,
    AdminReviewStats, AdminReviewList, AdminRatingList,
    SiteReviewOut, SiteRatingOut
)
from app.crud import site_review as review_crud

router = APIRouter(prefix="/admin", tags=["admin"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# SUPERADMIN: list all users
@router.get("/users", response_model=List[UserOut])
def list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not is_superadmin(current_user):
        raise HTTPException(status_code=403, detail="Superadmin only")
    return db.query(User).order_by(User.id.asc()).all()


# SUPERADMIN: create user with role
@router.post("/users", response_model=UserOut)
def create_user(
    payload: AdminCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not is_superadmin(current_user):
        raise HTTPException(status_code=403, detail="Superadmin only")
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=400, detail="Email already exists")
    user = User(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        is_active=True,
        is_admin=(payload.role in {"admin", "superadmin"}),
        role=payload.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


# SUPERADMIN: update a user's role
@router.put("/users/{user_id}/role", response_model=UserOut)
def update_role(
    user_id: str,  # Changed from int to str to accept UUID
    payload: RoleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not is_superadmin(current_user):
        raise HTTPException(status_code=403, detail="Superadmin only")
    
    # Convert string to UUID for database query
    try:
        from uuid import UUID
        user_uuid = UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID format")
    
    user = db.query(User).filter(User.id == user_uuid).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.role = payload.role
    user.is_admin = payload.role in {"admin", "superadmin"}
    db.commit()
    db.refresh(user)
    return user


# SUPERADMIN: delete user
@router.delete("/users/{user_id}")
def delete_user(
    user_id: str,  # Changed from int to str to accept UUID
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not is_superadmin(current_user):
        raise HTTPException(status_code=403, detail="Superadmin only")
    
    # Convert string to UUID for database query
    try:
        from uuid import UUID
        user_uuid = UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID format")
    
    user = db.query(User).filter(User.id == user_uuid).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(user)
    db.commit()
    return {"message": "User deleted"}


# ADMIN/REVIEWER: list pending contributions with filters + pagination
@router.get("/contributions/pending")
def list_pending_contributions(
    region: Optional[str] = Query(default=None),
    category: Optional[str] = Query(default=None),
    q: Optional[str] = Query(default=None, description="Fuzzy search over name/region/description/tags"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not (is_admin(current_user) or is_reviewer(current_user)):
        raise HTTPException(status_code=403, detail="Admin or reviewer only")
    items, total = contrib_crud.admin_list_pending_contributions(db, region, category, q, page, page_size)
    # Use ContributionOut for items via FastAPI's response model conversion
    return {
        "items": [ContributionOut.model_validate(i) for i in items],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


# ADMIN/REVIEWER: user contribution history with optional status filter + pagination
@router.get("/user/{user_id}/contributions")
def user_contribution_history(
    user_id: str,  
    status: Optional[ContributionStatus] = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not (is_admin(current_user) or is_reviewer(current_user)):
        raise HTTPException(status_code=403, detail="Admin or reviewer only")
    
    # Convert string to UUID for database query
    try:
        from uuid import UUID
        user_uuid = UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID format")
    
    u = db.query(User).filter(User.id == user_uuid).first()
    if not u:
        raise HTTPException(status_code=404, detail="User not found")
    items, total = contrib_crud.admin_user_contribution_history(db, u.email, page, page_size, status)
    return {
        "user_id": u.id,
        "user_email": u.email,
        "user_name": u.display_name,  # Use display_name for admin identity
        "items": [ContributionOut.model_validate(i) for i in items],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


# ADMIN: create heritage site directly (no approval needed)
@router.post("/heritage-sites", response_model=HeritageSiteOut)
def create_heritage_site_direct(
    site_data: HeritageSiteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a heritage site directly without going through contribution approval process.
    Only admins can use this endpoint for adding popular/official sites."""
    if not is_admin(current_user):
        raise HTTPException(status_code=403, detail="Admin only")
    
    # Create heritage site directly as approved (not pending)
    site = heritage_crud.create_heritage_site(
        db=db,
        site_data=site_data,
        user_id=current_user.email,  # Use admin's email as creator
        contribution_id=None  # No contribution since it's direct creation
    )
    
    # Set audit fields for direct admin creation
    site.approved_by = current_user.email
    site.approved_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(site)
    
    return site


# ==================== ADMIN REVIEW MANAGEMENT ====================

# ADMIN: Delete any review
@router.delete("/reviews/{review_id}", response_model=AdminAuditInfo)
def admin_delete_review(
    review_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Admin can delete any review with audit trail"""
    if not is_admin(current_user):
        raise HTTPException(status_code=403, detail="Admin only")
    
    result = review_crud.admin_delete_review(db, review_id, current_user.email)
    if not result:
        raise HTTPException(status_code=404, detail="Review not found")
    
    return AdminAuditInfo(**result)


# ADMIN: Update any review
@router.put("/reviews/{review_id}", response_model=AdminReviewUpdateResponse)
def admin_update_review(
    review_id: UUID,
    review_data: AdminReviewUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Admin can update any review with audit trail"""
    if not is_admin(current_user):
        raise HTTPException(status_code=403, detail="Admin only")
    
    result = review_crud.admin_update_review(db, review_id, review_data, current_user.email)
    if not result:
        raise HTTPException(status_code=404, detail="Review not found")
    
    review, original_values = result
    return AdminReviewUpdateResponse(
        review=SiteReviewOut.model_validate(review),
        original_values=original_values
    )


# ADMIN: Delete any rating
@router.delete("/ratings/{rating_id}", response_model=AdminAuditInfo)
def admin_delete_rating(
    rating_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Admin can delete any rating with audit trail"""
    if not is_admin(current_user):
        raise HTTPException(status_code=403, detail="Admin only")
    
    result = review_crud.admin_delete_rating(db, rating_id, current_user.email)
    if not result:
        raise HTTPException(status_code=404, detail="Rating not found")
    
    return AdminAuditInfo(**result)


# ADMIN: Update any rating
@router.put("/ratings/{rating_id}", response_model=AdminRatingUpdateResponse)
def admin_update_rating(
    rating_id: UUID,
    rating_data: AdminRatingUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Admin can update any rating with audit trail"""
    if not is_admin(current_user):
        raise HTTPException(status_code=403, detail="Admin only")
    
    result = review_crud.admin_update_rating(db, rating_id, rating_data.rating, current_user.email)
    if not result:
        raise HTTPException(status_code=404, detail="Rating not found")
    
    rating, original_value = result
    return AdminRatingUpdateResponse(
        rating=SiteRatingOut.model_validate(rating),
        original_value=original_value
    )


# ADMIN: Get all reviews with filters
@router.get("/reviews", response_model=AdminReviewList)
def admin_get_all_reviews(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    site_id: Optional[UUID] = Query(None),
    user_email: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Admin can get all reviews with optional filters"""
    if not is_admin(current_user):
        raise HTTPException(status_code=403, detail="Admin only")
    
    result = review_crud.admin_get_all_reviews(db, page, page_size, site_id, user_email)
    if not result:
        raise HTTPException(status_code=500, detail="Failed to retrieve reviews")
    
    reviews, total = result
    return AdminReviewList(
        reviews=[SiteReviewOut.model_validate(review) for review in reviews],
        total=total,
        page=page,
        page_size=page_size
    )


# ADMIN: Get all ratings with filters
@router.get("/ratings", response_model=AdminRatingList)
def admin_get_all_ratings(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    site_id: Optional[UUID] = Query(None),
    user_email: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Admin can get all ratings with optional filters"""
    if not is_admin(current_user):
        raise HTTPException(status_code=403, detail="Admin only")
    
    result = review_crud.admin_get_all_ratings(db, page, page_size, site_id, user_email)
    if not result:
        raise HTTPException(status_code=500, detail="Failed to retrieve ratings")
    
    ratings, total = result
    return AdminRatingList(
        ratings=[SiteRatingOut.model_validate(rating) for rating in ratings],
        total=total,
        page=page,
        page_size=page_size
    )


# ADMIN: Get comprehensive review statistics
@router.get("/reviews/stats", response_model=AdminReviewStats)
def admin_get_review_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Admin can get comprehensive review statistics"""
    if not is_admin(current_user):
        raise HTTPException(status_code=403, detail="Admin only")
    
    stats = review_crud.admin_get_review_stats(db)
    if not stats:
        raise HTTPException(status_code=500, detail="Failed to retrieve statistics")
    
    return AdminReviewStats(**stats)


# ADMIN: Get user's review history
@router.get("/users/{user_email}/reviews", response_model=AdminReviewList)
def admin_get_user_reviews(
    user_email: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Admin can get any user's review history"""
    if not is_admin(current_user):
        raise HTTPException(status_code=403, detail="Admin only")
    
    result = review_crud.admin_get_all_reviews(db, page, page_size, user_email=user_email)
    if not result:
        raise HTTPException(status_code=500, detail="Failed to retrieve user reviews")
    
    reviews, total = result
    return AdminReviewList(
        reviews=[SiteReviewOut.model_validate(review) for review in reviews],
        total=total,
        page=page,
        page_size=page_size
    )


# ADMIN: Get user's rating history
@router.get("/users/{user_email}/ratings", response_model=AdminRatingList)
def admin_get_user_ratings(
    user_email: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Admin can get any user's rating history"""
    if not is_admin(current_user):
        raise HTTPException(status_code=403, detail="Admin only")
    
    result = review_crud.admin_get_all_ratings(db, page, page_size, user_email=user_email)
    if not result:
        raise HTTPException(status_code=500, detail="Failed to retrieve user ratings")
    
    ratings, total = result
    return AdminRatingList(
        ratings=[SiteRatingOut.model_validate(rating) for rating in ratings],
        total=total,
        page=page,
        page_size=page_size
    )
