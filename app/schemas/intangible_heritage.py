from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from datetime import datetime
from uuid import UUID
from decimal import Decimal
from app.schemas.users import UserMinimal


# Media Schemas
class IntangibleMediaBase(BaseModel):
    media_type: str = Field(..., pattern="^(video|audio|photo)$")
    media_url: str
    file_size_mb: Decimal
    duration_seconds: Optional[int] = None
    mime_type: str
    width: Optional[int] = None
    height: Optional[int] = None
    thumbnail_url: Optional[str] = None
    processing_status: Optional[str] = "uploaded"

class IntangibleMediaCreate(IntangibleMediaBase):
    sort_order: Optional[int] = 0

class IntangibleMediaOut(IntangibleMediaBase):
    id: UUID
    intangible_id: UUID
    uploaded_by: Optional[UUID] = None
    created_at: datetime
    processed_at: Optional[datetime] = None
    sort_order: int

    model_config = ConfigDict(from_attributes=True)


# Heritage Schemas
class IntangibleHeritageBase(BaseModel):
    name_np: str = Field(..., min_length=3, max_length=255)
    name_en: str = Field(..., min_length=3, max_length=255)
    description: str = Field(..., min_length=20)
    category: str = Field(..., pattern="^(music|dance|ritual|craft|food|language|other)$")
    community: Optional[str] = Field(None, max_length=100)
    language: Optional[str] = Field(None, max_length=100)
    location_id: Optional[UUID] = None
    practiced_at_description: Optional[str] = Field(None, max_length=255)
    risk_level: str = Field(default="stable", pattern="^(critical|endangered|stable)$")

class IntangibleHeritageCreate(IntangibleHeritageBase):
    # Media URLs — uploaded first via POST /upload/, then included here
    image_url: Optional[str] = None
    secondary_images: Optional[List[str]] = None
    video_url: Optional[str] = None
    audio_url: Optional[str] = None

class IntangibleHeritageUpdate(BaseModel):
    name_np: Optional[str] = Field(None, min_length=3, max_length=255)
    name_en: Optional[str] = Field(None, min_length=3, max_length=255)
    description: Optional[str] = Field(None, min_length=20)
    category: Optional[str] = Field(None, pattern="^(music|dance|ritual|craft|food|language|other)$")
    community: Optional[str] = Field(None, max_length=100)
    language: Optional[str] = Field(None, max_length=100)
    location_id: Optional[UUID] = None
    practiced_at_description: Optional[str] = Field(None, max_length=255)
    risk_level: Optional[str] = Field(None, pattern="^(critical|endangered|stable)$")
    status: Optional[str] = Field(None, pattern="^(draft|pending|approved|rejected|flagged|archived)$")

class IntangibleHeritageOut(IntangibleHeritageBase):
    id: UUID
    contributor_id: UUID
    creator_details: Optional[UserMinimal] = None
    status: str
    approved_by: Optional[UUID] = None
    approval_notes: Optional[str] = None
    rejected_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    approved_at: Optional[datetime] = None
    view_count: int
    favorite_count: int
    engagement_score: Decimal
    media: List[IntangibleMediaOut] = []

    model_config = ConfigDict(from_attributes=True)


# Status updates for Admins
class IntangibleStatusUpdate(BaseModel):
    status: str = Field(..., pattern="^(approved|rejected|flagged|archived)$")
    notes: Optional[str] = None # Either approval_notes or rejected_reason depending on status
