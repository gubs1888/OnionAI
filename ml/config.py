"""
ML configuration — canonical constants for the whole pipeline.

SINGLE SOURCE OF TRUTH for class ids. Keep in sync with:
  * ml/dataset/data.yaml
  * backend/app/services/inference.py (CLASS_NAMES)
"""

from __future__ import annotations

from pathlib import Path

ML_ROOT = Path(__file__).resolve().parent
REPO_ROOT = ML_ROOT.parent

# --- Canonical classes (contract — do not renumber) -------------------------
# 8-class system aligned with NCCF 2026 procurement specifications.
# Classes 0-3 preserved from the original 4-class contract.
# Classes 4-7 split out from the generic 'damaged'/'rotten'/'sprouted' buckets
# using finer-grained labels already present in the raw Roboflow annotations.
CLASSES: dict[int, str] = {
    0: "onion",        # a healthy onion instance
    1: "damaged",      # generic physical damage (only when no specific defect)
    2: "rotten",       # decay / soft rot / fungal rot (NOT smut)
    3: "sprouted",     # green sprout emerging from the bulb
    4: "cut_crack",    # cuts, cracks — NCCF: "Cut/Crack"
    5: "smut",         # black smut / mut infection — NCCF: "Smut"
    6: "discoloured",  # staining / discoloration — NCCF: "Staining/Discoloration"
    7: "fresh_roots",  # rooting / rooted — NCCF: "Rooting"
}
# Alias kept identical to backend/app/services/inference.py for contract clarity.
CLASS_NAMES = CLASSES
CLASS_NAME_TO_ID = {v: k for k, v in CLASSES.items()}
NUM_CLASSES = len(CLASSES)

# --- Paths -------------------------------------------------------------------
DATASET_DIR = ML_ROOT / "dataset"
DATA_YAML = DATASET_DIR / "data.yaml"
MODELS_DIR = ML_ROOT / "models"
DEFAULT_MODEL_PATH = MODELS_DIR / "onion_yolo.pt"   # the deliverable artifact
PRETRAINED_BASE = "yolo11n.pt"                      # Ultralytics auto-downloads

# --- Training defaults (CLI flags override) ----------------------------------
IMG_SIZE = 640
EPOCHS = 100
BATCH_SIZE = 16
CONF_THRESHOLD = 0.25
SEED = 42

# --- Demo mode ---------------------------------------------------------------
# When no trained model exists, OnionDetector falls back to deterministic
# synthetic detections (flagged is_demo=True). Same image -> same result.
DEMO_NOTE = (
    "DEMO MODE: synthetic detections from the image file hash — NOT real model output."
)
