from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from uuid import UUID
from app.models.site_review import SiteReview, SiteRating
from app.models.heritage_site import HeritageSite
from app.models.contribution import Contribution
from app.schemas.site_review import SiteReviewCreate, SiteReviewUpdate, SiteRatingCreate
from datetime import datetime, timezone


def is_admin_or_superadmin(db: Session, user_email: str) -> bool:
    """Check if user is admin or superadmin"""
    from app.models.user import User
    user = db.query(User).filter(User.email == user_email).first()
    return user and user.role in ['admin', 'superadmin']


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


# ==================== ADMIN REVIEW MANAGEMENT ====================

def admin_delete_review(db: Session, review_id: UUID, admin_email: str):
    """Admin can delete any review"""
    if not is_admin_or_superadmin(db, admin_email):
        return None
    
    review = db.query(SiteReview).filter(SiteReview.id == review_id).first()
    if not review:
        return None
    
    # Store review info for audit trail
    review_info = {
        'deleted_by': admin_email,
        'deleted_at': datetime.now(timezone.utc),
        'original_review': {
            'id': review.id,
            'user_email': review.user_email,
            'rating': review.rating,
            'comment': review.comment,
            'site_id': review.site_id
        }
    }
    
    db.delete(review)
    db.commit()
    return review_info


def admin_update_review(db: Session, review_id: UUID, review_data: SiteReviewUpdate, admin_email: str):
    """Admin can update any review"""
    if not is_admin_or_superadmin(db, admin_email):
        return None
    
    review = db.query(SiteReview).filter(SiteReview.id == review_id).first()
    if not review:
        return None
    
    # Store original values for audit trail
    original_values = {
        'rating': review.rating,
        'comment': review.comment,
        'updated_by': admin_email,
        'updated_at': datetime.now(timezone.utc)
    }
    
    # Update review
    if review_data.comment is not None:
        review.comment = review_data.comment
    if review_data.rating is not None:
        review.rating = review_data.rating
    
    review.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(review)
    
    return review, original_values


def admin_delete_rating(db: Session, rating_id: UUID, admin_email: str):
    """Admin can delete any rating"""
    if not is_admin_or_superadmin(db, admin_email):
        return None
    
    rating = db.query(SiteRating).filter(SiteRating.id == rating_id).first()
    if not rating:
        return None
    
    # Store rating info for audit trail
    rating_info = {
        'deleted_by': admin_email,
        'deleted_at': datetime.now(timezone.utc),
        'original_rating': {
            'id': rating.id,
            'user_email': rating.user_email,
            'rating': rating.rating,
            'site_id': rating.site_id
        }
    }
    
    db.delete(rating)
    db.commit()
    return rating_info


def admin_update_rating(db: Session, rating_id: UUID, new_rating: int, admin_email: str):
    """Admin can update any rating"""
    if not is_admin_or_superadmin(db, admin_email):
        return None
    
    if new_rating < 0 or new_rating > 10:
        return None
    
    rating = db.query(SiteRating).filter(SiteRating.id == rating_id).first()
    if not rating:
        return None
    
    # Store original value for audit trail
    original_value = rating.rating
    
    rating.rating = new_rating
    rating.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(rating)
    
    return rating, original_value


def admin_get_all_reviews(db: Session, page: int = 1, page_size: int = 50, 
                         site_id: UUID = None, user_email: str = None):
    """Admin can get all reviews with optional filters"""
    query = db.query(SiteReview)
    
    if site_id:
        query = query.filter(SiteReview.site_id == site_id)
    if user_email:
        query = query.filter(SiteReview.user_email == user_email)
    
    total = query.count()
    offset = (page - 1) * page_size
    reviews = query.order_by(SiteReview.created_at.desc()).offset(offset).limit(page_size).all()
    
    return reviews, total


def admin_get_all_ratings(db: Session, page: int = 1, page_size: int = 50,
                         site_id: UUID = None, user_email: str = None):
    """Admin can get all ratings with optional filters"""
    query = db.query(SiteRating)
    
    if site_id:
        query = query.filter(SiteRating.site_id == site_id)
    if user_email:
        query = query.filter(SiteRating.user_email == user_email)
    
    total = query.count()
    offset = (page - 1) * page_size
    ratings = query.order_by(SiteRating.created_at.desc()).offset(offset).limit(page_size).all()
    
    return ratings, total


def admin_get_review_stats(db: Session):
    """Admin can get comprehensive review statistics"""
    # Overall stats
    total_reviews = db.query(func.count(SiteReview.id)).scalar()
    total_ratings = db.query(func.count(SiteRating.id)).scalar()
    avg_review_rating = db.query(func.avg(SiteReview.rating)).scalar()
    avg_rating_value = db.query(func.avg(SiteRating.rating)).scalar()
    
    # Reviews by rating distribution
    review_distribution = db.query(
        SiteReview.rating,
        func.count(SiteReview.id).label('count')
    ).group_by(SiteReview.rating).all()
    
    # Most active reviewers
    top_reviewers = db.query(
        SiteReview.user_email,
        func.count(SiteReview.id).label('review_count')
    ).group_by(SiteReview.user_email).order_by(
        func.count(SiteReview.id).desc()
    ).limit(10).all()
    
    # Most reviewed sites
    most_reviewed_sites = db.query(
        HeritageSite.name,
        func.count(SiteReview.id).label('review_count')
    ).join(SiteReview).group_by(
        HeritageSite.id, HeritageSite.name
    ).order_by(func.count(SiteReview.id).desc()).limit(10).all()
    
    return {
        'total_reviews': total_reviews or 0,
        'total_ratings': total_ratings or 0,
        'average_review_rating': float(avg_review_rating) if avg_review_rating else 0,
        'average_rating_value': float(avg_rating_value) if avg_rating_value else 0,
        'review_distribution': [{'rating': r, 'count': c} for r, c in review_distribution],
        'top_reviewers': [{'email': email, 'count': count} for email, count in top_reviewers],
        'most_reviewed_sites': [{'site_name': name, 'count': count} for name, count in most_reviewed_sites]
    }
