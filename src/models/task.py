"""
Task model for TOEFL Speaking questions.
"""
import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, UUIDMixin


class TaskType(str, enum.Enum):
    """
    Enum for TOEFL Speaking task types.
    """

    INDEPENDENT = "INDEPENDENT"  # Tasks 1-2: Personal preference/opinion
    INTEGRATED = "INTEGRATED"  # Tasks 3-4: Reading + Listening integration


class Task(Base, UUIDMixin):
    """
    Task model representing TOEFL Speaking questions.

    Attributes:
        id: UUID primary key
        task_type: Type of task (independent or integrated)
        prompt: The question text presented to the user
        source_reading: Optional reading passage for integrated tasks
        source_listening: Optional listening transcript for integrated tasks
        tags: JSONB field for categorization (e.g., topic, difficulty)
        created_at: Task creation timestamp
    """

    __tablename__ = "tasks"

    task_type: Mapped[TaskType] = mapped_column(
        Enum(TaskType, name="task_type_enum"),
        nullable=False,
        index=True,
    )

    prompt: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    source_reading: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    source_listening: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    tags: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        server_default="{}",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    # Relationships
    jobs: Mapped[list["Job"]] = relationship(  # noqa: F821
        "Job",
        back_populates="task",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"Task(id={self.id!r}, task_type={self.task_type.value!r})"
