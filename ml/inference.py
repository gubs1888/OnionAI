"""
OnionDetector — the STABLE ML inference interface.

Backend dependency rule: the backend (app/services/inference.py) mirrors this
exact contract; it never imports torch directly. TEAM A owns this file and
may rewrite `detect` internals freely — the signature and output shape are the
contract (docs/api/API_CONTRACT.md §5).

Usage:

    from ml.inference import OnionDetector

    detector = OnionDetector()                # auto: real model if present, else DEMO
    result   = detector.detect("photo.jpg")
    # {"detections":[{class_name, class_id, confidence, bbox}], "model_version",
    #  "is_demo", "inference_ms", "note"?}

CLI smoke test (works with ZERO heavy deps in demo mode):

    python ml/inference.py --image docs/demo/sample_images/sample_onions_01.jpg
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
import time
from pathlib import Path

# Allow running directly as a script:  python ml/inference.py --image x.jpg
_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from ml.config import (  # noqa: E402
    CLASS_NAME_TO_ID,
    CLASS_NAMES,
    CONF_THRESHOLD,
    DEFAULT_MODEL_PATH,
    DEMO_NOTE,
    PRETRAINED_BASE,
)


class ModelNotAvailableError(RuntimeError):
    """Raised when real inference is requested but no model file exists."""


class OnionDetector:
    """
    Loads `models/onion_yolo.pt` when available (and ultralytics installed);
    otherwise runs DEMO MODE: deterministic synthetic detections seeded from
    the image bytes, ALWAYS flagged `is_demo=True`.
    """

    def __init__(
        self,
        model_path: str | Path | None = None,
        allow_demo: bool = True,
        conf_threshold: float = CONF_THRESHOLD,
    ) -> None:
        self.model_path = Path(model_path) if model_path else DEFAULT_MODEL_PATH
        self.conf_threshold = conf_threshold
        self._model = None
        self._demo = False

        if self.model_path.exists():
            try:
                self._load()                  # may raise ImportError -> helpful msg
            except ImportError:
                if allow_demo:
                    self._demo = True
                else:
                    raise
        elif allow_demo:
            self._demo = True                 # clearly-marked DEMO MODE
        else:
            raise ModelNotAvailableError(
                f"Model not found at '{self.model_path}' and allow_demo=False."
            )

    # ------------------------------------------------------------------ state
    @property
    def is_demo(self) -> bool:
        return self._demo

    @property
    def model_version(self) -> str:
        return "demo-v0" if self._demo else f"yolo11n-{self.model_path.stem}"

    def _load(self) -> None:
        try:
            from ultralytics import YOLO     # lazy: keeps demo installs light
        except ImportError as exc:
            raise ImportError(
                "ultralytics is required for real inference: pip install -r ml/requirements.txt "
                "(or keep allow_demo=True for DEMO MODE)."
            ) from exc
        self._model = YOLO(str(self.model_path))

    # -------------------------------------------------------------- interface
    def detect(self, image_path: str | Path) -> dict:
        """STABLE contract method. See module docstring for the output shape."""
        start = time.perf_counter()
        if self._demo:
            detections = self._demo_detections(Path(image_path))
            note = DEMO_NOTE
        else:
            detections = self._yolo_detections(Path(image_path))
            note = None
        elapsed_ms = (time.perf_counter() - start) * 1000
        out = {
            "detections": detections,
            "model_version": self.model_version,
            "is_demo": self._demo,
            "inference_ms": round(elapsed_ms, 1),
        }
        if note:
            out["note"] = note
        return out

    # ------------------------------------------------------------ real path
    def _yolo_detections(self, path: Path) -> list[dict]:
        results = self._model.predict(source=str(path), conf=self.conf_threshold, verbose=False)
        detections: list[dict] = []
        if not results or not hasattr(results[0], "boxes") or results[0].boxes is None:
            return detections
        for box in results[0].boxes:
            cls_id = int(box.cls.item())
            name = self._model.names.get(cls_id, CLASS_NAMES.get(cls_id, "onion"))
            detections.append(
                {
                    "class_name": str(name).lower(),
                    "class_id": CLASS_NAME_TO_ID.get(str(name).lower(), cls_id),
                    "confidence": round(float(box.conf.item()), 4),
                    "bbox": [round(float(v), 1) for v in box.xyxy.tolist()[0]],
                }
            )
        return detections

    # ------------------------------------------------------------ demo path
    def _demo_detections(self, path: Path) -> list[dict]:
        """Deterministic synthetic detections (same file -> same result)."""
        seed = int.from_bytes(hashlib.sha256(path.read_bytes()).digest()[:8], "big")
        rng = random.Random(seed)
        detections: list[dict] = []
        for _ in range(rng.randint(10, 60)):
            if rng.random() < 0.22:
                # ~22% defective — distribute across all 7 defect classes
                # Weights roughly reflect NCCF defect prevalence
                class_id = rng.choices(
                    [1, 2, 3, 4, 5, 6, 7],
                    weights=[0.20, 0.10, 0.15, 0.10, 0.20, 0.15, 0.10],
                )[0]
                confidence = round(rng.uniform(0.60, 0.95), 4)
            else:
                class_id = 0
                confidence = round(rng.uniform(0.70, 0.98), 4)
            w, h = rng.randint(40, 150), rng.randint(40, 150)
            x1, y1 = rng.randint(5, 640 - w - 5), rng.randint(5, 480 - h - 5)
            detections.append(
                {
                    "class_name": CLASS_NAMES[class_id],
                    "class_id": class_id,
                    "confidence": confidence,
                    "bbox": [x1, y1, x1 + w, y1 + h],
                }
            )
        return detections


# --------------------------------------------------------------------- CLI
def main() -> None:
    parser = argparse.ArgumentParser(description="Onion detection — real model or DEMO mode")
    parser.add_argument("--image", required=True, help="Path to an image file")
    parser.add_argument("--model", default=None, help="Path to .pt weights (default: ml/models/onion_yolo.pt)")
    parser.add_argument("--json", action="store_true", help="Print raw JSON only")
    args = parser.parse_args()

    detector = OnionDetector(model_path=args.model)
    result = detector.detect(args.image)

    mode = "DEMO" if detector.is_demo else "REAL"
    print(f"[{mode}] model={detector.model_version} detections={len(result['detections'])}")
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        for det in result["detections"][:10]:
            print(f"  {det['class_name']:<9} conf={det['confidence']:.2f} bbox={det['bbox']}")
        if detector.is_demo:
            print(f"  NOTE: {DEMO_NOTE}")


if __name__ == "__main__":
    main()
