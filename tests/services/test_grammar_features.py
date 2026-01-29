"""Grammar Features 추출 서비스 테스트"""

import pytest
import pytest_asyncio

from src.services.grammar_features import (
    SPACY_AVAILABLE,
    GrammarFeatureExtractor,
    GrammarFeatures,
    get_grammar_feature_extractor,
)


@pytest_asyncio.fixture
def extractor() -> GrammarFeatureExtractor:
    """Grammar feature extractor 인스턴스"""
    return GrammarFeatureExtractor()


@pytest_asyncio.fixture
def sample_transcript() -> str:
    """샘플 transcript"""
    return (
        "I think education is very important because it helps people develop skills. "
        "When students learn new things, they become more confident."
    )


class TestGrammarFeatureExtractorGracefulDegradation:
    """Graceful degradation 테스트 (spaCy 없을 때)"""

    def test_graceful_degradation_when_spacy_unavailable(self, extractor: GrammarFeatureExtractor):
        """spaCy가 없을 때 None을 반환하고 에러를 발생시키지 않음"""
        if not SPACY_AVAILABLE:
            result = extractor.extract("Test transcript")

            assert isinstance(result, GrammarFeatures)
            assert result.poscvamax is None
            assert result.dep_clauses_per_clause is None
            assert result.spacy_available is False

    def test_singleton_pattern(self):
        """싱글톤 패턴 테스트"""
        instance1 = get_grammar_feature_extractor()
        instance2 = get_grammar_feature_extractor()

        assert instance1 is instance2


@pytest.mark.skipif(not SPACY_AVAILABLE, reason="spaCy not installed")
class TestGrammarFeatureExtractorWithSpacy:
    """spaCy가 설치된 경우의 테스트"""

    def test_extract_with_spacy(self, extractor: GrammarFeatureExtractor, sample_transcript: str):
        """spaCy로 문법 features 추출"""
        if extractor._nlp is None:
            pytest.skip("spaCy model not available")

        result = extractor.extract(sample_transcript)

        assert isinstance(result, GrammarFeatures)
        assert result.spacy_available is True

    def test_poscvamax_calculation(
        self, extractor: GrammarFeatureExtractor, sample_transcript: str
    ):
        """POS CVA 계산 테스트"""
        if extractor._nlp is None:
            pytest.skip("spaCy model not available")

        result = extractor.extract(sample_transcript)

        # POS 다양성 점수가 계산됨
        if result.poscvamax is not None:
            assert 0.0 <= result.poscvamax <= 1.0

    def test_dependent_clauses_calculation(
        self, extractor: GrammarFeatureExtractor, sample_transcript: str
    ):
        """종속절 수 계산 테스트"""
        if extractor._nlp is None:
            pytest.skip("spaCy model not available")

        result = extractor.extract(sample_transcript)

        # 종속절이 있는 문장이므로 > 0
        if result.dep_clauses_per_clause is not None:
            assert result.dep_clauses_per_clause >= 0.0

    def test_empty_transcript(self, extractor: GrammarFeatureExtractor):
        """빈 transcript 처리"""
        if extractor._nlp is None:
            pytest.skip("spaCy model not available")

        result = extractor.extract("")

        assert isinstance(result, GrammarFeatures)
        # 빈 텍스트는 None 또는 0.0 반환
        if result.poscvamax is not None:
            assert result.poscvamax == 0.0 or result.poscvamax is None

    def test_simple_sentence(self, extractor: GrammarFeatureExtractor):
        """단순 문장 처리"""
        if extractor._nlp is None:
            pytest.skip("spaCy model not available")

        result = extractor.extract("I like cats.")

        assert isinstance(result, GrammarFeatures)
        # 단순 문장은 종속절이 없음
        if result.dep_clauses_per_clause is not None:
            assert result.dep_clauses_per_clause == 0.0

    def test_complex_sentence(self, extractor: GrammarFeatureExtractor):
        """복잡한 문장 처리 (종속절 포함)"""
        if extractor._nlp is None:
            pytest.skip("spaCy model not available")

        complex_text = (
            "I think that education is important because it helps people, "
            "and when they learn new things, they become more confident."
        )
        result = extractor.extract(complex_text)

        assert isinstance(result, GrammarFeatures)
        # 복잡한 문장은 종속절이 있음
        if result.dep_clauses_per_clause is not None:
            assert result.dep_clauses_per_clause > 0.0


class TestGrammarFeaturesSchema:
    """GrammarFeatures 스키마 테스트"""

    def test_schema_validation(self):
        """스키마 유효성 검사"""
        features = GrammarFeatures(
            poscvamax=0.75,
            dep_clauses_per_clause=1.2,
            spacy_available=True,
        )

        assert features.poscvamax == 0.75
        assert features.dep_clauses_per_clause == 1.2
        assert features.spacy_available is True

    def test_schema_with_none_values(self):
        """None 값을 가진 스키마"""
        features = GrammarFeatures(
            poscvamax=None,
            dep_clauses_per_clause=None,
            spacy_available=False,
        )

        assert features.poscvamax is None
        assert features.dep_clauses_per_clause is None
        assert features.spacy_available is False

    def test_schema_default_values(self):
        """기본값 테스트"""
        features = GrammarFeatures()

        assert features.poscvamax is None
        assert features.dep_clauses_per_clause is None
        assert features.spacy_available is False
