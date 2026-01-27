"""
Set 관련 Pydantic 스키마.

문제 세트(Set)의 생성, 조회, 수정을 위한 스키마를 정의합니다.
"""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class SetBase(BaseModel):
    """Set 기본 스키마"""

    title: str = Field(
        ...,
        description="세트 제목",
        min_length=1,
        max_length=200,
    )
    source: str = Field(
        ...,
        description="출처 (예: ETS Official, Kaplan, Custom)",
        min_length=1,
        max_length=100,
    )
    version: str = Field(
        ...,
        description="버전 (예: v1.0, v2.2)",
        min_length=1,
        max_length=20,
    )
    description: Optional[str] = Field(
        None,
        description="세트 설명",
    )


class SetCreate(SetBase):
    """Set 생성 요청 스키마"""

    pass


class SetUpdate(BaseModel):
    """Set 수정 요청 스키마"""

    title: Optional[str] = Field(
        None,
        description="세트 제목",
        min_length=1,
        max_length=200,
    )
    source: Optional[str] = Field(
        None,
        description="출처",
        min_length=1,
        max_length=100,
    )
    version: Optional[str] = Field(
        None,
        description="버전",
        min_length=1,
        max_length=20,
    )
    description: Optional[str] = Field(
        None,
        description="세트 설명",
    )


class SetResponse(SetBase):
    """Set 응답 스키마"""

    id: UUID = Field(..., description="Set UUID")
    created_at: datetime = Field(..., description="생성 시각")
    updated_at: datetime = Field(..., description="수정 시각")
    item_count: int = Field(default=0, description="포함된 Item 수")

    model_config = {"from_attributes": True}


class SetListResponse(BaseModel):
    """Set 목록 응답 스키마"""

    items: list[SetResponse] = Field(..., description="Set 목록")
    total: int = Field(..., description="전체 개수")
    skip: int = Field(..., description="건너뛴 개수")
    limit: int = Field(..., description="조회 개수")
