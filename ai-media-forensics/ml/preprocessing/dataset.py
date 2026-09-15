import os
import io
import random
from pathlib import Path
from typing import Tuple, List, Optional
from PIL import Image

import torch
from torch.utils.data import Dataset
import torchvision.transforms as transforms
import torchvision.transforms.functional as TF

class ForensicSafeJPEGCompression:
    """
    Simulates real-world web/social media JPEG compression
    without wiping subtle high-frequency synthetic artifacts.
    """
    def __init__(self, quality_range: Tuple[int, int] = (70, 95)):
        self.quality_range = quality_range

    def __call__(self, img: Image.Image) -> Image.Image:
        if random.random() < 0.5:
            quality = random.randint(*self.quality_range)
            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=quality)
            buf.seek(0)
            return Image.open(buf).convert("RGB")
        return img


def get_forensic_transforms(split: str = "train", img_size: int = 224) -> transforms.Compose:
    """
    Returns image transformations tailored for digital media forensics.
    Deliberately avoids destructive distortions that eliminate subtle AI generation signatures.
    """
    if split == "train":
        return transforms.Compose([
            transforms.Resize(int(img_size * 1.15)),
            transforms.RandomCrop(img_size),
            transforms.RandomHorizontalFlip(p=0.5),
            transforms.RandomRotation(degrees=5),
            transforms.ColorJitter(brightness=0.1, contrast=0.1),
            ForensicSafeJPEGCompression(quality_range=(75, 95)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])
    else:
        return transforms.Compose([
            transforms.Resize(int(img_size * 1.15)),
            transforms.CenterCrop(img_size),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])


class ForensicMediaDataset(Dataset):
    """
    Standard forensic media dataset loader supporting tri-class or binary classification:
    - Real (class 0)
    - Synthetic / AI-Generated (class 1)
    - Manipulated (class 1 in binary setting, or class 2 in tri-class setting)
    """
    def __init__(
        self,
        root_dir: str,
        split: str = "train",
        binary_classification: bool = True,
        transform: Optional[transforms.Compose] = None
    ):
        self.root_dir = Path(root_dir) / split
        self.binary_classification = binary_classification
        self.transform = transform or get_forensic_transforms(split=split)
        self.samples: List[Tuple[Path, int]] = []

        self._load_samples()

    def _load_samples(self):
        # Scan for real, ai_generated, manipulated
        valid_extensions = {".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff"}

        real_dir = self.root_dir / "real"
        ai_dir = self.root_dir / "ai_generated"
        manip_dir = self.root_dir / "manipulated"

        # Real samples -> class 0
        if real_dir.exists():
            for p in real_dir.rglob("*"):
                if p.suffix.lower() in valid_extensions and p.is_file():
                    self.samples.append((p, 0))

        # AI-Generated -> class 1
        if ai_dir.exists():
            for p in ai_dir.rglob("*"):
                if p.suffix.lower() in valid_extensions and p.is_file():
                    self.samples.append((p, 1))

        # Manipulated -> class 1 (binary) or class 2 (multi)
        if manip_dir.exists():
            target_class = 1 if self.binary_classification else 2
            for p in manip_dir.rglob("*"):
                if p.suffix.lower() in valid_extensions and p.is_file():
                    self.samples.append((p, target_class))

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, int]:
        path, label = self.samples[idx]
        with Image.open(path) as img:
            img = img.convert("RGB")
            tensor = self.transform(img)
        return tensor, label
