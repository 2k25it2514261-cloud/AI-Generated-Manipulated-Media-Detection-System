import os
import re
import datetime
from pathlib import Path
from sqlalchemy.orm import Session
from fastapi import UploadFile, HTTPException

from app.config import settings
from app.models.db_models import Media, ProvenanceRecord, AuditLog
from app.preprocessing.image import (
    calculate_sha256,
    detect_mime_from_bytes,
    validate_and_preprocess_image,
    SUPPORTED_IMAGE_MIMES,
    SUPPORTED_VIDEO_MIMES
)
from app.preprocessing.metadata import extract_image_metadata

def generate_media_id(db: Session) -> str:
    """Generates sequential, standardized media ID, e.g. MED-2026-000001."""
    year = datetime.datetime.now(datetime.timezone.utc).year
    count = db.query(Media).count() + 1
    return f"MED-{year}-{count:06d}"

def sanitize_filename(filename: str) -> str:
    """Removes path traversals and illegal characters from uploaded filenames."""
    basename = os.path.basename(filename)
    clean = re.sub(r'[^a-zA-Z0-9_.-]', '_', basename)
    return clean or "uploaded_media"

async def ingest_media_file(file: UploadFile, db: Session, user: str = "system") -> dict:
    """
    Forensic ingestion pipeline:
    1. Read raw byte stream into memory.
    2. Cryptographic SHA-256 calculation.
    3. Magic byte MIME sniffing.
    4. Non-destructive preservation in originals vault.
    5. Generation of normalized analysis copy.
    6. EXIF and technical metadata extraction.
    7. Database persistence and immutable audit logging.
    """
    raw_bytes = await file.read()
    if not raw_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    max_size_bytes = 100 * 1024 * 1024 # 100 MB limit
    if len(raw_bytes) > max_size_bytes:
        raise HTTPException(status_code=413, detail="File size exceeds maximum allowed limit (100MB).")

    # 1. Calculate SHA-256
    sha256_hash = calculate_sha256(raw_bytes)

    # 2. Check authentic MIME type
    try:
        detected_mime = detect_mime_from_bytes(raw_bytes, file.filename or "media")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    is_image = detected_mime in SUPPORTED_IMAGE_MIMES
    is_video = detected_mime in SUPPORTED_VIDEO_MIMES

    if not (is_image or is_video):
        raise HTTPException(
            status_code=400,
            detail=f"MIME type '{detected_mime}' is not supported. Allowed: JPG, PNG, WEBP, TIFF, MP4, MOV, AVI, WEBM."
        )

    # 3. Generate Media ID & file paths
    media_id = generate_media_id(db)
    clean_name = sanitize_filename(file.filename or f"{media_id}.bin")

    original_filename = f"{media_id}_{clean_name}"
    original_path = os.path.join(settings.UPLOADS_PATH, "originals", original_filename)
    analysis_filename = f"{media_id}_analysis.png"
    analysis_path = os.path.join(settings.UPLOADS_PATH, "analysis", analysis_filename)

    # 4. Image Preprocessing & Preservation
    if is_image:
        try:
            preprocess_info = validate_and_preprocess_image(
                raw_bytes,
                original_path=original_path,
                analysis_path=analysis_path
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"Image validation error: {e}")

        # 5. Extract metadata
        metadata_info = extract_image_metadata(raw_bytes)
    else:
        # Video: Save original for asynchronous processing
        Path(original_path).parent.mkdir(parents=True, exist_ok=True)
        with open(original_path, "wb") as f:
            f.write(raw_bytes)
        preprocess_info = {"analysis_ready": False, "type": "video"}
        metadata_info = {"has_exif": False, "note": "Video metadata extraction configured in Phase 7."}
        analysis_path = original_path

    # 6. Database record creation
    media_record = Media(
        id=media_id,
        filename=clean_name,
        mime_type=detected_mime,
        size=len(raw_bytes),
        sha256=sha256_hash,
        storage_path=original_path,
        analysis_copy_path=analysis_path
    )
    db.add(media_record)

    # 7. Provenance Record Initial Entry
    provenance = ProvenanceRecord(
        media_id=media_id,
        sha256=sha256_hash,
        metadata_json=metadata_info,
        watermark_status="not_detected",
        c2pa_status="not_found",
        verification_status="unverified"
    )
    db.add(provenance)

    # 8. Immutable Audit Log Entry
    audit_entry = AuditLog(
        user=user,
        action="MEDIA_UPLOADED",
        media_id=media_id,
        operation="Ingest media evidence",
        result="SUCCESS",
        system_version=settings.PROJECT_VERSION,
        details={
            "filename": clean_name,
            "mime_type": detected_mime,
            "sha256": sha256_hash,
            "size": len(raw_bytes),
            "original_path": original_path,
            "analysis_path": analysis_path
        }
    )
    db.add(audit_entry)

    db.commit()
    db.refresh(media_record)

    return {
        "media_id": media_id,
        "filename": clean_name,
        "mime_type": detected_mime,
        "size": len(raw_bytes),
        "sha256": sha256_hash,
        "storage_path": original_path,
        "analysis_copy_path": analysis_path,
        "preprocess_info": preprocess_info,
        "metadata": metadata_info,
        "created_at": media_record.created_at
    }
