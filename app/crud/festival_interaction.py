from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime, timezone
from app.services.notification_service import notify_user
from app.models.festival_interaction import FestivalReaction, FestivalStory, FestivalReminder, FestivalDateSuggestion, StoryReaction
from app.models.festival import Festival
from app.schemas.festival_interaction import FestivalReactionCreate, FestivalStoryCreate, FestivalStoryUpdate, FestivalReminderCreate, FestivalDateSuggestionCreate, StoryReactionCreate
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
            
            # NOTIFY: New story on a festival (Notify people who reacted to the festival)
            festival = db.query(Festival).filter(Festival.id == story_in.festival_id).first()
            if festival:
                # Get everyone who "hearted" (reacted) to this festival
                followers = db.query(FestivalReaction).filter(
                    FestivalReaction.festival_id == festival.id,
                    FestivalReaction.user_email != user_email  # Don't notify the author
                ).all()
                
                for follower in followers:
                    notify_user(
                        db=db,
                        user_email=follower.user_email,
                        title=f"📸 New story for {festival.name}",
                        body="Someone just shared a new experience! Swipe to see it.",
                        data={"type": "new_story", "festival_id": str(festival.id), "screen": "festival_detail"}
                    )
            
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

    def toggle_story_reaction(self, db: Session, user_email: str, reaction_in: StoryReactionCreate) -> Dict[str, Any]:
        """Toggle a reaction for a specific story."""
        existing = db.query(StoryReaction).filter(
            StoryReaction.story_id == reaction_in.story_id,
            StoryReaction.user_email == user_email,
            StoryReaction.reaction_type == reaction_in.reaction_type
        ).first()

        if existing:
            db.delete(existing)
            db.commit()
            return {"status": "removed", "reaction": None}
            
        new_reaction = StoryReaction(
            story_id=reaction_in.story_id,
            user_email=user_email,
            reaction_type=reaction_in.reaction_type
        )
        db.add(new_reaction)
        try:
            db.commit()
            db.refresh(new_reaction)
            
            # NOTIFY: User liked a story
            story = db.query(FestivalStory).filter(FestivalStory.id == reaction_in.story_id).first()
            if story and story.user_email != user_email:
                from app.models.user import User
                # Simple lookup for name to make it personalized
                reactor = db.query(User).filter(User.email == user_email).first()
                name = reactor.display_name or reactor.name or "Someone"
                notify_user(
                    db=db,
                    user_email=story.user_email,
                    title="❤️ New Story Reaction",
                    body=f"{name} hearted your experience story!",
                    data={"type": "story_reaction", "story_id": str(story.id), "screen": "festival_detail"}
                )
            
            return {"status": "added", "reaction": new_reaction}
        except IntegrityError:
            db.rollback()
            raise HTTPException(status_code=400, detail="Could not add story reaction")

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

    # Reminders
    def create_or_update_reminder(self, db: Session, user_email: str, reminder_in: FestivalReminderCreate) -> FestivalReminder:
        existing = db.query(FestivalReminder).filter(
            FestivalReminder.festival_id == reminder_in.festival_id,
            FestivalReminder.user_email == user_email
        ).first()

        if existing:
            existing.reminder_dates = reminder_in.reminder_dates
            if reminder_in.is_active is not None:
                existing.is_active = reminder_in.is_active
            existing.updated_at = datetime.now(timezone.utc)
            db.commit()
            db.refresh(existing)
            return existing

        db_reminder = FestivalReminder(
            festival_id=reminder_in.festival_id,
            user_email=user_email,
            reminder_dates=reminder_in.reminder_dates,
            is_active=reminder_in.is_active if reminder_in.is_active is not None else True
        )
        db.add(db_reminder)
        try:
            db.commit()
            db.refresh(db_reminder)
            return db_reminder
        except IntegrityError:
            db.rollback()
            raise HTTPException(status_code=400, detail="Could not set reminder")

    def get_user_reminders(self, db: Session, user_email: str) -> List[FestivalReminder]:
        return db.query(FestivalReminder).filter(
            FestivalReminder.user_email == user_email,
            FestivalReminder.is_active == True
        ).all()

    def remove_reminder(self, db: Session, festival_id: UUID, user_email: str) -> bool:
        reminder = db.query(FestivalReminder).filter(
            FestivalReminder.festival_id == festival_id,
            FestivalReminder.user_email == user_email
        ).first()
        
        if reminder:
            db.delete(reminder)
            db.commit()
            return True
        return False

    # Date Suggestions
    def suggest_date(self, db: Session, user_email: str, suggestion_in: FestivalDateSuggestionCreate) -> FestivalDateSuggestion:
        db_suggestion = FestivalDateSuggestion(
            festival_id=suggestion_in.festival_id,
            user_email=user_email,
            proposed_start_date=suggestion_in.proposed_start_date,
            proposed_end_date=suggestion_in.proposed_end_date,
            proposed_nepali_date=suggestion_in.proposed_nepali_date,
            status="pending"
        )
        db.add(db_suggestion)
        try:
            db.commit()
            db.refresh(db_suggestion)
            return db_suggestion
        except IntegrityError:
            db.rollback()
            raise HTTPException(status_code=400, detail="Could not submit suggestion")

    def increment_views(self, db: Session, festival_id: UUID) -> bool:
        festival = db.query(Festival).filter(Festival.id == festival_id).first()
        if not festival:
            return False
        if festival.views_count is None:
            festival.views_count = 0
        festival.views_count += 1
        db.commit()
        return True

festival_interaction = CRUDFestivalInteraction()
