# Onion dataset expansion + retrain

## The short version

You asked for 4000 images scraped from the internet. What you actually need is
roughly **4000 labelled onions across ~600–900 images**, and the majority of the
value comes from about **80 photos taken with your own phone**, on white paper,
labelled by hand.

Scraped-but-unlabelled images contribute nothing to YOLO detection training.
Auto-labelling them with `ml/models/onion_yolo.pt` is worse than nothing,
because that checkpoint calls clean bulbs rotten at 0.82–0.87 — you would be
training the next model to repeat the bug you are trying to remove.

## Why the current model fails

Two separate problems, from the session log:

1. **Domain shift.** Every training image is a dim crate pile. Every photo the
   app receives is a single layer of bulbs on bright paper. The model has never
   seen the deployment domain, so it keys on scene cues and produces confident
   nonsense on white backgrounds.
2. **Label semantics.** The `damaged` class (717 boxes, the largest class) is a
   catch-all that includes dry skin and surface staining. The model learned
   "dark patch = defect". Meanwhile `rotten` has 202 boxes and four classes
   have zero.

Neither is fixed by volume. Both are fixed by *targeted* data.

## Priority order

| Priority | What | Count | Why |
|---|---|---|---|
| 1 | Your own phone photos, white paper, all-healthy bulbs, hand-labelled | ~60–80 images | Directly kills the false-rot bug. Highest value per hour by a wide margin. |
| 2 | Your own photos of genuinely rotten + sprouted bulbs, same setup | ~60 images | Teaches the real decision boundary in the deployment domain. |
| 3 | Public labelled sets (Roboflow Universe) | ~300–500 images | Cheap volume for the healthy baseline and pile scenes. |
| 4 | Open Images `Onion` class | as available | Healthy bulbs only. Background/negative diversity. |

Stop adding generic `damaged`. Relabel or drop it — `merge_datasets.py` drops it
by default.

## Class schema change

The grading spec only cares about **rotten, sprouted, undersized**. Undersized is
a measurement output, not a detection class. So the detector needs three classes,
not eight:

```
0 onion    1 rotten    2 sprouted
```

Surface staining and sunburn are Grade A/URS *modifiers* computed from pixels
inside an already-detected box — they do not need their own detection classes,
and giving them classes with 0 training samples is what produced the phantom
predictions.

## Running it

```bash
cd /home/michael/onion-quality-ai

export ROBOFLOW_API_KEY=...          # free account
python fetch_datasets.py --out ml/dataset_raw

# verify every Universe project in the web UI before trusting its labels
python merge_datasets.py --raw ml/dataset_raw --existing ml/dataset \
                         --out ml/dataset_v2 --val-frac 0.2

# label your own staged photos into ml/holdout_staged/{images,labels}/ first
python train_v2.py --data ml/dataset_v2/data.yaml --epochs 120
```

`merge_datasets.py` will print any class name it does not recognise rather than
guessing. Add it to `CLASS_MAP` and re-run — never let an unmapped class through.

## Labelling

Use Label Studio or CVAT locally, or Roboflow's free tier. Box the whole bulb,
including the visible skin, not just the defect patch. One box per bulb. For a
partly-occluded bulb, box the visible extent — that is what the model must learn
to fire on, and it is exactly the case that caused your undercount.

Budget: ~60–90 seconds per image for a 6-bulb photo. 80 images is about two
hours. That two hours is worth more than 3,800 scraped files.

## After the retrain

`backend/app/services/inference.py` currently contains several hacks added to
force one specific photo to give the right answer: `DETECT_CONF = 0.12`, the
bright-background ratio gate, the 0.90/0.80 split defect threshold, and the
low-confidence recovery pass. They were tuned on two images.

Once the retrained model passes the staged holdout, take them out and re-test at
a plain `conf=0.25`. If results degrade without the hacks, the model still is not
fixed and the hacks are hiding it.
