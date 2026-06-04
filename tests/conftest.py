import types
import pytest
from fastapi.testclient import TestClient
from datetime import datetime
import uuid

from app.main import app
from app.api.v1 import contribution as contribution_api
from app.api.v1 import heritage as heritage_api
from app.api.v1 import auth as auth_api
from app.models.user import User
from app.models.contribution import ContributionStatus


class DummyUser(User):
    def __init__(self, email: str, role: str):
        # bypass SQLAlchemy init
        for k, v in {"email": email, "role": role, "id": 1, "is_active": True, "is_admin": role in {"admin", "superadmin"}}.items():
            setattr(self, k, v)


def _get_current_user_with_role(role: str):
    def dep():
        return DummyUser(email=f"{role}@test.com", role=role)
    return dep


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def as_reviewer(client):
    app.dependency_overrides[auth_api.get_current_user] = _get_current_user_with_role("reviewer")
    yield client
    app.dependency_overrides.clear()


@pytest.fixture
def as_admin(client):
    app.dependency_overrides[auth_api.get_current_user] = _get_current_user_with_role("admin")
    yield client
    app.dependency_overrides.clear()


@pytest.fixture
def as_user(client):
    app.dependency_overrides[auth_api.get_current_user] = _get_current_user_with_role("user")
    yield client
    app.dependency_overrides.clear()


# convenience monkeypatch helpers for CRUD
@pytest.fixture
def patch_contrib_crud(monkeypatch):
    import app.crud.contributions as contrib_crud

    class DummyContrib:
        def __init__(self, id=1):
            self.id = id
            self.name = "X"
            self.description = None
            self.category = None
            self.region = None
            self.location = None
            self.latitude = 0.0
            self.longitude = 0.0
            self.image_url = None
            self.secondary_images = None
            self.tags = None
            self.public_id = uuid.uuid4()
            self.status = ContributionStatus.rejected
            self.status_reason = None
            self.rejection_reason = "bad"
            self.created_at = datetime.utcnow()
            self.created_by = "admin@test.com"

    def list_all_contributions(db, status=None):
        return []

    def approve_contribution(db, contrib_id, admin_user_id, comment=None):
        return (DummyContrib(contrib_id), uuid.uuid4(), None, None)

    def reject_contribution(db, contrib_id, reason):
        c = DummyContrib(contrib_id)
        return c

    monkeypatch.setattr(contrib_crud, "list_all_contributions", list_all_contributions)
    monkeypatch.setattr(contrib_crud, "approve_contribution", approve_contribution)
    monkeypatch.setattr(contrib_crud, "reject_contribution", reject_contribution)

    yield


@pytest.fixture
def patch_heritage_crud(monkeypatch):
    import app.crud.heritage_site as heritage_crud

    def get_filtered_sites(db, region=None, category=None, tag=None):
        return []

    class FakeSite:
        def __init__(self, site_id=1):
            self.id = site_id
            self.is_deleted = False

    def delete_site(db, site_id: int):
        return FakeSite(site_id)

    monkeypatch.setattr(heritage_crud, "get_filtered_sites", get_filtered_sites)
    monkeypatch.setattr(heritage_crud, "delete_site", delete_site)
    yield
