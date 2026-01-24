"""채점 관련 스키마"""

from typing import Any

from pydantic import BaseModel, Field


class WhisperSegment(BaseModel):
    """Whisper 세그먼트 (타임스탬프 포함)"""

    id: int = Field(..., description="세그먼트 ID")
    start: float = Field(..., description="시작 시간 (초)")
    end: float = Field(..., description="종료 시간 (초)")
    text: str = Field(..., description="전사된 텍스트")
    tokens: list[int] = Field(default_factory=list, description="토큰 ID 목록")
    temperature: float = Field(default=0.0, description="샘플링 온도")
    avg_logprob: float = Field(..., description="평균 로그 확률")
    compression_ratio: float = Field(..., description="압축 비율")
    no_speech_prob: float = Field(..., description="무음 확률")


class ASRResult(BaseModel):
    """Whisper ASR 결과"""

    transcript: str = Field(..., description="전체 전사 텍스트")
    segments: list[WhisperSegment] = Field(
        default_factory=list, description="타임스탬프 포함 세그먼트"
    )
    language: str = Field(..., description="감지된 언어 코드 (예: en)")
    avg_logprob: float = Field(..., description="전체 평균 로그 확률 (명료도 신호)")
    no_speech_prob: float = Field(..., description="무음 확률 (0-1)")
    duration_sec: float = Field(..., description="전체 오디오 길이 (초)")


class DeliverySignals(BaseModel):
    """Delivery 신호 (발화 특성)"""

    duration_sec: float = Field(..., description="전체 녹음 길이 (초)")
    wpm: float = Field(..., description="분당 단어 수 (Words Per Minute)")
    silence_ratio: float = Field(..., description="무음 비율 (침묵>500ms 누적 / 전체 길이)")
    pause_count: int = Field(..., description="무음 횟수 (침묵>500ms)")
    pause_p95_ms: float = Field(..., description="95th percentile 무음 길이 (밀리초)")
    filler_count: int = Field(..., description="filler 단어 카운트 (uh, um, like, you know)")
    asr_clarity_signal: float = Field(
        ..., description="ASR 명료도 신호 (avg_logprob 기반, -1.0 ~ 0.0)"
    )
    interpretation: str = Field(
        ..., description="해석 결과 (예: 속도 적절, 침묵 많음, 명료도 낮음)"
    )


class ScoringFeatures(BaseModel):
    """채점용 전체 Feature 세트"""

    asr_result: ASRResult = Field(..., description="Whisper ASR 결과")
    delivery_signals: DeliverySignals = Field(..., description="Delivery 신호")
    extracted_at: str = Field(..., description="추출 시각 (ISO 8601)")
