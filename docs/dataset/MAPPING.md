# CLASS MAPPING — source datasets → project contract (8-class system)

**Decision date:** 10 Sep 2026 · **Owner:** TEAM A + architect
**Previous version:** 4-class system (8 Sep 2026)
**Converter:** `ml/scripts/convert_roboflow_coco.py` (rerunnable)

## Source datasets

| Source | Roboflow project | Images | Native classes | License |
|---|---|---|---|---|
| `small` | `onion-condition-detection-5ycs5-ga8c5` | 151 | `good`, `bad` (+ empty junk class `badonion-goodonion`) | CC BY 4.0 |
| `large` | `onion-disease-rdezg-any7n` | 53 | 23 disease/condition labels incl. duplicates & typos (`onion` ×2, `blackmutinfected`/`blacksmutinfected` variants, combos like `sprouted-cuts`) | CC BY 4.0 |

Raw exports stay OUT of git (user's Google Drive). Curated result: `ml/dataset/`.

## 8-class system (aligned with NCCF 2026 procurement specs)

| ID | Class | NCCF Feature | Description |
|----|-------|-------------|-------------|
| 0 | `onion` | Healthy bulb | No defects detected |
| 1 | `damaged` | Mechanical Injury | Generic physical damage (only when no specific defect) |
| 2 | `rotten` | Rot/Rotting/Fungal | Decay, soft rot, fungal rot (NOT smut) |
| 3 | `sprouted` | Sprouted | Green sprout emerging from the bulb |
| 4 | `cut_crack` | Cut/Crack | Cuts, cracks |
| 5 | `smut` | Smut | Black smut / mut infection (surface fungal) |
| 6 | `discoloured` | Staining/Discoloration | Surface staining or discoloration |
| 7 | `fresh_roots` | Rooting | Fresh rooting / rooted |

## Mapping rule (8-class, fine-grained keyword matching)

Combo labels (e.g. `sprouted-blacksmutinfected`) emit **multiple annotations** on
the same bounding box. This matches reality — one onion can have multiple defects.

| Priority | Source keyword(s) (lowercased part) | → Contract class |
|---|---|---|
| 1 | `rotten` | **2 rotten** — decay (NOT smut) |
| 2 | `smut`, `mut` | **5 smut** — black smut infection |
| 3 | `sprout` | **3 sprouted** |
| 4 | `cut` | **4 cut_crack** |
| 5 | `discolou` | **6 discoloured** |
| 6 | `root`, `rooted`, `rooting` | **7 fresh_roots** |
| 7 | `onion`, `good` | **0 onion** — healthy |
| 8 | `bad` | **1 damaged** — only if no specific defect matched |
| — | `stem` | **skipped** (only 2 annotations — not enough to train) |

**Combo label handling:**
- Label is split on `-` (e.g. `sprouted-blacksmutinfected` → `sprouted` + `blacksmutinfected`)
- Each part is mapped independently → both class annotations emitted
- If `onion`/`good` appears alongside a defect → healthy is dropped (defect wins)
- If `bad` appears alongside a specific defect → generic `bad` is dropped

## Known caveats (honest list)

1. Two different annotation projects merged → label style differs (`bad` is
   broader than specific disease labels).
2. Boxes are loose/occasionally offset; a few class assignments are debatable
   (verified visually on sampled images).
3. Class imbalance: classes 4–7 have very few annotations (cut_crack: ~22, smut: ~150, discoloured: ~17, fresh_roots: ~4).
4. `small` dataset boxes are tiny (~3% of image) — dense pile photos; YOLO
   handles small objects but expect weaker recall there.
5. Both sources are Roboflow CC BY 4.0 → **attribution required** in the
   presentation/docs (already noted here; keep this file).
6. `fresh_roots` has only ~4 annotations — model will struggle with this class.
7. Combo labels produce multiple annotations per bbox — YOLO handles this but
   precision may be affected for overlapping classes.

## NCCF features NOT in the dataset (zero training data)

These NCCF specification features have no training data and are flagged as
"manual inspection required" by the rule engine:

- `ruptured_skin`
- `open_neck`
- `dry_sun_scald`
- `sunburn`
- `seed_stem`
- `double_misshape`
- `without_skin`
- `bacterial_soft_neck_rot`
- `thick_neck`
