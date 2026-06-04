from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey
from app.core.database import Base
from datetime import datetime, timezone

class UserSettings(Base):
    """Stores user specific settings like notification preferences."""
    __tablename__ = "user_settings"

    user_email = Column(String, ForeignKey("users.email", ondelete="CASCADE"), primary_key=True, index=True)
    push_notifications_enabled = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
