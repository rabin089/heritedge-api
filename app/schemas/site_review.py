from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from uuid import UUID
from datetime import datetime


class SiteReviewCreate(BaseModel):
    site_id: UUID = Field(..., description="Site UUID")
    comment: str = Field(..., min_length=1, max_length=1000)
    rating: int = Field(..., ge=0, le=10, description="Rating from 0 to 10")

    @field_validator('rating')
    @classmethod
    def validate_rating(cls, v):
        if v < 0 or v > 10:
            raise ValueError('Rating must be between 0 and 10')
        return v

    class Config:
        from_attributes = True


class SiteReviewUpdate(BaseModel):
    comment: Optional[str] = Field(None, min_length=1, max_length=1000)
    rating: Optional[int] = Field(None, ge=0, le=10, description="Rating from 0 to 10")

    @field_validator('rating')
    @classmethod
    def validate_rating(cls, v):
        if v is not None and (v < 0 or v > 10):
            raise ValueError('Rating must be between 0 and 10')
        return v

    class Config:
        from_attributes = True


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
        if v < 0 or v > 10:
            raise ValueError('Rating must be between 0 and 10')
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

    class Config:
        from_attributes = True


class PopularSite(BaseModel):
    id: UUID
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
    id: UUID
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


# ==================== ADMIN REVIEW MANAGEMENT SCHEMAS ====================

class AdminReviewUpdate(BaseModel):
    comment: Optional[str] = Field(None, min_length=1, max_length=1000)
    rating: Optional[int] = Field(None, ge=0, le=10, description="Rating from 0 to 10")

    @field_validator('rating')
    @classmethod
    def validate_rating(cls, v):
        if v is not None and (v < 0 or v > 10):
            raise ValueError('Rating must be between 0 and 10')
        return v

    class Config:
        from_attributes = True


class AdminRatingUpdate(BaseModel):
    rating: int = Field(..., ge=0, le=10, description="Rating from 0 to 10")

    @field_validator('rating')
    @classmethod
    def validate_rating(cls, v):
        if v < 0 or v > 10:
            raise ValueError('Rating must be between 0 and 10')
        return v

    class Config:
        from_attributes = True


class AdminAuditInfo(BaseModel):
    deleted_by: str
    deleted_at: datetime
    original_review: Optional[dict] = None
    original_rating: Optional[dict] = None

    class Config:
        from_attributes = True


class AdminReviewUpdateResponse(BaseModel):
    review: SiteReviewOut
    original_values: dict

    class Config:
        from_attributes = True


class AdminRatingUpdateResponse(BaseModel):
    rating: SiteRatingOut
    original_value: int

    class Config:
        from_attributes = True


class AdminReviewStats(BaseModel):
    total_reviews: int
    total_ratings: int
    average_review_rating: float
    average_rating_value: float
    review_distribution: List[dict]
    top_reviewers: List[dict]
    most_reviewed_sites: List[dict]

    class Config:
        from_attributes = True


class AdminReviewList(BaseModel):
    reviews: List[SiteReviewOut]
    total: int
    page: int
    page_size: int

    class Config:
        from_attributes = True


class AdminRatingList(BaseModel):
    ratings: List[SiteRatingOut]
    total: int
    page: int
    page_size: int

    class Config:
        from_attributes = True
