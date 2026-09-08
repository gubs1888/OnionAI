# DATASET STATS (generated 8 Sep 2026 by ml/scripts/convert_roboflow_coco.py)

## Headline numbers (for the presentation slide)

| | train | val | total |
|---|---|---|---|
| **Images** | 148 | 56 | **204** |
| **Boxes** | 1049 | 362 | **1411** |

## Boxes per class

| class | train | val | total | share |
|---|---|---|---|---|
| 0 onion | 322 | 90 | **412** | 29.2% |
| 1 damaged | 538 | 179 | **717** | 50.8% |
| 2 rotten | 133 | 69 | **202** | 14.3% |
| 3 sprouted | 56 | 24 | **80** | 5.7% |

Split: Roboflow train → train; Roboflow valid + test merged → val.
Validation: 100% of label files parse; classes ⊆ {0,1,2,3}; coords in [0,1];
image/label 1:1 — no orphans. 2 `stem` boxes skipped (see MAPPING.md).

## Provenance

* Sources: two Roboflow exports (CC BY 4.0) — see `docs/dataset/MAPPING.md`
* Preprocessing: RGB JPEG, max side 960 px, quality 88
* Raw archives: team Google Drive (`dataset_small.zip` 11.9 MB, `dataset_large.zip` 190 MB) — not in git
* `data.yaml`: 4 classes, points at `images/{train,val}` — ready for `python ml/train.py`

## Gaps to close during the sprint

- [ ] sprouted class is thin (80 boxes) → prioritise sprouted-onion photos tonight
- [ ] quality-pass on the 30 worst-annotated images before the GO/NO-GO gate
