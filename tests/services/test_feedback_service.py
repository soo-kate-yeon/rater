"""피드백 서비스 테스트 (모킹)"""

from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio

from src.schemas.jobs import FeedbackReport, ScoreBand
from src.services.feedback_service import DeliveryFeatures, FeedbackService, FeedbackServiceConfig


@pytest_asyncio.fixture
def feedback_service():
    """피드백 서비스 픽스처"""
    return FeedbackService()


@pytest_asyncio.fixture
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


@pytest_asyncio.fixture
def mock_feedback_report():
    """모킹된 피드백 리포트"""
    from src.schemas.jobs import (
        ActionItem,
        BottleneckInfo,
        DeliveryAnalysis,
        LanguageAnalysis,
        StructureAnalysis,
    )

    return FeedbackReport(
        summary_3lines=[
            "Your response demonstrates good organization and clear structure.",
            "There are minor grammar errors that affect clarity.",
            "Vocabulary usage is appropriate for the task level.",
        ],
        bottleneck=BottleneckInfo(
            title="Grammar consistency",
            explanation="Verb tense errors affect clarity",
            evidence_quote="I was go to school",
        ),
        action_items=[
            ActionItem(
                action="Focus on verb tense consistency",
                why="Tense errors reduce clarity",
                how_to="Practice past tense formation",
                example_sentence="I went to school yesterday.",
            )
        ],
        structure=StructureAnalysis(
            checklist={"has_intro": True, "has_body": True, "has_conclusion": True},
            missing=[],
            suggested_template="Introduction → Body → Conclusion",
        ),
        language=LanguageAnalysis(
            top_errors=["Verb tense", "Word choice"],
            improved_sentences=["I went to school instead of I was go to school"],
        ),
        delivery=DeliveryAnalysis(
            speed_comment="Natural speaking pace at 120 WPM",
            pause_comment="Some noticeable hesitation with 5 pauses",
            clarity_comment="Clear pronunciation with good ASR confidence",
        ),
        score_band=ScoreBand(
            min=22,
            max=25,
            rationale="Good structure and vocabulary, minor grammar issues",
        ),
        disclaimer="This is an automated assessment for practice purposes only.",
    )


@pytest.mark.asyncio
async def test_generate_feedback_independent(
    feedback_service: FeedbackService,
    delivery_features: DeliveryFeatures,
    mock_feedback_report: FeedbackReport,
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
    assert len(result.summary_3lines) == 3
    assert "delivery" in result.model_dump()
    assert "language" in result.model_dump()
    assert "structure" in result.model_dump()


@pytest.mark.asyncio
async def test_generate_feedback_integrated(
    feedback_service: FeedbackService,
    delivery_features: DeliveryFeatures,
    mock_feedback_report: FeedbackReport,
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
    feedback_service: FeedbackService,
    delivery_features: DeliveryFeatures,
    mock_feedback_report: FeedbackReport,
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
    feedback_service: FeedbackService,
    delivery_features: DeliveryFeatures,
    mock_feedback_report: FeedbackReport,
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


# ========== 3-Tier Feedback System Tests ==========


@pytest.mark.asyncio
async def test_generate_feedback_basic_tier(
    feedback_service: FeedbackService,
    delivery_features: DeliveryFeatures,
    mock_feedback_report: FeedbackReport,
):
    """Basic tier 피드백 생성 테스트"""
    with patch.object(
        feedback_service.llm_service, "generate_feedback", new_callable=AsyncMock
    ) as mock_generate:
        mock_generate.return_value = mock_feedback_report

        result = await feedback_service.generate_feedback(
            task_type="independent",
            prompt="Do you agree or disagree?",
            transcript="I think technology is important.",
            delivery_features=delivery_features,
            tier="basic",
        )

    # Basic tier 검증
    assert isinstance(result, FeedbackReport)
    # LLM 호출 시 tier 정보가 전달되는지 확인
    call_kwargs = mock_generate.call_args.kwargs
    assert "tier" in call_kwargs
    assert call_kwargs["tier"] == "basic"


@pytest.mark.asyncio
async def test_generate_feedback_standard_tier(
    feedback_service: FeedbackService,
    delivery_features: DeliveryFeatures,
    mock_feedback_report: FeedbackReport,
):
    """Standard tier 피드백 생성 테스트"""
    with patch.object(
        feedback_service.llm_service, "generate_feedback", new_callable=AsyncMock
    ) as mock_generate:
        mock_generate.return_value = mock_feedback_report

        result = await feedback_service.generate_feedback(
            task_type="independent",
            prompt="Do you agree or disagree?",
            transcript="I think technology is important because it helps learning.",
            delivery_features=delivery_features,
            tier="standard",
        )

    # Standard tier 검증
    assert isinstance(result, FeedbackReport)
    call_kwargs = mock_generate.call_args.kwargs
    assert "tier" in call_kwargs
    assert call_kwargs["tier"] == "standard"


@pytest.mark.asyncio
async def test_generate_feedback_premium_tier(
    feedback_service: FeedbackService,
    delivery_features: DeliveryFeatures,
    mock_feedback_report: FeedbackReport,
):
    """Premium tier 피드백 생성 테스트"""
    with patch.object(
        feedback_service.llm_service, "generate_feedback", new_callable=AsyncMock
    ) as mock_generate:
        mock_generate.return_value = mock_feedback_report

        result = await feedback_service.generate_feedback(
            task_type="independent",
            prompt="Do you agree or disagree?",
            transcript="I think technology is important. First, it helps learning. For example, online courses.",
            delivery_features=delivery_features,
            tier="premium",
        )

    # Premium tier 검증
    assert isinstance(result, FeedbackReport)
    call_kwargs = mock_generate.call_args.kwargs
    assert "tier" in call_kwargs
    assert call_kwargs["tier"] == "premium"


@pytest.mark.asyncio
async def test_generate_feedback_default_tier(
    feedback_service: FeedbackService,
    delivery_features: DeliveryFeatures,
    mock_feedback_report: FeedbackReport,
):
    """tier 미지정 시 기본값 basic 적용 테스트"""
    with patch.object(
        feedback_service.llm_service, "generate_feedback", new_callable=AsyncMock
    ) as mock_generate:
        mock_generate.return_value = mock_feedback_report

        result = await feedback_service.generate_feedback(
            task_type="independent",
            prompt="Test prompt",
            transcript="Test transcript",
            delivery_features=delivery_features,
            # tier 파라미터 생략
        )

    # 기본값 basic 확인
    assert isinstance(result, FeedbackReport)
    call_kwargs = mock_generate.call_args.kwargs
    assert "tier" in call_kwargs
    assert call_kwargs["tier"] == "basic"


@pytest.mark.asyncio
async def test_generate_feedback_invalid_tier(
    feedback_service: FeedbackService, delivery_features: DeliveryFeatures
):
    """잘못된 tier 값 처리 테스트 (타입 체커용)"""
    # Note: Literal 타입은 Python 런타임에서 검증되지 않고 mypy와 같은 정적 타입 체커에서만 검증됨
    # 따라서 이 테스트는 실제 ValidationError를 발생시키지 않음
    # 대신 tier 파라미터의 기본값이 제대로 작동하는지 테스트

    # tier를 명시하지 않고 호출 (기본값 "basic" 사용)
    with patch.object(
        feedback_service.llm_service, "generate_feedback", new_callable=AsyncMock
    ) as mock_generate:
        from src.schemas.jobs import (
            ActionItem,
            BottleneckInfo,
            DeliveryAnalysis,
            LanguageAnalysis,
            ScoreBand,
            StructureAnalysis,
        )

        mock_report = FeedbackReport(
            summary_3lines=["Test"] * 3,
            bottleneck=BottleneckInfo(title="Test", explanation="Test", evidence_quote="Test"),
            action_items=[
                ActionItem(action="Test", why="Test", how_to="Test", example_sentence="Test")
            ],
            structure=StructureAnalysis(checklist={}, missing=[], suggested_template="Test"),
            language=LanguageAnalysis(top_errors=[], improved_sentences=[]),
            delivery=DeliveryAnalysis(
                speed_comment="Test", pause_comment="Test", clarity_comment="Test"
            ),
            score_band=ScoreBand(min=20, max=25, rationale="Test"),
            disclaimer="Test",
        )
        mock_generate.return_value = mock_report

        result = await feedback_service.generate_feedback(
            task_type="independent",
            prompt="Test prompt",
            transcript="Test transcript",
            delivery_features=delivery_features,
            # tier 생략 - 기본값 "basic" 사용
        )

    # 기본값이 제대로 작동했는지 확인
    assert isinstance(result, FeedbackReport)
    call_kwargs = mock_generate.call_args.kwargs
    assert call_kwargs.get("tier") == "basic"


@pytest.mark.asyncio
async def test_tier_affects_llm_prompt(
    feedback_service: FeedbackService,
    delivery_features: DeliveryFeatures,
    mock_feedback_report: FeedbackReport,
):
    """tier에 따라 LLM 프롬프트가 달라지는지 확인"""
    with patch.object(
        feedback_service.llm_service, "generate_feedback", new_callable=AsyncMock
    ) as mock_generate:
        mock_generate.return_value = mock_feedback_report

        # Basic tier 호출
        await feedback_service.generate_feedback(
            task_type="independent",
            prompt="Test",
            transcript="Test",
            delivery_features=delivery_features,
            tier="basic",
        )
        basic_call = mock_generate.call_args

        mock_generate.reset_mock()

        # Premium tier 호출
        await feedback_service.generate_feedback(
            task_type="independent",
            prompt="Test",
            transcript="Test",
            delivery_features=delivery_features,
            tier="premium",
        )
        premium_call = mock_generate.call_args

    # tier 값이 다르게 전달되는지 확인
    assert basic_call.kwargs["tier"] == "basic"
    assert premium_call.kwargs["tier"] == "premium"
