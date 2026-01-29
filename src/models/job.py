"""
Job model for tracking scoring pipeline execution.
"""

from __future__ import annotations

import enum
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import GUID, BaseModel

if TYPE_CHECKING:
    from .report import Report


class JobStatus(enum.Enum):
    """
    Enum for job execution status in the scoring pipeline.

    Pipeline flow:
    QUEUED → FETCHING_AUDIO → ASR_RUNNING → FEATURE_EXTRACTING
    → LLM_ANALYZING → SCORING → DONE

    On failure: → FAILED
    """

    QUEUED = "QUEUED"
    FETCHING_AUDIO = "FETCHING_AUDIO"
    ASR_RUNNING = "ASR_RUNNING"
    FEATURE_EXTRACTING = "FEATURE_EXTRACTING"
    LLM_ANALYZING = "LLM_ANALYZING"
    SCORING = "SCORING"
    DONE = "DONE"
    FAILED = "FAILED"


class Job(BaseModel):
    """
    Job model for tracking async scoring pipeline execution.

    Attributes:
        id: UUID primary key (inherited)
        user_id: Foreign key to users table
        task_id: Foreign key to tasks table
        status: Current pipeline status
        progress: Progress percentage (0-100)
        audio_key: Storage key/path for the audio file
        error_code: Error code if job failed (optional)
        error_message: Detailed error message if job failed (optional)
        created_at: Job creation timestamp (inherited)
        updated_at: Last update timestamp (inherited)
    """

    __tablename__ = "jobs"

    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    task_id: Mapped[uuid.UUID] = mapped_column(
        GUID,
        ForeignKey("tasks.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    status: Mapped[JobStatus] = mapped_column(
        Enum(JobStatus, name="job_status_enum"),
        nullable=False,
        default=JobStatus.QUEUED,
        index=True,
    )

    progress: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    audio_key: Mapped[str] = mapped_column(
        String(512),
        nullable=False,
    )

    error_code: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # Relationships
    user: Mapped[User] = relationship(  # noqa: F821
        "User",
        back_populates="jobs",
        lazy="selectin",
    )

    task: Mapped[Task] = relationship(  # noqa: F821
        "Task",
        back_populates="jobs",
        lazy="selectin",
    )

    artifacts: Mapped[list[JobArtifact]] = relationship(  # noqa: F821
        "JobArtifact",
        back_populates="job",
        lazy="selectin",
        cascade="all, delete-orphan",
    )

    report: Mapped[Report | None] = relationship(  # noqa: F821
        "Report",
        back_populates="job",
        lazy="selectin",
        cascade="all, delete-orphan",
        passive_deletes=True,
        uselist=False,
    )

    def __repr__(self) -> str:
        return f"Job(id={self.id!r}, status={self.status.value!r}, progress={self.progress}%)"
