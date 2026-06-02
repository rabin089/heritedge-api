from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from uuid import UUID
from .users import UserMinimal


class IntangibleMediaSchema(BaseModel):
    id: UUID
    media_type: str
    media_url: str
    duration_seconds: Optional[int] = None

    class Config:
        from_attributes = True


class IntangibleHeritageBase(BaseModel):
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    community: Optional[str] = None
    language: Optional[str] = None
    risk_level: Optional[str] = None
    location_id: Optional[UUID] = None
    practiced_at: Optional[str] = None


class IntangibleHeritageCreate(IntangibleHeritageBase):
    pass


class IntangibleHeritageOut(IntangibleHeritageBase):
    id: UUID
    created_at: datetime
    created_by: str
    status: str
    media: List[IntangibleMediaSchema] = []
    creator_details: Optional[UserMinimal] = None

    class Config:
        from_attributes = True
