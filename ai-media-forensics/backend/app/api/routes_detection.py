from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session

from app.models.database import get_db
from app.models.db_models import DetectionResult, Media
from app.models.schemas import ImageDetectionResponse, VideoJobResponse
from app.services.media_service import ingest_media_file
from app.services.detection_service import analyze_image_media

router = APIRouter(prefix="/detect", tags=["Detection"])

@router.post("/image", response_model=ImageDetectionResponse)
async def detect_image(
    image: Optional[UploadFile] = File(None),
    media_id: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """
    Modular CNN artifact detection endpoint.
    Can be invoked with either:
    1. Direct multipart image upload (performs ingestion + forensic analysis).
    2. Existing `media_id` previously uploaded to the vault.
    """
    if media_id:
        # Use existing ingested media
        result = analyze_image_media(media_id=media_id, db=db, user="analyst")
        return result
    elif image:
        # Ingest first, then analyze
        ingest_res = await ingest_media_file(file=image, db=db, user="analyst")
        assigned_id = ingest_res["media_id"]
        result = analyze_image_media(media_id=assigned_id, db=db, user="analyst")
        return result
    else:
        raise HTTPException(
            status_code=400,
            detail="Either an image file or a 'media_id' must be provided."
        )

@router.get("/{detection_id}", response_model=ImageDetectionResponse)
def get_detection_result(detection_id: str, db: Session = Depends(get_db)):
    """Retrieve detailed detection results and evidence by detection ID."""
    record = db.query(DetectionResult).filter(DetectionResult.id == detection_id).first()
    if not record:
        raise HTTPException(status_code=404, detail=f"Detection record '{detection_id}' not found.")

    media = db.query(Media).filter(Media.id == record.media_id).first()
    evidence_items = [e.description for e in record.evidence]

    return ImageDetectionResponse(
        detection_id=record.id,
        media_type="image",
        classification=record.classification,
        confidence=record.confidence,
        scores={
            "cnn": record.cnn_score,
            "frequency": record.frequency_score,
            "facial": record.facial_score,
            "temporal": record.temporal_score,
            "blink": record.blink_score,
            "metadata": record.metadata_score,
            "provenance": record.provenance_score
        },
        evidence=evidence_items,
        provenance={
            "hash": media.sha256 if media else "unknown",
            "watermark_detected": False,
            "content_credentials": False,
            "c2pa_status": "not_found"
        },
        timestamp=record.created_at
    )

@router.post("/video", response_model=VideoJobResponse)
async def detect_video(video: UploadFile = File(...), db: Session = Depends(get_db)):
    """Queue video for asynchronous temporal and multi-frame analysis (Phase 7)."""
    return VideoJobResponse(
        job_id="JOB-000000",
        media_id="MED-000000",
        status="queued",
        progress=0.0
    )
