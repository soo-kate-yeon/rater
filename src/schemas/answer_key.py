"""
AnswerKey 관련 Pydantic 스키마.

모범답안(AnswerKey)의 생성, 조회, 수정을 위한 스키마를 정의합니다.
"""
from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from src.models.enums import AnswerKeyLevel, AnswerKeyType
from src.schemas.blueprint import BlueprintContent, IndependentBlueprint, IntegratedBlueprint


class AnswerKeyBase(BaseModel):
    """AnswerKey 기본 스키마"""

    answer_type: AnswerKeyType = Field(
        ...,
        description="모범답안 유형 (sample_response/transcript/outline/points/blueprint)",
    )
    level: Optional[AnswerKeyLevel] = Field(
        None,
        description="품질 수준 (high/mid/low)",
    )
    content: dict[str, Any] = Field(
        ...,
        description="모범답안 내용 또는 Blueprint JSON",
    )
    source: Optional[str] = Field(
        None,
        description="출처 (예: ETS Official, Expert Review)",
        max_length=100,
    )


class AnswerKeyCreate(AnswerKeyBase):
    """AnswerKey 생성 요청 스키마"""

    item_id: UUID = Field(..., description="소속 Item UUID")

    @field_validator("content")
    @classmethod
    def validate_content(cls, v: dict[str, Any], info) -> dict[str, Any]:
        """content 유효성 검증"""
        # 기본 검증: content가 비어있지 않은지 확인
        if not v:
            raise ValueError("content는 비어있을 수 없습니다")
        return v


class AnswerKeyCreateWithBlueprint(BaseModel):
    """Blueprint 유형의 AnswerKey 생성 요청 스키마"""

    item_id: UUID = Field(..., description="소속 Item UUID")
    answer_type: AnswerKeyType = Field(
        default=AnswerKeyType.BLUEPRINT,
        description="모범답안 유형 (blueprint 고정)",
    )
    level: Optional[AnswerKeyLevel] = Field(
        None,
        description="품질 수준",
    )
    blueprint: BlueprintContent = Field(
        ...,
        description="Blueprint 내용",
    )
    source: Optional[str] = Field(
        None,
        description="출처",
        max_length=100,
    )

    def to_answer_key_create(self) -> AnswerKeyCreate:
        """AnswerKeyCreate로 변환"""
        return AnswerKeyCreate(
            item_id=self.item_id,
            answer_type=self.answer_type,
            level=self.level,
            content=self.blueprint.model_dump(),
            source=self.source,
        )


class AnswerKeyUpdate(BaseModel):
    """AnswerKey 수정 요청 스키마"""

    answer_type: Optional[AnswerKeyType] = Field(
        None,
        description="모범답안 유형",
    )
    level: Optional[AnswerKeyLevel] = Field(
        None,
        description="품질 수준",
    )
    content: Optional[dict[str, Any]] = Field(
        None,
        description="모범답안 내용",
    )
    source: Optional[str] = Field(
        None,
        description="출처",
        max_length=100,
    )


class AnswerKeyResponse(BaseModel):
    """AnswerKey 응답 스키마"""

    id: UUID = Field(..., description="AnswerKey UUID")
    item_id: UUID = Field(..., description="소속 Item UUID")
    answer_type: AnswerKeyType = Field(..., description="모범답안 유형")
    level: Optional[AnswerKeyLevel] = Field(None, description="품질 수준")
    content: dict[str, Any] = Field(..., description="모범답안 내용")
    source: Optional[str] = Field(None, description="출처")
    created_at: datetime = Field(..., description="생성 시각")

    model_config = {"from_attributes": True}


class AnswerKeyListResponse(BaseModel):
    """AnswerKey 목록 응답 스키마"""

    items: list[AnswerKeyResponse] = Field(..., description="AnswerKey 목록")
    total: int = Field(..., description="전체 개수")


class SampleResponseContent(BaseModel):
    """sample_response 유형의 content 스키마"""

    text: str = Field(..., description="모범 응답 텍스트")
    audio_url: Optional[str] = Field(None, description="모범 응답 음성 URL")
    notes: Optional[str] = Field(None, description="평가자 노트")


class TranscriptContent(BaseModel):
    """transcript 유형의 content 스키마"""

    text: str = Field(..., description="스크립트 텍스트")
    speaker_labels: Optional[list[dict[str, Any]]] = Field(
        None,
        description="화자 구분 정보",
    )


class OutlineContent(BaseModel):
    """outline 유형의 content 스키마"""

    sections: list[dict[str, Any]] = Field(
        ...,
        description="응답 구조 섹션 목록",
    )


class PointsContent(BaseModel):
    """points 유형의 content 스키마"""

    key_points: list[str] = Field(
        ...,
        description="핵심 포인트 목록",
    )
    supporting_details: Optional[list[str]] = Field(
        None,
        description="보조 세부사항 목록",
    )
