from pydantic import BaseModel, field_validator
from typing import List, Optional
from datetime import datetime
from app.models.contribution import ContributionStatus, ContributionType
from uuid import UUID
from .users import UserMinimal


class ContributionBase(BaseModel):
    type: ContributionType = ContributionType.site
    name: str
    name_np: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    region: Optional[str] = None
    location: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    image_url: Optional[str] = None
    secondary_images: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    festival_id: Optional[UUID] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    significance: Optional[str] = None
    nepali_date: Optional[str] = None
    is_annual: Optional[bool] = None

    # Intangible Heritage fields
    community: Optional[str] = None
    language: Optional[str] = None
    risk_level: Optional[str] = None
    practiced_at: Optional[str] = None
    video_url: Optional[str] = None
    audio_url: Optional[str] = None

    @field_validator('is_annual', mode='before')
    @classmethod
    def convert_none_to_false(cls, v):
        return False if v is None else v


class ContributionCreate(ContributionBase):
    contributor_name: Optional[str] = None
    contributor_email: Optional[str] = None


class ContributionUpdate(ContributionBase):
    # allow partial update
    name: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    festival_id: Optional[UUID] = None


class ContributionOut(ContributionBase):
    id: UUID
    status: ContributionStatus
    status_reason: Optional[str] = None
    rejection_reason: Optional[str] = None
    created_at: datetime
    created_by: str
    contributor_name: Optional[str] = None
    contributor_email: Optional[str] = None
    creator_details: Optional[UserMinimal] = None

    # if approved, there may be a related site id
    class Config:
        from_attributes = True


class ApproveContributionIn(BaseModel):
    comment: Optional[str] = None


class RejectContributionIn(BaseModel):
    reason: Optional[str] = None


class ApproveContributionOut(BaseModel):
    message: str
    contribution_id: UUID
    heritage_site_id: Optional[UUID] = None
    festival_id: Optional[UUID] = None
    intangible_id: Optional[UUID] = None
