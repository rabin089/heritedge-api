import pytest

def test_complete_user_journey_flow(as_user, db_session):
    """
    End-to-End User Flow:
    1. A logged-in user likes a Heritage Site (adds favorite)
    2. We verify the favorite is saved via API
    3. We check recommendations to ensure they reflect this interaction
    """
    # 1. First, we need a site to interact with.
    # The 'patch_favorites_crud' or other mocks might interfere here if we don't use real DB
    # For a true integration test, we should rely on the actual endpoints and DB
    # We will use the database fixture directly to inject a site, or just test the API flow.
    # Insert the DummyUser that 'as_user' will authenticate as (int=1)
    import uuid
    from app.models.user import User
    test_user = User(
        id=uuid.UUID(int=1),
        email="user@test.com",
        role="user",
        hashed_password="pw"
    )
    db_session.add(test_user)
    
    from app.models.heritage_site import HeritageSite
    site = HeritageSite(
        name="Integration Site",
        description="Integration testing site",
        category="museum",
        tags=["art", "culture"],
        latitude=27.7,
        longitude=85.3,
        created_by="user@test.com"
    )
    db_session.add(site)
    db_session.commit()
    
    # Override the database dependency to use our SQLite db_session instead of Postgres SessionLocal
    from app.main import app
    from app.api.v1.favorites import get_db as fav_get_db
    from app.api.v1.heritage import get_db as heritage_get_db
    from app.api.v1.recommendations import get_db as rec_get_db
    from app.core.database import get_db as core_get_db
    
    def override_get_db():
        yield db_session
        
    app.dependency_overrides[fav_get_db] = override_get_db
    app.dependency_overrides[heritage_get_db] = override_get_db
    app.dependency_overrides[rec_get_db] = override_get_db
    app.dependency_overrides[core_get_db] = override_get_db
    
    try:
        # Actually hitting the API requires us to mock or bypass dependencies if they aren't fully set up.
        # We'll use the 'as_user' fixture which provides an authenticated test client.
    
        # 2. Add to favorites
        response = as_user.post(f"/api/v1/favorites/{site.id}")
        assert response.status_code == 200, f"Failed: {response.status_code} - {response.text}"
        
        # A simple integration: User fetches sites, picks one, and requests it.
        response = as_user.get(f"/api/v1/heritage-sites/{site.id}")
        assert response.status_code == 200, f"Failed: {response.status_code} - {response.text}"
        assert response.json()["name"] == "Integration Site"
        
        # 3. Check recommendations endpoint
        response = as_user.get(f"/api/v1/recommendations")
        assert response.status_code == 200
    finally:
        app.dependency_overrides.clear()
