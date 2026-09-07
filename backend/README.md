# Backend — Onion Quality AI (TEAM B)

FastAPI + SQLAlchemy + PostgreSQL (SQLite for zero-setup dev). **DEMO MODE is
ON by default** so the whole team works before the real YOLO model exists.

## Quick start (no Docker)

```bash
cd backend
python -m venv .venv && source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Open http://localhost:8000/docs (Swagger UI). Without Docker the default DB is
SQLite (`onion_quality_dev.db`) — nothing else to configure.

## Quick start (Docker)

From the repository root:

```bash
cp .env.example .env
docker compose up --build
```

## Demo login

`POST /api/auth/login` with `{"username": "demo", "password": "demo123"}`
(seeded automatically). DEMO ONLY.

## Layout

```
app/
├── main.py          FastAPI app, lifespan, error envelope
├── config.py        Settings (env/.env driven)
├── api/             health, auth, batches, analysis, reports  (routes only)
├── schemas/         Pydantic contracts (batch / analysis / report)
├── models/          SQLAlchemy ORM (users, batches, images, detections, assessments, reports)
├── services/        inference | preprocessing | measurement | grading | urs | report | auth
└── db/              engine/session + create_all init + migrations/ (Alembic later)
config/grading_config.json   ALL scoring thresholds — tune here, not in code
tests/               pytest suite (uses in-memory SQLite)
uploads/             uploaded images (gitignored)
reports/             generated PDFs (gitignored)
```

## The one rule that matters

**The backend never imports torch/ultralytics directly.** All ML goes through
`app/services/inference.py::analyze_image(path)` which returns the agreed
detection contract. TEAM A can swap DEMO for YOLO without touching any route.

## API surface (MVP)

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/health` | liveness + honest DB status + demo_mode |
| POST | `/api/auth/login` | JWT token (demo/demo123) |
| POST | `/api/batches` | create batch |
| GET | `/api/batches` | list batches |
| GET | `/api/batches/{batch_id}` | get batch (id or code) |
| GET | `/api/batches/{batch_id}/assessment` | latest assessment for batch |
| POST | `/api/analyze` | upload image → assess (multipart) |
| POST | `/api/reports/{assessment_id}` | generate PDF report |
| GET | `/api/reports/{report_id}` | report metadata |
| GET | `/api/reports/{report_id}/download` | download PDF |

Full request/response examples: `docs/api/API_CONTRACT.md`.

## Tests

```bash
python -m pytest backend/tests -q        # from repo root
# or from backend/:  python -m pytest tests -q
```

## Ownership

TEAM B owns everything in `backend/` and `backend/config/grading_config.json`.
TEAM A only touches `app/services/inference.py` (the YOLO adapter) when the
real model lands. Contract changes require sign-off from all teams.
