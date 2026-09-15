import os
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.config import settings
from app.models.db_models import Media, DetectionResult, ArtifactEvidence, ProvenanceRecord, AuditLog
from app.detection.cnn_detector import get_cnn_detector

def classify_evidence_level(score: float) -> str:
    """Classifies forensic evidence into standardized confidence tiers."""
    if score < settings.THRESHOLD_LOW_EVIDENCE:
        return "low_evidence"
    elif score < settings.THRESHOLD_INCONCLUSIVE:
        return "inconclusive"
    elif score < settings.THRESHOLD_SUSPICIOUS:
        return "suspicious"
    else:
        return "strong_evidence"

def generate_detection_id(db: Session) -> str:
    count = db.query(DetectionResult).count() + 1
    return f"DET-{count:06d}"

def analyze_image_media(media_id: str, db: Session, user: str = "system") -> Dict[str, Any]:
    """
    Executes multi-pipeline forensic analysis on an ingested media item.
    In Phase 3, this integrates the CNN baseline artifact detector with metadata signals.
    """
    media = db.query(Media).filter(Media.id == media_id).first()
    if not media:
        raise HTTPException(status_code=404, detail=f"Media record '{media_id}' not found.")

    # Select analysis copy (or fallback to original)
    target_path = media.analysis_copy_path or media.storage_path
    if not os.path.exists(target_path):
        raise HTTPException(status_code=404, detail=f"Media analysis file '{target_path}' not found on storage.")

    # 1. Run CNN artifact detector
    detector = get_cnn_detector("efficientnet_b0")
    cnn_output = detector.predict(target_path)
    cnn_synthetic_prob = cnn_output["synthetic_probability"]

    # 2. Retrieve metadata record and anomalies
    prov_record = db.query(ProvenanceRecord).filter(ProvenanceRecord.media_id == media_id).first()
    metadata = prov_record.metadata_json if prov_record else {}
    anomalies = metadata.get("anomaly_indicators", []) if isinstance(metadata, dict) else []

    # 3. Formulate Evidence Statements
    evidence_items: List[str] = []
    if cnn_synthetic_prob >= 0.70:
        evidence_items.append(f"CNN Artifact Detector ({detector.model_name}): High probability ({int(cnn_synthetic_prob * 100)}%) of synthetic generation artifacts.")
    elif cnn_synthetic_prob >= 0.50:
        evidence_items.append(f"CNN Artifact Detector ({detector.model_name}): Moderate synthetic probability ({int(cnn_synthetic_prob * 100)}%). Inconclusive visual artifacts.")
    else:
        evidence_items.append(f"CNN Artifact Detector ({detector.model_name}): Low probability ({int(cnn_synthetic_prob * 100)}%) of synthetic generation. Visual textures consistent with authentic camera captures.")

    # Add metadata observations
    for anomaly in anomalies:
        evidence_items.append(f"Metadata Signal: {anomaly}")

    # 4. Calculate overall confidence & classification
    classification = classify_evidence_level(cnn_synthetic_prob)
    detection_id = generate_detection_id(db)

    # 5. Persist DetectionResult
    result_record = DetectionResult(
        id=detection_id,
        media_id=media_id,
        classification=classification,
        confidence=cnn_synthetic_prob,
        cnn_score=cnn_synthetic_prob,
        frequency_score=None, # Phase 4
        facial_score=None,    # Phase 5
        temporal_score=None,  # Phase 7
        blink_score=None,     # Phase 7
        metadata_score=0.75 if anomalies else 0.20,
        provenance_score=0.0,
        model_version=cnn_output["model_version"],
        fusion_version="Baseline-v1.0"
    )
    db.add(result_record)

    # 6. Persist Evidence Items
    for item in evidence_items:
        evidence_entry = ArtifactEvidence(
            detection_id=detection_id,
            category="cnn" if "CNN" in item else "metadata",
            description=item,
            score=cnn_synthetic_prob if "CNN" in item else 0.5,
            severity="high" if cnn_synthetic_prob >= 0.80 else "medium"
        )
        db.add(evidence_entry)

    # 7. Audit Log
    audit_entry = AuditLog(
        user=user,
        action="ANALYSIS_COMPLETED",
        media_id=media_id,
        operation=f"CNN Baseline Analysis ({detector.model_name})",
        result=classification.upper(),
        system_version=settings.PROJECT_VERSION,
        details={
            "detection_id": detection_id,
            "cnn_score": cnn_synthetic_prob,
            "classification": classification,
            "model_version": cnn_output["model_version"]
        }
    )
    db.add(audit_entry)
    db.commit()

    return {
        "detection_id": detection_id,
        "media_type": "image",
        "classification": classification,
        "confidence": cnn_synthetic_prob,
        "scores": {
            "cnn": cnn_synthetic_prob,
            "frequency": None,
            "facial": None,
            "temporal": None,
            "blink": None,
            "metadata": 0.75 if anomalies else 0.20,
            "provenance": None
        },
        "evidence": evidence_items,
        "provenance": {
            "hash": media.sha256,
            "watermark_detected": prov_record.watermark_status == "detected" if prov_record else False,
            "content_credentials": prov_record.c2pa_status == "found" if prov_record else False,
            "c2pa_status": prov_record.c2pa_status if prov_record else "not_found"
        }
    }
