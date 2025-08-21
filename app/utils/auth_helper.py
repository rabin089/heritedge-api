# app/utils/auth_helpers.py
from app.models.user import User

def is_admin(user: User) -> bool:
    return user.is_admin
