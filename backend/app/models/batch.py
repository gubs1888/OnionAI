"""Batch model — a lot of onions submitted for quality assessment."""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.models.user import utcnow


class Batch(Base):
    __tablename__ = "batches"

    id: Mapped[int] = mapped_column(primary_key=True)
    # Human-friendly code shown to users, e.g. "ON-0001" (contract field).
    batch_code: Mapped[str] = mapped_column(String(16), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    variety: Mapped[str | None] = mapped_column(String(64), nullable=True)
    source: Mapped[str | None] = mapped_column(String(120), nullable=True)   # farm / mandi
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    # created | analyzing | analyzed | failed   (simple state, no workflow engine)
    status: Mapped[str] = mapped_column(String(16), default="created", nullable=False)

    created_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    creator: Mapped["User | None"] = relationship(back_populates="batches")  # noqa: F821
    images: Mapped[list["Image"]] = relationship(  # noqa: F821
        back_populates="batch", cascade="all, delete-orphan"
    )
    assessments: Mapped[list["Assessment"]] = relationship(  # noqa: F821
        back_populates="batch", cascade="all, delete-orphan"
    )

    @property
    def image_count(self) -> int:
        return len(self.images)
