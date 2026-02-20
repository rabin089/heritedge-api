from datetime import datetime
from pydantic import BaseModel
from typing import Optional
from uuid import UUID


class NotificationOut(BaseModel):
    id: UUID
    user_email: str
    title: str
    message: str
    is_read: bool
    read_at: Optional[datetime] = None

    class Config:
        from_attributes = True
