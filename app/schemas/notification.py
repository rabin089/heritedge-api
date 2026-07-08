from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class NotificationOut(BaseModel):
    # Map ORM attribute names to the public API field names so the JSON
    # contract (user_email / is_read) is preserved while still reading
    # from the SQLAlchemy model (recipient_email / read).
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
    )

    id: UUID
    user_email: str = Field(
        validation_alias="recipient_email",
        serialization_alias="user_email",
    )
    title: str
    message: Optional[str] = None
    is_read: bool = Field(
        validation_alias="read",
        serialization_alias="is_read",
    )
    read_at: Optional[datetime] = None
    created_at: datetime
