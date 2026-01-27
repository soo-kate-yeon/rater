# SPEC-TOEFL-FEATURE-001: 구현 계획

## TAG BLOCK

```yaml
SPEC-ID: SPEC-TOEFL-FEATURE-001
Document: Implementation Plan
Version: 1.0.0
Created: 2026-01-25
```

---

## HISTORY

| 날짜 | 버전 | 작성자 | 변경 내용 |
|------|------|--------|----------|
| 2026-01-25 | 1.0.0 | workflow-spec | 초기 구현 계획 작성 |

---

## 구현 개요

이 문서는 SPEC-TOEFL-FEATURE-001의 구현 계획을 정의합니다. ETS SpeechRater v5.0 기반 20개 피처와 3-tier 피드백 시스템 구현을 위한 기술적 접근 방식, 마일스톤, 아키텍처 설계를 포함합니다.

---

## 마일스톤

### Primary Goal: Text-based 피처 추출 (Phase 1)

**목표**: requires_audio=false인 12개 피처 구현

**포함 작업**:
1. Delivery 피처 추출기 확장 (8개 피처)
   - `silmean`, `wpsec`, `secpchk` - 기존 로직 활용
   - `numrep`, `numdff` - 패턴 매칭 추가
   - `silpsecutt`, `IPC`, `withinClauseSilMean` - spaCy 통합
2. Grammar 피처 추출기 신규 개발 (2개 피처)
   - `poscvamax` - POS n-gram 분석
   - `dep_clauses_per_clause` - 의존 구문 분석
3. Vocabulary 피처 추출기 신규 개발 (3개 피처)
   - `cvamax` - TF-IDF 기반 CVA
   - `types` - 고유 단어 수
   - `logFreq` - SUBTLEX 빈도 기반 계산

**파일 생성/수정**:
- `src/services/delivery_features.py` (수정)
- `src/services/grammar_features.py` (신규)
- `src/services/vocabulary_features.py` (신규)
- `src/schemas/features.py` (신규)

**의존성**: spaCy en_core_web_lg, nltk, textstat

---

### Secondary Goal: 3-tier 피드백 시스템 (Phase 2)

**목표**: Basic/Standard/Premium 피드백 레벨 구현

**포함 작업**:
1. 피드백 레벨 스키마 정의
   - `FeedbackLevel` Enum (basic, standard, premium)
   - 레벨별 응답 스키마 정의
2. 사용자 구독 티어 모델 추가
   - `UserSubscription` 모델
   - 구독 검증 미들웨어
3. 피드백 생성 로직 레벨화
   - Basic: 요약 + 강점/개선점
   - Standard: + 차원별 점수 + 피처 요약
   - Premium: + 전체 피처 + 상세 비교
4. LLM 프롬프트 레벨별 분기
   - 레벨에 따른 출력 JSON 스키마 변경

**파일 생성/수정**:
- `src/schemas/feedback.py` (신규)
- `src/models/subscription.py` (신규)
- `src/services/feedback_service.py` (수정)
- `src/api/routers/jobs.py` (수정)
- `src/core/middleware.py` (신규)

**의존성**: Primary Goal 완료

---

### Tertiary Goal: Blueprint/Structure 비교 (Phase 3)

**목표**: Integrated Task Blueprint 비교 및 Independent Task Structure 비교 구현

**포함 작업**:
1. Blueprint 모델 및 비교 로직 구현
   - Blueprint JSON 스키마 정의
   - 응답-Blueprint 매칭 알고리즘
   - 커버리지 계산 로직
2. Structure 패턴 분석 구현
   - Independent Task 유형별 기대 패턴 정의
   - 응답 구조 감지 알고리즘 (spaCy + 규칙 기반)
   - 매칭률 계산 로직
3. LLM 프롬프트에 비교 결과 통합
   - Blueprint/Structure 컨텍스트 추가
   - 비교 기반 피드백 생성

**파일 생성/수정**:
- `src/models/blueprint.py` (신규)
- `src/services/blueprint_comparison.py` (신규)
- `src/services/structure_comparison.py` (신규)
- `src/schemas/comparison.py` (신규)

**의존성**: SPEC-TOEFL-SCHEMA-001 완료, Secondary Goal 완료

---

### Optional Goal: Audio-based 피처 추출 (Phase 4)

**목표**: requires_audio=true인 7개 피처 구현

**포함 작업**:
1. 오디오 분석 파이프라인 구축
   - librosa 기반 스펙트럼 분석
   - parselmouth 기반 피치/강도 분석
2. Pronunciation 피처 구현 (2개)
   - `L1`, `amscore` - 음향모델 추론 (외부 API 또는 로컬 모델)
3. Prosody & Rhythm 피처 구현 (5개)
   - `powstddev` - RMS 표준편차
   - `pitdeltanorm` - 피치 범위
   - `phn_shift`, `rpvic`, `stresyllmdev` - 음소 정렬 기반

**파일 생성/수정**:
- `src/services/audio_features.py` (신규)
- `src/services/prosody_features.py` (신규)
- `src/services/pronunciation_features.py` (신규)

**의존성**: librosa, parselmouth, 음향모델 (선택)

---

## 기술적 접근 방식

### 아키텍처 설계

```
┌─────────────────────────────────────────────────────────────┐
│                      API Layer (FastAPI)                     │
│  /v1/jobs (POST) → feedback_level 파라미터 추가             │
│  /v1/jobs/{id}/report (GET) → 레벨별 필터링                 │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Celery Worker Pipeline                    │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐        │
│  │ ASR     │→ │ Feature │→ │ Compare │→ │ LLM     │        │
│  │ (기존)  │  │ Extract │  │ (B/S)   │  │ Analyze │        │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘        │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Feature Extractors                        │
│  ┌───────────────┐ ┌───────────────┐ ┌───────────────┐     │
│  │ Delivery      │ │ Grammar       │ │ Vocabulary    │     │
│  │ (8 features)  │ │ (2 features)  │ │ (3 features)  │     │
│  └───────────────┘ └───────────────┘ └───────────────┘     │
│  ┌───────────────┐ ┌───────────────┐                        │
│  │ Pronunciation │ │ Prosody       │  ← requires_audio     │
│  │ (2 features)  │ │ (5 features)  │                        │
│  └───────────────┘ └───────────────┘                        │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Comparison Services                       │
│  ┌─────────────────────┐ ┌─────────────────────┐           │
│  │ Blueprint Compare   │ │ Structure Compare   │           │
│  │ (Integrated Task)   │ │ (Independent Task)  │           │
│  └─────────────────────┘ └─────────────────────┘           │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Feedback Generator                        │
│  ┌───────┐ ┌──────────┐ ┌──────────┐                       │
│  │ Basic │ │ Standard │ │ Premium  │                       │
│  └───────┘ └──────────┘ └──────────┘                       │
└─────────────────────────────────────────────────────────────┘
```

### 피처 추출 전략

#### Delivery 피처 확장

기존 `delivery_features.py`의 `DeliveryFeatureExtractor` 클래스를 확장:

```python
# src/services/delivery_features.py (확장)

class DeliveryFeatureExtractorV2(DeliveryFeatureExtractor):
    """SpeechRater v5.0 호환 Delivery 피처 추출기"""

    def __init__(self, nlp: spacy.Language):
        super().__init__()
        self.nlp = nlp  # spaCy 모델 (절 분석용)

    def extract_all(self, asr_result: ASRResult) -> DeliveryFeaturesV2:
        # 기존 피처 추출
        basic = super().extract(asr_result)

        # 추가 피처 계산
        numrep = self._count_repetitions(asr_result.transcript)
        numdff = self._count_disfluencies(asr_result.transcript)
        ipc = self._calculate_ipc(asr_result)
        within_clause_sil = self._calculate_within_clause_silence(asr_result)

        return DeliveryFeaturesV2(
            silmean=basic.pause_mean_ms / 1000,
            wpsec=basic.wpm / 60,
            secpchk=basic.chunk_mean_sec,
            numrep=numrep,
            numdff=numdff,
            silpsecutt=basic.pause_count / basic.duration_sec,
            IPC=ipc,
            withinClauseSilMean=within_clause_sil
        )
```

#### Grammar 피처 신규 개발

spaCy를 활용한 문법 분석:

```python
# src/services/grammar_features.py (신규)

class GrammarFeatureExtractor:
    """SpeechRater v5.0 호환 Grammar 피처 추출기"""

    def __init__(self, nlp: spacy.Language):
        self.nlp = nlp

    def extract(self, transcript: str) -> GrammarFeatures:
        doc = self.nlp(transcript)

        # POS n-gram 기반 CVA
        poscvamax = self._calculate_pos_cva(doc)

        # 종속절 분석
        dep_clauses = self._count_dependent_clauses(doc)
        total_clauses = self._count_total_clauses(doc)
        dep_ratio = dep_clauses / max(total_clauses, 1)

        return GrammarFeatures(
            poscvamax=poscvamax,
            dep_clauses_per_clause=dep_ratio
        )
```

#### Vocabulary 피처 신규 개발

TF-IDF 및 빈도 분석:

```python
# src/services/vocabulary_features.py (신규)

class VocabularyFeatureExtractor:
    """SpeechRater v5.0 호환 Vocabulary 피처 추출기"""

    def __init__(self, subtlex_freq: dict):
        self.subtlex_freq = subtlex_freq  # SUBTLEX 빈도 테이블

    def extract(self, transcript: str) -> VocabularyFeatures:
        tokens = word_tokenize(transcript.lower())

        # 고유 단어 수
        types = len(set(tokens))

        # 평균 로그 빈도
        log_freqs = [
            math.log10(self.subtlex_freq.get(t, 1) + 1)
            for t in tokens
        ]
        logFreq = sum(log_freqs) / max(len(log_freqs), 1)

        # CVA (TF-IDF 기반 유사도)
        cvamax = self._calculate_cva(tokens)

        return VocabularyFeatures(
            cvamax=cvamax,
            types=types,
            logFreq=logFreq
        )
```

### 피드백 레벨 구현

```python
# src/schemas/feedback.py (신규)

class FeedbackLevel(str, Enum):
    BASIC = "basic"
    STANDARD = "standard"
    PREMIUM = "premium"

class BasicFeedback(BaseModel):
    """Basic 레벨 피드백 (무료 티어)"""
    overall: int
    band: Literal["high", "mid", "low"]
    summary: list[str]  # 3줄
    top_strengths: list[str]  # 2개
    top_improvements: list[str]  # 2개

class StandardFeedback(BasicFeedback):
    """Standard 레벨 피드백 (기본 구독)"""
    dimension_scores: DimensionScores
    feature_analysis_summary: FeatureAnalysisSummary
    coverage_percentage: Optional[float]  # Blueprint 또는 Structure

class PremiumFeedback(StandardFeedback):
    """Premium 레벨 피드백 (프리미엄 구독)"""
    full_feature_analysis: FullFeatureAnalysis
    comparison_details: Union[BlueprintComparison, StructureComparison]
    comparison_to_sample: Optional[SampleComparison]
    history_context: Optional[HistoryContext]
```

### Blueprint 비교 구현

```python
# src/services/blueprint_comparison.py (신규)

class BlueprintComparisonService:
    """Integrated Task Blueprint 비교 서비스"""

    def __init__(self, nlp: spacy.Language):
        self.nlp = nlp

    async def compare(
        self,
        transcript: str,
        blueprint: Blueprint
    ) -> BlueprintComparison:
        doc = self.nlp(transcript)

        covered_units = []
        for unit in blueprint.units:
            is_covered, span = self._find_unit_evidence(doc, unit)
            covered_units.append(UnitDetail(
                unit_id=unit.id,
                description=unit.description,
                covered=is_covered,
                evidence_span=span
            ))

        covered_count = sum(1 for u in covered_units if u.covered)
        coverage_pct = (covered_count / len(blueprint.units)) * 100

        return BlueprintComparison(
            total_units=len(blueprint.units),
            covered_count=covered_count,
            coverage_percentage=coverage_pct,
            unit_details=covered_units
        )
```

### Structure 비교 구현

```python
# src/services/structure_comparison.py (신규)

class StructureComparisonService:
    """Independent Task Structure 비교 서비스"""

    PATTERNS = {
        "preference": ["position", "reason_1", "example_1", "reason_2"],
        "agree_disagree": ["position", "reason_1", "example_1", "conclusion"],
        "explain": ["topic", "point_1", "detail_1", "point_2", "detail_2"]
    }

    def __init__(self, nlp: spacy.Language):
        self.nlp = nlp

    async def compare(
        self,
        transcript: str,
        topic_type: str
    ) -> StructureComparison:
        doc = self.nlp(transcript)
        expected = self.PATTERNS.get(topic_type, [])

        detected = []
        for component in expected:
            is_detected, span, quality = self._detect_component(doc, component)
            detected.append(ComponentDetail(
                component=component,
                expected=True,
                detected=is_detected,
                span=span,
                quality=quality
            ))

        detected_count = sum(1 for c in detected if c.detected)
        match_pct = (detected_count / len(expected)) * 100 if expected else 0

        return StructureComparison(
            topic_type=topic_type,
            expected_pattern="_".join(expected),
            detected_pattern="_".join([c.component for c in detected if c.detected]),
            match_percentage=match_pct,
            component_details=detected
        )
```

---

## 리스크 및 대응 계획

### 리스크 1: spaCy 모델 로딩 시간

**영향**: Worker 시작 지연
**대응**:
- 모델 프리로딩 (Worker 시작 시 한 번만 로드)
- 싱글톤 패턴으로 모델 인스턴스 관리

### 리스크 2: Audio 피처 처리 시간

**영향**: Job 완료 시간 증가
**대응**:
- Audio 피처를 별도 Celery Task로 분리
- Optional 처리로 Audio 없이도 채점 가능하게 설계

### 리스크 3: Blueprint 데이터 부재

**영향**: Integrated Task 비교 불가
**대응**:
- Blueprint 없을 경우 graceful degradation
- LLM 기반 추론으로 대체 커버리지 추정

### 리스크 4: 구독 티어 검증 우회

**영향**: 비즈니스 손실
**대응**:
- 서버 사이드 검증 필수
- API Gateway 레벨에서 추가 검증

---

## 테스트 전략

### 단위 테스트

- 각 피처 추출기별 테스트 케이스
- 경계값 테스트 (빈 transcript, 매우 긴 응답)
- 피처값 범위 검증

### 통합 테스트

- Worker 파이프라인 전체 흐름 테스트
- 피드백 레벨별 응답 스키마 검증
- Blueprint/Structure 비교 정확도 테스트

### E2E 테스트

- 실제 오디오 파일 기반 전체 파이프라인
- 각 구독 티어별 피드백 응답 검증
- 성능 테스트 (10초 내 완료 목표)

---

## 의존성 설치

```bash
# spaCy 및 영어 모델
pip install spacy>=3.8.0
python -m spacy download en_core_web_lg

# NLP 도구
pip install nltk>=3.9.0 textstat>=0.7.0

# 오디오 분석 (Phase 4)
pip install librosa>=0.10.0 parselmouth>=0.4.0
```

---

**작성자**: workflow-spec
**버전**: 1.0.0
**최종 수정일**: 2026-01-25
