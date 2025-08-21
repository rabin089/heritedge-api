from fastapi import APIRouter, Depends, HTTPException, Body
from typing import List, Optional
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.api.v1.auth import get_current_user
from app.models.user import User
from app.models.contribution import ContributionStatus
from app.schemas.contribution import (
    ContributionCreate, ContributionUpdate, ContributionOut,
    RejectContributionIn, ApproveContributionOut, ApproveContributionIn
)
from app.crud import contributions as crud
from ._role import is_admin  # or define locally

router = APIRouter(prefix="/contributions", tags=["contributions"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# user: create contribution
@router.post("", response_model=ContributionOut)
def create_contribution(
    payload: ContributionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Store creator as email (created_by is a String column)
    row = crud.create_contribution(db, payload, user_id=current_user.email)
    return row


# user: list my contributions
@router.get("/me", response_model=List[ContributionOut])
def my_contributions(
    status: Optional[ContributionStatus] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return crud.list_my_contributions(db, current_user.email, status)


# user: update my pending contribution
@router.put("/{contrib_id}", response_model=ContributionOut)
def update_my_contribution(
    contrib_id: int,
    payload: ContributionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    row = crud.update_my_pending_contribution(db, contrib_id, current_user.email, payload)
    if not row:
        raise HTTPException(status_code=403, detail="Cannot update: not found or not pending")
    return row


# user: delete my pending contribution
@router.delete("/{contrib_id}")
def delete_my_contribution(
    contrib_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    row = crud.delete_my_pending_contribution(db, contrib_id, current_user.email)
    if not row:
        raise HTTPException(status_code=403, detail="Cannot delete: not found or not pending")
    return {"message": "Contribution deleted"}


# admin: list all
@router.get("", response_model=List[ContributionOut])
def list_contributions(
    status: Optional[ContributionStatus] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not is_admin(current_user):
        raise HTTPException(status_code=403, detail="Admin only")
    return crud.list_all_contributions(db, status)


# admin: approve
@router.post("/{contrib_id}/approve", response_model=ApproveContributionOut)
def approve_contribution(
    contrib_id: int,
    payload: ApproveContributionIn = Body(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not is_admin(current_user):
        raise HTTPException(status_code=403, detail="Admin only")
    comment = payload.comment if payload else None
    result = crud.approve_contribution(db, contrib_id, admin_user_id=current_user.id, comment=comment)
    if not result:
        raise HTTPException(status_code=400, detail="Contribution not found or not pending")
    contrib, site = result
    return {"message": "Approved", "contribution_id": contrib.id, "heritage_site_id": site.id}


# admin: reject
@router.post("/{contrib_id}/reject", response_model=ContributionOut)
def reject_contribution(
    contrib_id: int,
    payload: RejectContributionIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not is_admin(current_user):
        raise HTTPException(status_code=403, detail="Admin only")
    if not payload or not payload.reason:
        raise HTTPException(status_code=422, detail="Rejection reason is required")
    row = crud.reject_contribution(db, contrib_id, payload.reason)
    if not row:
        raise HTTPException(status_code=400, detail="Contribution not found or not pending")
    return row


# user: resubmit a rejected contribution (optional update data)
@router.post("/{contrib_id}/resubmit", response_model=ContributionOut)
def resubmit_contribution(
    contrib_id: int,
    payload: Optional[ContributionUpdate] = Body(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    row = crud.resubmit_rejected_contribution(db, contrib_id, current_user.email, payload)
    if not row:
        raise HTTPException(status_code=403, detail="Cannot resubmit: not found or not rejected")
    return row
