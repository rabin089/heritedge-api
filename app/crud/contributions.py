from sqlalchemy.orm import Session, joinedload
from app.models.contribution import Contribution, ContributionStatus, ContributionType
from app.models.heritage_site import HeritageSite
from app.models.festival import Festival, FestivalStatus
from app.models.intangible_heritage import IntangibleHeritage, IntangibleMedia
from uuid import UUID
from app.schemas.contribution import ContributionCreate, ContributionUpdate
from app.schemas.heritage_site import HeritageSiteCreate
from datetime import datetime, timezone
from app.crud import notifications as notif_crud
from datetime import datetime, timezone
from app.crud import notifications as notif_crud
from sqlalchemy import or_, func
from app.utils.geocoding_util import get_location_name_from_coordinates


def create_contribution(db: Session, data: ContributionCreate, user_id: str):
    if data.latitude is not None and data.longitude is not None:
        loc_name = get_location_name_from_coordinates(data.latitude, data.longitude)
        if loc_name:
            data.location = loc_name
    row = Contribution(**data.model_dump(), created_by=user_id)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def get_contribution_by_id(db: Session, contrib_id: UUID):
    return db.query(Contribution).options(joinedload(Contribution.creator_details)).filter(Contribution.id == contrib_id).first()


def list_my_contributions(db: Session, user_id: str, status: ContributionStatus | None = None):
    q = db.query(Contribution).options(joinedload(Contribution.creator_details)).filter(
        Contribution.created_by == user_id,
        Contribution.is_deleted == False,
    )
    if status:
        q = q.filter(Contribution.status == status)
    return q.order_by(Contribution.created_at.desc()).all()


def list_all_contributions(db: Session, status: ContributionStatus | None = None):
    q = db.query(Contribution).options(joinedload(Contribution.creator_details)).filter(Contribution.is_deleted == False)
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
    base = db.query(Contribution).options(joinedload(Contribution.creator_details)).filter(
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
    base = db.query(Contribution).options(joinedload(Contribution.creator_details)).filter(
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
        
    if data.latitude is not None and data.longitude is not None:
        loc_name = get_location_name_from_coordinates(data.latitude, data.longitude)
        if loc_name:
            data.location = loc_name
            
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

    approved_item = None
    heritage_site_id = None
    festival_id = None
    intangible_id = None

    if row.type == ContributionType.intangible:
        from app.models.user import User
        from decimal import Decimal
        
        # Resolve created_by (email string) to user UUID
        user = db.query(User).filter(User.email == row.created_by).first()
        contributor_id = user.id if user else None
        if not contributor_id:
            try:
                contributor_id = UUID(admin_user_id)
            except (ValueError, TypeError):
                # Fallback to any superadmin
                admin = db.query(User).filter(User.role == "superadmin").first()
                if admin:
                    contributor_id = admin.id
                else:
                    # Final fallback to first user
                    any_user = db.query(User).first()
                    if any_user:
                        contributor_id = any_user.id

        approved_item = IntangibleHeritage(
            name_en=row.name,
            name_np=row.name_np or row.name, # Fallback to English name if Nepali is missing
            description=row.description,
            category=row.category or "other",
            community=row.community,
            language=row.language,
            location_id=row.festival_id, # Reusing festival_id field for location mapping if provided
            practiced_at_description=row.practiced_at,
            risk_level=row.risk_level or "stable",
            contributor_id=contributor_id,
            status="approved"
        )
        db.add(approved_item)
        db.flush()
        intangible_id = approved_item.id

        # Add media if URLs are present
        if row.video_url:
            db.add(IntangibleMedia(
                intangible_id=intangible_id,
                media_type="video",
                media_url=row.video_url,
                file_size_mb=Decimal("0.00"),
                mime_type="video/mp4"
            ))
        if row.audio_url:
            db.add(IntangibleMedia(
                intangible_id=intangible_id,
                media_type="audio",
                media_url=row.audio_url,
                file_size_mb=Decimal("0.00"),
                mime_type="audio/mpeg"
            ))
        if row.image_url:
            db.add(IntangibleMedia(
                intangible_id=intangible_id,
                media_type="photo",
                media_url=row.image_url,
                file_size_mb=Decimal("0.00"),
                mime_type="image/jpeg"
            ))
        if row.secondary_images:
            for idx, img_url in enumerate(row.secondary_images):
                db.add(IntangibleMedia(
                    intangible_id=intangible_id,
                    media_type="photo",
                    media_url=img_url,
                    file_size_mb=Decimal("0.00"),
                    mime_type="image/jpeg",
                    sort_order=idx + 1
                ))
            
    elif row.type == ContributionType.festival:
        # Check if dates are provided, fallback to now if missing (though they should be provided)
        st = row.start_date or datetime.now(timezone.utc)
        en = row.end_date or datetime.now(timezone.utc)
        
        # Create festival
        approved_item = Festival(
            name=row.name,
            description=row.description,
            significance=row.significance,
            start_date=st,
            end_date=en,
            nepali_date=row.nepali_date,
            region=row.region,
            is_location_specific=(row.latitude is not None and row.longitude is not None),
            location_name=row.location,
            latitude=row.latitude,
            longitude=row.longitude,
            locations=[{"lat": row.latitude, "lng": row.longitude}] if row.latitude is not None and row.longitude is not None else None,
            category=row.category,
            tags=row.tags,
            main_image=row.image_url,
            gallery=row.secondary_images,
            is_annual=row.is_annual,
            status=FestivalStatus.approved,
        )
        # Handle created_by more carefully since it's a UUID FK in Festival
        try:
            if isinstance(admin_user_id, str):
                approved_item.created_by = UUID(admin_user_id)
            else:
                approved_item.created_by = admin_user_id
        except (ValueError, TypeError):
            # Fallback to current admin user or handle error
            pass
            
        db.add(approved_item)
        db.flush() # Get the ID
        festival_id = approved_item.id
    else:
        # Create heritage site
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
        approved_item = HeritageSite(
            **site_data.model_dump(),
            created_by=row.created_by,      # original contributor
            contribution_id=row.id,
            is_pending=False,
        )
        # Audit on site
        approved_item.approved_by = str(admin_user_id)
        approved_item.approved_at = datetime.now(timezone.utc)
        db.add(approved_item)
        db.flush()
        heritage_site_id = approved_item.id

    # Update contribution status
    row.status = ContributionStatus.approved
    row.rejection_reason = None
    row.status_reason = comment
    row.approved_by = str(admin_user_id)
    row.approved_at = datetime.now(timezone.utc)

    # In-app notification for contributor
    try:
        region_str = f" in region {row.region}" if row.region else ""
        type_str = row.type.value if hasattr(row.type, 'value') else str(row.type)
        notif_msg = f"Your {type_str} contribution '{row.name}'{region_str} has been approved!"
        if comment:
            notif_msg += f"\n\nAdmin Comment: {comment}"
            
        notif_crud.create_notification(
            db,
            recipient_email=row.created_by,
            type="contribution_approved",
            title=f"Contribution Approved: {row.name}",
            message=notif_msg,
        )
    except Exception:
        pass

    db.commit()
    db.refresh(row)
    if approved_item:
        db.refresh(approved_item)
    
    return row, heritage_site_id, festival_id, intangible_id


def reject_contribution(db: Session, contrib_id: UUID, reason: str, admin_user_id: str):
    row = db.query(Contribution).filter(Contribution.id == contrib_id).first()
    if not row or row.status != ContributionStatus.pending:
        return None
    row.status = ContributionStatus.rejected
    row.rejection_reason = reason
    row.status_reason = reason
    row.updated_by = str(admin_user_id)
    row.updated_at = datetime.now(timezone.utc)
    try:
        region_str = f" in region {row.region}" if row.region else ""
        type_str = row.type.value if hasattr(row.type, 'value') else str(row.type)
        notif_msg = f"Your {type_str} contribution '{row.name}'{region_str} has been rejected.\n\nReason: {reason}"
        
        notif_crud.create_notification(
            db,
            recipient_email=row.created_by,
            type="contribution_rejected",
            title=f"Contribution Rejected: {row.name}",
            message=notif_msg,
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
