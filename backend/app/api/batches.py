"""Batch endpoints: create / list / get.

Contract: batch_code (e.g. "ON-0001") is the public identifier used by the
mobile app; numeric ids stay internal.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_current_user_optional, get_db, require_batch
from app.models.assessment import Assessment
from app.models.batch import Batch
from app.models.user import User
from app.schemas.analysis import AssessmentOut, to_assessment_out
from app.schemas.batch import BatchCreate, BatchOut, BatchUpdate

router = APIRouter(prefix="/batches", tags=["batches"])


def _next_batch_code(db: Session) -> str:
    """Generate the next sequential code ON-0001, ON-0002, ..."""
    count = db.query(func.count(Batch.id)).scalar() or 0
    return f"ON-{count + 1:04d}"


@router.post(
    "",
    response_model=BatchOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new batch",
    description="Creates a batch (a lot of onions) and returns it with its generated batch_code.",
    responses={422: {"description": "Validation error"}},
)
def create_batch(
    payload: BatchCreate,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
) -> BatchOut:
    batch = Batch(
        batch_code=_next_batch_code(db),
        name=payload.name,
        variety=payload.variety,
        source=payload.source,
        notes=payload.notes,
        status="created",
        created_by=current_user.id if current_user else None,
    )
    db.add(batch)
    db.commit()
    db.refresh(batch)
    return BatchOut.model_validate(batch)


@router.get(
    "",
    response_model=list[BatchOut],
    summary="List batches (newest first)",
    description="Returns all batches. Optional `status` filter: created|analyzing|analyzed|failed.",
)
def list_batches(
    status_filter: str | None = Query(default=None, alias="status", pattern="^(created|analyzing|analyzed|failed)$"),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
) -> list[BatchOut]:
    query = db.query(Batch).order_by(Batch.created_at.desc())
    if status_filter:
        query = query.filter(Batch.status == status_filter)
    return [BatchOut.model_validate(b) for b in query.limit(limit).all()]


@router.get(
    "/{batch_id}",
    response_model=BatchOut,
    summary="Get one batch",
    description="Accepts the numeric id or the batch code, e.g. `/api/batches/1` or `/api/batches/ON-0001`.",
    responses={404: {"description": "Batch not found"}},
)
def get_batch(batch_id: str, db: Session = Depends(get_db)) -> BatchOut:
    batch = require_batch(db, batch_id)
    return BatchOut.model_validate(batch)


@router.get(
    "/{batch_id}/assessment",
    response_model=AssessmentOut,
    summary="Get the latest assessment for a batch",
    description=(
        "Returns the most recent quality assessment for the batch (the "
        "Backend -> Mobile contract payload). 404 when the batch has not "
        "been analyzed yet."
    ),
    responses={404: {"description": "Batch or assessment not found"}},
)
def get_batch_assessment(batch_id: str, db: Session = Depends(get_db)) -> AssessmentOut:
    batch = require_batch(db, batch_id)
    assessment = (
        db.query(Assessment)
        .filter(Assessment.batch_id == batch.id)
        .order_by(Assessment.created_at.desc(), Assessment.id.desc())
        .first()
    )
    if assessment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "ASSESSMENT_NOT_FOUND",
                "message": f"Batch '{batch.batch_code}' has no assessment yet. POST /api/analyze first.",
            },
        )
    return to_assessment_out(assessment)


@router.patch(
    "/{batch_id}",
    response_model=BatchOut,
    summary="Update a batch (rename/close/notes)",
    description="Updates one or more fields of a batch (name, variety, source, notes, status).",
    responses={404: {"description": "Batch not found"}},
)
def update_batch(
    batch_id: str,
    payload: BatchUpdate,
    db: Session = Depends(get_db),
) -> BatchOut:
    batch = require_batch(db, batch_id)
    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(batch, field, value)
    db.commit()
    db.refresh(batch)
    return BatchOut.model_validate(batch)


@router.delete(
    "",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Clear all batches",
    description="Deletes all batches from the database.",
)
def clear_all_batches(db: Session = Depends(get_db)):
    db.query(Batch).delete()
    db.commit()
    return None
