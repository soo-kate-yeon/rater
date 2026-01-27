# SPEC-TOEFL-FEATURE-001: 인수 조건

## TAG BLOCK

```yaml
SPEC-ID: SPEC-TOEFL-FEATURE-001
Document: Acceptance Criteria
Version: 1.0.0
Created: 2026-01-25
```

---

## HISTORY

| 날짜 | 버전 | 작성자 | 변경 내용 |
|------|------|--------|----------|
| 2026-01-25 | 1.0.0 | workflow-spec | 초기 인수 조건 작성 |

---

## 인수 조건 개요

이 문서는 SPEC-TOEFL-FEATURE-001의 인수 조건을 Given-When-Then 형식으로 정의합니다. 각 요구사항에 대한 검증 시나리오와 품질 게이트 기준을 포함합니다.

---

## 1. Delivery 피처 추출 (REQ-FEAT-004)

### AC-001: 8개 Delivery 피처 추출 성공

**Given**: ASR 결과가 생성되어 transcript와 segments가 존재할 때
**When**: Delivery 피처 추출기가 실행되면
**Then**:
- `silmean` 값이 0 이상의 실수로 반환된다
- `wpsec` 값이 0 초과의 실수로 반환된다
- `secpchk` 값이 0 이상의 실수로 반환된다
- `numrep` 값이 0 이상의 정수로 반환된다
- `numdff` 값이 0 이상의 정수로 반환된다
- `silpsecutt` 값이 0 이상의 실수로 반환된다
- `IPC` 값이 0 이상의 정수로 반환된다
- `withinClauseSilMean` 값이 0 이상의 실수로 반환된다

### AC-002: 빈 transcript 처리

**Given**: ASR 결과의 transcript가 빈 문자열일 때
**When**: Delivery 피처 추출기가 실행되면
**Then**:
- 모든 피처 값이 0 또는 null로 반환된다
- 오류가 발생하지 않는다

### AC-003: 침묵이 없는 응답 처리

**Given**: segments 간 간격이 모두 0.1초 미만일 때
**When**: Delivery 피처 추출기가 실행되면
**Then**:
- `silmean` 값이 0으로 반환된다
- `silpsecutt` 값이 0으로 반환된다
- `IPC` 값이 0으로 반환된다

---

## 2. Grammar 피처 추출 (REQ-FEAT-005)

### AC-004: 2개 Grammar 피처 추출 성공

**Given**: transcript가 영어 문장으로 구성되어 있을 때
**When**: Grammar 피처 추출기가 실행되면
**Then**:
- `poscvamax` 값이 0과 1 사이의 실수로 반환된다
- `dep_clauses_per_clause` 값이 0 이상의 실수로 반환된다

### AC-005: 단순 문장 분석

**Given**: transcript가 "I like coffee." 단일 문장일 때
**When**: Grammar 피처 추출기가 실행되면
**Then**:
- `dep_clauses_per_clause` 값이 0으로 반환된다 (종속절 없음)

### AC-006: 복문 분석

**Given**: transcript가 "I think that online classes are better because students can study at their own pace." 일 때
**When**: Grammar 피처 추출기가 실행되면
**Then**:
- `dep_clauses_per_clause` 값이 0 초과로 반환된다 (종속절 존재)

---

## 3. Vocabulary 피처 추출 (REQ-FEAT-006)

### AC-007: 3개 Vocabulary 피처 추출 성공

**Given**: transcript가 영어 단어들로 구성되어 있을 때
**When**: Vocabulary 피처 추출기가 실행되면
**Then**:
- `cvamax` 값이 0과 1 사이의 실수로 반환된다
- `types` 값이 1 이상의 정수로 반환된다
- `logFreq` 값이 양수 실수로 반환된다

### AC-008: 어휘 다양성 계산

**Given**: transcript가 "I I I like like coffee coffee coffee" 일 때
**When**: Vocabulary 피처 추출기가 실행되면
**Then**:
- `types` 값이 3으로 반환된다 (I, like, coffee)

### AC-009: 저빈도 어휘 처리

**Given**: transcript에 "serendipity", "ephemeral" 같은 저빈도 단어가 포함될 때
**When**: Vocabulary 피처 추출기가 실행되면
**Then**:
- `logFreq` 값이 고빈도 단어만 있는 경우보다 낮게 반환된다

---

## 4. 피드백 레벨 - Basic (REQ-FEAT-011)

### AC-010: Basic 피드백 스키마 준수

**Given**: 채점이 완료되고 Basic 레벨 피드백이 요청될 때
**When**: 피드백 생성기가 실행되면
**Then**: 응답 JSON에 다음 필드가 포함된다:
- `overall`: 0-30 사이의 정수
- `band`: "high", "mid", "low" 중 하나
- `summary`: 3개 문자열 배열
- `top_strengths`: 2개 문자열 배열
- `top_improvements`: 2개 문자열 배열

### AC-011: Basic 피드백 제한 필드 미포함

**Given**: Basic 구독자가 피드백을 요청할 때
**When**: 피드백 생성기가 실행되면
**Then**: 응답 JSON에 다음 필드가 포함되지 않는다:
- `dimension_scores`
- `full_feature_analysis`
- `unit_details`
- `comparison_to_sample`

---

## 5. 피드백 레벨 - Standard (REQ-FEAT-012)

### AC-012: Standard 피드백 스키마 준수

**Given**: 채점이 완료되고 Standard 레벨 피드백이 요청될 때
**When**: 피드백 생성기가 실행되면
**Then**: Basic 필드에 추가로 다음 필드가 포함된다:
- `dimension_scores.delivery.score`: 0-10 사이의 실수
- `dimension_scores.language_use.score`: 0-10 사이의 실수
- `dimension_scores.topic_development.score`: 0-10 사이의 실수
- `feature_analysis_summary`: 객체
- `coverage_percentage`: 0-100 사이의 실수 또는 null

### AC-013: Standard 피드백 제한 필드 미포함

**Given**: Standard 구독자가 피드백을 요청할 때
**When**: 피드백 생성기가 실행되면
**Then**: 응답 JSON에 다음 필드가 포함되지 않는다:
- `full_feature_analysis`
- `unit_details`
- `comparison_to_sample`
- `history_context`

---

## 6. 피드백 레벨 - Premium (REQ-FEAT-013)

### AC-014: Premium 피드백 스키마 준수

**Given**: 채점이 완료되고 Premium 레벨 피드백이 요청될 때
**When**: 피드백 생성기가 실행되면
**Then**: Standard 필드에 추가로 다음 필드가 포함된다:
- `full_feature_analysis`: 20개 피처 분석 객체
- `unit_details` (Integrated) 또는 `component_details` (Independent): 배열
- `comparison_to_sample`: 객체 또는 null
- `history_context`: 객체 또는 null

### AC-015: Premium 전체 피처 분석 포함

**Given**: Premium 구독자가 피드백을 요청할 때
**When**: 피드백 생성기가 실행되면
**Then**: `full_feature_analysis`에 다음 카테고리가 모두 포함된다:
- `delivery`: 8개 피처
- `grammar`: 2개 피처
- `vocabulary`: 3개 피처
- `pronunciation`: 2개 피처 (null 허용)
- `prosody`: 5개 피처 (null 허용)

---

## 7. Blueprint 비교 (REQ-FEAT-009)

### AC-016: Blueprint 비교 성공

**Given**: Integrated Task이고 Blueprint 데이터가 존재할 때
**When**: Blueprint 비교 서비스가 실행되면
**Then**: 응답에 다음 필드가 포함된다:
- `total_units`: Blueprint 정보 단위 총 수
- `covered_count`: 응답에서 언급된 단위 수
- `coverage_percentage`: 0-100 사이의 실수
- `unit_details`: 단위별 상세 정보 배열

### AC-017: Blueprint 100% 커버리지

**Given**: 응답이 Blueprint의 모든 정보 단위를 언급할 때
**When**: Blueprint 비교 서비스가 실행되면
**Then**:
- `coverage_percentage`가 100으로 반환된다
- 모든 `unit_details[].covered`가 true이다

### AC-018: Blueprint 부분 커버리지

**Given**: 응답이 Blueprint의 4개 단위 중 3개만 언급할 때
**When**: Blueprint 비교 서비스가 실행되면
**Then**:
- `covered_count`가 3으로 반환된다
- `coverage_percentage`가 75로 반환된다
- 3개의 `unit_details[].covered`가 true이고 1개가 false이다

### AC-019: Blueprint 데이터 없음 처리

**Given**: Integrated Task이지만 Blueprint 데이터가 없을 때
**When**: Blueprint 비교 서비스가 실행되면
**Then**:
- `blueprint_comparison`이 null로 반환된다
- 오류가 발생하지 않는다

---

## 8. Structure 비교 (REQ-FEAT-010)

### AC-020: Structure 비교 성공

**Given**: Independent Task이고 topic_type이 "preference"일 때
**When**: Structure 비교 서비스가 실행되면
**Then**: 응답에 다음 필드가 포함된다:
- `topic_type`: "preference"
- `expected_pattern`: "position_reason_example" 등
- `detected_pattern`: 감지된 구성 요소 조합
- `component_details`: 구성 요소별 상세 정보 배열

### AC-021: 완전한 구조 감지

**Given**: 응답이 "In my opinion... First reason... For example... Second reason..." 구조일 때
**When**: Structure 비교 서비스가 실행되면
**Then**:
- `component_details`에서 position, reason_1, example_1, reason_2가 모두 detected=true이다
- `match_percentage`가 100에 가까운 값이다

### AC-022: 불완전한 구조 감지

**Given**: 응답이 "I think... because..." 만 포함할 때
**When**: Structure 비교 서비스가 실행되면
**Then**:
- `component_details`에서 일부만 detected=true이다
- `match_percentage`가 100 미만이다

---

## 9. 오디오 피처 처리 (REQ-FEAT-014)

### AC-023: 오디오 파일 없음 시 graceful degradation

**Given**: 오디오 파일이 서버에 존재하지 않을 때
**When**: 피처 추출 파이프라인이 실행되면
**Then**:
- requires_audio=false 피처 12개가 정상 추출된다
- requires_audio=true 피처 7개가 null로 반환된다
- 전체 파이프라인이 오류 없이 완료된다

### AC-024: 오디오 피처 정상 추출

**Given**: 오디오 파일이 정상적으로 접근 가능할 때
**When**: 오디오 피처 추출기가 실행되면
**Then**:
- `powstddev` 값이 양수 실수로 반환된다
- `pitdeltanorm` 값이 양수 실수로 반환된다
- 나머지 prosody 피처도 null이 아닌 값으로 반환된다

---

## 10. 구독 티어 검증 (REQ-FEAT-016)

### AC-025: 권한 없는 피드백 레벨 요청 거부

**Given**: Basic 구독자가 Premium 피드백을 요청할 때
**When**: API 엔드포인트가 호출되면
**Then**:
- HTTP 403 Forbidden 응답이 반환된다
- 에러 메시지에 구독 업그레이드 안내가 포함된다

### AC-026: 유효한 피드백 레벨 요청 허용

**Given**: Premium 구독자가 Premium 피드백을 요청할 때
**When**: API 엔드포인트가 호출되면
**Then**:
- HTTP 200 OK 응답이 반환된다
- Premium 레벨 피드백이 정상 반환된다

### AC-027: 하위 피드백 레벨 요청 허용

**Given**: Premium 구독자가 Basic 피드백을 요청할 때
**When**: API 엔드포인트가 호출되면
**Then**:
- HTTP 200 OK 응답이 반환된다
- Basic 레벨 피드백이 반환된다 (상위 티어는 하위 레벨 요청 가능)

---

## 11. 피처 스키마 일관성 (REQ-FEAT-001)

### AC-028: 피처 JSON 스키마 검증

**Given**: 피처 추출이 완료될 때
**When**: 결과가 데이터베이스에 저장되기 전
**Then**:
- Pydantic 스키마 검증을 통과한다
- 모든 필수 필드가 존재한다
- 타입이 정의된 스키마와 일치한다

### AC-029: 잘못된 피처 데이터 저장 방지

**Given**: 피처 추출 결과에 유효하지 않은 값이 포함될 때
**When**: 저장 시도가 이루어지면
**Then**:
- ValidationError가 발생한다
- 데이터베이스에 저장되지 않는다
- Job 상태가 FAILED로 변경된다

---

## 12. API 통합 테스트

### AC-030: Job 생성 시 피드백 레벨 지정

**Given**: 인증된 사용자가 Job 생성을 요청할 때
**When**: `POST /v1/jobs` 엔드포인트가 호출되면
**Then**:
- `feedback_level` 파라미터가 허용된다
- 기본값은 사용자 구독 티어의 최대 레벨이다

### AC-031: 리포트 조회 시 레벨별 필터링

**Given**: Premium 피드백이 생성된 Job이 존재할 때
**When**: Basic 사용자가 `GET /v1/jobs/{id}/report`를 호출하면
**Then**:
- Basic 레벨 필드만 포함된 응답이 반환된다
- Premium 전용 필드는 포함되지 않는다

---

## 품질 게이트 기준

### 테스트 커버리지
- 피처 추출기: 최소 90% 라인 커버리지
- 피드백 생성기: 최소 85% 라인 커버리지
- API 엔드포인트: 최소 80% 라인 커버리지

### 성능 기준
- 텍스트 기반 피처 추출: 2초 이내
- 오디오 기반 피처 추출: 10초 이내 (60초 오디오 기준)
- 전체 피드백 생성: 15초 이내

### 정확도 기준
- Blueprint 커버리지 매칭: F1 점수 0.8 이상
- Structure 컴포넌트 감지: F1 점수 0.75 이상
- 피처값 범위: ETS 기준 분포 내 (벤치마크 데이터 기준)

---

## Definition of Done

1. 모든 인수 조건(AC-001 ~ AC-031)이 통과한다
2. 단위 테스트 커버리지가 품질 게이트 기준을 충족한다
3. 통합 테스트가 성공적으로 완료된다
4. API 문서(OpenAPI)가 업데이트된다
5. 코드 리뷰가 완료되고 승인된다
6. 성능 테스트 결과가 기준을 충족한다

---

**작성자**: workflow-spec
**버전**: 1.0.0
**최종 수정일**: 2026-01-25
