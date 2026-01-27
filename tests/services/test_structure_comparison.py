"""Structure Comparison 서비스 테스트 (Stub)

TODO SPEC-TOEFL-FEATURE-001 Phase 2: 실제 구현 후 테스트 확장 필요
"""

import pytest

from src.services.structure_comparison import (
    StructureComparisonResult,
    StructureComparisonService,
    get_structure_comparison_service,
)


@pytest.fixture
def service() -> StructureComparisonService:
    """Structure comparison service 인스턴스"""
    return StructureComparisonService()


class TestStructureComparisonServiceStub:
    """Stub 구현 테스트"""

    def test_service_initialization(self, service: StructureComparisonService):
        """서비스 초기화"""
        assert service is not None

    def test_singleton_pattern(self):
        """싱글톤 패턴"""
        instance1 = get_structure_comparison_service()
        instance2 = get_structure_comparison_service()

        assert instance1 is instance2

    def test_analyze_structure_stub_implementation(self, service: StructureComparisonService):
        """Stub 구현: 0% 매칭 반환"""
        result = service.analyze_structure(
            transcript="I believe education is important. First, it helps people. For example, students learn."
        )

        assert isinstance(result, StructureComparisonResult)
        assert result.match_percentage == 0.0
        assert result.total_components == 3  # position, reason, example
        assert result.matched_components == 0
        assert len(result.components) == 0

    def test_analyze_structure_empty_transcript(self, service: StructureComparisonService):
        """빈 transcript 처리"""
        result = service.analyze_structure(transcript="")

        assert isinstance(result, StructureComparisonResult)
        assert result.match_percentage == 0.0

    def test_analyze_structure_simple_text(self, service: StructureComparisonService):
        """단순 텍스트 처리"""
        result = service.analyze_structure(transcript="Test")

        assert isinstance(result, StructureComparisonResult)
        # Stub이므로 항상 0% 반환
        assert result.match_percentage == 0.0
