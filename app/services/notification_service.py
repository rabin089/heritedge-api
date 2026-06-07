import os
import logging
import traceback

import firebase_admin
from firebase_admin import credentials, messaging

logger = logging.getLogger(__name__)


def _init_firebase():
    """
    Initialize Firebase Admin SDK once.
    """
    if firebase_admin._apps:
        logger.debug("Firebase already initialized")
        return

    try:
        cred_path = os.getenv("FIREBASE_CREDENTIALS_PATH")

        logger.info(f"FIREBASE_CREDENTIALS_PATH = {cred_path}")

        if cred_path and os.path.exists(cred_path):
            cred = credentials.Certificate(cred_path)
            app = firebase_admin.initialize_app(cred)
            
            # Log project ID for verification
            project_id = cred.project_id
            logger.info(f"✅ Firebase initialized with project: {project_id}")
            logger.info(f"Firebase service account email: {cred.service_account_email}")
            
        else:
            if not cred_path:
                logger.warning("FIREBASE_CREDENTIALS_PATH environment variable not set. Using default credentials.")
            else:
                logger.warning(f"FIREBASE_CREDENTIALS_PATH not found at {cred_path}. Using default credentials.")
            
            firebase_admin.initialize_app()
            logger.info("Firebase initialized using default credentials.")

    except ValueError as e:
        logger.warning(f"Firebase already initialized: {e}")

    except Exception as e:
        logger.error(f"❌ Firebase initialization failed: {e}")
        logger.error(traceback.format_exc())
        raise


def send_push_notification(
    token: str,
    title: str,
    body: str,
    data: dict = None
) -> bool:
    """
    Send notification to a single device.
    """
    _init_firebase()

    try:
        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body
            ),
            data={k: str(v) for k, v in (data or {}).items()},
            token=token,
        )

        response = messaging.send(message)

        logger.info(
            f"Push notification sent successfully. "
            f"Message ID: {response}"
        )

        return True

    except messaging.UnregisteredError:
        logger.warning(
            f"FCM token is unregistered: {token[:20]}..."
        )
        return False

    except Exception as e:
        logger.error(
            f"Failed to send push notification: {e}"
        )
        logger.error(traceback.format_exc())
        return False


def send_multicast_notification(
    tokens: list[str],
    title: str,
    body: str,
    data: dict = None
) -> dict:
    """
    Send notification to multiple devices.
    """
    _init_firebase()

    if not tokens:
        logger.warning("No FCM tokens provided.")
        return {
            "success": 0,
            "failure": 0,
            "invalid_tokens": []
        }

    logger.info(
        f"Sending multicast notification to "
        f"{len(tokens)} devices"
    )
    
    # Debug: Print FULL tokens to terminal (will always show)
    print(f"\n{'='*60}")
    print(f"NOTIFICATION SERVICE DEBUG: About to send to {len(tokens)} token(s)")
    for idx, token in enumerate(tokens):
        print(f"DEBUG Token #{idx + 1}: {token}")
        print(f"  → Length: {len(token)}")
        print(f"  → Valid prefix? {token.startswith('f') or 'APA' in token}")
    print(f"{'='*60}\n")
    
    # Debug: Log FULL tokens to verify they're complete
    for idx, token in enumerate(tokens):
        logger.debug(f"Token #{idx + 1}: {token} (length: {len(token)})")

    try:
        message = messaging.MulticastMessage(
            notification=messaging.Notification(
                title=title,
                body=body,
            ),
            data={k: str(v) for k, v in (data or {}).items()},
            tokens=tokens,
        )

        batch_response = messaging.send_each_for_multicast(
            message
        )

        logger.info(
            f"Multicast completed. "
            f"Success={batch_response.success_count}, "
            f"Failure={batch_response.failure_count}"
        )

        invalid_tokens = []
        for idx, response in enumerate(
            batch_response.responses
        ):
            if not response.success:
                token = tokens[idx]
                if response.exception:
                    error_msg = f"{type(response.exception).__name__}: {str(response.exception)}"
                else:
                    error_msg = "Unknown error (no exception details)"
                
                logger.error(
                    f"❌ Token #{idx + 1} ({token[:20]}...) failed: {error_msg}"
                )
                invalid_tokens.append({
                    "token": token[:20] + "...",
                    "error": error_msg
                })

        return {
            "success": batch_response.success_count,
            "failure": batch_response.failure_count,
            "invalid_tokens": invalid_tokens,
        }

    except Exception as e:
        logger.error(
            "Firebase multicast notification failed"
        )
        logger.error(
            f"Exception Type: {type(e).__name__}"
        )
        logger.error(
            f"Exception Message: {str(e)}"
        )
        logger.error(traceback.format_exc())

        return {
            "success": 0,
            "failure": len(tokens),
            "invalid_tokens": [],
            "error": str(e),
        }


def notify_user(
    db,
    user_email: str,
    title: str,
    body: str,
    data: dict = None
) -> bool:
    """
    Find all active device tokens for a user
    and send a push notification.
    """

    from app.models.user_device import UserDevice
    from app.models.user_settings import UserSettings

    settings = (
        db.query(UserSettings)
        .filter(
            UserSettings.user_email == user_email
        )
        .first()
    )

    if (
        settings
        and not settings.push_notifications_enabled
    ):
        logger.info(
            f"Push notifications disabled "
            f"for user {user_email}"
        )
        return False

    devices = (
        db.query(UserDevice)
        .filter(
            UserDevice.user_email == user_email,
            UserDevice.is_active == True
        )
        .all()
    )

    tokens = [
        device.fcm_token
        for device in devices
        if device.fcm_token
    ]

    logger.info(
        f"Found {len(tokens)} active tokens "
        f"for {user_email}"
    )

    if not tokens:
        logger.warning(
            f"No active FCM tokens found "
            f"for user {user_email}"
        )
        return False

    result = send_multicast_notification(
        tokens=tokens,
        title=title,
        body=body,
        data=data,
    )

    return result["success"] > 0