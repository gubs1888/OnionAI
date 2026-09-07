"""
ML package — Onion Quality AI (TEAM A).

Modules:
    config         canonical classes, paths, defaults
    data.yaml      dataset contract for Ultralytics (4 classes)
    preprocessing  image preparation helpers
    train.py       YOLO11n training entrypoint
    evaluate.py    metrics/evaluation entrypoint
    inference.py   OnionDetector — the STABLE inference interface

CONTRACT with the backend (see docs/api/API_CONTRACT.md):

    detector.detect(image_path) -> {
        "detections": [{"class_name", "class_id", "confidence", "bbox"}],
        "model_version": str,
        "is_demo": bool,
        "inference_ms": float,
    }
"""
