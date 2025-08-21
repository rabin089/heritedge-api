from sqlalchemy.orm import Session
from sqlalchemy import any_
from app.models.contribution import Contribution, ContributionStatus
from app.models.heritage_site import HeritageSite
from app.schemas.contribution import ContributionCreate, ContributionUpdate
from app.schemas.heritage_site import HeritageSiteCreate


def create_contribution(db: Session, data: ContributionCreate, user_id: str):
    row = Contribution(**data.model_dump(), created_by=user_id)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def get_contribution_by_id(db: Session, contrib_id: int):
    return db.query(Contribution).filter(Contribution.id == contrib_id).first()


def list_my_contributions(db: Session, user_id: str, status: ContributionStatus | None = None):
    q = db.query(Contribution).filter(Contribution.created_by == user_id)
    if status:
        q = q.filter(Contribution.status == status)
    return q.order_by(Contribution.created_at.desc()).all()


def list_all_contributions(db: Session, status: ContributionStatus | None = None):
    q = db.query(Contribution)
    if status:
        q = q.filter(Contribution.status == status)
    return q.order_by(Contribution.created_at.desc()).all()


def update_my_pending_contribution(db: Session, contrib_id: int, user_id: str, data: ContributionUpdate):
    row = db.query(Contribution).filter(
        Contribution.id == contrib_id,
        Contribution.created_by == user_id
    ).first()
    if not row or row.status != ContributionStatus.pending:
        return None

    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(row, k, v)
    db.commit()
    db.refresh(row)
    return row


def delete_my_pending_contribution(db: Session, contrib_id: int, user_id: str):
    row = db.query(Contribution).filter(
        Contribution.id == contrib_id,
        Contribution.created_by == user_id
    ).first()
    if not row or row.status != ContributionStatus.pending:
        return None
    db.delete(row)
    db.commit()
    return row


def approve_contribution(db: Session, contrib_id: int, admin_user_id: str, comment: str | None = None):
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
    db.commit()
    db.refresh(row)
    db.refresh(site)
    return row, site


def reject_contribution(db: Session, contrib_id: int, reason: str):
    row = db.query(Contribution).filter(Contribution.id == contrib_id).first()
    if not row or row.status != ContributionStatus.pending:
        return None
    row.status = ContributionStatus.rejected
    row.rejection_reason = reason
    row.status_reason = reason
    db.commit()
    db.refresh(row)
    return row


def resubmit_rejected_contribution(db: Session, contrib_id: int, user_id: str, data: ContributionUpdate | None = None):
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
