"""
Shared pytest fixtures for the HeritEdge backend test suite.

These fixtures are designed to run WITHOUT a real database by:
  * Overriding FastAPI `get_db` dependencies with a mock Session
  * Overriding `get_current_user` with a DummyUser in the right role
  * Monkeypatching CRUD functions called by the endpoints

This keeps the test suite fast (< 1s per test) and runnable on any machine.
"""
import types
import uuid
from datetime import datetime
from typing import Any, List, Optional

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.api.v1 import auth as auth_api
from app.api.v1 import contribution as contribution_api
from app.api.v1 import heritage as heritage_api
from app.api.v1 import favorites as favorites_api
from app.api.v1 import notification as notification_api
from app.models.user import User
from app.models.contribution import ContributionStatus, ContributionType


# ---------------------------------------------------------------------------
# Dummy in-memory user used to bypass SQLAlchemy session binding
# ---------------------------------------------------------------------------
class DummyUser(User):
    """Conforms to app.schemas.users.UserOut.

    Bypasses SQLAlchemy's `__init__` and sets the attributes that the
    response model needs.
    """

    def __init__(
        self,
        email: str,
        role: str = "user",
        user_id: int = 1,
        is_active: bool = True,
        display_name: Optional[str] = None,
        name: Optional[str] = None,
    ):
        for k, v in {
            "email": email,
            "role": role,
            "id": uuid.UUID(int=user_id),
            "is_active": is_active,
            "is_admin": role in {"admin", "superadmin"},
            "display_name": display_name or email.split("@")[0].title(),
            "name": name or email.split("@")[0].title(),
            "profile_photo_url": None,
            "auth_provider": "email",
            "account_created_at": datetime(2024, 1, 1),
            "last_login_at": None,
        }.items():
            setattr(self, k, v)


def _get_current_user_with_role(role: str, email: Optional[str] = None):
    """Factory that returns a dependency override for `get_current_user`."""

    def dep():
        return DummyUser(
            email=email or f"{role}@test.com",
            role=role,
        )

    return dep


# ---------------------------------------------------------------------------
# Mock database session
# ---------------------------------------------------------------------------
class MockDB:
    """A minimal SQLAlchemy-like session for tests."""

    def __init__(self):
        self.added: List[Any] = []
        self.committed = False
        self.closed = False

    def add(self, obj):
        self.added.append(obj)

    def commit(self):
        self.committed = True

    def refresh(self, obj):
        return obj

    def delete(self, obj):
        return None

    def close(self):
        self.closed = True

    def query(self, *args, **kwargs):
        return MockQuery()


class MockQuery:
    def filter(self, *args, **kwargs):
        return self

    def first(self):
        return None

    def all(self):
        return []


def _override_get_db(mock_db: MockDB):
    """Return a get_db() generator that always yields the same mock_db."""

    def _gen():
        try:
            yield mock_db
        finally:
            pass

    return _gen


# ---------------------------------------------------------------------------
# Pytest fixtures
# ---------------------------------------------------------------------------
@pytest.fixture(autouse=True)
def _reset_mock_query():
    """Auto-reset MockQuery.first/all between tests so patches don't leak."""
    # Save originals
    orig_first = MockQuery.first
    orig_all = MockQuery.all
    yield
    # Restore
    MockQuery.first = orig_first
    MockQuery.all = orig_all


@pytest.fixture
def mock_db():
    return MockDB()


@pytest.fixture
def client(mock_db):
    """Plain TestClient. No user override (use for unauthenticated tests)."""
    return TestClient(app)


@pytest.fixture
def as_reviewer(client, mock_db):
    app.dependency_overrides[auth_api.get_current_user] = _get_current_user_with_role("reviewer")
    app.dependency_overrides[auth_api.get_db] = _override_get_db(mock_db)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture
def as_admin(client, mock_db):
    app.dependency_overrides[auth_api.get_current_user] = _get_current_user_with_role("admin")
    app.dependency_overrides[auth_api.get_db] = _override_get_db(mock_db)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture
def as_user(client, mock_db):
    app.dependency_overrides[auth_api.get_current_user] = _get_current_user_with_role("user")
    app.dependency_overrides[auth_api.get_db] = _override_get_db(mock_db)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture
def as_superadmin(client, mock_db):
    app.dependency_overrides[auth_api.get_current_user] = _get_current_user_with_role("superadmin")
    app.dependency_overrides[auth_api.get_db] = _override_get_db(mock_db)
    yield client
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Schema-conformant fakes
# ---------------------------------------------------------------------------
def _make_uuid(seed) -> uuid.UUID:
    """Deterministic UUID for assertions in tests. Accepts int or UUID."""
    if isinstance(seed, uuid.UUID):
        return seed
    return uuid.UUID(int=seed)


class FakeHeritageSite:
    """Conforms to app.schemas.heritage_site.HeritageSiteOut."""

    def __init__(self, site_id: int = 1, **overrides):
        self.id = _make_uuid(site_id)
        self.name = "Test Site"
        self.description = "Test description"
        self.category = "temple"
        self.region = "Kathmandu"
        self.location = None
        self.latitude = 27.7
        self.longitude = 85.3
        self.image_url = None
        self.secondary_images = None
        self.tags = []
        self.created_by = "admin@test.com"
        self.created_at = datetime(2024, 1, 1, 12, 0, 0)
        self.contribution_id = None
        self.is_pending = False
        self.contributor_id = None
        self.contributor_name = "Anonymous"
        for k, v in overrides.items():
            setattr(self, k, v)


class FakeContribution:
    """Conforms to app.schemas.contribution.ContributionOut."""

    def __init__(self, contrib_id: int = 1, **overrides):
        self.id = _make_uuid(contrib_id)
        self.type = ContributionType.site
        self.name = "Test Contribution"
        self.name_np = None
        self.description = "Desc"
        self.category = "temple"
        self.region = "Kathmandu"
        self.location = None
        self.latitude = 27.7
        self.longitude = 85.3
        self.image_url = None
        self.secondary_images = None
        self.tags = None
        self.festival_id = None
        self.start_date = None
        self.end_date = None
        self.significance = None
        self.nepali_date = None
        self.is_annual = False
        self.community = None
        self.language = None
        self.risk_level = None
        self.practiced_at = None
        self.video_url = None
        self.audio_url = None
        self.public_id = _make_uuid(contrib_id)
        self.status = ContributionStatus.pending
        self.status_reason = None
        self.rejection_reason = None
        self.created_at = datetime(2024, 1, 1)
        self.created_by = "user@test.com"
        self.contributor_name = "Test User"
        self.contributor_email = "user@test.com"
        self.creator_details = None
        for k, v in overrides.items():
            setattr(self, k, v)


class FakeNotification:
    """Conforms to app.schemas.notification.NotificationOut.

    Note: NotificationOut uses `is_read` (with validation alias `read`).
    The attribute we set on the object must be `read` so the alias works.
    """

    def __init__(self, nid: int = 1, read: bool = False, **overrides):
        self.id = _make_uuid(nid)
        self.recipient_email = "user@test.com"
        self.title = "Test"
        self.message = "Hello"
        self.read = read
        self.read_at = None
        self.created_at = datetime(2024, 1, 1)
        for k, v in overrides.items():
            setattr(self, k, v)


# ---------------------------------------------------------------------------
# CRUD monkeypatch helpers
# ---------------------------------------------------------------------------
@pytest.fixture
def patch_contrib_crud(monkeypatch):
    """Patch the contributions CRUD module with dummies."""
    import app.crud.contributions as contrib_crud

    def list_all_contributions(db, status=None):
        return []

    def list_my_contributions(db, email, status=None):
        return []

    def create_contribution(db, payload, user_id=None):
        return FakeContribution(1)

    def update_my_pending_contribution(db, contrib_id, email, payload):
        return FakeContribution(contrib_id if isinstance(contrib_id, int) else 1)

    def delete_my_pending_contribution(db, contrib_id, email):
        return FakeContribution(contrib_id if isinstance(contrib_id, int) else 1)

    def approve_contribution(db, contrib_id, admin_user_id, comment=None):
        # Returned tuple: (contrib_obj, site_id, festival_id, intangible_id)
        seed = contrib_id.int if isinstance(contrib_id, uuid.UUID) else contrib_id
        return (FakeContribution(seed), _make_uuid(99), None, None)

    def reject_contribution(db, contrib_id, reason, admin_user_id=None):
        seed = contrib_id.int if isinstance(contrib_id, uuid.UUID) else contrib_id
        return FakeContribution(
            seed,
            status=ContributionStatus.rejected,
            rejection_reason=reason,
        )

    def resubmit_rejected_contribution(db, contrib_id, email, payload=None):
        seed = contrib_id.int if isinstance(contrib_id, uuid.UUID) else contrib_id
        return FakeContribution(seed, status=ContributionStatus.pending)

    monkeypatch.setattr(contrib_crud, "list_all_contributions", list_all_contributions)
    monkeypatch.setattr(contrib_crud, "list_my_contributions", list_my_contributions)
    monkeypatch.setattr(contrib_crud, "create_contribution", create_contribution)
    monkeypatch.setattr(contrib_crud, "update_my_pending_contribution", update_my_pending_contribution)
    monkeypatch.setattr(contrib_crud, "delete_my_pending_contribution", delete_my_pending_contribution)
    monkeypatch.setattr(contrib_crud, "approve_contribution", approve_contribution)
    monkeypatch.setattr(contrib_crud, "reject_contribution", reject_contribution)
    monkeypatch.setattr(contrib_crud, "resubmit_rejected_contribution", resubmit_rejected_contribution)

    yield contrib_crud


@pytest.fixture
def patch_heritage_crud(monkeypatch):
    """Patch the heritage_site CRUD module with dummies."""
    import app.crud.heritage_site as heritage_crud

    def get_filtered_sites(db, region=None, category=None, tag=None, q=None, page=None, page_size=None):
        return [FakeHeritageSite(1), FakeHeritageSite(2)]

    def get_site_by_id(db, site_id):
        return FakeHeritageSite(1)

    def update_heritage_site(db, site_id, site_data, admin_id=None):
        return FakeHeritageSite(1)

    def delete_site(db, site_id, admin_id=None):
        seed = site_id.int if isinstance(site_id, uuid.UUID) else site_id
        return FakeHeritageSite(seed)

    monkeypatch.setattr(heritage_crud, "get_filtered_sites", get_filtered_sites)
    monkeypatch.setattr(heritage_crud, "get_site_by_id", get_site_by_id)
    monkeypatch.setattr(heritage_crud, "update_heritage_site", update_heritage_site)
    monkeypatch.setattr(heritage_crud, "delete_site", delete_site)

    yield heritage_crud


@pytest.fixture
def patch_favorites_crud(monkeypatch):
    """Patch the favorites CRUD module with dummies."""
    import app.crud.favorites as fav_crud

    def add_favorite(db, user_id, site_id):
        return True

    def remove_favorite(db, user_id, site_id):
        return True

    def list_favorites(db, user_id):
        return [FakeHeritageSite(10, name="Fav Site", region="Lalitpur")]

    monkeypatch.setattr(fav_crud, "add_favorite", add_favorite)
    monkeypatch.setattr(fav_crud, "remove_favorite", remove_favorite)
    monkeypatch.setattr(fav_crud, "list_favorites", list_favorites)

    yield fav_crud


@pytest.fixture
def patch_notifications_crud(monkeypatch):
    """Patch the notifications CRUD module with dummies."""
    import app.crud.notifications as notif_crud

    def list_my_notifications(db, email):
        return [FakeNotification(1), FakeNotification(2, read=True)]

    def mark_read(db, email, ids):
        return len(ids)

    def count_unread(db, email):
        return 1

    def mark_all_read(db, email):
        return 3

    def create_notification(db, **kwargs):
        return FakeNotification(99)

    monkeypatch.setattr(notif_crud, "list_my_notifications", list_my_notifications)
    monkeypatch.setattr(notif_crud, "mark_read", mark_read)
    monkeypatch.setattr(notif_crud, "count_unread", count_unread)
    monkeypatch.setattr(notif_crud, "mark_all_read", mark_all_read)
    monkeypatch.setattr(notif_crud, "create_notification", create_notification)

    yield notif_crud


# ---------------------------------------------------------------------------
# Auth-specific fixtures (mock DB so we can test signup/login)
# ---------------------------------------------------------------------------
@pytest.fixture
def patch_security(monkeypatch):
    """Mock password hashing and JWT creation/verification for unit tests."""
    from app.core import security

    def hash_password(pw: str) -> str:
        return f"hashed::{pw}"

    def verify_password(plain: str, hashed: str) -> bool:
        return hashed == f"hashed::{plain}"

    def create_access_token(data, expires_delta=None):
        return "fake.access.token"

    def create_refresh_token(data, expires_delta=None):
        return "fake.refresh.token"

    monkeypatch.setattr(security, "hash_password", hash_password)
    monkeypatch.setattr(security, "verify_password", verify_password)
    monkeypatch.setattr(security, "create_access_token", create_access_token)
    monkeypatch.setattr(security, "create_refresh_token", create_refresh_token)
    yield security
