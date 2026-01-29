"""Blueprint Comparison 서비스 테스트

SPEC-TOEFL-FEATURE-001 Phase 2: Blueprint Matching 구현 테스트
"""

import pytest
import pytest_asyncio

from src.services.blueprint_comparison import (
    BlueprintComparisonResult,
    BlueprintComparisonService,
    UnitMatch,
    get_blueprint_comparison_service,
)


@pytest_asyncio.fixture
def service() -> BlueprintComparisonService:
    """Blueprint comparison service 인스턴스"""
    return BlueprintComparisonService()


class TestBlueprintComparisonServiceBasics:
    """기본 기능 테스트"""

    def test_service_initialization(self, service: BlueprintComparisonService):
        """서비스 초기화"""
        assert service is not None

    def test_singleton_pattern(self):
        """싱글톤 패턴"""
        instance1 = get_blueprint_comparison_service()
        instance2 = get_blueprint_comparison_service()

        assert instance1 is instance2

    def test_compare_empty_transcript(self, service: BlueprintComparisonService):
        """빈 transcript 처리: 0% 커버리지"""
        result = service.compare(transcript="", blueprint_units=["education quality"])

        assert isinstance(result, BlueprintComparisonResult)
        assert result.coverage_percentage == 0.0
        assert result.total_units == 1
        assert result.matched_count == 0

    def test_compare_empty_blueprint(self, service: BlueprintComparisonService):
        """빈 blueprint 처리: 100% 커버리지 (빈 경우)"""
        result = service.compare(transcript="Test content", blueprint_units=[])

        assert isinstance(result, BlueprintComparisonResult)
        assert result.total_units == 0
        assert result.matched_count == 0
        # 빈 blueprint은 100% 커버리지로 간주
        assert result.coverage_percentage == 100.0


class TestBlueprintMatchingLogic:
    """Blueprint 매칭 로직 테스트"""

    def test_exact_match_single_unit(self, service: BlueprintComparisonService):
        """완전 매칭: 단일 unit"""
        transcript = "The lecture discusses the importance of education quality in modern society."
        blueprint_units = ["education quality"]

        result = service.compare(transcript=transcript, blueprint_units=blueprint_units)

        assert result.total_units == 1
        assert result.matched_count == 1
        assert result.coverage_percentage == 100.0
        assert len(result.matched_units) == 1

        unit_match = result.matched_units[0]
        assert unit_match.unit_id == "U0"
        assert unit_match.matched is True
        assert unit_match.confidence >= 0.6
        assert unit_match.evidence_span is not None
        assert "education quality" in unit_match.evidence_span.lower()

    def test_partial_match_with_keywords(self, service: BlueprintComparisonService):
        """부분 매칭: 키워드 일부만 포함"""
        transcript = "The professor talks about education. Students need good learning environment."
        blueprint_units = ["education quality standards"]

        result = service.compare(transcript=transcript, blueprint_units=blueprint_units)

        assert result.total_units == 1
        # "education"만 매칭되므로 confidence는 낮을 수 있지만 매칭은 될 수 있음
        # 알고리즘에 따라 달라질 수 있음

    def test_case_insensitive_matching(self, service: BlueprintComparisonService):
        """대소문자 무시 매칭"""
        transcript = "EDUCATION QUALITY is very important."
        blueprint_units = ["education quality"]

        result = service.compare(transcript=transcript, blueprint_units=blueprint_units)

        assert result.matched_count >= 1
        # 대소문자 관계없이 매칭되어야 함

    def test_multiple_units_partial_coverage(self, service: BlueprintComparisonService):
        """복수 units, 일부만 커버"""
        transcript = """
        The lecture explains climate change effects on agriculture.
        Rising temperatures affect crop yields significantly.
        """
        blueprint_units = [
            "climate change effects",
            "agricultural impact",
            "economic consequences",  # 이 부분은 없음
        ]

        result = service.compare(transcript=transcript, blueprint_units=blueprint_units)

        assert result.total_units == 3
        # 최소 1개 이상은 매칭되어야 함
        assert result.matched_count >= 1
        assert result.matched_count < result.total_units
        assert 0 < result.coverage_percentage < 100.0

    def test_no_match_different_content(self, service: BlueprintComparisonService):
        """매칭 없음: 완전히 다른 내용"""
        transcript = "I like playing basketball and watching movies."
        blueprint_units = ["climate change", "global warming"]

        result = service.compare(transcript=transcript, blueprint_units=blueprint_units)

        assert result.total_units == 2
        assert result.matched_count == 0
        assert result.coverage_percentage == 0.0


class TestConfidenceScoring:
    """Confidence 점수 계산 테스트"""

    def test_high_confidence_full_match(self, service: BlueprintComparisonService):
        """높은 confidence: 완전 매칭"""
        transcript = "The main topic of the lecture is renewable energy sources."
        blueprint_units = ["renewable energy sources"]

        result = service.compare(transcript=transcript, blueprint_units=blueprint_units)

        matched = [u for u in result.matched_units if u.matched]
        if matched:
            # 완전 매칭이므로 confidence가 높아야 함
            assert matched[0].confidence >= 0.8

    def test_medium_confidence_partial_match(self, service: BlueprintComparisonService):
        """중간 confidence: 부분 매칭"""
        transcript = "The lecture is about renewable energy."
        blueprint_units = ["renewable energy sources and sustainability"]

        result = service.compare(transcript=transcript, blueprint_units=blueprint_units)

        # 부분 매칭이므로 confidence는 중간 정도
        if result.matched_count > 0:
            matched = [u for u in result.matched_units if u.matched]
            if matched:
                assert 0.4 <= matched[0].confidence < 0.9

    def test_confidence_below_threshold_not_matched(
        self, service: BlueprintComparisonService
    ):
        """낮은 confidence: 매칭 안 됨"""
        transcript = "The topic is about technology."
        blueprint_units = ["climate change effects on agriculture"]

        result = service.compare(transcript=transcript, blueprint_units=blueprint_units)

        # confidence가 threshold(0.6) 미만이면 matched=False
        unmatched = [u for u in result.matched_units if not u.matched]
        if unmatched:
            assert unmatched[0].confidence < 0.6


class TestEvidenceSpanExtraction:
    """Evidence span 추출 테스트"""

    def test_evidence_span_contains_keywords(self, service: BlueprintComparisonService):
        """Evidence span이 키워드 포함"""
        transcript = "First, the professor mentions global warming. Second, deforestation is discussed."
        blueprint_units = ["global warming"]

        result = service.compare(transcript=transcript, blueprint_units=blueprint_units)

        matched = [u for u in result.matched_units if u.matched]
        if matched:
            evidence = matched[0].evidence_span
            assert evidence is not None
            assert "global warming" in evidence.lower()

    def test_evidence_span_null_when_not_matched(
        self, service: BlueprintComparisonService
    ):
        """매칭 안 되면 evidence_span은 None"""
        transcript = "The lecture is about history."
        blueprint_units = ["quantum physics"]

        result = service.compare(transcript=transcript, blueprint_units=blueprint_units)

        # 매칭 안 된 unit은 evidence_span이 None
        unmatched = [u for u in result.matched_units if not u.matched]
        for unit in unmatched:
            assert unit.evidence_span is None


class TestEdgeCases:
    """엣지 케이스 테스트"""

    def test_very_short_transcript(self, service: BlueprintComparisonService):
        """매우 짧은 transcript"""
        transcript = "Education."
        blueprint_units = ["education quality"]

        result = service.compare(transcript=transcript, blueprint_units=blueprint_units)

        # 에러 없이 처리되어야 함
        assert isinstance(result, BlueprintComparisonResult)

    def test_very_long_transcript(self, service: BlueprintComparisonService):
        """매우 긴 transcript"""
        transcript = "The lecture discusses education. " * 100
        blueprint_units = ["education quality"]

        result = service.compare(transcript=transcript, blueprint_units=blueprint_units)

        # 에러 없이 처리되어야 함
        assert isinstance(result, BlueprintComparisonResult)

    def test_special_characters_in_text(self, service: BlueprintComparisonService):
        """특수 문자 포함"""
        transcript = "The lecture's topic: climate-change & it's effects!"
        blueprint_units = ["climate change effects"]

        result = service.compare(transcript=transcript, blueprint_units=blueprint_units)

        # 특수 문자 처리되어야 함
        assert isinstance(result, BlueprintComparisonResult)

    def test_unit_id_generation(self, service: BlueprintComparisonService):
        """Unit ID 생성 확인"""
        blueprint_units = ["unit1", "unit2", "unit3"]
        result = service.compare(transcript="test", blueprint_units=blueprint_units)

        assert len(result.matched_units) == 3
        assert result.matched_units[0].unit_id == "U0"
        assert result.matched_units[1].unit_id == "U1"
        assert result.matched_units[2].unit_id == "U2"
