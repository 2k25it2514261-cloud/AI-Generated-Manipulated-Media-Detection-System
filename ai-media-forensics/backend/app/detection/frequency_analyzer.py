"""
Frequency-Domain Analysis Detector
Detects AI-generated images via DCT/FFT spectral artifacts and checkerboard patterns.
"""
import logging
import numpy as np
from pathlib import Path
from typing import Dict, Any, Union
from PIL import Image

logger = logging.getLogger("ai_forensics.frequency")


def _load_gray_array(image_input: Union[str, Path, Image.Image]) -> np.ndarray:
    if isinstance(image_input, (str, Path)):
        img = Image.open(str(image_input)).convert("L")
    elif isinstance(image_input, Image.Image):
        img = image_input.convert("L")
    else:
        raise ValueError(f"Unsupported image input: {type(image_input)}")
    return np.array(img, dtype=np.float64)


def _dct2(block: np.ndarray) -> np.ndarray:
    """2D DCT via FFT (Type-II)."""
    from scipy.fft import dctn
    return dctn(block, norm="ortho")


def analyze_frequency(image_input: Union[str, Path, Image.Image]) -> Dict[str, Any]:
    """
    Performs frequency-domain forensic analysis.

    Returns:
        - fft_mean_high_freq: mean energy in high-frequency FFT bands (AI upsampling artifact)
        - checkerboard_score: power at Nyquist sub-harmonics (GAN transposed-conv artifact)
        - dct_uniformity: low variance => suspiciously uniform (AI synthesis signature)
        - synthetic_probability: heuristic composite score [0, 1]
    """
    try:
        gray = _load_gray_array(image_input)
        h, w = gray.shape

        # --- FFT Analysis ---
        fft = np.fft.fft2(gray)
        fft_shift = np.fft.fftshift(fft)
        magnitude = np.abs(fft_shift)

        center_h, center_w = h // 2, w // 2
        # High-frequency ring mask (outer 25% of frequency space)
        Y, X = np.ogrid[:h, :w]
        dist = np.sqrt((Y - center_h) ** 2 + (X - center_w) ** 2)
        max_dist = min(center_h, center_w)
        high_freq_mask = dist > 0.75 * max_dist
        high_freq_energy = float(np.mean(magnitude[high_freq_mask]))
        total_energy = float(np.mean(magnitude)) + 1e-9
        fft_mean_high_freq = high_freq_energy / total_energy

        # --- Checkerboard Artifact Score ---
        # GAN transposed convolution creates periodic artifacts at Nyquist/2
        nyquist_h, nyquist_w = h // 4, w // 4
        check_region = magnitude[
            center_h - nyquist_h: center_h + nyquist_h,
            center_w - nyquist_w: center_w + nyquist_w,
        ]
        checkerboard_score = float(np.std(check_region) / (np.mean(check_region) + 1e-9))

        # --- DCT Block Uniformity ---
        block_size = 8
        dct_vars = []
        for i in range(0, min(h, 64), block_size):
            for j in range(0, min(w, 64), block_size):
                block = gray[i: i + block_size, j: j + block_size]
                if block.shape == (block_size, block_size):
                    try:
                        dct_block = _dct2(block)
                        dct_vars.append(float(np.var(dct_block)))
                    except Exception:
                        pass

        dct_uniformity = float(1.0 / (np.mean(dct_vars) + 1.0)) if dct_vars else 0.5

        # --- Heuristic composite score ---
        # High high-freq energy + low checkerboard variance + high DCT uniformity => synthetic
        score = min(1.0, max(0.0,
            0.4 * min(fft_mean_high_freq / 10.0, 1.0) +
            0.3 * min(1.0 / (checkerboard_score + 0.5), 1.0) +
            0.3 * dct_uniformity
        ))

        return {
            "fft_mean_high_freq_ratio": round(fft_mean_high_freq, 4),
            "checkerboard_score": round(checkerboard_score, 4),
            "dct_uniformity": round(dct_uniformity, 4),
            "synthetic_probability": round(score, 4),
            "analysis": "frequency_domain",
            "status": "success",
        }

    except Exception as e:
        logger.error(f"Frequency analysis failed: {e}", exc_info=True)
        return {
            "fft_mean_high_freq_ratio": 0.0,
            "checkerboard_score": 0.0,
            "dct_uniformity": 0.0,
            "synthetic_probability": 0.5,
            "analysis": "frequency_domain",
            "status": "error",
            "error": str(e),
        }
