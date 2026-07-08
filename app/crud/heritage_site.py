from sqlalchemy.orm import Session, joinedload
from sqlalchemy import any_, func
from uuid import UUID
from app.models.heritage_site import HeritageSite
from app.schemas.heritage_site import HeritageSiteCreate
from datetime import datetime, timezone
from app.utils.geocoding_util import get_location_name_from_coordinates
from app.utils.search_algorithms import best_fuzzy_score, haversine_distance_km


def create_heritage_site(
    db: Session,
    site_data: HeritageSiteCreate,
    user_id: str,
    contribution_id: UUID | None = None
):
    if site_data.latitude is not None and site_data.longitude is not None:
        loc_name = get_location_name_from_coordinates(site_data.latitude, site_data.longitude)
        if loc_name:
            site_data.location = loc_name
            
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
    latitude: float | None = None,
    longitude: float | None = None,
    radius_km: float | None = None,
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
    query = query.order_by(HeritageSite.created_at.desc())
    sites = query.all()

    if q:
        sites = [
            site for site in sites
            if best_fuzzy_score(
                q,
                [
                    site.name,
                    site.region,
                    site.location,
                    site.description,
                    site.category,
                    ",".join(site.tags or []),
                ],
            ) >= 0.62
        ]
        sites.sort(
            key=lambda site: best_fuzzy_score(
                q,
                [
                    site.name,
                    site.region,
                    site.location,
                    site.description,
                    site.category,
                    ",".join(site.tags or []),
                ],
            ),
            reverse=True,
        )

    if latitude is not None and longitude is not None:
        sites_with_distance = []
        for site in sites:
            if site.latitude is None or site.longitude is None:
                continue
            distance_km = haversine_distance_km(latitude, longitude, site.latitude, site.longitude)
            if radius_km is None or distance_km <= radius_km:
                site.distance_km = round(distance_km, 2)
                sites_with_distance.append(site)
        sites = sorted(sites_with_distance, key=lambda site: site.distance_km)

    if page_size is not None or page is not None:
        p = max(page or 1, 1)
        ps = min(max(page_size or 20, 1), 100)
        offset = (p - 1) * ps
        sites = sites[offset:offset + ps]

    return sites


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
        if site_data.latitude is not None and site_data.longitude is not None:
            loc_name = get_location_name_from_coordinates(site_data.latitude, site_data.longitude)
            if loc_name:
                site_data.location = loc_name
                
        for k, v in site_data.model_dump(exclude_unset=True).items():
            setattr(site, k, v)
        if acting_user_id is not None:
            site.updated_by = str(acting_user_id)
            site.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(site)
    return site
