import io
import os
import hashlib
import pytest
from PIL import Image
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def create_dummy_png(color="blue", size=(100, 100)) -> bytes:
    img = Image.new("RGB", size, color=color)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

def create_dummy_jpeg(color="red", size=(100, 100)) -> bytes:
    img = Image.new("RGB", size, color=color)
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()

def test_upload_valid_png():
    raw_bytes = create_dummy_png("cyan", (64, 64))
    expected_sha256 = hashlib.sha256(raw_bytes).hexdigest()

    response = client.post(
        "/api/v1/media/upload",
        files={"file": ("test_sample.png", raw_bytes, "image/png")}
    )

    assert response.status_code == 201
    data = response.json()
    assert data["media_id"].startswith("MED-")
    assert data["sha256"] == expected_sha256
    assert data["mime_type"] == "image/png"
    assert data["size"] == len(raw_bytes)
    assert os.path.exists(data["storage_path"])
    assert os.path.exists(data["analysis_copy_path"])

    media_id = data["media_id"]

    # Test retrieval
    get_res = client.get(f"/api/v1/media/{media_id}")
    assert get_res.status_code == 200
    assert get_res.json()["id"] == media_id

    # Test metadata
    meta_res = client.get(f"/api/v1/media/{media_id}/metadata")
    assert meta_res.status_code == 200
    assert "metadata" in meta_res.json()

    # Test file retrieval
    file_res = client.get(f"/api/v1/media/{media_id}/file?target=original")
    assert file_res.status_code == 200
    assert file_res.content == raw_bytes

    # Test audit trail
    audit_res = client.get(f"/api/v1/media/{media_id}/audit")
    assert audit_res.status_code == 200
    audit_logs = audit_res.json()
    assert len(audit_logs) >= 1
    assert audit_logs[0]["action"] == "MEDIA_UPLOADED"

def test_upload_valid_jpeg():
    raw_bytes = create_dummy_jpeg("green", (50, 50))
    expected_sha256 = hashlib.sha256(raw_bytes).hexdigest()

    response = client.post(
        "/api/v1/media/upload",
        files={"file": ("photo.jpg", raw_bytes, "image/jpeg")}
    )

    assert response.status_code == 201
    data = response.json()
    assert data["mime_type"] == "image/jpeg"
    assert data["sha256"] == expected_sha256

def test_upload_spoofed_file_rejected():
    # Plain text file disguised as png
    fake_bytes = b"This is just a text file claiming to be an image."
    response = client.post(
        "/api/v1/media/upload",
        files={"file": ("malicious.png", fake_bytes, "image/png")}
    )
    assert response.status_code == 400
    assert "Unsupported or corrupted media format" in response.json()["detail"] or "signature" in response.json()["detail"]
