"""
Tests for the heritage-site endpoints:
  GET    /api/v1/heritage-sites              (public)
  GET    /api/v1/heritage-sites/secured      (admin/reviewer)
  GET    /api/v1/heritage-sites/{site_id}    (public)
  PUT    /api/v1/heritage-sites/{site_id}    (admin)
  DELETE /api/v1/heritage-sites/{site_id}    (admin)
"""
import pytest
from fastapi import status


# ---------------------------------------------------------------------------
# Public list
# ---------------------------------------------------------------------------
def test_public_list_sites_returns_list(client, patch_heritage_crud):
    """Anyone can list public heritage sites."""
    resp = client.get("/api/v1/heritage-sites")
    assert resp.status_code == status.HTTP_200_OK
    assert isinstance(resp.json(), list)
    assert len(resp.json()) == 2


def test_public_list_sites_with_filters(client, patch_heritage_crud):
    resp = client.get("/api/v1/heritage-sites?region=Kathmandu&category=temple&q=temple")
    assert resp.status_code == status.HTTP_200_OK
    assert isinstance(resp.json(), list)


# ---------------------------------------------------------------------------
# Secured list (admin/reviewer)
# ---------------------------------------------------------------------------
def test_user_cannot_access_secured_sites(as_user, patch_heritage_crud):
    resp = as_user.get("/api/v1/heritage-sites/secured")
    assert resp.status_code == status.HTTP_403_FORBIDDEN


def test_reviewer_can_access_secured_sites(as_reviewer, patch_heritage_crud):
    resp = as_reviewer.get("/api/v1/heritage-sites/secured")
    assert resp.status_code == status.HTTP_200_OK
    assert isinstance(resp.json(), list)


def test_admin_can_access_secured_sites(as_admin, patch_heritage_crud):
    resp = as_admin.get("/api/v1/heritage-sites/secured")
    assert resp.status_code == status.HTTP_200_OK


# ---------------------------------------------------------------------------
# Get by ID
# ---------------------------------------------------------------------------
def test_get_site_by_id_success(client, patch_heritage_crud):
    site_id = "11111111-1111-1111-1111-111111111111"
    resp = client.get(f"/api/v1/heritage-sites/{site_id}")
    assert resp.status_code == status.HTTP_200_OK
    body = resp.json()
    assert "id" in body or "public_id" in body


def test_get_site_by_id_not_found(client, patch_heritage_crud, monkeypatch):
    """When CRUD returns None, endpoint must return 404."""
    import app.crud.heritage_site as heritage_crud
    monkeypatch.setattr(heritage_crud, "get_site_by_id", lambda db, sid: None)
    resp = client.get("/api/v1/heritage-sites/11111111-1111-1111-1111-111111111111")
    assert resp.status_code == status.HTTP_404_NOT_FOUND


# ---------------------------------------------------------------------------
# Update (admin)
# ---------------------------------------------------------------------------
def test_user_cannot_update_site(as_user, patch_heritage_crud):
    resp = as_user.put(
        "/api/v1/heritage-sites/11111111-1111-1111-1111-111111111111",
        json={
            "name": "Hacked",
            "description": "no",
            "category": "temple",
            "region": "X",
            "latitude": 0,
            "longitude": 0,
        },
    )
    assert resp.status_code == status.HTTP_403_FORBIDDEN


def test_admin_can_update_site(as_admin, patch_heritage_crud):
    resp = as_admin.put(
        "/api/v1/heritage-sites/11111111-1111-1111-1111-111111111111",
        json={
            "name": "Updated Site",
            "description": "Updated",
            "category": "temple",
            "region": "Bhaktapur",
            "latitude": 27.67,
            "longitude": 85.42,
        },
    )
    assert resp.status_code == status.HTTP_200_OK


# ---------------------------------------------------------------------------
# Delete (admin)
# ---------------------------------------------------------------------------
def test_reviewer_cannot_delete_site(as_reviewer, patch_heritage_crud):
    resp = as_reviewer.delete("/api/v1/heritage-sites/11111111-1111-1111-1111-111111111111")
    assert resp.status_code == status.HTTP_403_FORBIDDEN


def test_admin_can_soft_delete_site(as_admin, patch_heritage_crud):
    resp = as_admin.delete("/api/v1/heritage-sites/11111111-1111-1111-1111-111111111111")
    assert resp.status_code == status.HTTP_200_OK
    assert "deleted" in resp.json()["message"].lower()
