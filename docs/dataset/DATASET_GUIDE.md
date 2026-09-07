# DATASET GUIDE (TEAM A + TEAM D)

Target: a YOLO-format dataset for onion detection + defect classification.

## Classes (STABLE — never renumber)

| id | name | what to label |
|----|------|---------------|
| 0 | `onion` | a healthy bulb |
| 1 | `damaged` | physical damage: cuts, cracks, bruised/broken skin |
| 2 | `rotten` | decay: mould, black rot, soft/mushy areas |
| 3 | `sprouted` | green sprout visibly emerging from the neck |

One bounding box per onion instance. When unsure between two defect classes,
label the most severe visible condition and note the image filename for review.

## Collection checklist (TEAM D leads, everyone helps)

- [ ] 300–500 photos minimum before first training run
- [ ] Mix of scenes: loose onions on tray, onions in jute bag/heap, single close-ups
- [ ] Lighting: daylight + indoor warm + slight shadow (robustness)
- [ ] Angles: top-down + 45°
- [ ] Defect balance: ≥50 images per defect class (harder to source — start now)
- [ ] Camera: any modern phone, 4:3 or 3:2, avoid digital zoom
- [ ] No people/number plates in frame; shoot in a clean workspace

## File layout (already scaffolded in `ml/dataset/`)

```
dataset/
├── raw/          ← originals straight from the camera (gitignored — share via drive)
├── processed/    ← resized/curated versions (gitignored)
├── images/train/ ─┐
├── images/val/   ─┤ YOLO layout — what Ultralytics reads (data.yaml points here)
├── labels/train/ ─┤   images/xxx.jpg  ↔  labels/xxx.txt (same basename!)
├── labels/val/   ─┘
└── data.yaml     ← path/train/val/nc/names — already configured
```

## Annotation

* Tool (suggested): Roboflow (free, exports YOLO) or LabelImg/Label Studio.
* Export format: **YOLO txt** — one line per box:
  `class_id  x_center  y_center  width  height` (all normalized 0–1).
* Val split: ~20%, split by SESSION (all images from one shoot go to the same
  side) to avoid near-duplicate leakage between train and val.

## Naming convention

`onion_<yyyymmdd>_<scene>_<seq>.jpg` e.g. `onion_20260908_tray_a_017.jpg`

## Size estimation note

Size estimation is handled SEPARATELY by the backend measurement service —
YOLO only detects + classifies. If you include a reference object (e.g. a
coin) in some calibration photos, keep them in `dataset/raw/calibration/`.
