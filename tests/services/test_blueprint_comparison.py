"""Blueprint Comparison 서비스 테스트 (Stub)

TODO SPEC-TOEFL-FEATURE-001 Phase 2: 실제 구현 후 테스트 확장 필요
"""

import pytest

from src.services.blueprint_comparison import (
    BlueprintComparisonResult,
    BlueprintComparisonService,
    get_blueprint_comparison_service,
)


@pytest.fixture
def service() -> BlueprintComparisonService:
    """Blueprint comparison service 인스턴스"""
    return BlueprintComparisonService()


class TestBlueprintComparisonServiceStub:
    """Stub 구현 테스트"""

    def test_service_initialization(self, service: BlueprintComparisonService):
        """서비스 초기화"""
        assert service is not None

    def test_singleton_pattern(self):
        """싱글톤 패턴"""
        instance1 = get_blueprint_comparison_service()
        instance2 = get_blueprint_comparison_service()

        assert instance1 is instance2

    def test_compare_stub_implementation(self, service: BlueprintComparisonService):
        """Stub 구현: 0% 커버리지 반환"""
        result = service.compare(
            transcript="I think education is important.",
            blueprint_units=["unit1", "unit2", "unit3"],
        )

        assert isinstance(result, BlueprintComparisonResult)
        assert result.coverage_percentage == 0.0
        assert result.total_units == 3
        assert result.matched_count == 0
        assert len(result.matched_units) == 0

    def test_compare_empty_transcript(self, service: BlueprintComparisonService):
        """빈 transcript 처리"""
        result = service.compare(transcript="", blueprint_units=["unit1"])

        assert isinstance(result, BlueprintComparisonResult)
        assert result.coverage_percentage == 0.0

    def test_compare_empty_blueprint(self, service: BlueprintComparisonService):
        """빈 blueprint 처리"""
        result = service.compare(transcript="Test", blueprint_units=[])

        assert isinstance(result, BlueprintComparisonResult)
        assert result.total_units == 0
