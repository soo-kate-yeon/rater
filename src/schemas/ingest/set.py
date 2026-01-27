"""
SetIngest 스키마 - sets.json 파싱용.

JSON 파일의 string ID를 그대로 받아서 검증합니다.
UUID 변환은 매핑 레이어에서 수행됩니다.
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class SetIngest(BaseModel):
    """
    Set 데이터 수집용 스키마.

    Attributes:
        set_id: 세트 ID (string, UUID로 변환됨)
        title: 세트 제목
        source: 출처
        version: 버전
        created_at: 생성 시각 (선택, DB에서 자동 생성)
        updated_at: 수정 시각 (선택, DB에서 자동 생성)
    """

    set_id: str = Field(
        ...,
        description="세트 ID (UUID로 변환됨)",
        min_length=1,
        max_length=100,
    )
    title: str = Field(
        ...,
        description="세트 제목",
        min_length=1,
        max_length=200,
    )
    source: str = Field(
        ...,
        description="출처 (예: ETS Official, Kaplan)",
        min_length=1,
        max_length=100,
    )
    version: str = Field(
        ...,
        description="버전 (예: v1.0)",
        min_length=1,
        max_length=20,
    )
    created_at: Optional[datetime] = Field(
        None,
        description="생성 시각 (DB 자동 생성으로 무시됨)",
    )
    updated_at: Optional[datetime] = Field(
        None,
        description="수정 시각 (DB 자동 생성으로 무시됨)",
    )

    model_config = ConfigDict(
        from_attributes=True,
        extra="ignore",  # 추가 필드 무시
    )
