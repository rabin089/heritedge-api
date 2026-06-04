from pydantic import BaseModel
from typing import Optional

class UserSettingsBase(BaseModel):
    push_notifications_enabled: bool

class UserSettingsCreate(UserSettingsBase):
    pass

class UserSettingsUpdate(BaseModel):
    push_notifications_enabled: Optional[bool] = None

class UserSettingsOut(UserSettingsBase):
    user_email: str

    class Config:
        from_attributes = True
