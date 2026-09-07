# API CONTRACT — Onion Quality AI

**THE single source of truth for all cross-team JSON.**
Version: 1.0 (foundation) · Base URL: `http://localhost:8000`

**Stability rules**
1. Any field rename/removal = contract change → all four teams agree first.
2. Adding optional fields is fine — clients must tolerate unknown fields.
3. Errors ALWAYS use the envelope: `{"error": {"code", "message", "details"}}`.
4. DEMO results are always flagged `"is_demo": true` and clients MUST surface it.

---

## Endpoints

### GET /api/health
```json
{
  "status": "ok",            // "ok" | "degraded"
  "service": "onion-quality-ai",
  "version": "0.1.0",
  "database": "connected",   // real probe — NEVER faked; "disconnected" if down
  "demo_mode": true,
  "time": "2026-09-07T10:00:00+00:00"
}
```

### POST /api/auth/login
Request:
```json
{"username": "demo", "password": "demo123"}
```
Response `200`:
```json
{"access_token": "<jwt>", "token_type": "bearer", "expires_in": 43200,
 "user": {"id": 1, "username": "demo", "role": "operator"}}
```
`401` on bad credentials (`code: "INVALID_CREDENTIALS"`).

### POST /api/batches
Request:
```json
{"name": "Lot A — Nashik farm", "variety": "Nashik Red", "source": "Lasalgaon Mandi", "notes": null}
```
Response `201`:
```json
{"id": 1, "batch_code": "ON-0001", "name": "Lot A — Nashik farm", "variety": "Nashik Red",
 "source": "Lasalgaon Mandi", "notes": null, "status": "created",
 "created_by": null, "image_count": 0, "created_at": "2026-09-07T10:00:00"}
```

### GET /api/batches?status=analyzed&limit=50
Response `200`: array of batch objects (same shape as above).

### GET /api/batches/{batch_id}
`{batch_id}` = numeric id **or** batch code (`ON-0001`). `200` batch object / `404 BATCH_NOT_FOUND`.

### POST /api/analyze
`multipart/form-data`:
| field | type | required |
|---|---|---|
| `image` | file (jpg/jpeg/png, ≤15 MB) | ✔ |
| `batch_id` | string (id or code) | ✖ (walk-in batch auto-created) |

Response `200` — **Backend → Mobile core contract**:
```json
{
  "assessment_id": 1,
  "batch_id": "ON-0001",
  "total_onions": 48,
  "healthy": 39,
  "damaged": 4,
  "rotten": 2,
  "sprouted": 1,
  "undersized": 2,
  "defect_percentage": 18.75,
  "quality_score": 76.4,
  "grade": "B",
  "urs_percentage": 12.5,
  "confidence": 91.7,
  "reasons": ["7/48 onions non-healthy (defect 14.6%) -8.8 pts", "..."],
  "is_demo": true,
  "model_version": "demo-v0",
  "created_at": "2026-09-07T10:00:00",
  "image_id": 1,
  "detections": [
    {"class_name": "rotten", "class_id": 2, "confidence": 0.94,
     "bbox": [112.0, 61.0, 340.0, 280.0], "estimated_size_mm": 82.4}
  ]
}
```
Notes:
* The example numbers are illustrative only — nothing is hard-coded.
* Buckets are mutually exclusive: `healthy+damaged+rotten+sprouted+undersized == total_onions`.
* `defect_percentage = 100 − healthy%` (undersized counts as non-healthy).
* `quality_score`/`grade` come from OUR MVP scoring — not an official standard.
* `confidence` = mean detection confidence × 100.
* DEMO MODE: same image bytes ⇒ identical result (deterministic).
Errors: `404 BATCH_NOT_FOUND` · `422 UNSUPPORTED_FILE_TYPE | FILE_TOO_LARGE | NOTHING_DETECTED` · `503 INFERENCE_UNAVAILABLE` (real mode, model missing).

### GET /api/batches/{batch_id}/assessment
Latest assessment for the batch — same shape as the analyze response minus
`image_id`/`detections`. `404 ASSESSMENT_NOT_FOUND` until first analysis.

### POST /api/reports/{assessment_id}
Response `201`:
```json
{"report_id": 1, "report_code": "RPT-0001-20260907-101500", "assessment_id": 1,
 "batch_id": "ON-0001", "format": "pdf", "is_demo": true,
 "generated_at": "2026-09-07T10:01:00", "download_url": "/api/reports/1/download"}
```
Demo-based reports are watermarked **"DEMO DATA — NOT FOR OFFICIAL USE"**.
`501 REPORT_UNAVAILABLE` if reportlab missing.

### GET /api/reports/{report_id}
Metadata (same shape). Accepts id or report code.

### GET /api/reports/{report_id}/download
Binary PDF. `404 REPORT_NOT_FOUND` · `410 FILE_MISSING`.

---

## ML → Backend contract (internal)

`backend/app/services/inference.py::analyze_image(path)` and
`ml/inference.py::OnionDetector.detect(path)` return the same shape:

```json
{
  "detections": [
    {"class_name": "rotten", "class_id": 2, "confidence": 0.94, "bbox": [x1, y1, x2, y2]}
  ],
  "model_version": "demo-v0 | yolo11n-onion_yolo",
  "is_demo": true,
  "inference_ms": 12.3,
  "note": "DEMO MODE: ... (only when is_demo)"
}
```
Classes (STABLE): `0=onion, 1=damaged, 2=rotten, 3=sprouted`.

## Grading engine contract (internal)

Input (pure function, no DB):
```json
{"counts": {"total_onions": 48, "healthy": 39, "damaged": 4, "rotten": 2, "sprouted": 1, "undersized": 2},
 "urs_percentage": 12.5, "avg_confidence": 0.917}
```
Output:
```json
{"quality_score": 76.4, "grade": "B", "reasons": ["..."]}
```
All thresholds: `backend/config/grading_config.json` → `mvp_scoring` (active)
and `official_standards_TO_VERIFY` (inactive until verified).
URS formula = `urs.categories` list in the same file — **definition NOT yet verified**.
