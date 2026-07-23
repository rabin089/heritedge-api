import pytest
import uuid
from app.services.activity_service import record_activity, get_item
from app.models.user_activity import ItemType, ActionType
from app.models.user_interest_profile import UserInterestProfile
from app.models.heritage_site import HeritageSite

def test_record_activity_creates_profile_and_updates_scores(db_session):
    # let's just create a dummy site and user manually in this session
    
    # 1. Create a User
    from app.models.user import User
    user = User(email="service@test.com", role="user", hashed_password="pw")
    db_session.add(user)
    db_session.flush()
    
    # 2. Create a Heritage Site
    site = HeritageSite(
        name="Test Service Site",
        description="A beautiful site",
        category="monument",
        tags=["historical", "ancient"],
        latitude=27.7,
        longitude=85.3,
        created_by="service@test.com"
    )
    db_session.add(site)
    db_session.flush()
    
    # 3. Record Activity (mock get_item to bypass SQLite ARRAY read issue)
    from unittest.mock import patch, MagicMock
    
    mock_site = MagicMock()
    mock_site.id = site.id
    mock_site.category = "monument"
    mock_site.tags = ["historical", "ancient"]
    
    with patch("app.services.activity_service.get_item", return_value=mock_site):
        activity = record_activity(
            db=db_session,
            user_id=user.id,
            item_id=site.id,
            item_type=ItemType.site,
            action_type=ActionType.favorite
        )
    
    assert activity is not None
    assert activity.user_id == user.id
    
    # 4. Verify User Interest Profile was created and updated
    profile = db_session.query(UserInterestProfile).filter(UserInterestProfile.user_id == user.id).first()
    
    assert profile is not None
    assert "monument" in profile.category_scores
    assert profile.category_scores["monument"] == 0.6  # favorite weight
    
    assert "historical" in profile.tag_scores
    assert profile.tag_scores["historical"] == 0.6
    assert "ancient" in profile.tag_scores
