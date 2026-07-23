import uuid
import math
from sqlalchemy.orm import Session
from sqlalchemy import select
from collections import defaultdict
from typing import List, Dict, Any

from app.models.heritage_site import HeritageSite
from app.models.festival import Festival
from app.models.intangible_heritage import IntangibleHeritage
from app.models.user_activity import UserActivity, ItemType, ActionType
from app.models.user_interest_profile import UserInterestProfile
from app.models.recommendation_history import RecommendationHistory

# Default Weights
WEIGHT_CATEGORY = 0.35
WEIGHT_INTERACTION = 0.30
WEIGHT_SIMILARITY = 0.20
WEIGHT_LOCATION = 0.15

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great circle distance between two points on the earth (specified in decimal degrees)"""
    if lat1 is None or lon1 is None or lat2 is None or lon2 is None:
        return float('inf')
        
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    r = 6371 # Radius of earth in kilometers.
    return c * r

def calculate_category_score(user_profile: UserInterestProfile, item) -> float:
    if not user_profile or not user_profile.category_scores:
        return 0.0
    
    category = getattr(item, "category", None)
    if category and hasattr(category, "value"):
        category = category.value
    elif category:
        category = str(category).lower()
        
    if not category:
        return 0.0

    # Max score we cap at is 10.0 from activity tracking, let's normalize between 0-1
    score = user_profile.category_scores.get(category, 0.0)
    return min(score / 10.0, 1.0)


def calculate_interaction_score(user_activities: List[UserActivity], item_id: uuid.UUID) -> float:
    # If the user has interacted directly with this item, score it higher
    from app.services.activity_service import ACTION_WEIGHTS
    
    total_score = 0.0
    for act in user_activities:
        if act.item_id == item_id:
            total_score += ACTION_WEIGHTS.get(act.action_type, 0.1)
            
    # Max possible score we consider 1.0 (e.g. they bookmarked it)
    return min(total_score, 1.0)


def calculate_similarity_score(user_profile: UserInterestProfile, item) -> float:
    if not user_profile or not user_profile.tag_scores:
        return 0.0
        
    item_tags = getattr(item, "tags", []) or []
    if not item_tags:
        return 0.0
        
    item_tags = set(str(t).lower() for t in item_tags)
    user_tags = set(str(t).lower() for t in user_profile.tag_scores.keys())
    
    intersection = user_tags.intersection(item_tags)
    union = user_tags.union(item_tags)
    
    if not union:
        return 0.0
        
    # Jaccard Similarity
    return len(intersection) / len(union)


def calculate_location_score(user_lat: float, user_lon: float, item) -> float:
    if user_lat is None or user_lon is None:
        return 0.0
        
    item_lat = getattr(item, "latitude", None)
    item_lon = getattr(item, "longitude", None)
    
    dist = haversine_distance(user_lat, user_lon, item_lat, item_lon)
    if dist == float('inf'):
        return 0.0
        
    # LocationScore = 1 / (1 + d)
    return 1.0 / (1.0 + dist)


def generate_recommendations(db: Session, user_id: uuid.UUID, lat: float = None, lon: float = None, limit: int = 10, item_type: ItemType = None) -> List[Dict[str, Any]]:
    # 1. Fetch user profile and activities
    profile = db.query(UserInterestProfile).filter(UserInterestProfile.user_id == user_id).first()
    activities = db.query(UserActivity).filter(UserActivity.user_id == user_id).all()
    
    # 2. Fetch all candidate items
    candidates = []
    
    if item_type is None or item_type == ItemType.site:
        sites = db.query(HeritageSite).all()
        for s in sites:
            candidates.append((s, ItemType.site))
            
    if item_type is None or item_type == ItemType.festival:
        festivals = db.query(Festival).all()
        for f in festivals:
            candidates.append((f, ItemType.festival))
            
    if item_type is None or item_type == ItemType.intangible:
        intangibles = db.query(IntangibleHeritage).all()
        for i in intangibles:
            candidates.append((i, ItemType.intangible))
        
    scored_items = []
    
    # 3. Calculate scores
    for item, item_type in candidates:
        cat_score = calculate_category_score(profile, item)
        int_score = calculate_interaction_score(activities, item.id)
        sim_score = calculate_similarity_score(profile, item)
        loc_score = calculate_location_score(lat, lon, item)
        
        final_score = (WEIGHT_CATEGORY * cat_score) + \
                      (WEIGHT_INTERACTION * int_score) + \
                      (WEIGHT_SIMILARITY * sim_score) + \
                      (WEIGHT_LOCATION * loc_score)
                      
        # Generate an explanation reason based on highest contributing factor
        reason = "Recommended based on your activity."
        if final_score > 0:
            scores_dict = {
                "category preference": cat_score * WEIGHT_CATEGORY,
                "direct interaction": int_score * WEIGHT_INTERACTION,
                "similar cultural tradition": sim_score * WEIGHT_SIMILARITY,
                "location": loc_score * WEIGHT_LOCATION
            }
            top_factor = max(scores_dict, key=scores_dict.get)
            if top_factor == "category preference":
                reason = "Recommended because it matches your preferred heritage categories."
            elif top_factor == "direct interaction":
                reason = "Recommended because you've interacted with similar items."
            elif top_factor == "similar cultural tradition":
                reason = "Recommended because it shares a similar cultural tradition to your interests."
            elif top_factor == "location":
                reason = "Recommended based on your location."

        name = getattr(item, "name", None) or getattr(item, "name_en", None) or "Unknown Item"
        
        scored_items.append({
            "id": str(item.id),
            "name": name,
            "type": item_type.value,
            "score": round(final_score, 2),
            "reason": reason
        })
        
    # 4. Sort by score
    scored_items.sort(key=lambda x: x["score"], reverse=True)
    top_recommendations = scored_items[:limit]
    
    # 5. Save history
    history = RecommendationHistory(
        user_id=user_id,
        recommendations=top_recommendations
    )
    db.add(history)
    db.commit()
    
    return top_recommendations
