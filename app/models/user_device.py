from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base
import uuid
from datetime import datetime, timezone


class UserDevice(Base):
    """Stores FCM push tokens per user device."""
    __tablename__ = "user_devices"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_email = Column(String, nullable=False, index=True)
    fcm_token = Column(String, nullable=False)
    device_platform = Column(String, nullable=True)   # android, ios
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        # One token per user per device — re-registering updates it
        UniqueConstraint('user_email', 'fcm_token', name='unique_user_fcm_token'),
    )
