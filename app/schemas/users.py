from pydantic import BaseModel, EmailStr
from typing import Literal
from uuid import UUID

class UserCreate(BaseModel):
    email: EmailStr
    password: str

class AdminCreate(UserCreate):
    role: Literal["user", "admin", "superadmin", "reviewer"] = "user"

class UserOut(BaseModel):
    id: UUID
    email: EmailStr
    is_active: bool
    is_admin: bool
    role: str

    class Config:
        from_attributes = True


class RoleUpdate(BaseModel):
    role: Literal["user", "admin", "superadmin", "reviewer"]


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str