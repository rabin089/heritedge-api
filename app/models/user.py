from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base
import uuid
from datetime import datetime, timezone


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=True)  # From Google/other auth providers
    profile_photo_url = Column(String, nullable=True)
    display_name = Column(String, nullable=True)  # Added as real column
    auth_provider = Column(String, default="email", nullable=False)  # email, google, firebase, etc.
    hashed_password = Column(String, nullable=True)
    firebase_uid = Column(String, unique=True, index=True, nullable=True)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    role = Column(String, default="user", nullable=False)
    account_created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    last_login_at = Column(DateTime(timezone=True), nullable=True)
