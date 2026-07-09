import uuid
from sqlalchemy.orm import Session
from sqlalchemy import select
from fastapi import BackgroundTasks

from app.models.user_activity import UserActivity, ItemType, ActionType
from app.models.user_interest_profile import UserInterestProfile
from app.models.heritage_site import HeritageSite
from app.models.festival import Festival
from app.models.intangible_heritage import IntangibleHeritage

ACTION_WEIGHTS = {
    ActionType.bookmark: 1.0,
    ActionType.review: 0.8,
    ActionType.share: 0.7,
    ActionType.favorite: 0.6,
    ActionType.view: 0.3,
    ActionType.search: 0.2,
}

def get_item(db: Session, item_id: uuid.UUID, item_type: ItemType):
    if item_type == ItemType.site:
        return db.query(HeritageSite).filter(HeritageSite.id == item_id).first()
    elif item_type == ItemType.festival:
        return db.query(Festival).filter(Festival.id == item_id).first()
    elif item_type == ItemType.intangible:
        return db.query(IntangibleHeritage).filter(IntangibleHeritage.id == item_id).first()
    return None

def update_user_interest_profile(db: Session, user_id: uuid.UUID, item_id: uuid.UUID, item_type: ItemType, action_type: ActionType):
    item = get_item(db, item_id, item_type)
    if not item:
        return

    # Get or create profile
    profile = db.query(UserInterestProfile).filter(UserInterestProfile.user_id == user_id).first()
    if not profile:
        profile = UserInterestProfile(user_id=user_id, category_scores={}, tag_scores={})
        db.add(profile)
        db.flush() # ensure profile.id is generated if needed

    weight = ACTION_WEIGHTS.get(action_type, 0.1)

    # We update category scores and tag scores based on the item
    category = getattr(item, "category", None)
    # the model returns an enum for FestivalCategory, so we handle it
    if category and hasattr(category, "value"):
        category = category.value
    elif category:
        category = str(category).lower()

    if category:
        # Avoid assigning dict directly without creating a new copy if using JSONB, or use set/get correctly
        cat_scores = dict(profile.category_scores) if profile.category_scores else {}
        current_cat_score = cat_scores.get(category, 0.0)
        cat_scores[category] = min(current_cat_score + weight, 10.0) # Cap at 10.0 for now, normalize later
        profile.category_scores = cat_scores

    tags = getattr(item, "tags", []) or []
    if tags:
        tag_scores = dict(profile.tag_scores) if profile.tag_scores else {}
        for tag in tags:
            tag = str(tag).lower()
            current_tag_score = tag_scores.get(tag, 0.0)
            tag_scores[tag] = min(current_tag_score + weight, 10.0)
        profile.tag_scores = tag_scores

    db.commit()


def record_activity(db: Session, user_id: uuid.UUID, item_id: uuid.UUID, item_type: ItemType, action_type: ActionType, background_tasks: BackgroundTasks = None):
    activity = UserActivity(
        user_id=user_id,
        item_id=item_id,
        item_type=item_type,
        action_type=action_type
    )
    db.add(activity)
    db.commit()
    
    if background_tasks:
        background_tasks.add_task(update_user_interest_profile, db, user_id, item_id, item_type, action_type)
    else:
        update_user_interest_profile(db, user_id, item_id, item_type, action_type)
    
    return activity
