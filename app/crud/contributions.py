from sqlalchemy.orm import Session
from sqlalchemy.orm import Session
from app.models.contribution import Contribution, ContributionStatus
from app.models.heritage_site import HeritageSite
from uuid import UUID
from app.schemas.contribution import ContributionCreate, ContributionUpdate
from app.schemas.heritage_site import HeritageSiteCreate
from datetime import datetime, timezone
from app.crud import notifications as notif_crud
from sqlalchemy import or_, func


def create_contribution(db: Session, data: ContributionCreate, user_id: str):
    row = Contribution(**data.model_dump(), created_by=user_id)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def get_contribution_by_id(db: Session, contrib_id: UUID):
    return db.query(Contribution).filter(Contribution.id == contrib_id).first()


def list_my_contributions(db: Session, user_id: str, status: ContributionStatus | None = None):
    q = db.query(Contribution).filter(
        Contribution.created_by == user_id,
        Contribution.is_deleted == False,
    )
    if status:
        q = q.filter(Contribution.status == status)
    return q.order_by(Contribution.created_at.desc()).all()


def list_all_contributions(db: Session, status: ContributionStatus | None = None):
    q = db.query(Contribution).filter(Contribution.is_deleted == False)
    if status:
        q = q.filter(Contribution.status == status)
    return q.order_by(Contribution.created_at.desc()).all()


def admin_list_pending_contributions(
    db: Session,
    region: str | None,
    category: str | None,
    q: str | None,
    page: int,
    page_size: int,
):
    base = db.query(Contribution).filter(
        Contribution.is_deleted == False,
        Contribution.status == ContributionStatus.pending,
    )
    if region:
        base = base.filter(Contribution.region.ilike(f"%{region}%"))
    if category:
        base = base.filter(Contribution.category.ilike(f"%{category}%"))
    if q:
        like = f"%{q}%"
        base = base.filter(
            or_(
                Contribution.name.ilike(like),
                Contribution.region.ilike(like),
                Contribution.description.ilike(like),
                func.array_to_string(Contribution.tags, ' ').ilike(like),
            )
        )

    total = base.count()
    items = (
        base.order_by(Contribution.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return items, total


def admin_user_contribution_history(
    db: Session,
    user_email: str,
    page: int,
    page_size: int,
    status: ContributionStatus | None = None,
):
    base = db.query(Contribution).filter(
        Contribution.is_deleted == False,
        Contribution.created_by == user_email,
    )
    if status:
        base = base.filter(Contribution.status == status)

    total = base.count()
    items = (
        base.order_by(Contribution.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return items, total


def update_my_pending_contribution(db: Session, contrib_id: UUID, user_id: str, data: ContributionUpdate):
    row = db.query(Contribution).filter(
        Contribution.id == contrib_id,
        Contribution.created_by == user_id
    ).first()
    if not row:
        return None
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(row, k, v)
    row.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(row)
    return row


def delete_my_pending_contribution(db: Session, contrib_id: UUID, user_id: str):
    row = db.query(Contribution).filter(
        Contribution.id == contrib_id,
        Contribution.created_by == user_id
    ).first()
    if not row:
        return None
    row.is_deleted = True
    row.deleted_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(row)
    return row


def approve_contribution(db: Session, contrib_id: UUID, admin_user_id: str, comment: str | None = None):
    row = db.query(Contribution).filter(Contribution.id == contrib_id).first()
    if not row or row.status != ContributionStatus.pending:
        return None

    # create heritage site from contribution
    site_data = HeritageSiteCreate(
        name=row.name,
        description=row.description,
        category=row.category,
        region=row.region,
        location=row.location,
        latitude=row.latitude,
        longitude=row.longitude,
        image_url=row.image_url,
        secondary_images=row.secondary_images,
        tags=row.tags,
    )
    site = HeritageSite(
        **site_data.model_dump(),
        created_by=row.created_by,      # original contributor
        contribution_id=row.id,
        is_pending=False,
    )
    db.add(site)
    # update contribution status
    row.status = ContributionStatus.approved
    row.rejection_reason = None
    row.status_reason = comment
    row.approved_by = str(admin_user_id)
    row.approved_at = datetime.now(timezone.utc)
    # audit on site: who approved (admin)
    site.approved_by = str(admin_user_id)
    site.approved_at = datetime.now(timezone.utc)
    # in-app notification for contributor (admin note in message)
    try:
        notif_crud.create_notification(
            db,
            recipient_email=row.created_by,
            type="contribution_approved",
            title=f"Contribution #{row.id} approved",
            message=comment or "Approved",
        )
    except Exception:
        pass
    db.commit()
    db.refresh(row)
    db.refresh(site)
    return row, site


def reject_contribution(db: Session, contrib_id: UUID, reason: str, admin_user_id: str):
    row = db.query(Contribution).filter(Contribution.id == contrib_id).first()
    if not row or row.status != ContributionStatus.pending:
        return None
    row.status = ContributionStatus.rejected
    row.rejection_reason = reason
    row.status_reason = reason
    row.updated_by = str(admin_user_id)
    row.updated_at = datetime.now(timezone.utc)
    # in-app notification for contributor with admin reason
    try:
        notif_crud.create_notification(
            db,
            recipient_email=row.created_by,
            type="contribution_rejected",
            title=f"Contribution #{row.id} rejected",
            message=reason,
        )
    except Exception:
        pass
    db.commit()
    db.refresh(row)
    return row


def resubmit_rejected_contribution(db: Session, contrib_id: UUID, user_id: str, data: ContributionUpdate | None = None):
    row = db.query(Contribution).filter(
        Contribution.id == contrib_id,
        Contribution.created_by == user_id
    ).first()
    if not row or row.status != ContributionStatus.rejected:
        return None

    # apply updates if provided
    if data is not None:
        for k, v in data.model_dump(exclude_unset=True).items():
            setattr(row, k, v)

    # reset status to pending for review
    row.status = ContributionStatus.pending
    row.rejection_reason = None
    row.status_reason = None
    db.commit()
    db.refresh(row)
    return row
