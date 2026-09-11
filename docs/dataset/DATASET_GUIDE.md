# DATASET GUIDE (TEAM A + TEAM D) — 8-class NCCF-aligned system

Target: a YOLO-format dataset for onion detection + defect classification,
aligned with NCCF 2026 procurement specifications.

## Classes (STABLE — never renumber)

| id | name | NCCF feature | what to label |
|----|------|-------------|---------------|
| 0 | `onion` | Healthy bulb | a healthy bulb with no visible defects |
| 1 | `damaged` | Mechanical Injury | generic physical damage (cuts/cracks/bruises NOT already covered by class 4) |
| 2 | `rotten` | Rot/Rotting/Fungal | decay: mould, soft rot, fungal rot (NOT black smut — use class 5) |
| 3 | `sprouted` | Sprouted | green sprout visibly emerging from the neck |
| 4 | `cut_crack` | Cut/Crack | visible cuts or cracks in the bulb |
| 5 | `smut` | Smut | black smut / black mould infection on the surface |
| 6 | `discoloured` | Staining/Discoloration | surface staining, discoloration, or colour irregularity |
| 7 | `fresh_roots` | Rooting | fresh roots growing from the base |

One bounding box per onion instance. When an onion has MULTIPLE defects,
label the most severe visible condition. If annotating in detail, one onion
can have multiple defect labels (multi-label per bbox).

## NCCF features NOT YET trainable (need new data)

| NCCF Feature | Status | Priority |
|---|---|---|
| Ruptured skin | No training data | High |
| Open neck | No training data | High |
| Dry sun scald | No training data | Medium |
| Sun burn | No training data | Medium |
| Seed stem | 2 annotations (skipped) | Medium |
| Double/misshape | No training data | Medium (key for Grade-A vs URS) |
| Without skin | No training data | Low |
| Thick neck | Needs mm measurement | Low |

## Collection checklist (TEAM D leads, everyone helps)

- [ ] 300–500 photos minimum before first training run
- [ ] Mix of scenes: loose onions on tray, onions in jute bag/heap, single close-ups
- [ ] Lighting: daylight + indoor warm + slight shadow (robustness)
- [ ] Angles: top-down + 45°
- [ ] Defect balance: ≥50 images per defect class (harder to source — start now)
- [ ] Camera: any modern phone, 4:3 or 3:2, avoid digital zoom
- [ ] No people/number plates in frame; shoot in a clean workspace
- [ ] **NEW**: Include reference objects (coin, ruler) in calibration photos for size estimation

## File layout (already scaffolded in `ml/dataset/`)

```
dataset/
├── raw/          ← originals straight from the camera (gitignored — share via drive)
├── processed/    ← resized/curated versions (gitignored)
├── images/train/ ─┐
├── images/val/   ─┤ YOLO layout — what Ultralytics reads (data.yaml points here)
├── labels/train/ ─┤   images/xxx.jpg  ↔  labels/xxx.txt (same basename!)
├── labels/val/   ─┘
└── data.yaml     ← path/train/val/nc/names — already configured (8 classes)
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
YOLO only detects + classifies. The NCCF rule engine checks diameter against
the specification range (EOI: 45–65mm, PAACS: 35–70mm).

If you include a reference object (e.g. a coin) in some calibration photos,
keep them in `dataset/raw/calibration/`.
