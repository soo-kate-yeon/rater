"""Blueprint Comparison 서비스

SPEC-TOEFL-FEATURE-001 Phase 2: Integrated Task Blueprint Matching
- Unit matching for Integrated tasks
- Calculate coverage percentage
- Generate unit_details with evidence spans
"""

import logging
import re
from difflib import SequenceMatcher

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# English stopwords (간소화된 목록)
STOPWORDS: set[str] = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "has",
    "he",
    "in",
    "is",
    "it",
    "its",
    "of",
    "on",
    "that",
    "the",
    "to",
    "was",
    "were",
    "will",
    "with",
    "this",
    "these",
    "those",
}


class UnitMatch(BaseModel):
    """Unit 매칭 결과"""

    unit_id: str = Field(..., description="Blueprint unit ID")
    matched: bool = Field(..., description="매칭 여부")
    confidence: float = Field(..., ge=0.0, le=1.0, description="매칭 신뢰도 (0.0-1.0)")
    evidence_span: str | None = Field(default=None, description="증거 텍스트 span")


class BlueprintComparisonResult(BaseModel):
    """Blueprint 비교 결과"""

    coverage_percentage: float = Field(..., ge=0.0, le=100.0, description="Blueprint 커버리지 (%)")
    matched_units: list[UnitMatch] = Field(default_factory=list, description="매칭된 units")
    total_units: int = Field(..., ge=0, description="전체 unit 수")
    matched_count: int = Field(..., ge=0, description="매칭된 unit 수")


class BlueprintComparisonService:
    """
    Blueprint Comparison 서비스

    Integrated Task에서 사용자 응답이 blueprint의 key units를 얼마나 커버하는지 분석합니다.

    Algorithm:
        1. 각 blueprint unit에서 키워드 추출 (stopwords 제거)
        2. transcript에서 유사한 구문 검색 (fuzzy matching)
        3. confidence = matched_keywords / total_keywords
        4. confidence >= 0.6이면 matched=True
        5. coverage_percentage = matched_count / total_units * 100
    """

    def __init__(self, confidence_threshold: float = 0.6) -> None:
        """
        서비스 초기화

        Args:
            confidence_threshold: 매칭으로 간주할 최소 confidence (기본값: 0.6)
        """
        self.confidence_threshold = confidence_threshold
        logger.info(f"BlueprintComparisonService initialized (threshold={confidence_threshold})")

    def compare(self, transcript: str, blueprint_units: list[str]) -> BlueprintComparisonResult:
        """
        Transcript와 blueprint units 비교

        Args:
            transcript: 사용자 응답 텍스트
            blueprint_units: Blueprint key units 목록

        Returns:
            BlueprintComparisonResult: 비교 결과
        """
        # Edge case: 빈 blueprint은 100% 커버리지
        if not blueprint_units:
            return BlueprintComparisonResult(
                coverage_percentage=100.0,
                matched_units=[],
                total_units=0,
                matched_count=0,
            )

        # Edge case: 빈 transcript는 0% 커버리지
        if not transcript.strip():
            return BlueprintComparisonResult(
                coverage_percentage=0.0,
                matched_units=[
                    UnitMatch(
                        unit_id=f"U{i}",
                        matched=False,
                        confidence=0.0,
                        evidence_span=None,
                    )
                    for i in range(len(blueprint_units))
                ],
                total_units=len(blueprint_units),
                matched_count=0,
            )

        # 텍스트 정규화
        transcript_lower = transcript.lower()

        # 각 unit 매칭 시도
        matched_units: list[UnitMatch] = []
        matched_count = 0

        for idx, unit in enumerate(blueprint_units):
            unit_id = f"U{idx}"

            # Unit에서 키워드 추출
            keywords = self._extract_keywords(unit)

            if not keywords:
                # 키워드가 없으면 매칭 불가
                matched_units.append(
                    UnitMatch(
                        unit_id=unit_id,
                        matched=False,
                        confidence=0.0,
                        evidence_span=None,
                    )
                )
                continue

            # Transcript에서 키워드 매칭 및 confidence 계산
            confidence, evidence_span = self._calculate_match(
                transcript_lower, keywords, transcript
            )

            # Threshold 기준으로 매칭 여부 결정
            is_matched = confidence >= self.confidence_threshold

            matched_units.append(
                UnitMatch(
                    unit_id=unit_id,
                    matched=is_matched,
                    confidence=confidence,
                    evidence_span=evidence_span if is_matched else None,
                )
            )

            if is_matched:
                matched_count += 1

        # Coverage 계산
        coverage_percentage = (matched_count / len(blueprint_units)) * 100.0

        return BlueprintComparisonResult(
            coverage_percentage=coverage_percentage,
            matched_units=matched_units,
            total_units=len(blueprint_units),
            matched_count=matched_count,
        )

    def _extract_keywords(self, text: str) -> list[str]:
        """
        텍스트에서 키워드 추출 (stopwords 제거)

        Args:
            text: 입력 텍스트

        Returns:
            키워드 리스트
        """
        # 소문자 변환 및 특수 문자 제거
        text_clean = re.sub(r"[^a-z0-9\s]", " ", text.lower())

        # 단어 분리
        words = text_clean.split()

        # Stopwords 제거 및 짧은 단어(2글자 이하) 제거
        keywords = [w for w in words if w not in STOPWORDS and len(w) > 2]

        return keywords

    def _calculate_match(
        self, transcript_lower: str, keywords: list[str], original_transcript: str
    ) -> tuple[float, str | None]:
        """
        키워드 매칭 및 confidence 계산

        Args:
            transcript_lower: 소문자 변환된 transcript
            keywords: 매칭할 키워드 리스트
            original_transcript: 원본 transcript (evidence span 추출용)

        Returns:
            (confidence, evidence_span) 튜플
        """
        if not keywords:
            return 0.0, None

        # 각 키워드가 transcript에 포함되는지 확인
        matched_keywords: list[str] = []
        keyword_positions: list[int] = []

        for keyword in keywords:
            # 정확 매칭 시도
            if keyword in transcript_lower:
                matched_keywords.append(keyword)
                pos = transcript_lower.find(keyword)
                keyword_positions.append(pos)
            else:
                # Fuzzy matching 시도 (유사도 0.8 이상)
                best_ratio = 0.0
                best_pos = -1

                # 슬라이딩 윈도우로 유사한 부분 찾기
                words_in_transcript = transcript_lower.split()
                for i, word in enumerate(words_in_transcript):
                    ratio = SequenceMatcher(None, keyword, word).ratio()
                    if ratio > best_ratio:
                        best_ratio = ratio
                        if ratio >= 0.8:  # Fuzzy match threshold
                            # 위치 추정
                            text_before = " ".join(words_in_transcript[:i])
                            best_pos = len(text_before) + (1 if text_before else 0)

                if best_ratio >= 0.8:
                    matched_keywords.append(keyword)
                    if best_pos >= 0:
                        keyword_positions.append(best_pos)

        # Confidence 계산
        confidence = len(matched_keywords) / len(keywords) if keywords else 0.0

        # Evidence span 추출
        evidence_span: str | None = None
        if matched_keywords and keyword_positions:
            # 매칭된 키워드 주변 문맥 추출
            min_pos = min(keyword_positions)
            max_pos = max(keyword_positions)

            # 문맥 범위 확장 (앞뒤로 단어 추가)
            start = max(0, min_pos - 20)
            end = min(len(original_transcript), max_pos + 50)

            evidence_span = original_transcript[start:end].strip()

            # 불완전한 문장 시작/끝 정리
            if start > 0 and not original_transcript[start].isupper():
                # 첫 단어 경계 찾기
                space_idx = evidence_span.find(" ")
                if space_idx > 0:
                    evidence_span = evidence_span[space_idx + 1 :]

            if end < len(original_transcript):
                # 마지막 단어 경계 찾기
                last_space = evidence_span.rfind(" ")
                if last_space > 0:
                    evidence_span = evidence_span[:last_space]

        return confidence, evidence_span


# 싱글톤 인스턴스
_service: BlueprintComparisonService | None = None


def get_blueprint_comparison_service() -> BlueprintComparisonService:
    """Blueprint Comparison Service 싱글톤 인스턴스 반환"""
    global _service
    if _service is None:
        _service = BlueprintComparisonService()
    return _service
