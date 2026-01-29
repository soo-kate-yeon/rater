"""
AnswerKey 모델 - 모범답안 및 채점 기준.

AnswerKey는 Item에 대한 모범답안, 스크립트, 개요, 포인트, 또는 Blueprint를 저장합니다.
여러 수준(high, mid, low)의 모범답안을 지원합니다.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, Enum, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import GUID, Base, UUIDMixin
from .enums import AnswerKeyLevel, AnswerKeyType


class AnswerKey(Base, UUIDMixin):
    """
    모범답안 모델.

    Attributes:
        id: UUID 기본 키 (UUIDMixin에서 상속)
        item_id: 소속 Item의 UUID
        answer_type: 모범답안 유형 (sample_response, transcript, outline, points, blueprint)
        level: 품질 수준 (high, mid, low) - 선택
        content: 모범답안 내용 또는 Blueprint JSON (JSONB)
        source: 출처 (예: "ETS Official", "Expert Review")
        created_at: 생성 시각
    """

    __tablename__ = "answer_keys"

    item_id: Mapped[uuid.UUID] = mapped_column(
        GUID,
        ForeignKey("items.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="소속 Item UUID",
    )

    answer_type: Mapped[AnswerKeyType] = mapped_column(
        Enum(AnswerKeyType, name="answer_key_type_enum"),
        nullable=False,
        index=True,
        comment="모범답안 유형",
    )

    level: Mapped[AnswerKeyLevel | None] = mapped_column(
        Enum(AnswerKeyLevel, name="answer_key_level_enum"),
        nullable=True,
        index=True,
        comment="품질 수준 (high/mid/low)",
    )

    content: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        comment="모범답안 내용 또는 Blueprint JSON",
    )

    source: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="출처 (예: ETS Official)",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="생성 시각",
    )

    # Relationships
    item: Mapped[Item] = relationship(  # noqa: F821
        "Item",
        back_populates="answer_keys",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"AnswerKey(id={self.id!r}, type={self.answer_type.value!r}, level={self.level.value if self.level else None!r})"
