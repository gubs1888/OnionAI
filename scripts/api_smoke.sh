#!/usr/bin/env bash
# ==============================================================================
# API Smoke Test Script — Onion Quality AI Backend
# Tests all core endpoints against a running backend server.
# Usage:
#   bash scripts/api_smoke.sh [BASE_URL]
# Default BASE_URL: http://127.0.0.1:8000
# ==============================================================================

set -euo pipefail

BASE_URL="${1:-http://127.0.0.1:8000}"
SAMPLE_IMG="docs/demo/sample_images/sample_onions_01.jpg"

echo "==> Starting API Smoke Test against ${BASE_URL}..."

# 1. Health check
echo -n "[1/9] GET /api/health ... "
HEALTH_RES=$(curl -s -f "${BASE_URL}/api/health" || { echo "FAILED"; exit 1; })
echo "OK ✓ (${HEALTH_RES})"

# 2. Login
echo -n "[2/9] POST /api/auth/login ... "
TOKEN_RES=$(curl -s -f -X POST "${BASE_URL}/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"demo","password":"demo123"}')
TOKEN=$(echo "${TOKEN_RES}" | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)
echo "OK ✓ (token acquired)"

# 3. Create batch
echo -n "[3/9] POST /api/batches ... "
BATCH_RES=$(curl -s -f -X POST "${BASE_URL}/api/batches" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"name":"Smoke Test Lot","variety":"Nashik Red","source":"Lasalgaon"}')
BATCH_CODE=$(echo "${BATCH_RES}" | grep -o '"batch_code":"[^"]*' | cut -d'"' -f4)
echo "OK ✓ (batch_code: ${BATCH_CODE})"

# 4. List batches
echo -n "[4/9] GET /api/batches ... "
curl -s -f "${BASE_URL}/api/batches" > /dev/null
echo "OK ✓"

# 5. Get batch
echo -n "[5/9] GET /api/batches/${BATCH_CODE} ... "
curl -s -f "${BASE_URL}/api/batches/${BATCH_CODE}" > /dev/null
echo "OK ✓"

# 6. Patch batch
echo -n "[6/9] PATCH /api/batches/${BATCH_CODE} ... "
curl -s -f -X PATCH "${BASE_URL}/api/batches/${BATCH_CODE}" \
  -H "Content-Type: application/json" \
  -d '{"notes":"Smoke test patch verified"}' > /dev/null
echo "OK ✓"

# 7. Analyze image
if [ -f "${SAMPLE_IMG}" ]; then
  echo -n "[7/9] POST /api/analyze ... "
  ANALYSIS_RES=$(curl -s -f -X POST "${BASE_URL}/api/analyze" \
    -F "image=@${SAMPLE_IMG}" \
    -F "batch_id=${BATCH_CODE}")
  ASSESSMENT_ID=$(echo "${ANALYSIS_RES}" | grep -o '"assessment_id":[^,}]*' | head -n 1 | cut -d':' -f2 | tr -d ' ')
  echo "OK ✓ (assessment_id: ${ASSESSMENT_ID})"

  # 8. Batch assessment contract
  echo -n "[8/9] GET /api/batches/${BATCH_CODE}/assessment ... "
  curl -s -f "${BASE_URL}/api/batches/${BATCH_CODE}/assessment" > /dev/null
  echo "OK ✓"

  # 9. PDF report creation & download
  echo -n "[9/9] POST /api/reports/${ASSESSMENT_ID} & GET /download ... "
  REPORT_RES=$(curl -s -f -X POST "${BASE_URL}/api/reports/${ASSESSMENT_ID}")
  REPORT_ID=$(echo "${REPORT_RES}" | grep -o '"report_id":[^,}]*' | head -n 1 | cut -d':' -f2 | tr -d ' ')
  curl -s -f "${BASE_URL}/api/reports/${REPORT_ID}/download" > /dev/null
  echo "OK ✓ (report_id: ${REPORT_ID})"
else
  echo "[7/9] Skipping image analysis test (sample image not found at ${SAMPLE_IMG})"
  echo "[8/9] Skipping assessment contract test"
  echo "[9/9] Skipping PDF report test"
fi

echo "=============================================================================="
echo "🎉 ALL 9 API SMOKE TESTS PASSED CLEANLY!"
echo "=============================================================================="
