from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from app.models.database import get_db
from app.models.schemas import ImageDetectionResponse, VideoJobResponse

router = APIRouter(prefix="/detect", tags=["Detection"])

@router.post("/image", response_model=ImageDetectionResponse)
async def detect_image(image: UploadFile = File(...), db: Session = Depends(get_db)):
    """Analyze image using multi-model forensics pipeline (Phase 2+ integration)."""
    # Baseline placeholder for initial Phase 1 foundation
    return ImageDetectionResponse(
        detection_id="DET-000000",
        media_type="image",
        classification="inconclusive",
        confidence=0.50,
        scores={
            "cnn": 0.50,
            "frequency": 0.50,
            "facial": None,
            "metadata": 0.50
        },
        evidence=["Phase 1 foundation active. Multi-pipeline analyzers ready for phase integration."],
        provenance={
            "hash": "pending_upload_stream",
            "watermark_detected": False,
            "content_credentials": False,
            "c2pa_status": "not_found"
        }
    )

@router.post("/video", response_model=VideoJobResponse)
async def detect_video(video: UploadFile = File(...), db: Session = Depends(get_db)):
    """Queue video for asynchronous temporal and multi-frame analysis."""
    return VideoJobResponse(
        job_id="JOB-000000",
        media_id="MED-000000",
        status="queued",
        progress=0.0
    )
