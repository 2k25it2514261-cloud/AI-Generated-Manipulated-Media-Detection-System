import os
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Union
from pathlib import Path
from PIL import Image

import torch
import torch.nn as nn
import torchvision.transforms as transforms
import torchvision.models as models

logger = logging.getLogger("ai_forensics.cnn")

class BaseArtifactDetector(ABC):
    """
    Abstract Base Class for CNN Artifact Detectors.
    Allows modular swapping between EfficientNet, ConvNeXt, ViT, etc.
    """
    @abstractmethod
    def predict(self, image_input: Union[str, Path, Image.Image]) -> Dict[str, Any]:
        """Runs artifact inference on an image and returns real/synthetic probabilities."""
        pass

    @abstractmethod
    def get_model_info(self) -> Dict[str, str]:
        """Returns model name and version for reproducible forensics audit trails."""
        pass


class EfficientNetArtifactDetector(BaseArtifactDetector):
    """
    EfficientNet-B0 baseline classifier for detecting AI-generated / synthetic artifacts.
    Standardized on 224x224 RGB inputs with Softmax probability outputs.
    """
    def __init__(self, checkpoint_path: str = None, device: str = None):
        self.model_name = "EfficientNet-B0"
        self.model_version = "EfficientNet-B0-v1.0"
        
        if device is None:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        else:
            self.device = torch.device(device)

        logger.info(f"Initializing {self.model_name} on device: {self.device}")

        # Build EfficientNet-B0 architecture
        self.model = models.efficientnet_b0(weights=models.EfficientNet_B0_Weights.DEFAULT)
        num_features = self.model.classifier[1].in_features
        # Binary head: [0: real, 1: synthetic/manipulated]
        self.model.classifier[1] = nn.Linear(num_features, 2)

        # Load custom weights if provided
        if checkpoint_path and os.path.exists(checkpoint_path):
            logger.info(f"Loading trained checkpoint from {checkpoint_path}")
            checkpoint = torch.load(checkpoint_path, map_location=self.device)
            if "state_dict" in checkpoint:
                self.model.load_state_dict(checkpoint["state_dict"])
            else:
                self.model.load_state_dict(checkpoint)
            if "model_version" in checkpoint:
                self.model_version = checkpoint["model_version"]

        self.model.to(self.device)
        self.model.eval()

        # Standard forensic inference transforms
        self.transform = transforms.Compose([
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225]
            )
        ])

    def predict(self, image_input: Union[str, Path, Image.Image]) -> Dict[str, Any]:
        """
        Executes forward inference on image input.
        Returns real and synthetic probabilities.
        """
        if isinstance(image_input, (str, Path)):
            pil_img = Image.open(str(image_input)).convert("RGB")
        elif isinstance(image_input, Image.Image):
            pil_img = image_input.convert("RGB")
        else:
            raise ValueError(f"Unsupported image input type: {type(image_input)}")

        tensor = self.transform(pil_img).unsqueeze(0).to(self.device)

        with torch.no_grad():
            logits = self.model(tensor)
            probs = torch.softmax(logits, dim=1).squeeze(0).cpu().numpy()

        real_prob = float(probs[0])
        synthetic_prob = float(probs[1])

        return {
            "real_probability": round(real_prob, 4),
            "synthetic_probability": round(synthetic_prob, 4),
            "model_name": self.model_name,
            "model_version": self.model_version,
            "device": str(self.device)
        }

    def get_model_info(self) -> Dict[str, str]:
        return {
            "model_name": self.model_name,
            "model_version": self.model_version,
            "architecture": "efficientnet_b0",
            "input_resolution": "224x224"
        }


# Singleton cache for inference
_detector_instance = None

def get_cnn_detector(
    model_type: str = "efficientnet_b0",
    checkpoint_path: str = None,
    force_reload: bool = False
) -> BaseArtifactDetector:
    """
    Factory function for modular CNN detector instantiation.
    Enables future expansion to ConvNeXt-Tiny, ViT, or ensemble detectors.
    """
    global _detector_instance
    if _detector_instance is None or force_reload:
        if model_type == "efficientnet_b0":
            # Check if default checkpoint exists in ml/checkpoints
            default_chk = Path(__file__).resolve().parent.parent.parent.parent / "ml" / "checkpoints" / "efficientnet_b0_best.pt"
            chk = checkpoint_path or (str(default_chk) if default_chk.exists() else None)
            _detector_instance = EfficientNetArtifactDetector(checkpoint_path=chk)
        else:
            raise ValueError(f"Unknown detector model type: '{model_type}'. Supported: 'efficientnet_b0'.")

    return _detector_instance
