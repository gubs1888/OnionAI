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

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

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
    metrics = model.val(data=args.data, imgsz=args.imgsz)

    # Per-class mAP50 breakdown (critical for GO/NO-GO gate)
    class_names = ["onion", "damaged", "rotten", "sprouted"]
    per_class: dict[str, dict] = {}
    try:
        ap50_per_class = metrics.box.ap50            # shape: (nc,)
        ap_per_class = metrics.box.ap                 # shape: (nc, 10)
        p_per_class = metrics.box.p                   # shape: (nc,)
        r_per_class = metrics.box.r                   # shape: (nc,)
        for i, name in enumerate(class_names):
            if i < len(ap50_per_class):
                per_class[name] = {
                    "map50": round(float(ap50_per_class[i]), 4),
                    "map50_95": round(float(ap_per_class[i].mean()), 4),
                    "precision": round(float(p_per_class[i]), 4),
                    "recall": round(float(r_per_class[i]), 4),
                }
    except (AttributeError, IndexError):
        per_class = {"note": "Per-class metrics unavailable for this ultralytics version."}

    report = {
        "model": str(model_path),
        "data": args.data,
        "evaluated_at": datetime.now(timezone.utc).isoformat(),
        "map50": float(getattr(metrics.box, "map50", 0.0)),
        "map50_95": float(getattr(metrics.box, "map", 0.0)),
        "precision": float(getattr(metrics.box, "mp", 0.0)),
        "recall": float(getattr(metrics.box, "mr", 0.0)),
        "per_class": per_class,
    }

    # GO/NO-GO gate: mAP50 >= 0.6 on the 'onion' class
    GATE_THRESHOLD = 0.6
    onion_map50 = per_class.get("onion", {}).get("map50", 0.0)
    gate_pass = isinstance(onion_map50, float) and onion_map50 >= GATE_THRESHOLD
    report["go_no_go"] = {
        "gate": f"onion mAP50 >= {GATE_THRESHOLD}",
        "onion_map50": onion_map50,
        "pass": gate_pass,
    }

    out_path = model_path.parent / "eval_report.json"
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(json.dumps(report, indent=2))
    gate_status = "PASS ✓" if gate_pass else "FAIL ✗"
    print(f"\n[GO/NO-GO] onion mAP50 = {onion_map50} → {gate_status}")
    print(f"[DONE] Report written to {out_path}")


if __name__ == "__main__":
    main()
