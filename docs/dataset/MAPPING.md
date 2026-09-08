# CLASS MAPPING — source datasets → project contract

**Decision date:** 8 Sep 2026 · **Owner:** TEAM A + architect
**Converter:** `ml/scripts/convert_roboflow_coco.py` (rerunnable)

## Source datasets

| Source | Roboflow project | Images | Native classes | License |
|---|---|---|---|---|
| `small` | `onion-condition-detection-5ycs5-ga8c5` | 151 | `good`, `bad` (+ empty junk class `badonion-goodonion`) | CC BY 4.0 |
| `large` | `onion-disease-rdezg-any7n` | 53 | 23 disease/condition labels incl. duplicates & typos (`onion` ×2, `blackmutinfected`/`blacksmutinfected` variants, combos like `sprouted-cuts`) | CC BY 4.0 |

Raw exports stay OUT of git (user's Google Drive). Curated result: `ml/dataset/`.

## Mapping rule (severity-priority, first match wins)

| Priority | Source keyword(s) (lowercased substring) | → Contract class |
|---|---|---|
| 1 | `rotten`, `smut`, `mut` | **2 rotten** — fungal decay bucket (black smut/mut typos included) |
| 2 | `sprout`, `root` | **3 sprouted** |
| 3 | `cut`, `discolou`, `bad` | **1 damaged** — physical/surface defect; generic `bad` lands here |
| 4 | `onion`, `good` | **0 onion** — healthy |
| — | anything else (`stem`, …) | **skipped** (counted + reported) |

Rationale: grading cares about the WORST visible condition, so more severe
conditions win over combo labels (e.g. `sprouted-blacksmutinfected` → rotten).

## Known caveats (honest list)

1. Two different annotation projects merged → label style differs (`bad` is
   broader than specific disease labels).
2. Boxes are loose/occasionally offset; a few class assignments are debatable
   (verified visually on sampled images).
3. Class imbalance: damaged ≫ sprouted (see DATASET_STATS.md).
4. `small` dataset boxes are tiny (~3% of image) — dense pile photos; YOLO
   handles small objects but expect weaker recall there.
5. Both sources are Roboflow CC BY 4.0 → **attribution required** in the
   presentation/docs (already noted here; keep this file).

If any of these blocks the mAP gate on 9 Sep, prefer FIXING LABELS on the
worst 30 images over architecture changes.
