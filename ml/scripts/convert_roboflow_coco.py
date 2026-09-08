"""
Convert Roboflow COCO exports into the Onion Quality AI YOLO dataset.

Inputs : one or more Roboflow export dirs (train/valid/test with _annotations.coco.json)
Output : ml/dataset/{images,labels}/{train,val} + docs/dataset/DATASET_STATS.md data

CLASS MAPPING (documented decision — see docs/dataset/MAPPING.md)
----------------------------------------------------------------
Source labels are messy (two different Roboflow projects merged). We map with
a severity-priority rule; first matching keyword wins:

    1. rotten | smut | mut      -> 2 rotten   (fungal decay bucket)
    2. sprout | root            -> 3 sprouted
    3. cut | discolou | bad     -> 1 damaged  (physical/surface defect; 'bad' = generic)
    4. onion | good             -> 0 onion    (healthy)
    5. anything else (stem ...) -> SKIPPED (counted, reported)

Notes:
* 'black(m)utinfected' case/typo variants all map to rotten (fungal disease —
  treated like decay for grading).
* COCO bbox [x, y, w, h] (absolute px) -> YOLO txt (class cx cy w h, normalized).
* Roboflow 'valid' AND 'test' splits are merged into 'val'.
* Images are resized to max side 960 px (YOLO11n trains at 640) to keep the
  repo light. Originals stay outside the repo (Drive / incoming/).

Usage:
    python ml/scripts/convert_roboflow_coco.py \
        --source path/to/export1 --source path/to/export2 \
        --out ml/dataset
"""

from __future__ import annotations

import argparse
import json
import shutil
from collections import Counter
from pathlib import Path

try:
    from PIL import Image
except ImportError as exc:  # pragma: no cover
    raise SystemExit("Pillow required: pip install Pillow") from exc

MAX_SIDE = 960
SPLITS = {"train": "train", "valid": "val", "test": "val"}  # merge valid+test -> val


def map_class(label: str) -> int | None:
    """Severity-priority keyword mapping. None = skip."""
    l = label.lower()
    if any(k in l for k in ("rotten", "smut", "mut")):
        return 2
    if any(k in l for k in ("sprout", "root")):
        return 3
    if any(k in l for k in ("cut", "discolou", "bad")):
        return 1
    if any(k in l for k in ("onion", "good")):
        return 0
    return None


CLASS_NAMES = {0: "onion", 1: "damaged", 2: "rotten", 3: "sprouted"}


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
                cls = map_class(raw_label)
                if cls is None:
                    skipped[raw_label] += 1
                    continue
                x, y, w, h = a["bbox"]  # COCO absolute px
                if w <= 1 or h <= 1:
                    continue
                cx, cy = x + w / 2, y + h / 2
                # normalize against ORIGINAL size, then rescale for resized image
                ncx, ncy = cx / width, cy / height
                nw, nh = w / width, h / height
                # clip to [0,1]
                ncx, ncy = min(max(ncx, 0.0), 1.0), min(max(ncy, 0.0), 1.0)
                nw, nh = min(nw, 1.0), min(nh, 1.0)
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
    for cls in range(4):
        n = stats[CLASS_NAMES[cls]]
        total += n
        print(f"  {cls} {CLASS_NAMES[cls]:10s} {n}")
    print(f"  TOTAL boxes: {total}")
    if skipped:
        print("\n=== skipped annotations (unmapped labels) ===")
        for label, n in skipped.most_common():
            print(f"  {label}: {n}")


if __name__ == "__main__":
    main()
