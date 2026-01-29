"""
Blueprint Pydantic 스키마.

TOEFL Speaking 문제의 모범답안 구조(Blueprint)를 정의합니다.
Integrated(통합형)와 Independent(독립형) 두 가지 유형의 Blueprint를 지원합니다.
"""

from typing import Literal

from pydantic import BaseModel, Field, field_validator

from src.models.enums import TopicType


class InfoUnit(BaseModel):
    """
    정보 단위 - Integrated Blueprint용.

    읽기 또는 듣기 자료에서 추출한 정보 단위를 나타냅니다.
    """

    source: Literal["reading", "listening"] = Field(
        ...,
        description="정보 출처 (reading 또는 listening)",
    )
    label: str = Field(
        ...,
        description="정보 단위 레이블 (예: Main Point, Example 1, Reason)",
        max_length=100,
    )
    content: str = Field(
        ...,
        description="정보 내용",
        min_length=1,
    )
    importance: Literal["essential", "supporting", "optional"] = Field(
        default="supporting",
        description="중요도 (essential: 필수, supporting: 보조, optional: 선택)",
    )


class LinkingMove(BaseModel):
    """
    연결 표현 - 응답 구조의 전환점에서 사용할 표현.

    문장 간 또는 단락 간 연결에 사용되는 표현을 정의합니다.
    """

    position: str = Field(
        ...,
        description="사용 위치 (예: transition_to_listening, contrast, conclusion)",
        max_length=50,
    )
    phrases: list[str] = Field(
        ...,
        description="사용 가능한 연결 표현 목록",
        min_length=1,
    )


class TimeBudget(BaseModel):
    """
    시간 배분 - 응답의 각 섹션에 할당된 시간(초).

    효과적인 시간 관리를 위한 권장 시간 배분을 정의합니다.
    """

    intro_seconds: int = Field(
        default=10,
        ge=5,
        le=15,
        description="도입부 시간 (초)",
    )
    reading_summary_seconds: int = Field(
        default=15,
        ge=10,
        le=25,
        description="읽기 요약 시간 (초)",
    )
    listening_summary_seconds: int = Field(
        default=20,
        ge=15,
        le=30,
        description="듣기 요약 시간 (초)",
    )
    conclusion_seconds: int = Field(
        default=5,
        ge=0,
        le=10,
        description="결론 시간 (초)",
    )


class IndependentTimeBudget(BaseModel):
    """
    Independent 문제용 시간 배분.
    """

    intro_seconds: int = Field(
        default=10,
        ge=5,
        le=15,
        description="도입부 시간 (초)",
    )
    body_seconds: int = Field(
        default=30,
        ge=20,
        le=40,
        description="본론 시간 (초)",
    )
    conclusion_seconds: int = Field(
        default=5,
        ge=0,
        le=10,
        description="결론 시간 (초)",
    )


class ScoreExpectation(BaseModel):
    """
    채점 기대치 - 각 평가 영역의 가중치.

    구조, 언어, 전달의 세 영역에 대한 가중치 합이 1.0이 되어야 합니다.
    """

    structure_weight: float = Field(
        default=0.3,
        ge=0,
        le=1,
        description="구조 가중치 (0-1)",
    )
    language_weight: float = Field(
        default=0.4,
        ge=0,
        le=1,
        description="언어 가중치 (0-1)",
    )
    delivery_weight: float = Field(
        default=0.3,
        ge=0,
        le=1,
        description="전달 가중치 (0-1)",
    )

    @field_validator("delivery_weight")
    @classmethod
    def validate_weights_sum(cls, v: float, info) -> float:
        """가중치 합이 1.0인지 검증"""
        data = info.data
        total = data.get("structure_weight", 0.3) + data.get("language_weight", 0.4) + v
        if abs(total - 1.0) > 0.01:  # 부동소수점 오차 허용
            raise ValueError(f"가중치 합이 1.0이어야 합니다 (현재: {total:.2f})")
        return v


class IntegratedBlueprint(BaseModel):
    """
    통합형 문제 Blueprint.

    Integrated 문제(Task 3-4)의 모범답안 구조를 정의합니다.
    읽기와 듣기 자료를 통합하여 응답하는 방법을 안내합니다.
    """

    schema_version: str = Field(
        default="1.0",
        description="Blueprint 스키마 버전",
    )
    info_units: list[InfoUnit] = Field(
        ...,
        description="정보 단위 목록",
        min_length=1,
    )
    recommended_order: list[str] = Field(
        ...,
        description="권장 응답 순서 (info_unit 레이블 목록)",
        min_length=1,
    )
    linking_moves: list[LinkingMove] = Field(
        default_factory=list,
        description="연결 표현 목록",
    )
    coverage_expectations: dict[str, float] = Field(
        default={"reading": 0.3, "listening": 0.7},
        description="자료별 커버리지 기대치 (합 1.0)",
    )
    time_budget: TimeBudget = Field(
        default_factory=TimeBudget,
        description="시간 배분",
    )

    model_config = {"extra": "forbid"}

    @field_validator("coverage_expectations")
    @classmethod
    def validate_coverage(cls, v: dict[str, float]) -> dict[str, float]:
        """커버리지 합이 1.0인지 검증"""
        if "reading" not in v or "listening" not in v:
            raise ValueError("coverage_expectations에 reading과 listening이 필요합니다")
        total = v.get("reading", 0) + v.get("listening", 0)
        if abs(total - 1.0) > 0.01:
            raise ValueError(f"커버리지 합이 1.0이어야 합니다 (현재: {total:.2f})")
        return v


class IndependentBlueprint(BaseModel):
    """
    독립형 문제 Blueprint.

    Independent 문제(Task 1-2)의 모범답안 구조를 정의합니다.
    개인적인 의견이나 선호도를 표현하는 방법을 안내합니다.
    """

    schema_version: str = Field(
        default="1.0",
        description="Blueprint 스키마 버전",
    )
    topic_type: TopicType = Field(
        ...,
        description="주제 유형",
    )
    recommended_structure: list[str] = Field(
        ...,
        description="권장 응답 구조 (예: [intro, reason_1, example_1, reason_2, conclusion])",
        min_length=1,
    )
    linking_moves: list[LinkingMove] = Field(
        default_factory=list,
        description="연결 표현 목록",
    )
    score_expectations: ScoreExpectation = Field(
        default_factory=ScoreExpectation,
        description="채점 기대치",
    )
    topic_specific_vocabulary: list[str] = Field(
        default_factory=list,
        description="주제별 권장 어휘 목록",
    )
    time_budget: IndependentTimeBudget = Field(
        default_factory=IndependentTimeBudget,
        description="시간 배분",
    )

    model_config = {"extra": "forbid"}


class BlueprintContent(BaseModel):
    """
    AnswerKey content 필드에 저장되는 Blueprint wrapper.

    answer_type이 'blueprint'인 경우 이 스키마를 사용합니다.
    """

    blueprint_type: Literal["integrated", "independent"] = Field(
        ...,
        description="Blueprint 유형",
    )
    data: dict = Field(
        ...,
        description="IntegratedBlueprint 또는 IndependentBlueprint 데이터",
    )

    @field_validator("data")
    @classmethod
    def validate_blueprint_data(cls, v: dict, info) -> dict:
        """Blueprint 데이터 유효성 검증"""
        blueprint_type = info.data.get("blueprint_type")
        if blueprint_type == "integrated":
            # IntegratedBlueprint 스키마 검증
            IntegratedBlueprint.model_validate(v)
        elif blueprint_type == "independent":
            # IndependentBlueprint 스키마 검증
            IndependentBlueprint.model_validate(v)
        return v

    model_config = {"extra": "forbid"}
