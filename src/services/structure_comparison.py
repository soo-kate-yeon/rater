"""Structure Comparison 서비스

SPEC-TOEFL-FEATURE-001 Phase 2: Independent Task Structure Pattern Detection
- Detect position, reason, example components
- Calculate match percentage
- Pattern-based structure analysis

TODO: Phase 2 구현 필요
"""

import logging
from typing import List, Optional

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class ComponentMatch(BaseModel):
    """구조 component 매칭 결과"""

    component_type: str = Field(..., description="Component 타입 (position, reason, example)")
    detected: bool = Field(..., description="감지 여부")
    evidence_text: Optional[str] = Field(default=None, description="증거 텍스트")
    confidence: float = Field(..., ge=0.0, le=1.0, description="신뢰도 (0.0-1.0)")


class StructureComparisonResult(BaseModel):
    """구조 비교 결과"""

    match_percentage: float = Field(..., ge=0.0, le=100.0, description="구조 매칭 비율 (%)")
    components: List[ComponentMatch] = Field(
        default_factory=list, description="Component 매칭 결과"
    )
    total_components: int = Field(..., ge=0, description="전체 component 수")
    matched_components: int = Field(..., ge=0, description="매칭된 component 수")


class StructureComparisonService:
    """
    Structure Comparison 서비스

    Independent Task에서 응답 구조를 분석합니다.
    - Position statement: 입장 표명
    - Reasons: 이유 제시
    - Examples: 예시/근거 제시
    """

    def __init__(self) -> None:
        """서비스 초기화"""
        logger.info("StructureComparisonService initialized (stub)")

    def analyze_structure(self, transcript: str) -> StructureComparisonResult:
        """
        Transcript 구조 분석

        Args:
            transcript: 사용자 응답 텍스트

        Returns:
            StructureComparisonResult: 구조 분석 결과

        TODO: Phase 2 구현 필요
        - Discourse marker detection
        - Sentence role classification
        - Pattern-based structure analysis
        """
        logger.warning("StructureComparisonService.analyze_structure() is a stub implementation")

        # Stub 구현: 항상 0% 매칭 반환
        return StructureComparisonResult(
            match_percentage=0.0,
            components=[],
            total_components=3,  # position, reason, example
            matched_components=0,
        )


# 싱글톤 인스턴스
_service: Optional[StructureComparisonService] = None


def get_structure_comparison_service() -> StructureComparisonService:
    """Structure Comparison Service 싱글톤 인스턴스 반환"""
    global _service
    if _service is None:
        _service = StructureComparisonService()
    return _service
