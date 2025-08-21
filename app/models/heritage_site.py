from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import relationship
from app.core.database import Base
import uuid


class HeritageSite(Base):
    __tablename__ = "heritage_sites"

    id = Column(Integer, primary_key=True, index=True)
    public_id = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, nullable=False, index=True)
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
    is_pending = Column(Boolean, default=False, nullable=False)  # approved data is not pending
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    created_by = Column(String, nullable=False)           # original contributor user id/email
    contribution_id = Column(Integer, ForeignKey("contributions.id"), nullable=True)
    # soft delete flag
    is_deleted = Column(Boolean, default=False, nullable=False)

    # audit fields
    approved_by = Column(String, nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    updated_by = Column(String, nullable=True)
    updated_at = Column(DateTime(timezone=True), nullable=True)
    deleted_by = Column(String, nullable=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    contribution = relationship("Contribution", back_populates="heritage_site")
