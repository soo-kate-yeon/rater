"""
Topic/Structure 신호 추출 서비스

Transcript에서 답변 구조, 프롬프트 충족도, 연결어 사용, 구체성을 분석합니다.
"""

import logging
import re
from typing import Any

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class StructureFeatures(BaseModel):
    """Structure 신호"""

    prompt_coverage: bool = Field(
        default=False,
        description="프롬프트 질문 충족 여부",
    )
    structure_checklist: dict[str, bool] = Field(
        default_factory=dict,
        description="TOEFL 템플릿 체크리스트 (Intro, Reason1, Example1, Reason2, Example2, Wrap-up)",
    )
    coherence_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="연결어 사용 점수 (0.0-1.0)",
    )
    specificity_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="구체성 점수 (0.0-1.0)",
    )


class StructureFeaturesExtractor:
    """
    Structure 신호 추출기

    Transcript를 분석하여 답변 구조 특징을 추출합니다.
    - 프롬프트 키워드 매칭
    - TOEFL 템플릿 요소 감지 (Intro, Reason, Example, Conclusion)
    - 연결어 (discourse markers) 사용 빈도
    - 구체적 예시 포함 여부
    """

    # TOEFL Speaking 템플릿 요소 감지 패턴
    INTRO_PATTERNS = [
        r"\b(in my opinion|i think|i believe|personally)\b",
        r"\b(for two reasons|there are two reasons)\b",
    ]

    REASON_PATTERNS = [
        r"\b(first|firstly|second|secondly|to begin with|another reason)\b",
        r"\b(because|since|as)\b",
    ]

    EXAMPLE_PATTERNS = [
        r"\b(for example|for instance|such as|like)\b",
        r"\b(when i|in my experience|one time|once)\b",
    ]

    CONCLUSION_PATTERNS = [
        r"\b(in conclusion|to sum up|overall|that's why|therefore)\b",
        r"\b(that is why|so that's|in summary)\b",
    ]

    # 연결어 리스트
    COHERENCE_MARKERS = [
        "first",
        "firstly",
        "second",
        "secondly",
        "also",
        "furthermore",
        "moreover",
        "however",
        "on the other hand",
        "for example",
        "for instance",
        "in conclusion",
        "to sum up",
        "therefore",
        "thus",
    ]

    # 구체성 키워드 (예시, 경험 표현)
    SPECIFICITY_KEYWORDS = [
        "for example",
        "for instance",
        "when i",
        "in my experience",
        "one time",
        "once",
        "specifically",
        "such as",
    ]

    def extract(self, transcript: str, prompt: str) -> StructureFeatures:
        """
        Transcript에서 Structure 신호 추출

        Args:
            transcript: Whisper ASR 결과 텍스트
            prompt: 질문 텍스트

        Returns:
            StructureFeatures: 추출된 구조 신호
        """
        # 소문자 변환 (패턴 매칭용)
        transcript_lower = transcript.lower()
        prompt_lower = prompt.lower()

        # 1. 프롬프트 충족도
        prompt_coverage = self._check_prompt_coverage(transcript_lower, prompt_lower)

        # 2. 구조 체크리스트
        structure_checklist = self._check_structure_elements(transcript_lower)

        # 3. Coherence 점수 (연결어 사용)
        coherence_score = self._calculate_coherence_score(transcript_lower)

        # 4. Specificity 점수 (구체성)
        specificity_score = self._calculate_specificity_score(transcript_lower)

        logger.info(
            f"Structure features extracted: prompt_coverage={prompt_coverage}, "
            f"coherence={coherence_score:.2f}, specificity={specificity_score:.2f}"
        )

        return StructureFeatures(
            prompt_coverage=prompt_coverage,
            structure_checklist=structure_checklist,
            coherence_score=round(coherence_score, 2),
            specificity_score=round(specificity_score, 2),
        )

    def _check_prompt_coverage(self, transcript: str, prompt: str) -> bool:
        """
        프롬프트 키워드 매칭 여부 확인

        Args:
            transcript: 응답 텍스트 (소문자)
            prompt: 질문 텍스트 (소문자)

        Returns:
            키워드 3개 이상 매칭되면 True
        """
        # 프롬프트에서 의미있는 단어 추출 (stopwords 제거)
        stopwords = {"a", "an", "the", "is", "are", "do", "you", "think", "what", "why", "how"}
        prompt_words = set(re.findall(r"\b[a-z]{3,}\b", prompt))  # 3글자 이상
        prompt_keywords = prompt_words - stopwords

        # Transcript에서 키워드 매칭 카운트
        matched = sum(1 for keyword in prompt_keywords if keyword in transcript)

        # 3개 이상 매칭되면 충족
        coverage = matched >= min(3, len(prompt_keywords))
        return coverage

    def _check_structure_elements(self, transcript: str) -> dict[str, bool]:
        """
        TOEFL 템플릿 요소 감지

        Args:
            transcript: 응답 텍스트 (소문자)

        Returns:
            구조 체크리스트 딕셔너리
        """
        checklist = {
            "Intro": self._has_patterns(transcript, self.INTRO_PATTERNS),
            "Reason1": self._has_patterns(transcript, self.REASON_PATTERNS),
            "Example1": self._has_patterns(transcript, self.EXAMPLE_PATTERNS),
            "Reason2": False,  # 2개 이상의 reason 감지는 복잡하므로 단순화
            "Example2": False,  # 2개 이상의 example 감지는 복잡하므로 단순화
            "Wrap-up": self._has_patterns(transcript, self.CONCLUSION_PATTERNS),
        }

        # Reason과 Example이 각각 2회 이상 나타나는지 간단히 체크
        reason_count = sum(1 for pattern in self.REASON_PATTERNS if re.search(pattern, transcript))
        example_count = sum(
            1 for pattern in self.EXAMPLE_PATTERNS if re.search(pattern, transcript)
        )

        if reason_count >= 2:
            checklist["Reason2"] = True
        if example_count >= 2:
            checklist["Example2"] = True

        return checklist

    def _has_patterns(self, text: str, patterns: list[str]) -> bool:
        """
        패턴 리스트 중 하나라도 매칭되는지 확인

        Args:
            text: 텍스트
            patterns: 정규식 패턴 리스트

        Returns:
            매칭되면 True
        """
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False

    def _calculate_coherence_score(self, transcript: str) -> float:
        """
        연결어 사용 점수 계산

        Args:
            transcript: 응답 텍스트 (소문자)

        Returns:
            Coherence 점수 (0.0-1.0)
        """
        # 연결어 출현 카운트
        marker_count = sum(1 for marker in self.COHERENCE_MARKERS if marker in transcript)

        # 점수: 연결어 3개 이상이면 1.0, 0개면 0.0
        score = min(marker_count / 3, 1.0)
        return score

    def _calculate_specificity_score(self, transcript: str) -> float:
        """
        구체성 점수 계산

        Args:
            transcript: 응답 텍스트 (소문자)

        Returns:
            Specificity 점수 (0.0-1.0)
        """
        # 구체성 키워드 출현 카운트
        keyword_count = sum(1 for keyword in self.SPECIFICITY_KEYWORDS if keyword in transcript)

        # 점수: 키워드 2개 이상이면 1.0, 0개면 0.0
        score = min(keyword_count / 2, 1.0)
        return score


def extract_structure_features(transcript: str, prompt: str) -> dict[str, Any]:
    """
    Structure Features 추출 헬퍼 함수

    Args:
        transcript: Whisper ASR 결과 텍스트
        prompt: 질문 텍스트

    Returns:
        Structure Features 딕셔너리
    """
    extractor = StructureFeaturesExtractor()
    features = extractor.extract(transcript, prompt)
    return features.model_dump()
