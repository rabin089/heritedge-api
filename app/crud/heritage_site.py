from sqlalchemy.orm import Session, joinedload
from sqlalchemy import any_, func
from uuid import UUID
from app.models.heritage_site import HeritageSite
from app.schemas.heritage_site import HeritageSiteCreate
from datetime import datetime, timezone


def create_heritage_site(
    db: Session,
    site_data: HeritageSiteCreate,
    user_id: str,
    contribution_id: UUID | None = None
):
    site = HeritageSite(
        **site_data.model_dump(),
        created_by=user_id,
        contribution_id=contribution_id,
        is_pending=False,
    )
    db.add(site)
    db.commit()
    db.refresh(site)
    return site


def get_filtered_sites(
    db: Session,
    region: str | None = None,
    category: str | None = None,
    tag: str | None = None,
    q: str | None = None,
    page: int | None = None,
    page_size: int | None = None,
):
    # Public should only see approved sites
    query = db.query(HeritageSite).options(joinedload(HeritageSite.creator_details)).filter(
        HeritageSite.is_pending == False,
        HeritageSite.is_deleted == False,
    )

    if region:
        query = query.filter(HeritageSite.region.ilike(f"%{region}%"))
    if category:
        query = query.filter(HeritageSite.category.ilike(f"%{category}%"))
    if tag:
        query = query.filter(tag == any_(HeritageSite.tags))
    if q:
        # fuzzy search on name, region, description, and tags string
        tag_str = func.array_to_string(HeritageSite.tags, ',')
        like = f"%{q}%"
        query = query.filter(
            (HeritageSite.name.ilike(like))
            | (HeritageSite.region.ilike(like))
            | (HeritageSite.description.ilike(like))
            | (tag_str.ilike(like))
        )

    query = query.order_by(HeritageSite.created_at.desc())

    # pagination (backward compatible: only apply if params provided)
    if page_size is not None or page is not None:
        p = page or 1
        ps = page_size or 20
        ps = min(max(ps, 1), 100)
        offset = (max(p, 1) - 1) * ps
        query = query.offset(offset).limit(ps)

    return query.all()


def get_site_by_id(db: Session, site_id: UUID):
    return (
        db.query(HeritageSite)
        .options(joinedload(HeritageSite.creator_details))
        .filter(HeritageSite.id == site_id, HeritageSite.is_deleted == False)
        .first()
    )


def delete_site(db: Session, site_id: UUID, acting_user_id: str | int):
    site = db.query(HeritageSite).filter(HeritageSite.id == site_id).first()
    if site and not site.is_deleted:
        site.is_deleted = True
        site.deleted_by = str(acting_user_id)
        site.deleted_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(site)
    return site


def update_heritage_site(db: Session, site_id: UUID, site_data: HeritageSiteCreate, acting_user_id: str | int | None = None):
    site = db.query(HeritageSite).filter(HeritageSite.id == site_id).first()
    if site:
        for k, v in site_data.model_dump(exclude_unset=True).items():
            setattr(site, k, v)
        if acting_user_id is not None:
            site.updated_by = str(acting_user_id)
            site.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(site)
    return site
