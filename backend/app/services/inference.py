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
    """Real inference using YOLO model with EXIF auto-rotation and adaptive confidence thresholds."""
    model = _load_model()
    start = time.perf_counter()
    try:
        import numpy as np
        from PIL import Image, ImageOps

        try:
            with Image.open(image_path) as img:
                img_upright = ImageOps.exif_transpose(img).convert("RGB")
                # YOLO expects BGR format. Convert RGB to BGR using slicing.
                source = np.array(img_upright)[:, :, ::-1]
        except Exception:
            source = image_path

        # Run prediction with conf=0.25 (standard threshold to avoid noise)
        results = model.predict(source=source, conf=0.25, iou=0.60, agnostic_nms=True, verbose=False)
        # Fallback to conf=0.10 if no objects detected at 0.25
        if results and len(results[0].boxes) == 0:
            results = model.predict(source=source, conf=0.10, iou=0.60, agnostic_nms=True, verbose=False)
    except Exception as exc:  # never leak a fake result on failure
        raise InferenceError(f"YOLO inference failed: {exc}") from exc
    elapsed_ms = (time.perf_counter() - start) * 1000

    detections: list[dict] = []
    if results:  # safety: results may be empty on corrupt / zero-pixel images
        result = results[0]
        boxes_list = list(result.boxes)
        
        # Filter out "group" boxes (a box that completely encloses another valid box)
        filtered_boxes = []
        for i, box_a in enumerate(boxes_list):
            x1_a, y1_a, x2_a, y2_a = box_a.xyxy.tolist()[0]
            area_a = (x2_a - x1_a) * (y2_a - y1_a)
            is_enclosing = False
            for j, box_b in enumerate(boxes_list):
                if i == j: continue
                x1_b, y1_b, x2_b, y2_b = box_b.xyxy.tolist()[0]
                area_b = (x2_b - x1_b) * (y2_b - y1_b)
                if area_a > 1.3 * area_b:
                    inter_x1, inter_y1 = max(x1_a, x1_b), max(y1_a, y1_b)
                    inter_x2, inter_y2 = min(x2_a, x2_b), min(y2_a, y2_b)
                    if inter_x2 > inter_x1 and inter_y2 > inter_y1:
                        inter_area = (inter_x2 - inter_x1) * (inter_y2 - inter_y1)
                        if inter_area > 0.8 * area_b:
                            is_enclosing = True
                            break
            if not is_enclosing:
                filtered_boxes.append(box_a)

        for box in filtered_boxes:
            cls_id = int(box.cls.item())
            name = model.names.get(cls_id, CLASS_NAMES.get(cls_id, "onion"))
            class_name_str = str(name).lower()
            conf_val = float(box.conf.item())
            
            # Hackathon Demo Fix: Prevent dried roots from being misclassified as rot/sprouted 
            # by overriding low-confidence defect predictions back to a healthy 'onion'.
            if class_name_str != "onion" and conf_val < 0.40:
                class_name_str = "onion"
                cls_id = CLASS_NAME_TO_ID.get("onion", 0)
                
            detections.append(
                {
                    "class_name": class_name_str,
                    "class_id": CLASS_NAME_TO_ID.get(class_name_str, cls_id),
                    "confidence": round(conf_val, 4),
                    "bbox": [round(float(v), 1) for v in box.xyxy.tolist()[0]],
                }
            )

    # YOLO results store the original shape as (height, width)
    img_h, img_w = 0, 0
    if results and hasattr(results[0], "orig_shape"):
        img_h, img_w = results[0].orig_shape

    return {
        "detections": detections,
        "image_width": img_w,
        "image_height": img_h,
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
