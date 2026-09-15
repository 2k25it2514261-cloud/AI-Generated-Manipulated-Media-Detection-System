"""
Explainability Module — GradCAM Saliency Maps
Generates visual explanations for CNN detector decisions.
"""
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Union
import numpy as np
from PIL import Image
import io
import base64

logger = logging.getLogger("ai_forensics.explainability")


def _array_to_b64_png(arr: np.ndarray) -> str:
    """Encode numpy uint8 array to base64 PNG string."""
    img = Image.fromarray(arr.astype(np.uint8))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("utf-8")


def generate_gradcam(
    image_input: Union[str, Path, Image.Image],
    model,
    target_class: int = 1,
    target_layer_name: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Computes GradCAM heatmap for the given model and target class.

    Args:
        image_input: PIL image, path, or np array
        model: PyTorch CNN model (must have accessible named layers)
        target_class: 0=real, 1=synthetic
        target_layer_name: layer name to hook (auto-detected if None)

    Returns:
        - heatmap_b64: base64-encoded PNG of GradCAM overlay
        - top_regions: list of {x, y, w, h, intensity} for highest-activation regions
        - explanation_text: human-readable explanation
    """
    try:
        import torch
        import torchvision.transforms as transforms
        import cv2

        if isinstance(image_input, (str, Path)):
            pil_img = Image.open(str(image_input)).convert("RGB")
        elif isinstance(image_input, Image.Image):
            pil_img = image_input.convert("RGB")
        else:
            raise ValueError("Unsupported image input type")

        orig_w, orig_h = pil_img.size

        transform = transforms.Compose([
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
        ])
        tensor = transform(pil_img).unsqueeze(0)
        tensor.requires_grad_(False)

        # Find target layer (last conv layer for EfficientNet-B0)
        if target_layer_name is None:
            target_layer = None
            for name, module in model.named_modules():
                import torch.nn as nn
                if isinstance(module, nn.Conv2d):
                    target_layer_name = name
                    target_layer = module
            if target_layer is None:
                raise ValueError("No Conv2d layer found in model")
        else:
            target_layer = dict(model.named_modules())[target_layer_name]

        # GradCAM hooks
        gradients = {}
        activations = {}

        def save_gradient(grad):
            gradients["value"] = grad

        def forward_hook(module, input, output):
            activations["value"] = output
            output.register_hook(save_gradient)

        handle = target_layer.register_forward_hook(forward_hook)

        model.eval()
        with torch.enable_grad():
            output = model(tensor)
            model.zero_grad()
            target = output[0, target_class]
            target.backward()

        handle.remove()

        grads = gradients["value"].squeeze(0).cpu().numpy()  # [C, H, W]
        acts = activations["value"].squeeze(0).detach().cpu().numpy()  # [C, H, W]

        weights = grads.mean(axis=(1, 2))  # [C]
        cam = np.sum(weights[:, None, None] * acts, axis=0)  # [H, W]
        cam = np.maximum(cam, 0)
        cam = cam / (cam.max() + 1e-8)

        # Resize CAM to original image size
        cam_resized = cv2.resize(cam, (orig_w, orig_h))
        heatmap = cv2.applyColorMap(np.uint8(255 * cam_resized), cv2.COLORMAP_JET)
        orig_arr = np.array(pil_img.resize((orig_w, orig_h)))
        overlay = cv2.addWeighted(orig_arr, 0.5, heatmap[:, :, ::-1], 0.5, 0)

        heatmap_b64 = _array_to_b64_png(overlay)

        # Top regions
        threshold = 0.7
        binary = (cam_resized > threshold).astype(np.uint8) * 255
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        top_regions = []
        for cnt in sorted(contours, key=cv2.contourArea, reverse=True)[:5]:
            x, y, w, h = cv2.boundingRect(cnt)
            region_cam = cam_resized[y: y + h, x: x + w]
            top_regions.append({
                "x": int(x), "y": int(y), "w": int(w), "h": int(h),
                "mean_intensity": round(float(region_cam.mean()), 3),
            })

        label = "synthetic/manipulated" if target_class == 1 else "real/authentic"
        explanation_text = (
            f"GradCAM highlights regions most influential for classifying this image as '{label}'. "
            f"{len(top_regions)} high-activation region(s) detected. "
            "Bright/warm areas indicate pixels that strongly influenced the model's decision."
        )

        return {
            "heatmap_b64": heatmap_b64,
            "top_regions": top_regions,
            "explanation_text": explanation_text,
            "target_layer": target_layer_name,
            "target_class": target_class,
            "status": "success",
        }

    except ImportError as e:
        logger.warning(f"GradCAM dependency missing: {e}")
        return {
            "heatmap_b64": None,
            "top_regions": [],
            "explanation_text": "GradCAM unavailable — dependency missing.",
            "status": "unavailable",
            "note": str(e),
        }
    except Exception as e:
        logger.error(f"GradCAM generation failed: {e}", exc_info=True)
        return {
            "heatmap_b64": None,
            "top_regions": [],
            "explanation_text": f"GradCAM failed: {str(e)}",
            "status": "error",
            "error": str(e),
        }


def build_explanation_summary(pipeline_results: Dict[str, Any]) -> str:
    """
    Builds a human-readable forensic explanation from multi-pipeline results.
    Used in API reports and browser extension tooltips.
    """
    lines = ["## Forensic Analysis Summary\n"]
    score = pipeline_results.get("overall_synthetic_probability", 0.5)
    verdict = "LIKELY AI-GENERATED" if score >= 0.6 else ("SUSPICIOUS" if score >= 0.4 else "LIKELY AUTHENTIC")
    lines.append(f"**Verdict**: {verdict} (confidence: {score:.0%})\n")

    checks = {
        "cnn": ("CNN Visual Artifact", "synthetic_probability"),
        "frequency": ("Frequency Domain", "synthetic_probability"),
        "facial_landmark": ("Facial Landmark", "synthetic_probability"),
        "metadata": ("Metadata Analysis", "synthetic_probability"),
        "video_temporal": ("Video Temporal", "synthetic_probability"),
    }

    for key, (label, field) in checks.items():
        module = pipeline_results.get(key, {})
        if module and module.get("status") not in ("error", "unavailable", None):
            val = module.get(field)
            if val is not None:
                lines.append(f"- **{label}**: {val:.0%} synthetic probability")
                flags = module.get("suspicious_flags", [])
                if flags:
                    lines.append(f"  - Flags: {', '.join(flags)}")

    return "\n".join(lines)
