import uuid
from pydantic import BaseModel
from app.models.user_activity import ItemType, ActionType

class ActivityCreate(BaseModel):
    item_id: uuid.UUID
    item_type: ItemType
    action_type: ActionType

class ActivityResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    item_id: uuid.UUID
    item_type: ItemType
    action_type: ActionType

    class Config:
        orm_mode = True
