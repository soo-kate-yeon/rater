"""
Set 모델 - TOEFL Speaking 문제 세트.

문제 세트(Set)는 여러 개별 문항(Item)을 그룹화하여 관리합니다.
하나의 세트는 출처(source)와 버전(version)으로 식별됩니다.
"""
from __future__ import annotations

from typing import Optional

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel


class Set(BaseModel):
    """
    문제 세트 모델.

    Attributes:
        id: UUID 기본 키 (BaseModel에서 상속)
        title: 세트 제목 (예: "ETS Practice Set 1")
        source: 출처 (예: "ETS Official", "Kaplan", "Custom")
        version: 버전 (예: "v1.0", "v2.2")
        description: 세트 설명 (선택)
        created_at: 생성 시각 (BaseModel에서 상속)
        updated_at: 수정 시각 (BaseModel에서 상속)
        items: 세트에 포함된 Item 목록
    """

    __tablename__ = "sets"

    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="세트 제목",
    )

    source: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        comment="출처 (예: ETS Official, Kaplan)",
    )

    version: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
        comment="버전 (예: v1.0)",
    )

    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="세트 설명",
    )

    # Relationships
    items: Mapped[list[Item]] = relationship(  # noqa: F821
        "Item",
        back_populates="set",
        lazy="selectin",
        cascade="all, delete-orphan",
        order_by="Item.task_no",
    )

    def __repr__(self) -> str:
        return f"Set(id={self.id!r}, title={self.title!r}, source={self.source!r}, version={self.version!r})"
