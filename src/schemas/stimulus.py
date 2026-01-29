"""
Stimulus 관련 Pydantic 스키마.

자극자료(Stimulus)의 생성, 조회, 수정을 위한 스키마를 정의합니다.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from src.models.enums import StimulusKind


class StimulusBase(BaseModel):
    """Stimulus 기본 스키마"""

    kind: StimulusKind = Field(
        ...,
        description="자료 유형 (reading/audio/image/direction)",
    )
    title: str | None = Field(
        None,
        description="자료 제목",
        max_length=200,
    )
    content_text: str | None = Field(
        None,
        description="텍스트 내용 (reading, direction 용)",
    )
    asset_url: str | None = Field(
        None,
        description="미디어 URL (audio, image 용)",
        max_length=500,
    )
    duration_seconds: int | None = Field(
        None,
        description="음성 길이 (초, audio 전용)",
        ge=0,
        le=600,
    )
    display_order: int = Field(
        default=0,
        description="표시 순서",
        ge=0,
    )
    notes_allowed: bool = Field(
        default=False,
        description="노트 필기 허용 여부",
    )


class StimulusCreate(StimulusBase):
    """Stimulus 생성 요청 스키마"""

    item_id: UUID = Field(..., description="소속 Item UUID")

    @model_validator(mode="after")
    def validate_kind_fields(self) -> "StimulusCreate":
        """kind별 필수 필드 검증 (REQ-SCHEMA-006)"""
        kind = self.kind

        if kind == StimulusKind.READING:
            if not self.content_text:
                raise ValueError("reading 유형은 content_text가 필수입니다")

        elif kind == StimulusKind.AUDIO:
            if not self.asset_url:
                raise ValueError("audio 유형은 asset_url이 필수입니다")
            if self.duration_seconds is None:
                raise ValueError("audio 유형은 duration_seconds가 필수입니다")

        elif kind == StimulusKind.IMAGE:
            if not self.asset_url:
                raise ValueError("image 유형은 asset_url이 필수입니다")

        elif kind == StimulusKind.DIRECTION:
            if not self.content_text:
                raise ValueError("direction 유형은 content_text가 필수입니다")

        return self


class StimulusUpdate(BaseModel):
    """Stimulus 수정 요청 스키마"""

    kind: StimulusKind | None = Field(
        None,
        description="자료 유형",
    )
    title: str | None = Field(
        None,
        description="자료 제목",
        max_length=200,
    )
    content_text: str | None = Field(
        None,
        description="텍스트 내용",
    )
    asset_url: str | None = Field(
        None,
        description="미디어 URL",
        max_length=500,
    )
    duration_seconds: int | None = Field(
        None,
        description="음성 길이 (초)",
        ge=0,
        le=600,
    )
    display_order: int | None = Field(
        None,
        description="표시 순서",
        ge=0,
    )
    notes_allowed: bool | None = Field(
        None,
        description="노트 필기 허용 여부",
    )


class StimulusResponse(BaseModel):
    """Stimulus 응답 스키마"""

    id: UUID = Field(..., description="Stimulus UUID")
    item_id: UUID = Field(..., description="소속 Item UUID")
    kind: StimulusKind = Field(..., description="자료 유형")
    title: str | None = Field(None, description="자료 제목")
    content_text: str | None = Field(None, description="텍스트 내용")
    asset_url: str | None = Field(None, description="미디어 URL")
    duration_seconds: int | None = Field(None, description="음성 길이 (초)")
    display_order: int = Field(..., description="표시 순서")
    notes_allowed: bool = Field(..., description="노트 필기 허용 여부")
    created_at: datetime = Field(..., description="생성 시각")

    model_config = {"from_attributes": True}


class StimulusListResponse(BaseModel):
    """Stimulus 목록 응답 스키마"""

    items: list[StimulusResponse] = Field(..., description="Stimulus 목록")
    total: int = Field(..., description="전체 개수")
