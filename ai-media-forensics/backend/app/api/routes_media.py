import os
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.models.database import get_db
from app.models.db_models import Media, ProvenanceRecord, AuditLog
from app.models.schemas import MediaUploadResponse, MediaResponse, MediaMetadataResponse, AuditLogResponse
from app.services.media_service import ingest_media_file

router = APIRouter(prefix="/media", tags=["Media"])

@router.post("/upload", response_model=MediaUploadResponse, status_code=201)
async def upload_media_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Forensic media ingestion endpoint:
    - Validates MIME & file signatures
    - Computes cryptographic SHA-256 hash
    - Stores unaltered evidence in originals vault
    - Creates normalized RGB analysis copy
    - Extracts EXIF & prompt metadata
    - Records immutable audit log
    """
    result = await ingest_media_file(file=file, db=db, user="system")
    return result

@router.get("/{media_id}", response_model=MediaResponse)
def get_media_details(media_id: str, db: Session = Depends(get_db)):
    """Retrieve metadata and storage information for an ingested media file."""
    media = db.query(Media).filter(Media.id == media_id).first()
    if not media:
        raise HTTPException(status_code=404, detail=f"Media with ID '{media_id}' not found.")
    return media

@router.get("/{media_id}/metadata", response_model=MediaMetadataResponse)
def get_media_metadata(media_id: str, db: Session = Depends(get_db)):
    """Retrieve extracted EXIF and technical metadata for a media item."""
    record = db.query(ProvenanceRecord).filter(ProvenanceRecord.media_id == media_id).first()
    if not record:
        raise HTTPException(status_code=404, detail=f"Provenance metadata for '{media_id}' not found.")
    return {
        "media_id": media_id,
        "sha256": record.sha256,
        "metadata": record.metadata_json or {}
    }

@router.get("/{media_id}/file")
def get_media_file(
    media_id: str,
    target: str = Query("original", pattern="^(original|analysis)$"),
    db: Session = Depends(get_db)
):
    """Serve the original or normalized analysis copy for browser inspection and UI preview."""
    media = db.query(Media).filter(Media.id == media_id).first()
    if not media:
        raise HTTPException(status_code=404, detail=f"Media '{media_id}' not found.")

    file_path = media.storage_path if target == "original" else (media.analysis_copy_path or media.storage_path)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found on storage disk.")

    return FileResponse(
        path=file_path,
        media_type=media.mime_type if target == "original" else "image/png",
        filename=os.path.basename(file_path)
    )

@router.get("/{media_id}/audit", response_model=list[AuditLogResponse])
def get_media_audit_trail(media_id: str, db: Session = Depends(get_db)):
    """Retrieve immutable audit log history for forensic chain of custody."""
    logs = db.query(AuditLog).filter(AuditLog.media_id == media_id).order_by(AuditLog.timestamp.desc()).all()
    return logs
