"""
Task model for TOEFL Speaking questions.

NOTE: 이 모델은 하위 호환성을 위해 유지됩니다.
새로운 문제는 Item 모델을 사용하세요. Task는 Item으로 마이그레이션 예정입니다.
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, Enum, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import GUID, Base, UUIDMixin


class TaskType(str, enum.Enum):
    """
    Enum for TOEFL Speaking task types.
    """

    INDEPENDENT = "INDEPENDENT"  # Tasks 1-2: Personal preference/opinion
    INTEGRATED = "INTEGRATED"  # Tasks 3-4: Reading + Listening integration


class Task(Base, UUIDMixin):
    """
    Task model representing TOEFL Speaking questions.

    NOTE: Deprecated - 새로운 문제는 Item 모델을 사용하세요.

    Attributes:
        id: UUID primary key
        task_type: Type of task (independent or integrated)
        prompt: The question text presented to the user
        source_reading: Optional reading passage for integrated tasks
        source_listening: Optional listening transcript for integrated tasks
        tags: JSONB field for categorization (e.g., topic, difficulty)
        created_at: Task creation timestamp
        item_id: Optional FK to Item model (for migration)
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
        JSON,
        nullable=False,
        server_default="{}",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    # Item 참조 (마이그레이션용)
    item_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID,
        ForeignKey("items.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="연결된 Item UUID (마이그레이션용)",
    )

    # Relationships
    jobs: Mapped[list[Job]] = relationship(  # noqa: F821
        "Job",
        back_populates="task",
        lazy="selectin",
    )

    item: Mapped[Item | None] = relationship(  # noqa: F821
        "Item",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"Task(id={self.id!r}, task_type={self.task_type.value!r})"
