"""Detection model — ONE onion instance found by the inference service.

Contract with ML (TEAM A): every detection has
    class_name, class_id, confidence, bbox = [x1, y1, x2, y2]

8-class system (NCCF 2026 aligned):
    0=onion 1=damaged 2=rotten 3=sprouted 4=cut_crack 5=smut 6=discoloured 7=fresh_roots

`estimated_size_mm` is filled by the measurement service (see services/measurement.py).
"""

from datetime import datetime

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.models.user import utcnow


class Detection(Base):
    __tablename__ = "detections"

    id: Mapped[int] = mapped_column(primary_key=True)
    image_id: Mapped[int] = mapped_column(
        ForeignKey("images.id", ondelete="CASCADE"), index=True, nullable=False
    )

    # Canonical classes: 0=onion 1=damaged 2=rotten 3=sprouted (ml/config.py)
    class_id: Mapped[int] = mapped_column(Integer, nullable=False)
    class_name: Mapped[str] = mapped_column(String(32), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    bbox: Mapped[list] = mapped_column(JSON, nullable=False)  # [x1, y1, x2, y2]

    # Filled by the size-estimation step; None when not yet estimated.
    estimated_size_mm: Mapped[float | None] = mapped_column(Float, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    image: Mapped["Image"] = relationship(back_populates="detections")  # noqa: F821
