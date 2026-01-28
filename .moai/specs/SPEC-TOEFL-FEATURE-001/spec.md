# SPEC-TOEFL-FEATURE-001: ETS SpeechRater 피처 시스템 및 피드백 고도화

## TAG BLOCK

```yaml
SPEC-ID: SPEC-TOEFL-FEATURE-001
Title: ETS SpeechRater 피처 시스템 및 피드백 고도화
Created: 2026-01-25
Status: completed
Priority: Medium
Assigned: workflow-spec
Dependencies:
  - SPEC-TOEFL-001 (Worker, 기존 피처 추출)
  - SPEC-TOEFL-SCHEMA-001 (Blueprint/AnswerKey 모델)
Labels: [backend, scoring, feature-extraction, feedback]
Lifecycle: spec-anchored
```

---

## HISTORY

| 날짜 | 버전 | 작성자 | 변경 내용 |
|------|------|--------|----------|
| 2026-01-25 | 1.0.0 | workflow-spec | 초기 SPEC 작성 |
| 2026-01-28 | 2.0.0 | Claude Sonnet 4.5 | Phase 1+2 구현 완료: 13/13 features 활성화, spaCy 3.7.5 설치, 커버리지 64% 달성 |

---

## 개요

ETS SpeechRater v5.0 기반의 20개 핵심 Feature와 3-tier 피드백 시스템을 구현합니다. 이 SPEC은 기존 SPEC-TOEFL-001의 채점 파이프라인을 확장하여, 보다 정교한 피처 추출과 계층화된 피드백 제공을 목표로 합니다.

### 핵심 가치

- **ETS 공식 피처 호환**: SpeechRater v5.0 20개 피처 완전 구현
- **계층적 피드백**: Basic/Standard/Premium 3-tier 구조로 비즈니스 모델 지원
- **Blueprint 비교**: Integrated Task의 정보 단위 커버리지 분석
- **Structure 비교**: Independent Task의 응답 구조 패턴 매칭

---

## Environment (환경)

### 기술 스택 (기존 SPEC-TOEFL-001 확장)

#### Backend (API 서버)
- **FastAPI**: 0.115+ (기존 유지)
- **PostgreSQL**: 15+ (기존 유지)
- **SQLAlchemy 2.0**: async 지원 (기존 유지)
- **Pydantic v2.9**: 데이터 검증 (기존 유지)
- **Celery + Redis**: 비동기 작업 큐 (기존 유지)

#### 신규 의존성
- **spaCy**: 3.7.5 (Python 3.9 호환, 문법 분석, POS 태깅) ✅ 설치됨
- **scikit-learn**: 1.6.1 (TF-IDF, cosine similarity) ✅ 설치됨
- **nltk**: 3.9.2 (어휘 분석, 빈도 계산) ✅ 설치됨
- **scipy**: 1.13.1 (scikit-learn 의존성) ✅ 설치됨
- **textstat**: 0.7+ (텍스트 복잡도 분석) - Phase 2 Optional
- **librosa**: 0.10+ (오디오 피처 추출, requires_audio=true 피처용) - Phase 2 Optional
- **parselmouth**: 0.4+ (Praat 기반 음향 분석) - Phase 2 Optional

#### 오디오 분석 (requires_audio=true 피처용)
- **Praat-parselmouth**: 피치, 포먼트, 강세 분석
- **librosa**: 스펙트럼 분석, 음량 변화
- **webrtcvad**: Voice Activity Detection (기존)

### 운영 환경
- **Platform**: Linux (Docker) / macOS (개발)
- **Python**: 3.11+ (spaCy, librosa 호환)
- **RAM**: 최소 4GB (spaCy 모델 + librosa)

---

## Assumptions (가정사항)

### 비즈니스 가정

1. **사용자 구독 티어가 존재**한다고 가정합니다 (Basic/Standard/Premium).
2. **피드백 레벨은 구독 티어에 연동**되어 비즈니스 모델을 지원합니다.
3. **Blueprint와 AnswerKey 데이터가 SPEC-TOEFL-SCHEMA-001에서 정의**된다고 가정합니다.

### 기술 가정

1. **spaCy en_core_web_lg 모델이 서버에 설치**되어 있다고 가정합니다.
2. **librosa와 parselmouth가 오디오 파일에 접근 가능**하다고 가정합니다.
3. **기존 Whisper ASR 파이프라인의 segments 데이터를 활용**할 수 있다고 가정합니다.
4. **Celery Worker가 오디오 파일을 로컬에 다운로드 후 분석**한다고 가정합니다.

### 팀 가정

1. **개발자가 NLP 및 오디오 분석 라이브러리에 대한 기본 지식**을 보유하고 있다고 가정합니다.
2. **ETS SpeechRater 논문 및 문서를 참고**하여 피처 계산 로직을 검증할 수 있다고 가정합니다.

### 리스크 분석

| 가정사항 | 신뢰도 | 근거 | 틀렸을 경우 리스크 | 검증 방법 |
|---------|--------|------|-------------------|----------|
| spaCy 모델 정확도 | High | 공식 벤치마크 | 문법 오류 탐지 정확도 저하 | 테스트 데이터셋으로 평가 |
| librosa 처리 시간 | Medium | 일반 벤치마크 | Worker 지연 | POC에서 성능 테스트 |
| requires_audio=true 피처 지원 | Medium | 선택적 구현 | 발음/운율 피처 미제공 | Phase 2로 분리 가능 |

---

## Requirements (요구사항)

### 1. Ubiquitous Requirements (시스템 전체 필수 요구사항)

#### REQ-FEAT-001: 피처 스키마 일관성
**시스템은 항상** 모든 피처 추출 결과를 SpeechRater v5.0 호환 JSON 스키마로 반환**해야 한다**.

**WHY**: 피처 데이터의 일관성은 LLM 분석 및 점수 계산의 기반
**IMPACT**: 스키마 불일치 시 LLM 프롬프트 오류 및 채점 실패

#### REQ-FEAT-002: 피처 코드 표준화
**시스템은 항상** 피처 코드를 ETS 표준 명명 규칙(silmean, wpsec, cvamax 등)으로 사용**해야 한다**.

**WHY**: 외부 시스템 연동 및 연구 재현성 보장
**IMPACT**: 비표준 명명 시 데이터 호환성 상실

#### REQ-FEAT-003: 피드백 레벨 검증
**시스템은 항상** 요청된 피드백 레벨(Basic/Standard/Premium)이 사용자 구독 티어와 일치하는지 검증**해야 한다**.

**WHY**: 비즈니스 규칙 준수 및 무단 접근 방지
**IMPACT**: 검증 없이는 프리미엄 기능 무단 사용 가능

---

### 2. Event-Driven Requirements (이벤트 기반 요구사항)

#### REQ-FEAT-004: Delivery 피처 추출
**WHEN** ASR 결과(transcript, segments)가 생성되면,
**THEN** 시스템은 다음 8개 Delivery 피처를 추출**해야 한다**:
- `silmean`: 평균 침묵 길이 (초)
- `wpsec`: 발화 속도 (초당 단어 수)
- `secpchk`: 평균 청크 길이 (침묵 사이 발화 구간)
- `numrep`: 반복 횟수
- `numdff`: 비유창성 횟수 (필러, 거짓 시작)
- `silpsecutt`: 침묵 빈도 (초당 침묵 발생 횟수)
- `IPC`: 절 내 중단 횟수
- `withinClauseSilMean`: 절 내 침묵 평균 길이

**WHY**: Delivery 피처는 TOEFL 점수의 ~38% 가중치
**IMPACT**: Delivery 분석 누락 시 채점 정확도 대폭 하락

#### REQ-FEAT-005: Grammar 피처 추출
**WHEN** transcript가 생성되면,
**THEN** 시스템은 다음 2개 Grammar 피처를 추출**해야 한다**:
- `poscvamax`: POS n-gram 기반 문법 프로파일 유사도
- `dep_clauses_per_clause`: 평균 종속절 수

**WHY**: Grammar 피처는 언어 사용 품질 평가의 핵심
**IMPACT**: 문법 분석 누락 시 언어 사용 점수 부정확

#### REQ-FEAT-006: Vocabulary 피처 추출
**WHEN** transcript가 생성되면,
**THEN** 시스템은 다음 3개 Vocabulary 피처를 추출**해야 한다**:
- `cvamax`: Content Vector Analysis 기반 어휘 유사도
- `types`: 고유 단어 수 (Type 수)
- `logFreq`: 단어들의 평균 로그 빈도

**WHY**: Vocabulary 피처는 TOEFL 점수의 ~20% 가중치
**IMPACT**: 어휘 분석 누락 시 언어 사용 평가 불완전

#### REQ-FEAT-007: Pronunciation 피처 추출 (Optional)
**WHEN** 원본 오디오 파일이 가용하고 `requires_audio=true` 피처가 요청되면,
**THEN** 시스템은 다음 2개 Pronunciation 피처를 추출**해야 한다**:
- `L1`: 원어민 음향모델 log-likelihood 점수
- `amscore`: 비원어민 음향모델 log-likelihood 점수

**WHY**: Pronunciation 피처는 발음 정확도 평가의 핵심
**IMPACT**: 미구현 시 발음 점수 추정으로 대체 (정확도 하락)

#### REQ-FEAT-008: Prosody & Rhythm 피처 추출 (Optional)
**WHEN** 원본 오디오 파일이 가용하고 `requires_audio=true` 피처가 요청되면,
**THEN** 시스템은 다음 5개 Prosody & Rhythm 피처를 추출**해야 한다**:
- `powstddev`: 음량 변화량 (프레임별 파워 표준편차)
- `pitdeltanorm`: 피치 범위 (정규화된 피치 변화 범위)
- `phn_shift`: 모음 지속시간 편차
- `rpvic`: 자음 간격 PVI (Pairwise Variability Index)
- `stresyllmdev`: 강세 음절 타이밍 편차

**WHY**: Prosody 피처는 자연스러운 발화 평가의 핵심
**IMPACT**: 미구현 시 운율 점수 추정으로 대체 (정확도 하락)

#### REQ-FEAT-009: Blueprint 비교 (Integrated Task)
**WHEN** Integrated Task의 채점이 요청되고 Blueprint 데이터가 존재하면,
**THEN** 시스템은 다음 Blueprint 비교 결과를 생성**해야 한다**:
- `total_units`: 전체 정보 단위 수
- `covered_count`: 응답에서 언급된 단위 수
- `coverage_percentage`: 커버리지 백분율
- `unit_details`: 각 단위별 언급 여부 및 위치

**WHY**: Integrated Task는 소스 자료의 정보 통합 능력 평가
**IMPACT**: Blueprint 비교 없이는 Topic Development 점수 부정확

#### REQ-FEAT-010: Structure 비교 (Independent Task)
**WHEN** Independent Task의 채점이 요청되면,
**THEN** 시스템은 다음 Structure 비교 결과를 생성**해야 한다**:
- `topic_type`: 문제 유형 (preference, agree_disagree, explain)
- `expected_pattern`: 기대 응답 구조 패턴
- `detected_pattern`: 감지된 응답 구조 패턴
- `component_details`: 각 구성 요소별 감지 여부 및 위치

**WHY**: Independent Task는 논리적 구조와 주장 전개 능력 평가
**IMPACT**: Structure 비교 없이는 구조 점수 부정확

#### REQ-FEAT-011: 피드백 생성 (Basic 레벨)
**WHEN** 채점이 완료되고 Basic 레벨 피드백이 요청되면,
**THEN** 시스템은 다음 정보를 포함한 피드백을 생성**해야 한다**:
- `overall`: 전체 점수 (0-30)
- `band`: 점수대 (high/mid/low)
- `summary`: 3줄 요약
- `top_strengths`: 강점 2개
- `top_improvements`: 개선점 2개

**WHY**: Basic 레벨은 무료 티어 사용자에게 핵심 정보 제공
**IMPACT**: 기본 피드백 없이는 사용자 가치 전달 불가

#### REQ-FEAT-012: 피드백 생성 (Standard 레벨)
**WHEN** 채점이 완료되고 Standard 레벨 피드백이 요청되면,
**THEN** 시스템은 Basic 레벨에 추가로 다음 정보를 포함**해야 한다**:
- `dimension_scores`: Delivery, Language Use, Topic Development 개별 점수
- `feature_analysis_summary`: 주요 피처 분석 요약
- `blueprint_coverage_percentage` (Integrated) 또는 `structure_match_percentage` (Independent)

**WHY**: Standard 레벨은 기본 구독자에게 심화 분석 제공
**IMPACT**: 중간 단계 없이는 무료↔프리미엄 전환율 저하

#### REQ-FEAT-013: 피드백 생성 (Premium 레벨)
**WHEN** 채점이 완료되고 Premium 레벨 피드백이 요청되면,
**THEN** 시스템은 Standard 레벨에 추가로 다음 정보를 포함**해야 한다**:
- `full_feature_analysis`: 전체 20개 피처 분석 결과
- `unit_details` (Integrated) 또는 `component_details` (Independent)
- `comparison_to_sample`: 모범 답안과의 비교 분석
- `history_context`: 이전 응답 대비 변화 추이

**WHY**: Premium 레벨은 프리미엄 구독자에게 최대 가치 제공
**IMPACT**: 프리미엄 차별화 없이는 구독 전환 유인 부족

---

### 3. State-Driven Requirements (상태 기반 요구사항)

#### REQ-FEAT-014: 오디오 파일 가용성 상태
**IF** 오디오 파일이 서버에 존재하지 않거나 접근 불가**이면**,
**THEN** 시스템은 `requires_audio=false` 피처만 추출하고, `requires_audio=true` 피처는 `null`로 반환**해야 한다**.

**WHY**: 오디오 의존 피처의 graceful degradation 보장
**IMPACT**: 오류 처리 없이는 전체 채점 실패

#### REQ-FEAT-015: Blueprint 데이터 가용성 상태
**IF** Integrated Task에 대해 Blueprint 데이터가 존재하지 않**으면**,
**THEN** 시스템은 Blueprint 비교를 건너뛰고, `blueprint_comparison: null`로 반환**해야 한다**.

**WHY**: Blueprint 없는 Task에 대한 graceful degradation 보장
**IMPACT**: 오류 처리 없이는 Integrated Task 채점 실패

---

### 4. Unwanted Requirements (금지 요구사항)

#### REQ-FEAT-016: 권한 없는 피드백 레벨 접근 금지
**시스템은** 사용자 구독 티어보다 높은 피드백 레벨을 반환**하지 않아야 한다**.
예: Basic 구독자에게 Premium 피드백 반환 금지

**WHY**: 비즈니스 모델 및 수익 보호
**IMPACT**: 무단 접근 시 유료 서비스 가치 하락

#### REQ-FEAT-017: 미검증 피처 데이터 저장 금지
**시스템은** 피처 추출 결과를 스키마 검증 없이 데이터베이스에 저장**하지 않아야 한다**.

**WHY**: 데이터 무결성 및 LLM 분석 정확성 보장
**IMPACT**: 잘못된 데이터 저장 시 후속 분석 오류

---

### 5. Optional Requirements (선택 요구사항)

#### REQ-FEAT-018: 실시간 피처 추출 스트리밍
**가능하면**, Worker가 피처 추출 단계별 진행 상황을 WebSocket으로 스트리밍하여 UI에서 실시간 표시**할 수 있다**.

**WHY**: 사용자 대기 경험 개선
**IMPACT**: 미구현 시에도 폴링으로 상태 확인 가능

#### REQ-FEAT-019: 피처 캐싱
**가능하면**, 동일 오디오에 대한 피처 추출 결과를 캐싱하여 재분석 시 재사용**할 수 있다**.

**WHY**: 리소스 효율성 및 응답 시간 단축
**IMPACT**: 미구현 시에도 매번 추출 수행

---

## Specifications (세부 명세)

### Part A: SpeechRater v5.0 피처 정의 (20개)

#### Delivery Features (~38% 가중치)

| Feature Code | 한글명 | 정의 | requires_audio | 계산 방식 |
|-------------|--------|------|----------------|----------|
| silmean | 평균 침묵 길이 | 침묵(pause)의 평균 길이(초) | false | segments gap 평균 |
| wpsec | 발화 속도 | 초당 단어 수 (WPM/60) | false | word_count / duration_sec |
| secpchk | 평균 청크 길이 | 침묵 사이 발화 구간 평균 길이 | false | 청크 duration 평균 |
| numrep | 반복 횟수 | 단어/구문 반복 횟수 | false | n-gram 반복 탐지 |
| numdff | 비유창성 횟수 | 필러(uh, um), 거짓 시작 등 | false | 필러 패턴 매칭 |
| silpsecutt | 침묵 빈도 | 초당 침묵 발생 횟수 | false | pause_count / duration_sec |
| IPC | 절 내 중단 | 절 내부 중단/재구성 횟수 | false | spaCy 절 분석 + pause 매핑 |
| withinClauseSilMean | 절 내 침묵 평균 | 절 내부 침묵 평균 길이 | false | 절 내 pause 평균 |

#### Pronunciation Features (~12% 가중치)

| Feature Code | 한글명 | 정의 | requires_audio | 계산 방식 |
|-------------|--------|------|----------------|----------|
| L1 | 원어민 음향모델 점수 | 원어민 음향모델 log-likelihood | true | 음향모델 추론 (Phase 2) |
| amscore | 비원어민 음향모델 점수 | 비원어민 음향모델 log-likelihood | true | 음향모델 추론 (Phase 2) |

#### Prosody & Rhythm Features (~14% 가중치)

| Feature Code | 한글명 | 정의 | requires_audio | 계산 방식 |
|-------------|--------|------|----------------|----------|
| powstddev | 음량 변화량 | 프레임별 파워 표준편차 | true | librosa RMS std |
| pitdeltanorm | 피치 범위 | 정규화된 피치 변화 범위 | true | parselmouth pitch range |
| phn_shift | 모음 지속시간 편차 | 기대 모음 길이 대비 편차 | true | 음소 정렬 (Phase 2) |
| rpvic | 자음 간격 PVI | 자음 간격 Pairwise Variability Index | true | 음소 정렬 (Phase 2) |
| stresyllmdev | 강세 음절 타이밍 편차 | 강세 음절 간 간격 편차 | true | parselmouth intensity |

#### Grammar Features (~6% 가중치)

| Feature Code | 한글명 | 정의 | requires_audio | 계산 방식 |
|-------------|--------|------|----------------|----------|
| poscvamax | POS 문법 유사도 | POS n-gram 기반 문법 프로파일 유사도 | false | spaCy POS + CVA |
| dep_clauses_per_clause | 절당 종속절 수 | 평균 종속절 수 | false | spaCy dependency parsing |

#### Vocabulary Features (~20% 가중치)

| Feature Code | 한글명 | 정의 | requires_audio | 계산 방식 |
|-------------|--------|------|----------------|----------|
| cvamax | 어휘 CVA 점수 | Content Vector Analysis 기반 어휘 유사도 | false | TF-IDF + 코사인 유사도 |
| types | 고유 단어 수 | 응답 내 고유 단어 타입 수 | false | set(tokens) 크기 |
| logFreq | 평균 단어 빈도 | 단어들의 평균 로그 빈도 | false | SUBTLEX 빈도 테이블 |

---

### Part B: 피드백 스키마 고도화

#### 점수 구조 스키마

```json
{
  "scores": {
    "overall": 23,
    "band": "mid",
    "dimensions": {
      "delivery": {
        "score": 7.5,
        "weight": 0.40,
        "sub_scores": {
          "fluency": 7.0,
          "pace": 8.0,
          "pausing": 7.5
        }
      },
      "language_use": {
        "score": 7.0,
        "weight": 0.30,
        "sub_scores": {
          "grammar": 7.0,
          "vocabulary": 7.0
        }
      },
      "topic_development": {
        "score": 8.0,
        "weight": 0.30,
        "sub_scores": {
          "content": 8.0,
          "coherence": 8.0
        }
      }
    }
  }
}
```

#### 피처 분석 결과 스키마

```json
{
  "feature_analysis": {
    "delivery": {
      "silmean": 0.42,
      "silmean_rating": "acceptable",
      "wpsec": 2.13,
      "wpsec_rating": "good",
      "numrep": 3,
      "numrep_rating": "needs_work",
      "numdff": 5,
      "numdff_rating": "acceptable"
    },
    "language_use": {
      "types": 74,
      "types_rating": "good",
      "logFreq": 3.2,
      "logFreq_rating": "good",
      "dep_clauses_per_clause": 0.8,
      "dep_clauses_per_clause_rating": "acceptable"
    },
    "topic_development": {
      "coverage_ratio": 0.75,
      "coverage_rating": "good",
      "structure_score": 0.85,
      "structure_rating": "good"
    }
  }
}
```

#### Blueprint 비교 스키마 (Integrated Task)

```json
{
  "blueprint_comparison": {
    "total_units": 4,
    "covered_count": 3,
    "coverage_percentage": 75,
    "unit_details": [
      {
        "unit_id": "U1",
        "description": "Main topic of lecture",
        "covered": true,
        "evidence_span": [45, 82]
      },
      {
        "unit_id": "U2",
        "description": "First supporting detail",
        "covered": true,
        "evidence_span": [95, 132]
      },
      {
        "unit_id": "U3",
        "description": "Second supporting detail",
        "covered": false,
        "evidence_span": null
      },
      {
        "unit_id": "U4",
        "description": "Conclusion or summary",
        "covered": true,
        "evidence_span": [180, 210]
      }
    ]
  }
}
```

#### Structure 비교 스키마 (Independent Task)

```json
{
  "structure_comparison": {
    "topic_type": "preference",
    "expected_pattern": "position_reason_example",
    "detected_pattern": "position_reason",
    "match_percentage": 66.7,
    "component_details": [
      {
        "component": "position",
        "expected": true,
        "detected": true,
        "span": [0, 35],
        "quality": "clear"
      },
      {
        "component": "reason_1",
        "expected": true,
        "detected": true,
        "span": [36, 95],
        "quality": "adequate"
      },
      {
        "component": "example_1",
        "expected": true,
        "detected": false,
        "span": null,
        "quality": null
      },
      {
        "component": "reason_2",
        "expected": true,
        "detected": false,
        "span": null,
        "quality": null
      }
    ]
  }
}
```

#### 피드백 레벨별 포함 내용

| 필드 | Basic | Standard | Premium |
|------|-------|----------|---------|
| overall score | O | O | O |
| band | O | O | O |
| summary (3줄) | O | O | O |
| top_strengths (2개) | O | O | O |
| top_improvements (2개) | O | O | O |
| dimension_scores | X | O | O |
| feature_analysis 요약 | X | O | O |
| blueprint/structure coverage % | X | O | O |
| full_feature_analysis (20개) | X | X | O |
| unit_details / component_details | X | X | O |
| comparison_to_sample | X | X | O |
| history_context | X | X | O |

---

### API Endpoints (추가/수정)

#### 1. 피처 추출 설정 조회
- `GET /v1/features/config`: 피처 목록 및 requires_audio 여부 조회

#### 2. Job 생성 (수정)
- `POST /v1/jobs`: 기존 + `feedback_level` 파라미터 추가
  - Request: `{"audio_key": "...", "task_id": 1, "feedback_level": "standard"}`

#### 3. 피드백 리포트 조회 (수정)
- `GET /v1/jobs/{job_id}/report`: 피드백 레벨에 따른 필터링된 결과 반환

---

### Database Schema (추가)

#### feature_configs 테이블
```sql
CREATE TABLE feature_configs (
    id SERIAL PRIMARY KEY,
    feature_code VARCHAR(50) UNIQUE NOT NULL,
    feature_name_ko VARCHAR(100) NOT NULL,
    category VARCHAR(50) NOT NULL,  -- delivery, pronunciation, prosody, grammar, vocabulary
    weight DECIMAL(4,2) NOT NULL,
    requires_audio BOOLEAN DEFAULT false,
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### user_subscriptions 테이블
```sql
CREATE TABLE user_subscriptions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    tier VARCHAR(20) NOT NULL,  -- basic, standard, premium
    started_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP,
    is_active BOOLEAN DEFAULT true
);

CREATE INDEX idx_subscriptions_user_id ON user_subscriptions(user_id);
```

---

## Traceability (추적성)

- **관련 SPEC**: SPEC-TOEFL-001, SPEC-TOEFL-SCHEMA-001
- **Epic**: TOEFL Speaking Rater v2.0
- **Labels**: `backend`, `scoring`, `feature-extraction`, `feedback`

---

## 참고 문서

- **ETS SpeechRater v5.0 Documentation**: ETS 내부 문서
- **spaCy Documentation**: https://spacy.io/api
- **librosa Documentation**: https://librosa.org/doc/
- **Parselmouth Documentation**: https://parselmouth.readthedocs.io/

---

**작성자**: workflow-spec
**검토자**: 수연
**버전**: 1.0.0
**최종 수정일**: 2026-01-25
