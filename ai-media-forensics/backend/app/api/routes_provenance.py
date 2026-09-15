from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.models.database import get_db
from app.models.schemas import ProvenanceCheckRequest, ProvenanceCheckResponse

router = APIRouter(prefix="/provenance", tags=["Provenance"])

@router.post("/check", response_model=ProvenanceCheckResponse)
async def check_provenance(request: ProvenanceCheckRequest, db: Session = Depends(get_db)):
    """Check SHA-256 hash or media against provenance records and C2PA manifest registry."""
    return ProvenanceCheckResponse(
        sha256=request.sha256 or "unknown",
        media_id=request.media_id,
        watermark_status="not_detected",
        c2pa_status="not_found",
        verification_status="unverified",
        records=[]
    )
