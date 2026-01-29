"""
통합 피드백 생성 서비스

Delivery, Language, Structure features를 통합하여 최종 피드백을 생성합니다.

TODO SPEC-TOEFL-FEATURE-001 Phase 2: 3-Tier Feedback System
- Basic tier: 기본 피드백 (점수, 간단한 요약)
- Standard tier: 상세 피드백 (섹션별 분석, 개선 제안)
- Premium tier: 전문가급 피드백 (세부 예시, 맞춤 학습 계획)
"""

import logging
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field

from src.schemas.jobs import FeedbackReport
from src.services.language_features import extract_language_features
from src.services.llm_service import LLMConfig, LLMProvider, LLMService
from src.services.structure_features import extract_structure_features

logger = logging.getLogger(__name__)


class DeliveryFeatures(BaseModel):
    """Delivery 신호 (Whisper segments 기반)"""

    duration_sec: float = Field(..., ge=0.0, description="전체 녹음 길이 (초)")
    wpm: float = Field(..., ge=0.0, description="Words per minute")
    silence_ratio: float = Field(..., ge=0.0, le=1.0, description="침묵 비율 (0.0-1.0)")
    pause_count: int = Field(..., ge=0, description="침묵(>500ms) 횟수")
    pause_p95_ms: int = Field(..., ge=0, description="95th percentile pause 길이 (ms)")
    filler_count: int = Field(..., ge=0, description="Filler 단어 카운트 (uh, um, like)")
    asr_clarity_signal: dict[str, float] = Field(
        ...,
        description="ASR 명료도 신호 (avg_logprob, no_speech_prob)",
    )


class FeedbackServiceConfig(BaseModel):
    """피드백 서비스 설정"""

    llm_provider: LLMProvider = Field(
        default=LLMProvider.OPENAI,
        description="LLM 제공자",
    )
    llm_model: str = Field(
        default="gpt-4o-2024-08-06",
        description="LLM 모델 이름",
    )
    llm_temperature: float = Field(
        default=0.3,
        ge=0.0,
        le=2.0,
        description="LLM Temperature",
    )


class FeedbackService:
    """
    통합 피드백 생성 서비스

    Delivery, Language, Structure features를 추출하고,
    LLM을 사용하여 최종 FeedbackReport를 생성합니다.

    Workflow:
        1. Delivery features 수신 (이미 추출됨)
        2. Language features 추출 (transcript 기반)
        3. Structure features 추출 (transcript + prompt 기반)
        4. 모든 features를 LLM에 전달하여 피드백 생성
    """

    def __init__(self, config: Optional[FeedbackServiceConfig] = None) -> None:
        """
        피드백 서비스 초기화

        Args:
            config: 서비스 설정 (None이면 기본값 사용)
        """
        self.config = config or FeedbackServiceConfig()

        # LLM 서비스 초기화
        llm_config = LLMConfig(
            provider=self.config.llm_provider,
            model=self.config.llm_model,
            temperature=self.config.llm_temperature,
        )
        self.llm_service = LLMService(config=llm_config)

    async def generate_feedback(
        self,
        task_type: Literal["independent", "integrated"],
        prompt: str,
        transcript: str,
        delivery_features: DeliveryFeatures,
        source_reading: Optional[str] = None,
        source_listening: Optional[str] = None,
        tier: Literal["basic", "standard", "premium"] = "basic",
    ) -> FeedbackReport:
        """
        최종 피드백 생성

        Args:
            task_type: 문제 유형 (independent/integrated)
            prompt: 질문 텍스트
            transcript: Whisper ASR 결과
            delivery_features: Delivery 신호 (이미 추출됨)
            source_reading: 읽기 지문 (통합형)
            source_listening: 듣기 지문 (통합형)
            tier: 피드백 레벨 (basic/standard/premium, 기본값: basic)

        Returns:
            FeedbackReport: 최종 피드백 리포트

        Raises:
            RuntimeError: 피드백 생성 실패

        Note:
            SPEC-TOEFL-FEATURE-001 Phase 2: 3-Tier Feedback System
            - Basic: 기본 피드백 (점수, 간단한 요약)
            - Standard: 상세 피드백 (섹션별 분석, 개선 제안)
            - Premium: 전문가급 피드백 (세부 예시, 맞춤 학습 계획)
        """
        logger.info(f"피드백 생성 시작: task_type={task_type}, tier={tier}")

        # 1. Language Features 추출
        logger.info("Language features 추출 중...")
        language_features = extract_language_features(transcript)

        # 2. Structure Features 추출
        logger.info("Structure features 추출 중...")
        structure_features = extract_structure_features(transcript, prompt)

        # 3. 모든 Features 통합
        all_features = {
            "delivery": delivery_features.model_dump(),
            "language": language_features,
            "structure": structure_features,
        }

        logger.info(f"Features 추출 완료: {self._summarize_features(all_features)}")

        # 4. LLM을 통한 피드백 생성
        logger.info(f"LLM 피드백 생성 중... (tier={tier})")
        feedback_report = await self.llm_service.generate_feedback(
            task_type=task_type,
            prompt=prompt,
            transcript=transcript,
            features=all_features,
            source_reading=source_reading,
            source_listening=source_listening,
            tier=tier,
        )

        logger.info(
            f"피드백 생성 완료: score_band={feedback_report.score_band.min}-{feedback_report.score_band.max}"
        )

        return feedback_report

    def _summarize_features(self, features: dict[str, Any]) -> str:
        """
        Features 요약 (로그용)

        Args:
            features: 통합 Features 딕셔너리

        Returns:
            요약 문자열
        """
        delivery = features["delivery"]
        language = features["language"]
        structure = features["structure"]

        summary = (
            f"WPM={delivery.get('wpm', 0):.0f}, "
            f"Silence={delivery.get('silence_ratio', 0):.2f}, "
            f"TTR={language.get('lexical_diversity', 0):.2f}, "
            f"Errors={len(language.get('error_types', []))}, "
            f"Coherence={structure.get('coherence_score', 0):.2f}"
        )

        return summary


async def generate_full_feedback(
    task_type: Literal["independent", "integrated"],
    prompt: str,
    transcript: str,
    delivery_features_dict: dict[str, Any],
    source_reading: Optional[str] = None,
    source_listening: Optional[str] = None,
    llm_provider: LLMProvider = LLMProvider.OPENAI,
    tier: Literal["basic", "standard", "premium"] = "basic",
    grammar_features: Optional[dict[str, Any]] = None,
    vocabulary_features: Optional[dict[str, Any]] = None,
    blueprint_result: Optional[dict[str, Any]] = None,
    structure_result: Optional[dict[str, Any]] = None,
) -> FeedbackReport:
    """
    피드백 생성 헬퍼 함수

    Args:
        task_type: 문제 유형
        prompt: 질문 텍스트
        transcript: Whisper 결과
        delivery_features_dict: Delivery features 딕셔너리
        source_reading: 읽기 지문
        source_listening: 듣기 지문
        llm_provider: LLM 제공자
        tier: 피드백 레벨 (basic/standard/premium)
        grammar_features: Grammar features (Phase 1+2)
        vocabulary_features: Vocabulary features (Phase 1+2)
        blueprint_result: Blueprint comparison result (Integrated)
        structure_result: Structure comparison result (Independent)

    Returns:
        FeedbackReport: 최종 피드백 리포트
    """
    # Delivery features 검증
    delivery_features = DeliveryFeatures.model_validate(delivery_features_dict)

    # 서비스 초기화 및 피드백 생성
    config = FeedbackServiceConfig(llm_provider=llm_provider)
    service = FeedbackService(config=config)

    # Language features 추출 (기존 방식 유지)
    language_features = extract_language_features(transcript)

    # Structure features 추출 (기존 방식 유지)
    structure_features = extract_structure_features(transcript, prompt)

    # 모든 features 통합
    all_features = {
        "delivery": delivery_features.model_dump(),
        "language": language_features,
        "structure": structure_features,
        "grammar": grammar_features or {},
        "vocabulary": vocabulary_features or {},
        "blueprint": blueprint_result,
        "structure_comparison": structure_result,
    }

    # LLM 피드백 생성
    report = await service.llm_service.generate_feedback(
        task_type=task_type,
        prompt=prompt,
        transcript=transcript,
        features=all_features,
        source_reading=source_reading,
        source_listening=source_listening,
        tier=tier,
    )

    return report
