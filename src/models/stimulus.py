"""
Stimulus 모델 - 자극자료.

Stimulus는 Item에 제공되는 자료(읽기 지문, 음성, 이미지, 지시문)를 나타냅니다.
하나의 Item은 여러 개의 Stimulus를 가질 수 있으며, display_order로 표시 순서를 결정합니다.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, UUIDMixin
from .enums import StimulusKind


class Stimulus(Base, UUIDMixin):
    """
    자극자료 모델.

    Attributes:
        id: UUID 기본 키 (UUIDMixin에서 상속)
        item_id: 소속 Item의 UUID
        kind: 자료 유형 (reading, audio, image, direction)
        title: 자료 제목 (선택)
        content_text: 텍스트 내용 (reading, direction 용)
        asset_url: 미디어 URL (audio, image 용)
        duration_seconds: 음성 길이 (audio 용)
        display_order: 표시 순서
        notes_allowed: 노트 필기 허용 여부
        created_at: 생성 시각
    """

    __tablename__ = "stimuli"

    item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("items.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="소속 Item UUID",
    )

    kind: Mapped[StimulusKind] = mapped_column(
        Enum(StimulusKind, name="stimulus_kind_enum"),
        nullable=False,
        index=True,
        comment="자료 유형 (reading/audio/image/direction)",
    )

    title: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
        comment="자료 제목",
    )

    content_text: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="텍스트 내용 (reading, direction 용)",
    )

    asset_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="미디어 URL (audio, image 용)",
    )

    duration_seconds: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="음성 길이 (초, audio 전용)",
    )

    display_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="표시 순서",
    )

    notes_allowed: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="노트 필기 허용 여부",
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
        back_populates="stimuli",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"Stimulus(id={self.id!r}, kind={self.kind.value!r}, order={self.display_order})"
