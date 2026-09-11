"""Assessment model — the aggregated quality verdict for one batch analysis run.

POST-NCCF ARCHITECTURE:
    This model now contains BOTH:
    1. NCCF rule engine results (grade_a_count, grade_urs_count, etc.)
    2. Legacy MVP metrics (quality_score, grade A/B/C/D) for backward compat.

    The NCCF fields are the source of truth for government-spec reporting.
    Legacy fields are preserved so old mobile clients don't break.
"""

from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.models.user import utcnow


class Assessment(Base):
    __tablename__ = "assessments"

    id: Mapped[int] = mapped_column(primary_key=True)
    batch_id: Mapped[int] = mapped_column(
        ForeignKey("batches.id", ondelete="CASCADE"), index=True, nullable=False
    )
    # Image the assessment was computed from (nullable for future multi-image runs).
    image_id: Mapped[int | None] = mapped_column(
        ForeignKey("images.id", ondelete="SET NULL"), nullable=True
    )

    # --- NCCF Rule Engine results (primary, post-NCCF) ---
    grade_a_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    grade_urs_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    non_qualifying_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    specification_id: Mapped[str] = mapped_column(
        String(64), nullable=False, default="NCCF_PAACS_2026"
    )
    nccf_grade: Mapped[str] = mapped_column(
        String(32), nullable=False, default="NON_QUALIFYING"
    )
    # Per-onion grade details (JSON array of {onion_id, grade, reasons, defects})
    onion_grades: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    # Features requiring manual inspection (JSON array of strings)
    manual_flags: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    # Per-defect counts (JSON dict of {defect_name: count})
    defect_breakdown: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    # --- Legacy counts (backward compat — sum to total_onions) ---
    total_onions: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    healthy: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    damaged: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    rotten: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    sprouted: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    undersized: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # --- Legacy metrics (backward compat) ---
    defect_percentage: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    quality_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    grade: Mapped[str] = mapped_column(String(2), nullable=False, default="D")
    urs_percentage: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    avg_confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)  # 0..1

    reasons: Mapped[list] = mapped_column(JSON, nullable=False, default=list)

    # --- Provenance / transparency ---
    # TRUE -> results are synthetic DEMO DATA, never real model output.
    is_demo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    model_version: Mapped[str] = mapped_column(String(64), nullable=False, default="demo-v0")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    batch: Mapped["Batch"] = relationship(back_populates="assessments")  # noqa: F821
    reports: Mapped[list["Report"]] = relationship(  # noqa: F821
        back_populates="assessment", cascade="all, delete-orphan"
    )
