"""Vocabulary Feature 추출 서비스

SPEC-TOEFL-FEATURE-001: ETS SpeechRater v5.0 Vocabulary Features
- cvamax: TF-IDF + cosine similarity (transcript vs reference)
- types: Unique word count (lexical diversity)
- logFreq: Average log frequency

Requirements:
- scikit-learn for TF-IDF
- nltk for word frequency
- Python 3.9+ compatibility
"""

import logging
import math
import re
from typing import List, Optional, Set

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# scikit-learn 가용성 확인
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity

    SKLEARN_AVAILABLE = True
    logger.info("scikit-learn is available for TF-IDF computation")
except ImportError:
    SKLEARN_AVAILABLE = False
    logger.warning("scikit-learn is not installed. cvamax will return None.")

# nltk 가용성 확인
try:
    import nltk
    from nltk.corpus import brown

    NLTK_AVAILABLE = True
    logger.info("nltk is available for word frequency analysis")
except ImportError:
    NLTK_AVAILABLE = False
    logger.warning("nltk is not installed. logFreq will use fallback method.")


class VocabularyFeatures(BaseModel):
    """Vocabulary 신호 (어휘 특징)"""

    cvamax: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="TF-IDF 기반 Content Vector Analysis 유사도 (0.0-1.0)",
    )
    types: int = Field(
        default=0,
        ge=0,
        description="고유 단어 수 (Lexical diversity)",
    )
    logFreq: Optional[float] = Field(
        default=None,
        description="평균 log frequency (낮을수록 고급 어휘)",
    )
    sklearn_available: bool = Field(
        default=False,
        description="scikit-learn 가용성 여부",
    )
    nltk_available: bool = Field(
        default=False,
        description="nltk 가용성 여부",
    )


class VocabularyFeatureExtractor:
    """
    Vocabulary 신호 추출기

    TF-IDF와 word frequency를 사용하여 어휘 특징을 추출합니다.
    - TF-IDF 기반 content similarity
    - Unique word count (lexical diversity)
    - Log frequency (어휘 난이도)
    """

    def __init__(self) -> None:
        """추출기 초기화"""
        self._word_freq_cache: Optional[dict] = None
        if NLTK_AVAILABLE:
            try:
                # Brown corpus 다운로드 시도
                self._word_freq_cache = self._build_word_freq_dict()
                logger.info("nltk Brown corpus loaded for word frequency")
            except Exception as e:
                logger.warning(f"Failed to load Brown corpus: {e}")
                self._word_freq_cache = None

    def extract(
        self, transcript: str, reference_text: Optional[str] = None
    ) -> VocabularyFeatures:
        """
        Transcript에서 Vocabulary 신호 추출

        Args:
            transcript: Whisper ASR 결과 텍스트
            reference_text: 참조 텍스트 (CVA 계산용, Optional)

        Returns:
            VocabularyFeatures: 추출된 어휘 신호
        """
        logger.info("Extracting vocabulary features")

        # 1. cvamax: TF-IDF 유사도
        cvamax = self._calculate_cvamax(transcript, reference_text)

        # 2. types: 고유 단어 수
        types = self._count_unique_words(transcript)

        # 3. logFreq: 평균 log frequency
        logFreq = self._calculate_log_frequency(transcript)

        return VocabularyFeatures(
            cvamax=cvamax,
            types=types,
            logFreq=logFreq,
            sklearn_available=SKLEARN_AVAILABLE,
            nltk_available=NLTK_AVAILABLE and self._word_freq_cache is not None,
        )

    def _calculate_cvamax(
        self, transcript: str, reference_text: Optional[str]
    ) -> Optional[float]:
        """
        TF-IDF 기반 Content Vector Analysis (CVA) 유사도 계산

        Args:
            transcript: 사용자 응답
            reference_text: 참조 텍스트 (Optional)

        Returns:
            코사인 유사도 (0.0-1.0) 또는 None
        """
        if not SKLEARN_AVAILABLE or reference_text is None or not reference_text.strip():
            return None

        try:
            # TF-IDF 벡터화
            vectorizer = TfidfVectorizer(
                lowercase=True,
                stop_words="english",
                max_features=1000,
            )

            # 두 텍스트의 TF-IDF 벡터 생성
            tfidf_matrix = vectorizer.fit_transform([transcript, reference_text])

            # 코사인 유사도 계산
            similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]

            return round(float(similarity), 3)
        except Exception as e:
            logger.warning(f"Failed to calculate cvamax: {e}")
            return None

    def _count_unique_words(self, transcript: str) -> int:
        """
        고유 단어 수 계산 (Lexical diversity)

        Args:
            transcript: 텍스트

        Returns:
            고유 단어 수
        """
        # 알파벳만 추출하여 소문자로 변환
        words = re.findall(r"\b[a-zA-Z]+\b", transcript.lower())
        unique_words: Set[str] = set(words)
        return len(unique_words)

    def _calculate_log_frequency(self, transcript: str) -> Optional[float]:
        """
        평균 log frequency 계산

        낮은 값일수록 고급 어휘 사용을 의미합니다.

        Args:
            transcript: 텍스트

        Returns:
            평균 log frequency 또는 None
        """
        words = re.findall(r"\b[a-zA-Z]+\b", transcript.lower())

        if not words:
            return None

        if NLTK_AVAILABLE and self._word_freq_cache is not None:
            # Brown corpus 기반 frequency 사용
            log_freqs = []
            for word in words:
                freq = self._word_freq_cache.get(word, 1)  # 없으면 최소값 1
                log_freq = math.log10(freq + 1)  # +1 to avoid log(0)
                log_freqs.append(log_freq)

            avg_log_freq = sum(log_freqs) / len(log_freqs)
            return round(avg_log_freq, 3)
        else:
            # Fallback: 단순 어휘 길이 기반 추정
            # 긴 단어일수록 고급 어휘로 간주
            avg_word_length = sum(len(word) for word in words) / len(words)
            # Normalize to log scale (역수 사용: 긴 단어 = 낮은 frequency)
            estimated_log_freq = round(3.0 - (avg_word_length / 10.0), 3)
            return max(0.0, estimated_log_freq)

    def _build_word_freq_dict(self) -> dict:
        """
        Brown corpus에서 word frequency dictionary 생성

        Returns:
            {word: frequency} dictionary
        """
        try:
            # Brown corpus 단어 빈도 계산
            from collections import Counter

            brown_words = [word.lower() for word in brown.words()]
            freq_dist = Counter(brown_words)
            return dict(freq_dist)
        except Exception as e:
            logger.error(f"Failed to build word frequency dict: {e}")
            # Try to download brown corpus
            try:
                nltk.download("brown", quiet=True)
                brown_words = [word.lower() for word in brown.words()]
                from collections import Counter

                freq_dist = Counter(brown_words)
                return dict(freq_dist)
            except Exception:
                return {}


# 싱글톤 인스턴스
_extractor: Optional[VocabularyFeatureExtractor] = None


def get_vocabulary_feature_extractor() -> VocabularyFeatureExtractor:
    """Vocabulary Feature Extractor 싱글톤 인스턴스 반환"""
    global _extractor
    if _extractor is None:
        _extractor = VocabularyFeatureExtractor()
    return _extractor
