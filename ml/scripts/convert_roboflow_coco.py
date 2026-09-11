"""
Convert Roboflow COCO exports into the Onion Quality AI YOLO dataset.

Inputs : one or more Roboflow export dirs (train/valid/test with _annotations.coco.json)
Output : ml/dataset/{images,labels}/{train,val} + docs/dataset/DATASET_STATS.md data

CLASS MAPPING — 8-class system (aligned with NCCF 2026 procurement specs)
-------------------------------------------------------------------------
Source labels are messy (two different Roboflow projects merged). We map with
fine-grained keyword matching. Combo labels (e.g. 'sprouted-blacksmutinfected')
emit MULTIPLE annotations on the same bounding box — this matches reality
(one onion can have multiple defects simultaneously).

    0 = onion        healthy bulb
    1 = damaged      generic physical damage (only 'bad' with no specific defect)
    2 = rotten       decay / soft rot / fungal rot (NOT smut)
    3 = sprouted     green sprout emerging
    4 = cut_crack    cuts, cracks
    5 = smut         black smut / mut infection (surface fungal)
    6 = discoloured  staining / discoloration
    7 = fresh_roots  rooting / rooted

See docs/dataset/MAPPING.md for the full rationale.

Notes:
* COCO bbox [x, y, w, h] (absolute px) -> YOLO txt (class cx cy w h, normalized).
* Roboflow 'valid' AND 'test' splits are merged into 'val'.
* Images are resized to max side 960 px (YOLO11n trains at 640) to keep the
  repo light. Originals stay outside the repo (Drive / incoming/).

Usage:
    python ml/scripts/convert_roboflow_coco.py \\
        --source path/to/export1 --source path/to/export2 \\
        --out ml/dataset
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

try:
    from PIL import Image
except ImportError as exc:  # pragma: no cover
    raise SystemExit("Pillow required: pip install Pillow") from exc

MAX_SIDE = 960
SPLITS = {"train": "train", "valid": "val", "test": "val"}  # merge valid+test -> val

CLASS_NAMES = {
    0: "onion",
    1: "damaged",
    2: "rotten",
    3: "sprouted",
    4: "cut_crack",
    5: "smut",
    6: "discoloured",
    7: "fresh_roots",
}


def map_class_multi(label: str) -> list[int]:
    """Map a raw Roboflow label to one or more class IDs.

    For combo labels (e.g. 'sprouted-blacksmutinfected'), returns MULTIPLE
    class IDs. Each will emit a separate YOLO annotation on the same bbox.

    Returns empty list if the label should be skipped entirely.
    """
    l = label.lower()

    # --- Single-class labels (most specific first) ---
    # Check if this is a combo label (contains a hyphen between two known parts)
    parts = l.replace("_", "-").split("-")

    classes: set[int] = set()

    for part in parts:
        part = part.strip()
        if not part:
            continue

        # Rotten / decay (NOT smut)
        if part == "rotten":
            classes.add(2)
        # Smut (black smut / mut infection — surface fungal, distinct from rot)
        elif "smut" in part or "mut" in part:
            classes.add(5)
        # Sprouted
        elif "sprout" in part:
            classes.add(3)
        # Cut/crack
        elif "cut" in part:
            classes.add(4)
        # Discoloured / staining
        elif "discolou" in part:
            classes.add(6)
        # Rooting / rooted
        elif part in ("root", "rooted", "rooting"):
            classes.add(7)
        # Healthy onion
        elif part in ("onion", "good"):
            classes.add(0)
        # Generic bad — only if no specific defect matched
        elif part == "bad":
            classes.add(1)
        # Stem — now mapped to a note (was skipped in 4-class system)
        elif part == "stem":
            pass  # still skip — only 2 annotations, not enough to train
        # Unrecognized
        else:
            pass  # will be counted in skipped

    # If 'bad' was the only match alongside a specific defect, remove 'bad'
    # (e.g. a theoretical 'bad-rotten' should just be rotten)
    if len(classes) > 1 and 1 in classes:
        classes.discard(1)

    # If 'onion' (healthy) appeared alongside a defect, remove 'onion'
    # (the defect takes priority)
    if len(classes) > 1 and 0 in classes:
        classes.discard(0)

    # If no classes matched at all from the parts, check the full label
    if not classes:
        if any(k in l for k in ("rotten",)):
            classes.add(2)
        elif any(k in l for k in ("smut", "mut")):
            classes.add(5)
        elif any(k in l for k in ("sprout",)):
            classes.add(3)
        elif any(k in l for k in ("cut",)):
            classes.add(4)
        elif any(k in l for k in ("discolou",)):
            classes.add(6)
        elif any(k in l for k in ("root",)):
            classes.add(7)
        elif any(k in l for k in ("onion", "good")):
            classes.add(0)
        elif "bad" in l:
            classes.add(1)

    return sorted(classes) if classes else []


def convert_one(source: Path, out: Path, stats: Counter, skipped: Counter) -> None:
    for roboflow_split, our_split in SPLITS.items():
        ann_file = source / roboflow_split / "_annotations.coco.json"
        if not ann_file.exists():
            continue
        coco = json.loads(ann_file.read_text(encoding="utf-8"))
        cats = {c["id"]: c["name"] for c in coco["categories"]}

        imgs_dir = out / "images" / our_split
        labels_dir = out / "labels" / our_split
        imgs_dir.mkdir(parents=True, exist_ok=True)
        labels_dir.mkdir(parents=True, exist_ok=True)

        # group annotations per image
        anns_by_img: dict[int, list[dict]] = {}
        for a in coco["annotations"]:
            anns_by_img.setdefault(a["image_id"], []).append(a)

        for img in coco["images"]:
            file_name = img["file_name"]
            width, height = img["width"], img["height"]
            src_path = source / roboflow_split / file_name
            if not src_path.exists():
                print(f"  !! missing image referenced in COCO: {src_path}")
                continue

            stem = Path(file_name).stem
            # unique-ish name keeps both sources' files apart after merge
            base = f"{source.name}_{stem}"
            dst_path = imgs_dir / f"{base}.jpg"

            # normalize to RGB jpg, downscale (keeps repo light, matches training size)
            with Image.open(src_path) as im:
                rgb = im.convert("RGB")
                scale = MAX_SIDE / max(rgb.size)
                if scale < 1.0:
                    rgb = rgb.resize((round(rgb.width * scale), round(rgb.height * scale)))
                rgb.save(dst_path, "JPEG", quality=88)
            new_w, new_h = rgb.size

            # YOLO label file (empty file = valid negative/background image)
            lines: list[str] = []
            for a in anns_by_img.get(img["id"], []):
                raw_label = cats.get(a["category_id"], "?")
                class_ids = map_class_multi(raw_label)
                if not class_ids:
                    skipped[raw_label] += 1
                    continue

                x, y, w, h = a["bbox"]  # COCO absolute px
                if w <= 1 or h <= 1:
                    continue
                cx, cy = x + w / 2, y + h / 2
                # normalize against ORIGINAL size
                ncx, ncy = cx / width, cy / height
                nw, nh = w / width, h / height
                # clip to [0,1]
                ncx, ncy = min(max(ncx, 0.0), 1.0), min(max(ncy, 0.0), 1.0)
                nw, nh = min(nw, 1.0), min(nh, 1.0)

                # Emit one annotation per class (combo labels -> multiple lines)
                for cls in class_ids:
                    lines.append(f"{cls} {ncx:.6f} {ncy:.6f} {nw:.6f} {nh:.6f}")
                    stats[CLASS_NAMES[cls]] += 1

            (labels_dir / f"{base}.txt").write_text("\n".join(lines), encoding="utf-8")
            stats[f"_imgs_{our_split}"] += 1


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", action="append", required=True, help="Roboflow export dir (repeatable)")
    parser.add_argument("--out", default="ml/dataset", help="Output dataset root")
    args = parser.parse_args()

    out = Path(args.out)
    stats: Counter = Counter()
    skipped: Counter = Counter()

    for src in args.source:
        src = Path(src)
        print(f"==> converting {src.name}")
        convert_one(src, out, stats, skipped)

    print("\n=== images ===")
    for split in ("train", "val"):
        n = stats[f"_imgs_{split}"]
        print(f"  {split}: {n}")
    print("\n=== boxes per class ===")
    total = 0
    for cls in range(8):
        n = stats[CLASS_NAMES[cls]]
        total += n
        print(f"  {cls} {CLASS_NAMES[cls]:14s} {n}")
    print(f"  TOTAL boxes: {total}")
    if skipped:
        print("\n=== skipped annotations (unmapped labels) ===")
        for label, n in skipped.most_common():
            print(f"  {label}: {n}")


if __name__ == "__main__":
    main()
