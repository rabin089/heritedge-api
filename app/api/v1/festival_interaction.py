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
    FestivalStats
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
