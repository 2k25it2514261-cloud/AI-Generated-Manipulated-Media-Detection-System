"""
Detection Orchestrator — Multi-Pipeline Fusion Engine
Runs all detection modules in parallel and fuses results into a confidence score.
"""
import logging
import asyncio
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, Any, Optional
from PIL import Image

from app.detection.cnn_detector import get_cnn_detector
from app.detection.frequency_analyzer import analyze_frequency
from app.detection.facial_landmark_detector import analyze_facial_landmarks
from app.detection.metadata_analyzer import analyze_metadata

logger = logging.getLogger("ai_forensics.orchestrator")

# Weight vector for ensemble fusion (must sum to 1.0)
PIPELINE_WEIGHTS = {
    "cnn": 0.40,
    "frequency": 0.20,
    "facial_landmark": 0.20,
    "metadata": 0.20,
}


def _run_cnn(image_path: str) -> Dict[str, Any]:
    try:
        detector = get_cnn_detector()
        return detector.predict(image_path)
    except Exception as e:
        logger.error(f"CNN pipeline failed: {e}")
        return {"synthetic_probability": 0.5, "status": "error", "error": str(e)}


def _run_frequency(image_path: str) -> Dict[str, Any]:
    try:
        return analyze_frequency(image_path)
    except Exception as e:
        logger.error(f"Frequency pipeline failed: {e}")
        return {"synthetic_probability": 0.5, "status": "error", "error": str(e)}


def _run_facial_landmark(image_path: str) -> Dict[str, Any]:
    try:
        return analyze_facial_landmarks(image_path)
    except Exception as e:
        logger.error(f"Facial landmark pipeline failed: {e}")
        return {"synthetic_probability": 0.5, "status": "error", "error": str(e)}


def _run_metadata(image_path: str) -> Dict[str, Any]:
    try:
        return analyze_metadata(image_path)
    except Exception as e:
        logger.error(f"Metadata pipeline failed: {e}")
        return {"synthetic_probability": 0.5, "status": "error", "error": str(e)}


def fuse_scores(pipeline_results: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """
    Weighted average fusion of pipeline synthetic_probability scores.
    Skips errored/unavailable pipelines and renormalizes weights.
    """
    total_weight = 0.0
    weighted_sum = 0.0
    active_pipelines = []

    for key, weight in PIPELINE_WEIGHTS.items():
        result = pipeline_results.get(key, {})
        status = result.get("status", "error")
        prob = result.get("synthetic_probability")

        if status in ("success",) and prob is not None:
            weighted_sum += weight * float(prob)
            total_weight += weight
            active_pipelines.append(key)

    if total_weight == 0:
        overall_score = 0.5
    else:
        overall_score = weighted_sum / total_weight

    verdict = "LIKELY_AI_GENERATED" if overall_score >= 0.65 else (
        "SUSPICIOUS" if overall_score >= 0.45 else "LIKELY_AUTHENTIC"
    )
    confidence_label = (
        "HIGH" if abs(overall_score - 0.5) >= 0.3 else
        "MEDIUM" if abs(overall_score - 0.5) >= 0.15 else
        "LOW"
    )

    return {
        "overall_synthetic_probability": round(overall_score, 4),
        "verdict": verdict,
        "confidence": confidence_label,
        "active_pipelines": active_pipelines,
        "pipeline_weights_used": {k: PIPELINE_WEIGHTS[k] for k in active_pipelines},
    }


def run_image_detection_pipeline(image_path: str, include_gradcam: bool = False) -> Dict[str, Any]:
    """
    Runs the full multi-pipeline image detection in parallel.
    Returns fused forensic report.
    """
    start_time = time.time()

    pipeline_fns = {
        "cnn": _run_cnn,
        "frequency": _run_frequency,
        "facial_landmark": _run_facial_landmark,
        "metadata": _run_metadata,
    }

    pipeline_results = {}

    with ThreadPoolExecutor(max_workers=4) as executor:
        future_to_key = {
            executor.submit(fn, image_path): key
            for key, fn in pipeline_fns.items()
        }
        for future in as_completed(future_to_key):
            key = future_to_key[future]
            try:
                pipeline_results[key] = future.result(timeout=30)
            except Exception as e:
                logger.error(f"Pipeline '{key}' raised: {e}")
                pipeline_results[key] = {
                    "synthetic_probability": 0.5,
                    "status": "error",
                    "error": str(e),
                }

    fusion = fuse_scores(pipeline_results)
    elapsed = round(time.time() - start_time, 3)

    # GradCAM (optional, sequential after pipeline)
    gradcam_result = None
    if include_gradcam:
        try:
            from app.explainability.gradcam import generate_gradcam
            detector = get_cnn_detector()
            gradcam_result = generate_gradcam(image_path, detector.model)
        except Exception as e:
            gradcam_result = {"status": "error", "error": str(e)}

    return {
        "pipelines": pipeline_results,
        "fusion": fusion,
        "gradcam": gradcam_result,
        "processing_time_seconds": elapsed,
        "media_type": "image",
    }
