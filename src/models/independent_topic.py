"""
IndependentTopic 모델 - Independent Speaking 토픽 뱅크.

Independent 문제에 사용할 수 있는 토픽 목록을 관리합니다.
각 토픽은 번호와 프롬프트, 출처로 구성됩니다.
"""

from __future__ import annotations

from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import BaseModel


class IndependentTopic(BaseModel):
    """
    Independent Speaking 토픽 모델.

    Attributes:
        id: UUID 기본 키 (BaseModel에서 상속)
        number: 토픽 번호
        prompt: 토픽 프롬프트 (질문)
        source: 출처 (예: "Independent_Topics.pdf")
        created_at: 생성 시각 (BaseModel에서 상속)
        updated_at: 수정 시각 (BaseModel에서 상속)
    """

    __tablename__ = "independent_topics"

    number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        unique=True,
        index=True,
        comment="토픽 번호",
    )

    prompt: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="토픽 프롬프트 (질문)",
    )

    source: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        comment="출처 (예: Independent_Topics.pdf)",
    )

    def __repr__(self) -> str:
        return f"IndependentTopic(id={self.id!r}, number={self.number}, source={self.source!r})"
