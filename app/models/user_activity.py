from datetime import datetime, timezone
import uuid
import enum
from sqlalchemy import Column, String, DateTime, Enum, Index
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class ItemType(str, enum.Enum):
    site = "site"
    festival = "festival"
    intangible = "intangible"


class ActionType(str, enum.Enum):
    view = "view"
    bookmark = "bookmark"
    favorite = "favorite"
    review = "review"
    share = "share"
    search = "search"


class UserActivity(Base):
    __tablename__ = "user_activity"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), index=True, nullable=False)
    item_id = Column(UUID(as_uuid=True), index=True, nullable=False)
    item_type = Column(Enum(ItemType), nullable=False)
    action_type = Column(Enum(ActionType), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        Index("ix_user_activity_user_item", "user_id", "item_id"),
        Index("ix_user_activity_user_action", "user_id", "action_type"),
    )
