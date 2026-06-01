from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey, UniqueConstraint, Boolean
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
from app.core.database import Base
import uuid


class FestivalReaction(Base):
    __tablename__ = "festival_reactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    festival_id = Column(UUID(as_uuid=True), ForeignKey("festivals.id"), nullable=False, index=True)
    user_email = Column(String, nullable=False, index=True)
    reaction_type = Column(String, default="heart", nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    festival = relationship("Festival", back_populates="reactions")

    # Constraints
    __table_args__ = (
        UniqueConstraint('festival_id', 'user_email', name='unique_festival_user_reaction'),
    )


class FestivalStory(Base):
    __tablename__ = "festival_stories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    festival_id = Column(UUID(as_uuid=True), ForeignKey("festivals.id"), nullable=False, index=True)
    user_email = Column(String, nullable=False, index=True)
    content = Column(Text, nullable=False)
    media_urls = Column(ARRAY(String), nullable=True)  # To support optional photos/videos
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    festival = relationship("Festival", back_populates="stories")
    reactions = relationship("StoryReaction", back_populates="story", cascade="all, delete-orphan")

    # Constraints
    __table_args__ = (
        UniqueConstraint('festival_id', 'user_email', name='unique_festival_user_story'),
    )


class FestivalReminder(Base):
    __tablename__ = "festival_reminders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    festival_id = Column(UUID(as_uuid=True), ForeignKey("festivals.id"), nullable=False, index=True)
    user_email = Column(String, nullable=False, index=True)
    
    # User can select multiple exact dates for reminders
    reminder_dates = Column(ARRAY(DateTime(timezone=True)), nullable=False)
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    festival = relationship("Festival", back_populates="reminders")


class FestivalDateSuggestion(Base):
    __tablename__ = "festival_date_suggestions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    festival_id = Column(UUID(as_uuid=True), ForeignKey("festivals.id"), nullable=False, index=True)
    user_email = Column(String, nullable=False, index=True)
    
    proposed_start_date = Column(DateTime(timezone=True), nullable=False)
    proposed_end_date = Column(DateTime(timezone=True), nullable=False)
    proposed_nepali_date = Column(String, nullable=True)
    
    status = Column(String, default="pending")  # pending, approved, rejected
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    festival = relationship("Festival", backref="date_suggestions")

class StoryReaction(Base):
    __tablename__ = "story_reactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    story_id = Column(UUID(as_uuid=True), ForeignKey("festival_stories.id"), nullable=False, index=True)
    user_email = Column(String, nullable=False, index=True)
    reaction_type = Column(String, default="heart", nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    story = relationship("FestivalStory", back_populates="reactions")

    # Constraints
    __table_args__ = (
        UniqueConstraint('story_id', 'user_email', name='unique_story_user_reaction'),
    )
