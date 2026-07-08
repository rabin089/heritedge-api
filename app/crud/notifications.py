from datetime import datetime, timezone
from typing import Iterable
from uuid import UUID

from sqlalchemy.orm import Session
from app.models.notification import Notification


def create_notification(
    db: Session,
    recipient_email: str,
    type: str,
    title: str,
    message: str | None = None,
) -> Notification:
    note = Notification(
        recipient_email=recipient_email,
        type=type,
        title=title,
        message=message,
    )
    db.add(note)
    return note


def list_my_notifications(db: Session, recipient_email: str):
    return (
        db.query(Notification)
        .filter(Notification.recipient_email == recipient_email)
        .order_by(Notification.created_at.desc())
        .all()
    )


def mark_read(db: Session, recipient_email: str, notification_ids: Iterable[UUID]) -> int:
    ids: list[UUID] = list(notification_ids)
    if not ids:
        return 0
    q = (
        db.query(Notification)
        .filter(
            Notification.recipient_email == recipient_email,
            Notification.id.in_(ids),
        )
    )
    count = 0
    now = datetime.now(timezone.utc)
    for n in q.all():
        if not n.read:
            n.read = True
            n.read_at = now
            count += 1
    db.commit()
    return count


def count_unread(db: Session, recipient_email: str) -> int:
    return (
        db.query(Notification)
        .filter(
            Notification.recipient_email == recipient_email,
            Notification.read == False,
        )
        .count()
    )


def mark_all_read(db: Session, recipient_email: str) -> int:
    q = (
        db.query(Notification)
        .filter(
            Notification.recipient_email == recipient_email,
            Notification.read == False,
        )
    )
    now = datetime.now(timezone.utc)
    count = 0
    for n in q.all():
        n.read = True
        n.read_at = now
        count += 1
    db.commit()
    return count
