from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.api.v1.auth import get_current_user
from app.schemas.recommendation import RecommendationResponse
from app.services.recommendation_service import generate_recommendations

router = APIRouter(prefix="/recommendations", tags=["recommendations"])

from app.models.user_activity import ItemType

@router.get("", response_model=RecommendationResponse)
def get_recommendations(
    latitude: Optional[float] = Query(None, description="User's current latitude for location-based recommendations"),
    longitude: Optional[float] = Query(None, description="User's current longitude for location-based recommendations"),
    item_type: Optional[ItemType] = Query(None, description="Filter recommendations by type (site, festival, intangible)"),
    limit: int = Query(10, description="Max recommendations to return"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get personalized recommendations based on the Hybrid Cultural Recommendation Engine.
    """
    recommendations = generate_recommendations(
        db=db,
        user_id=current_user.id,
        lat=latitude,
        lon=longitude,
        limit=limit,
        item_type=item_type
    )
    return {"recommendations": recommendations}
