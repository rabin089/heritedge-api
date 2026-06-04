# pyrefly: ignore [missing-import]
from fastapi import status


def test_reviewer_can_view_contributions(as_reviewer, patch_contrib_crud):
    resp = as_reviewer.get("/contributions")
    assert resp.status_code == status.HTTP_200_OK
    assert isinstance(resp.json(), list)


def test_reviewer_cannot_approve_or_reject(as_reviewer, patch_contrib_crud):
    resp_a = as_reviewer.post("/contributions/11111111-1111-1111-1111-111111111111/approve", json={"comment": "ok"})
    resp_r = as_reviewer.post("/contributions/11111111-1111-1111-1111-111111111111/reject", json={"reason": "bad"})
    assert resp_a.status_code == status.HTTP_403_FORBIDDEN
    assert resp_r.status_code == status.HTTP_403_FORBIDDEN


def test_admin_can_approve_and_reject(as_admin, patch_contrib_crud):
    resp_a = as_admin.post("/contributions/22222222-2222-2222-2222-222222222222/approve", json={"comment": "ok"})
    assert resp_a.status_code == status.HTTP_200_OK
    body = resp_a.json()
    assert body["message"] == "Approved"
    assert body["contribution_id"] == "22222222-2222-2222-2222-222222222222"

    resp_r = as_admin.post("/contributions/33333333-3333-3333-3333-333333333333/reject", json={"reason": "bad"})
    assert resp_r.status_code == status.HTTP_200_OK
    assert resp_r.json()["id"] == "33333333-3333-3333-3333-333333333333"


def test_user_cannot_list_all_contributions(as_user, patch_contrib_crud):
    resp = as_user.get("/contributions")
    assert resp.status_code == status.HTTP_403_FORBIDDEN


def test_reviewer_can_view_secured_sites(as_reviewer, patch_heritage_crud):
    resp = as_reviewer.get("/heritage-sites/secured")
    assert resp.status_code == status.HTTP_200_OK
    assert isinstance(resp.json(), list)


def test_reviewer_cannot_delete_site(as_reviewer, patch_heritage_crud):
    resp = as_reviewer.delete("/heritage-sites/11111111-1111-1111-1111-111111111111")
    assert resp.status_code == status.HTTP_403_FORBIDDEN


def test_admin_can_soft_delete_site(as_admin, patch_heritage_crud):
    resp = as_admin.delete("/heritage-sites/11111111-1111-1111-1111-111111111111")
    assert resp.status_code == status.HTTP_200_OK
    assert resp.json()["message"].lower().startswith("heritage site deleted")
