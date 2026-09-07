# ARCHITECTURE — Onion Quality AI

Smart India Hackathon 2026 · PS 26031 · foundation version 0.1.0

## 1. Design principles

| Principle | How it shows up in the code |
|---|---|
| **Modular** | 4 independent modules (ml / backend / mobile / docs). The backend never imports torch; screens never call fetch; grading never touches the DB. |
| **Contract-first** | JSON contracts + schemas defined BEFORE features (`docs/api/API_CONTRACT.md`, `backend/app/schemas/`, `mobile/types/assessment.ts`, `ml/inference.py`). |
| **Demo-first** | `DEMO_MODE=true` default. Deterministic synthetic inference lets all teams + the final demo work before the model exists. Always flagged `is_demo`. |
| **Testable** | Pure service functions, 37 tests, in-memory SQLite for API tests, ML tests need zero heavy deps. |
| **Easy to collaborate** | Path ownership, feature branches, one shared contract file per direction, config over code. |

## 2. System overview

```
┌────────────────────────────┐
│ MOBILE (TEAM C)            │  React Native + Expo SDK 53 + expo-router
│ Home→Batch→Camera→         │  screens: app/*.tsx
│ Analyzing→Results→Report   │  api client: services/api.ts (only touchpoint)
└─────────────┬──────────────┘
              │ REST + JSON (contracts in docs/api/API_CONTRACT.md)
┌─────────────▼──────────────────────────────────────────────┐
│ BACKEND (TEAM B)                        uvicorn :8000      │
│                                                            │
│  api/        health · auth · batches · analysis · reports  │  ← routes ONLY
│  schemas/    pydantic wire contracts                       │
│  services/   inference → measurement → grading → urs       │  ← business logic
│              report (PDF) · auth (JWT)                     │
│  models/     SQLAlchemy: users, batches, images,           │
│              detections, assessments, reports              │
│  db/         engine + create_all init (Alembic later)      │
│  config/grading_config.json   ← ALL thresholds (MVP vs     │
│                                  OFFICIAL-TO-VERIFY)       │
└──────┬─────────────────────────────┬───────────────────────┘
       │ STABLE contract             │ STABLE contract
┌──────▼──────────────┐   ┌──────────▼─────────────────────┐
│ PostgreSQL          │   │ ML GATEWAY                     │
│ (SQLite in dev)     │   │ app/services/inference.py      │
└─────────────────────┘   │  ├ DEMO: hash-seeded synthetic │
                          │  └ REAL: lazy YOLO on          │
                          │         ml/models/onion_yolo.pt│
                          └──────────┬─────────────────────┘
                          ┌──────────▼─────────────────────┐
                          │ ml/ (TEAM A)                   │
                          │ train.py · evaluate.py ·       │
                          │ inference.py (OnionDetector)   │
                          │ dataset/{raw,processed,        │
                          │   images,labels} + data.yaml   │
                          │ classes: 0 onion · 1 damaged · │
                          │ 2 rotten · 3 sprouted          │
                          └────────────────────────────────┘
```

## 3. The analysis data flow (single most important path)

```
POST /api/analyze (multipart image, optional batch_id)
  1 validate type/size                 api/analysis.py
  2 resolve or create batch            api/deps.py
  3 store file  → uploads/             backend/uploads (gitignored)
  4 detections = inference.analyze_image(path)
  5 sizes      = measurement.estimate_sizes(detections)
  6 counts     = grading.aggregate_counts(detections)
  7 urs%       = urs.compute_urs(counts)               ← formula from config
  8 score/grade/reasons = grading.grade_batch(...)    ← weights from config
  9 persist  Image + Detections + Assessment
 10 respond Assessment contract (+ detections detail, + is_demo flag)
```

Steps 4–8 are pure, independently testable functions. Any team can replace its
step without touching the others.

## 4. Replaceability contracts

| Swap | What changes | What does NOT change |
|---|---|---|
| DEMO → real YOLO | `ml/train.py` output + `.env` (`DEMO_MODE=false`, `MODEL_PATH`) | API routes, mobile app, reports |
| Grading heuristic → official thresholds | `backend/config/grading_config.json` (`official_standards_TO_VERIFY` section after TEAM D verifies) | grading.py interface, API, mobile |
| URS interpretation | `grading_config.json → urs.categories` | urs.py, everything else |
| SQLite → PostgreSQL | `DATABASE_URL` in `.env` | all models/endpoints |
| PDF → other format | `services/report.py` internals | `/api/reports/*` routes |

## 5. Database schema

```
users(id, username✦, password_hash, role, created_at)
  1 ── * batches
batches(id, batch_code✦ ON-0001, name, variety, source, notes, status, created_by→users, created_at)
  1 ── * images                       1 ── * assessments
images(id, batch_id→batches, file_path, original_filename, status, created_at)
  1 ── * detections
detections(id, image_id→images, class_id, class_name, confidence, bbox JSON, estimated_size_mm, created_at)
assessments(id, batch_id→batches, image_id→images?, total_onions, healthy, damaged, rotten,
            sprouted, undersized, defect_percentage, quality_score, grade, urs_percentage,
            avg_confidence, reasons JSON, is_demo, model_version, created_at)
  1 ── * reports
reports(id, report_code✦, assessment_id→assessments, file_path, format, is_demo, generated_at)
```

✦ = unique. Buckets are mutually exclusive and sum to `total_onions`.
Init: `Base.metadata.create_all()` on startup — safe on an empty DB. Alembic
slot reserved at `backend/app/db/migrations/`.

## 6. Grading & URS design

* **No official standard is hard-coded.** All numbers live in
  `backend/config/grading_config.json`.
* `mvp_scoring` (active): `score = 100 − w_defect·defect% − w_urs·URS% −
  w_conf·lowConfidencePenalty`, grades A/B/C/D at 80/60/40/0 (MVP placeholders).
* `official_standards_TO_VERIFY`: reserved, unused by code, filled only after
  TEAM D verification (docs/standards/).
* **URS definition is NOT verified.** Current configurable interpretation:
  `URS% = (undersized + rotten + sprouted) / total × 100`. The category list in
  config IS the formula.

## 7. Honest-status policy

| Flag | Meaning | Where enforced |
|---|---|---|
| `is_demo: true` | synthetic result | assessment schema, mobile banner, PDF watermark |
| `model_version` | provenance | `demo-v0` vs `yolo11n-*` |
| `/api/health → database` | real `SELECT 1` probe — never faked | health.py |
| `503 INFERENCE_UNAVAILABLE` | real mode requested, model missing | inference.py |

## 8. Deliberately OUT of scope (roadmap, do not build now)

auto-retraining · marketplace · advanced analytics · IoT · blockchain ·
microservices · Kubernetes · complex RBAC · chatbot · production cloud.
