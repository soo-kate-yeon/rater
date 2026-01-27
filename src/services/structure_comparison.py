"""Structure Comparison 서비스

SPEC-TOEFL-FEATURE-001 Phase 2: Independent Task Structure Pattern Detection
- Detect position, reason, example components
- Calculate match percentage
- Pattern-based structure analysis
"""

import logging
import re
from typing import Dict, List, Optional, Set

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# Discourse markers by component type
POSITION_MARKERS: Set[str] = {
    "i think",
    "i believe",
    "in my opinion",
    "i prefer",
    "i agree",
    "i disagree",
    "i feel",
    "i would say",
    "personally",
}

REASON_MARKERS: Set[str] = {
    "because",
    "since",
    "reason",
    "first",
    "second",
    "third",
    "firstly",
    "secondly",
    "thirdly",
    "one reason",
    "another reason",
    "the main reason",
    "this is because",
}

EXAMPLE_MARKERS: Set[str] = {
    "for example",
    "for instance",
    "such as",
    "like",
    "an example",
    "to illustrate",
    "specifically",
    "in particular",
}


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
    - Reasons: 이유 제시 (reason1, reason2)
    - Examples: 예시/근거 제시

    Expected structure:
        - position: 1개
        - reason1: 1개
        - reason2: 1개 (선택적)
        - example: 1개

    Algorithm:
        1. Split transcript into sentences
        2. Classify each sentence by discourse markers
        3. Detect components (position, reason1, reason2, example)
        4. match_percentage = (detected / expected) * 100
    """

    # Expected components for Independent Task
    EXPECTED_COMPONENTS: List[str] = ["position", "reason1", "reason2", "example"]

    def __init__(self) -> None:
        """서비스 초기화"""
        logger.info("StructureComparisonService initialized")

    def analyze_structure(self, transcript: str) -> StructureComparisonResult:
        """
        Transcript 구조 분석

        Args:
            transcript: 사용자 응답 텍스트

        Returns:
            StructureComparisonResult: 구조 분석 결과
        """
        # Edge case: 빈 transcript
        if not transcript.strip():
            return StructureComparisonResult(
                match_percentage=0.0,
                components=[
                    ComponentMatch(
                        component_type=comp,
                        detected=False,
                        evidence_text=None,
                        confidence=0.0,
                    )
                    for comp in self.EXPECTED_COMPONENTS
                ],
                total_components=len(self.EXPECTED_COMPONENTS),
                matched_components=0,
            )

        # 문장 분리
        sentences = self._split_sentences(transcript)

        # 각 문장 분류
        classified_sentences = self._classify_sentences(sentences)

        # Components 감지
        components = self._detect_components(classified_sentences)

        # 매칭된 component 수 계산
        matched_count = sum(1 for comp in components if comp.detected)

        # Match percentage 계산
        match_percentage = (matched_count / len(self.EXPECTED_COMPONENTS)) * 100.0

        return StructureComparisonResult(
            match_percentage=match_percentage,
            components=components,
            total_components=len(self.EXPECTED_COMPONENTS),
            matched_components=matched_count,
        )

    def _split_sentences(self, text: str) -> List[str]:
        """
        텍스트를 문장으로 분리

        Args:
            text: 입력 텍스트

        Returns:
            문장 리스트
        """
        # 단순 문장 분리 (마침표, 느낌표, 물음표 기준)
        sentences = re.split(r'[.!?]+', text)

        # 빈 문장 제거 및 공백 정리
        sentences = [s.strip() for s in sentences if s.strip()]

        return sentences

    def _classify_sentences(self, sentences: List[str]) -> Dict[str, List[str]]:
        """
        문장을 discourse marker로 분류

        Note: 한 문장에 여러 마커가 있을 수 있음 (예: "I think X because Y")
        이 경우 모든 해당 카테고리에 추가

        Args:
            sentences: 문장 리스트

        Returns:
            분류된 문장 딕셔너리 {marker_type: [sentences]}
        """
        classified: Dict[str, List[str]] = {
            "position": [],
            "reason": [],
            "example": [],
        }

        for sentence in sentences:
            sentence_lower = sentence.lower()
            added_to_any = False

            # Position 마커 확인
            if any(marker in sentence_lower for marker in POSITION_MARKERS):
                classified["position"].append(sentence)
                added_to_any = True

            # Reason 마커 확인
            if any(marker in sentence_lower for marker in REASON_MARKERS):
                classified["reason"].append(sentence)
                added_to_any = True

            # Example 마커 확인
            if any(marker in sentence_lower for marker in EXAMPLE_MARKERS):
                classified["example"].append(sentence)
                added_to_any = True

        return classified

    def _detect_components(
        self, classified_sentences: Dict[str, List[str]]
    ) -> List[ComponentMatch]:
        """
        분류된 문장에서 components 감지

        Args:
            classified_sentences: 분류된 문장 딕셔너리

        Returns:
            ComponentMatch 리스트
        """
        components: List[ComponentMatch] = []

        # Position component
        position_detected = len(classified_sentences["position"]) > 0
        position_confidence = 1.0 if position_detected else 0.0
        position_evidence = (
            classified_sentences["position"][0] if position_detected else None
        )

        components.append(
            ComponentMatch(
                component_type="position",
                detected=position_detected,
                evidence_text=position_evidence,
                confidence=position_confidence,
            )
        )

        # Reason components (reason1, reason2)
        reason_count = len(classified_sentences["reason"])

        # reason1
        reason1_detected = reason_count >= 1
        reason1_confidence = 1.0 if reason1_detected else 0.0
        reason1_evidence = classified_sentences["reason"][0] if reason1_detected else None

        components.append(
            ComponentMatch(
                component_type="reason1",
                detected=reason1_detected,
                evidence_text=reason1_evidence,
                confidence=reason1_confidence,
            )
        )

        # reason2
        reason2_detected = reason_count >= 2
        reason2_confidence = 1.0 if reason2_detected else 0.0
        reason2_evidence = classified_sentences["reason"][1] if reason2_detected else None

        components.append(
            ComponentMatch(
                component_type="reason2",
                detected=reason2_detected,
                evidence_text=reason2_evidence,
                confidence=reason2_confidence,
            )
        )

        # Example component
        example_detected = len(classified_sentences["example"]) > 0
        example_confidence = 1.0 if example_detected else 0.0
        example_evidence = classified_sentences["example"][0] if example_detected else None

        components.append(
            ComponentMatch(
                component_type="example",
                detected=example_detected,
                evidence_text=example_evidence,
                confidence=example_confidence,
            )
        )

        return components


# 싱글톤 인스턴스
_service: Optional[StructureComparisonService] = None


def get_structure_comparison_service() -> StructureComparisonService:
    """Structure Comparison Service 싱글톤 인스턴스 반환"""
    global _service
    if _service is None:
        _service = StructureComparisonService()
    return _service
