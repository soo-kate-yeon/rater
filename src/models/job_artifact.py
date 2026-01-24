"""
JobArtifact model for storing intermediate pipeline results.
"""
import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, UUIDMixin


class JobArtifact(Base, UUIDMixin):
    """
    JobArtifact model for storing intermediate pipeline results.

    Stores the raw output from each pipeline stage:
    - ASR (Whisper): transcript, segments, confidence scores
    - Feature extraction: delivery signals, language signals, structure analysis
    - LLM analysis: feedback, structure checklist, error categorization

    Attributes:
        id: UUID primary key
        job_id: Foreign key to jobs table
        asr_json: Whisper ASR results (transcript, segments, logprob, etc.)
        features_json: Extracted features (WPM, silence ratio, grammar errors, etc.)
        llm_json: LLM analysis output (feedback, structure, language analysis)
        rubric_version: Version of the scoring rubric (e.g., "toefl_speaking_2026_v1")
        pipeline_version: Version of the processing pipeline
        created_at: Artifact creation timestamp
    """

    __tablename__ = "job_artifacts"

    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("jobs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    asr_json: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        server_default="{}",
    )

    features_json: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        server_default="{}",
    )

    llm_json: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        server_default="{}",
    )

    rubric_version: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="toefl_speaking_2026_v1",
    )

    pipeline_version: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="1.0.0",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    # Relationships
    job: Mapped["Job"] = relationship(  # noqa: F821
        "Job",
        back_populates="artifacts",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return (
            f"JobArtifact(id={self.id!r}, job_id={self.job_id!r}, "
            f"rubric={self.rubric_version!r})"
        )
