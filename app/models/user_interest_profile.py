from datetime import datetime, timezone
import uuid
from sqlalchemy import Column, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.core.database import Base


class UserInterestProfile(Base):
    __tablename__ = "user_interest_profile"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), index=True, nullable=False, unique=True)
    
    # Store dynamic scores
    category_scores = Column(JSONB, default=dict)
    tag_scores = Column(JSONB, default=dict)

    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
