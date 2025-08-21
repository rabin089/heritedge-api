from pydantic import BaseModel, EmailStr
from typing import Literal

class UserCreate(BaseModel):
    email: EmailStr
    password: str

class AdminCreate(UserCreate):
    role: Literal["user", "admin", "superadmin", "reviewer"] = "user"

class UserOut(BaseModel):
    id: int
    email: EmailStr
    is_active: bool
    is_admin: bool
    role: str

    class Config:
        orm_mode = True


class RoleUpdate(BaseModel):
    role: Literal["user", "admin", "superadmin", "reviewer"]


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str