"""
Training entrypoint — YOLO11n on the onion defect dataset.

Usage (after dataset is in place per ml/dataset/data.yaml):

    python ml/train.py                          # defaults from ml/config.py
    python ml/train.py --epochs 150 --batch 8
    python ml/train.py --data ml/dataset/data.yaml --model yolo11n.pt

Output:
    ml/models/onion_yolo.pt   (copied best weights — the artifact the
                               backend loads when DEMO_MODE=false)

Honest failure: if torch/ultralytics are missing, this prints setup guidance
and exits non-zero. It NEVER pretends to have trained anything.
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from ml.config import (
    BATCH_SIZE,
    DATA_YAML,
    DEFAULT_MODEL_PATH,
    EPOCHS,
    IMG_SIZE,
    MODELS_DIR,
    PRETRAINED_BASE,
    SEED,
)


def fail(msg: str) -> None:
    print(f"\n[TRAIN ABORTED] {msg}")
    print("Setup: python -m venv .venv-ml && .venv-ml/bin/pip install -r ml/requirements.txt")
    sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Train YOLO11n onion defect detector")
    parser.add_argument("--data", default=str(DATA_YAML), help="Path to data.yaml")
    parser.add_argument("--model", default=PRETRAINED_BASE, help="Base/pretrained weights")
    parser.add_argument("--epochs", type=int, default=EPOCHS)
    parser.add_argument("--imgsz", type=int, default=IMG_SIZE)
    parser.add_argument("--batch", type=int, default=BATCH_SIZE)
    parser.add_argument("--name", default="onion_yolo_v1")
    args = parser.parse_args()

    data_path = Path(args.data)
    if not data_path.exists():
        fail(f"Dataset spec not found: {data_path}")

    train_images = data_path.parent / "images" / "train"
    if not train_images.exists() or not any(train_images.iterdir()):
        fail(
            f"No training images in {train_images}. Put labeled data there first — "
            "see docs/dataset/DATASET_GUIDE.md."
        )

    try:
        from ultralytics import YOLO
    except ImportError:
        fail("ultralytics/torch are not installed in this environment.")

    model = YOLO(args.model)  # auto-downloads yolo11n.pt on first use
    results = model.train(
        data=str(data_path),
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        seed=SEED,
        name=args.name,
        # Augmentation tuned for onion photos (including minority defect classes)
        hsv_h=0.015,
        hsv_s=0.7,
        hsv_v=0.4,
        degrees=10.0,
        translate=0.1,
        scale=0.5,
        fliplr=0.5,
        mosaic=1.0,
        mixup=0.1,
        copy_paste=0.1,
    )

    # Publish the artifact at the contract path the backend expects.
    best = Path(results.save_dir) / "weights" / "best.pt"
    if best.exists():
        MODELS_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy2(best, DEFAULT_MODEL_PATH)
        print(f"\n[DONE] Best weights copied to {DEFAULT_MODEL_PATH}")
        print("Next: python ml/evaluate.py  then set DEMO_MODE=false with MODEL_PATH set.")
    else:
        fail("Training finished but best.pt was not found — check runs/ output.")


if __name__ == "__main__":
    main()
