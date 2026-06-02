from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from sqlalchemy.orm import Session
from uuid import UUID
from app.core.database import get_db
from app.schemas.intangible import IntangibleHeritageOut
from app.crud import intangible as crud

router = APIRouter(prefix="/intangible", tags=["intangible"])


@router.get("", response_model=List[IntangibleHeritageOut])
def list_intangible_heritage(
    category: Optional[str] = Query(None),
    community: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """List all approved intangible heritage traditions"""
    return crud.list_intangible_heritage(db, category=category, community=community)


@router.get("/{intangible_id}", response_model=IntangibleHeritageOut)
def get_intangible_detail(
    intangible_id: UUID,
    db: Session = Depends(get_db)
):
    """Get detailed information about a specific tradition"""
    item = crud.get_intangible_by_id(db, intangible_id)
    if not item:
        raise HTTPException(status_code=404, detail="Intangible heritage not found")
    return item
