from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import SessionLocal
from app.api.v1.auth import get_current_user
from app.models.user import User
from app.core.security import hash_password
from app.schemas.users import UserOut, AdminCreate, RoleUpdate
from ._role import is_superadmin, is_admin, is_reviewer
from app.schemas.contribution import ContributionOut
from app.models.contribution import ContributionStatus
from app.crud import contributions as contrib_crud

router = APIRouter(prefix="/admin", tags=["admin"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# SUPERADMIN: list all users
@router.get("/users", response_model=List[UserOut])
def list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not is_superadmin(current_user):
        raise HTTPException(status_code=403, detail="Superadmin only")
    return db.query(User).order_by(User.id.asc()).all()


# SUPERADMIN: create user with role
@router.post("/users", response_model=UserOut)
def create_user(
    payload: AdminCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not is_superadmin(current_user):
        raise HTTPException(status_code=403, detail="Superadmin only")
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=400, detail="Email already exists")
    user = User(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        is_active=True,
        is_admin=(payload.role in {"admin", "superadmin"}),
        role=payload.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


# SUPERADMIN: update a user's role
@router.put("/users/{user_id}/role", response_model=UserOut)
def update_role(
    user_id: int,
    payload: RoleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not is_superadmin(current_user):
        raise HTTPException(status_code=403, detail="Superadmin only")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.role = payload.role
    user.is_admin = payload.role in {"admin", "superadmin"}
    db.commit()
    db.refresh(user)
    return user


# SUPERADMIN: delete user
@router.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not is_superadmin(current_user):
        raise HTTPException(status_code=403, detail="Superadmin only")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(user)
    db.commit()
    return {"message": "User deleted"}


# ADMIN/REVIEWER: list pending contributions with filters + pagination
@router.get("/contributions/pending")
def list_pending_contributions(
    region: Optional[str] = Query(default=None),
    category: Optional[str] = Query(default=None),
    q: Optional[str] = Query(default=None, description="Fuzzy search over name/region/description/tags"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not (is_admin(current_user) or is_reviewer(current_user)):
        raise HTTPException(status_code=403, detail="Admin or reviewer only")
    items, total = contrib_crud.admin_list_pending_contributions(db, region, category, q, page, page_size)
    # Use ContributionOut for items via FastAPI's response model conversion
    return {
        "items": [ContributionOut.model_validate(i) for i in items],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


# ADMIN/REVIEWER: user contribution history with optional status filter + pagination
@router.get("/user/{user_id}/contributions")
def user_contribution_history(
    user_id: int,
    status: Optional[ContributionStatus] = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not (is_admin(current_user) or is_reviewer(current_user)):
        raise HTTPException(status_code=403, detail="Admin or reviewer only")
    u = db.query(User).filter(User.id == user_id).first()
    if not u:
        raise HTTPException(status_code=404, detail="User not found")
    items, total = contrib_crud.admin_user_contribution_history(db, u.email, page, page_size, status)
    return {
        "user_id": u.id,
        "user_email": u.email,
        "items": [ContributionOut.model_validate(i) for i in items],
        "total": total,
        "page": page,
        "page_size": page_size,
    }
