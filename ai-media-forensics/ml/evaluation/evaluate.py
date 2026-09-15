import argparse
from pathlib import Path
import torch
from torch.utils.data import DataLoader

import sys
sys.path.append(str(Path(__file__).resolve().parent.parent.parent / "backend"))

from ml.preprocessing.dataset import ForensicMediaDataset
from ml.evaluation.metrics import calculate_forensic_metrics
from app.detection.cnn_detector import get_cnn_detector

def evaluate_model(dataset_dir: str, checkpoint_path: str = None, split: str = "test"):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    dataset = ForensicMediaDataset(dataset_dir, split=split)

    if len(dataset) == 0:
        print(f"[Warning] No evaluation samples in {dataset_dir}/{split}.")
        return

    loader = DataLoader(dataset, batch_size=16, shuffle=False)
    detector = get_cnn_detector("efficientnet_b0", checkpoint_path=checkpoint_path)

    all_labels = []
    all_probs = []

    print(f"[*] Evaluating {len(dataset)} samples...")
    for images, labels in loader:
        images = images.to(device)
        with torch.no_grad():
            outputs = detector.model(images)
            probs = torch.softmax(outputs, dim=1)[:, 1].cpu().numpy()

        all_labels.extend(labels.numpy().tolist())
        all_probs.extend(probs.tolist())

    metrics = calculate_forensic_metrics(all_labels, all_probs)
    print("\n--- FORENSIC EVALUATION REPORT ---")
    print(f"Accuracy:  {metrics['accuracy'] * 100:.2f}%")
    print(f"Precision: {metrics['precision'] * 100:.2f}%")
    print(f"Recall:    {metrics['recall'] * 100:.2f}%")
    print(f"F1-Score:  {metrics['f1_score']:.4f}")
    print(f"ROC-AUC:   {metrics['roc_auc']:.4f}")
    print(f"PR-AUC:    {metrics['pr_auc']:.4f}")
    print(f"FPR:       {metrics['false_positive_rate'] * 100:.2f}%")
    print(f"FNR:       {metrics['false_negative_rate'] * 100:.2f}%")
    print("Confusion Matrix:", metrics["confusion_matrix"])

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate Forensic Artifact Detector")
    parser.add_argument("--dataset_dir", type=str, default="ml/datasets")
    parser.add_argument("--checkpoint", type=str, default=None)
    parser.add_argument("--split", type=str, default="test")
    args = parser.parse_args()

    evaluate_model(args.dataset_dir, args.checkpoint, args.split)
