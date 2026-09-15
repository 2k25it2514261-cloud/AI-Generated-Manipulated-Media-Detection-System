import os
import argparse
from pathlib import Path
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torchvision import models

# Support running directly as script
import sys
sys.path.append(str(Path(__file__).resolve().parent.parent.parent / "backend"))

from ml.preprocessing.dataset import ForensicMediaDataset, get_forensic_transforms

def train_cnn(
    dataset_dir: str,
    epochs: int = 5,
    batch_size: int = 16,
    lr: float = 1e-4,
    save_dir: str = "ml/checkpoints"
):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"[Training] Running on device: {device}")

    Path(save_dir).mkdir(parents=True, exist_ok=True)

    # Initialize datasets
    train_dataset = ForensicMediaDataset(dataset_dir, split="train")
    val_dataset = ForensicMediaDataset(dataset_dir, split="validation")

    if len(train_dataset) == 0:
        print(f"[Warning] No training data found in {dataset_dir}/train. Please populate datasets before training.")
        return

    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True, num_workers=0)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False, num_workers=0)

    # Build model: EfficientNet-B0 with 2-class binary head
    model = models.efficientnet_b0(weights=models.EfficientNet_B0_Weights.DEFAULT)
    num_features = model.classifier[1].in_features
    model.classifier[1] = nn.Linear(num_features, 2)
    model.to(device)

    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-2)

    best_val_loss = float("inf")

    for epoch in range(1, epochs + 1):
        model.train()
        running_loss = 0.0
        correct = 0
        total = 0

        for images, labels in train_loader:
            images, labels = images.to(device), labels.to(device)

            optimizer.zero_grad()
            outputs = model(images)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()

            running_loss += loss.item() * images.size(0)
            _, preds = torch.max(outputs, 1)
            correct += torch.sum(preds == labels.data).item()
            total += labels.size(0)

        epoch_loss = running_loss / max(total, 1)
        epoch_acc = correct / max(total, 1)

        print(f"Epoch {epoch}/{epochs} - Train Loss: {epoch_loss:.4f} - Train Acc: {epoch_acc:.4f}")

        # Validation phase
        if len(val_dataset) > 0:
            model.eval()
            val_loss = 0.0
            val_correct = 0
            val_total = 0

            with torch.no_grad():
                for images, labels in val_loader:
                    images, labels = images.to(device), labels.to(device)
                    outputs = model(images)
                    loss = criterion(outputs, labels)

                    val_loss += loss.item() * images.size(0)
                    _, preds = torch.max(outputs, 1)
                    val_correct += torch.sum(preds == labels.data).item()
                    val_total += labels.size(0)

            val_epoch_loss = val_loss / max(val_total, 1)
            val_epoch_acc = val_correct / max(val_total, 1)
            print(f"Validation - Loss: {val_epoch_loss:.4f} - Acc: {val_epoch_acc:.4f}")

            if val_epoch_loss < best_val_loss:
                best_val_loss = val_epoch_loss
                save_path = Path(save_dir) / "efficientnet_b0_best.pt"
                torch.save({
                    "epoch": epoch,
                    "model_name": "EfficientNet-B0",
                    "model_version": "EfficientNet-B0-v1.0",
                    "state_dict": model.state_dict(),
                    "val_loss": val_epoch_loss,
                    "val_acc": val_epoch_acc
                }, save_path)
                print(f"[*] Saved new best checkpoint to {save_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train CNN Forensic Artifact Detector")
    parser.add_argument("--dataset_dir", type=str, default="ml/datasets", help="Path to dataset root")
    parser.add_argument("--epochs", type=int, default=5, help="Number of training epochs")
    parser.add_argument("--batch_size", type=int, default=16, help="Batch size")
    parser.add_argument("--lr", type=float, default=1e-4, help="Learning rate")
    parser.add_argument("--save_dir", type=str, default="ml/checkpoints", help="Save directory")
    args = parser.parse_args()

    train_cnn(
        dataset_dir=args.dataset_dir,
        epochs=args.epochs,
        batch_size=args.batch_size,
        lr=args.lr,
        save_dir=args.save_dir
    )
