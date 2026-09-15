import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.models.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(50), default="ANALYST", nullable=False) # ADMIN, ANALYST, FACT_CHECKER, RESEARCHER, VIEWER
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class Media(Base):
    __tablename__ = "media"

    id = Column(String(50), primary_key=True, index=True) # e.g. MED-2026-000001
    filename = Column(String(255), nullable=False)
    mime_type = Column(String(100), nullable=False)
    size = Column(Integer, nullable=False)
    sha256 = Column(String(64), index=True, nullable=False)
    storage_path = Column(String(500), nullable=False)
    analysis_copy_path = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    results = relationship("DetectionResult", back_populates="media", cascade="all, delete-orphan")
    provenance_records = relationship("ProvenanceRecord", back_populates="media", cascade="all, delete-orphan")

class DetectionJob(Base):
    __tablename__ = "detection_jobs"

    id = Column(String(50), primary_key=True, index=True) # e.g. JOB-001
    media_id = Column(String(50), ForeignKey("media.id"), nullable=False)
    status = Column(String(50), default="queued") # queued, processing, completed, failed
    progress = Column(Float, default=0.0)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

class DetectionResult(Base):
    __tablename__ = "detection_results"

    id = Column(String(50), primary_key=True, index=True) # e.g. DET-001
    media_id = Column(String(50), ForeignKey("media.id"), nullable=False)
    classification = Column(String(50), nullable=False) # low_evidence, inconclusive, suspicious, strong_evidence
    confidence = Column(Float, nullable=False) # 0.0 - 1.0
    cnn_score = Column(Float, nullable=True)
    frequency_score = Column(Float, nullable=True)
    facial_score = Column(Float, nullable=True)
    temporal_score = Column(Float, nullable=True)
    blink_score = Column(Float, nullable=True)
    metadata_score = Column(Float, nullable=True)
    provenance_score = Column(Float, nullable=True)
    model_version = Column(String(100), default="EfficientNet-B0-v1.0")
    fusion_version = Column(String(100), default="Fusion-v1.0")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    media = relationship("Media", back_populates="results")
    evidence = relationship("ArtifactEvidence", back_populates="detection_result", cascade="all, delete-orphan")

class ArtifactEvidence(Base):
    __tablename__ = "artifact_evidence"

    id = Column(Integer, primary_key=True, autoincrement=True)
    detection_id = Column(String(50), ForeignKey("detection_results.id"), nullable=False)
    category = Column(String(50), nullable=False) # cnn, frequency, facial, temporal, metadata, provenance
    description = Column(Text, nullable=False)
    score = Column(Float, nullable=True)
    severity = Column(String(50), default="medium") # low, medium, high
    details = Column(JSON, nullable=True)

    detection_result = relationship("DetectionResult", back_populates="evidence")

class ProvenanceRecord(Base):
    __tablename__ = "provenance_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    media_id = Column(String(50), ForeignKey("media.id"), nullable=False)
    sha256 = Column(String(64), nullable=False)
    metadata_json = Column(JSON, nullable=True)
    watermark_status = Column(String(50), default="not_detected") # detected, not_detected, invalid
    c2pa_status = Column(String(50), default="not_found") # found, not_found, invalid, incomplete
    verification_status = Column(String(50), default="unverified")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    media = relationship("Media", back_populates="provenance_records")

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user = Column(String(100), default="system")
    action = Column(String(100), nullable=False) # MEDIA_UPLOADED, ANALYSIS_STARTED, ANALYSIS_COMPLETED, REPORT_GENERATED, PROVENANCE_CHECKED
    media_id = Column(String(50), nullable=True)
    operation = Column(String(100), nullable=False)
    result = Column(String(100), nullable=True)
    system_version = Column(String(50), default="1.0.0")
    details = Column(JSON, nullable=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
