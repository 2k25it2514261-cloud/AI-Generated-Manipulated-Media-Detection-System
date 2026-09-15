"""
Facial Landmark Inconsistency Detector
Uses MediaPipe Face Mesh to detect geometric anomalies common in deepfakes.
"""
import logging
from pathlib import Path
from typing import Dict, Any, Union, List, Optional
import numpy as np
from PIL import Image

logger = logging.getLogger("ai_forensics.facial_landmark")


def _pil_to_rgb_array(image_input: Union[str, Path, Image.Image]) -> np.ndarray:
    if isinstance(image_input, (str, Path)):
        img = Image.open(str(image_input)).convert("RGB")
    elif isinstance(image_input, Image.Image):
        img = image_input.convert("RGB")
    else:
        raise ValueError(f"Unsupported image input: {type(image_input)}")
    return np.array(img, dtype=np.uint8)


def _compute_symmetry_score(landmarks: List) -> float:
    """
    Computes bilateral facial symmetry score.
    True human faces have ~85-95% symmetry. AI faces often over-perfect or under-perfect.
    Returns [0, 1] where 1 = perfectly symmetric.
    """
    if len(landmarks) < 468:
        return 0.5

    # Mirror pairs (MediaPipe indices) for left/right eye, eyebrow, mouth corners
    pairs = [
        (33, 263), (160, 387), (158, 385),  # Eye corners
        (46, 276), (52, 282), (55, 285),    # Eyebrows
        (61, 291), (39, 269), (37, 267),    # Mouth
        (0, 17), (4, 4),                    # Nose tip (self-ref)
    ]

    diffs = []
    for left_idx, right_idx in pairs:
        if left_idx >= len(landmarks) or right_idx >= len(landmarks):
            continue
        lx, ly = landmarks[left_idx].x, landmarks[left_idx].y
        rx, ry = landmarks[right_idx].x, landmarks[right_idx].y
        # Reflected right should match left when mirrored across x=0.5
        diff = abs(lx - (1.0 - rx)) + abs(ly - ry)
        diffs.append(diff)

    if not diffs:
        return 0.5
    mean_diff = float(np.mean(diffs))
    # Map [0, 0.2] diff range to [1.0, 0.0] symmetry score
    return round(max(0.0, 1.0 - mean_diff / 0.2), 4)


def _compute_eye_aspect_ratio(landmarks: List, eye_indices: List[int]) -> float:
    """EAR — used for blink naturalness."""
    if len(landmarks) < max(eye_indices) + 1:
        return 0.3
    pts = [(landmarks[i].x, landmarks[i].y) for i in eye_indices]
    # Vertical distances
    v1 = np.linalg.norm(np.array(pts[1]) - np.array(pts[5]))
    v2 = np.linalg.norm(np.array(pts[2]) - np.array(pts[4]))
    # Horizontal distance
    h = np.linalg.norm(np.array(pts[0]) - np.array(pts[3]))
    ear = (v1 + v2) / (2.0 * h + 1e-6)
    return float(ear)


def analyze_facial_landmarks(image_input: Union[str, Path, Image.Image]) -> Dict[str, Any]:
    """
    Detects facial landmark anomalies indicating deepfakes.

    Returns:
        - faces_detected: number of faces found
        - symmetry_score: bilateral facial symmetry [0,1]
        - left_ear / right_ear: Eye Aspect Ratios
        - ear_asymmetry: absolute difference in EAR between eyes
        - synthetic_probability: heuristic composite
    """
    try:
        import mediapipe as mp
    except ImportError:
        logger.warning("mediapipe not installed — facial landmark analysis unavailable.")
        return {
            "faces_detected": 0,
            "symmetry_score": None,
            "left_ear": None,
            "right_ear": None,
            "ear_asymmetry": None,
            "synthetic_probability": 0.5,
            "analysis": "facial_landmark",
            "status": "unavailable",
            "note": "mediapipe not installed",
        }

    try:
        mp_face_mesh = mp.solutions.face_mesh

        rgb_array = _pil_to_rgb_array(image_input)

        with mp_face_mesh.FaceMesh(
            static_image_mode=True,
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
        ) as face_mesh:
            results = face_mesh.process(rgb_array)

        if not results.multi_face_landmarks:
            return {
                "faces_detected": 0,
                "symmetry_score": None,
                "left_ear": None,
                "right_ear": None,
                "ear_asymmetry": None,
                "synthetic_probability": 0.3,
                "analysis": "facial_landmark",
                "status": "success",
                "note": "No face detected",
            }

        lm = results.multi_face_landmarks[0].landmark

        symmetry = _compute_symmetry_score(lm)

        # MediaPipe left eye indices (from face mesh map)
        left_eye_idx = [33, 160, 158, 133, 153, 144]
        right_eye_idx = [362, 385, 387, 263, 373, 380]

        left_ear = _compute_eye_aspect_ratio(lm, left_eye_idx)
        right_ear = _compute_eye_aspect_ratio(lm, right_eye_idx)
        ear_asymmetry = abs(left_ear - right_ear)

        # Heuristic: low symmetry OR high EAR asymmetry => suspicious
        # Over-perfect symmetry (>0.97) is also suspicious (AI over-correction)
        low_sym_score = max(0.0, 0.7 - symmetry) * 2  # [0,1]
        overperfect_score = max(0.0, symmetry - 0.97) * 10  # [0,1]
        ear_score = min(ear_asymmetry * 5.0, 1.0)

        synthetic_probability = min(1.0, max(0.0,
            0.4 * max(low_sym_score, overperfect_score) +
            0.6 * ear_score
        ))

        return {
            "faces_detected": 1,
            "symmetry_score": round(symmetry, 4),
            "left_ear": round(left_ear, 4),
            "right_ear": round(right_ear, 4),
            "ear_asymmetry": round(ear_asymmetry, 4),
            "synthetic_probability": round(synthetic_probability, 4),
            "analysis": "facial_landmark",
            "status": "success",
        }

    except Exception as e:
        logger.error(f"Facial landmark analysis failed: {e}", exc_info=True)
        return {
            "faces_detected": 0,
            "symmetry_score": None,
            "left_ear": None,
            "right_ear": None,
            "ear_asymmetry": None,
            "synthetic_probability": 0.5,
            "analysis": "facial_landmark",
            "status": "error",
            "error": str(e),
        }
