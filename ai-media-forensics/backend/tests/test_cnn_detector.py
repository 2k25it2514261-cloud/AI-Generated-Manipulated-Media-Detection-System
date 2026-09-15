import io
import os
import pytest
from PIL import Image
from fastapi.testclient import TestClient

import sys
from pathlib import Path

# Add backend and repository root
backend_dir = Path(__file__).resolve().parent.parent
repo_dir = backend_dir.parent
sys.path.insert(0, str(backend_dir))
sys.path.insert(0, str(repo_dir))

from app.main import app
from app.detection.cnn_detector import get_cnn_detector, EfficientNetArtifactDetector
from ml.evaluation.metrics import calculate_forensic_metrics

client = TestClient(app)

def create_test_image(color="purple", size=(224, 224)) -> bytes:
    img = Image.new("RGB", size, color=color)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

def test_cnn_detector_initialization():
    detector = get_cnn_detector("efficientnet_b0")
    assert isinstance(detector, EfficientNetArtifactDetector)
    info = detector.get_model_info()
    assert info["model_name"] == "EfficientNet-B0"
    assert "v1.0" in info["model_version"]

def test_cnn_detector_prediction():
    detector = get_cnn_detector("efficientnet_b0")
    raw_bytes = create_test_image("orange", (224, 224))
    pil_img = Image.open(io.BytesIO(raw_bytes))

    pred = detector.predict(pil_img)
    assert "real_probability" in pred
    assert "synthetic_probability" in pred
    assert 0.0 <= pred["real_probability"] <= 1.0
    assert 0.0 <= pred["synthetic_probability"] <= 1.0
    assert abs((pred["real_probability"] + pred["synthetic_probability"]) - 1.0) < 0.01

def test_evaluation_metrics():
    y_true = [0, 0, 1, 1, 1]
    y_probs = [0.1, 0.2, 0.8, 0.9, 0.4]
    metrics = calculate_forensic_metrics(y_true, y_probs, threshold=0.5)

    assert "accuracy" in metrics
    assert "precision" in metrics
    assert "recall" in metrics
    assert "f1_score" in metrics
    assert "roc_auc" in metrics
    assert "confusion_matrix" in metrics
    assert metrics["accuracy"] >= 0.0

def test_detect_image_api_endpoint():
    raw_bytes = create_test_image("teal", (256, 256))

    # Test direct file detection
    response = client.post(
        "/api/v1/detect/image",
        files={"image": ("test_detection.png", raw_bytes, "image/png")}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["detection_id"].startswith("DET-")
    assert data["classification"] in ["low_evidence", "inconclusive", "suspicious", "strong_evidence"]
    assert "scores" in data
    assert data["scores"]["cnn"] is not None
    assert len(data["evidence"]) >= 1
    assert "provenance" in data

    detection_id = data["detection_id"]

    # Test retrieval by detection_id
    get_res = client.get(f"/api/v1/detect/{detection_id}")
    assert get_res.status_code == 200
    assert get_res.json()["detection_id"] == detection_id
