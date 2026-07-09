from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, Integer, Float, Boolean, ForeignKey, DateTime, DECIMAL, Index
from sqlalchemy.dialects.postgresql import UUID, INET, TSVECTOR, ARRAY
from sqlalchemy.orm import relationship
from app.core.database import Base
import uuid


class IntangibleHeritage(Base):
    __tablename__ = "intangible_heritage"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Basic Information
    name_np = Column(String(255), nullable=False)
    name_en = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    
    # Categorization
    category = Column(String(50), nullable=False, index=True)
    
    # Community & Language
    community = Column(String(100), index=True)
    language = Column(String(100))
    tags = Column(ARRAY(String), nullable=True)
    
    # Geographic & Practical
    location_id = Column(UUID(as_uuid=True), ForeignKey("heritage_sites.id", ondelete="SET NULL"), nullable=True, index=True)
    practiced_at_description = Column(String(255))
    
    # Risk Level
    risk_level = Column(String(20), default="stable", nullable=False, index=True)
    
    # Contributor Information
    contributor_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Status & Moderation
    status = Column(String(20), default="pending", nullable=False, index=True)
    approved_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    approval_notes = Column(Text)
    rejected_reason = Column(String(255))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    
    # Metadata
    view_count = Column(Integer, default=0, index=True)
    favorite_count = Column(Integer, default=0)
    engagement_score = Column(DECIMAL(10, 2), default=0.0)
    
    # Soft Delete
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    location = relationship("HeritageSite")
    contributor = relationship("User", foreign_keys=[contributor_id])
    approver = relationship("User", foreign_keys=[approved_by])
    # Alias used by schemas and CRUD for consistent contributor_details pattern
    creator_details = relationship("User", foreign_keys=[contributor_id], viewonly=True)

    media = relationship("IntangibleMedia", back_populates="intangible", cascade="all, delete-orphan")
    engagement = relationship("IntangibleEngagement", back_populates="intangible", cascade="all, delete-orphan")
    comments = relationship("IntangibleComments", back_populates="intangible", cascade="all, delete-orphan")
    flags = relationship("IntangibleFlags", back_populates="intangible", cascade="all, delete-orphan")
    analytics = relationship("IntangibleAnalytics", back_populates="intangible", cascade="all, delete-orphan")


class IntangibleMedia(Base):
    __tablename__ = "intangible_media"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    intangible_id = Column(UUID(as_uuid=True), ForeignKey("intangible_heritage.id", ondelete="CASCADE"), nullable=False, index=True)
    
    media_type = Column(String(10), nullable=False, index=True) # video, audio, photo
    media_url = Column(Text, nullable=False)
    file_size_mb = Column(DECIMAL(10, 2), nullable=False)
    duration_seconds = Column(Integer)
    mime_type = Column(String(50), nullable=False)
    width = Column(Integer)
    height = Column(Integer)
    thumbnail_url = Column(Text)
    
    uploaded_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    processing_status = Column(String(20), default="uploaded", index=True)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    processed_at = Column(DateTime(timezone=True), nullable=True)
    
    sort_order = Column(Integer, default=0)

    intangible = relationship("IntangibleHeritage", back_populates="media")
    uploader = relationship("User", foreign_keys=[uploaded_by])


class IntangibleEngagement(Base):
    __tablename__ = "intangible_engagement"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    intangible_id = Column(UUID(as_uuid=True), ForeignKey("intangible_heritage.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    action_type = Column(String(20), nullable=False, index=True) # view, favorite, share, comment, flag
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    ip_address = Column(INET, nullable=True)

    intangible = relationship("IntangibleHeritage", back_populates="engagement")
    user = relationship("User")


class IntangibleComments(Base):
    __tablename__ = "intangible_comments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    intangible_id = Column(UUID(as_uuid=True), ForeignKey("intangible_heritage.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    parent_comment_id = Column(UUID(as_uuid=True), ForeignKey("intangible_comments.id", ondelete="CASCADE"), nullable=True, index=True)
    
    content = Column(Text, nullable=False)
    is_flagged = Column(Boolean, default=False)
    flag_reason = Column(String(255))
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    like_count = Column(Integer, default=0)

    intangible = relationship("IntangibleHeritage", back_populates="comments")
    user = relationship("User")
    parent = relationship("IntangibleComments", remote_side=[id], back_populates="replies")
    replies = relationship("IntangibleComments", back_populates="parent", cascade="all, delete-orphan")

class IntangibleFlags(Base):
    __tablename__ = "intangible_flags"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    intangible_id = Column(UUID(as_uuid=True), ForeignKey("intangible_heritage.id", ondelete="CASCADE"), nullable=False, index=True)
    flagged_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    
    flag_reason = Column(String(50), nullable=False, index=True) # inaccurate, duplicate, offensive, etc.
    description = Column(Text)
    
    status = Column(String(20), default="open", index=True)
    resolved_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    resolution_notes = Column(Text)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    intangible = relationship("IntangibleHeritage", back_populates="flags")
    flagger = relationship("User", foreign_keys=[flagged_by])
    resolver = relationship("User", foreign_keys=[resolved_by])


class IntangibleAnalytics(Base):
    __tablename__ = "intangible_analytics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    intangible_id = Column(UUID(as_uuid=True), ForeignKey("intangible_heritage.id", ondelete="CASCADE"), nullable=False, index=True)
    
    date = Column(DateTime, nullable=False, index=True)
    
    views_today = Column(Integer, default=0)
    new_favorites = Column(Integer, default=0)
    new_comments = Column(Integer, default=0)
    new_shares = Column(Integer, default=0)
    engagement_score_today = Column(DECIMAL(10, 2), default=0.0)
    
    total_views = Column(Integer, default=0)
    total_engagement_score = Column(DECIMAL(10, 2), default=0.0)
    
    view_trend = Column(String(10)) # up, down, stable

    intangible = relationship("IntangibleHeritage", back_populates="analytics")
