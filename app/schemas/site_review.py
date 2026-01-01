from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from datetime import datetime
from uuid import UUID


class SiteReviewCreate(BaseModel):
    site_id: UUID = Field(..., description="Site UUID")
    comment: str = Field(..., min_length=1, max_length=1000)
    rating: int = Field(..., ge=0, le=10, description="Rating from 0 to 10")

    @field_validator('rating')
    @classmethod
    def validate_rating(cls, v):
        if not isinstance(v, int) or v < 0 or v > 10:
            raise ValueError('Rating must be an integer between 0 and 10')
        return v


class SiteReviewUpdate(BaseModel):
    comment: Optional[str] = Field(None, min_length=1, max_length=1000)
    rating: Optional[int] = Field(None, ge=0, le=10)

    @field_validator('rating')
    @classmethod
    def validate_rating(cls, v):
        if v is not None and (not isinstance(v, int) or v < 0 or v > 10):
            raise ValueError('Rating must be an integer between 0 and 10')
        return v


class SiteReviewOut(BaseModel):
    id: UUID
    site_id: UUID
    user_email: str
    rating: int
    comment: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SiteRatingCreate(BaseModel):
    site_id: UUID = Field(..., description="Site UUID")
    rating: int = Field(..., ge=0, le=10, description="Rating from 0 to 10")

    @field_validator('rating')
    @classmethod
    def validate_rating(cls, v):
        if not isinstance(v, int) or v < 0 or v > 10:
            raise ValueError('Rating must be an integer between 0 and 10')
        return v


class SiteRatingOut(BaseModel):
    id: UUID
    site_id: UUID
    user_email: str
    rating: int
    created_at: datetime

    class Config:
        from_attributes = True


class SiteReviewStats(BaseModel):
    average_rating: Optional[float] = None
    total_reviews: int = 0
    total_ratings: int = 0
    user_has_reviewed: bool = False
    user_rating: Optional[int] = None


class PopularSite(BaseModel):
    id: UUID
    public_id: UUID
    name: str
    category: Optional[str] = None
    region: Optional[str] = None
    image_url: Optional[str] = None
    average_rating: Optional[float] = None
    total_reviews: int = 0
    total_ratings: int = 0

    class Config:
        from_attributes = True


class HeritageSiteWithReviews(BaseModel):
    # Basic heritage site fields
    id: int
    public_id: UUID
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    region: Optional[str] = None
    location: Optional[str] = None
    image_url: Optional[str] = None
    tags: Optional[List[str]] = None
    created_at: datetime
    
    # Review and rating stats
    average_rating: Optional[float] = None
    total_reviews: int = 0
    total_ratings: int = 0
    user_has_reviewed: bool = False
    user_rating: Optional[int] = None

    class Config:
        from_attributes = True
