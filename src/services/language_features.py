"""
Language Use 신호 추출 서비스

Transcript에서 문법 오류, 어휘 다양성, 문장 복잡도, 반복 표현을 분석합니다.
"""

import logging
import re
from collections import Counter
from typing import Any

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class LanguageFeatures(BaseModel):
    """Language Use 신호"""

    error_types: list[str] = Field(
        default_factory=list,
        description="감지된 오류 유형 (시제/수일치/관사/전치사)",
    )
    error_density: float = Field(
        default=0.0,
        ge=0.0,
        description="오류 밀도 (오류 수 / 100단어)",
    )
    lexical_diversity: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Type-Token Ratio (0.0-1.0)",
    )
    avg_sentence_length: float = Field(
        default=0.0,
        ge=0.0,
        description="평균 문장 길이 (단어 수)",
    )
    repetition_ratio: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="반복 표현 비율 (0.0-1.0)",
    )


class LanguageFeaturesExtractor:
    """
    Language Use 신호 추출기

    Transcript를 분석하여 언어 사용 특징을 추출합니다.
    - 문법 오류 패턴 감지 (규칙 기반)
    - 어휘 다양성 (TTR)
    - 문장 복잡도
    - 반복 표현 비율
    """

    # 오류 패턴 (단순 규칙 기반 - 실제로는 더 정교한 NLP 필요)
    ERROR_PATTERNS = {
        "시제 불일치": [
            r"\b(I|He|She)\s+go\b",  # I go yesterday (should be went)
            r"\b(yesterday|last\s+\w+).*\b(is|am|are)\b",  # yesterday is (should be was)
        ],
        "수일치 오류": [
            r"\b(He|She|It)\s+(are|have)\b",  # He are (should be is)
            r"\b(They|We)\s+(is|has)\b",  # They is (should be are)
        ],
        "관사 누락": [
            r"\b(have|has)\s+(experience|idea|opinion)\b",  # have experience (should be an experience)
        ],
        "전치사 오류": [
            r"\bgo\s+to\s+home\b",  # go to home (should be go home)
            r"\barrived\s+to\b",  # arrived to (should be arrived at)
        ],
    }

    def extract(self, transcript: str) -> LanguageFeatures:
        """
        Transcript에서 Language Use 신호 추출

        Args:
            transcript: Whisper ASR 결과 텍스트

        Returns:
            LanguageFeatures: 추출된 언어 사용 신호
        """
        # 기본 전처리
        cleaned_transcript = self._preprocess(transcript)

        # 단어 및 문장 분리
        words = self._tokenize_words(cleaned_transcript)
        sentences = self._tokenize_sentences(cleaned_transcript)

        # 1. 오류 유형 감지
        error_types = self._detect_error_types(cleaned_transcript)

        # 2. 오류 밀도 (오류 수 / 100단어)
        error_count = len(error_types)
        word_count = len(words)
        error_density = (error_count / word_count * 100) if word_count > 0 else 0.0

        # 3. Lexical Diversity (TTR)
        lexical_diversity = self._calculate_ttr(words)

        # 4. 평균 문장 길이
        avg_sentence_length = self._calculate_avg_sentence_length(sentences, words)

        # 5. 반복 표현 비율
        repetition_ratio = self._calculate_repetition_ratio(words)

        logger.info(
            f"Language features extracted: errors={error_count}, "
            f"TTR={lexical_diversity:.3f}, avg_sent_len={avg_sentence_length:.1f}"
        )

        return LanguageFeatures(
            error_types=error_types,
            error_density=round(error_density, 2),
            lexical_diversity=round(lexical_diversity, 3),
            avg_sentence_length=round(avg_sentence_length, 1),
            repetition_ratio=round(repetition_ratio, 3),
        )

    def _preprocess(self, text: str) -> str:
        """텍스트 전처리 (소문자 변환, 공백 정리)"""
        text = text.strip()
        text = re.sub(r"\s+", " ", text)  # 연속 공백 제거
        return text

    def _tokenize_words(self, text: str) -> list[str]:
        """단어 토큰화 (알파벳 단어만 추출)"""
        words = re.findall(r"\b[a-zA-Z]+\b", text.lower())
        return words

    def _tokenize_sentences(self, text: str) -> list[str]:
        """문장 토큰화 (마침표, 느낌표, 물음표 기준)"""
        sentences = re.split(r"[.!?]+", text)
        sentences = [s.strip() for s in sentences if s.strip()]
        return sentences

    def _detect_error_types(self, text: str) -> list[str]:
        """
        문법 오류 유형 감지 (규칙 기반)

        Args:
            text: 전처리된 텍스트

        Returns:
            감지된 오류 유형 리스트
        """
        detected_errors = []

        for error_type, patterns in self.ERROR_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    detected_errors.append(error_type)
                    break  # 동일 유형은 1회만 카운트

        return detected_errors

    def _calculate_ttr(self, words: list[str]) -> float:
        """
        Type-Token Ratio (TTR) 계산

        Args:
            words: 단어 리스트

        Returns:
            TTR 값 (0.0-1.0)
        """
        if not words:
            return 0.0

        unique_words = set(words)
        ttr = len(unique_words) / len(words)
        return ttr

    def _calculate_avg_sentence_length(self, sentences: list[str], words: list[str]) -> float:
        """
        평균 문장 길이 계산

        Args:
            sentences: 문장 리스트
            words: 전체 단어 리스트

        Returns:
            평균 문장 길이 (단어 수)
        """
        if not sentences:
            return 0.0

        avg_length = len(words) / len(sentences)
        return avg_length

    def _calculate_repetition_ratio(self, words: list[str]) -> float:
        """
        반복 표현 비율 계산

        Args:
            words: 단어 리스트

        Returns:
            반복 비율 (0.0-1.0)
        """
        if not words:
            return 0.0

        # 2회 이상 나타나는 단어 카운트
        word_counts = Counter(words)
        repeated_words = [word for word, count in word_counts.items() if count >= 2]

        # 반복 단어의 전체 출현 횟수
        repeated_count = sum(word_counts[word] for word in repeated_words)

        repetition_ratio = repeated_count / len(words)
        return repetition_ratio


def extract_language_features(transcript: str) -> dict[str, Any]:
    """
    Language Features 추출 헬퍼 함수

    Args:
        transcript: Whisper ASR 결과 텍스트

    Returns:
        Language Features 딕셔너리
    """
    extractor = LanguageFeaturesExtractor()
    features = extractor.extract(transcript)
    return features.model_dump()
