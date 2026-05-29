from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID
from datetime import datetime


class HeritageSiteBase(BaseModel):
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


class HeritageSiteCreate(HeritageSiteBase):
    pass


class HeritageSiteOut(HeritageSiteBase):
    id: UUID
    created_by: str
    created_at: datetime
    contribution_id: Optional[UUID] = None
    is_pending: bool = False
    contributor_id: Optional[UUID] = None
    contributor_name: str = "Anonymous"

    class Config:
        from_attributes = True
