"""
Video Temporal Consistency Analyzer
Detects temporal artifacts in video: frame-drop patterns, optical flow inconsistencies,
and blink-pattern anomalies (for deepfake video detection).
"""
import logging
import os
import tempfile
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import numpy as np

logger = logging.getLogger("ai_forensics.video_temporal")


def _load_frames(video_path: str, max_frames: int = 60, sample_rate: int = 1) -> Tuple[List[np.ndarray], float]:
    """Extract frames from video using OpenCV."""
    try:
        import cv2
    except ImportError:
        raise ImportError("opencv-python required for video analysis")

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Cannot open video: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    frames = []
    frame_idx = 0

    while len(frames) < max_frames:
        ret, frame = cap.read()
        if not ret:
            break
        if frame_idx % sample_rate == 0:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            frames.append(gray)
        frame_idx += 1

    cap.release()
    return frames, fps


def _optical_flow_variance(frames: List[np.ndarray]) -> Dict[str, float]:
    """Compute inter-frame optical flow magnitude variance."""
    try:
        import cv2
    except ImportError:
        return {"mean_flow": 0.0, "flow_variance": 0.0, "flow_anomaly_score": 0.5}

    magnitudes = []
    for i in range(1, len(frames)):
        flow = cv2.calcOpticalFlowFarneback(
            frames[i - 1], frames[i], None,
            0.5, 3, 15, 3, 5, 1.2, 0
        )
        mag = np.sqrt(flow[..., 0] ** 2 + flow[..., 1] ** 2)
        magnitudes.append(float(np.mean(mag)))

    if not magnitudes:
        return {"mean_flow": 0.0, "flow_variance": 0.0, "flow_anomaly_score": 0.5}

    mean_flow = float(np.mean(magnitudes))
    flow_variance = float(np.var(magnitudes))
    # Sudden spikes in optical flow variance indicate temporal inconsistency
    flow_anomaly_score = min(1.0, flow_variance / (mean_flow + 1.0))

    return {
        "mean_flow": round(mean_flow, 4),
        "flow_variance": round(flow_variance, 4),
        "flow_anomaly_score": round(flow_anomaly_score, 4),
    }


def _frame_diff_stats(frames: List[np.ndarray]) -> Dict[str, float]:
    """Pixel-level frame difference statistics."""
    diffs = []
    for i in range(1, len(frames)):
        diff = np.abs(frames[i].astype(float) - frames[i - 1].astype(float))
        diffs.append(float(np.mean(diff)))

    if not diffs:
        return {"mean_frame_diff": 0.0, "diff_variance": 0.0, "temporal_consistency_score": 0.5}

    mean_diff = float(np.mean(diffs))
    diff_variance = float(np.var(diffs))

    # Very low variance → suspiciously stable (looping or static generation)
    # Very high variance → temporal inconsistency (frame-splice artifacts)
    low_var_flag = 1.0 - min(diff_variance / (mean_diff + 1.0), 1.0)
    high_var_flag = min(diff_variance / 500.0, 1.0)
    temporal_consistency_score = min(1.0, max(0.0, 0.5 * low_var_flag + 0.5 * high_var_flag))

    return {
        "mean_frame_diff": round(mean_diff, 4),
        "diff_variance": round(diff_variance, 4),
        "temporal_consistency_score": round(temporal_consistency_score, 4),
    }


def _detect_blink_patterns(frames: List[np.ndarray], fps: float) -> Dict[str, Any]:
    """
    Simplified blink detection via eye region intensity variation.
    True deepfakes often suppress blinking (pre-2022) or over-regularize it.
    """
    try:
        import cv2
    except ImportError:
        return {"blink_count": None, "blink_rate_per_min": None, "blink_anomaly_score": 0.5}

    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_eye.xml")

    eye_intensities = []
    for frame in frames:
        faces = face_cascade.detectMultiScale(frame, scaleFactor=1.1, minNeighbors=5, minSize=(80, 80))
        if len(faces) == 0:
            continue
        x, y, w, h = faces[0]
        face_roi = frame[y: y + h, x: x + w]
        eyes = eye_cascade.detectMultiScale(face_roi, scaleFactor=1.1, minNeighbors=3)
        if len(eyes) >= 2:
            # Mean intensity of eye region (low = closed/blink)
            ex, ey, ew, eh = eyes[0]
            eye_region = face_roi[ey: ey + eh, ex: ex + ew]
            eye_intensities.append(float(np.mean(eye_region)))

    if len(eye_intensities) < 5:
        return {
            "blink_count": None,
            "blink_rate_per_min": None,
            "blink_anomaly_score": 0.4,
            "note": "insufficient_frames_for_blink_detection",
        }

    # Detect blinks as dips below threshold
    intensities = np.array(eye_intensities)
    threshold = np.mean(intensities) - 1.5 * np.std(intensities)
    blink_frames = np.where(intensities < threshold)[0]

    # Count distinct blink events (consecutive frames = 1 blink)
    blink_count = 0
    in_blink = False
    for i, v in enumerate(intensities):
        if v < threshold:
            if not in_blink:
                blink_count += 1
                in_blink = True
        else:
            in_blink = False

    duration_sec = len(frames) / fps
    blink_rate = (blink_count / duration_sec) * 60 if duration_sec > 0 else 0

    # Normal human blink rate: 12–20 blinks/min
    # Deepfakes: often 0–4 (early) or >30 (jitter)
    if blink_rate < 4 or blink_rate > 35:
        blink_anomaly_score = 0.75
    elif 8 <= blink_rate <= 24:
        blink_anomaly_score = 0.1
    else:
        blink_anomaly_score = 0.4

    return {
        "blink_count": blink_count,
        "blink_rate_per_min": round(blink_rate, 2),
        "blink_anomaly_score": round(blink_anomaly_score, 4),
    }


def analyze_video_temporal(video_path: str) -> Dict[str, Any]:
    """
    Full temporal consistency analysis pipeline for video deepfake detection.
    """
    try:
        frames, fps = _load_frames(video_path, max_frames=90)

        if len(frames) < 3:
            return {
                "frames_analyzed": len(frames),
                "fps": fps,
                "synthetic_probability": 0.5,
                "analysis": "video_temporal",
                "status": "insufficient_frames",
            }

        flow_stats = _optical_flow_variance(frames)
        diff_stats = _frame_diff_stats(frames)
        blink_stats = _detect_blink_patterns(frames, fps)

        # Composite
        synthetic_probability = min(1.0, max(0.0,
            0.35 * flow_stats.get("flow_anomaly_score", 0.5) +
            0.35 * diff_stats.get("temporal_consistency_score", 0.5) +
            0.30 * blink_stats.get("blink_anomaly_score", 0.5)
        ))

        return {
            "frames_analyzed": len(frames),
            "fps": round(fps, 2),
            **flow_stats,
            **diff_stats,
            **blink_stats,
            "synthetic_probability": round(synthetic_probability, 4),
            "analysis": "video_temporal",
            "status": "success",
        }

    except ImportError:
        return {
            "synthetic_probability": 0.5,
            "analysis": "video_temporal",
            "status": "unavailable",
            "note": "opencv-python not installed",
        }
    except Exception as e:
        logger.error(f"Video temporal analysis failed: {e}", exc_info=True)
        return {
            "synthetic_probability": 0.5,
            "analysis": "video_temporal",
            "status": "error",
            "error": str(e),
        }
