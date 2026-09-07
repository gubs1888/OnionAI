"""Image model — one uploaded photo belonging to a batch."""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.models.user import utcnow


class Image(Base):
    __tablename__ = "images"

    id: Mapped[int] = mapped_column(primary_key=True)
    batch_id: Mapped[int] = mapped_column(
        ForeignKey("batches.id", ondelete="CASCADE"), index=True, nullable=False
    )
    # Path of the stored file (relative to the backend root).
    file_path: Mapped[str] = mapped_column(String(512), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(256), nullable=False)
    # uploaded | processing | processed | failed
    status: Mapped[str] = mapped_column(String(16), default="uploaded", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    batch: Mapped["Batch"] = relationship(back_populates="images")  # noqa: F821
    detections: Mapped[list["Detection"]] = relationship(  # noqa: F821
        back_populates="image", cascade="all, delete-orphan"
    )
