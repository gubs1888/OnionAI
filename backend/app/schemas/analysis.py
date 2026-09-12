"""
Analysis schemas — THE core Backend <-> Mobile contract.

POST-NCCF ARCHITECTURE:
    Response now includes BOTH:
    1. NCCF fields (grade_a_count, grade_urs_count, nccf_grade, etc.)
    2. Legacy fields (grade A/B/C/D, quality_score, urs_percentage) for compat.

    Mobile should transition to using nccf_grade and the per-onion breakdown.
    Legacy fields are deprecated but will remain populated.

Example assessment payload (new fields marked with *):

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
        "created_at": "2026-09-07T10:00:00+00:00",
        *"grade_a_count": 32,
        *"grade_urs_count": 7,
        *"non_qualifying_count": 9,
        *"specification_id": "NCCF_PAACS_2026",
        *"nccf_grade": "GRADE_A",
        *"defect_breakdown": {"smut": 3, "sprouted": 1, ...},
        *"manual_flags": ["ruptured_skin", "open_neck", ...],
        *"onion_grades": [{"onion_id": 1, "grade": "GRADE_A", ...}, ...]
    }
"""

from datetime import datetime

from pydantic import BaseModel, Field

from app.models.assessment import Assessment


ALL_CLASS_NAMES = (
    "onion", "damaged", "rotten", "sprouted",
    "cut_crack", "smut", "discoloured", "fresh_roots",
)


class DetectionOut(BaseModel):
    """One detected onion instance (ML -> Backend -> Mobile contract)."""

    id: int | None = Field(default=None, description="Detection ID from database")
    class_name: str = Field(
        examples=list(ALL_CLASS_NAMES),
    )
    class_id: int = Field(
        ge=0, le=7,
        description="0=onion 1=damaged 2=rotten 3=sprouted 4=cut_crack 5=smut 6=discoloured 7=fresh_roots",
    )
    confidence: float = Field(ge=0.0, le=1.0)
    bbox: list[float] = Field(description="[x1, y1, x2, y2] in pixels")
    diameter_px: float | None = Field(default=None, description="Raw physical diameter in pixels")
    estimated_size_mm: float | None = Field(
        default=None, description="Estimated bulb diameter in mm (demo estimator for now)"
    )


class AssessmentOut(BaseModel):
    """Aggregated quality verdict — Backend -> Mobile contract."""

    assessment_id: int
    batch_id: str = Field(description="Batch code, e.g. ON-0001")

    # --- Legacy counts (backward compat) ---
    total_onions: int
    healthy: int
    damaged: int
    rotten: int
    sprouted: int
    undersized: int

    # --- Legacy metrics (backward compat — deprecated, use NCCF fields) ---
    defect_percentage: float
    quality_score: float = Field(description="0..100, OUR MVP scoring — not an official grade")
    grade: str = Field(description="A/B/C/D per OUR MVP thresholds (DEPRECATED — use nccf_grade)")
    urs_percentage: float = Field(description="Legacy URS — DEPRECATED, use grade_urs_count/total")
    confidence: float = Field(description="Average detection confidence in percent (0..100)")

    reasons: list[str] = Field(default_factory=list)

    # --- NCCF Rule Engine results (primary) ---
    grade_a_count: int = Field(default=0, description="Onions meeting NCCF Grade-A")
    grade_urs_count: int = Field(default=0, description="Onions meeting NCCF Grade-URS")
    non_qualifying_count: int = Field(default=0, description="Onions failing both grades")
    specification_id: str = Field(
        default="NCCF_PAACS_2026",
        description="Which NCCF specification was applied",
    )
    nccf_grade: str = Field(
        default="NON_QUALIFYING",
        description="Batch-level NCCF grade: GRADE_A / GRADE_URS / NON_QUALIFYING",
    )
    defect_breakdown: dict[str, int] = Field(
        default_factory=dict,
        description="Per-defect type counts: {defect_name: count}",
    )
    manual_flags: list[str] = Field(
        default_factory=list,
        description="NCCF features requiring manual inspection (no training data)",
    )
    onion_grades: list[dict] = Field(
        default_factory=list,
        description="Per-onion grade details: [{onion_id, grade, reasons, defects, ...}]",
    )

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
        # NCCF fields
        grade_a_count=assessment.grade_a_count,
        grade_urs_count=assessment.grade_urs_count,
        non_qualifying_count=assessment.non_qualifying_count,
        specification_id=assessment.specification_id,
        nccf_grade=assessment.nccf_grade,
        defect_breakdown=dict(assessment.defect_breakdown or {}),
        manual_flags=list(assessment.manual_flags or []),
        onion_grades=list(assessment.onion_grades or []),
        # Transparency
        is_demo=assessment.is_demo,
        model_version=assessment.model_version,
        created_at=assessment.created_at,
    )
