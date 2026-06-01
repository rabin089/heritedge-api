from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID

from app.core.database import get_db
from app.api.v1.auth import get_current_user
from app.schemas.festival_interaction import (
    FestivalReactionCreate,
    FestivalReactionOut,
    FestivalStoryCreate,
    FestivalStoryUpdate,
    FestivalStoryOut,
    FestivalStats,
    FestivalReminderCreate,
    FestivalReminderOut,
    FestivalDateSuggestionCreate,
    FestivalDateSuggestionOut,
    StoryReactionCreate,
    StoryReactionOut
)
from app.crud.festival_interaction import festival_interaction

router = APIRouter(prefix="/festivals/interactions", tags=["festival-interactions"])


@router.post("/reactions")
def toggle_reaction(
    reaction_in: FestivalReactionCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Toggle a reaction (heart) for a festival.
    If the reaction exists, it will be removed. If it doesn't, it will be added.
    """
    return festival_interaction.toggle_reaction(db=db, user_email=current_user.email, reaction_in=reaction_in)


@router.post("/stories", response_model=FestivalStoryOut)
def create_story(
    story_in: FestivalStoryCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Share an experience story for a festival.
    """
    return festival_interaction.create_story(db=db, user_email=current_user.email, story_in=story_in)


@router.get("/stories/{festival_id}")
def get_festival_stories(
    festival_id: UUID,
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db)
) -> list[FestivalStoryOut]:
    """
    Get all stories for a specific festival.
    """
    return festival_interaction.get_stories_by_festival(db=db, festival_id=festival_id, skip=skip, limit=limit)


@router.put("/stories/{story_id}", response_model=FestivalStoryOut)
def update_story(
    story_id: UUID,
    update_in: FestivalStoryUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Update an existing story.
    """
    story = festival_interaction.get_story(db=db, story_id=story_id)
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")
    
    if story.user_email != current_user.email:
        raise HTTPException(status_code=403, detail="Not enough permissions to update this story")
        
    return festival_interaction.update_story(db=db, db_story=story, story_in=update_in)


@router.delete("/stories/{story_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_story(
    story_id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Delete a story.
    """
    story = festival_interaction.get_story(db=db, story_id=story_id)
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")
        
    if story.user_email != current_user.email:
        raise HTTPException(status_code=403, detail="Not enough permissions to delete this story")
        
    festival_interaction.delete_story(db=db, db_story=story)


@router.post("/stories/{story_id}/reactions")
def toggle_story_reaction(
    story_id: UUID,
    reaction_in: StoryReactionCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Toggle a reaction for a specific story.
    """
    if reaction_in.story_id != story_id:
        raise HTTPException(status_code=400, detail="Path story_id and body story_id must match")
    return festival_interaction.toggle_story_reaction(db=db, user_email=current_user.email, reaction_in=reaction_in)


@router.get("/stats/{festival_id}", response_model=FestivalStats)
def get_festival_stats(
    festival_id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get interaction stats (total reactions, stories) for a festival.
    Also returns whether the current user has reacted.
    """
    return festival_interaction.get_festival_stats(db=db, festival_id=festival_id, user_email=current_user.email)


@router.post("/reminders", response_model=FestivalReminderOut)
def set_reminder(
    reminder_in: FestivalReminderCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Set or update reminder dates for a specific festival for the current user.
    """
    return festival_interaction.create_or_update_reminder(db=db, user_email=current_user.email, reminder_in=reminder_in)


@router.get("/reminders", response_model=list[FestivalReminderOut])
def get_reminders(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get all active reminders for the current user.
    """
    return festival_interaction.get_user_reminders(db=db, user_email=current_user.email)


@router.delete("/reminders/{festival_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_reminder(
    festival_id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Completely remove a reminder for a specific festival.
    """
    success = festival_interaction.remove_reminder(db=db, festival_id=festival_id, user_email=current_user.email)
    if not success:
        raise HTTPException(status_code=404, detail="Reminder not found")


@router.post("/suggestions", response_model=FestivalDateSuggestionOut)
def suggest_festival_date(
    suggestion_in: FestivalDateSuggestionCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Suggest a new date for a festival that changes every year (e.g. crowdsourced variable).
    """
    return festival_interaction.suggest_date(db=db, user_email=current_user.email, suggestion_in=suggestion_in)


@router.post("/views/{festival_id}", status_code=status.HTTP_200_OK)
def increment_festival_views(
    festival_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Increment the view count of a festival when a user opens the details page.
    """
    success = festival_interaction.increment_views(db=db, festival_id=festival_id)
    if not success:
        raise HTTPException(status_code=404, detail="Festival not found")
    return {"message": "View incremented successfully"}
