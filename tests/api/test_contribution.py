"""
Tests for the contribution workflow:
  POST   /api/v1/contributions                  (any user)
  GET    /api/v1/contributions/me               (any user, own)
  PUT    /api/v1/contributions/{id}             (owner, only if pending)
  DELETE /api/v1/contributions/{id}             (owner, only if pending)
  GET    /api/v1/contributions                  (admin/reviewer)
  POST   /api/v1/contributions/{id}/approve     (admin)
  POST   /api/v1/contributions/{id}/reject      (admin)
  POST   /api/v1/contributions/{id}/resubmit    (owner, only if rejected)
"""
import pytest
import uuid
from fastapi import status


SAMPLE_PAYLOAD = {
    "name": "Basantapur Temple",
    "description": "Historic temple in Kathmandu",
    "category": "temple",
    "region": "Kathmandu",
    "latitude": 27.7,
    "longitude": 85.3,
    "tags": ["heritage", "temple"],
}


# ---------------------------------------------------------------------------
# Create contribution (any authenticated user)
# ---------------------------------------------------------------------------
def test_user_can_create_contribution(as_user, patch_contrib_crud):
    resp = as_user.post("/api/v1/contributions", json=SAMPLE_PAYLOAD)
    assert resp.status_code == status.HTTP_200_OK
    body = resp.json()
    # FakeContribution default name is "Test Contribution"
    assert body["name"] == "Test Contribution"
    assert body["status"] == "pending"


def test_create_contribution_rejects_http_image(as_user, patch_contrib_crud):
    """Image URLs must be HTTPS, not HTTP."""
    bad_payload = {**SAMPLE_PAYLOAD, "image_url": "http://insecure.example.com/x.jpg"}
    resp = as_user.post("/api/v1/contributions", json=bad_payload)
    assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_create_contribution_rejects_ftp_scheme(as_user, patch_contrib_crud):
    bad_payload = {**SAMPLE_PAYLOAD, "image_url": "ftp://server/x.jpg"}
    resp = as_user.post("/api/v1/contributions", json=bad_payload)
    assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_create_contribution_accepts_https_image(as_user, patch_contrib_crud):
    good_payload = {**SAMPLE_PAYLOAD, "image_url": "https://cdn.example.com/x.jpg"}
    resp = as_user.post("/api/v1/contributions", json=good_payload)
    assert resp.status_code == status.HTTP_200_OK


# ---------------------------------------------------------------------------
# /me - list own contributions
# ---------------------------------------------------------------------------
def test_user_can_list_own_contributions(as_user, patch_contrib_crud):
    resp = as_user.get("/api/v1/contributions/me")
    assert resp.status_code == status.HTTP_200_OK
    assert isinstance(resp.json(), list)


def test_user_can_list_own_by_status(as_user, patch_contrib_crud):
    resp = as_user.get("/api/v1/contributions/me?status=pending")
    assert resp.status_code == status.HTTP_200_OK


# ---------------------------------------------------------------------------
# Update / Delete own contribution
# ---------------------------------------------------------------------------
def test_user_can_update_own_pending_contribution(as_user, patch_contrib_crud):
    # NOTE: PUT route uses int (not UUID) for contrib_id
    resp = as_user.put(
        "/api/v1/contributions/1",
        json={"name": "Updated Name"},
    )
    assert resp.status_code == status.HTTP_200_OK


def test_user_can_delete_own_pending_contribution(as_user, patch_contrib_crud):
    cid = "11111111-1111-1111-1111-111111111111"
    resp = as_user.delete(f"/api/v1/contributions/{cid}")
    assert resp.status_code == status.HTTP_200_OK
    assert "deleted" in resp.json()["message"].lower()


# ---------------------------------------------------------------------------
# Admin/Reviewer listing
# ---------------------------------------------------------------------------
def test_user_cannot_list_all_contributions(as_user, patch_contrib_crud):
    resp = as_user.get("/api/v1/contributions")
    assert resp.status_code == status.HTTP_403_FORBIDDEN


def test_reviewer_can_list_all_contributions(as_reviewer, patch_contrib_crud):
    resp = as_reviewer.get("/api/v1/contributions")
    assert resp.status_code == status.HTTP_200_OK
    assert isinstance(resp.json(), list)


def test_admin_can_list_all_contributions(as_admin, patch_contrib_crud):
    resp = as_admin.get("/api/v1/contributions")
    assert resp.status_code == status.HTTP_200_OK


# ---------------------------------------------------------------------------
# Approve / Reject (admin only)
# ---------------------------------------------------------------------------
def test_reviewer_cannot_approve(as_reviewer, patch_contrib_crud):
    cid = "11111111-1111-1111-1111-111111111111"
    resp = as_reviewer.post(
        f"/api/v1/contributions/{cid}/approve",
        json={"comment": "Looks good"},
    )
    assert resp.status_code == status.HTTP_403_FORBIDDEN


def test_reviewer_cannot_reject(as_reviewer, patch_contrib_crud):
    cid = "11111111-1111-1111-1111-111111111111"
    resp = as_reviewer.post(
        f"/api/v1/contributions/{cid}/reject",
        json={"reason": "bad"},
    )
    assert resp.status_code == status.HTTP_403_FORBIDDEN


def test_admin_can_approve_contribution(as_admin, patch_contrib_crud):
    cid = "22222222-2222-2222-2222-222222222222"
    resp = as_admin.post(
        f"/api/v1/contributions/{cid}/approve",
        json={"comment": "Looks good"},
    )
    assert resp.status_code == status.HTTP_200_OK
    body = resp.json()
    assert body["message"] == "Approved"
    # The endpoint echoes the UUID string from the URL path
    assert body["contribution_id"] == cid


def test_admin_can_reject_contribution(as_admin, patch_contrib_crud):
    cid = "33333333-3333-3333-3333-333333333333"
    resp = as_admin.post(
        f"/api/v1/contributions/{cid}/reject",
        json={"reason": "Insufficient evidence"},
    )
    assert resp.status_code == status.HTTP_200_OK
    body = resp.json()
    # body here is the ContributionOut of the rejected row
    assert body["rejection_reason"] == "Insufficient evidence"
    assert body["status"] == "rejected"


def test_admin_reject_without_reason_returns_400(as_admin, patch_contrib_crud):
    cid = "33333333-3333-3333-3333-333333333333"
    resp = as_admin.post(
        f"/api/v1/contributions/{cid}/reject",
        json={},
    )
    assert resp.status_code == status.HTTP_400_BAD_REQUEST


# ---------------------------------------------------------------------------
# Resubmit
# ---------------------------------------------------------------------------
def test_user_can_resubmit_rejected_contribution(as_user, patch_contrib_crud):
    cid = "44444444-4444-4444-4444-444444444444"
    resp = as_user.post(
        f"/api/v1/contributions/{cid}/resubmit",
        json={"name": "Better Name"},
    )
    assert resp.status_code == status.HTTP_200_OK
