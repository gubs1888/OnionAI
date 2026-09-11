"""
ML INFERENCE GATEWAY — the ONLY ML entry point the backend is allowed to use.

Contract (STABLE — do not change the signature or output shape without
sign-off from TEAM A + TEAM B, see docs/api/API_CONTRACT.md):

    analyze_image(image_path: str) -> {
        "detections": [
            {
                "class_name": "rotten",        # onion | damaged | rotten | sprouted
                "class_id": 2,                 # 0=onion 1=damaged 2=rotten 3=sprouted
                "confidence": 0.94,            # 0..1
                "bbox": [x1, y1, x2, y2]       # pixels
            }, ...
        ],
        "model_version": "demo-v0",
        "is_demo": True,                       # ALWAYS present and honest
        "inference_ms": 12.3
    }

Behavior:
    * DEMO_MODE=true (default)  -> deterministic synthetic detections,
      seeded from the image bytes: the same image ALWAYS yields the same
      result. Clearly flagged `is_demo: true`.
    * DEMO_MODE=false           -> loads the real YOLO weights from
      settings.model_path (lazy-imports ultralytics — the backend itself
      never hard-depends on ML libs). If the model is missing, raises
      InferenceError — we NEVER fake real results.

TEAM A owns the YOLO path. Replace `_yolo_analyze` internals when the real
model is ready; nothing else in the backend needs to change.
"""

from __future__ import annotations

import hashlib
import random
import time
from pathlib import Path

from app.config import settings

# Canonical class mapping (must match ml/config.py and ml/dataset/data.yaml)
# 8-class system aligned with NCCF 2026 procurement specifications.
CLASS_NAMES: dict[int, str] = {
    0: "onion", 1: "damaged", 2: "rotten", 3: "sprouted",
    4: "cut_crack", 5: "smut", 6: "discoloured", 7: "fresh_roots",
}
CLASS_NAME_TO_ID = {v: k for k, v in CLASS_NAMES.items()}

DEMO_NOTE = (
    "DEMO MODE: results are deterministic SYNTHETIC data generated from the "
    "image file hash. This is NOT real AI output."
)


class InferenceError(RuntimeError):
    """Raised when real inference is requested but unavailable."""


def analyze_image(image_path: str) -> dict:
    """STABLE interface used by the API layer. See module docstring."""
    if settings.demo_mode:
        return _demo_analyze(image_path)
    return _yolo_analyze(image_path)


# ---------------------------------------------------------------------------
# Real YOLO path (TEAM A)
# ---------------------------------------------------------------------------
_model = None


def _load_model():
    """Lazy-load YOLO weights. Returns None when unavailable in demo mode."""
    global _model
    if _model is not None:
        return _model

    model_path = Path(settings.model_path)
    if not model_path.exists():
        raise InferenceError(
            f"Model file not found at '{model_path}'. "
            "Set DEMO_MODE=true or train a model (see ml/README.md)."
        )
    try:
        from ultralytics import YOLO  # imported lazily — backend stays light
    except ImportError as exc:  # pragma: no cover
        raise InferenceError(
            "ultralytics is not installed in the backend environment. "
            "Install ml/requirements.txt or keep DEMO_MODE=true."
        ) from exc

    _model = YOLO(str(model_path))
    return _model


def _yolo_analyze(image_path: str) -> dict:
    """Real inference. TODO(TEAM A): verify preprocessing + class mapping."""
    model = _load_model()
    start = time.perf_counter()
    try:
        results = model.predict(source=image_path, conf=0.15, verbose=False)
    except Exception as exc:  # never leak a fake result on failure
        raise InferenceError(f"YOLO inference failed: {exc}") from exc
    elapsed_ms = (time.perf_counter() - start) * 1000

    detections: list[dict] = []
    if results:  # safety: results may be empty on corrupt / zero-pixel images
        result = results[0]
        for box in result.boxes:
            cls_id = int(box.cls.item())
            name = model.names.get(cls_id, CLASS_NAMES.get(cls_id, "onion"))
            detections.append(
                {
                    "class_name": str(name).lower(),
                    "class_id": CLASS_NAME_TO_ID.get(str(name).lower(), cls_id),
                    "confidence": round(float(box.conf.item()), 4),
                    "bbox": [round(float(v), 1) for v in box.xyxy.tolist()[0]],
                }
            )

    return {
        "detections": detections,
        "model_version": f"yolo11n-{Path(settings.model_path).stem}",
        "is_demo": False,
        "inference_ms": round(elapsed_ms, 1),
    }


# ---------------------------------------------------------------------------
# DEMO path — deterministic synthetic detections
# ---------------------------------------------------------------------------
def _demo_analyze(image_path: str) -> dict:
    """
    Deterministic DEMO detections derived from the image content hash.

    Same file => same results (hash-stable), so demos are reproducible and
    tests are stable. NO randomness leaks between different files.
    """
    start = time.perf_counter()
    image_bytes = Path(image_path).read_bytes()
    seed = int.from_bytes(hashlib.sha256(image_bytes).digest()[:8], "big")
    rng = random.Random(seed)

    n_onions = rng.randint(10, 60)
    detections: list[dict] = []
    for _ in range(n_onions):
        if rng.random() < 0.22:  # ~22% defective in demo data
            # Distribute across all 7 defect classes (NCCF-aligned weights)
            class_id = rng.choices(
                [1, 2, 3, 4, 5, 6, 7],
                weights=[0.20, 0.10, 0.15, 0.10, 0.20, 0.15, 0.10],
            )[0]
            confidence = round(rng.uniform(0.60, 0.95), 4)
        else:
            class_id = 0
            confidence = round(rng.uniform(0.70, 0.98), 4)

        w = rng.randint(40, 150)
        h = rng.randint(40, 150)
        x1 = rng.randint(5, 640 - w - 5)
        y1 = rng.randint(5, 480 - h - 5)
        detections.append(
            {
                "class_name": CLASS_NAMES[class_id],
                "class_id": class_id,
                "confidence": confidence,
                "bbox": [x1, y1, x1 + w, y1 + h],
            }
        )

    elapsed_ms = (time.perf_counter() - start) * 1000
    return {
        "detections": detections,
        "model_version": "demo-v0",
        "is_demo": True,
        "inference_ms": round(elapsed_ms, 1),
        "note": DEMO_NOTE,
    }
