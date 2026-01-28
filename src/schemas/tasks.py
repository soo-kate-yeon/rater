"""Task 관련 스키마"""

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class TaskCreate(BaseModel):
    """Task 생성 요청 스키마"""

    task_type: str = Field(..., description="Task 타입 (INDEPENDENT 또는 INTEGRATED)")
    prompt: str = Field(..., description="문제 프롬프트")
    source_reading: Optional[str] = Field(None, description="읽기 지문 (Integrated만)")
    source_listening: Optional[str] = Field(None, description="듣기 지문 (Integrated만)")
    tags: Optional[dict[str, Any]] = Field(default_factory=dict, description="태그 (난이도, 주제 등)")


class TaskResponse(BaseModel):
    """Task 응답 스키마"""

    id: UUID = Field(..., description="Task UUID")
    task_type: str = Field(..., description="Task 타입")
    prompt: str = Field(..., description="문제 프롬프트")
    source_reading: Optional[str] = Field(None, description="읽기 지문")
    source_listening: Optional[str] = Field(None, description="듣기 지문")
    tags: dict[str, Any] = Field(default_factory=dict, description="태그")
    created_at: datetime = Field(..., description="생성 시각")

    model_config = {"from_attributes": True}
