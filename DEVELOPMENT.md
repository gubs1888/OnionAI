# DEVELOPMENT — setup, commands, troubleshooting

## 0. Prerequisites

* Python **3.11+**
* Node **18+** (20 LTS recommended)
* Git
* Docker (optional — only for PostgreSQL via compose)
* A phone with **Expo Go** (Android/iOS) or an emulator for mobile dev

## 1. One-time setup

```bash
git clone <repo-url> && cd onion-quality-ai
cp .env.example .env                  # defaults are fine for local dev
# or: bash scripts/setup.sh
```

### Backend (zero-setup: SQLite)

```bash
cd backend
python -m venv .venv && source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

* Swagger UI: http://localhost:8000/docs
* Health: http://localhost:8000/api/health
* First start creates `onion_quality_dev.db` and seeds login `demo/demo123`.

### Backend with PostgreSQL (Docker)

```bash
docker compose up --build             # from repo root; postgres + backend
# DATABASE_URL in .env switches the backend to PostgreSQL automatically in compose.
```

### Mobile

```bash
cd mobile
npm install
npx expo start
# press a (Android emu) / i (iOS sim) / w (web), or scan the QR with Expo Go
```

Backend URL for the app — pick per device:

```bash
EXPO_PUBLIC_API_URL=http://localhost:8000 npx expo start        # iOS sim / web
EXPO_PUBLIC_API_URL=http://10.0.2.2:8000 npx expo start         # Android emu
EXPO_PUBLIC_API_URL=http://192.168.x.x:8000 npx expo start --tunnel  # phone
```

No backend running? The app still navigates end-to-end using clearly-marked
MOCK data (`mobile/services/api.ts`).

### ML environment (heavy — only TEAM A needs it locally)

```bash
python -m venv .venv-ml && source .venv-ml/bin/activate
pip install -r ml/requirements.txt
```

## 2. Daily commands

| Task | Command |
|---|---|
| Start backend (dev) | `uvicorn app.main:app --reload --port 8000` (from `backend/`) |
| Start DB+backend (docker) | `docker compose up` |
| Start mobile | `cd mobile && npx expo start` |
| Run ALL tests | `python -m pytest` (repo root — backend + ML) |
| Backend tests only | `python -m pytest backend/tests` |
| ML tests only | `python -m pytest ml/tests` |
| Mobile smoke test | `cd mobile && npm run smoke` |
| Reset local SQLite DB | delete `backend/onion_quality_dev.db`, restart backend |
| Helper scripts | `bash scripts/start-backend.sh` / `bash scripts/start-mobile.sh` |

## 3. Environment variables

Everything is in `.env.example` with comments. Copy → `.env` → edit.
**Never commit `.env`.** Key switches:

* `DEMO_MODE=true|false` — synthetic vs real inference
* `DATABASE_URL` — postgres URL, or sqlite for zero-setup
* `MODEL_PATH` — where the trained `onion_yolo.pt` lives
* `EXPO_PUBLIC_API_URL` — backend URL for the mobile app

## 4. Troubleshooting

| Symptom | Fix |
|---|---|
| `GET /api/health` shows `"database":"disconnected"` | compose: wait for postgres healthcheck; local: check `DATABASE_URL` |
| Mobile can't reach backend | wrong `EXPO_PUBLIC_API_URL` for the device type — see table above |
| Port 8000 busy | `uvicorn ... --port 8001` and update `EXPO_PUBLIC_API_URL` |
| `ultralytics not installed` | expected outside ML venv — keep `DEMO_MODE=true` for app dev |
| Expo `47.x mismatch` errors | `cd mobile && rm -rf node_modules && npm install` |
| Tests fail with DB locked | stop the running uvicorn (SQLite single-writer), re-run |

## 5. Where things live (fast links)

* API contracts → `docs/api/API_CONTRACT.md`
* Scoring thresholds → `backend/config/grading_config.json`
* ML class contract → `ml/dataset/data.yaml` + `ml/config.py`
* Demo materials → `docs/demo/`
* What NOT to build → `ARCHITECTURE.md §8`
