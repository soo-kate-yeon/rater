"""LLM Service 테스트

LLMService의 모든 메서드와 프로바이더 통합을 테스트합니다.
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from pydantic import ValidationError

from src.schemas.jobs import FeedbackReport
from src.services.llm_service import LLMConfig, LLMProvider, LLMService


# ============================================================================
# 테스트 픽스처
# ============================================================================


@pytest_asyncio.fixture
def mock_feedback_dict() -> dict:
    """모킹된 FeedbackReport JSON"""
    return {
        "summary_3lines": [
            "Your response shows good organization.",
            "Main issue: Minor grammar errors.",
            "With practice, you can reach higher scores.",
        ],
        "bottleneck": {
            "title": "문법 오류",
            "explanation": "동사 시제 일관성이 부족합니다.",
            "evidence_quote": "I was go to school",
        },
        "action_items": [
            {
                "action": "동사 시제 연습",
                "why": "시제 일관성이 중요합니다",
                "how_to": "과거 시제 문장 10개 작성",
                "example_sentence": "I went to school yesterday.",
            }
        ],
        "structure": {
            "checklist": {
                "Intro": True,
                "Reason1": True,
                "Example1": True,
                "Reason2": False,
                "Example2": False,
                "Wrap-up": True,
            },
            "missing": ["Reason2", "Example2"],
            "suggested_template": "Intro → Reason1 → Example1 → Reason2 → Example2 → Wrap-up",
        },
        "language": {
            "top_errors": ["Verb tense (3)", "Article usage (2)"],
            "improved_sentences": ["I was go → I went"],
        },
        "delivery": {
            "speed_comment": "Natural speaking pace",
            "pause_comment": "Some hesitation noted",
            "clarity_comment": "Clear pronunciation",
        },
        "score_band": {"min": 22, "max": 25, "rationale": "Good organization with minor errors"},
        "disclaimer": "본 평가는 학습 도구이며 실제 TOEFL 점수와 다를 수 있습니다.",
    }


@pytest_asyncio.fixture
def llm_config_openai() -> LLMConfig:
    """OpenAI LLM 설정"""
    return LLMConfig(
        provider=LLMProvider.OPENAI,
        model="gpt-4o-2024-08-06",
        temperature=0.3,
        max_tokens=4096,
        max_retries=3,
    )


@pytest_asyncio.fixture
def llm_config_anthropic() -> LLMConfig:
    """Anthropic LLM 설정"""
    return LLMConfig(
        provider=LLMProvider.ANTHROPIC,
        model="claude-3-5-sonnet-20241022",
        temperature=0.3,
        max_tokens=4096,
        max_retries=3,
    )


# ============================================================================
# LLMService 초기화 테스트
# ============================================================================


def test_llm_service_default_config():
    """기본 설정으로 LLMService 초기화"""
    service = LLMService()
    assert service.config.provider == LLMProvider.OPENAI
    assert service.config.model == "gpt-4o-2024-08-06"


def test_llm_service_custom_config(llm_config_anthropic: LLMConfig):
    """커스텀 설정으로 LLMService 초기화"""
    service = LLMService(config=llm_config_anthropic)
    assert service.config.provider == LLMProvider.ANTHROPIC
    assert service.config.model == "claude-3-5-sonnet-20241022"


# ============================================================================
# OpenAI 클라이언트 테스트
# ============================================================================


def test_openai_client_lazy_initialization(llm_config_openai: LLMConfig):
    """OpenAI 클라이언트 lazy initialization"""
    with patch("src.services.llm_service.settings") as mock_settings:
        mock_settings.openai_api_key = "test-api-key"

        service = LLMService(config=llm_config_openai)
        assert service._openai_client is None

        # 첫 접근 시 초기화
        client = service.openai_client
        assert client is not None
        assert service._openai_client is not None


def test_openai_client_missing_api_key(llm_config_openai: LLMConfig):
    """OpenAI API 키 미설정 시 에러"""
    with patch("src.services.llm_service.settings") as mock_settings:
        mock_settings.openai_api_key = None

        service = LLMService(config=llm_config_openai)
        with pytest.raises(ValueError, match="OPENAI_API_KEY"):
            _ = service.openai_client


# ============================================================================
# Anthropic 클라이언트 테스트
# ============================================================================


def test_anthropic_client_lazy_initialization(llm_config_anthropic: LLMConfig):
    """Anthropic 클라이언트 lazy initialization"""
    with patch("src.services.llm_service.settings") as mock_settings:
        mock_settings.anthropic_api_key = "test-api-key"

        service = LLMService(config=llm_config_anthropic)
        assert service._anthropic_client is None

        # 첫 접근 시 초기화
        client = service.anthropic_client
        assert client is not None
        assert service._anthropic_client is not None


def test_anthropic_client_missing_api_key(llm_config_anthropic: LLMConfig):
    """Anthropic API 키 미설정 시 에러"""
    with patch("src.services.llm_service.settings") as mock_settings:
        mock_settings.anthropic_api_key = None

        service = LLMService(config=llm_config_anthropic)
        with pytest.raises(ValueError, match="ANTHROPIC_API_KEY"):
            _ = service.anthropic_client


# ============================================================================
# _call_openai 테스트
# ============================================================================


@pytest.mark.asyncio
async def test_call_openai_success(llm_config_openai: LLMConfig, mock_feedback_dict: dict):
    """OpenAI API 호출 성공 테스트"""
    with patch("src.services.llm_service.settings") as mock_settings:
        mock_settings.openai_api_key = "test-api-key"

        service = LLMService(config=llm_config_openai)

        # Mock OpenAI response
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content=json.dumps(mock_feedback_dict)))
        ]

        # Mock the internal client directly
        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        service._openai_client = mock_client

        result = await service._call_openai("system prompt", "user prompt")

        assert result == json.dumps(mock_feedback_dict)
        mock_client.chat.completions.create.assert_called_once()


@pytest.mark.asyncio
async def test_call_openai_empty_response(llm_config_openai: LLMConfig):
    """OpenAI 응답이 비어있는 경우"""
    with patch("src.services.llm_service.settings") as mock_settings:
        mock_settings.openai_api_key = "test-api-key"

        service = LLMService(config=llm_config_openai)

        # Mock empty response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content=None))]

        # Mock the internal client directly
        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        service._openai_client = mock_client

        with pytest.raises(RuntimeError, match="비어있습니다"):
            await service._call_openai("system prompt", "user prompt")


# ============================================================================
# _call_anthropic 테스트
# ============================================================================


@pytest.mark.asyncio
async def test_call_anthropic_success(llm_config_anthropic: LLMConfig, mock_feedback_dict: dict):
    """Anthropic API 호출 성공 테스트"""
    with patch("src.services.llm_service.settings") as mock_settings:
        mock_settings.anthropic_api_key = "test-api-key"

        service = LLMService(config=llm_config_anthropic)

        # Mock Anthropic response
        mock_content_block = MagicMock()
        mock_content_block.text = json.dumps(mock_feedback_dict)
        mock_response = MagicMock()
        mock_response.content = [mock_content_block]

        # Mock the internal client directly
        mock_client = MagicMock()
        mock_client.messages.create = AsyncMock(return_value=mock_response)
        service._anthropic_client = mock_client

        result = await service._call_anthropic("system prompt", "user prompt")

        assert result == json.dumps(mock_feedback_dict)
        mock_client.messages.create.assert_called_once()


# ============================================================================
# _parse_and_validate 테스트
# ============================================================================


def test_parse_and_validate_success(mock_feedback_dict: dict):
    """JSON 파싱 및 검증 성공"""
    service = LLMService()
    raw_response = json.dumps(mock_feedback_dict)

    result = service._parse_and_validate(raw_response)

    assert isinstance(result, FeedbackReport)
    assert result.score_band.min == 22
    assert result.score_band.max == 25


def test_parse_and_validate_invalid_json():
    """잘못된 JSON 형식"""
    service = LLMService()
    raw_response = "This is not valid JSON"

    with pytest.raises(json.JSONDecodeError):
        service._parse_and_validate(raw_response)


def test_parse_and_validate_invalid_schema():
    """Pydantic 스키마 검증 실패"""
    service = LLMService()
    # score_band가 없는 잘못된 데이터
    invalid_data = {
        "summary_3lines": ["line1", "line2", "line3"],
        # score_band 누락
    }
    raw_response = json.dumps(invalid_data)

    with pytest.raises(ValidationError):
        service._parse_and_validate(raw_response)


# ============================================================================
# generate_feedback 통합 테스트
# ============================================================================


@pytest.mark.asyncio
async def test_generate_feedback_openai_success(llm_config_openai: LLMConfig, mock_feedback_dict: dict):
    """OpenAI를 사용한 피드백 생성 성공"""
    with patch("src.services.llm_service.settings") as mock_settings:
        mock_settings.openai_api_key = "test-api-key"

        service = LLMService(config=llm_config_openai)

        with patch.object(service, "_call_openai", new_callable=AsyncMock) as mock_call:
            mock_call.return_value = json.dumps(mock_feedback_dict)

            result = await service.generate_feedback(
                task_type="independent",
                prompt="Test prompt",
                transcript="Test transcript",
                features={"delivery": {"wpm": 120}},
                tier="basic",
            )

            assert isinstance(result, FeedbackReport)
            assert result.score_band.min == 22
            mock_call.assert_called_once()


@pytest.mark.asyncio
async def test_generate_feedback_anthropic_success(llm_config_anthropic: LLMConfig, mock_feedback_dict: dict):
    """Anthropic을 사용한 피드백 생성 성공"""
    with patch("src.services.llm_service.settings") as mock_settings:
        mock_settings.anthropic_api_key = "test-api-key"

        service = LLMService(config=llm_config_anthropic)

        with patch.object(service, "_call_anthropic", new_callable=AsyncMock) as mock_call:
            mock_call.return_value = json.dumps(mock_feedback_dict)

            result = await service.generate_feedback(
                task_type="integrated",
                prompt="Test prompt",
                transcript="Test transcript",
                features={"delivery": {"wpm": 120}},
                source_reading="Reading passage",
                source_listening="Listening transcript",
                tier="premium",
            )

            assert isinstance(result, FeedbackReport)
            assert result.score_band.min == 22
            mock_call.assert_called_once()


@pytest.mark.asyncio
async def test_generate_feedback_retry_on_parse_error(llm_config_openai: LLMConfig, mock_feedback_dict: dict):
    """파싱 실패 시 재시도 로직"""
    with patch("src.services.llm_service.settings") as mock_settings:
        mock_settings.openai_api_key = "test-api-key"

        service = LLMService(config=llm_config_openai)
        service.config.max_retries = 2

        with patch.object(service, "_call_openai", new_callable=AsyncMock) as mock_call:
            # 첫 번째 호출은 잘못된 JSON 반환, 두 번째는 성공
            mock_call.side_effect = [
                "Invalid JSON",
                json.dumps(mock_feedback_dict),
            ]

            result = await service.generate_feedback(
                task_type="independent",
                prompt="Test prompt",
                transcript="Test transcript",
                features={"delivery": {"wpm": 120}},
                tier="basic",
            )

            assert isinstance(result, FeedbackReport)
            assert mock_call.call_count == 2


@pytest.mark.asyncio
async def test_generate_feedback_max_retries_exceeded(llm_config_openai: LLMConfig):
    """최대 재시도 횟수 초과"""
    with patch("src.services.llm_service.settings") as mock_settings:
        mock_settings.openai_api_key = "test-api-key"

        service = LLMService(config=llm_config_openai)
        service.config.max_retries = 2

        with patch.object(service, "_call_openai", new_callable=AsyncMock) as mock_call:
            # 모든 호출이 잘못된 JSON 반환
            mock_call.return_value = "Invalid JSON"

            with pytest.raises(RuntimeError, match="최대 재시도 횟수 초과"):
                await service.generate_feedback(
                    task_type="independent",
                    prompt="Test prompt",
                    transcript="Test transcript",
                    features={"delivery": {"wpm": 120}},
                    tier="basic",
                )

            assert mock_call.call_count == 2


@pytest.mark.asyncio
async def test_generate_feedback_unsupported_provider():
    """지원하지 않는 프로바이더"""
    config = LLMConfig(provider="openai")
    service = LLMService(config=config)

    # Bypass Pydantic validation by directly modifying the field
    service.config.provider = "unsupported_provider"  # type: ignore

    with pytest.raises(ValueError, match="지원하지 않는 provider"):
        await service.generate_feedback(
            task_type="independent",
            prompt="Test prompt",
            transcript="Test transcript",
            features={"delivery": {"wpm": 120}},
            tier="basic",
        )


# ============================================================================
# 프롬프트 생성 테스트
# ============================================================================


def test_build_system_prompt_independent_basic():
    """Independent Task, Basic Tier 시스템 프롬프트"""
    service = LLMService()
    prompt = service._build_system_prompt(task_type="independent", tier="basic")

    assert "independent" in prompt.lower()
    assert "basic" in prompt.lower()
    assert "concise" in prompt.lower()


def test_build_system_prompt_integrated_premium():
    """Integrated Task, Premium Tier 시스템 프롬프트"""
    service = LLMService()
    prompt = service._build_system_prompt(task_type="integrated", tier="premium")

    assert "integrated" in prompt.lower()
    assert "premium" in prompt.lower()
    assert "expert-level" in prompt.lower()


def test_build_user_prompt_independent():
    """Independent Task 사용자 프롬프트"""
    service = LLMService()
    prompt = service._build_user_prompt(
        task_type="independent",
        prompt="Test prompt",
        transcript="Test transcript",
        features={"delivery": {"wpm": 120}},
        tier="basic",
    )

    assert "independent" in prompt.lower()
    assert "Test prompt" in prompt
    assert "Test transcript" in prompt


def test_build_user_prompt_integrated_with_sources():
    """Integrated Task 사용자 프롬프트 (source 포함)"""
    service = LLMService()
    prompt = service._build_user_prompt(
        task_type="integrated",
        prompt="Summarize the lecture.",
        transcript="Test transcript",
        features={"delivery": {"wpm": 120}},
        source_reading="Reading passage",
        source_listening="Listening transcript",
        tier="premium",
    )

    assert "integrated" in prompt.lower()
    assert "Reading passage" in prompt
    assert "Listening transcript" in prompt
    assert "premium" in prompt.lower()
