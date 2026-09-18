#!/usr/bin/env python3
"""
Retrain the onion detector and -- more importantly -- evaluate whether the
retrain actually fixed the failure mode.

The previous model's problem was not mAP. It was domain shift: every training
photo is a crate pile, every deployment photo is bulbs on white paper. A model
can score well on a crate val set and still call clean bulbs rotten at 0.87.
So this script reports a held-out staged-photo score separately.

Usage:
    python train_v2.py --data ml/dataset_v2/data.yaml --epochs 120
    python train_v2.py --eval-only runs/onion_v2/weights/best.pt \
                       --staged-dir ml/holdout_staged
"""

import argparse
from collections import Counter
from pathlib import Path


def train(args) -> Path:
    from ultralytics import YOLO

    model = YOLO(args.weights)
    results = model.train(
        data=str(args.data),
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        patience=25,
        project="runs",
        name=args.name,
        exist_ok=True,
        # Domain-shift mitigation. The deployment domain is a bright, flat,
        # single-layer background; training data is dim crates. Push colour and
        # geometry augmentation hard so the model stops keying on scene cues.
        hsv_h=0.020, hsv_s=0.75, hsv_v=0.55,
        degrees=20.0, scale=0.55, shear=3.0,
        fliplr=0.5, flipud=0.35,
        mosaic=1.0, close_mosaic=15,   # mosaic off for last 15 epochs
        mixup=0.12,
        copy_paste=0.25,               # helps the minority defect classes
        # Occlusion: bulbs in a pile overlap heavily, which is what caused the
        # original undercount. Lower the NMS-time IoU expectation during val.
        iou=0.5,
        cos_lr=True,
        seed=1337,
    )
    # Ultralytics nests under runs/detect/ by task; return the real save_dir
    try:
        return Path(str(results.save_dir)) / "weights" / "best.pt"
    except Exception:
        return Path("runs") / args.name / "weights" / "best.pt"


def eval_staged(weights: Path, staged_dir: Path, conf: float) -> None:
    """Score the deployment domain specifically.

    staged_dir should hold white-background phone photos with YOLO labels --
    the domain the app actually sees. 60-80 hand-labelled images is enough to
    tell whether the retrain worked; it is the single highest-value labelling
    you can do.
    """
    from ultralytics import YOLO

    if not staged_dir.exists():
        print(f"[skip] no staged holdout at {staged_dir} -- "
              "this is the eval that matters most; go label ~60 photos.")
        return

    model = YOLO(str(weights))
    tot_gt = tot_pred = 0
    count_err: list[int] = []
    false_defect = 0
    confusion = Counter()

    for img in sorted(staged_dir.rglob("*.jpg")):
        lbl = Path(str(img.parent).replace("images", "labels")) / (img.stem + ".txt")
        if not lbl.exists():
            continue
        gt = [ln.split() for ln in lbl.read_text().splitlines() if ln.strip()]
        res = model.predict(source=str(img), conf=conf, iou=0.5,
                            imgsz=960, agnostic_nms=True, verbose=False)
        preds = res[0].boxes
        tot_gt += len(gt)
        tot_pred += len(preds)
        count_err.append(len(preds) - len(gt))

        gt_defect = sum(1 for g in gt if int(g[0]) != 0)
        pr_defect = sum(1 for b in preds if int(b.cls.item()) != 0)
        if pr_defect > gt_defect:
            false_defect += pr_defect - gt_defect
        confusion[(gt_defect, pr_defect)] += 1

    n = len(count_err) or 1
    exact = sum(1 for e in count_err if e == 0)
    print(f"\n=== Staged-domain holdout ({n} images) ===")
    print(f"  exact count match : {exact}/{n} ({100*exact/n:.0f}%)")
    print(f"  mean count error  : {sum(count_err)/n:+.2f} bulbs/image")
    print(f"  total GT / pred   : {tot_gt} / {tot_pred}")
    print(f"  FALSE DEFECTS     : {false_defect}  <-- the old model's core bug")
    print("\n  If false defects are still non-zero at conf 0.25, the data did "
          "not fix it and you need more clean-bulb staged samples, not more "
          "images overall.")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", type=Path, default=Path("ml/dataset_v2/data.yaml"))
    ap.add_argument("--weights", default="yolo11n.pt")
    ap.add_argument("--epochs", type=int, default=120)
    ap.add_argument("--imgsz", type=int, default=960)
    ap.add_argument("--batch", type=int, default=8)
    ap.add_argument("--name", default="onion_v2")
    ap.add_argument("--conf", type=float, default=0.25)
    ap.add_argument("--staged-dir", type=Path, default=Path("ml/holdout_staged"))
    ap.add_argument("--eval-only", type=Path)
    args = ap.parse_args()

    best = args.eval_only if args.eval_only else train(args)
    print(f"\nWeights: {best}")
    eval_staged(best, args.staged_dir, args.conf)
    print("\nIf the staged numbers look good, REMOVE the threshold hacks in "
          "backend/app/services/inference.py (DETECT_CONF 0.12, the "
          "bright-background gate, the recovery pass) and re-test at conf 0.25. "
          "Those exist to paper over the old model; keeping them on top of a "
          "good one will cause new, weirder failures.")


if __name__ == "__main__":
    main()
