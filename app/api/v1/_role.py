from app.models.user import User
from fastapi import Depends, HTTPException
from typing import Callable

ADMIN_ROLES = {"admin", "superadmin"}
REVIEWER_ROLES = {"reviewer"}

def is_admin(user: User) -> bool:
    # Prefer explicit role if present; fallback to legacy boolean flag
    role = getattr(user, "role", None)
    if role is not None:
        return role in ADMIN_ROLES
    return bool(getattr(user, "is_admin", False))

def is_superadmin(user: User) -> bool:
    role = getattr(user, "role", None)
    return role == "superadmin"

def is_reviewer(user: User) -> bool:
    role = getattr(user, "role", None)
    return role in REVIEWER_ROLES


def require_role(*allowed_roles: str) -> Callable:
    """FastAPI dependency factory to require specific user roles."""
    def role_checker(user: User = Depends()) -> User:
        if user.role not in allowed_roles:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return user
    return role_checker
