from sqlalchemy.orm import Session
from sqlalchemy import any_
from app.models.heritage_site import HeritageSite
from app.schemas.heritage_site import HeritageSiteCreate


def create_heritage_site(
    db: Session,
    site_data: HeritageSiteCreate,
    user_id: str,
    contribution_id: int | None = None
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


def get_filtered_sites(db: Session, region: str | None = None, category: str | None = None, tag: str | None = None):
    # Public should only see approved sites
    query = db.query(HeritageSite).filter(HeritageSite.is_pending == False)

    if region:
        query = query.filter(HeritageSite.region.ilike(f"%{region}%"))
    if category:
        query = query.filter(HeritageSite.category.ilike(f"%{category}%"))
    if tag:
        query = query.filter(tag == any_(HeritageSite.tags))

    return query.order_by(HeritageSite.created_at.desc()).all()


def get_site_by_id(db: Session, site_id: int):
    return db.query(HeritageSite).filter(HeritageSite.id == site_id).first()


def get_site_by_public_id(db: Session, public_id: str):
    # Public detail should only resolve approved entries
    return (
        db.query(HeritageSite)
        .filter(
            HeritageSite.public_id == public_id,
            HeritageSite.is_pending == False,
        )
        .first()
    )


def delete_site(db: Session, site_id: int):
    site = db.query(HeritageSite).filter(HeritageSite.id == site_id).first()
    if site:
        db.delete(site)
        db.commit()
    return site


def update_heritage_site(db: Session, site_id: int, site_data: HeritageSiteCreate):
    site = db.query(HeritageSite).filter(HeritageSite.id == site_id).first()
    if site:
        for k, v in site_data.model_dump(exclude_unset=True).items():
            setattr(site, k, v)
        db.commit()
        db.refresh(site)
    return site
