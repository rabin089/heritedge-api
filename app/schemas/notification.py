from datetime import datetime
from pydantic import BaseModel
from typing import Optional
from uuid import UUID


class NotificationOut(BaseModel):
    id: UUID
    recipient_email: str
    type: str
    title: str
    message: Optional[str] = None
    created_at: datetime
    read: bool
    read_at: Optional[datetime] = None

    class Config:
        orm_mode = True
