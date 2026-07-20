from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, select, literal_column
from typing import List
from app.core.database import SessionLocal
from app.models.heritage_site import HeritageSite
from app.models.site_review import SiteReview, SiteRating
from app.models.festival import Festival
from app.models.festival_interaction import FestivalReaction
from app.schemas.heritage_site import HeritageSiteOut
from app.schemas.festival import FestivalOut
from app.models.intangible_heritage import IntangibleHeritage
from app.schemas.intangible_heritage import IntangibleHeritageOut

router = APIRouter(prefix="/discover", tags=["discover"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/popular-sites", response_model=List[HeritageSiteOut])
def get_popular_sites(limit: int = 10, db: Session = Depends(get_db)):
    """
    Get top heritage sites based on popularity score:
    Score = views_count + (review_count * 5) + (avg_rating * 10)
    """
    
    # Subquery for review counts
    review_counts = (
        db.query(
            SiteReview.site_id,
            func.count(SiteReview.id).label("review_count")
        )
        .group_by(SiteReview.site_id)
        .subquery()
    )

    # Subquery for average rating
    avg_ratings = (
        db.query(
            SiteRating.site_id,
            func.avg(SiteRating.rating).label("avg_rating")
        )
        .group_by(SiteRating.site_id)
        .subquery()
    )

    # Query sites with calculated score
    sites = (
        db.query(
            HeritageSite,
            func.coalesce(review_counts.c.review_count, 0).label("review_count"),
            func.coalesce(avg_ratings.c.avg_rating, 0).label("avg_rating")
        )
        .outerjoin(review_counts, HeritageSite.id == review_counts.c.site_id)
        .outerjoin(avg_ratings, HeritageSite.id == avg_ratings.c.site_id)
        .filter(HeritageSite.is_pending == False, HeritageSite.is_deleted == False)
        .order_by(
            desc(
                HeritageSite.views_count +
                (func.coalesce(review_counts.c.review_count, 0) * 5) +
                (func.coalesce(avg_ratings.c.avg_rating, 0) * 10)
            )
        )
        .limit(limit)
        .all()
    )
    
    # Return just the HeritageSite instances (the schema will parse them)
    return [site for site, rc, ar in sites]


@router.get("/popular-festivals", response_model=List[FestivalOut])
def get_popular_festivals(limit: int = 10, db: Session = Depends(get_db)):
    """
    Get top festivals based on popularity score:
    Score = views_count + (reactions_count * 5)
    """
    
    # Subquery for reaction counts
    reaction_counts = (
        db.query(
            FestivalReaction.festival_id,
            func.count(FestivalReaction.id).label("reaction_count")
        )
        .group_by(FestivalReaction.festival_id)
        .subquery()
    )

    # Query festivals with calculated score
    festivals = (
        db.query(
            Festival,
            func.coalesce(reaction_counts.c.reaction_count, 0).label("reaction_count")
        )
        .outerjoin(reaction_counts, Festival.id == reaction_counts.c.festival_id)
        .filter(Festival.status == 'approved')
        .order_by(
            desc(
                Festival.views_count +
                (func.coalesce(reaction_counts.c.reaction_count, 0) * 5)
            )
        )
        .limit(limit)
        .all()
    )
    
    return [fest for fest, rc in festivals]


@router.get("/popular-traditions", response_model=List[IntangibleHeritageOut])
def get_popular_traditions(limit: int = 10, db: Session = Depends(get_db)):
    """
    Get top traditions (intangible heritage) based on popularity score:
    Score = view_count + (favorite_count * 5)
    """
    traditions = (
        db.query(IntangibleHeritage)
        .filter(IntangibleHeritage.status == 'approved')
        .order_by(
            desc(
                IntangibleHeritage.view_count +
                (IntangibleHeritage.favorite_count * 5)
            )
        )
        .limit(limit)
        .all()
    )
    
    return traditions

