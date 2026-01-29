"""채점 Job 관련 Pydantic 스키마"""

from datetime import datetime
from enum import Enum
from typing import Literal, Optional

from pydantic import BaseModel, Field


class JobStatus(str, Enum):
    """Job 상태 열거형"""

    QUEUED = "QUEUED"
    FETCHING_AUDIO = "FETCHING_AUDIO"
    ASR_RUNNING = "ASR_RUNNING"
    FEATURE_EXTRACTING = "FEATURE_EXTRACTING"
    LLM_ANALYZING = "LLM_ANALYZING"
    SCORING = "SCORING"
    DONE = "DONE"
    FAILED = "FAILED"


class TaskType(str, Enum):
    """TOEFL 문제 유형"""

    INDEPENDENT = "independent"
    INTEGRATED = "integrated"


class JobCreate(BaseModel):
    """Job 생성 요청 스키마"""

    audio_key: str = Field(..., description="업로드된 오디오 파일 키")
    task_id: str = Field(..., description="문제 UUID")
    task_type: TaskType = Field(..., description="문제 유형 (independent/integrated)")
    prompt: str = Field(..., description="질문 텍스트")
    source_reading: Optional[str] = Field(None, description="통합형 문제용 읽기 지문")
    source_listening: Optional[str] = Field(None, description="통합형 문제용 듣기 지문")
    tier: Literal["basic", "standard", "premium"] = Field(
        default="basic",
        description="피드백 티어 레벨 (basic/standard/premium)",
    )


class JobResponse(BaseModel):
    """Job 생성 응답 스키마"""

    job_id: str = Field(..., description="Job UUID")
    status: JobStatus = Field(..., description="Job 상태")

    model_config = {"from_attributes": True}


class JobStatusResponse(BaseModel):
    """Job 상태 조회 응답 스키마"""

    status: JobStatus = Field(..., description="현재 Job 상태")
    progress: int = Field(..., ge=0, le=100, description="진행률 (0-100)")
    created_at: datetime = Field(..., description="Job 생성 시각")
    updated_at: datetime = Field(..., description="Job 업데이트 시각")
    error_code: Optional[str] = Field(None, description="에러 코드 (실패 시)")
    error_message: Optional[str] = Field(None, description="에러 메시지 (실패 시)")

    model_config = {"from_attributes": True}


class BottleneckInfo(BaseModel):
    """가장 큰 병목 정보"""

    title: str = Field(..., description="병목 제목")
    explanation: str = Field(..., description="병목 설명")
    evidence_quote: str = Field(..., description="증거 문장 인용")


class ActionItem(BaseModel):
    """행동 아이템"""

    action: str = Field(..., description="구체적 행동")
    why: str = Field(..., description="이유")
    how_to: str = Field(..., description="방법")
    example_sentence: str = Field(..., description="예시 문장")


class StructureAnalysis(BaseModel):
    """답변 구조 분석"""

    checklist: dict[str, bool] = Field(..., description="구조 체크리스트")
    missing: list[str] = Field(..., description="누락된 구조 요소")
    suggested_template: str = Field(..., description="제안 템플릿")


class LanguageAnalysis(BaseModel):
    """언어 사용 분석"""

    top_errors: list[str] = Field(..., description="반복 오류 TOP 2")
    improved_sentences: list[str] = Field(..., description="개선 문장 예시")


class DeliveryAnalysis(BaseModel):
    """Delivery 분석"""

    speed_comment: str = Field(..., description="속도 코멘트")
    pause_comment: str = Field(..., description="침묵 코멘트")
    clarity_comment: str = Field(..., description="명료도 코멘트")


class ScoreBand(BaseModel):
    """점수 범위"""

    min: int = Field(..., ge=0, le=30, description="최소 점수")
    max: int = Field(..., ge=0, le=30, description="최대 점수")
    rationale: str = Field(..., description="점수 근거")


class FeedbackReport(BaseModel):
    """최종 피드백 리포트"""

    summary_3lines: list[str] = Field(..., description="요약 진단 (3줄)")
    bottleneck: BottleneckInfo = Field(..., description="가장 큰 병목 1가지")
    action_items: list[ActionItem] = Field(..., description="행동 아이템 (1-2개)")
    structure: StructureAnalysis = Field(..., description="답변 구조 분석")
    language: LanguageAnalysis = Field(..., description="언어 사용 분석")
    delivery: DeliveryAnalysis = Field(..., description="Delivery 분석")
    score_band: ScoreBand = Field(..., description="점수 범위")
    disclaimer: str = Field(..., description="면책 고지")


class ReportResponse(BaseModel):
    """리포트 조회 응답 스키마"""

    job_id: str = Field(..., description="Job UUID")
    report: FeedbackReport = Field(..., description="피드백 리포트")
    created_at: datetime = Field(..., description="리포트 생성 시각")

    model_config = {"from_attributes": True}
