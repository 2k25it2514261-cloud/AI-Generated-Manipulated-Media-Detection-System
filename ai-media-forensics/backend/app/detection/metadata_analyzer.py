"""
Metadata / EXIF Analysis Detector
Flags suspicious or absent metadata patterns common in AI-generated media.
"""
import logging
import re
from pathlib import Path
from typing import Dict, Any, Union, Optional
from PIL import Image
import piexif

logger = logging.getLogger("ai_forensics.metadata")

# Known AI generation software signatures found in EXIF / XMP tags
AI_SOFTWARE_SIGNATURES = [
    "stable diffusion", "midjourney", "dall-e", "dalle", "firefly",
    "imagen", "craiyon", "nightcafe", "dream by wombo", "artbreeder",
    "deepdream", "gan", "generative", "ai-generated", "ai generated",
    "synthetic", "nijijourney", "leonardo.ai",
]


def _extract_exif(img: Image.Image) -> Optional[Dict]:
    try:
        raw = img.info.get("exif")
        if raw:
            return piexif.load(raw)
    except Exception:
        pass
    return None


def _decode_bytes(val) -> str:
    if isinstance(val, bytes):
        try:
            return val.decode("utf-8", errors="replace").strip()
        except Exception:
            return repr(val)
    return str(val)


def analyze_metadata(image_input: Union[str, Path]) -> Dict[str, Any]:
    """
    Inspects EXIF metadata for AI generation signals.

    Returns:
        - has_exif: whether EXIF block exists
        - software_tag: software string from EXIF if present
        - ai_software_detected: whether known AI tool signature found
        - gps_present: whether GPS data is embedded
        - make_model: camera make/model (absent in AI images)
        - original_datetime: capture datetime if present
        - suspicious_flags: list of detected red flags
        - synthetic_probability: heuristic composite
    """
    try:
        path = str(image_input) if isinstance(image_input, Path) else image_input
        img = Image.open(path)

        exif_data = _extract_exif(img)
        suspicious_flags = []
        software_tag = None
        make_model = None
        original_datetime = None
        gps_present = False
        ai_software_detected = False

        if exif_data is None:
            suspicious_flags.append("no_exif_block")
            has_exif = False
        else:
            has_exif = True

            # Software tag (IFD0 → 0th)
            ifd0 = exif_data.get("0th", {})
            raw_sw = ifd0.get(piexif.ImageIFD.Software)
            if raw_sw:
                software_tag = _decode_bytes(raw_sw)
                sw_lower = software_tag.lower()
                for sig in AI_SOFTWARE_SIGNATURES:
                    if sig in sw_lower:
                        ai_software_detected = True
                        suspicious_flags.append(f"ai_software:{software_tag}")
                        break

            # Make / Model
            make = ifd0.get(piexif.ImageIFD.Make)
            model = ifd0.get(piexif.ImageIFD.Model)
            if make or model:
                make_model = f"{_decode_bytes(make)} {_decode_bytes(model)}".strip()
            else:
                suspicious_flags.append("no_camera_make_model")

            # DateTime
            dt = ifd0.get(piexif.ImageIFD.DateTime)
            if dt:
                original_datetime = _decode_bytes(dt)
                # Check for obviously wrong dates (year 0000 or 9999)
                if re.search(r"\b(0000|9999)\b", original_datetime):
                    suspicious_flags.append("invalid_datetime")
            else:
                suspicious_flags.append("no_datetime")

            # GPS
            gps_ifd = exif_data.get("GPS", {})
            gps_present = bool(gps_ifd)

            # Exif IFD sub-tags
            exif_ifd = exif_data.get("Exif", {})
            if not exif_ifd:
                suspicious_flags.append("no_exif_ifd")
            else:
                # FlashPix version, ColorSpace — absence suspicious
                if piexif.ExifIFD.ColorSpace not in exif_ifd:
                    suspicious_flags.append("no_colorspace_tag")
                # ExposureTime / FNumber absence
                if piexif.ExifIFD.ExposureTime not in exif_ifd:
                    suspicious_flags.append("no_exposure_time")

        # Composite score
        flag_weights = {
            "no_exif_block": 0.55,
            "no_camera_make_model": 0.25,
            "no_datetime": 0.1,
            "invalid_datetime": 0.2,
            "no_exif_ifd": 0.15,
            "no_colorspace_tag": 0.05,
            "no_exposure_time": 0.1,
        }
        base_score = 0.0
        for flag in suspicious_flags:
            # Check for prefix match (e.g. ai_software:xxx)
            key = flag.split(":")[0]
            base_score += flag_weights.get(key, 0.0)
        if ai_software_detected:
            base_score += 0.9  # very strong signal

        synthetic_probability = min(1.0, base_score)

        return {
            "has_exif": has_exif,
            "software_tag": software_tag,
            "ai_software_detected": ai_software_detected,
            "gps_present": gps_present,
            "make_model": make_model,
            "original_datetime": original_datetime,
            "suspicious_flags": suspicious_flags,
            "synthetic_probability": round(synthetic_probability, 4),
            "analysis": "metadata",
            "status": "success",
        }

    except Exception as e:
        logger.error(f"Metadata analysis failed: {e}", exc_info=True)
        return {
            "has_exif": False,
            "software_tag": None,
            "ai_software_detected": False,
            "gps_present": False,
            "make_model": None,
            "original_datetime": None,
            "suspicious_flags": ["analysis_error"],
            "synthetic_probability": 0.5,
            "analysis": "metadata",
            "status": "error",
            "error": str(e),
        }
