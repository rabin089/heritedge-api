from pydantic import BaseModel, EmailStr, field_validator
from typing import Literal, Optional
from uuid import UUID
from datetime import datetime

class UserCreate(BaseModel):
    email: EmailStr
    password: Optional[str] = None  # Optional for OAuth users
    name: Optional[str] = ""  # From Google/other providers
    profile_photo_url: Optional[str] = None
    auth_provider: str = "email"  # email, google, firebase, etc.

class AdminCreate(UserCreate):
    role: Literal["user", "admin", "superadmin", "reviewer"] = "user"

class UserOut(BaseModel):
    id: UUID
    email: EmailStr
    name: Optional[str] = ""  # From Google/other providers
    display_name: Optional[str] = ""  # For admin identity
    profile_photo_url: Optional[str] = None
    auth_provider: str = "email"
    is_active: bool
    is_admin: bool
    role: str
    account_created_at: datetime
    last_login_at: Optional[datetime] = None

    @field_validator('name', 'display_name', mode='before')
    @classmethod
    def empty_string_for_none(cls, v):
        return v if v is not None else ""

    class Config:
        from_attributes = True


class RoleUpdate(BaseModel):
    role: Literal["user", "admin", "superadmin", "reviewer"]


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str


class FirebaseLoginRequest(BaseModel):
    id_token: str


class AccountLinkingRequest(BaseModel):
    id_token: str
    email: EmailStr
    password: str