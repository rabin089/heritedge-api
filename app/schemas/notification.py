from datetime import datetime
from pydantic import BaseModel
from typing import Optional


class NotificationOut(BaseModel):
    id: int
    recipient_email: str
    type: str
    title: str
    message: Optional[str] = None
    created_at: datetime
    read: bool
    read_at: Optional[datetime] = None

    class Config:
        orm_mode = True
