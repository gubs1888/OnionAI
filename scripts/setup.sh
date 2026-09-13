#!/usr/bin/env bash
# Onion Quality AI — one-time setup (TEAM D owns scripts/)
# Creates .env, a Python venv for the backend, and installs dependencies.
set -euo pipefail
cd "$(dirname "$0")/.."
ROOT="$(pwd)"

echo "==> Onion Quality AI — setup"

if [ ! -f .env ]; then
  cp .env.example .env
  echo "    created .env from .env.example (defaults are fine for dev)"
else
  echo "    .env already exists — keeping it"
fi

echo "==> Creating backend virtualenv (.venv)"
python3 -m venv .venv
.venv/bin/pip install --upgrade pip -q
echo "==> Installing backend requirements"
.venv/bin/pip install -q -r backend/requirements.txt

echo "==> Installing mobile dependencies (npm)"
if command -v npm >/dev/null 2>&1; then
  (cd mobile && npm install --no-audit --no-fund)
else
  echo "    WARN: npm not found — install Node 18+ then run: cd mobile && npm install"
fi

cat <<'DONE'

Setup complete. Next steps:
  Backend:   source .venv/bin/activate && cd backend && uvicorn app.main:app --reload --port 8000
             (or: bash scripts/start-backend.sh)
  Database:  docker compose up -d postgres        (optional — SQLite works without it)
  Mobile:    bash scripts/start-mobile.sh
  Tests:     .venv/bin/python -m pytest
DONE
