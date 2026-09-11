"""
Onion Quality Grading CLI — Classify any onion image as Grade A, Grade URS, or None (Non-Qualifying).

Usage:
    python ml/predict_grade.py --image path/to/onion.jpg
    python ml/predict_grade.py --image path/to/onion.jpg --json

Rules enforced (NCCF / NAFED Procurement Standards):
- Grade A: Premium quality, 35-70mm, firm, clean, free from rot/sprouting/cuts/sunburn.
- Grade URS: Under Relaxed Specifications, 35-70mm, up to 40% staining, 10% sunburn, 30% smut, free from inner rot/sprouting.
- None (Non-Qualifying): Fails both Grade A & Grade URS (e.g. rot, sprouting, cut/crack, out-of-size).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Add repo root to path
_REPO_ROOT = Path(__file__).resolve().parents[1]
_BACKEND_ROOT = _REPO_ROOT / "backend"
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

from ml.inference import OnionDetector
from backend.app.services.measurement import estimate_sizes
from backend.app.services.nccf_rule_engine import (
    load_nccf_specs,
    get_active_spec,
    extract_features,
    classify_onion,
    grade_batch,
)

SPEC_PATH = _REPO_ROOT / "backend" / "config" / "nccf_specifications.json"


def classify_image(image_path: str | Path, model_path: str | Path | None = None) -> dict:
    """Run detection + NCCF rule engine to determine if onion photo is Grade A, Grade URS, or None."""
    detector = OnionDetector(model_path=model_path)
    res = detector.detect(image_path)
    detections = res.get("detections", [])

    if not detections:
        return {
            "image": str(image_path),
            "verdict": "None",
            "grade_label": "None (No Onions Detected)",
            "specification": "NCCF PAACS Procurement Specification 2026",
            "total_onions": 0,
            "grade_a_count": 0,
            "grade_urs_count": 0,
            "non_qualifying_count": 0,
            "onions": [],
            "reasons": ["No onions detected in the image."],
            "is_demo": res.get("is_demo", False),
        }

    # Add size estimation (mm)
    detections = estimate_sizes(detections)

    # Load NCCF active specification (PAACS 2026 relaxed spec)
    specs = load_nccf_specs(SPEC_PATH)
    spec_id, spec = get_active_spec(specs)

    # Convert detections to feature vectors & evaluate
    features_list = extract_features(detections)
    batch_result = grade_batch(features_list, spec, spec_id)

    # Map per-onion and batch verdict
    onion_summaries = []
    for og in batch_result.per_onion_grades:
        grade = og["grade"]
        display_grade = "Grade A" if grade == "GRADE_A" else ("Grade URS" if grade == "GRADE_URS" else "None")
        onion_summaries.append({
            "onion_id": og["onion_id"],
            "grade": display_grade,
            "raw_grade": grade,
            "defects": og["defects"],
            "diameter_mm": og["diameter_mm"],
            "reasons": og["reasons"],
        })

    # Overall image verdict
    batch_grade = batch_result.batch_grade
    overall_verdict = "Grade A" if batch_grade == "GRADE_A" else ("Grade URS" if batch_grade == "GRADE_URS" else "None")

    return {
        "image": str(image_path),
        "verdict": overall_verdict,
        "grade_label": f"{overall_verdict} Quality",
        "specification": batch_result.specification_name,
        "total_onions": batch_result.total_onions,
        "grade_a_count": batch_result.grade_a_count,
        "grade_urs_count": batch_result.grade_urs_count,
        "non_qualifying_count": batch_result.non_qualifying_count,
        "onions": onion_summaries,
        "reasons": batch_result.reasons,
        "is_demo": res.get("is_demo", False),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Classify onion image into Grade A, Grade URS, or None")
    parser.add_argument("--image", required=True, help="Path to onion image")
    parser.add_argument("--model", default=None, help="Path to model weights (optional)")
    parser.add_argument("--json", action="store_true", help="Output raw JSON")
    args = parser.parse_args()

    result = classify_image(args.image, model_path=args.model)

    if args.json:
        print(json.dumps(result, indent=2))
        return

    print("=" * 60)
    print(f"  ONION QUALITY VERDICT: {result['verdict'].upper()}")
    print("=" * 60)
    print(f"Image:         {result['image']}")
    print(f"Specification: {result['specification']}")
    print(f"Total Onions:  {result['total_onions']}")
    print(f"  - Grade A:   {result['grade_a_count']}")
    print(f"  - Grade URS: {result['grade_urs_count']}")
    print(f"  - None:      {result['non_qualifying_count']}")
    print("-" * 60)
    print("Per-Onion Breakdown:")
    for onion in result["onions"]:
        defects_str = ", ".join(onion["defects"]) if onion["defects"] else "None (Clean)"
        size_str = f"{onion['diameter_mm']}mm" if onion['diameter_mm'] else "N/A"
        print(f"  Bulb #{onion['onion_id']}: {onion['grade']:<10} | Size: {size_str:<7} | Defects: {defects_str}")
        if onion["reasons"]:
            for r in onion["reasons"]:
                print(f"     └─ {r}")
    print("=" * 60)


if __name__ == "__main__":
    main()
