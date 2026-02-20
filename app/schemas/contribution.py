from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from app.models.contribution import ContributionStatus
from uuid import UUID


class ContributionBase(BaseModel):
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    region: Optional[str] = None
    location: Optional[str] = None
    latitude: float
    longitude: float
    image_url: Optional[str] = None
    secondary_images: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    festival_id: Optional[UUID] = None


class ContributionCreate(ContributionBase):
    pass


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

    # if approved, there may be a related site id
    class Config:
        from_attributes = True


class ApproveContributionIn(BaseModel):
    comment: Optional[str] = None


class RejectContributionIn(BaseModel):
    reason: str


class ApproveContributionOut(BaseModel):
    message: str
    contribution_id: UUID
    heritage_site_id: UUID
