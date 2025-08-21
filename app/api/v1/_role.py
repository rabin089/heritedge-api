from app.models.user import User

ADMIN_ROLES = {"admin", "superadmin"}

def is_admin(user: User) -> bool:
    # Prefer explicit role if present; fallback to legacy boolean flag
    role = getattr(user, "role", None)
    if role is not None:
        return role in ADMIN_ROLES
    return bool(getattr(user, "is_admin", False))
