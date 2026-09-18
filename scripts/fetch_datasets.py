#!/usr/bin/env python3
"""
Pull LABELLED onion datasets from public sources into ml/dataset_raw/.

Why labelled sources only: YOLO detection training needs bounding boxes.
Scraped web images have none, and auto-labelling them with the current
checkpoint reproduces its errors in the training data. Every source below
ships boxes.

Usage:
    export ROBOFLOW_API_KEY=...        # free account, roboflow.com/settings
    python scripts/fetch_datasets.py --out ml/dataset_raw

Then run merge_datasets.py to remap classes and build the train/val split.
"""

import argparse
import json
import os
import sys
from pathlib import Path

# Roboflow Universe projects that ship onion detection boxes.
# Verified Sep 2026 via Universe search -- all are detection (not classification).
# Still verify labels in the UI before trusting: Universe quality varies, and
# onion-disease-rdezg has 22 noisy classes that merge_datasets.py will drop/report.
# Format: (workspace, project, version, note)
ROBOFLOW_SOURCES = [
    ("onion-dataset", "onions-detection-gt9ir", 5, "healthy baseline, 1 class"),
    ("onion-detection-system", "onion-disease-rdezg", 1, "defect classes incl. rotten/sprouted"),
    ("onion-grading", "onions-ciqkj", 3, "graded piles"),
    ("imagelabelling", "onion-sorting-cghvq", 1, "good vs rotten"),
]

# Non-Roboflow sources requiring manual download (no stable API).
MANUAL_SOURCES = [
    {
        "name": "PlantVillage-style onion sets",
        "url": "https://www.kaggle.com/datasets",
        "note": "Search 'onion disease'. Mostly CLASSIFICATION (whole-image "
                "labels, no boxes). Usable only for a separate defect "
                "classifier head, NOT for YOLO detection.",
    },
    {
        "name": "Open Images V7",
        "url": "https://storage.googleapis.com/openimages/web/index.html",
        "note": "Has an 'Onion' class with boxes. Healthy bulbs only -- good "
                "for boosting the 'onion' baseline class, useless for defects.",
    },
]


def fetch_roboflow(out_dir: Path) -> int:
    key = os.environ.get("ROBOFLOW_API_KEY")
    if not key:
        print("ROBOFLOW_API_KEY not set -- skipping Roboflow sources.", file=sys.stderr)
        return 0
    try:
        from roboflow import Roboflow
    except ImportError:
        print("pip install roboflow", file=sys.stderr)
        return 0

    try:
        rf = Roboflow(api_key=key)
    except Exception as exc:  # noqa: BLE001 -- bad/revoked key raises 401 at init
        print(f"[fail] Roboflow auth failed: {exc}", file=sys.stderr)
        print("Get a real key at roboflow.com/settings (Account > Roboflow Keys), "
              "then: export ROBOFLOW_API_KEY=rf_<yours>", file=sys.stderr)
        return 0
    got = 0
    for ws, proj, ver, note in ROBOFLOW_SOURCES:
        dest = out_dir / f"{ws}__{proj}_v{ver}"
        if dest.exists():
            print(f"[skip] {dest.name} already present")
            got += 1
            continue
        try:
            print(f"[fetch] {ws}/{proj} v{ver} -- {note}")
            project = rf.workspace(ws).project(proj)
            project.version(ver).download("yolov8", location=str(dest))
            got += 1
        except Exception as exc:  # noqa: BLE001 -- Universe projects vanish often
            print(f"[fail] {ws}/{proj}: {exc}", file=sys.stderr)
    return got


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="ml/dataset_raw", type=Path)
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    n = fetch_roboflow(args.out)
    print(f"\nFetched {n} Roboflow dataset(s) into {args.out}")

    print("\nManual sources (no API -- download yourself):")
    for src in MANUAL_SOURCES:
        print(f"  * {src['name']}: {src['url']}\n    {src['note']}")

    (args.out / "SOURCES.json").write_text(
        json.dumps(
            {"roboflow": [list(s) for s in ROBOFLOW_SOURCES], "manual": MANUAL_SOURCES},
            indent=2,
        )
    )
    print(f"\nProvenance written to {args.out / 'SOURCES.json'}")
    print("Next: python scripts/merge_datasets.py --raw", args.out)


if __name__ == "__main__":
    main()
