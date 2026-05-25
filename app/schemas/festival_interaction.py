from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID
from datetime import datetime


# Reactions
class FestivalReactionCreate(BaseModel):
    festival_id: UUID = Field(..., description="Festival UUID")
    reaction_type: str = Field(default="heart", description="Type of reaction")

    class Config:
        from_attributes = True


class FestivalReactionOut(BaseModel):
    id: UUID
    festival_id: UUID
    user_email: str
    reaction_type: str
    created_at: datetime

    class Config:
        from_attributes = True


# Stories
class FestivalStoryCreate(BaseModel):
    festival_id: UUID = Field(..., description="Festival UUID")
    content: str = Field(..., min_length=1, max_length=5000, description="Story content")
    media_urls: Optional[List[str]] = Field(default=None, description="Optional media URLs for the story")

    class Config:
        from_attributes = True


class FestivalStoryUpdate(BaseModel):
    content: Optional[str] = Field(None, min_length=1, max_length=5000)
    media_urls: Optional[List[str]] = None

    class Config:
        from_attributes = True


class FestivalStoryOut(BaseModel):
    id: UUID
    festival_id: UUID
    user_email: str
    content: str
    media_urls: Optional[List[str]] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Aggregated Stats
class FestivalStats(BaseModel):
    total_reactions: int = 0
    total_stories: int = 0
    user_has_reacted: bool = False
    
    class Config:
        from_attributes = True
