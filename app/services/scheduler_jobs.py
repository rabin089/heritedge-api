"""
APScheduler background jobs for Heritedge push notifications.

Jobs:
  1. send_reminder_notifications  — Runs daily at 08:00 NPT (02:15 UTC)
     Scans festival_reminders table and notifies users whose reminder_dates
     match today's date.

  2. ping_contributors_for_dates  — Runs on the 1st of every month at 09:00 NPT
     Finds crowdsourced_variable festivals whose last_verified_year < current year
     and pings original contributors to confirm this year's dates.
"""

import logging
from datetime import datetime, timezone, timedelta, date
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.festival_interaction import FestivalReminder
from app.models.festival import Festival, DateDeterminationType
from app.models.user_device import UserDevice
from app.services.notification_service import send_multicast_notification
from app.crud import notifications as notif_crud

logger = logging.getLogger(__name__)


def _get_db() -> Session:
    return SessionLocal()


def send_reminder_notifications():
    """
    Daily job: Find all reminders whose reminder_dates include today (±30 min window),
    gather FCM tokens for those users, and fire push notifications.
    """
    db = _get_db()
    logger.info("⏰ Running daily reminder notification job...")
    try:
        now_utc = datetime.now(timezone.utc)
        # Check a 60-minute window around "now" to avoid timing precision issues
        window_start = now_utc - timedelta(minutes=30)
        window_end = now_utc + timedelta(minutes=30)

        # Fetch all active reminders
        reminders = db.query(FestivalReminder).filter(
            FestivalReminder.is_active == True
        ).all()

        reminders_to_notify: dict[str, list[FestivalReminder]] = {}
        for reminder in reminders:
            for reminder_dt in (reminder.reminder_dates or []):
                # Make timezone-aware if naive
                if reminder_dt.tzinfo is None:
                    reminder_dt = reminder_dt.replace(tzinfo=timezone.utc)
                if window_start <= reminder_dt <= window_end:
                    reminders_to_notify.setdefault(reminder.user_email, []).append(reminder)
                    break  # One match per reminder is enough

        if not reminders_to_notify:
            logger.info("No reminders to fire today.")
            return

        logger.info(f"Firing reminders for {len(reminders_to_notify)} users...")

        for user_email, user_reminders in reminders_to_notify.items():
            tokens = [
                d.fcm_token for d in db.query(UserDevice).filter(
                    UserDevice.user_email == user_email,
                    UserDevice.is_active == True
                ).all()
            ]
            if not tokens:
                continue

            for reminder in user_reminders:
                festival = db.query(Festival).filter(Festival.id == reminder.festival_id).first()
                if not festival:
                    continue
                title = f"🎉 {festival.name} is coming up!"
                body = "You have a reminder set for this festival. Make sure you're ready!"

                # Persist an in-app notification row so it shows up in
                # GET /api/v1/notifications, not just as a one-off FCM push.
                notif_crud.create_notification(
                    db,
                    recipient_email=user_email,
                    type="festival_reminder",
                    title=title,
                    message=body,
                )

                send_multicast_notification(
                    tokens=tokens,
                    title=title,
                    body=body,
                    data={
                        "type": "festival_reminder",
                        "festival_id": str(festival.id),
                        "screen": "festival_detail"
                    }
                )

        db.commit()
        logger.info("✅ Reminder notifications job completed.")
    except Exception as e:
        logger.error(f"Error in reminder notification job: {e}")
    finally:
        db.close()


def ping_contributors_for_dates():
    """
    Monthly job: Find all crowdsourced_variable festivals that haven't been
    verified this year, and notify the original contributor to confirm the date.
    """
    db = _get_db()
    logger.info("📅 Running monthly contributor ping job...")
    try:
        current_year = datetime.now(timezone.utc).year

        unverified_festivals = db.query(Festival).filter(
            Festival.date_determination == DateDeterminationType.crowdsourced_variable,
            (Festival.last_verified_year == None) | (Festival.last_verified_year < current_year)
        ).all()

        if not unverified_festivals:
            logger.info("All crowdsourced festivals are verified for this year.")
            return

        logger.info(f"Pinging contributors for {len(unverified_festivals)} unverified festivals...")

        for festival in unverified_festivals:
            # Look up the contributor's devices by matching their user ID to user email
            # (Requires joining via User model)
            from app.models.user import User
            contributor = db.query(User).filter(User.id == festival.created_by).first()
            if not contributor:
                continue

            tokens = [
                d.fcm_token for d in db.query(UserDevice).filter(
                    UserDevice.user_email == contributor.email,
                    UserDevice.is_active == True
                ).all()
            ]
            if not tokens:
                continue

            title = f"📅 Update needed for {festival.name}"
            body = f"You added '{festival.name}' to Heritedge. Can you confirm this year's dates so the community stays informed?"

            # Persist an in-app notification row so the ping shows up in
            # GET /api/v1/notifications, not just as a one-off FCM push.
            notif_crud.create_notification(
                db,
                recipient_email=contributor.email,
                type="date_verification_request",
                title=title,
                message=body,
            )

            send_multicast_notification(
                tokens=tokens,
                title=title,
                body=body,
                data={
                    "type": "date_verification_request",
                    "festival_id": str(festival.id),
                    "screen": "festival_edit"
                }
            )

        db.commit()
        logger.info("✅ Contributor ping job completed.")
    except Exception as e:
        logger.error(f"Error in contributor ping job: {e}")
    finally:
        db.close()
