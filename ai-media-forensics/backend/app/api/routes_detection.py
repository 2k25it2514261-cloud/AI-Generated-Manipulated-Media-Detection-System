"""
Updated Detection API Routes — wired to the real multi-pipeline orchestrator.
"""
import os
import uuid
import shutil
import logging
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks, Query
from sqlalchemy.orm import Session

from app.models.database import get_db
from app.models.db_models import Media, DetectionResult
from app.config import settings

router = APIRouter(prefix="/detection", tags=["Detection"])
logger = logging.getLogger("ai_forensics.api.detection")

UPLOAD_DIR = Path(settings.STORAGE_PATH) / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif", "image/bmp", "image/tiff"}
ALLOWED_VIDEO_TYPES = {"video/mp4", "video/mpeg", "video/quicktime", "video/x-msvideo", "video/webm"}
MAX_FILE_SIZE_MB = 50


def _save_upload(upload: UploadFile) -> Path:
    ext = Path(upload.filename).suffix.lower() if upload.filename else ".bin"
    dest = UPLOAD_DIR / f"{uuid.uuid4()}{ext}"
    with open(dest, "wb") as f:
        shutil.copyfileobj(upload.file, f)
    size_mb = dest.stat().st_size / (1024 * 1024)
    if size_mb > MAX_FILE_SIZE_MB:
        dest.unlink()
        raise HTTPException(status_code=413, detail=f"File exceeds {MAX_FILE_SIZE_MB}MB limit.")
    return dest


@router.post("/image")
async def detect_image(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="Image file (JPEG, PNG, WebP, BMP, TIFF)"),
    include_gradcam: bool = Query(False, description="Include GradCAM saliency map"),
    db: Session = Depends(get_db),
):
    """
    Submit an image for multi-pipeline AI-generation detection.
    Returns a full forensic report with pipeline-level and fused scores.
    """
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(status_code=415, detail=f"Unsupported media type: {file.content_type}")

    saved_path = _save_upload(file)

    try:
        from app.detection.orchestrator import run_image_detection_pipeline
        result = run_image_detection_pipeline(str(saved_path), include_gradcam=include_gradcam)
    except Exception as e:
        logger.error(f"Detection pipeline error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Detection failed: {str(e)}")
    finally:
        # Clean up temp file in background
        background_tasks.add_task(lambda p=saved_path: p.unlink(missing_ok=True))

    return {
        "filename": file.filename,
        "media_type": "image",
        **result,
    }


@router.post("/video")
async def detect_video(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="Video file (MP4, MOV, AVI, WebM)"),
    db: Session = Depends(get_db),
):
    """
    Submit a video for temporal consistency and deepfake analysis.
    """
    if file.content_type not in ALLOWED_VIDEO_TYPES:
        raise HTTPException(status_code=415, detail=f"Unsupported media type: {file.content_type}")

    saved_path = _save_upload(file)

    try:
        from app.detection.video_temporal_analyzer import analyze_video_temporal
        temporal_result = analyze_video_temporal(str(saved_path))
    except Exception as e:
        logger.error(f"Video analysis failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Video analysis failed: {str(e)}")
    finally:
        background_tasks.add_task(lambda p=saved_path: p.unlink(missing_ok=True))

    score = temporal_result.get("synthetic_probability", 0.5)
    verdict = "LIKELY_AI_GENERATED" if score >= 0.65 else ("SUSPICIOUS" if score >= 0.45 else "LIKELY_AUTHENTIC")

    return {
        "filename": file.filename,
        "media_type": "video",
        "pipelines": {"video_temporal": temporal_result},
        "fusion": {
            "overall_synthetic_probability": score,
            "verdict": verdict,
            "confidence": "MEDIUM",
            "active_pipelines": ["video_temporal"],
        },
        "processing_time_seconds": temporal_result.get("processing_time_seconds"),
    }


@router.post("/url")
async def detect_from_url(
    url: str = Query(..., description="Public URL of image to analyze"),
    include_gradcam: bool = Query(False),
    db: Session = Depends(get_db),
):
    """
    Download an image from a URL and run the full detection pipeline.
    """
    import httpx
    import tempfile

    try:
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            content_type = resp.headers.get("content-type", "").split(";")[0].strip()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to fetch URL: {str(e)}")

    if content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(status_code=415, detail=f"URL does not point to a supported image: {content_type}")

    ext_map = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp", "image/gif": ".gif"}
    ext = ext_map.get(content_type, ".jpg")
    dest = UPLOAD_DIR / f"{uuid.uuid4()}{ext}"

    try:
        dest.write_bytes(resp.content)
        from app.detection.orchestrator import run_image_detection_pipeline
        result = run_image_detection_pipeline(str(dest), include_gradcam=include_gradcam)
    except Exception as e:
        logger.error(f"URL detection failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        dest.unlink(missing_ok=True)

    return {"source_url": url, "media_type": "image", **result}
