import io
from typing import Dict, Any, List
from PIL import Image, ExifTags

AI_SOFTWARE_SIGNATURES = [
    "stable diffusion",
    "midjourney",
    "dall-e",
    "comfyui",
    "automatic1111",
    "novelai",
    "invokeai",
    "adobe firefly",
    "flux",
    "bing image creator"
]

EDITING_SOFTWARE_SIGNATURES = [
    "adobe photoshop",
    "gimp",
    "lightroom",
    "affinity photo",
    "snapseed",
    "canva",
    "picsart"
]

def extract_image_metadata(data: bytes) -> Dict[str, Any]:
    """
    Extracts EXIF, technical parameters, and text chunks (e.g. PNG prompt headers)
    from media bytes. Analyzes anomalies without making definitive fake assumptions.
    """
    metadata: Dict[str, Any] = {
        "has_exif": False,
        "camera_make": None,
        "camera_model": None,
        "software": None,
        "datetime_original": None,
        "datetime_modified": None,
        "gps_info": None,
        "raw_exif": {},
        "embedded_text_chunks": {},
        "ai_generator_signatures_found": [],
        "editing_software_detected": [],
        "anomaly_indicators": []
    }

    try:
        with Image.open(io.BytesIO(data)) as img:
            # 1. Inspect PNG info / text chunks
            if hasattr(img, "info") and img.info:
                for k, v in img.info.items():
                    if isinstance(v, (str, int, float, bool)):
                        # Truncate overly long values
                        str_val = str(v)
                        metadata["embedded_text_chunks"][str(k)] = str_val[:1000]
                        # Check for AI prompts / parameters
                        val_lower = str_val.lower()
                        for sig in AI_SOFTWARE_SIGNATURES:
                            if sig in val_lower and sig not in metadata["ai_generator_signatures_found"]:
                                metadata["ai_generator_signatures_found"].append(sig)

            # 2. Extract EXIF data if present
            exif_data = img.getexif()
            if exif_data:
                metadata["has_exif"] = True
                for tag_id, value in exif_data.items():
                    tag_name = ExifTags.TAGS.get(tag_id, str(tag_id))
                    # Clean binary or complex values
                    if isinstance(value, bytes):
                        try:
                            value = value.decode("utf-8", errors="ignore").strip("\x00")
                        except Exception:
                            value = f"<bytes length={len(value)}>"
                    elif not isinstance(value, (str, int, float, bool, list, tuple)):
                        value = str(value)

                    metadata["raw_exif"][tag_name] = value

                    # Key attributes
                    if tag_name == "Make":
                        metadata["camera_make"] = str(value).strip()
                    elif tag_name == "Model":
                        metadata["camera_model"] = str(value).strip()
                    elif tag_name == "Software":
                        metadata["software"] = str(value).strip()
                        software_lower = str(value).lower()
                        for sig in EDITING_SOFTWARE_SIGNATURES:
                            if sig in software_lower:
                                metadata["editing_software_detected"].append(sig)
                        for sig in AI_SOFTWARE_SIGNATURES:
                            if sig in software_lower and sig not in metadata["ai_generator_signatures_found"]:
                                metadata["ai_generator_signatures_found"].append(sig)
                    elif tag_name in ["DateTimeOriginal", "DateTime"]:
                        metadata["datetime_original"] = str(value).strip()
                    elif tag_name == "DateTimeDigitized":
                        metadata["datetime_modified"] = str(value).strip()

            # 3. Anomaly Heuristics
            if not metadata["has_exif"]:
                metadata["anomaly_indicators"].append(
                    "Missing camera EXIF data (typical for AI generations and web-compressed social media)."
                )
            if metadata["ai_generator_signatures_found"]:
                metadata["anomaly_indicators"].append(
                    f"Direct synthetic generator tags detected in metadata: {', '.join(metadata['ai_generator_signatures_found'])}"
                )
            if metadata["editing_software_detected"]:
                metadata["anomaly_indicators"].append(
                    f"Image manipulation software detected: {', '.join(metadata['editing_software_detected'])}"
                )

    except Exception as e:
        metadata["extraction_error"] = str(e)

    return metadata
