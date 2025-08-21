from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.models.user_favorite import UserFavorite
from app.models.heritage_site import HeritageSite


def add_favorite(db: Session, user_id: int, heritage_site_id: int) -> bool:
    fav = UserFavorite(user_id=user_id, heritage_site_id=heritage_site_id)
    db.add(fav)
    try:
        db.commit()
        return True
    except IntegrityError:
        db.rollback()
        # already exists or FK issue
        # Treat duplicate as success (idempotent add)
        return True


def remove_favorite(db: Session, user_id: int, heritage_site_id: int) -> bool:
    row = (
        db.query(UserFavorite)
        .filter(
            UserFavorite.user_id == user_id,
            UserFavorite.heritage_site_id == heritage_site_id,
        )
        .first()
    )
    if not row:
        return True  # idempotent remove
    db.delete(row)
    db.commit()
    return True


def list_favorites(db: Session, user_id: int):
    # join to sites and only return non-deleted, approved sites
    q = (
        db.query(HeritageSite)
        .join(UserFavorite, UserFavorite.heritage_site_id == HeritageSite.id)
        .filter(
            UserFavorite.user_id == user_id,
            HeritageSite.is_deleted == False,
            HeritageSite.is_pending == False,
        )
        .order_by(HeritageSite.created_at.desc())
    )
    return q.all()
