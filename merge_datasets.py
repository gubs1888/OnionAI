#!/usr/bin/env python3
"""
Merge heterogeneous onion datasets into one YOLO dataset on YOUR class schema.

The hard part of combining datasets is not file copying -- it is that every
source uses different class names for the same thing ("rot", "rotten",
"spoiled", "bad_onion"). Silent misalignment here is worse than no extra data:
you train the model to call healthy bulbs rotten, which is the failure you
already have.

Usage:
    python merge_datasets.py --raw ml/dataset_raw --existing ml/dataset \
                             --out ml/dataset_v2 --val-frac 0.2
"""

import argparse
import hashlib
import random
import shutil
import sys
from collections import Counter
from pathlib import Path

import yaml

# Your target schema. Scope per the Grade A / URS spec: the grading decision
# only needs rotten, sprouted, and size -- everything else is a healthy bulb.
TARGET_CLASSES = ["onion", "rotten", "sprouted"]
TARGET_IDX = {name: i for i, name in enumerate(TARGET_CLASSES)}

# Source class name (lowercased) -> target name, or None to DROP the box.
# Extend this as you add sources. Anything unmapped is reported and dropped,
# never guessed.
CLASS_MAP = {
    # healthy
    "onion": "onion", "onions": "onion", "good": "onion", "fresh": "onion",
    "healthy": "onion", "good_onion": "onion", "normal": "onion",
    "red_onion": "onion", "white_onion": "onion",
    "good onion": "onion",  # imagelabelling/onion-sorting-cghvq
    # rotten -- true decay only
    "rotten": "rotten", "rot": "rotten", "spoiled": "rotten",
    "bad_onion": "rotten", "decay": "rotten", "mould": "rotten",
    "mold": "rotten", "black_mould": "rotten",
    "rotten onion": "rotten",  # imagelabelling/onion-sorting-cghvq
    # sprouted
    "sprouted": "sprouted", "sprout": "sprouted", "sprouting": "sprouted",
    "germinated": "sprouted",
    # deliberately dropped: surface-only defects are Grade A/URS modifiers,
    # not detection classes, and your old "damaged" class was a catch-all that
    # taught the model to call dry skin rot.
    "damaged": None, "damage": None, "bruised": None, "discoloured": None,
    "discolored": None, "stained": None, "smut": None, "sunburn": None,
    "cut": None, "cuts": None, "cut_crack": None, "crack": None, "peeled": None,
    "fresh_roots": None, "root": None, "rooted": None, "rooting": None,
    "neck": None, "stem": None,
    # onion-disease-rdezg compound/noisy labels -- ambiguous, never guess
    "blackmutinfected": None, "blacksmutinfected": None,
    "blackmutinfected-cuts": None, "blacksmutinfected-cuts": None,
    "blacksmutinfected-rotten": None, "blacksmutinfected-sprouted": None,
    "discoloured-blacksmutinfected": None, "discoloured-sprouted": None,
    "sprouted-blacksmutinfected": None, "sprouted-cuts": None,
    "sprouted-discoloured": None, "sprouted-rooting": None,
}


def load_source_names(ds_dir: Path) -> list[str] | None:
    for cand in ("data.yaml", "dataset.yaml"):
        p = ds_dir / cand
        if p.exists():
            data = yaml.safe_load(p.read_text())
            names = data.get("names")
            if isinstance(names, dict):
                names = [names[k] for k in sorted(names)]
            return names
    return None


def iter_pairs(ds_dir: Path):
    """Yield (image_path, label_path) for every split in a YOLO dataset.

    Handles both layouts:
      ml/dataset/images/train/*.jpg -> ml/dataset/labels/train/*.txt
      roboflow/train/images/*.jpg   -> roboflow/train/labels/*.txt
    """
    img_exts = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
    for img in ds_dir.rglob("*"):
        if not img.is_file():
            continue
        if img.suffix.lower() not in img_exts:
            continue
        if "images" not in img.parts:
            continue
        parts = list(img.parts)
        # replace LAST "images" component (covers nested dataset dirs)
        idx = len(parts) - 1 - parts[::-1].index("images")
        parts[idx] = "labels"
        lbl = Path(*parts).with_suffix(".txt")
        if not lbl.exists():
            continue
        yield img, lbl


def file_hash(path: Path) -> str:
    return hashlib.md5(path.read_bytes()).hexdigest()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", type=Path, default=Path("ml/dataset_raw"))
    ap.add_argument("--existing", type=Path, default=Path("ml/dataset"))
    ap.add_argument("--out", type=Path, default=Path("ml/dataset_v2"))
    ap.add_argument("--val-frac", type=float, default=0.2)
    ap.add_argument("--seed", type=int, default=1337)
    args = ap.parse_args()

    sources = [d for d in args.raw.iterdir() if d.is_dir()] if args.raw.exists() else []
    if args.existing.exists():
        sources.append(args.existing)
    if not sources:
        sys.exit(f"No datasets found under {args.raw} or {args.existing}")

    records, seen, unmapped, dropped = [], {}, Counter(), 0

    for ds in sources:
        names = load_source_names(ds)
        if not names:
            print(f"[warn] no data.yaml in {ds.name}, skipping", file=sys.stderr)
            continue
        print(f"[read] {ds.name}: {names}")
        for img, lbl in iter_pairs(ds):
            h = file_hash(img)
            if h in seen:          # exact-duplicate image across sources
                continue
            seen[h] = True
            out_lines = []
            for line in lbl.read_text().splitlines():
                parts = line.split()
                if len(parts) < 5:
                    continue
                src_idx = int(parts[0])
                if src_idx >= len(names):
                    continue
                src_name = str(names[src_idx]).lower().strip()
                if src_name not in CLASS_MAP:
                    unmapped[f"{ds.name}:{src_name}"] += 1
                    continue
                tgt = CLASS_MAP[src_name]
                if tgt is None:
                    dropped += 1
                    continue
                out_lines.append(" ".join([str(TARGET_IDX[tgt])] + parts[1:]))
            if out_lines:          # images with no surviving boxes are useless
                records.append((img, out_lines))

    if unmapped:
        print("\n[!] UNMAPPED CLASSES -- boxes dropped. Add these to CLASS_MAP:")
        for k, v in unmapped.most_common():
            print(f"    {k}: {v} boxes")

    random.Random(args.seed).shuffle(records)
    n_val = int(len(records) * args.val_frac)
    splits = {"val": records[:n_val], "train": records[n_val:]}

    for split, rows in splits.items():
        (args.out / "images" / split).mkdir(parents=True, exist_ok=True)
        (args.out / "labels" / split).mkdir(parents=True, exist_ok=True)
        for i, (img, lines) in enumerate(rows):
            stem = f"{split}_{i:06d}"
            shutil.copy2(img, args.out / "images" / split / f"{stem}{img.suffix.lower()}")
            (args.out / "labels" / split / f"{stem}.txt").write_text("\n".join(lines))

    (args.out / "data.yaml").write_text(yaml.safe_dump({
        "path": str(args.out.resolve()),
        "train": "images/train",
        "val": "images/val",
        "nc": len(TARGET_CLASSES),
        "names": TARGET_CLASSES,
    }, sort_keys=False))

    counts = Counter()
    for split, rows in splits.items():
        for _, lines in rows:
            for ln in lines:
                counts[TARGET_CLASSES[int(ln.split()[0])]] += 1

    print(f"\nMerged -> {args.out}")
    print(f"  images: {len(records)}  (train {len(splits['train'])} / val {len(splits['val'])})")
    print(f"  boxes:  {dict(counts)}   dropped surface-defect boxes: {dropped}")
    worst = min(counts.values()) if counts else 0
    best = max(counts.values()) if counts else 0
    if worst and best / worst > 5:
        print(f"  [!] class imbalance {best/worst:.1f}:1 -- see train_v2.py notes")


if __name__ == "__main__":
    main()
