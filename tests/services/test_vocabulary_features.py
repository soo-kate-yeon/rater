"""Vocabulary Features 추출 서비스 테스트"""

import pytest
import pytest_asyncio

from src.services.vocabulary_features import (
    NLTK_AVAILABLE,
    SKLEARN_AVAILABLE,
    VocabularyFeatureExtractor,
    VocabularyFeatures,
    get_vocabulary_feature_extractor,
)


@pytest_asyncio.fixture
def extractor() -> VocabularyFeatureExtractor:
    """Vocabulary feature extractor 인스턴스"""
    return VocabularyFeatureExtractor()


@pytest_asyncio.fixture
def sample_transcript() -> str:
    """샘플 transcript"""
    return (
        "I believe education is crucial for personal development. "
        "Learning new skills helps individuals grow professionally and personally."
    )


@pytest_asyncio.fixture
def reference_text() -> str:
    """참조 텍스트"""
    return (
        "Education plays a vital role in shaping individuals. "
        "Acquiring knowledge and skills contributes to professional growth."
    )


class TestVocabularyFeatureExtractorBasicBehavior:
    """기본 동작 테스트"""

    def test_extract_basic_features(
        self, extractor: VocabularyFeatureExtractor, sample_transcript: str
    ):
        """기본 features 추출"""
        result = extractor.extract(sample_transcript)

        assert isinstance(result, VocabularyFeatures)
        assert result.types > 0  # 고유 단어 수가 계산됨
        assert result.sklearn_available == SKLEARN_AVAILABLE
        assert result.nltk_available == (NLTK_AVAILABLE and extractor._word_freq_cache is not None)

    def test_unique_word_count(self, extractor: VocabularyFeatureExtractor):
        """고유 단어 수 계산"""
        # 단순 문장
        result = extractor.extract("The cat sat on the mat.")
        assert result.types == 5  # the, cat, sat, on, mat

        # 중복 단어
        result = extractor.extract("I think I can do it.")
        assert result.types == 5  # i, think, can, do, it

    def test_empty_transcript(self, extractor: VocabularyFeatureExtractor):
        """빈 transcript 처리"""
        result = extractor.extract("")

        assert result.types == 0
        assert result.cvamax is None
        assert result.logFreq is None

    def test_singleton_pattern(self):
        """싱글톤 패턴"""
        instance1 = get_vocabulary_feature_extractor()
        instance2 = get_vocabulary_feature_extractor()

        assert instance1 is instance2


@pytest.mark.skipif(not SKLEARN_AVAILABLE, reason="scikit-learn not installed")
class TestVocabularyFeatureExtractorWithSklearn:
    """scikit-learn이 설치된 경우의 테스트"""

    def test_cvamax_calculation(
        self,
        extractor: VocabularyFeatureExtractor,
        sample_transcript: str,
        reference_text: str,
    ):
        """TF-IDF 기반 CVA 유사도 계산"""
        result = extractor.extract(sample_transcript, reference_text)

        # 유사도가 계산됨
        assert result.cvamax is not None
        assert 0.0 <= result.cvamax <= 1.0

    def test_cvamax_similar_texts(self, extractor: VocabularyFeatureExtractor):
        """유사한 텍스트의 cvamax는 높음"""
        text1 = "Education is important for learning."
        text2 = "Learning is crucial for education."

        result = extractor.extract(text1, text2)

        # 유사한 텍스트이므로 높은 유사도
        assert result.cvamax is not None
        assert result.cvamax > 0.3  # 관련 단어가 많으므로

    def test_cvamax_different_texts(self, extractor: VocabularyFeatureExtractor):
        """다른 주제의 텍스트의 cvamax는 낮음"""
        text1 = "I love playing soccer and basketball."
        text2 = "Cooking delicious meals requires proper ingredients."

        result = extractor.extract(text1, text2)

        # 다른 주제이므로 낮은 유사도
        assert result.cvamax is not None
        assert result.cvamax < 0.5

    def test_cvamax_without_reference(
        self, extractor: VocabularyFeatureExtractor, sample_transcript: str
    ):
        """참조 텍스트 없이 호출 시 None 반환"""
        result = extractor.extract(sample_transcript, None)

        assert result.cvamax is None


class TestVocabularyFeatureExtractorLogFrequency:
    """Log frequency 계산 테스트"""

    def test_log_frequency_simple_words(self, extractor: VocabularyFeatureExtractor):
        """간단한 단어의 log frequency"""
        # 흔한 단어들
        common_text = "I am a cat and dog."
        result = extractor.extract(common_text)

        assert result.logFreq is not None

    def test_log_frequency_complex_words(self, extractor: VocabularyFeatureExtractor):
        """복잡한 단어의 log frequency"""
        # 복잡한 단어들
        complex_text = "The phenomenon demonstrates unprecedented implications."
        result = extractor.extract(complex_text)

        assert result.logFreq is not None

    def test_log_frequency_empty(self, extractor: VocabularyFeatureExtractor):
        """빈 텍스트의 log frequency는 None"""
        result = extractor.extract("")

        assert result.logFreq is None


class TestVocabularyFeaturesSchema:
    """VocabularyFeatures 스키마 테스트"""

    def test_schema_validation(self):
        """스키마 유효성 검사"""
        features = VocabularyFeatures(
            cvamax=0.85,
            types=42,
            logFreq=2.5,
            sklearn_available=True,
            nltk_available=True,
        )

        assert features.cvamax == 0.85
        assert features.types == 42
        assert features.logFreq == 2.5
        assert features.sklearn_available is True
        assert features.nltk_available is True

    def test_schema_with_none_values(self):
        """None 값을 가진 스키마"""
        features = VocabularyFeatures(
            cvamax=None,
            types=10,
            logFreq=None,
            sklearn_available=False,
            nltk_available=False,
        )

        assert features.cvamax is None
        assert features.types == 10
        assert features.logFreq is None

    def test_schema_default_values(self):
        """기본값 테스트"""
        features = VocabularyFeatures()

        assert features.cvamax is None
        assert features.types == 0
        assert features.logFreq is None
        assert features.sklearn_available is False
        assert features.nltk_available is False

    def test_schema_cvamax_bounds(self):
        """cvamax 범위 검증 (0.0-1.0)"""
        # 유효한 값
        features = VocabularyFeatures(cvamax=0.5)
        assert features.cvamax == 0.5

        # 경계값
        features = VocabularyFeatures(cvamax=0.0)
        assert features.cvamax == 0.0

        features = VocabularyFeatures(cvamax=1.0)
        assert features.cvamax == 1.0

        # 범위 밖 값은 에러
        with pytest.raises(Exception):
            VocabularyFeatures(cvamax=1.5)

        with pytest.raises(Exception):
            VocabularyFeatures(cvamax=-0.1)


class TestVocabularyFeatureExtractorEdgeCases:
    """Edge cases 테스트"""

    def test_only_punctuation(self, extractor: VocabularyFeatureExtractor):
        """구두점만 있는 텍스트"""
        result = extractor.extract("!!! ??? ... ,,,")

        assert result.types == 0
        assert result.logFreq is None

    def test_mixed_case(self, extractor: VocabularyFeatureExtractor):
        """대소문자 혼합 (case-insensitive)"""
        result = extractor.extract("Hello HELLO hello")

        # 대소문자 무시하므로 1개 단어
        assert result.types == 1

    def test_numbers_ignored(self, extractor: VocabularyFeatureExtractor):
        """숫자는 무시됨"""
        result = extractor.extract("I have 123 cats and 456 dogs.")

        # 숫자 제외: i, have, cats, and, dogs
        assert result.types == 5

    def test_contractions(self, extractor: VocabularyFeatureExtractor):
        """축약형 처리"""
        result = extractor.extract("I'm doesn't can't won't.")

        # m, doesn, t, can, t, won, t (축약형이 분리됨)
        # i, m, doesn, t, can, won (고유 단어)
        assert result.types >= 4
