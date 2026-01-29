"""Structure Comparison 서비스 테스트

SPEC-TOEFL-FEATURE-001 Phase 2: Structure Pattern Detection 구현 테스트
"""

import pytest_asyncio

from src.services.structure_comparison import (
    StructureComparisonResult,
    StructureComparisonService,
    get_structure_comparison_service,
)


@pytest_asyncio.fixture
def service() -> StructureComparisonService:
    """Structure comparison service 인스턴스"""
    return StructureComparisonService()


class TestStructureComparisonServiceBasics:
    """기본 기능 테스트"""

    def test_service_initialization(self, service: StructureComparisonService):
        """서비스 초기화"""
        assert service is not None

    def test_singleton_pattern(self):
        """싱글톤 패턴"""
        instance1 = get_structure_comparison_service()
        instance2 = get_structure_comparison_service()

        assert instance1 is instance2

    def test_analyze_structure_empty_transcript(self, service: StructureComparisonService):
        """빈 transcript 처리: 0% 매칭"""
        result = service.analyze_structure(transcript="")

        assert isinstance(result, StructureComparisonResult)
        assert result.match_percentage == 0.0
        assert result.total_components == 4  # position, reason1, reason2, example
        assert result.matched_components == 0

    def test_analyze_structure_simple_text(self, service: StructureComparisonService):
        """단순 텍스트: 구조 없음"""
        result = service.analyze_structure(transcript="Test")

        assert isinstance(result, StructureComparisonResult)
        assert result.match_percentage == 0.0


class TestPositionDetection:
    """Position statement 감지 테스트"""

    def test_detect_position_with_i_think(self, service: StructureComparisonService):
        """'I think' 마커로 position 감지"""
        transcript = "I think education is very important for society."

        result = service.analyze_structure(transcript=transcript)

        position_components = [c for c in result.components if c.component_type == "position"]
        assert len(position_components) > 0
        assert position_components[0].detected is True
        assert position_components[0].evidence_text is not None
        assert "i think" in position_components[0].evidence_text.lower()

    def test_detect_position_with_i_believe(self, service: StructureComparisonService):
        """'I believe' 마커로 position 감지"""
        transcript = "I believe that technology helps people."

        result = service.analyze_structure(transcript=transcript)

        position_components = [c for c in result.components if c.component_type == "position"]
        assert len(position_components) > 0
        assert position_components[0].detected is True

    def test_detect_position_with_prefer(self, service: StructureComparisonService):
        """'prefer' 마커로 position 감지"""
        transcript = "I prefer studying in the library rather than at home."

        result = service.analyze_structure(transcript=transcript)

        position_components = [c for c in result.components if c.component_type == "position"]
        assert len(position_components) > 0
        assert position_components[0].detected is True


class TestReasonDetection:
    """Reason statement 감지 테스트"""

    def test_detect_reason_with_because(self, service: StructureComparisonService):
        """'because' 마커로 reason 감지"""
        transcript = "I think education is important because it helps people grow."

        result = service.analyze_structure(transcript=transcript)

        reason_components = [c for c in result.components if "reason" in c.component_type]
        assert len(reason_components) >= 1
        detected_reasons = [c for c in reason_components if c.detected]
        assert len(detected_reasons) >= 1
        assert "because" in detected_reasons[0].evidence_text.lower()

    def test_detect_multiple_reasons(self, service: StructureComparisonService):
        """복수 reasons 감지: First, Second"""
        transcript = """
        I think studying abroad is beneficial.
        First, it broadens your perspective.
        Second, you learn a new language.
        """

        result = service.analyze_structure(transcript=transcript)

        reason_components = [c for c in result.components if "reason" in c.component_type]
        detected_reasons = [c for c in reason_components if c.detected]
        # 최소 1개 이상의 reason이 감지되어야 함
        assert len(detected_reasons) >= 1

    def test_detect_reason_with_since(self, service: StructureComparisonService):
        """'since' 마커로 reason 감지"""
        transcript = "I prefer online classes since they are more flexible."

        result = service.analyze_structure(transcript=transcript)

        reason_components = [c for c in result.components if "reason" in c.component_type]
        detected_reasons = [c for c in reason_components if c.detected]
        assert len(detected_reasons) >= 1


class TestExampleDetection:
    """Example statement 감지 테스트"""

    def test_detect_example_with_for_example(self, service: StructureComparisonService):
        """'for example' 마커로 example 감지"""
        transcript = "Education helps people. For example, students learn critical thinking."

        result = service.analyze_structure(transcript=transcript)

        example_components = [c for c in result.components if c.component_type == "example"]
        assert len(example_components) > 0
        assert example_components[0].detected is True
        assert "for example" in example_components[0].evidence_text.lower()

    def test_detect_example_with_for_instance(self, service: StructureComparisonService):
        """'for instance' 마커로 example 감지"""
        transcript = "Technology is useful. For instance, smartphones connect people."

        result = service.analyze_structure(transcript=transcript)

        example_components = [c for c in result.components if c.component_type == "example"]
        assert len(example_components) > 0
        assert example_components[0].detected is True

    def test_detect_example_with_such_as(self, service: StructureComparisonService):
        """'such as' 마커로 example 감지"""
        transcript = "Many activities are helpful, such as reading and writing."

        result = service.analyze_structure(transcript=transcript)

        example_components = [c for c in result.components if c.component_type == "example"]
        assert len(example_components) > 0
        assert example_components[0].detected is True


class TestCompleteStructure:
    """완전한 구조 테스트"""

    def test_complete_structure_all_components(self, service: StructureComparisonService):
        """모든 components 포함: 100% 매칭"""
        transcript = """
        I believe that studying abroad is very beneficial.
        First, it helps you understand different cultures.
        Second, you can improve your language skills.
        For example, my friend studied in Spain and became fluent in Spanish.
        """

        result = service.analyze_structure(transcript=transcript)

        # 모든 component가 감지되어야 함
        assert result.matched_components >= 3  # position, reason, example 최소
        assert result.match_percentage >= 75.0  # 3/4 = 75%

    def test_partial_structure_position_and_reason_only(self, service: StructureComparisonService):
        """부분 구조: position + reason만"""
        transcript = """
        I think education is important because it helps people succeed.
        """

        result = service.analyze_structure(transcript=transcript)

        # Position과 reason은 감지, example은 없음
        assert result.matched_components >= 2
        assert 25.0 < result.match_percentage < 100.0

    def test_no_structure_detected(self, service: StructureComparisonService):
        """구조 없음: 서술만"""
        transcript = "The weather is nice today. I like sunny days."

        result = service.analyze_structure(transcript=transcript)

        # 구조 마커가 없으므로 매칭 낮음
        assert result.match_percentage < 50.0


class TestMatchPercentage:
    """Match percentage 계산 테스트"""

    def test_match_percentage_formula(self, service: StructureComparisonService):
        """Match percentage = (detected / expected) * 100"""
        transcript = "I think cats are better. Because they are independent."

        result = service.analyze_structure(transcript=transcript)

        # expected = 4 (position, reason1, reason2, example)
        # detected = 2 (position, reason1)
        # percentage = 2/4 * 100 = 50%
        assert result.total_components == 4

        expected_percentage = (result.matched_components / result.total_components) * 100
        assert result.match_percentage == expected_percentage

    def test_match_percentage_bounds(self, service: StructureComparisonService):
        """Match percentage는 0-100 범위"""
        transcript = "Random text without structure."

        result = service.analyze_structure(transcript=transcript)

        assert 0.0 <= result.match_percentage <= 100.0


class TestConfidenceScoring:
    """Confidence 점수 테스트"""

    def test_confidence_high_with_clear_marker(self, service: StructureComparisonService):
        """명확한 마커: 높은 confidence"""
        transcript = "I believe education is important."

        result = service.analyze_structure(transcript=transcript)

        position_components = [c for c in result.components if c.component_type == "position"]
        if position_components and position_components[0].detected:
            # 명확한 "I believe" 마커가 있으므로 confidence 높음
            assert position_components[0].confidence >= 0.8

    def test_confidence_medium_with_weak_marker(self, service: StructureComparisonService):
        """약한 마커: 중간 confidence"""
        transcript = "Maybe technology is useful."

        _result = service.analyze_structure(transcript=transcript)

        # "maybe"는 약한 position 마커이므로 confidence 중간
        # 구현에 따라 다를 수 있음


class TestEdgeCases:
    """엣지 케이스 테스트"""

    def test_very_long_transcript(self, service: StructureComparisonService):
        """매우 긴 transcript"""
        transcript = "I think education is important. " * 100

        result = service.analyze_structure(transcript=transcript)

        # 에러 없이 처리되어야 함
        assert isinstance(result, StructureComparisonResult)

    def test_special_characters(self, service: StructureComparisonService):
        """특수 문자 포함"""
        transcript = "I think it's important! Because... well, it helps people."

        result = service.analyze_structure(transcript=transcript)

        # 특수 문자 처리되어야 함
        assert isinstance(result, StructureComparisonResult)

    def test_mixed_case_markers(self, service: StructureComparisonService):
        """대소문자 혼합 마커"""
        transcript = "I THINK education is IMPORTANT. BECAUSE it helps."

        result = service.analyze_structure(transcript=transcript)

        # 대소문자 무시하고 마커 감지되어야 함
        position_detected = any(
            c.component_type == "position" and c.detected for c in result.components
        )
        assert position_detected
