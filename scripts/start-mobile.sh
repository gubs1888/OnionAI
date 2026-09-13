#!/usr/bin/env bash
# Start the Expo dev server for the mobile app.
set -euo pipefail
cd "$(dirname "$0")/../mobile"

if [ ! -d node_modules ]; then
  echo "==> Installing mobile dependencies"
  npm install --no-audit --no-fund
fi

echo "==> Starting Expo (EXPO_PUBLIC_API_URL=${EXPO_PUBLIC_API_URL:-http://localhost:8000})"
exec npx expo start
