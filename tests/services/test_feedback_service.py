"""피드백 서비스 테스트 (모킹)"""

from unittest.mock import AsyncMock, patch

import pytest

from src.schemas.jobs import FeedbackReport, ScoreBand
from src.services.feedback_service import DeliveryFeatures, FeedbackService, FeedbackServiceConfig


@pytest.fixture
def feedback_service():
    """피드백 서비스 픽스처"""
    return FeedbackService()


@pytest.fixture
def delivery_features():
    """Delivery features 픽스처"""
    return DeliveryFeatures(
        duration_sec=45.5,
        wpm=120.5,
        silence_ratio=0.15,
        pause_count=5,
        pause_p95_ms=800,
        filler_count=2,
        asr_clarity_signal={"avg_logprob": -0.25, "no_speech_prob": 0.02},
    )


@pytest.fixture
def mock_feedback_report():
    """모킹된 피드백 리포트"""
    return FeedbackReport(
        summary={
            "line1": "Your response demonstrates good organization and clear structure.",
            "line2": "There are minor grammar errors that affect clarity.",
            "line3": "Vocabulary usage is appropriate for the task level.",
        },
        delivery={
            "speed": {"status": "good", "description": "Natural speaking pace at 120 WPM"},
            "pauses": {
                "status": "fair",
                "description": "Some noticeable hesitation with 5 pauses",
            },
            "clarity": {"status": "good", "description": "Clear pronunciation with good ASR confidence"},
        },
        language_use={
            "errors": [
                {"type": "grammar", "example": "I was go to school"},
                {"type": "word_choice", "example": "very much good"},
            ],
            "vocabulary_level": "intermediate",
            "sentence_variety": "good",
        },
        structure={
            "has_intro": True,
            "has_body": True,
            "has_conclusion": True,
            "coherence": "good",
        },
        score_band=ScoreBand(min=22, max=25),
        action_items=[
            "Focus on verb tense consistency",
            "Practice reducing filler words",
            "Work on smoother transitions between ideas",
        ],
    )


@pytest.mark.asyncio
async def test_generate_feedback_independent(
    feedback_service: FeedbackService, delivery_features: DeliveryFeatures, mock_feedback_report: FeedbackReport
):
    """독립형 문제 피드백 생성 테스트"""
    # LLM 서비스 모킹
    with patch.object(
        feedback_service.llm_service, "generate_feedback", new_callable=AsyncMock
    ) as mock_generate:
        mock_generate.return_value = mock_feedback_report

        # 피드백 생성
        result = await feedback_service.generate_feedback(
            task_type="independent",
            prompt="Do you agree or disagree that technology improves education?",
            transcript="I think technology is very important for education. It helps students learn more efficiently.",
            delivery_features=delivery_features,
        )

    # 검증
    assert isinstance(result, FeedbackReport)
    assert result.score_band.min >= 0
    assert result.score_band.max <= 30
    assert result.score_band.min <= result.score_band.max
    assert len(result.summary) == 3
    assert "delivery" in result.model_dump()
    assert "language_use" in result.model_dump()
    assert "structure" in result.model_dump()


@pytest.mark.asyncio
async def test_generate_feedback_integrated(
    feedback_service: FeedbackService, delivery_features: DeliveryFeatures, mock_feedback_report: FeedbackReport
):
    """통합형 문제 피드백 생성 테스트"""
    with patch.object(
        feedback_service.llm_service, "generate_feedback", new_callable=AsyncMock
    ) as mock_generate:
        mock_generate.return_value = mock_feedback_report

        result = await feedback_service.generate_feedback(
            task_type="integrated",
            prompt="Summarize the lecture and reading passage.",
            transcript="The lecture explains that climate change affects marine ecosystems.",
            delivery_features=delivery_features,
            source_reading="Climate change is affecting ocean temperatures...",
            source_listening="The professor discusses how rising temperatures impact coral reefs...",
        )

    # 검증
    assert isinstance(result, FeedbackReport)
    assert result.score_band.min >= 0
    assert result.score_band.max <= 30


@pytest.mark.asyncio
async def test_generate_feedback_with_language_features(
    feedback_service: FeedbackService, delivery_features: DeliveryFeatures, mock_feedback_report: FeedbackReport
):
    """Language features 추출 확인 테스트"""
    with patch.object(
        feedback_service.llm_service, "generate_feedback", new_callable=AsyncMock
    ) as mock_generate:
        mock_generate.return_value = mock_feedback_report

        # Language features가 추출되는지 확인하기 위해 transcript 제공
        await feedback_service.generate_feedback(
            task_type="independent",
            prompt="Test prompt",
            transcript="This is a test transcript with some words.",
            delivery_features=delivery_features,
        )

        # LLM이 호출되었는지 확인
        assert mock_generate.called
        call_args = mock_generate.call_args
        assert "features" in call_args.kwargs
        assert "language" in call_args.kwargs["features"]
        assert "delivery" in call_args.kwargs["features"]
        assert "structure" in call_args.kwargs["features"]


@pytest.mark.asyncio
async def test_generate_feedback_with_structure_features(
    feedback_service: FeedbackService, delivery_features: DeliveryFeatures, mock_feedback_report: FeedbackReport
):
    """Structure features 추출 확인 테스트"""
    with patch.object(
        feedback_service.llm_service, "generate_feedback", new_callable=AsyncMock
    ) as mock_generate:
        mock_generate.return_value = mock_feedback_report

        await feedback_service.generate_feedback(
            task_type="independent",
            prompt="Do you agree or disagree?",
            transcript="I agree because firstly, secondly, in conclusion.",
            delivery_features=delivery_features,
        )

        # Structure features가 포함되었는지 확인
        call_args = mock_generate.call_args
        assert "structure" in call_args.kwargs["features"]


@pytest.mark.asyncio
async def test_feedback_service_config():
    """피드백 서비스 설정 테스트"""
    from src.services.llm_service import LLMProvider

    config = FeedbackServiceConfig(
        llm_provider=LLMProvider.ANTHROPIC,
        llm_model="claude-3-5-sonnet-20241022",
        llm_temperature=0.5,
    )

    service = FeedbackService(config=config)

    assert service.config.llm_provider == LLMProvider.ANTHROPIC
    assert service.config.llm_model == "claude-3-5-sonnet-20241022"
    assert service.config.llm_temperature == 0.5


@pytest.mark.asyncio
async def test_generate_feedback_error_handling(
    feedback_service: FeedbackService, delivery_features: DeliveryFeatures
):
    """피드백 생성 중 오류 처리 테스트"""
    # LLM이 오류를 발생시키도록 모킹
    with patch.object(
        feedback_service.llm_service, "generate_feedback", new_callable=AsyncMock
    ) as mock_generate:
        mock_generate.side_effect = RuntimeError("LLM API failed")

        # 오류 발생 확인
        with pytest.raises(RuntimeError, match="LLM API failed"):
            await feedback_service.generate_feedback(
                task_type="independent",
                prompt="Test prompt",
                transcript="Test transcript",
                delivery_features=delivery_features,
            )


def test_delivery_features_validation():
    """DeliveryFeatures 검증 테스트"""
    # 정상적인 데이터
    features = DeliveryFeatures(
        duration_sec=45.5,
        wpm=120.0,
        silence_ratio=0.15,
        pause_count=5,
        pause_p95_ms=800,
        filler_count=2,
        asr_clarity_signal={"avg_logprob": -0.25, "no_speech_prob": 0.02},
    )

    assert features.duration_sec == 45.5
    assert features.wpm == 120.0
    assert features.silence_ratio == 0.15

    # 잘못된 데이터 (음수)
    with pytest.raises(Exception):  # Pydantic ValidationError
        DeliveryFeatures(
            duration_sec=-10.0,  # 음수 불가
            wpm=120.0,
            silence_ratio=0.15,
            pause_count=5,
            pause_p95_ms=800,
            filler_count=2,
            asr_clarity_signal={"avg_logprob": -0.25, "no_speech_prob": 0.02},
        )


def test_feedback_service_summarize_features(feedback_service: FeedbackService):
    """Features 요약 메서드 테스트"""
    features = {
        "delivery": {"wpm": 120.5, "silence_ratio": 0.15},
        "language": {"lexical_diversity": 0.75, "error_types": ["grammar", "word_choice"]},
        "structure": {"coherence_score": 0.85},
    }

    summary = feedback_service._summarize_features(features)

    assert "WPM=120" in summary or "WPM=121" in summary  # 반올림
    assert "Silence=0.15" in summary
    assert "TTR=0.75" in summary
    assert "Errors=2" in summary
    assert "Coherence=0.85" in summary
