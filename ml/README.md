# ML — Onion Quality AI (TEAM A)

YOLO11n pipeline for onion detection + defect classification.

## Status: FOUNDATION (DEMO MODE)

The interface, dataset layout, training/eval entrypoints and tests exist.
**No trained model yet** — `OnionDetector` runs in clearly-marked DEMO MODE
(deterministic synthetic detections) until `models/onion_yolo.pt` exists.

## Classes (STABLE contract — never renumber)

| id | class     | meaning |
|----|-----------|---------|
| 0  | `onion`   | healthy bulb |
| 1  | `damaged` | physical damage / broken skin |
| 2  | `rotten`  | decay / mould |
| 3  | `sprouted`| green sprout emerging |

Size estimation is handled SEPARATELY by the backend measurement service —
YOLO only detects + classifies.

## Pipeline

```
dataset/raw/  ->  annotate (YOLO format)  ->  dataset/images + dataset/labels
                                              (split train/val)
train.py  ->  models/onion_yolo.pt  ->  evaluate.py -> eval_report.json
                                        inference.py (OnionDetector)
```

## Commands

```bash
pip install -r ml/requirements.txt          # heavy: torch + ultralytics

# Smoke test WITHOUT any heavy deps (demo mode):
python ml/inference.py --image docs/demo/sample_images/sample_onions_01.jpg

# Real pipeline (after dataset is ready):
python ml/train.py
python ml/evaluate.py
python ml/inference.py --image <photo.jpg> --model ml/models/onion_yolo.pt
```

## The one rule that matters

`OnionDetector.detect(image_path)` is a **contract** (same dict as
`backend/app/services/inference.py::analyze_image`). Change the internals
freely; changing the output shape requires sign-off from TEAM B + TEAM C.

## First-week task list

1. Collect ~300–500 photos (bag + tray shots, varied lighting) → `dataset/raw/`
2. Annotate in YOLO format (see `docs/dataset/DATASET_GUIDE.md`)
3. Split train/val (~80/20) into `dataset/images` + `dataset/labels`
4. `python ml/train.py` → target mAP50 ≥ 0.7 on `onion` class first
5. Swap backend to real inference: `.env` → `DEMO_MODE=false`, `MODEL_PATH` set
