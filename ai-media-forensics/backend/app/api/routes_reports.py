"""
Reports API — generates comprehensive forensic PDF/JSON reports.
"""
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.models.database import get_db

router = APIRouter(prefix="/reports", tags=["Reports"])
logger = logging.getLogger("ai_forensics.api.reports")


@router.get("/{detection_id}")
def get_report(detection_id: str, db: Session = Depends(get_db)):
    """
    Retrieve comprehensive forensic report for a detection ID.
    Returns JSON with all pipeline results, fusion score, metadata, and provenance.
    """
    return {
        "detection_id": detection_id,
        "status": "Report retrieval is available after persisting results to the database.",
        "note": "Integrate with Media/DetectionResult DB models to store and retrieve historical reports.",
    }


@router.get("/")
def list_reports(skip: int = 0, limit: int = 20, db: Session = Depends(get_db)):
    """List all detection reports with pagination."""
    return {
        "total": 0,
        "reports": [],
        "skip": skip,
        "limit": limit,
        "note": "Reports are stored in the database after full pipeline integration.",
    }
