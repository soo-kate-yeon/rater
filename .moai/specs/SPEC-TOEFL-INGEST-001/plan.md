# SPEC-TOEFL-INGEST-001 구현 계획

## TAG BLOCK

```
SPEC-ID: SPEC-TOEFL-INGEST-001
제목: TOEFL Speaking 데이터 수집 파이프라인 구현 계획
생성일: 2026-01-25
상태: draft
우선순위: High
```

---

## HISTORY

| 버전 | 날짜 | 작성자 | 변경 내용 |
|------|------|--------|-----------|
| 1.0.0 | 2026-01-25 | workflow-spec | 초기 구현 계획 작성 |

---

## 구현 우선순위 및 마일스톤

### Primary Goal (1순위 핵심 기능)

**목표**: JSON 파일을 파싱하고 데이터베이스에 시딩하는 기본 파이프라인 완성

#### Milestone 1.1: Pydantic 스키마 정의
- **완료 조건**: 5개 소스 파일에 대응하는 Pydantic 모델 생성 및 단위 테스트 통과
- **작업 내용**:
  - `src/schemas/ingest/` 디렉토리 생성
  - `SetSchema`, `ItemSchema`, `StimulusSchema`, `AnswerKeySchema`, `IndependentTopicSchema` 정의
  - 각 스키마에 대한 검증 테스트 작성
  - Optional 필드 및 기본값 설정

#### Milestone 1.2: JSON 파서 구현
- **완료 조건**: 5개 JSON 파일을 로드하고 Pydantic 모델로 변환 성공
- **작업 내용**:
  - `src/services/ingest/parser.py` 구현
  - `load_json_file(path: str)` 함수 구현
  - `parse_to_schema(data: list[dict], schema_class: type[BaseModel])` 함수 구현
  - UTF-8 인코딩 강제 및 예외 처리
  - 파싱 결과 로깅

#### Milestone 1.3: SQLAlchemy 모델 매핑
- **완료 조건**: Pydantic 스키마에서 SQLAlchemy 모델로 변환 성공
- **작업 내용**:
  - `src/services/ingest/mapper.py` 구현
  - `schema_to_model(schema: BaseModel, model_class: type[Base])` 함수 구현
  - FK 관계 설정 (set_id → Item, item_id → Stimulus/AnswerKey)
  - 중첩 JSON 필드(tags) 처리

#### Milestone 1.4: Bulk Insert 구현
- **완료 조건**: 100개 이상 레코드를 batch_size=100으로 성공적으로 삽입
- **작업 내용**:
  - `src/services/ingest/seeder.py` 구현
  - `bulk_insert(session: AsyncSession, models: list[Base], batch_size: int = 100)` 함수 구현
  - 트랜잭션 관리 (commit/rollback)
  - 진행률 로깅

#### Milestone 1.5: CLI 기본 명령 구현
- **완료 조건**: `python -m src.cli.seed --file=external/sets.json` 명령 정상 작동
- **작업 내용**:
  - `src/cli/seed.py` 구현 (Click 프레임워크 사용)
  - `--file` 옵션 구현
  - `--all` 옵션 구현 (의존성 순서 고려)
  - 기본 에러 핸들링 및 출력

---

### Secondary Goal (2순위 확장 기능)

**목표**: 고급 기능 추가 및 사용자 경험 개선

#### Milestone 2.1: Upsert 지원
- **완료 조건**: `--upsert` 옵션으로 기존 레코드 업데이트 성공
- **작업 내용**:
  - PostgreSQL `ON CONFLICT` 구문 활용
  - `upsert_batch(session, models, pk_field)` 함수 구현
  - INSERT/UPDATE 건수 별도 카운팅

#### Milestone 2.2: 검증 및 Dry-run 모드
- **완료 조건**: `--validate-only` 및 `--dry-run` 옵션 정상 작동
- **작업 내용**:
  - 스키마 검증 전용 로직 분리
  - 검증 결과 리포트 포맷팅
  - Dry-run 시 변환 결과 미리보기 출력

#### Milestone 2.3: 대용량 파일 스트리밍
- **완료 조건**: 10MB 이상 JSON 파일을 512MB 미만 메모리로 처리
- **작업 내용**:
  - ijson 라이브러리 통합
  - `stream_json_file(path: str)` 제너레이터 구현
  - 파일 크기 감지 및 자동 모드 전환

#### Milestone 2.4: 진행률 표시
- **완료 조건**: tqdm을 사용한 진행률 바 표시
- **작업 내용**:
  - tqdm 통합 (`--verbose` 옵션과 연동)
  - 파일별/레코드별 진행률 표시
  - 예상 완료 시간(ETA) 표시

---

### Final Goal (3순위 최적화 및 안정성)

**목표**: 프로덕션 수준의 안정성 및 테스트 커버리지

#### Milestone 3.1: 에러 처리 강화
- **완료 조건**: 모든 에러 코드(E001-E006)에 대한 핸들링 및 친화적 메시지 출력
- **작업 내용**:
  - 커스텀 예외 클래스 정의 (`IngestError`, `ValidationError`, `FKViolationError`)
  - 에러 코드별 복구 가이드 메시지
  - 상세 에러 로그 (파일명, 라인 번호, 필드명)

#### Milestone 3.2: 테스트 작성
- **완료 조건**: 테스트 커버리지 85% 이상
- **작업 내용**:
  - 스키마 검증 단위 테스트
  - 파서 단위 테스트 (정상/오류 케이스)
  - Bulk Insert 통합 테스트
  - CLI 엔드투엔드 테스트
  - Mock 데이터 fixtures 생성

#### Milestone 3.3: 문서화
- **완료 조건**: CLI 사용법 및 에러 해결 가이드 문서 작성
- **작업 내용**:
  - CLI `--help` 메시지 상세화
  - README에 시딩 가이드 추가
  - 에러 코드 레퍼런스 문서

---

## 기술 스택 명세

### 핵심 라이브러리

| 라이브러리 | 버전 | 용도 |
|-----------|------|------|
| **pydantic** | ^2.9.0 | JSON 스키마 검증 |
| **sqlalchemy** | ^2.0.0 | ORM 및 Bulk Insert |
| **asyncpg** | ^0.29.0 | PostgreSQL 비동기 드라이버 |
| **click** | ^8.1.0 | CLI 프레임워크 |
| **ijson** | ^3.2.0 | JSON 스트리밍 파서 |
| **tqdm** | ^4.66.0 | 진행률 표시 |
| **structlog** | ^24.1.0 | 구조화된 로깅 |

### 의존성 설치

```bash
# pyproject.toml에 추가
poetry add click ijson tqdm structlog

# 또는 uv 사용
uv add click ijson tqdm structlog
```

---

## 아키텍처 설계

### 디렉토리 구조

```
src/
├── cli/
│   └── seed.py              # CLI 진입점
├── schemas/
│   └── ingest/
│       ├── __init__.py
│       ├── set.py           # SetSchema
│       ├── item.py          # ItemSchema
│       ├── stimulus.py      # StimulusSchema
│       ├── answer_key.py    # AnswerKeySchema
│       └── topic.py         # IndependentTopicSchema
├── services/
│   └── ingest/
│       ├── __init__.py
│       ├── parser.py        # JSON 파서
│       ├── mapper.py        # 스키마 → 모델 변환
│       ├── seeder.py        # Bulk Insert/Upsert
│       └── validator.py     # 스키마 검증
└── models/
    └── content/             # SPEC-TOEFL-SCHEMA-001 참조
        ├── set.py
        ├── item.py
        ├── stimulus.py
        ├── answer_key.py
        └── independent_topic.py
```

### 데이터 흐름

```
[external/*.json]
       |
       v
[parser.py: load_json_file()]
       |
       v
[validator.py: validate_schema()]
       |
       v
[Pydantic Models]
       |
       v
[mapper.py: schema_to_model()]
       |
       v
[SQLAlchemy Models]
       |
       v
[seeder.py: bulk_insert() / upsert_batch()]
       |
       v
[PostgreSQL Tables]
```

### 시딩 순서 의존성

```
1. sets.json        → sets 테이블 (독립)
2. items.json       → items 테이블 (FK: set_id)
3. stimuli.json     → stimuli 테이블 (FK: item_id)
4. answer_keys.json → answer_keys 테이블 (FK: item_id)
5. independent_topics.json → independent_topics 테이블 (독립)

의존성 그래프:
sets ──┬─→ items ──┬─→ stimuli
       │           └─→ answer_keys
       │
independent_topics (독립)
```

---

## 리스크 분석 및 대응 전략

### 리스크 1: FK 무결성 오류
- **확률**: Medium
- **영향도**: High (시딩 실패)
- **대응**:
  - 시딩 전 참조 테이블 존재 여부 검증
  - FK 오류 레코드 건너뛰기 + 경고 로그
  - 의존성 순서 엄격 적용

### 리스크 2: 대용량 파일 메모리 초과
- **확률**: Low (현재 데이터 규모 작음)
- **영향도**: Medium (OOM 오류)
- **대응**:
  - 파일 크기 감지 후 자동 스트리밍 모드 전환
  - batch_size 조절 옵션 제공

### 리스크 3: 스키마 변경에 따른 호환성 문제
- **확률**: Medium
- **영향도**: High (파싱 실패)
- **대응**:
  - Pydantic `extra="ignore"` 설정으로 추가 필드 무시
  - 스키마 버전 관리 고려

### 리스크 4: 중복 데이터 처리
- **확률**: High (반복 시딩 시)
- **영향도**: Medium (데이터 불일치)
- **대응**:
  - `--upsert` 옵션 기본 제공
  - 중복 PK 발생 시 명확한 오류 메시지

---

## 성공 지표 (KPI)

### 기능 지표
- **스키마 검증 정확도**: 100% (유효 데이터 통과, 무효 데이터 거부)
- **시딩 성공률**: 99% 이상 (네트워크/DB 오류 제외)
- **Upsert 정확도**: 100% (INSERT/UPDATE 정확 분류)

### 성능 지표
- **파싱 속도**: 1000 레코드/초 이상
- **Insert 속도**: 500 레코드/초 이상
- **전체 시딩 시간**: 1분 이내 (예상 1200 레코드)
- **메모리 사용량**: 512MB 이하

### 품질 지표
- **테스트 커버리지**: 85% 이상
- **린터 경고**: 0건 (Ruff)
- **타입 체크**: 통과 (Pyright/mypy)

---

## 다음 단계

1. **SPEC-TOEFL-INGEST-001 승인 대기**: 수연님의 검토 및 피드백
2. **SPEC-TOEFL-SCHEMA-001 구현 확인**: Set/Item/Stimulus/AnswerKey 모델 존재 여부
3. **Milestone 1.1 시작**: Pydantic 스키마 정의
4. **단위 테스트 환경 구성**: pytest fixtures 준비

---

**작성자**: workflow-spec
**검토자**: 수연
**버전**: 1.0.0
**최종 수정일**: 2026-01-25
