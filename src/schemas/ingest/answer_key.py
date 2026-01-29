"""
AnswerKeyIngest 스키마 - answer_keys.json 파싱용.
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class AnswerKeyIngest(BaseModel):
    """
    AnswerKey 데이터 수집용 스키마.

    Attributes:
        answer_id: 모범답안 ID (string, UUID로 변환됨)
        item_id: 소속 Item ID (string, UUID로 변환됨)
        type: 모범답안 유형
        level: 품질 수준 (선택)
        content: 모범답안 내용 (string, JSONB로 변환됨)
        source: 출처
    """

    answer_id: str = Field(..., description="모범답안 ID", min_length=1)
    item_id: str = Field(..., description="소속 Item ID", min_length=1)
    type: Literal["sample_response", "transcript", "blueprint"] = Field(
        ..., description="모범답안 유형"
    )
    level: Literal["basic", "advanced", "ultimate"] | None = Field(None, description="품질 수준")
    content: str = Field(..., description="모범답안 내용", min_length=1)
    source: str = Field(..., description="출처", min_length=1)
    created_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True, extra="ignore")
