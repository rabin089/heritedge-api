import firebase_admin
from firebase_admin import credentials, messaging
import os
import logging

logger = logging.getLogger(__name__)

_firebase_initialized = False


def _init_firebase():
    global _firebase_initialized
    if _firebase_initialized:
        return
    try:
        cred_path = os.getenv("FIREBASE_CREDENTIALS_PATH")
        if cred_path and os.path.exists(cred_path):
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
        else:
            # Use application default credentials (for cloud deployment)
            firebase_admin.initialize_app()
        _firebase_initialized = True
        logger.info("Firebase Admin SDK initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize Firebase: {e}")


def send_push_notification(
    token: str,
    title: str,
    body: str,
    data: dict = None
) -> bool:
    """Send a single push notification to a specific FCM token."""
    _init_firebase()
    try:
        message = messaging.Message(
            notification=messaging.Notification(title=title, body=body),
            data={k: str(v) for k, v in (data or {}).items()},
            token=token,
        )
        messaging.send(message)
        logger.info(f"Push notification sent to token: {token[:20]}...")
        return True
    except messaging.UnregisteredError:
        logger.warning(f"FCM token is unregistered/invalid: {token[:20]}...")
        return False
    except Exception as e:
        logger.error(f"Failed to send push notification: {e}")
        return False


def send_multicast_notification(
    tokens: list[str],
    title: str,
    body: str,
    data: dict = None
) -> dict:
    """Send a notification to multiple FCM tokens at once (batch)."""
    _init_firebase()
    if not tokens:
        return {"success": 0, "failure": 0}
    try:
        message = messaging.MulticastMessage(
            notification=messaging.Notification(title=title, body=body),
            data={k: str(v) for k, v in (data or {}).items()},
            tokens=tokens,
        )
        batch_response = messaging.send_each_for_multicast(message)
        logger.info(
            f"Multicast sent: {batch_response.success_count} success, "
            f"{batch_response.failure_count} failures"
        )
        return {
            "success": batch_response.success_count,
            "failure": batch_response.failure_count
        }
    except Exception as e:
        logger.error(f"Failed to send multicast notification: {e}")
        return {"success": 0, "failure": len(tokens)}


def notify_user(
    db: "Session",
    user_email: str,
    title: str,
    body: str,
    data: dict = None
) -> bool:
    """Helper to find all active device tokens for a user and send a notification, if settings permit."""
    from app.models.user_device import UserDevice
    from app.models.user_settings import UserSettings
    
    # Check settings first
    settings = db.query(UserSettings).filter(UserSettings.user_email == user_email).first()
    if settings and not settings.push_notifications_enabled:
        logger.info(f"Push notifications disabled for user {user_email}")
        return False
        
    tokens = [
        d.fcm_token for d in db.query(UserDevice).filter(
            UserDevice.user_email == user_email,
            UserDevice.is_active == True
        ).all()
    ]
    if not tokens:
        return False
        
    result = send_multicast_notification(tokens, title, body, data)
    return result["success"] > 0
