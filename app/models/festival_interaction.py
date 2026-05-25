from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey, UniqueConstraint
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

    # Constraints
    __table_args__ = (
        UniqueConstraint('festival_id', 'user_email', name='unique_festival_user_story'),
    )
