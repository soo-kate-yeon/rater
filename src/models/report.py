"""
Report model for storing final user-facing feedback and scores.
"""

import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import GUID, Base, UUIDMixin


class Report(Base, UUIDMixin):
    """
    Report model for storing final user-facing feedback and scores.

    Contains the complete feedback report presented to the user:
    - Summary diagnosis (3 lines)
    - Delivery analysis (speed, pauses, clarity)
    - Language use analysis (errors, vocabulary, complexity)
    - Structure visualization (checklist of elements)
    - Score range with rationale
    - Actionable improvement items

    Attributes:
        id: UUID primary key
        job_id: Foreign key to jobs table (one-to-one relationship)
        report_json: Complete feedback report in JSON format
        score_band_min: Minimum estimated score (e.g., 22)
        score_band_max: Maximum estimated score (e.g., 25)
        created_at: Report generation timestamp
    """

    __tablename__ = "reports"

    job_id: Mapped[uuid.UUID] = mapped_column(
        GUID,
        ForeignKey("jobs.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    report_json: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        server_default="{}",
    )

    score_band_min: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    score_band_max: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    # Relationships
    job: Mapped["Job"] = relationship(  # noqa: F821
        "Job",
        back_populates="report",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return (
            f"Report(id={self.id!r}, job_id={self.job_id!r}, "
            f"score_range={self.score_band_min}-{self.score_band_max})"
        )
