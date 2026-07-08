from fastapi import APIRouter, Depends, HTTPException, Body, status
from typing import List
from sqlalchemy.orm import Session
from datetime import timezone
from app.core.database import SessionLocal
from app.api.v1.auth import get_current_user
from app.models.user import User
from app.schemas.notification import NotificationOut
from app.crud import notifications as crud

router = APIRouter(prefix="/notifications", tags=["notifications"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("", response_model=List[NotificationOut])
def list_my_notifications(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return crud.list_my_notifications(db, current_user.email)


@router.post("/read")
def mark_read(
    ids: List[int] = Body(..., embed=True),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    updated = crud.mark_read(db, current_user.email, ids)
    return {"updated": updated}


@router.get("/unread-count")
def unread_count(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    count = crud.count_unread(db, current_user.email)
    return {"count": count}


@router.post("/read-all")
def mark_all_read(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    updated = crud.mark_all_read(db, current_user.email)
    return {"updated": updated}


@router.post("/test-push")
def test_push_notification(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    from app.models.user_settings import UserSettings
    from app.models.user_device import UserDevice
    from app.services.notification_service import send_multicast_notification
    import logging

    logger = logging.getLogger(__name__)

    # 1. Get the set of users who have DISABLED push notifications.
    #    Users with no settings row at all are treated as "enabled" (default = True).
    disabled_user_emails = set(
        email for (email,) in db.query(UserSettings.user_email)
        .filter(UserSettings.push_notifications_enabled == False)
        .all()
    )

    logger.info(
        f"Test-push triggered by {current_user.email}. "
        f"Users with notifications disabled: {disabled_user_emails or 'none'}"
    )

    # 2. Get ALL active device tokens across all users,
    #    EXCLUDING tokens whose owner has disabled push notifications.
    query = db.query(UserDevice).filter(UserDevice.is_active == True)
    all_active_devices = query.all()

    devices = [
        device for device in all_active_devices
        if device.user_email not in disabled_user_emails
    ]

    # Deduplicate tokens (a user may have registered the same token on multiple records)
    seen_tokens = set()
    unique_tokens = []
    for device in devices:
        if device.fcm_token and device.fcm_token not in seen_tokens:
            seen_tokens.add(device.fcm_token)
            unique_tokens.append(device.fcm_token)
    tokens = unique_tokens

    # Debug: Log all tokens being sent
    print(f"\n{'='*60}")
    print(f"DEBUG: Retrieved {len(devices)} active device(s) from {len(set(d.user_email for d in devices))} user(s)")
    print(f"DEBUG: Sending to {len(tokens)} unique token(s) (after dedup)")
    for idx, token in enumerate(tokens):
        print(f"DEBUG: Token #{idx + 1}: {token[:25]}...  (length: {len(token)})")
    print(f"{'='*60}\n")

    logger.info(
        f"Retrieved {len(devices)} active device(s) from "
        f"{len(set(d.user_email for d in devices))} user(s) "
        f"({len(tokens)} unique token(s) after dedup)"
    )
    for idx, token in enumerate(tokens):
        logger.info(f"  Token #{idx + 1}: {token[:25]}... (length: {len(token)})")

    if not tokens:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "No active device tokens found across any user. "
                "Devices must register a token via POST /me/device-token before notifications can be sent."
            )
        )

    logger.info(
        f"Broadcasting test notification to {len(tokens)} device(s) "
        f"triggered by {current_user.email}"
    )

    # 3. Persist an in-app notification row for every unique recipient so the
    #    broadcast also shows up in GET /api/v1/notifications (the FCM push
    #    is just a wake-up signal; the DB row is the source of truth).
    broadcast_title = "Test Push Notification"
    broadcast_message = (
        "This is a test notification. "
        "If you see this, push notifications are working!"
    )
    unique_recipient_emails = {d.user_email for d in devices}
    for user_email in unique_recipient_emails:
        crud.create_notification(
            db,
            recipient_email=user_email,
            type="broadcast",
            title=broadcast_title,
            message=broadcast_message,
        )
    db.commit()

    # 4. Send the test notification to ALL collected devices via multicast
    result = send_multicast_notification(
        tokens=tokens,
        title=broadcast_title,
        body=broadcast_message,
        data={"type": "test_notification", "sent_at": str(__import__('datetime').datetime.now(timezone.utc).isoformat())}
    )

    logger.info(
        f"Test broadcast result (triggered by {current_user.email}): "
        f"Success={result.get('success', 0)}, Failure={result.get('failure', 0)}"
    )

    # 4. Return detailed results including error info
    success_count = result.get("success", 0)
    failure_count = result.get("failure", 0)
    invalid_tokens = result.get("invalid_tokens", [])

    if success_count == 0 and failure_count > 0:
        error_details = "\n".join([f"  - {t['token']}: {t['error']}" for t in invalid_tokens])
        logger.error(f"All tokens failed:\n{error_details}")

        error_response = f"Failed to send notification to all {failure_count} token(s). Details:\n{error_details}\n\nTroubleshooting:\n1. Check Firebase credentials are correctly configured\n2. Verify the FCM token is for the same Firebase project\n3. Check server logs for detailed Firebase errors"

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_response
        )

    return {
        "message": "Test notification sent successfully." if success_count > 0 else "Partial failure.",
        "triggered_by": current_user.email,
        "targeted_users": len(set(d.user_email for d in devices)),
        "targeted_devices": len(devices),
        "unique_tokens": len(tokens),
        "result": {
            "success": success_count,
            "failure": failure_count,
            "invalid_tokens": invalid_tokens,
        },
        "hint": "If you didn't receive the notification, check that: 1) App has notification permission, 2) FCM token is valid, 3) App was properly initialized with Firebase"
    }
