"""
Evaluation entrypoint — honest metrics for the trained model.

Usage:
    python ml/evaluate.py                         # uses ml/models/onion_yolo.pt
    python ml/evaluate.py --model path/to/best.pt

Writes ml/models/eval_report.json (gitignored) and prints a summary.
Exits non-zero when there is no model — never fabricates metrics.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from ml.config import DATA_YAML, DEFAULT_MODEL_PATH, IMG_SIZE


def fail(msg: str) -> None:
    print(f"\n[EVAL ABORTED] {msg}")
    sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate trained onion detector")
    parser.add_argument("--model", default=str(DEFAULT_MODEL_PATH))
    parser.add_argument("--data", default=str(DATA_YAML))
    parser.add_argument("--imgsz", type=int, default=IMG_SIZE)
    args = parser.parse_args()

    model_path = Path(args.model)
    if not model_path.exists():
        fail(f"No model at {model_path}. Train first: python ml/train.py")

    try:
        from ultralytics import YOLO
    except ImportError:
        fail("ultralytics/torch are not installed in this environment.")

    model = YOLO(str(model_path))
    metrics = model.val(data=args.data, imgsz=args.imgsz)  # TODO(TEAM A): per-class report

    report = {
        "model": str(model_path),
        "data": args.data,
        "evaluated_at": datetime.now(timezone.utc).isoformat(),
        "map50": float(getattr(metrics.box, "map50", 0.0)),
        "map50_95": float(getattr(metrics.box, "map", 0.0)),
        "precision": float(getattr(metrics.box, "mp", 0.0)),
        "recall": float(getattr(metrics.box, "mr", 0.0)),
        "note": "Raw YOLO validation metrics — interpretation pending TEAM A/D.",
    }
    out_path = model_path.parent / "eval_report.json"
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(json.dumps(report, indent=2))
    print(f"\n[DONE] Report written to {out_path}")


if __name__ == "__main__":
    main()
