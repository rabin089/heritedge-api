from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone
from uuid import UUID

from app.core.database import get_db
from app.api.v1.auth import get_current_user
from app.models.user_device import UserDevice

router = APIRouter(prefix="/me", tags=["user-devices"])


class DeviceTokenRegister(BaseModel):
    fcm_token: str
    device_platform: Optional[str] = None  # "android" | "ios"


class DeviceTokenOut(BaseModel):
    id: UUID
    user_email: str
    fcm_token: str
    device_platform: Optional[str]
    is_active: bool

    class Config:
        from_attributes = True


@router.post("/device-token", response_model=DeviceTokenOut)
def register_device_token(
    token_in: DeviceTokenRegister,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    Register or refresh an FCM push token for the current user's device.
    Call this on every app startup after login.
    """
    existing = db.query(UserDevice).filter(
        UserDevice.user_email == current_user.email,
        UserDevice.fcm_token == token_in.fcm_token
    ).first()

    if existing:
        # Just reactivate and update
        existing.is_active = True
        existing.device_platform = token_in.device_platform or existing.device_platform
        existing.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(existing)
        return existing

    device = UserDevice(
        user_email=current_user.email,
        fcm_token=token_in.fcm_token,
        device_platform=token_in.device_platform,
        is_active=True
    )
    db.add(device)
    db.commit()
    db.refresh(device)
    return device


@router.delete("/device-token", status_code=status.HTTP_204_NO_CONTENT)
def unregister_device_token(
    token_in: DeviceTokenRegister,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    Deactivate an FCM token (e.g. on logout). Stops notifications to that device.
    """
    device = db.query(UserDevice).filter(
        UserDevice.user_email == current_user.email,
        UserDevice.fcm_token == token_in.fcm_token
    ).first()

    if device:
        device.is_active = False
        db.commit()
