#!/usr/bin/env python3
"""Store a phone's camera scale after a one-time ruler calibration.

Flow:
  1. Photograph a ruler at a fixed height (e.g. phone on a book stack,
     exactly 25 cm above the table). Note the height.
  2. Measure pixels-per-mm off the ruler (a human reads this, honestly).
  3. Run this script. All later photos taken at a known distance get real
     millimetres: mm_per_px(d) = mm_per_px_ref * (d / d_ref).

Usage:
    python scripts/calibrate_device.py --mm-per-pixel 0.042 --at-cm 25 \
        --phone "Redmi Note 13"
    python scripts/calibrate_device.py --clear   # back to honest uncalibrated
"""
import argparse
import datetime
import json
from pathlib import Path

PROFILE = Path(__file__).resolve().parent.parent / "backend" / "config" / "device_profile.json"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mm-per-pixel", type=float)
    ap.add_argument("--at-cm", type=float)
    ap.add_argument("--phone", default="unknown")
    ap.add_argument("--clear", action="store_true")
    args = ap.parse_args()

    if args.clear:
        PROFILE.write_text(json.dumps({
            "configured": False, "phone": None, "ref_distance_cm": None,
            "mm_per_pixel_at_ref": None, "calibrated_at": None,
            "note": "Cleared. Sizes honestly uncalibrated (null).",
        }, indent=2))
        print("cleared ->", PROFILE)
        return

    if not args.mm_per_pixel or not args.at_cm:
        ap.error("--mm-per-pixel and --at-cm are required (or --clear)")
    PROFILE.write_text(json.dumps({
        "configured": True,
        "phone": args.phone,
        "ref_distance_cm": args.at_cm,
        "mm_per_pixel_at_ref": args.mm_per_pixel,
        "calibrated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "note": "One-time ruler calibration. Demo photos must be taken at a known distance.",
    }, indent=2))
    print("calibrated ->", PROFILE)
    print(f"  {args.mm_per_pixel} mm/px at {args.at_cm} cm ({args.phone})")


if __name__ == "__main__":
    main()
