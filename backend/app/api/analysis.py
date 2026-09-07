"""
POST /api/analyze — upload an image, run the ML gateway, aggregate, grade, persist.

Orchestration ONLY: every hard problem lives in a service module.
  inference.py  -> detections          (TEAM A swap point)
  measurement.py -> sizes
  grading.py    -> counts + score + grade + reasons
  urs.py        -> URS %

If DEMO MODE is on (default) the whole chain works TODAY with clearly-marked
synthetic data.
"""

import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user_optional, get_db, require_batch
from app.config import BACKEND_ROOT, settings
from app.models.batch import Batch
from app.models.detection import Detection
from app.models.image import Image
from app.models.user import User
from app.schemas.analysis import AnalyzeResponse, DetectionOut, to_assessment_out
from app.services import grading, inference, measurement, urs as urs_service
from app.services.grading import GradingError
from app.services.inference import InferenceError

router = APIRouter(tags=["analysis"])

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png"}
MAX_UPLOAD_BYTES = 15 * 1024 * 1024  # 15 MB


@router.post(
    "/analyze",
    response_model=AnalyzeResponse,
    summary="Upload an image and run the quality-assessment pipeline",
    description=(
        "multipart/form-data fields:\n"
        "- `image`: jpg/jpeg/png file (required)\n"
        "- `batch_id`: batch code or numeric id (optional — a walk-in batch is "
        "created when omitted)\n\n"
        "Runs: save image -> inference service -> size estimation -> grading -> "
        "URS -> persist (image, detections, assessment). "
        "**When DEMO MODE is on the detections are synthetic and the response is "
        "flagged `is_demo: true` — the client must show a DEMO banner.**"
    ),
    responses={
        404: {"description": "batch_id provided but not found"},
        422: {"description": "Unsupported file type, empty file, or nothing detected"},
        503: {"description": "Real inference requested but model unavailable"},
    },
)
def analyze_image_endpoint(
    image: UploadFile = File(..., description="Batch photo (jpg/jpeg/png)"),
    batch_id: str | None = Form(default=None, description="Batch code or id (optional)"),
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
) -> AnalyzeResponse:
    # 1. Validate upload -----------------------------------------------------
    original_name = image.filename or "upload.jpg"
    ext = Path(original_name).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": "UNSUPPORTED_FILE_TYPE",
                "message": f"'{ext}' not allowed. Use one of: {sorted(ALLOWED_EXTENSIONS)}.",
            },
        )

    # 2. Resolve / create the batch ------------------------------------------
    if batch_id:
        batch = require_batch(db, batch_id)
    else:
        batch = Batch(
            batch_code=f"ON-{(db.query(Batch).count() or 0) + 1:04d}",
            name=f"Walk-in batch {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')}",
            status="created",
            created_by=current_user.id if current_user else None,
        )
        db.add(batch)
        db.flush()

    # 3. Persist the uploaded file -------------------------------------------
    stored_name = f"{uuid.uuid4().hex}{ext}"
    stored_path = settings.upload_dir / stored_name
    size_limit = MAX_UPLOAD_BYTES
    with stored_path.open("wb") as out:
        shutil.copyfileobj(image.file, out, length=1024 * 1024)
        if out.tell() > size_limit:
            out.close()
            stored_path.unlink(missing_ok=True)
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"code": "FILE_TOO_LARGE", "message": "Max upload size is 15 MB."},
            )

    image_row = Image(
        batch_id=batch.id,
        file_path=str(stored_path.relative_to(BACKEND_ROOT)),
        original_filename=original_name,
        status="processing",
    )
    db.add(image_row)
    db.flush()

    # 4. Inference (DEMO or real YOLO — the caller cannot tell, by design) ----
    try:
        result = inference.analyze_image(str(stored_path))
    except InferenceError as exc:
        image_row.status = "failed"
        batch.status = "failed"
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"code": "INFERENCE_UNAVAILABLE", "message": str(exc)},
        ) from exc

    detections: list[dict] = result["detections"]
    if not detections:
        image_row.status = "failed"
        batch.status = "failed"
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": "NOTHING_DETECTED",
                "message": "No onions detected in the image. Try a clearer photo.",
            },
        )

    # 5. Measurements -> counts -> URS -> grading (pure functions) -----------
    try:
        config = grading.load_config()
    except GradingError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "CONFIG_ERROR", "message": str(exc)},
        ) from exc

    detections = measurement.estimate_sizes(detections, config=config)
    counts = grading.aggregate_counts(detections, config=config)
    urs_pct = urs_service.compute_urs(counts, config=config)
    avg_confidence = sum(d["confidence"] for d in detections) / len(detections)
    verdict = grading.grade_batch(counts, urs_pct, avg_confidence, config=config)

    defect_pct = round(
        100.0 * (counts["total_onions"] - counts["healthy"]) / counts["total_onions"], 2
    )

    # 6. Persist detections + assessment --------------------------------------
    for det in detections:
        db.add(
            Detection(
                image_id=image_row.id,
                class_id=int(det["class_id"]),
                class_name=det["class_name"],
                confidence=float(det["confidence"]),
                bbox=det["bbox"],
                estimated_size_mm=det.get("estimated_size_mm"),
            )
        )
    image_row.status = "processed"

    from app.models.assessment import Assessment

    assessment = Assessment(
        batch_id=batch.id,
        image_id=image_row.id,
        total_onions=counts["total_onions"],
        healthy=counts["healthy"],
        damaged=counts["damaged"],
        rotten=counts["rotten"],
        sprouted=counts["sprouted"],
        undersized=counts["undersized"],
        defect_percentage=defect_pct,
        quality_score=verdict["quality_score"],
        grade=verdict["grade"],
        urs_percentage=urs_pct,
        avg_confidence=round(avg_confidence, 4),
        reasons=verdict["reasons"],
        is_demo=bool(result.get("is_demo", settings.demo_mode)),
        model_version=result.get("model_version", "unknown"),
    )
    db.add(assessment)
    batch.status = "analyzed"
    db.commit()
    db.refresh(assessment)
    db.refresh(batch)

    # 7. Contract response -----------------------------------------------------
    base = to_assessment_out(assessment).model_dump()
    return AnalyzeResponse(
        **base,
        image_id=image_row.id,
        detections=[DetectionOut(**d) for d in detections],
    )
