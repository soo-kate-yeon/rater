"""
Item 모델 - TOEFL Speaking 개별 문항.

Item은 Set에 속하는 개별 문제를 나타냅니다.
Independent와 Integrated 두 가지 유형이 있으며, 각 유형별로 필수 필드가 다릅니다.
"""
import uuid

from sqlalchemy import Enum, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel
from .enums import Difficulty, TopicCategory, TopicType
from .task import TaskType


class Item(BaseModel):
    """
    개별 문항 모델.

    Attributes:
        id: UUID 기본 키 (BaseModel에서 상속)
        set_id: 소속 Set의 UUID
        task_no: Set 내 문항 번호 (1, 2, 3, 4)
        task_type: 문항 유형 (INDEPENDENT 또는 INTEGRATED)
        prompt: 문제 지시문
        prep_seconds: 준비 시간 (초)
        response_seconds: 응답 시간 (초)

        # Independent 전용 필드
        topic_type: 주제 유형 (preference, agree_disagree 등)
        topic_category: 주제 카테고리 (education, technology 등)
        question_pattern: 질문 패턴 (예: "Do you agree or disagree...")

        # 공통 필드
        tags: 태그 (JSONB)
        difficulty: 난이도 (easy, medium, hard)
        scoring_focus: 채점 가중치 (JSONB)

        created_at: 생성 시각 (BaseModel에서 상속)
        updated_at: 수정 시각 (BaseModel에서 상속)
    """

    __tablename__ = "items"
    __table_args__ = (
        # Set 내에서 task_no는 유일해야 함
        UniqueConstraint("set_id", "task_no", name="uq_items_set_task_no"),
    )

    set_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="소속 Set UUID",
    )

    task_no: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Set 내 문항 번호 (1-4)",
    )

    task_type: Mapped[TaskType] = mapped_column(
        Enum(TaskType, name="task_type_enum", create_type=False),
        nullable=False,
        index=True,
        comment="문항 유형 (INDEPENDENT/INTEGRATED)",
    )

    prompt: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="문제 지시문",
    )

    prep_seconds: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=15,
        comment="준비 시간 (초)",
    )

    response_seconds: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=45,
        comment="응답 시간 (초)",
    )

    # Independent 전용 필드
    topic_type: Mapped[TopicType | None] = mapped_column(
        Enum(TopicType, name="topic_type_enum"),
        nullable=True,
        index=True,
        comment="주제 유형 (Independent 전용)",
    )

    topic_category: Mapped[TopicCategory | None] = mapped_column(
        Enum(TopicCategory, name="topic_category_enum"),
        nullable=True,
        index=True,
        comment="주제 카테고리 (Independent 전용)",
    )

    question_pattern: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
        comment="질문 패턴 (예: Do you agree or disagree...)",
    )

    # 공통 필드
    tags: Mapped[list] = mapped_column(
        JSONB,
        nullable=False,
        server_default="[]",
        comment="태그 목록",
    )

    difficulty: Mapped[Difficulty | None] = mapped_column(
        Enum(Difficulty, name="difficulty_enum"),
        nullable=True,
        index=True,
        comment="난이도 (easy/medium/hard)",
    )

    scoring_focus: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        server_default="{}",
        comment="채점 가중치 (예: {structure: 0.3, language: 0.4, delivery: 0.3})",
    )

    # Relationships
    set: Mapped["Set"] = relationship(  # noqa: F821
        "Set",
        back_populates="items",
        lazy="selectin",
    )

    stimuli: Mapped[list["Stimulus"]] = relationship(  # noqa: F821
        "Stimulus",
        back_populates="item",
        lazy="selectin",
        cascade="all, delete-orphan",
        order_by="Stimulus.display_order",
    )

    answer_keys: Mapped[list["AnswerKey"]] = relationship(  # noqa: F821
        "AnswerKey",
        back_populates="item",
        lazy="selectin",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"Item(id={self.id!r}, task_no={self.task_no}, task_type={self.task_type.value!r})"
