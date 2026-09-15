from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from pydantic import BaseModel, Field, ConfigDict

def utc_now():
    return datetime.now(timezone.utc)

# Health Check
class HealthCheckResponse(BaseModel):
    status: str = "ok"
    version: str = "1.0.0"
    database: Dict[str, Any]
    timestamp: datetime = Field(default_factory=utc_now)

# Media Schemas
class MediaBase(BaseModel):
    filename: str
    mime_type: str
    size: int
    sha256: str

class MediaCreate(MediaBase):
    pass

class MediaResponse(MediaBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    storage_path: str
    created_at: datetime

# Detection Schemas
class ScoreSummary(BaseModel):
    cnn: Optional[float] = None
    frequency: Optional[float] = None
    facial: Optional[float] = None
    temporal: Optional[float] = None
    blink: Optional[float] = None
    metadata: Optional[float] = None
    provenance: Optional[float] = None

class ProvenanceSummary(BaseModel):
    hash: str
    watermark_detected: bool = False
    content_credentials: bool = False
    c2pa_status: str = "not_found"

class ImageDetectionResponse(BaseModel):
    detection_id: str
    media_type: str = "image"
    classification: str # low_evidence, inconclusive, suspicious, strong_evidence
    confidence: float
    scores: ScoreSummary
    evidence: List[str]
    provenance: ProvenanceSummary
    timestamp: datetime = Field(default_factory=utc_now)

class VideoJobResponse(BaseModel):
    job_id: str
    media_id: str
    status: str # queued, processing, completed, failed
    progress: float = 0.0
    created_at: datetime = Field(default_factory=utc_now)

# Provenance Check
class ProvenanceCheckRequest(BaseModel):
    sha256: Optional[str] = None
    media_id: Optional[str] = None

class ProvenanceCheckResponse(BaseModel):
    sha256: str
    media_id: Optional[str] = None
    watermark_status: str
    c2pa_status: str
    verification_status: str
    records: List[Dict[str, Any]] = []

# Audit Log Schema
class AuditLogCreate(BaseModel):
    user: str = "system"
    action: str
    media_id: Optional[str] = None
    operation: str
    result: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
