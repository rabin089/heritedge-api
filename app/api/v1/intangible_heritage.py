from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from app.core.database import SessionLocal
from app.models.user import User
from app.api.v1.auth import get_current_user
from app.schemas.intangible_heritage import (
    IntangibleHeritageCreate, 
    IntangibleHeritageUpdate, 
    IntangibleHeritageOut,
    IntangibleMediaCreate,
    IntangibleMediaOut,
    IntangibleStatusUpdate
)
from app.crud import intangible_heritage as crud
from app.api.v1._role import is_admin, is_reviewer
from app.crud import contributions as contrib_crud
from app.schemas.contribution import ContributionCreate, ContributionOut
from app.models.contribution import ContributionType

router = APIRouter(prefix="/intangible-heritage", tags=["intangible_heritage"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("", response_model=IntangibleHeritageOut, responses={202: {"model": ContributionOut}}, status_code=status.HTTP_201_CREATED)
def create_tradition(
    payload: IntangibleHeritageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Submit an intangible heritage tradition.
    - **Admin/Superadmin**: Tradition is created directly and marked as approved.
    - **Regular user**: Tradition is queued as a pending Contribution. It will
      appear in the Admin review list under GET /admin/contributions/pending
      (type=intangible). Once approved, it will be published to the intangible_heritage table.
    """
    # Admin: create directly and mark approved
    if is_admin(current_user):
        return crud.create_intangible_heritage(db, payload, current_user.id)

    # Regular user: go through contribution review queue
    contrib_payload = ContributionCreate(
        type=ContributionType.intangible,
        name=payload.name_en, # Use English name for unified name
        name_np=payload.name_np,
        description=payload.description,
        category=payload.category,
        community=payload.community,
        language=payload.language,
        festival_id=payload.location_id, # Reusing festival_id column to map location_id
        practiced_at=payload.practiced_at_description,
        risk_level=payload.risk_level,
        image_url=payload.image_url,
        secondary_images=payload.secondary_images,
        video_url=payload.video_url,
        audio_url=payload.audio_url,
        contributor_name=current_user.display_name or current_user.name,
        contributor_email=current_user.email,
    )
    contrib = contrib_crud.create_contribution(db, contrib_payload, user_id=current_user.email)

    # Return a 202 Accepted with the contribution details so the frontend knows
    # the tradition is under review, not yet published.
    return JSONResponse(
        status_code=status.HTTP_202_ACCEPTED,
        content={
            "message": "Intangible heritage submitted for review. It will be published once an admin approves it.",
            "contribution_id": str(contrib.id),
            "status": contrib.status,
            "type": contrib.type,
        }
    )


@router.get("", response_model=List[IntangibleHeritageOut])
def list_traditions(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    category: Optional[str] = None,
    search: Optional[str] = None,
    status: Optional[str] = "approved",
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user) # might want public read later
):
    """List intangible heritages (feed view)."""
    # Only admins can view non-approved items
    if status != "approved":
        if not current_user or not (is_admin(current_user) or is_reviewer(current_user)):
            raise HTTPException(status_code=403, detail="Not authorized to filter non-approved items")
            
    return crud.list_intangible_heritages(
        db, skip=skip, limit=limit, category=category, status=status, search=search
    )


@router.get("/me", response_model=List[IntangibleHeritageOut])
def my_traditions(
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve intangible heritage contributions created by the current user."""
    return crud.list_my_intangible_heritages(db, current_user.id, status=status)


@router.get("/{id}", response_model=IntangibleHeritageOut)
def get_tradition(
    id: UUID, 
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    """Retrieve full details of an intangible heritage tradition."""
    tradition = crud.get_intangible_heritage(db, id)
    if not tradition:
        raise HTTPException(status_code=404, detail="Intangible heritage not found")
        
    # Security: Only creator or admin can view if not approved
    if tradition.status != "approved":
        if not current_user or (tradition.contributor_id != current_user.id and not is_admin(current_user)):
            raise HTTPException(status_code=403, detail="Not authorized to view pending contributions")
            
    # Optionally: Here you would create an engagement record for "view" in production
    
    return tradition


@router.put("/{id}", response_model=IntangibleHeritageOut)
def update_tradition(
    id: UUID,
    payload: IntangibleHeritageUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a pending heritage submission (Creator) or approve/flag (Admin)."""
    tradition = crud.get_intangible_heritage(db, id)
    if not tradition:
        raise HTTPException(status_code=404, detail="Intangible heritage not found")
        
    # Authorization checks
    is_owner = tradition.contributor_id == current_user.id
    isAdmin = is_admin(current_user)
    
    if not is_owner and not isAdmin:
        raise HTTPException(status_code=403, detail="Not authorized to modify this record")
        
    if is_owner and not isAdmin and tradition.status == "approved":
        raise HTTPException(status_code=400, detail="Cannot modify an already approved tradition")
        
    # Prevent users from upgrading their own status
    if not isAdmin and payload.status and payload.status != "draft" and payload.status != "pending":
         raise HTTPException(status_code=403, detail="Not authorized to change moderation status")

    return crud.update_intangible_heritage(db, tradition, payload)


@router.post("/{id}/media", response_model=IntangibleMediaOut, status_code=status.HTTP_201_CREATED)
def attach_media(
    id: UUID,
    payload: IntangibleMediaCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Attach media (video/audio/photo) to an intangible heritage."""
    tradition = crud.get_intangible_heritage(db, id)
    if not tradition:
        raise HTTPException(status_code=404, detail="Intangible heritage not found")
        
    # Only allow owners to add media initially
    if tradition.contributor_id != current_user.id and not is_admin(current_user):
        raise HTTPException(status_code=403, detail="Not authorized to attach media")
        
    return crud.add_media_to_intangible_heritage(db, id, payload, current_user.id)


@router.post("/{id}/moderate", response_model=IntangibleHeritageOut)
def moderate_tradition(
    id: UUID,
    payload: IntangibleStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Admin endpoint to approve, reject, or archive a tradition."""
    if not is_admin(current_user) and not is_reviewer(current_user):
        raise HTTPException(status_code=403, detail="Not authorized as moderator")
        
    tradition = crud.get_intangible_heritage(db, id)
    if not tradition:
        raise HTTPException(status_code=404, detail="Intangible heritage not found")
        
    return crud.update_status(db, tradition, payload.status, current_user.id, payload.notes)


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tradition(
    id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Soft delete an intangible heritage (Creator or Admin)."""
    tradition = crud.get_intangible_heritage(db, id)
    if not tradition:
        raise HTTPException(status_code=404, detail="Not found")
        
    if tradition.contributor_id != current_user.id and not is_admin(current_user):
        raise HTTPException(status_code=403, detail="Not authorized to delete")
        
    crud.delete_intangible_heritage(db, tradition)
    return None
