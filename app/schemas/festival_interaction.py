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
    user_name: str
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
    user_name: str
    content: str
    media_urls: Optional[List[str]] = None
    reactions_count: int = 0
    user_has_reacted: bool = False
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class StoryReactionCreate(BaseModel):
    story_id: UUID = Field(..., description="Story UUID")
    reaction_type: str = Field(default="heart", description="Type of reaction")

    class Config:
        from_attributes = True

class StoryReactionOut(BaseModel):
    id: UUID
    story_id: UUID
    user_name: str
    reaction_type: str
    created_at: datetime

    class Config:
        from_attributes = True


# Aggregated Stats
class FestivalStats(BaseModel):
    total_reactions: int = 0
    total_stories: int = 0
    user_has_reacted: bool = False
    
    class Config:
        from_attributes = True


# Reminders
class FestivalReminderCreate(BaseModel):
    festival_id: UUID = Field(..., description="Festival UUID")
    reminder_dates: List[datetime] = Field(..., description="Array of exact datetimes to remind the user")
    is_active: Optional[bool] = True

    class Config:
        from_attributes = True


class FestivalReminderOut(BaseModel):
    id: UUID
    festival_id: UUID
    user_name: str
    reminder_dates: List[datetime]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Date Suggestions
class FestivalDateSuggestionCreate(BaseModel):
    festival_id: UUID = Field(..., description="Festival UUID")
    proposed_start_date: datetime
    proposed_end_date: datetime
    proposed_nepali_date: Optional[str] = None

    class Config:
        from_attributes = True


class FestivalDateSuggestionOut(BaseModel):
    id: UUID
    festival_id: UUID
    user_name: str
    proposed_start_date: datetime
    proposed_end_date: datetime
    proposed_nepali_date: Optional[str] = None
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True


# Admin Story Management
class AdminStoryListResponse(BaseModel):
    stories: List[FestivalStoryOut]
    total: int
    page: int
    page_size: int


class AdminStoryDeleteInfo(BaseModel):
    message: str
    story_id: UUID
    deleted_by: str
    reason: Optional[str] = None
