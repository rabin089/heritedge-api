from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, Integer, ForeignKey, DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base
import uuid


class IntangibleHeritage(Base):
    __tablename__ = "intangible_heritage"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    category = Column(String(50))  # 'music','dance','ritual','craft','food'
    community = Column(String(100))  # 'Newari','Tamang','Sherpa'...
    language = Column(String(100))
    risk_level = Column(String(20))  # 'critical','endangered','stable'
    
    # Link to a physical site if applicable
    location_id = Column(UUID(as_uuid=True), ForeignKey("heritage_sites.id"), nullable=True)
    practiced_at = Column(String(255))  # physical address/area
    
    # Tracking
    created_by = Column(String, nullable=False) # contributor email/id
    status = Column(String(20), default="approved") # Permanent items are usually already approved
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Relation to the staging contribution
    contribution_id = Column(UUID(as_uuid=True), ForeignKey("contributions.id"), nullable=True)
    
    # soft delete flag
    is_deleted = Column(Boolean, default=False, nullable=False)

    # Relationships
    location = relationship("HeritageSite")
    media = relationship("IntangibleMedia", back_populates="intangible", cascade="all, delete-orphan")
    contribution = relationship("Contribution", uselist=False)

    creator_details = relationship(
        "User",
        primaryjoin="foreign(IntangibleHeritage.created_by) == User.email",
        viewonly=True,
        uselist=False
    )


class IntangibleMedia(Base):
    __tablename__ = "intangible_media"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    intangible_id = Column(UUID(as_uuid=True), ForeignKey("intangible_heritage.id"), nullable=False)
    media_type = Column(String(10))  # 'video','audio','photo'
    media_url = Column(Text, nullable=False)  # MinIO URL
    duration_seconds = Column(Integer, nullable=True)

    # Relationships
    intangible = relationship("IntangibleHeritage", back_populates="media")
