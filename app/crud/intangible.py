from sqlalchemy.orm import Session, joinedload
from app.models.intangible_heritage import IntangibleHeritage
from uuid import UUID


def get_intangible_by_id(db: Session, intangible_id: UUID):
    return db.query(IntangibleHeritage).options(
        joinedload(IntangibleHeritage.media),
        joinedload(IntangibleHeritage.creator_details)
    ).filter(IntangibleHeritage.id == intangible_id, IntangibleHeritage.deleted_at == None).first()


def list_intangible_heritage(db: Session, category: str = None, community: str = None):
    q = db.query(IntangibleHeritage).options(
        joinedload(IntangibleHeritage.media),
        joinedload(IntangibleHeritage.creator_details)
    ).filter(IntangibleHeritage.deleted_at == None)
    
    if category:
        q = q.filter(IntangibleHeritage.category == category)
    if community:
        q = q.filter(IntangibleHeritage.community.ilike(f"%{community}%"))
        
    return q.order_by(IntangibleHeritage.created_at.desc()).all()
