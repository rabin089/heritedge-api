from app.models.user import User

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
