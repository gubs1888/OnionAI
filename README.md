# Onion Quality AI

**AI-based Onion Quality Assessment and Grading System**
Smart India Hackathon 2026 · Problem Statement ID **26031**
Demo date: **11 September 2026**

> **This repository is the shared BASE FRAMEWORK (Milestone 1).** It is a
> stable, modular skeleton that four teams can clone and develop in parallel
> today. Incomplete parts run in a clearly-marked **DEMO MODE** — nothing is
> fake-finished, everything is honest.

---

## What works right now

| Area | Status |
|---|---|
| Backend API (FastAPI) | ✅ runs — 9 endpoints, contract schemas, uniform errors |
| Database (PostgreSQL / SQLite) | ✅ models + auto-init on empty DB |
| Inference | 🟡 **DEMO MODE** — deterministic synthetic detections, flagged `is_demo` |
| Grading + URS | ✅ MVP logic — config-driven, official thresholds **TO VERIFY** |
| PDF reports (ReportLab) | ✅ works, watermarked when demo |
| Mobile app (Expo) | ✅ full flow Home→Batch→Camera→Analyze→Results→Report (mock fallback offline) |
| ML pipeline | 🟡 structure + contract + tests ready; training waits on dataset |
| Docker | ✅ `docker compose up` → postgres + backend |
| Tests | ✅ 37 tests green (backend + ML contract tests) |

Legend: ✅ working · 🟡 structure ready, content pending

## Architecture in one picture

```
        TEAM C                      TEAM B                          TEAM A
   ┌─────────────┐   REST/JSON   ┌──────────────────────┐   contract   ┌──────────────┐
   │ React Native│ ────────────► │  FastAPI backend     │ ───────────► │ ml/ YOLO11n  │
   │ Expo router │ ◄──────────── │  services layer      │ ◄─────────── │ (or DEMO)    │
   └─────────────┘               │  ├ inference.py  ◄── only ML touchpoint          │
                                 │  ├ grading.py  ┌──────────────────────────────┐   │
                                 │  ├ urs.py      │ config/grading_config.json   │   │
                                 │  └ report.py   └──────────────────────────────┘   │
                                 └──────────┬───────────────────────────────────────┘
                                            │ SQLAlchemy
                                 ┌──────────▼──────────┐
                                 │ PostgreSQL (SQLite  │
                                 │ for zero-setup dev) │
                                 └─────────────────────┘
```

**Modularity rule:** the backend never imports torch/YOLO. All ML goes through
`backend/app/services/inference.py::analyze_image(path)` → TEAM A can swap DEMO
for a real model without touching a single route or screen.

## Quick start

### 0. Prerequisites
Python 3.11+, Node 18+, (optional) Docker.

### A. Everything with Docker (backend + database)

```bash
git clone <repo-url> && cd onion-quality-ai
cp .env.example .env          # defaults are fine for dev
docker compose up --build
# → http://localhost:8000/api/health
```

### B. Backend without Docker (zero-setup SQLite)

```bash
cd backend
python -m venv .venv && source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
# → http://localhost:8000/docs  (Swagger UI)
```

### C. Mobile app

```bash
cd mobile
npm install
npx expo start           # a = Android emulator, i = iOS simulator, w = web
```

The app works immediately (MOCK fallback when the backend is off). To use the
real backend from a device set `EXPO_PUBLIC_API_URL` (see `mobile/README.md`).

### Verify

```bash
curl http://localhost:8000/api/health
# {"status":"ok","service":"onion-quality-ai","version":"0.1.0","database":"connected","demo_mode":true,...}

python -m pytest            # 37 tests (backend + ML contracts)
```

## DEMO MODE — what it is and is not

* `DEMO_MODE=true` (default, `.env`) → `/api/analyze` returns **deterministic
  synthetic detections** (same photo ⇒ same result) flagged `"is_demo": true`.
* Mobile + reports show a visible **DEMO DATA** banner.
* ❌ Demo results are **never** real model accuracy and must never be
  presented as such — on stage or in documents.
* Switch to real inference later: train via `ml/train.py` → set
  `DEMO_MODE=false` + `MODEL_PATH` → done. No other code changes.

Demo login: `demo` / `demo123` (seeded automatically, DEMO ONLY).

## Team ownership

| Team | Owns | First tasks (see docs/demo/DEMO_SCRIPT.md too) |
|---|---|---|
| **A — ML/CV** | `ml/` | dataset, annotation, train YOLO11n, swap DEMO→real |
| **B — Backend** | `backend/` | harden endpoints, auth enforcement, Alembic, uploads polish |
| **C — Mobile** | `mobile/` | camera UX, wire real batch list, render tests, UI polish |
| **D — QA/Docs** | `docs/`, `scripts/`, tests | verify standards (URS!), API tests, demo script, dataset curation |

Branching: `main` ← `develop` ← `feature/ml` `feature/backend` `feature/mobile`
`feature/qa`. See **CONTRIBUTING.md**.

## Repository map

```
onion-quality-ai/
├── README.md / ARCHITECTURE.md / CONTRIBUTING.md / DEVELOPMENT.md
├── .env.example / docker-compose.yml / pytest.ini
├── backend/        FastAPI API + services + models + tests + Dockerfile
│   └── config/grading_config.json   ← ALL scoring thresholds live here
├── ml/             dataset layout, train/evaluate/inference, tests, data.yaml
├── mobile/         Expo app: 6 screens + 5 components + api client
├── docs/           api contract · dataset guide · standards · demo materials
└── scripts/        setup.sh, start-backend.sh, start-mobile.sh
```

## Key documents

* `docs/NEXT_STEPS.md` — **sprint plan to the 11 Sep demo (start here every morning)**
* `ARCHITECTURE.md` — module boundaries, data flow, design decisions
* `docs/api/API_CONTRACT.md` — **the** JSON contracts between teams
* `DEVELOPMENT.md` — setup, commands, troubleshooting
* `CONTRIBUTING.md` — branching, commits, PRs, ownership
* `docs/standards/STANDARDS_TO_VERIFY.md` — ⚠️ what TEAM D must verify before demo
* `docs/demo/` — sample analysis JSON, demo script for 11 Sep
