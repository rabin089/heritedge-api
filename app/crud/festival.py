from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload
from app.services.notification_service import notify_user
from sqlalchemy import and_, or_, func, text, cast
from sqlalchemy.dialects.postgresql import JSONB
from app.models.festival import Festival, FestivalHeritageSite, FestivalStatus, FestivalCategory
from app.models.heritage_site import HeritageSite
from app.schemas.festival import FestivalCreate, FestivalUpdate, FestivalHeritageSiteCreate
from uuid import UUID
import uuid


class FestivalCRUD:
    def get(self, db: Session, festival_id: UUID) -> Optional[Festival]:
        """Get a festival by ID"""
        return db.query(Festival).options(joinedload(Festival.user)).filter(Festival.id == festival_id).first()

    def get_multi(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        region: Optional[str] = None,
        category: Optional[FestivalCategory] = None,
        status: Optional[FestivalStatus] = None,
        created_by: Optional[str] = None,
        tag: Optional[str] = None,
        q: Optional[str] = None,
        is_approved: Optional[bool] = None, # Legacy support or mapping
        include_unapproved: bool = False
    ) -> tuple[List[Festival], int]:
        """Get multiple festivals with filters and pagination"""
        query = db.query(Festival).options(joinedload(Festival.user))
        
        # Apply filters
        if created_by:
            query = query.filter(Festival.created_by == UUID(created_by))

        if region:
            query = query.filter(Festival.region.ilike(f"%{region}%"))
        
        if category:
            query = query.filter(Festival.category == category)
        
        if status:
            query = query.filter(Festival.status == status)
        elif is_approved is not None:
            if is_approved:
                query = query.filter(Festival.status == FestivalStatus.approved)
            else:
                query = query.filter(Festival.status != FestivalStatus.approved)
        elif not include_unapproved:
            # Default to approved only for public listings
            query = query.filter(Festival.status == FestivalStatus.approved)
        
        if tag:
            # Assumes tags is ARRAY(String)
            query = query.filter(func.array_to_string(Festival.tags, ',').ilike(f"%{tag}%"))
        
        if q:
            # Fuzzy search across multiple fields
            search_filter = or_(
                Festival.name.ilike(f"%{q}%"),
                Festival.description.ilike(f"%{q}%"),
                Festival.significance.ilike(f"%{q}%"),
            )
            query = query.filter(search_filter)
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        festivals = query.offset(skip).limit(limit).all()
        
        return festivals, total

    def create(self, db: Session, obj_in: FestivalCreate, created_by: str, status: FestivalStatus = FestivalStatus.pending) -> Festival:
        """Create a new festival"""
        # Convert created_by str to UUID if needed, DB expects UUID
        # obj_in locations is List[LatLng], Pydantic handles it, DB expects JSONB compatible list of dicts.
        # .model_dump() usually converts sub-models to dicts which is perfect for JSONB.
        
        db_obj = Festival(
            **obj_in.model_dump(),
            created_by=UUID(created_by),
            status=status
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(
        self,
        db: Session,
        db_obj: Festival,
        obj_in: FestivalUpdate,
        updated_by: str
    ) -> Festival:
        """Update a festival"""
        # updated_by kept in audit logic but user schema didn't have updated_by/at fields.
        # I removed them from model. So I can't set them.
        # I will just update fields.
        
        update_data = obj_in.model_dump(exclude_unset=True)
        # update_data["updated_by"] = updated_by # Field removed
        
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def approve(
        self,
        db: Session,
        festival_id: UUID,
        approved_by: str,
        approval_reason: Optional[str] = None
    ) -> Optional[Festival]:
        """Approve a festival"""
        festival = self.get(db, festival_id)
        if festival:
            festival.status = FestivalStatus.approved
            festival.moderation_note = approval_reason
            db.commit()
            db.refresh(festival)
            
            # NOTIFY: Festival Approved
            from app.models.user import User
            owner = db.query(User).filter(User.id == festival.created_by).first()
            if owner:
                notify_user(
                    db=db,
                    user_email=owner.email,
                    title="✅ Festival Approved!",
                    body=f"Great news! Your festival '{festival.name}' has been approved and is now live on Heritedge.",
                    data={"type": "festival_approved", "festival_id": str(festival_id), "screen": "festival_detail"}
                )
        return festival

    def reject(
        self,
        db: Session,
        festival_id: UUID,
        approved_by: str,
        rejection_reason: str
    ) -> Optional[Festival]:
        """Reject a festival"""
        festival = self.get(db, festival_id)
        if festival:
            festival.status = FestivalStatus.rejected
            festival.moderation_note = rejection_reason
            db.commit()
            db.refresh(festival)
            
            # NOTIFY: Festival Rejected/Changes Requested
            from app.models.user import User
            owner = db.query(User).filter(User.id == festival.created_by).first()
            if owner:
                notify_user(
                    db=db,
                    user_email=owner.email,
                    title="📝 Update needed for your festival",
                    body=f"The moderators have requested changes for '{festival.name}'. Check the note for details.",
                    data={"type": "festival_rejected", "festival_id": str(festival_id), "screen": "festival_edit"}
                )
        return festival

    def delete(self, db: Session, festival_id: UUID) -> bool:
        """Hard delete a festival"""
        festival = self.get(db, festival_id)
        if festival:
            db.delete(festival)
            db.commit()
            return True
        return False

    def get_upcoming_festivals(self, db: Session, limit: int = 10) -> List[Festival]:
        """Get upcoming approved festivals"""
        return db.query(Festival).options(joinedload(Festival.user)).filter(
            and_(
                Festival.status == FestivalStatus.approved,
                Festival.start_date > func.now()
            )
        ).order_by(Festival.start_date).limit(limit).all()

    def get_ongoing_festivals(self, db: Session) -> List[Festival]:
        """Get currently ongoing approved festivals"""
        now = func.now()
        return db.query(Festival).options(joinedload(Festival.user)).filter(
            and_(
                Festival.status == FestivalStatus.approved,
                Festival.start_date <= now,
                Festival.end_date >= now
            )
        ).all()

    def get_calendar_festivals(self, db: Session, year: Optional[int] = None, month: Optional[int] = None) -> List[Festival]:
        """Get approved festivals filtered by optional year and month for calendar views"""
        from sqlalchemy import extract
        query = db.query(Festival).options(joinedload(Festival.user)).filter(
            Festival.status == FestivalStatus.approved
        )
        
        if year:
            query = query.filter(extract('year', Festival.start_date) == year)
        if month:
            query = query.filter(extract('month', Festival.start_date) == month)
            
        return query.order_by(Festival.start_date).all()


class FestivalHeritageSiteCRUD:
    def create(self, db: Session, obj_in: FestivalHeritageSiteCreate, created_by: str) -> FestivalHeritageSite:
        """Create a festival-heritage site relationship"""
        db_obj = FestivalHeritageSite(
            **obj_in.model_dump(),
            created_by=created_by
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get_by_festival(self, db: Session, festival_id: UUID) -> List[FestivalHeritageSite]:
        """Get all heritage sites associated with a festival"""
        return db.query(FestivalHeritageSite).filter(
            FestivalHeritageSite.festival_id == festival_id
        ).all()

    def get_by_heritage_site(self, db: Session, heritage_site_id: UUID) -> List[FestivalHeritageSite]:
        """Get all festivals associated with a heritage site"""
        return db.query(FestivalHeritageSite).filter(
            FestivalHeritageSite.heritage_site_id == heritage_site_id
        ).all()

    def remove(self, db: Session, festival_id: UUID, heritage_site_id: UUID) -> bool:
        """Remove a festival-heritage site relationship"""
        relationship = db.query(FestivalHeritageSite).filter(
            and_(
                FestivalHeritageSite.festival_id == festival_id,
                FestivalHeritageSite.heritage_site_id == heritage_site_id
            )
        ).first()
        
        if relationship:
            db.delete(relationship)
            db.commit()
            return True
        return False


# Create singleton instances
festival_crud = FestivalCRUD()
festival_heritage_site_crud = FestivalHeritageSiteCRUD()
