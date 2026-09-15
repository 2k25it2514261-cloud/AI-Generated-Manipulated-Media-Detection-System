"""
Provenance API routes — C2PA, phash deduplication, full provenance report.
"""
import logging
import shutil
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, BackgroundTasks
from sqlalchemy.orm import Session

from app.models.database import get_db
from app.config import settings

router = APIRouter(prefix="/provenance", tags=["Provenance"])
logger = logging.getLogger("ai_forensics.api.provenance")

UPLOAD_DIR = Path(settings.STORAGE_PATH) / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@router.post("/check")
async def check_provenance(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="Image file to check provenance"),
    db: Session = Depends(get_db),
):
    """
    Run C2PA Content Credentials detection, perceptual hash, and AI metadata scan.
    """
    ext = Path(file.filename).suffix.lower() if file.filename else ".jpg"
    dest = UPLOAD_DIR / f"{uuid.uuid4()}{ext}"

    with open(dest, "wb") as f:
        shutil.copyfileobj(file.file, f)

    try:
        from app.provenance.provenance_analyzer import analyze_provenance
        result = analyze_provenance(str(dest))
    except Exception as e:
        logger.error(f"Provenance analysis error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        background_tasks.add_task(lambda p=dest: p.unlink(missing_ok=True))

    return {"filename": file.filename, **result}


@router.get("/phash-similarity")
async def phash_similarity(
    hash1: str = Query(..., description="First perceptual hash (hex string)"),
    hash2: str = Query(..., description="Second perceptual hash (hex string)"),
):
    """
    Compute Hamming distance between two perceptual hashes.
    Distance ≤ 10 indicates near-duplicate images.
    """
    from app.provenance.provenance_analyzer import _hamming_distance
    try:
        distance = _hamming_distance(hash1, hash2)
        similar = distance >= 0 and distance <= 10
        return {
            "hash1": hash1,
            "hash2": hash2,
            "hamming_distance": distance,
            "likely_duplicate": similar,
            "similarity_percent": round(max(0, 1 - distance / 256) * 100, 2),
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
