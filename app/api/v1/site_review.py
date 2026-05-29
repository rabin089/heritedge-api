from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from app.core.database import SessionLocal
from app.schemas.site_review import (
    SiteReviewCreate, SiteReviewUpdate, SiteReviewOut, 
    SiteRatingCreate, SiteRatingOut, SiteReviewStats,
    PopularSite, HeritageSiteWithReviews
)
from app.crud import site_review as crud
from app.api.v1.auth import get_current_user
from app.models.user import User

router = APIRouter(prefix="/heritage-sites", tags=["site-reviews"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# GET /heritage-sites/popular - Get most popular sites
@router.get("/popular", response_model=List[PopularSite])
def get_popular_sites(
    limit: int = Query(10, ge=1, le=50),
    by_reviews: bool = Query(True, description="Order by number of reviews (true) or by rating (false)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get most popular heritage sites by reviews or ratings"""
    sites = crud.get_popular_sites(db, limit, by_reviews)
    return sites


# POST /heritage-sites/{site_id}/reviews - Add a review
@router.post("/{site_id}/reviews", response_model=SiteReviewOut)
def create_site_review(
    site_id: UUID,
    review_data: SiteReviewCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add a review to a heritage site (users cannot review their own contributions)"""
    review_data = SiteReviewCreate(site_id=site_id, **review_data.dict(exclude={"site_id"}))
    try:
        review = crud.create_site_review(db, review_data, current_user.email)
        return review
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# GET /heritage-sites/{site_id}/reviews - Get all reviews for a site
@router.get("/{site_id}/reviews", response_model=List[SiteReviewOut])
def get_site_reviews(
    site_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get all reviews for a heritage site with pagination"""
    reviews, total = crud.get_site_reviews(db, site_id, page, page_size)
    return reviews


# PUT /heritage-sites/reviews/{review_id} - Update own review
@router.put("/reviews/{review_id}", response_model=SiteReviewOut)
def update_site_review(
    review_id: UUID,
    review_data: SiteReviewUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update your own review"""
    review = crud.update_site_review(db, review_id, review_data, current_user.email)
    
    if not review:
        raise HTTPException(
            status_code=404, 
            detail="Review not found or you don't have permission to update it"
        )
    
    return review


# DELETE /heritage-sites/reviews/{review_id} - Delete own review
@router.delete("/reviews/{review_id}")
def delete_site_review(
    review_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete your own review"""
    review = crud.delete_site_review(db, review_id, current_user.email)
    
    if not review:
        raise HTTPException(
            status_code=404, 
            detail="Review not found or you don't have permission to delete it"
        )
    
    return {"message": "Review deleted successfully"}


# POST /heritage-sites/{site_id}/rate - Rate a site (0-10)
@router.post("/{site_id}/rate", response_model=SiteRatingOut)
def rate_site(
    site_id: UUID,
    rating_data: SiteRatingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Rate a heritage site (users cannot rate their own contributions)"""
    rating_data = SiteRatingCreate(site_id=site_id, **rating_data.dict(exclude={"site_id"}))
    try:
        rating = crud.create_site_rating(db, rating_data, current_user.email)
        return rating
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# GET /heritage-sites/{site_id}/stats - Get site review stats
@router.get("/{site_id}/stats", response_model=SiteReviewStats)
def get_site_stats(
    site_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get review and rating statistics for a heritage site"""
    stats = crud.get_site_review_stats(db, site_id, current_user.email)
    return stats


# GET /heritage-sites/{site_id}/with-reviews - Get site with review stats
@router.get("/{site_id}/with-reviews", response_model=HeritageSiteWithReviews)
def get_site_with_reviews(
    site_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get heritage site with review and rating statistics"""
    from app.crud import heritage_site as heritage_crud
    
    site = heritage_crud.get_site_by_id(db, site_id)
    if not site:
        raise HTTPException(status_code=404, detail="Heritage site not found")
    
    stats = crud.get_site_review_stats(db, site_id, current_user.email)
    
    # Combine site data with stats
    site_dict = {
        'id': site.id,
        'name': site.name,
        'description': site.description,
        'category': site.category,
        'region': site.region,
        'location': site.location,
        'image_url': site.image_url,
        'tags': site.tags,
        'created_at': site.created_at,
        **stats
    }
    
    return HeritageSiteWithReviews(**site_dict)


# GET /heritage-sites/my-reviews - Get current user's reviews
@router.get("/my-reviews", response_model=List[SiteReviewOut])
def get_my_reviews(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all reviews written by the current user"""
    reviews, total = crud.get_user_reviews(db, current_user.email, page, page_size)
    return reviews
