"""파일 업로드 관련 Pydantic 스키마"""

from datetime import datetime

from pydantic import BaseModel, Field


class UploadResponse(BaseModel):
    """파일 업로드 응답 스키마"""

    audio_key: str = Field(..., description="저장된 오디오 파일 키 (경로)")
    uploaded_at: datetime = Field(..., description="업로드 시각")

    model_config = {"from_attributes": True}
