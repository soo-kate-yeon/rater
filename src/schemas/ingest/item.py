"""
ItemIngest 스키마 - items.json 파싱용.
"""
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class ItemIngest(BaseModel):
    """
    Item 데이터 수집용 스키마.

    Attributes:
        item_id: 문항 ID (string, UUID로 변환됨)
        set_id: 소속 Set ID (string, UUID로 변환됨)
        task_no: Set 내 문항 번호
        task_type: 문항 유형
        prompt: 문제 지시문
        prep_seconds: 준비 시간 (초)
        response_seconds: 응답 시간 (초)
        language: 언어 (기본값: "en")
        tags: 태그 목록
        difficulty: 난이도
        scoring_focus: 채점 가중치
    """

    item_id: str = Field(..., description="문항 ID", min_length=1)
    set_id: str = Field(..., description="소속 Set ID", min_length=1)
    task_no: int = Field(..., description="Set 내 문항 번호", ge=1)
    task_type: Literal["independent", "integrated_read_listen", "integrated_listen_only"] = Field(
        ..., description="문항 유형"
    )
    prompt: str = Field(..., description="문제 지시문", min_length=1)
    prep_seconds: int = Field(15, description="준비 시간 (초)", ge=0)
    response_seconds: int = Field(45, description="응답 시간 (초)", ge=0)
    language: str = Field("en", description="언어", max_length=10)
    tags: list[str] = Field(default_factory=list, description="태그 목록")
    difficulty: Optional[str] = Field(None, description="난이도")
    scoring_focus: Optional[str] = Field(None, description="채점 가중치")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True, extra="ignore")
