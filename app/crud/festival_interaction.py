from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime, timezone
from app.models.festival_interaction import FestivalReaction, FestivalStory
from app.schemas.festival_interaction import FestivalReactionCreate, FestivalStoryCreate, FestivalStoryUpdate
from fastapi import HTTPException


class CRUDFestivalInteraction:
    # Reactions
    def toggle_reaction(self, db: Session, user_email: str, reaction_in: FestivalReactionCreate) -> Dict[str, Any]:
        """Toggle a reaction (heart) for a festival."""
        existing_reaction = db.query(FestivalReaction).filter(
            FestivalReaction.festival_id == reaction_in.festival_id,
            FestivalReaction.user_email == user_email,
            FestivalReaction.reaction_type == reaction_in.reaction_type
        ).first()

        if existing_reaction:
            db.delete(existing_reaction)
            db.commit()
            return {"status": "removed", "reaction": None}
        
        new_reaction = FestivalReaction(
            festival_id=reaction_in.festival_id,
            user_email=user_email,
            reaction_type=reaction_in.reaction_type
        )
        db.add(new_reaction)
        try:
            db.commit()
            db.refresh(new_reaction)
            return {"status": "added", "reaction": new_reaction}
        except IntegrityError:
            db.rollback()
            raise HTTPException(status_code=400, detail="Could not add reaction")

    def get_reactions_for_festival(self, db: Session, festival_id: UUID) -> List[FestivalReaction]:
        return db.query(FestivalReaction).filter(FestivalReaction.festival_id == festival_id).all()

    def get_user_reactions(self, db: Session, user_email: str, skip: int = 0, limit: int = 100) -> List[FestivalReaction]:
        return db.query(FestivalReaction).filter(
            FestivalReaction.user_email == user_email
        ).offset(skip).limit(limit).all()

    # Stories
    def create_story(self, db: Session, user_email: str, story_in: FestivalStoryCreate) -> FestivalStory:
        # Check if user already has a story for this festival
        existing = db.query(FestivalStory).filter(
            FestivalStory.festival_id == story_in.festival_id,
            FestivalStory.user_email == user_email
        ).first()
        
        if existing:
            raise HTTPException(status_code=400, detail="You have already shared a story for this festival")

        db_story = FestivalStory(
            festival_id=story_in.festival_id,
            user_email=user_email,
            content=story_in.content,
            media_urls=story_in.media_urls
        )
        db.add(db_story)
        try:
            db.commit()
            db.refresh(db_story)
            return db_story
        except IntegrityError:
            db.rollback()
            raise HTTPException(status_code=400, detail="Could not create story")

    def get_stories_by_festival(self, db: Session, festival_id: UUID, skip: int = 0, limit: int = 10) -> List[FestivalStory]:
        return db.query(FestivalStory).filter(
            FestivalStory.festival_id == festival_id
        ).order_by(FestivalStory.created_at.desc()).offset(skip).limit(limit).all()

    def get_story(self, db: Session, story_id: UUID) -> Optional[FestivalStory]:
        return db.query(FestivalStory).filter(FestivalStory.id == story_id).first()

    def update_story(self, db: Session, db_story: FestivalStory, story_in: FestivalStoryUpdate) -> FestivalStory:
        update_data = story_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_story, field, value)
        
        db_story.updated_at = datetime.now(timezone.utc)
        db.add(db_story)
        db.commit()
        db.refresh(db_story)
        return db_story

    def delete_story(self, db: Session, db_story: FestivalStory) -> bool:
        db.delete(db_story)
        db.commit()
        return True

    # Stats
    def get_festival_stats(self, db: Session, festival_id: UUID, user_email: Optional[str] = None) -> Dict[str, Any]:
        total_reactions = db.query(FestivalReaction).filter(FestivalReaction.festival_id == festival_id).count()
        total_stories = db.query(FestivalStory).filter(FestivalStory.festival_id == festival_id).count()
        
        user_has_reacted = False
        if user_email:
            reaction = db.query(FestivalReaction).filter(
                FestivalReaction.festival_id == festival_id,
                FestivalReaction.user_email == user_email
            ).first()
            if reaction:
                user_has_reacted = True
                
        return {
            "total_reactions": total_reactions,
            "total_stories": total_stories,
            "user_has_reacted": user_has_reacted
        }

festival_interaction = CRUDFestivalInteraction()
