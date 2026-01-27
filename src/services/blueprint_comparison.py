"""Blueprint Comparison 서비스

SPEC-TOEFL-FEATURE-001 Phase 2: Integrated Task Blueprint Matching
- Unit matching for Integrated tasks
- Calculate coverage percentage
- Generate unit_details with evidence spans

TODO: Phase 2 구현 필요
"""

import logging
from typing import List, Optional

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class UnitMatch(BaseModel):
    """Unit 매칭 결과"""

    unit_id: str = Field(..., description="Blueprint unit ID")
    matched: bool = Field(..., description="매칭 여부")
    confidence: float = Field(..., ge=0.0, le=1.0, description="매칭 신뢰도 (0.0-1.0)")
    evidence_span: Optional[str] = Field(default=None, description="증거 텍스트 span")


class BlueprintComparisonResult(BaseModel):
    """Blueprint 비교 결과"""

    coverage_percentage: float = Field(
        ..., ge=0.0, le=100.0, description="Blueprint 커버리지 (%)"
    )
    matched_units: List[UnitMatch] = Field(default_factory=list, description="매칭된 units")
    total_units: int = Field(..., ge=0, description="전체 unit 수")
    matched_count: int = Field(..., ge=0, description="매칭된 unit 수")


class BlueprintComparisonService:
    """
    Blueprint Comparison 서비스

    Integrated Task에서 사용자 응답이 blueprint의 key units를 얼마나 커버하는지 분석합니다.
    """

    def __init__(self) -> None:
        """서비스 초기화"""
        logger.info("BlueprintComparisonService initialized (stub)")

    def compare(
        self, transcript: str, blueprint_units: List[str]
    ) -> BlueprintComparisonResult:
        """
        Transcript와 blueprint units 비교

        Args:
            transcript: 사용자 응답 텍스트
            blueprint_units: Blueprint key units 목록

        Returns:
            BlueprintComparisonResult: 비교 결과

        TODO: Phase 2 구현 필요
        - Semantic matching (BERT/sentence-transformers)
        - Evidence span extraction
        - Confidence scoring
        """
        logger.warning("BlueprintComparisonService.compare() is a stub implementation")

        # Stub 구현: 항상 0% 커버리지 반환
        return BlueprintComparisonResult(
            coverage_percentage=0.0,
            matched_units=[],
            total_units=len(blueprint_units),
            matched_count=0,
        )


# 싱글톤 인스턴스
_service: Optional[BlueprintComparisonService] = None


def get_blueprint_comparison_service() -> BlueprintComparisonService:
    """Blueprint Comparison Service 싱글톤 인스턴스 반환"""
    global _service
    if _service is None:
        _service = BlueprintComparisonService()
    return _service
