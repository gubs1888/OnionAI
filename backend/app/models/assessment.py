"""Assessment model — the aggregated quality verdict for one batch analysis run.

This is the object serialized in the Backend -> Mobile contract
(see docs/api/API_CONTRACT.md). Values here are OUR MVP metrics — they are
NOT official grades until TEAM D verifies thresholds (docs/standards/).
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

    # --- Counts (mutually exclusive buckets; they sum to total_onions) ---
    total_onions: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    healthy: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    damaged: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    rotten: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    sprouted: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    undersized: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # --- Metrics ---
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
