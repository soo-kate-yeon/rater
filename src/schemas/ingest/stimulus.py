"""
StimulusIngest 스키마 - stimuli.json 파싱용.
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class StimulusIngest(BaseModel):
    """
    Stimulus 데이터 수집용 스키마.

    Attributes:
        stimulus_id: 자극자료 ID (string, UUID로 변환됨)
        item_id: 소속 Item ID (string, UUID로 변환됨)
        kind: 자료 유형 (reading, direction, listening)
        title: 자료 제목
        content_text: 텍스트 내용
        asset_url: 미디어 URL
        duration_seconds: 음성 길이 (초)
        order: 표시 순서
        notes_allowed: 노트 필기 허용 여부
    """

    stimulus_id: str = Field(..., description="자극자료 ID", min_length=1)
    item_id: str = Field(..., description="소속 Item ID", min_length=1)
    kind: Literal["reading", "direction", "listening"] = Field(..., description="자료 유형")
    title: str = Field(..., description="자료 제목", min_length=1)
    content_text: str | None = Field(None, description="텍스트 내용")
    asset_url: str | None = Field(None, description="미디어 URL")
    duration_seconds: float | None = Field(None, description="음성 길이 (초)")
    order: int = Field(0, description="표시 순서", ge=0)
    notes_allowed: bool = Field(True, description="노트 필기 허용 여부")
    created_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True, extra="ignore")
