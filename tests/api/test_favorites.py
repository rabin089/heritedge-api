"""
Tests for the favorites endpoints:
  POST   /api/v1/favorites/{site_id}
  DELETE /api/v1/favorites/{site_id}
  GET    /api/v1/favorites
"""
import pytest
from fastapi import status


SITE_ID = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"


# ---------------------------------------------------------------------------
# Add
# ---------------------------------------------------------------------------
def test_user_can_add_favorite(as_user, patch_favorites_crud):
    resp = as_user.post(f"/api/v1/favorites/{SITE_ID}")
    assert resp.status_code == status.HTTP_200_OK
    body = resp.json()
    assert "added" in body["message"].lower()


def test_add_favorite_requires_auth(client, patch_favorites_crud):
    resp = client.post(f"/api/v1/favorites/{SITE_ID}")
    assert resp.status_code in (401, 403)


def test_add_favorite_fails_when_crud_returns_false(as_user, patch_favorites_crud, monkeypatch):
    import app.crud.favorites as fav_crud
    monkeypatch.setattr(fav_crud, "add_favorite", lambda db, uid, sid: False)
    resp = as_user.post(f"/api/v1/favorites/{SITE_ID}")
    assert resp.status_code == status.HTTP_400_BAD_REQUEST


# ---------------------------------------------------------------------------
# Remove
# ---------------------------------------------------------------------------
def test_user_can_remove_favorite(as_user, patch_favorites_crud):
    resp = as_user.delete(f"/api/v1/favorites/{SITE_ID}")
    assert resp.status_code == status.HTTP_200_OK
    body = resp.json()
    assert "removed" in body["message"].lower()


def test_remove_favorite_fails_when_crud_returns_false(as_user, patch_favorites_crud, monkeypatch):
    import app.crud.favorites as fav_crud
    monkeypatch.setattr(fav_crud, "remove_favorite", lambda db, uid, sid: False)
    resp = as_user.delete(f"/api/v1/favorites/{SITE_ID}")
    assert resp.status_code == status.HTTP_400_BAD_REQUEST


# ---------------------------------------------------------------------------
# List
# ---------------------------------------------------------------------------
def test_user_can_list_favorites(as_user, patch_favorites_crud):
    resp = as_user.get("/api/v1/favorites")
    assert resp.status_code == status.HTTP_200_OK
    body = resp.json()
    assert isinstance(body, list)
    assert len(body) >= 1
    assert "name" in body[0]


def test_admin_can_list_favorites(as_admin, patch_favorites_crud):
    resp = as_admin.get("/api/v1/favorites")
    assert resp.status_code == status.HTTP_200_OK
    assert isinstance(resp.json(), list)


def test_reviewer_can_list_favorites(as_reviewer, patch_favorites_crud):
    resp = as_reviewer.get("/api/v1/favorites")
    assert resp.status_code == status.HTTP_200_OK
