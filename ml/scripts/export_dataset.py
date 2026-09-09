"""
Helper script to package ml/dataset into onion_dataset.zip for Colab upload.

Usage:
    python ml/scripts/export_dataset.py
"""

import shutil
from pathlib import Path

ML_DIR = Path(__file__).resolve().parent.parent
DATASET_DIR = ML_DIR / "dataset"
OUTPUT_ZIP = ML_DIR / "onion_dataset.zip"


def main():
    if not DATASET_DIR.exists():
        print(f"[ERROR] Dataset directory not found at {DATASET_DIR}")
        return

    print(f"==> Zipping {DATASET_DIR} to {OUTPUT_ZIP}...")
    shutil.make_archive(str(ML_DIR / "onion_dataset"), "zip", str(DATASET_DIR))
    print(f"[SUCCESS] Zip created at: {OUTPUT_ZIP}")
    print("Upload this file to Google Colab or Kaggle Datasets for T4 GPU training.")


if __name__ == "__main__":
    main()
