"""Grammar Feature 추출 서비스

SPEC-TOEFL-FEATURE-001: ETS SpeechRater v5.0 Grammar Features
- poscvamax: POS n-gram 기반 문법 프로파일 유사도
- dep_clauses_per_clause: 평균 종속절 수

Requirements:
- spaCy 3.8+ with en_core_web_lg model
- Python 3.9+ compatibility
"""

import logging

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# spaCy 가용성 확인
try:
    import spacy
    from spacy.tokens import Doc

    SPACY_AVAILABLE = True
    logger.info("spaCy is available for grammar feature extraction")
except ImportError:
    SPACY_AVAILABLE = False
    logger.warning("spaCy is not installed. Grammar features will return None.")


class GrammarFeatures(BaseModel):
    """Grammar 신호 (문법 특징)"""

    poscvamax: float | None = Field(
        default=None,
        description="POS n-gram 기반 문법 프로파일 유사도 (0.0-1.0)",
    )
    dep_clauses_per_clause: float | None = Field(
        default=None,
        ge=0.0,
        description="평균 종속절 수",
    )
    spacy_available: bool = Field(
        default=False,
        description="spaCy 가용성 여부",
    )


class GrammarFeatureExtractor:
    """
    Grammar 신호 추출기

    spaCy를 사용하여 문법 특징을 추출합니다.
    - POS tagging 기반 문법 프로파일
    - Dependency parsing 기반 절 분석
    """

    def __init__(self) -> None:
        """추출기 초기화"""
        self._nlp: object | None = None
        if SPACY_AVAILABLE:
            try:
                # Try to load models in order of preference
                for model_name in ["en_core_web_lg", "en_core_web_md", "en_core_web_sm"]:
                    try:
                        self._nlp = spacy.load(model_name)
                        logger.info(f"spaCy model '{model_name}' loaded successfully")
                        break
                    except OSError:
                        continue

                if self._nlp is None:
                    logger.warning(
                        "No spaCy model found. Install with: "
                        "python -m spacy download en_core_web_sm"
                    )
            except Exception as e:
                logger.warning(f"Failed to load spaCy model: {e}")
                self._nlp = None

    def extract(self, transcript: str, reference_text: str | None = None) -> GrammarFeatures:
        """
        Transcript에서 Grammar 신호 추출

        Args:
            transcript: Whisper ASR 결과 텍스트
            reference_text: 참조 텍스트 (CVA 계산용, Optional)

        Returns:
            GrammarFeatures: 추출된 문법 신호
        """
        if not SPACY_AVAILABLE or self._nlp is None:
            logger.warning("Grammar feature extraction skipped (spaCy not available)")
            return GrammarFeatures(
                poscvamax=None,
                dep_clauses_per_clause=None,
                spacy_available=False,
            )

        logger.info("Extracting grammar features with spaCy")

        # spaCy 문서 생성
        doc = self._nlp(transcript)

        # 1. poscvamax: POS n-gram 유사도
        poscvamax = self._calculate_poscvamax(doc, reference_text)

        # 2. dep_clauses_per_clause: 종속절 수
        dep_clauses_per_clause = self._calculate_dependent_clauses(doc)

        return GrammarFeatures(
            poscvamax=poscvamax,
            dep_clauses_per_clause=dep_clauses_per_clause,
            spacy_available=True,
        )

    def _calculate_poscvamax(
        self, doc: "Doc", reference_text: str | None
    ) -> float | None:
        """
        POS n-gram 기반 Content Vector Analysis (CVA) 유사도 계산

        Args:
            doc: spaCy Doc object
            reference_text: 참조 텍스트 (Optional)

        Returns:
            CVA 유사도 점수 (0.0-1.0) 또는 None
        """
        if reference_text is None:
            # 참조 텍스트가 없으면 기본 POS 분포 분석
            pos_tags = [token.pos_ for token in doc if not token.is_punct]
            if not pos_tags:
                return None

            # POS 다양성 점수로 대체 (0.0-1.0)
            pos_diversity = len(set(pos_tags)) / len(pos_tags)
            return round(pos_diversity, 3)

        # 참조 텍스트와 비교하는 로직은 추후 구현
        # TODO: TF-IDF 기반 POS n-gram 유사도 계산
        return None

    def _calculate_dependent_clauses(self, doc: "Doc") -> float:
        """
        평균 종속절 수 계산

        Args:
            doc: spaCy Doc object

        Returns:
            평균 종속절 수
        """
        # 절 감지: ROOT 동사를 기준으로
        root_verbs = [token for token in doc if token.dep_ == "ROOT" and token.pos_ == "VERB"]

        if not root_verbs:
            return 0.0

        # 종속절 감지: 주절에 종속된 동사 수
        total_dependent_clauses = 0
        for root in root_verbs:
            # ROOT에 종속된 동사 찾기 (advcl, ccomp, xcomp, acl, relcl 등)
            dependent_clause_deps = {"advcl", "ccomp", "xcomp", "acl", "relcl"}
            dependents = [
                child for child in root.children
                if child.dep_ in dependent_clause_deps
            ]
            total_dependent_clauses += len(dependents)

        # 평균 계산
        avg_dependent_clauses = total_dependent_clauses / len(root_verbs)
        return round(avg_dependent_clauses, 2)


# 싱글톤 인스턴스
_extractor: GrammarFeatureExtractor | None = None


def get_grammar_feature_extractor() -> GrammarFeatureExtractor:
    """Grammar Feature Extractor 싱글톤 인스턴스 반환"""
    global _extractor
    if _extractor is None:
        _extractor = GrammarFeatureExtractor()
    return _extractor
