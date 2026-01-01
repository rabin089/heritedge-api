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


class Contribution(Base):
    __tablename__ = "contributions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    # submitted content (same fields as heritage site)
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

    status = Column(Enum(ContributionStatus), default=ContributionStatus.pending, nullable=False)
    # unified status reason to record approval comment or rejection reason
    status_reason = Column(Text, nullable=True)
    rejection_reason = Column(Text, nullable=True)

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
