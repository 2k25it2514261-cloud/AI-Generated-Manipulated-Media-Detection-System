import os
import io
import hashlib
from typing import Tuple, Dict, Any
from pathlib import Path
from PIL import Image, ImageOps

SUPPORTED_IMAGE_MIMES = {
    "image/jpeg": [".jpg", ".jpeg"],
    "image/png": [".png"],
    "image/webp": [".webp"],
    "image/tiff": [".tiff", ".tif"]
}

SUPPORTED_VIDEO_MIMES = {
    "video/mp4": [".mp4"],
    "video/quicktime": [".mov"],
    "video/x-msvideo": [".avi"],
    "video/webm": [".webm"]
}

MAGIC_SIGNATURES = {
    b"\xFF\xD8\xFF": "image/jpeg",
    b"\x89PNG\r\n\x1a\n": "image/png",
    b"RIFF": "image/webp", # checked with WEBP chunk
    b"II*\x00": "image/tiff",
    b"MM\x00*": "image/tiff",
}

def calculate_sha256(data: bytes) -> str:
    """Calculates cryptographic SHA-256 hash of raw media bytes."""
    hasher = hashlib.sha256()
    hasher.update(data)
    return hasher.hexdigest()

def detect_mime_from_bytes(data: bytes, claimed_filename: str) -> str:
    """
    Inspects magic bytes of the file to determine authentic MIME type.
    Does not rely on file extensions alone.
    """
    if len(data) < 12:
        raise ValueError("File payload too small to be valid media.")

    # Check known image magic headers
    for sig, mime in MAGIC_SIGNATURES.items():
        if data.startswith(sig):
            if sig == b"RIFF":
                # Ensure it's WEBP: bytes 8-12 must be 'WEBP'
                if len(data) >= 12 and data[8:12] == b"WEBP":
                    return "image/webp"
            else:
                return mime

    # Video check: ftyp box for mp4/mov
    if len(data) >= 12 and data[4:8] == b"ftyp":
        major_brand = data[8:12]
        if major_brand in [b"qt  ", b"moov"]:
            return "video/quicktime"
        return "video/mp4"

    # Matroska / WebM
    if data.startswith(b"\x1a\x45\xdf\xa3"):
        return "video/webm"

    # AVI
    if data.startswith(b"RIFF") and len(data) >= 12 and data[8:12] == b"AVI ":
        return "video/x-msvideo"

    # Attempt PIL identification as fallback for images
    try:
        with Image.open(io.BytesIO(data)) as img:
            format_name = (img.format or "").lower()
            if format_name in ["jpeg", "jpg"]:
                return "image/jpeg"
            elif format_name == "png":
                return "image/png"
            elif format_name == "webp":
                return "image/webp"
            elif format_name == "tiff":
                return "image/tiff"
    except Exception:
        pass

    raise ValueError("Unsupported or corrupted media format. File signature not recognized.")

def validate_and_preprocess_image(
    data: bytes,
    original_path: str,
    analysis_path: str,
    target_size: Tuple[int, int] = (224, 224)
) -> Dict[str, Any]:
    """
    1. Validates image integrity with Pillow.
    2. Writes original immutable byte stream to original_path.
    3. Generates normalized RGB analysis copy at analysis_path.
    """
    # 1. Integrity check
    try:
        with Image.open(io.BytesIO(data)) as probe:
            probe.verify()
    except Exception as e:
        raise ValueError(f"Image integrity verification failed: {e}")

    # Re-open for operations after verify()
    image = Image.open(io.BytesIO(data))
    original_format = image.format or "UNKNOWN"
    width, height = image.size

    # 2. Write original evidence intact
    Path(original_path).parent.mkdir(parents=True, exist_ok=True)
    with open(original_path, "wb") as f:
        f.write(data)

    # 3. Create normalized RGB analysis copy
    # Handle EXIF orientation if needed
    try:
        image = ImageOps.exif_transpose(image)
    except Exception:
        pass

    # Convert to RGB (handles RGBA, Palette, Grayscale, CMYK)
    if image.mode != "RGB":
        rgb_image = image.convert("RGB")
    else:
        rgb_image = image.copy()

    # Save normalized analysis copy
    Path(analysis_path).parent.mkdir(parents=True, exist_ok=True)
    rgb_image.save(analysis_path, format="PNG", optimize=True)

    return {
        "width": width,
        "height": height,
        "mode": image.mode,
        "format": original_format,
        "channels": 3,
        "analysis_ready": True
    }
