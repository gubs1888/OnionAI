"""
Analysis schemas — THE core Backend <-> Mobile contract.

The field names below are STABLE. Mobile (TEAM C) and report generation depend
on them. Any change must be agreed with all teams first (contract-first rule).

Example assessment payload:

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
        "reasons": [],
        "is_demo": true,
        "model_version": "demo-v0",
        "created_at": "2026-09-07T10:00:00+00:00"
    }
"""

from datetime import datetime

from pydantic import BaseModel, Field

from app.models.assessment import Assessment


class DetectionOut(BaseModel):
    """One detected onion instance (ML -> Backend -> Mobile contract)."""

    class_name: str = Field(examples=["onion", "damaged", "rotten", "sprouted"])
    class_id: int = Field(ge=0, le=3, description="0=onion 1=damaged 2=rotten 3=sprouted")
    confidence: float = Field(ge=0.0, le=1.0)
    bbox: list[float] = Field(description="[x1, y1, x2, y2] in pixels")
    estimated_size_mm: float | None = Field(
        default=None, description="Estimated bulb diameter in mm (demo estimator for now)"
    )


class AssessmentOut(BaseModel):
    """Aggregated quality verdict — exactly the Backend -> Mobile contract."""

    assessment_id: int
    batch_id: str = Field(description="Batch code, e.g. ON-0001")

    total_onions: int
    healthy: int
    damaged: int
    rotten: int
    sprouted: int
    undersized: int

    defect_percentage: float
    quality_score: float = Field(description="0..100, OUR MVP scoring — not an official grade")
    grade: str = Field(description="A/B/C/D per OUR MVP thresholds (config-driven)")
    urs_percentage: float = Field(description="URS — CONFIGURABLE definition, MUST be verified")
    confidence: float = Field(description="Average detection confidence in percent (0..100)")

    reasons: list[str] = Field(default_factory=list)

    # Transparency flags — the app MUST surface these to the user.
    is_demo: bool = Field(description="True => synthetic DEMO DATA, not real AI output")
    model_version: str

    created_at: datetime


class AnalyzeResponse(AssessmentOut):
    """Response of POST /api/analyze = AssessmentOut + detections detail."""

    image_id: int
    detections: list[DetectionOut] = Field(default_factory=list)


def to_assessment_out(assessment: Assessment) -> AssessmentOut:
    """Explicit ORM -> contract mapping.

    NOTE: `batch_id` in the contract is the human-readable batch CODE (string),
    while the ORM column is an integer FK — hence the explicit mapping.
    """
    return AssessmentOut(
        assessment_id=assessment.id,
        batch_id=assessment.batch.batch_code,
        total_onions=assessment.total_onions,
        healthy=assessment.healthy,
        damaged=assessment.damaged,
        rotten=assessment.rotten,
        sprouted=assessment.sprouted,
        undersized=assessment.undersized,
        defect_percentage=round(assessment.defect_percentage, 2),
        quality_score=round(assessment.quality_score, 1),
        grade=assessment.grade,
        urs_percentage=round(assessment.urs_percentage, 1),
        confidence=round(assessment.avg_confidence * 100, 1),
        reasons=list(assessment.reasons or []),
        is_demo=assessment.is_demo,
        model_version=assessment.model_version,
        created_at=assessment.created_at,
    )
