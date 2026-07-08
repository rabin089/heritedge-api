from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict, UUID4
from app.models.festival import FestivalStatus, FestivalCategory


class LatLng(BaseModel):
    lat: float = Field(..., ge=-90, le=90)
    lng: float = Field(..., ge=-180, le=180)


class FestivalBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    significance: Optional[str] = None
    
    start_date: datetime
    end_date: datetime
    nepali_date: Optional[str] = None
    
    region: Optional[str] = None
    is_location_specific: bool = False
    location_name: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    locations: Optional[List[LatLng]] = None
    
    category: Optional[FestivalCategory] = None
    tags: Optional[List[str]] = None
    
    main_image: Optional[str] = None
    gallery: Optional[List[str]] = None
    
    is_annual: bool = False


class FestivalCreate(FestivalBase):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Spring Heritage Festival",
                "description": "Annual celebration of local cultural heritage",
                "significance": "Marks the beginning of spring season",
                "category": "Cultural",
                "region": "Kathmandu",
                "is_location_specific": True,
                "location_name": "Kathmandu Durbar Square",
                "latitude": 27.7061,
                "longitude": 85.3301,
                "locations": [{"lat": 27.7061, "lng": 85.3301}],
                "start_date": "2026-04-15T10:00:00Z",
                "end_date": "2026-04-17T18:00:00Z",
                "nepali_date": "2083-01-02",
                "main_image": "https://example.com/festival.jpg",
                "gallery": ["https://example.com/festival1.jpg", "https://example.com/festival2.jpg"],
                "tags": ["heritage", "culture", "spring", "traditional"],
                "is_annual": True
            }
        }
    )


class FestivalUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    significance: Optional[str] = None
    
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    nepali_date: Optional[str] = None
    
    region: Optional[str] = None
    is_location_specific: Optional[bool] = None
    location_name: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    locations: Optional[List[LatLng]] = None
    
    category: Optional[FestivalCategory] = None
    tags: Optional[List[str]] = None
    
    main_image: Optional[str] = None
    gallery: Optional[List[str]] = None
    
    is_annual: Optional[bool] = None
    status: Optional[FestivalStatus] = None


class FestivalOut(FestivalBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID4
    status: FestivalStatus
    moderation_note: Optional[str] = None
    
    created_at: datetime
    created_by: UUID4
    contributor_id: UUID4
    contributor_name: str = "Anonymous"
    distance_km: Optional[float] = None
    
    # Relationships if needed to be embedded, usually handled separately not to bloat
    # but based on previous schema, we keep it simple.


class FestivalApproval(BaseModel):
    is_approved: bool = True  # defaults to approve
    status: Optional[FestivalStatus] = FestivalStatus.approved  # defaults to approved
    rejection_reason: Optional[str] = None


class FestivalHeritageSiteBase(BaseModel):
    relationship_type: Optional[str] = "hosted_at"
    notes: Optional[str] = None


class FestivalHeritageSiteCreate(FestivalHeritageSiteBase):
    festival_id: UUID4
    heritage_site_id: UUID4


class FestivalHeritageSiteOut(FestivalHeritageSiteBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID4
    festival_id: UUID4
    heritage_site_id: UUID4
    created_at: datetime
    created_by: str # In model creation is by user ID string or UUID? 
    # FestivalHeritageSite model has created_by = Column(String). So str is correct.


# Paginated response for festival listings
class FestivalListResponse(BaseModel):
    items: List[FestivalOut]
    total: int
    page: int
    page_size: int
