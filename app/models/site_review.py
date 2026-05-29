from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey, UniqueConstraint, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base
import uuid


class SiteReview(Base):
    __tablename__ = "site_reviews"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    site_id = Column(UUID(as_uuid=True), ForeignKey("heritage_sites.id"), nullable=False, index=True)
    user_email = Column(String, nullable=False, index=True)
    rating = Column(Integer, nullable=False)  # 0-10 integer rating
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    heritage_site = relationship("HeritageSite", back_populates="reviews")
    
    reviewer = relationship(
        "User",
        primaryjoin="foreign(SiteReview.user_email) == User.email",
        viewonly=True,
        uselist=False
    )

    @property
    def reviewer_name(self):
        if self.reviewer:
            return self.reviewer.display_name or self.reviewer.name or "Anonymous User"
        return "Anonymous User"
        
    @property
    def reviewer_avatar(self):
        if self.reviewer:
            return self.reviewer.profile_photo_url
        return None

    # Constraints
    __table_args__ = (
        CheckConstraint('rating >= 0 AND rating <= 10', name='check_rating_range'),
        UniqueConstraint('site_id', 'user_email', name='unique_site_user_review'),
    )


class SiteRating(Base):
    __tablename__ = "site_ratings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    site_id = Column(UUID(as_uuid=True), ForeignKey("heritage_sites.id"), nullable=False, index=True)
    user_email = Column(String, nullable=False, index=True)
    rating = Column(Integer, nullable=False)  # 0-10 integer rating
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    heritage_site = relationship("HeritageSite", back_populates="ratings")

    # Constraints
    __table_args__ = (
        CheckConstraint('rating >= 0 AND rating <= 10', name='check_rating_range'),
        UniqueConstraint('site_id', 'user_email', name='unique_site_user_rating'),
    )
