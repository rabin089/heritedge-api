"""
Admin-only schemas: expose full details including user PII, audit metadata,
and all nested relationships. These must ONLY be used in admin-gated endpoints.
"""
from pydantic import BaseModel
from typing import List, Optional, Any, Dict
from uuid import UUID
from datetime import datetime


# ──────────────────────────────────────────────
#  User full detail (admin view — includes PII)
# ──────────────────────────────────────────────
class AdminUserDetail(BaseModel):
    id: UUID
    email: str                          # PII — admin only
    name: Optional[str] = None
    display_name: Optional[str] = None
    profile_photo_url: Optional[str] = None
    auth_provider: str
    role: str
    is_active: bool
    is_admin: bool
    account_created_at: datetime
    last_login_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ──────────────────────────────────────────────
#  Heritage Site full detail (admin view)
# ──────────────────────────────────────────────
class AdminHeritageSiteDetail(BaseModel):
    id: UUID
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    region: Optional[str] = None
    location: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    image_url: Optional[str] = None
    secondary_images: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    is_pending: bool
    is_deleted: bool

    # Contributor info (full PII for admin)
    created_by: str                     # raw email/id stored in DB
    creator_details: Optional[AdminUserDetail] = None

    # Audit trail
    contribution_id: Optional[UUID] = None
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    updated_by: Optional[str] = None
    updated_at: Optional[datetime] = None
    deleted_by: Optional[str] = None
    deleted_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ──────────────────────────────────────────────
#  Intangible Heritage full detail (admin view)
# ──────────────────────────────────────────────
class AdminIntangibleMediaDetail(BaseModel):
    id: UUID
    media_type: str
    media_url: str
    duration_seconds: Optional[int] = None

    class Config:
        from_attributes = True


class AdminIntangibleHeritageDetail(BaseModel):
    id: UUID
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    community: Optional[str] = None
    language: Optional[str] = None
    risk_level: Optional[str] = None
    location_id: Optional[UUID] = None
    practiced_at: Optional[str] = None
    status: str
    is_deleted: bool

    # Contributor info (full PII for admin)
    created_by: str
    creator_details: Optional[AdminUserDetail] = None

    # Linked staging contribution
    contribution_id: Optional[UUID] = None

    # Media gallery
    media: List[AdminIntangibleMediaDetail] = []

    created_at: datetime

    class Config:
        from_attributes = True


# ──────────────────────────────────────────────
#  Festival full detail (admin view)
# ──────────────────────────────────────────────
class AdminFestivalDetail(BaseModel):
    id: UUID
    name: str
    description: Optional[str] = None
    significance: Optional[str] = None
    start_date: datetime
    end_date: datetime
    nepali_date: Optional[str] = None
    region: Optional[str] = None
    locations: Optional[Any] = None     # JSONB list of LatLng
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    main_image: Optional[str] = None
    gallery: Optional[List[str]] = None
    is_annual: bool
    views_count: int = 0
    date_determination: Optional[str] = None
    last_verified_year: Optional[int] = None

    # Status & moderation
    status: str
    moderation_note: Optional[str] = None

    # Creator — full user detail for admin
    created_by: UUID
    creator_details: Optional[AdminUserDetail] = None    # via festival.user relationship

    created_at: datetime

    # Engagement summary
    story_count: int = 0
    reaction_count: int = 0

    class Config:
        from_attributes = True


class AdminFestivalListResponse(BaseModel):
    items: List[AdminFestivalDetail]
    total: int
    page: int
    page_size: int


# ──────────────────────────────────────────────
#  Contribution full detail (admin view)
# ──────────────────────────────────────────────
class AdminContributionDetail(BaseModel):
    id: UUID
    type: str
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    region: Optional[str] = None
    location: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    image_url: Optional[str] = None
    secondary_images: Optional[List[str]] = None
    tags: Optional[List[str]] = None

    # Festival-specific fields
    festival_id: Optional[UUID] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    significance: Optional[str] = None
    nepali_date: Optional[str] = None
    is_annual: bool = False

    # Intangible-specific fields
    community: Optional[str] = None
    language: Optional[str] = None
    risk_level: Optional[str] = None
    practiced_at: Optional[str] = None
    video_url: Optional[str] = None
    audio_url: Optional[str] = None

    # Status & audit
    status: str
    status_reason: Optional[str] = None
    rejection_reason: Optional[str] = None

    # Contributor full info (admin)
    created_by: str
    contributor_name: Optional[str] = None
    contributor_email: Optional[str] = None
    creator_details: Optional[AdminUserDetail] = None

    # Audit trail
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    updated_by: Optional[str] = None
    updated_at: Optional[datetime] = None
    deleted_by: Optional[str] = None
    deleted_at: Optional[datetime] = None
    is_deleted: bool = False
    created_at: datetime

    class Config:
        from_attributes = True
