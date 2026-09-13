#!/usr/bin/env bash
# Start the backend in dev mode (SQLite default; respects .env).
set -euo pipefail
cd "$(dirname "$0")/../backend"

if [ ! -d ../.venv ]; then
  echo "No .venv found — run scripts/setup.sh first (or create your own venv)."
  exit 1
fi

exec ../.venv/bin/python -m uvicorn app.main:app --reload --host 0.0.0.0 --port "${BACKEND_PORT:-8000}"
