from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, Text, Boolean, DateTime, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum
import uuid


class ContributionStatus(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


class ContributionType(str, enum.Enum):
    site = "site"
    festival = "festival"


class Contribution(Base):
    __tablename__ = "contributions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    # submitted content (same fields as heritage site)
    type = Column(Enum(ContributionType), default=ContributionType.site, nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text)
    category = Column(String)
    region = Column(String)
    location = Column(String)
    latitude = Column(Float)
    longitude = Column(Float)
    image_url = Column(String)
    secondary_images = Column(ARRAY(String, dimensions=1), nullable=True)
    tags = Column(ARRAY(String, dimensions=1), nullable=True)
    
    # For Festival type specifically
    start_date = Column(DateTime(timezone=True), nullable=True)
    end_date = Column(DateTime(timezone=True), nullable=True)
    significance = Column(Text, nullable=True)
    nepali_date = Column(String, nullable=True)
    is_annual = Column(Boolean, default=False)

    status = Column(Enum(ContributionStatus), default=ContributionStatus.pending, nullable=False)
    # unified status reason to record approval comment or rejection reason
    status_reason = Column(Text, nullable=True)
    rejection_reason = Column(Text, nullable=True)
    
    # Festival association
    festival_id = Column(UUID(as_uuid=True), ForeignKey("festivals.id"), nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    created_by = Column(String, nullable=False)  # user id or email (your existing type)

    # soft delete flag
    is_deleted = Column(Boolean, default=False, nullable=False)

    # audit fields
    approved_by = Column(String, nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    updated_by = Column(String, nullable=True)
    updated_at = Column(DateTime(timezone=True), nullable=True)
    deleted_by = Column(String, nullable=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    # backref from HeritageSite if approved (optional relationship)
    heritage_site = relationship("HeritageSite", uselist=False, back_populates="contribution")
    festival = relationship("Festival", back_populates="contributions")
