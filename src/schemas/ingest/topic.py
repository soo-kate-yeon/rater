"""
IndependentTopicIngest 스키마 - independent_topics.json 파싱용.
"""

from pydantic import BaseModel, ConfigDict, Field


class IndependentTopicIngest(BaseModel):
    """
    IndependentTopic 데이터 수집용 스키마.

    Attributes:
        topic_id: 토픽 ID (string, UUID로 변환됨)
        number: 토픽 번호
        prompt: 토픽 프롬프트
        source: 출처
    """

    topic_id: str = Field(..., description="토픽 ID", min_length=1)
    number: int = Field(..., description="토픽 번호", ge=1)
    prompt: str = Field(..., description="토픽 프롬프트", min_length=1)
    source: str = Field(..., description="출처", min_length=1)

    model_config = ConfigDict(from_attributes=True, extra="ignore")
