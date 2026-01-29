"""
LLM API 통합 서비스

OpenAI GPT-4 및 Anthropic Claude API를 통합하여 구조화된 피드백을 생성합니다.
JSON 모드 출력을 강제하고, 파싱 실패 시 재시도 로직을 제공합니다.
"""

import json
import logging
from enum import Enum
from typing import Any, Literal, Optional

from anthropic import AsyncAnthropic
from openai import AsyncOpenAI
from pydantic import BaseModel, Field, ValidationError

from src.core.config import settings
from src.schemas.jobs import FeedbackReport

logger = logging.getLogger(__name__)


class LLMProvider(str, Enum):
    """LLM 제공자"""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"


class LLMConfig(BaseModel):
    """LLM 설정"""

    provider: LLMProvider = Field(
        default=LLMProvider.OPENAI,
        description="LLM 제공자 (openai/anthropic)",
    )
    model: str = Field(
        default="gpt-4o-2024-08-06",
        description="LLM 모델 이름",
    )
    temperature: float = Field(
        default=0.3,
        ge=0.0,
        le=2.0,
        description="Temperature (0.0-2.0)",
    )
    max_tokens: int = Field(
        default=4096,
        ge=256,
        le=16384,
        description="최대 토큰 수",
    )
    max_retries: int = Field(
        default=3,
        ge=1,
        le=5,
        description="재시도 최대 횟수",
    )


class LLMService:
    """
    LLM API 통합 서비스

    OpenAI GPT-4 또는 Anthropic Claude를 사용하여 TOEFL Speaking 응답에 대한
    구조화된 피드백을 생성합니다.

    Features:
        - JSON 모드 강제 출력
        - 재시도 로직 (파싱 실패 시)
        - 비동기 처리
        - 멀티 프로바이더 지원
    """

    def __init__(self, config: Optional[LLMConfig] = None) -> None:
        """
        LLM 서비스 초기화

        Args:
            config: LLM 설정 (None이면 기본값 사용)
        """
        self.config = config or LLMConfig()
        self._openai_client: Optional[AsyncOpenAI] = None
        self._anthropic_client: Optional[AsyncAnthropic] = None

    @property
    def openai_client(self) -> AsyncOpenAI:
        """OpenAI 클라이언트 (lazy initialization)"""
        if self._openai_client is None:
            if not settings.openai_api_key:
                raise ValueError("OPENAI_API_KEY가 설정되지 않았습니다.")
            self._openai_client = AsyncOpenAI(api_key=settings.openai_api_key)
        return self._openai_client

    @property
    def anthropic_client(self) -> AsyncAnthropic:
        """Anthropic 클라이언트 (lazy initialization)"""
        if self._anthropic_client is None:
            if not settings.anthropic_api_key:
                raise ValueError("ANTHROPIC_API_KEY가 설정되지 않았습니다.")
            self._anthropic_client = AsyncAnthropic(api_key=settings.anthropic_api_key)
        return self._anthropic_client

    async def generate_feedback(
        self,
        task_type: Literal["independent", "integrated"],
        prompt: str,
        transcript: str,
        features: dict[str, Any],
        source_reading: Optional[str] = None,
        source_listening: Optional[str] = None,
        tier: Literal["basic", "standard", "premium"] = "basic",
    ) -> FeedbackReport:
        """
        TOEFL Speaking 응답에 대한 구조화된 피드백 생성

        Args:
            task_type: 문제 유형 (independent/integrated)
            prompt: 질문 텍스트
            transcript: Whisper ASR 결과
            features: Feature 추출 결과 (delivery, language, structure 신호)
            source_reading: 통합형 문제용 읽기 지문 (선택)
            source_listening: 통합형 문제용 듣기 지문 (선택)

        Returns:
            FeedbackReport: 구조화된 피드백 리포트

        Raises:
            ValueError: API 키 미설정 또는 잘못된 provider
            RuntimeError: 최대 재시도 횟수 초과
        """
        # LLM 프롬프트 생성
        system_prompt = self._build_system_prompt(task_type, tier)
        user_prompt = self._build_user_prompt(
            task_type=task_type,
            prompt=prompt,
            transcript=transcript,
            features=features,
            source_reading=source_reading,
            source_listening=source_listening,
            tier=tier,
        )

        # 재시도 로직 (최대 max_retries회)
        for attempt in range(1, self.config.max_retries + 1):
            try:
                logger.info(f"LLM 피드백 생성 시도 {attempt}/{self.config.max_retries}")

                # Provider별 호출
                if self.config.provider == LLMProvider.OPENAI:
                    raw_response = await self._call_openai(system_prompt, user_prompt)
                elif self.config.provider == LLMProvider.ANTHROPIC:
                    raw_response = await self._call_anthropic(system_prompt, user_prompt)
                else:
                    raise ValueError(f"지원하지 않는 provider: {self.config.provider}")

                # JSON 파싱 및 Pydantic 검증
                report = self._parse_and_validate(raw_response)

                logger.info("LLM 피드백 생성 성공")
                return report

            except (json.JSONDecodeError, ValidationError) as e:
                logger.warning(f"파싱 실패 (시도 {attempt}/{self.config.max_retries}): {e}")
                if attempt == self.config.max_retries:
                    raise RuntimeError(
                        f"최대 재시도 횟수 초과 ({self.config.max_retries}회): {e}"
                    ) from e
                continue

            except Exception as e:
                logger.error(f"LLM API 호출 실패: {e}")
                raise

        # 이 라인은 도달하지 않음 (타입 체커를 위한 fallback)
        raise RuntimeError("예상치 못한 오류 발생")

    async def _call_openai(self, system_prompt: str, user_prompt: str) -> str:
        """
        OpenAI API 호출 (JSON 모드 강제)

        Args:
            system_prompt: 시스템 프롬프트
            user_prompt: 사용자 프롬프트

        Returns:
            JSON 문자열 응답
        """
        response = await self.openai_client.chat.completions.create(
            model=self.config.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
            response_format={"type": "json_object"},  # JSON 모드 강제
        )

        content = response.choices[0].message.content
        if content is None:
            raise RuntimeError("OpenAI 응답 내용이 비어있습니다.")

        return content

    async def _call_anthropic(self, system_prompt: str, user_prompt: str) -> str:
        """
        Anthropic API 호출

        Args:
            system_prompt: 시스템 프롬프트
            user_prompt: 사용자 프롬프트

        Returns:
            JSON 문자열 응답
        """
        # Anthropic은 JSON 모드가 없으므로 프롬프트에 명시
        enhanced_user_prompt = f"{user_prompt}\n\n**중요**: 반드시 유효한 JSON 형식으로만 응답하세요."

        response = await self.anthropic_client.messages.create(
            model=self.config.model,
            max_tokens=self.config.max_tokens,
            temperature=self.config.temperature,
            system=system_prompt,
            messages=[{"role": "user", "content": enhanced_user_prompt}],
        )

        # Anthropic 응답에서 텍스트 추출
        content_block = response.content[0]
        if hasattr(content_block, "text"):
            return content_block.text
        else:
            raise RuntimeError("Anthropic 응답 형식이 올바르지 않습니다.")

    def _parse_and_validate(self, raw_response: str) -> FeedbackReport:
        """
        JSON 파싱 및 Pydantic 검증

        Args:
            raw_response: LLM 원본 응답 (JSON 문자열)

        Returns:
            FeedbackReport: 검증된 피드백 리포트

        Raises:
            json.JSONDecodeError: JSON 파싱 실패
            ValidationError: Pydantic 검증 실패
        """
        # JSON 파싱
        data = json.loads(raw_response)

        # Pydantic 모델 검증
        report = FeedbackReport.model_validate(data)

        return report

    def _build_system_prompt(
        self,
        task_type: Literal["independent", "integrated"],
        tier: Literal["basic", "standard", "premium"] = "basic",
    ) -> str:
        """
        시스템 프롬프트 생성

        Args:
            task_type: 문제 유형 (independent/integrated)
            tier: 피드백 티어 (basic/standard/premium)

        Returns:
            시스템 프롬프트 문자열
        """
        tier_instructions = {
            "basic": "Provide concise feedback focusing on key points only.",
            "standard": "Provide detailed feedback with analysis and actionable recommendations.",
            "premium": "Provide expert-level detailed feedback with comprehensive analysis, examples, and personalized improvement strategies.",
        }

        return f"""You are an expert TOEFL Speaking evaluator specializing in {task_type} tasks.

Feedback Level: {tier.upper()}
{tier_instructions[tier]}

Your role:
- Analyze the user's speaking response based on TOEFL rubric criteria
- Provide actionable feedback focusing on the SINGLE BIGGEST bottleneck
- Generate a score range (min-max) with clear rationale
- Present feedback in a structured JSON format

TOEFL Speaking Rubric (0-4 scale per question, scaled to 0-30):
- **Delivery**: Speech clarity, pace (WPM), pauses, pronunciation
- **Language Use**: Grammar accuracy, vocabulary range, sentence complexity
- **Topic Development**: Addressing prompt, logical structure, examples

Key Principles:
1. **Focus on ONE bottleneck**: Identify the single most impactful issue reducing the score
2. **Actionable items**: Provide 1-2 concrete actions the user can apply immediately
3. **Score range**: Estimate min-max score (e.g., 22-25) instead of a single number
4. **Evidence-based**: Quote specific transcript segments to support your analysis

Output Format: Valid JSON matching the FeedbackReport schema.
"""

    def _build_user_prompt(
        self,
        task_type: Literal["independent", "integrated"],
        prompt: str,
        transcript: str,
        features: dict[str, Any],
        source_reading: Optional[str] = None,
        source_listening: Optional[str] = None,
        tier: Literal["basic", "standard", "premium"] = "basic",
    ) -> str:
        """
        사용자 프롬프트 생성

        Args:
            task_type: 문제 유형
            prompt: 질문 텍스트
            transcript: Whisper 결과
            features: Feature 추출 결과
            source_reading: 읽기 지문 (통합형)
            source_listening: 듣기 지문 (통합형)

        Returns:
            사용자 프롬프트 문자열
        """
        # 기본 정보
        prompt_text = f"""**Task Type**: {task_type}

**Prompt**:
{prompt}
"""

        # 통합형 문제인 경우 source 추가
        if task_type == "integrated":
            if source_reading:
                prompt_text += f"""
**Source Reading**:
{source_reading}
"""
            if source_listening:
                prompt_text += f"""
**Source Listening**:
{source_listening}
"""

        # Transcript 및 Features
        prompt_text += f"""
**Transcript**:
{transcript}

**Extracted Features**:
```json
{json.dumps(features, indent=2, ensure_ascii=False)}
```

**Feedback Tier**: {tier}
- Basic: Overall score, band, 3-line summary, top 2 strengths, top 2 improvements
- Standard: Basic + dimension scores, feature analysis summary, blueprint/structure coverage %
- Premium: Standard + full feature analysis (20 features), unit/component details, comparison to sample, history context

---

Please analyze this response and generate a complete feedback report in JSON format with the following structure:

{{
  "summary_3lines": [
    "Current level position (e.g., 'Your response shows intermediate-level skills...')",
    "Biggest penalty factor (e.g., 'Main issue: Lack of clear structure...')",
    "Overall assessment (e.g., 'With improved organization, you could reach...')"
  ],
  "bottleneck": {{
    "title": "Brief title (e.g., '구조 부재')",
    "explanation": "Why this is the biggest issue",
    "evidence_quote": "Direct quote from transcript"
  }},
  "action_items": [
    {{
      "action": "Specific action to take",
      "why": "Why this helps",
      "how_to": "How to implement",
      "example_sentence": "Example sentence to use"
    }}
  ],
  "structure": {{
    "checklist": {{"Intro": true/false, "Reason1": true/false, "Example1": true/false, "Reason2": true/false, "Example2": true/false, "Wrap-up": true/false}},
    "missing": ["List of missing elements"],
    "suggested_template": "Recommended template (e.g., 'Intro → Reason1 → Example1 → Reason2 → Example2 → Wrap-up')"
  }},
  "language": {{
    "top_errors": ["Error type 1 (count)", "Error type 2 (count)"],
    "improved_sentences": ["Original → Corrected"]
  }},
  "delivery": {{
    "speed_comment": "Comment on speaking speed (based on WPM feature)",
    "pause_comment": "Comment on pauses and silence (based on silence_ratio feature)",
    "clarity_comment": "Comment on pronunciation clarity (based on ASR confidence)"
  }},
  "score_band": {{
    "min": 15,
    "max": 20,
    "rationale": "Explanation for the score range"
  }},
  "disclaimer": "본 평가는 학습 도구이며 실제 TOEFL 점수와 다를 수 있습니다."
}}
"""

        return prompt_text
