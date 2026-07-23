"""
Tests for the notification endpoints:
  GET  /api/v1/notifications
  POST /api/v1/notifications/read
  GET  /api/v1/notifications/unread-count
  POST /api/v1/notifications/read-all
"""
import pytest
from fastapi import status


# ---------------------------------------------------------------------------
# List
# ---------------------------------------------------------------------------
def test_user_can_list_own_notifications(as_user, patch_notifications_crud):
    resp = as_user.get("/api/v1/notifications")
    assert resp.status_code == status.HTTP_200_OK
    body = resp.json()
    assert isinstance(body, list)
    assert len(body) == 2


def test_list_notifications_requires_auth(client, patch_notifications_crud):
    resp = client.get("/api/v1/notifications")
    assert resp.status_code in (401, 403)


def test_admin_can_list_notifications(as_admin, patch_notifications_crud):
    resp = as_admin.get("/api/v1/notifications")
    assert resp.status_code == status.HTTP_200_OK
    assert isinstance(resp.json(), list)


# ---------------------------------------------------------------------------
# Mark specific as read
# ---------------------------------------------------------------------------
def test_user_can_mark_notifications_read(as_user, patch_notifications_crud):
    # Body must be {"ids": [1,2,3]} because the endpoint uses embed=True
    resp = as_user.post("/api/v1/notifications/read", json={"ids": [1, 2, 3]})
    assert resp.status_code == status.HTTP_200_OK
    body = resp.json()
    assert body["updated"] == 3


def test_mark_read_with_empty_list(as_user, patch_notifications_crud):
    resp = as_user.post("/api/v1/notifications/read", json={"ids": []})
    assert resp.status_code == status.HTTP_200_OK
    body = resp.json()
    assert body["updated"] == 0


def test_mark_read_requires_auth(client, patch_notifications_crud):
    resp = client.post("/api/v1/notifications/read", json={"ids": [1]})
    assert resp.status_code in (401, 403)


# ---------------------------------------------------------------------------
# Unread count
# ---------------------------------------------------------------------------
def test_user_can_get_unread_count(as_user, patch_notifications_crud):
    resp = as_user.get("/api/v1/notifications/unread-count")
    assert resp.status_code == status.HTTP_200_OK
    body = resp.json()
    assert "count" in body
    assert body["count"] >= 0


# ---------------------------------------------------------------------------
# Mark all read
# ---------------------------------------------------------------------------
def test_user_can_mark_all_read(as_user, patch_notifications_crud):
    resp = as_user.post("/api/v1/notifications/read-all")
    assert resp.status_code == status.HTTP_200_OK
    body = resp.json()
    assert "updated" in body
    assert body["updated"] >= 0


def test_mark_all_read_requires_auth(client, patch_notifications_crud):
    resp = client.post("/api/v1/notifications/read-all")
    assert resp.status_code in (401, 403)
