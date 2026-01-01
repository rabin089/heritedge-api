from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from uuid import UUID
from app.models.site_review import SiteReview, SiteRating
from app.models.heritage_site import HeritageSite
from app.models.contribution import Contribution
from app.schemas.site_review import SiteReviewCreate, SiteReviewUpdate, SiteRatingCreate
from datetime import datetime, timezone


def can_user_review_site(db: Session, site_id: UUID, user_email: str) -> bool:
    """Check if user can review a site (not their own contribution)"""
    # Check if user contributed this site
    contribution = db.query(Contribution).filter(
        and_(
            Contribution.created_by == user_email,
            or_(
                Contribution.status == 'approved',
                Contribution.status == 'pending'
            )
        )
    ).first()
    
    if contribution and contribution.heritage_site and contribution.heritage_site.id == site_id:
        return False  # User cannot review their own contribution
    
    # Admins can review any site
    from app.models.user import User
    user = db.query(User).filter(User.email == user_email).first()
    if user and user.role in ['admin', 'superadmin']:
        return True
    
    return True


def create_site_review(db: Session, review_data: SiteReviewCreate, user_email: str):
    """Create a new site review"""
    if not can_user_review_site(db, review_data.site_id, user_email):
        return None
    
    # Check if user already reviewed this site
    existing_review = db.query(SiteReview).filter(
        and_(SiteReview.site_id == review_data.site_id, SiteReview.user_email == user_email)
    ).first()
    
    if existing_review:
        return None  # User already reviewed
    
    review = SiteReview(
        site_id=review_data.site_id,
        user_email=user_email,
        rating=review_data.rating,
        comment=review_data.comment
    )
    db.add(review)
    db.commit()
    db.refresh(review)
    return review


def update_site_review(db: Session, review_id: UUID, review_data: SiteReviewUpdate, user_email: str):
    """Update user's own review"""
    review = db.query(SiteReview).filter(
        and_(SiteReview.id == review_id, SiteReview.user_email == user_email)
    ).first()
    
    if not review:
        return None
    
    if review_data.comment is not None:
        review.comment = review_data.comment
    if review_data.rating is not None:
        review.rating = review_data.rating
    
    review.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(review)
    return review


def delete_site_review(db: Session, review_id: UUID, user_email: str):
    """Delete user's own review"""
    review = db.query(SiteReview).filter(
        and_(SiteReview.id == review_id, SiteReview.user_email == user_email)
    ).first()
    
    if not review:
        return None
    
    db.delete(review)
    db.commit()
    return review


def get_site_reviews(db: Session, site_id: UUID, page: int = 1, page_size: int = 20):
    """Get all reviews for a site with pagination"""
    query = db.query(SiteReview).filter(SiteReview.site_id == site_id)
    total = query.count()
    
    offset = (page - 1) * page_size
    reviews = query.order_by(SiteReview.created_at.desc()).offset(offset).limit(page_size).all()
    
    return reviews, total


def create_site_rating(db: Session, rating_data: SiteRatingCreate, user_email: str):
    """Create or update a site rating"""
    if not can_user_review_site(db, rating_data.site_id, user_email):
        return None
    
    # Check if user already rated this site
    existing_rating = db.query(SiteRating).filter(
        and_(SiteRating.site_id == rating_data.site_id, SiteRating.user_email == user_email)
    ).first()
    
    if existing_rating:
        # Update existing rating
        existing_rating.rating = rating_data.rating
        db.commit()
        db.refresh(existing_rating)
        return existing_rating
    else:
        # Create new rating
        rating = SiteRating(
            site_id=rating_data.site_id,
            user_email=user_email,
            rating=rating_data.rating
        )
        db.add(rating)
        db.commit()
        db.refresh(rating)
        return rating


def get_site_review_stats(db: Session, site_id: UUID, user_email: str = None) -> dict:
    """Get review statistics for a site"""
    # Get review stats
    review_stats = db.query(
        func.count(SiteReview.id).label('total_reviews'),
        func.avg(SiteReview.rating).label('average_rating')
    ).filter(SiteReview.site_id == site_id).first()
    
    # Get rating stats
    rating_stats = db.query(
        func.count(SiteRating.id).label('total_ratings'),
        func.avg(SiteRating.rating).label('average_rating_only')
    ).filter(SiteRating.site_id == site_id).first()
    
    # Check if user has reviewed
    user_has_reviewed = False
    user_rating = None
    if user_email:
        user_review = db.query(SiteReview).filter(
            and_(SiteReview.site_id == site_id, SiteReview.user_email == user_email)
        ).first()
        user_has_reviewed = user_review is not None
        user_rating = user_review.rating if user_review else None
    
    # Calculate combined average
    total_reviews = review_stats.total_reviews or 0
    total_ratings = rating_stats.total_ratings or 0
    avg_review_rating = float(review_stats.average_rating) if review_stats.average_rating else None
    avg_rating_rating = float(rating_stats.average_rating_only) if rating_stats.average_rating_only else None
    
    # Weighted average (reviews count more than simple ratings)
    if total_reviews > 0 and total_ratings > 0:
        average_rating = (avg_review_rating * total_reviews + avg_rating_rating * total_ratings) / (total_reviews + total_ratings)
    elif total_reviews > 0:
        average_rating = avg_review_rating
    elif total_ratings > 0:
        average_rating = avg_rating_rating
    else:
        average_rating = None
    
    return {
        'average_rating': average_rating,
        'total_reviews': total_reviews,
        'total_ratings': total_ratings,
        'user_has_reviewed': user_has_reviewed,
        'user_rating': user_rating
    }


def get_popular_sites(db: Session, limit: int = 10, by_reviews: bool = True):
    """Get most popular sites by reviews or ratings"""
    if by_reviews:
        # Most reviewed sites
        query = db.query(
            HeritageSite.id,
            HeritageSite.name,
            HeritageSite.category,
            HeritageSite.region,
            HeritageSite.image_url,
            func.count(SiteReview.id).label('total_reviews'),
            func.avg(SiteReview.rating).label('average_rating')
        ).outerjoin(SiteReview).filter(
            and_(
                HeritageSite.is_deleted == False,
                HeritageSite.is_pending == False
            )
        ).group_by(
            HeritageSite.id, HeritageSite.name,
            HeritageSite.category, HeritageSite.region, HeritageSite.image_url
        ).order_by(func.count(SiteReview.id).desc()).limit(limit)
    else:
        # Highest rated sites
        query = db.query(
            HeritageSite.id,
            HeritageSite.name,
            HeritageSite.category,
            HeritageSite.region,
            HeritageSite.image_url,
            func.count(SiteRating.id).label('total_ratings'),
            func.avg(SiteRating.rating).label('average_rating')
        ).outerjoin(SiteRating).filter(
            and_(
                HeritageSite.is_deleted == False,
                HeritageSite.is_pending == False
            )
        ).group_by(
            HeritageSite.id, HeritageSite.name,
            HeritageSite.category, HeritageSite.region, HeritageSite.image_url
        ).order_by(func.avg(SiteRating.rating).desc()).limit(limit)
    
    return query.all()


def get_user_reviews(db: Session, user_email: str, page: int = 1, page_size: int = 20):
    """Get all reviews by a user"""
    query = db.query(SiteReview).filter(SiteReview.user_email == user_email)
    total = query.count()
    
    offset = (page - 1) * page_size
    reviews = query.order_by(SiteReview.created_at.desc()).offset(offset).limit(page_size).all()
    
    return reviews, total
