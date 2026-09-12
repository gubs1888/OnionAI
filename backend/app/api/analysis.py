"""
POST /api/analyze — upload an image, run the ML gateway, aggregate, grade, persist.

Orchestration ONLY: every hard problem lives in a service module.
  inference.py         -> detections          (TEAM A swap point)
  measurement.py       -> sizes
  nccf_rule_engine.py  -> per-onion grading (NCCF specs)
  grading.py           -> legacy counts + score + grade + reasons
  urs.py               -> URS %

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

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
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
        "Runs: save image -> inference service -> size estimation -> "
        "NCCF rule engine -> grading -> persist (image, detections, assessment). "
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
    distance_cm: float | None = Form(default=None, description="Camera distance in cm"),
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
) -> AnalyzeResponse:
    # 1. Validate upload -----------------------------------------------------
    original_name = image.filename or "upload.jpg"
    ext = Path(original_name).suffix.lower()
    print("ext", ext)
    if not ext or ext == ".":
        ext = ".jpg"
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

    # Auto-decode base64 / data URL text payload if sent by mobile/web client
    try:
        import base64
        with stored_path.open("rb") as f:
            header = f.read(256)
        if (
            header.startswith(b"data:image/")
            or b"base64," in header
            or (
                not header.startswith(b"\xff\xd8")
                and not header.startswith(b"\x89PNG")
                and not header.startswith(b"RIFF")
                and not header.startswith(b"GIF")
            )
        ):
            raw_text = stored_path.read_text(encoding="utf-8", errors="ignore").strip()
            if "base64," in raw_text:
                raw_text = raw_text.split("base64,")[1]
            try:
                decoded_bytes = base64.b64decode(raw_text)
                if len(decoded_bytes) > 0:
                    stored_path.write_bytes(decoded_bytes)
            except Exception:
                pass
    except Exception:
        pass

    # Store the path relative to the backend root when possible (nice for
    # logs/portability); fall back to the absolute path for external dirs.
    try:
        stored_ref = str(stored_path.relative_to(BACKEND_ROOT))
    except ValueError:
        stored_ref = str(stored_path)

    image_row = Image(
        batch_id=batch.id,
        file_path=stored_ref,
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

    # 5. Measurements -> NCCF rule engine -> legacy grading -------------------
    try:
        config = grading.load_config()
    except GradingError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "CONFIG_ERROR", "message": str(exc)},
        ) from exc

    image_width = result.get("image_width", 0)
    detections = measurement.estimate_sizes(
        detections, 
        config=config, 
        distance_cm=distance_cm, 
        image_width=image_width,
        image_path=str(stored_path)
    )

    # --- NCCF Rule Engine (primary grading path) ---
    nccf_result = grading.grade_batch_nccf(detections, config=config)

    # --- Legacy scoring (backward compat) ---
    counts = grading.aggregate_counts(detections, config=config)
    urs_pct_legacy = urs_service.compute_urs(counts, config=config)
    avg_confidence = sum(d["confidence"] for d in detections) / len(detections)
    verdict = grading.grade_batch(counts, urs_pct_legacy, avg_confidence, config=config)

    # URS% from NCCF (the correct value)
    urs_pct_nccf = urs_service.compute_urs_from_nccf(nccf_result)

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
                diameter_px=det.get("diameter_px"),
                estimated_size_mm=det.get("estimated_size_mm"),
            )
        )
    image_row.status = "processed"

    from app.models.assessment import Assessment

    assessment = Assessment(
        batch_id=batch.id,
        image_id=image_row.id,
        # --- NCCF results ---
        grade_a_count=nccf_result.grade_a_count,
        grade_urs_count=nccf_result.grade_urs_count,
        non_qualifying_count=nccf_result.non_qualifying_count,
        specification_id=nccf_result.specification_id,
        nccf_grade=nccf_result.batch_grade,
        onion_grades=nccf_result.per_onion_grades,
        manual_flags=nccf_result.manual_flags,
        defect_breakdown=nccf_result.defect_breakdown,
        # --- Legacy fields ---
        total_onions=counts["total_onions"],
        healthy=counts["healthy"],
        damaged=counts["damaged"],
        rotten=counts["rotten"],
        sprouted=counts["sprouted"],
        undersized=counts["undersized"],
        defect_percentage=defect_pct,
        quality_score=verdict["quality_score"],
        grade=verdict["grade"],
        urs_percentage=urs_pct_nccf,  # use NCCF-derived URS% even in legacy field
        avg_confidence=round(avg_confidence, 4),
        reasons=nccf_result.reasons,  # use NCCF reasons as primary
        # --- Provenance ---
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
