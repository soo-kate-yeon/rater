"""
Item 관련 Pydantic 스키마.

개별 문항(Item)의 생성, 조회, 수정을 위한 스키마를 정의합니다.
"""
from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator

from src.models.enums import Difficulty, TopicCategory, TopicType
from src.models.task import TaskType


class ItemBase(BaseModel):
    """Item 기본 스키마"""

    task_no: int = Field(
        ...,
        description="Set 내 문항 번호 (1-4)",
        ge=1,
        le=10,
    )
    task_type: TaskType = Field(
        ...,
        description="문항 유형 (INDEPENDENT 또는 INTEGRATED)",
    )
    prompt: str = Field(
        ...,
        description="문제 지시문",
        min_length=1,
    )
    prep_seconds: int = Field(
        default=15,
        description="준비 시간 (초)",
        ge=0,
        le=120,
    )
    response_seconds: int = Field(
        default=45,
        description="응답 시간 (초)",
        ge=15,
        le=120,
    )

    # Independent 전용 필드
    topic_type: Optional[TopicType] = Field(
        None,
        description="주제 유형 (Independent 전용)",
    )
    topic_category: Optional[TopicCategory] = Field(
        None,
        description="주제 카테고리 (Independent 전용)",
    )
    question_pattern: Optional[str] = Field(
        None,
        description="질문 패턴 (예: Do you agree or disagree...)",
        max_length=200,
    )

    # 공통 필드
    tags: list[str] = Field(
        default_factory=list,
        description="태그 목록",
    )
    difficulty: Optional[Difficulty] = Field(
        None,
        description="난이도 (easy/medium/hard)",
    )
    scoring_focus: dict[str, float] = Field(
        default_factory=dict,
        description="채점 가중치 (예: {structure: 0.3, language: 0.4, delivery: 0.3})",
    )


class ItemCreate(ItemBase):
    """Item 생성 요청 스키마"""

    set_id: UUID = Field(..., description="소속 Set UUID")

    @model_validator(mode="after")
    def validate_independent_fields(self) -> "ItemCreate":
        """Independent 문제의 필수 필드 검증"""
        if self.task_type == TaskType.INDEPENDENT:
            if not self.topic_type:
                raise ValueError("Independent 문제는 topic_type이 필수입니다")
            if not self.topic_category:
                raise ValueError("Independent 문제는 topic_category가 필수입니다")
        return self

    @field_validator("scoring_focus")
    @classmethod
    def validate_scoring_focus(cls, v: dict[str, float]) -> dict[str, float]:
        """채점 가중치 검증"""
        if v:
            for key, value in v.items():
                if not 0 <= value <= 1:
                    raise ValueError(f"{key}의 가중치는 0-1 사이여야 합니다")
            total = sum(v.values())
            if abs(total - 1.0) > 0.01:
                raise ValueError(f"가중치 합이 1.0이어야 합니다 (현재: {total:.2f})")
        return v


class ItemUpdate(BaseModel):
    """Item 수정 요청 스키마"""

    task_no: Optional[int] = Field(
        None,
        description="Set 내 문항 번호 (1-4)",
        ge=1,
        le=10,
    )
    task_type: Optional[TaskType] = Field(
        None,
        description="문항 유형",
    )
    prompt: Optional[str] = Field(
        None,
        description="문제 지시문",
        min_length=1,
    )
    prep_seconds: Optional[int] = Field(
        None,
        description="준비 시간 (초)",
        ge=0,
        le=120,
    )
    response_seconds: Optional[int] = Field(
        None,
        description="응답 시간 (초)",
        ge=15,
        le=120,
    )
    topic_type: Optional[TopicType] = Field(
        None,
        description="주제 유형",
    )
    topic_category: Optional[TopicCategory] = Field(
        None,
        description="주제 카테고리",
    )
    question_pattern: Optional[str] = Field(
        None,
        description="질문 패턴",
        max_length=200,
    )
    tags: Optional[list[str]] = Field(
        None,
        description="태그 목록",
    )
    difficulty: Optional[Difficulty] = Field(
        None,
        description="난이도",
    )
    scoring_focus: Optional[dict[str, float]] = Field(
        None,
        description="채점 가중치",
    )


class ItemResponse(BaseModel):
    """Item 응답 스키마"""

    id: UUID = Field(..., description="Item UUID")
    set_id: UUID = Field(..., description="소속 Set UUID")
    task_no: int = Field(..., description="Set 내 문항 번호")
    task_type: TaskType = Field(..., description="문항 유형")
    prompt: str = Field(..., description="문제 지시문")
    prep_seconds: int = Field(..., description="준비 시간 (초)")
    response_seconds: int = Field(..., description="응답 시간 (초)")

    # Independent 전용 필드
    topic_type: Optional[TopicType] = Field(None, description="주제 유형")
    topic_category: Optional[TopicCategory] = Field(None, description="주제 카테고리")
    question_pattern: Optional[str] = Field(None, description="질문 패턴")

    # 공통 필드
    tags: list[Any] = Field(default_factory=list, description="태그 목록")
    difficulty: Optional[Difficulty] = Field(None, description="난이도")
    scoring_focus: dict[str, Any] = Field(default_factory=dict, description="채점 가중치")

    created_at: datetime = Field(..., description="생성 시각")
    updated_at: datetime = Field(..., description="수정 시각")

    model_config = {"from_attributes": True}


class ItemListResponse(BaseModel):
    """Item 목록 응답 스키마"""

    items: list[ItemResponse] = Field(..., description="Item 목록")
    total: int = Field(..., description="전체 개수")
    skip: int = Field(..., description="건너뛴 개수")
    limit: int = Field(..., description="조회 개수")
