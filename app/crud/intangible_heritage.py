from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional
from uuid import UUID
from datetime import datetime, timezone
from app.models.intangible_heritage import IntangibleHeritage, IntangibleMedia
from app.schemas.intangible_heritage import (
    IntangibleHeritageCreate, 
    IntangibleHeritageUpdate,
    IntangibleMediaCreate
)


def create_intangible_heritage(db: Session, obj_in: IntangibleHeritageCreate, user_id: UUID) -> IntangibleHeritage:
    db_obj = IntangibleHeritage(
        **obj_in.model_dump(),
        contributor_id=user_id
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def get_intangible_heritage(db: Session, id: UUID) -> Optional[IntangibleHeritage]:
    return db.query(IntangibleHeritage).filter(IntangibleHeritage.id == id, IntangibleHeritage.deleted_at == None).first()


def list_intangible_heritages(
    db: Session, 
    skip: int = 0, 
    limit: int = 20, 
    category: Optional[str] = None,
    status: Optional[str] = "approved",
    search: Optional[str] = None
) -> List[IntangibleHeritage]:
    query = db.query(IntangibleHeritage).filter(IntangibleHeritage.deleted_at == None)
    
    if status:
        query = query.filter(IntangibleHeritage.status == status)
    
    if category:
        query = query.filter(IntangibleHeritage.category == category)
        
    if search:
        query = query.filter(
            or_(
                IntangibleHeritage.name_en.ilike(f"%{search}%"),
                IntangibleHeritage.name_np.ilike(f"%{search}%"),
                IntangibleHeritage.community.ilike(f"%{search}%")
            )
        )
        
    return query.order_by(IntangibleHeritage.created_at.desc()).offset(skip).limit(limit).all()


def list_my_intangible_heritages(
    db: Session, 
    user_id: UUID,
    status: Optional[str] = None
) -> List[IntangibleHeritage]:
    query = db.query(IntangibleHeritage).filter(
        IntangibleHeritage.contributor_id == user_id,
        IntangibleHeritage.deleted_at == None
    )
    if status:
        query = query.filter(IntangibleHeritage.status == status)
    return query.order_by(IntangibleHeritage.created_at.desc()).all()


def update_intangible_heritage(
    db: Session, db_obj: IntangibleHeritage, obj_in: IntangibleHeritageUpdate
) -> IntangibleHeritage:
    update_data = obj_in.model_dump(exclude_unset=True)
    for field in update_data:
        setattr(db_obj, field, update_data[field])
    
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def add_media_to_intangible_heritage(
    db: Session, intangible_id: UUID, obj_in: IntangibleMediaCreate, user_id: UUID
) -> IntangibleMedia:
    media_obj = IntangibleMedia(
        **obj_in.model_dump(),
        intangible_id=intangible_id,
        uploaded_by=user_id
    )
    db.add(media_obj)
    db.commit()
    db.refresh(media_obj)
    return media_obj


def update_status(
    db: Session, 
    db_obj: IntangibleHeritage, 
    status: str, 
    admin_id: UUID, 
    notes: Optional[str] = None
) -> IntangibleHeritage:
    db_obj.status = status
    db_obj.approved_by = admin_id
    
    if status == "approved":
        db_obj.approved_at = datetime.now(timezone.utc)
        db_obj.approval_notes = notes
    elif status == "rejected":
        db_obj.rejected_reason = notes
        
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def delete_intangible_heritage(db: Session, db_obj: IntangibleHeritage) -> IntangibleHeritage:
    db_obj.deleted_at = datetime.now(timezone.utc)
    db.add(db_obj)
    db.commit()
    return db_obj
