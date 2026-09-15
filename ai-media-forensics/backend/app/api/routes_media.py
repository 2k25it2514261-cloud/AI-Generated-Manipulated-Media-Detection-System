from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.models.database import get_db
from app.models.db_models import Media
from app.models.schemas import MediaResponse

router = APIRouter(prefix="/media", tags=["Media"])

@router.get("/{media_id}", response_model=MediaResponse)
def get_media_details(media_id: str, db: Session = Depends(get_db)):
    """Retrieve metadata and storage information for an ingested media file."""
    media = db.query(Media).filter(Media.id == media_id).first()
    if not media:
        raise HTTPException(status_code=404, detail="Media record not found")
    return media
