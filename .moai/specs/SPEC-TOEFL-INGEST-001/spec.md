# SPEC-TOEFL-INGEST-001: TOEFL Speaking 데이터 수집 파이프라인

## TAG BLOCK

```
SPEC-ID: SPEC-TOEFL-INGEST-001
제목: TOEFL Speaking 데이터 수집 파이프라인
생성일: 2026-01-25
상태: draft
우선순위: High
담당: workflow-spec
의존성: SPEC-TOEFL-SCHEMA-001 (Set/Item/Stimulus/AnswerKey 모델)
```

---

## HISTORY

| 버전 | 날짜 | 작성자 | 변경 내용 |
|------|------|--------|-----------|
| 1.0.0 | 2026-01-25 | workflow-spec | 초기 SPEC 작성 |

---

## 개요

이 SPEC은 `external/` 폴더에 저장된 TOEFL Speaking 문제 데이터(JSON 형식)를 PostgreSQL 데이터베이스로 수집하는 파이프라인을 정의합니다.

### 핵심 가치

- **데이터 무결성**: Pydantic v2 기반 스키마 검증으로 잘못된 데이터 유입 방지
- **효율적 수집**: Bulk Insert 및 Upsert로 대량 데이터 빠른 처리
- **유연한 CLI**: 파일별 또는 전체 시딩, 검증 전용 모드, Dry-run 지원
- **트랜잭션 안정성**: 오류 발생 시 전체 롤백으로 데이터 일관성 보장

---

## Environment (환경)

### 입력 데이터 소스

| 파일명 | 설명 | 예상 레코드 수 |
|--------|------|----------------|
| `external/sets.json` | 문제 세트 목록 (테스트 세트 정보) | ~40개 |
| `external/items.json` | 개별 문항 정보 (Q1-Q6 문제) | ~240개 |
| `external/stimuli.json` | Reading/Listening 자극자료 | ~300개 |
| `external/answer_keys.json` | 모범답안 및 Blueprint | ~500개 |
| `external/independent_topics.json` | Independent Speaking 토픽 뱅크 | ~100개 |

### 기술 스택

| 구성 요소 | 버전 | 용도 |
|-----------|------|------|
| **Python** | 3.11+ | 런타임 환경 |
| **Pydantic** | v2.9+ | JSON 스키마 검증 |
| **SQLAlchemy** | 2.0+ | ORM 및 Bulk Insert |
| **ijson** | latest | 대용량 JSON 스트리밍 |
| **tqdm** | latest | 진행률 표시 |
| **Click** | latest | CLI 인터페이스 |

### 데이터베이스 대상 테이블

| 테이블명 | 소스 파일 | PK |
|----------|-----------|-----|
| `sets` | sets.json | set_id |
| `items` | items.json | item_id |
| `stimuli` | stimuli.json | stimulus_id |
| `answer_keys` | answer_keys.json | answer_id |
| `independent_topics` | independent_topics.json | topic_id |

---

## Assumptions (가정사항)

### 비즈니스 가정

1. **JSON 파일은 UTF-8 인코딩**으로 저장되어 있으며, 올바른 JSON 형식을 따른다고 가정합니다.
2. **set_id는 items 테이블의 FK로 참조**되며, 시딩 순서는 sets → items → stimuli → answer_keys 순서를 따른다고 가정합니다.
3. **데이터는 한 번 시딩된 후 주기적으로 업데이트**될 수 있으며, Upsert 지원이 필요하다고 가정합니다.

### 기술 가정

1. **PostgreSQL 데이터베이스가 이미 설정**되어 있고, 연결이 가능하다고 가정합니다.
2. **SPEC-TOEFL-SCHEMA-001에서 정의한 SQLAlchemy 모델**이 이미 구현되어 있다고 가정합니다.
3. **대용량 파일(10MB 이상)도 메모리 효율적으로 처리**해야 하므로 스트리밍 파서(ijson)가 필요하다고 가정합니다.

### 리스크 분석

| 가정사항 | 신뢰도 | 근거 | 틀렸을 경우 리스크 | 검증 방법 |
|---------|--------|------|-------------------|----------|
| JSON 형식 올바름 | High | 직접 생성된 파일 | 파싱 실패 | --validate-only 모드 사용 |
| FK 관계 존재 | Medium | 데이터 설계 문서 | FK 무결성 오류 | 시딩 전 FK 검증 |
| 모델 구현 완료 | Medium | SPEC-TOEFL-SCHEMA-001 | Import 오류 | 의존성 체크 |

---

## Requirements (요구사항)

### 1. Ubiquitous Requirements (시스템 전체 필수 요구사항)

#### REQ-ING-001: UTF-8 인코딩 처리
**시스템은 항상** 모든 JSON 파일을 UTF-8 인코딩으로 읽어야 **한다**.

**WHY**: 한글 및 특수 문자가 포함된 콘텐츠의 올바른 처리를 보장
**IMPACT**: 인코딩 오류 시 데이터 손상 또는 파싱 실패 발생

#### REQ-ING-002: 트랜잭션 기반 처리
**시스템은 항상** 각 파일 시딩을 단일 트랜잭션 내에서 수행하고, 오류 발생 시 전체 롤백**해야 한다**.

**WHY**: 부분적 데이터 삽입으로 인한 데이터 불일치 방지
**IMPACT**: 트랜잭션 없이는 실패 시 데이터베이스 정리 수동 필요

#### REQ-ING-003: 로깅 및 에러 리포트
**시스템은 항상** 시딩 과정의 진행 상태, 성공/실패 레코드 수, 오류 상세를 로그에 기록**해야 한다**.

**WHY**: 문제 발생 시 신속한 원인 파악 및 디버깅 지원
**IMPACT**: 로깅 없이는 시딩 실패 원인 추적 불가능

---

### 2. Event-Driven Requirements (이벤트 기반 요구사항)

#### REQ-ING-004: 단일 파일 시딩
**WHEN** 사용자가 `python -m src.cli.seed --file=external/sets.json` 명령을 실행하면,
**THEN** 시스템은 다음 작업을 순서대로 수행**해야 한다**:
1. 지정된 JSON 파일을 로드 및 파싱
2. Pydantic 모델로 스키마 검증
3. SQLAlchemy 모델로 변환
4. 데이터베이스에 Bulk Insert 수행
5. 성공/실패 결과를 콘솔에 출력

**WHY**: 개별 데이터 소스의 선택적 시딩 지원
**IMPACT**: 파일 단위 업데이트 불가 시 전체 재시딩 필요

#### REQ-ING-005: 전체 시딩
**WHEN** 사용자가 `python -m src.cli.seed --all` 명령을 실행하면,
**THEN** 시스템은 다음 순서로 모든 데이터 소스를 시딩**해야 한다**:
1. `sets.json` → sets 테이블
2. `items.json` → items 테이블 (FK: set_id)
3. `stimuli.json` → stimuli 테이블 (FK: item_id)
4. `answer_keys.json` → answer_keys 테이블 (FK: item_id)
5. `independent_topics.json` → independent_topics 테이블

**WHY**: FK 의존성을 고려한 올바른 시딩 순서 보장
**IMPACT**: 순서 오류 시 FK 무결성 위반 발생

#### REQ-ING-006: 검증 전용 모드
**WHEN** 사용자가 `python -m src.cli.seed --validate-only` 명령을 실행하면,
**THEN** 시스템은 다음 작업만 수행**해야 한다**:
1. 모든 JSON 파일 로드 및 파싱
2. Pydantic 모델로 스키마 검증
3. 검증 결과(성공/실패, 오류 상세) 출력
4. **데이터베이스에 쓰기 작업을 수행하지 않음**

**WHY**: 실제 시딩 전 데이터 무결성 사전 검증 지원
**IMPACT**: 검증 모드 없이는 실제 시딩 후에야 오류 발견

#### REQ-ING-007: Dry-run 모드
**WHEN** 사용자가 `python -m src.cli.seed --dry-run` 명령을 실행하면,
**THEN** 시스템은 다음 작업을 수행**해야 한다**:
1. 모든 JSON 파일 로드 및 파싱
2. Pydantic 모델로 스키마 검증
3. SQLAlchemy 모델로 변환
4. 변환된 데이터의 요약 정보 출력 (레코드 수, 필드 샘플)
5. **데이터베이스에 쓰기 작업을 수행하지 않음**

**WHY**: 변환 로직 검증 및 예상 결과 미리보기 지원
**IMPACT**: Dry-run 없이는 변환 오류를 실제 시딩 시에만 발견

#### REQ-ING-008: Upsert 지원
**WHEN** 사용자가 `python -m src.cli.seed --file=external/items.json --upsert` 명령을 실행하면,
**THEN** 시스템은 다음 로직으로 데이터를 처리**해야 한다**:
1. 각 레코드의 PK(예: item_id)로 기존 레코드 존재 여부 확인
2. 존재하는 레코드: UPDATE 수행
3. 존재하지 않는 레코드: INSERT 수행
4. INSERT/UPDATE 각 건수를 별도 보고

**WHY**: 기존 데이터 보존하면서 변경사항만 업데이트 지원
**IMPACT**: Upsert 없이는 전체 삭제 후 재삽입 필요

---

### 3. State-Driven Requirements (상태 기반 요구사항)

#### REQ-ING-009: 대용량 파일 스트리밍
**IF** 처리할 JSON 파일이 5MB 이상**이면**,
**THEN** 시스템은 ijson 라이브러리를 사용하여 스트리밍 방식으로 파싱**해야 한다**.

**WHY**: 메모리 효율적인 대용량 파일 처리 지원
**IMPACT**: 스트리밍 없이는 대용량 파일 처리 시 메모리 부족 발생 가능

#### REQ-ING-010: FK 참조 무결성
**IF** items 테이블 시딩 시 set_id가 sets 테이블에 존재하지 않으면**,
**THEN** 시스템은 해당 레코드를 건너뛰고 오류 로그에 기록**해야 한다**.

**WHY**: FK 무결성 위반으로 인한 전체 시딩 실패 방지
**IMPACT**: FK 검증 없이는 데이터베이스 오류로 전체 롤백 발생

#### REQ-ING-011: 배치 크기 조절
**IF** 시스템 메모리가 제한적이거나 레코드 수가 1000개 이상**이면**,
**THEN** 시스템은 batch_size(기본값 100)로 나누어 Bulk Insert를 수행**해야 한다**.

**WHY**: 메모리 사용량 조절 및 트랜잭션 안정성 확보
**IMPACT**: 배치 처리 없이는 대량 Insert 시 타임아웃 또는 메모리 오류

---

### 4. Unwanted Requirements (금지 요구사항)

#### REQ-ING-012: 부분 커밋 금지
**시스템은** 시딩 중 오류 발생 시 이미 삽입된 레코드를 커밋**하지 않아야 한다**.
전체 트랜잭션 롤백을 수행**해야 한다**.

**WHY**: 부분 데이터로 인한 불일치 상태 방지
**IMPACT**: 부분 커밋 시 데이터 정리에 수동 개입 필요

#### REQ-ING-013: 중복 PK 무시 금지
**시스템은** 중복된 PK 레코드를 무시하고 진행**하지 않아야 한다**.
--upsert 옵션 없이 중복 발생 시 오류로 처리**해야 한다**.

**WHY**: 의도하지 않은 데이터 유실 방지
**IMPACT**: 무시 시 기존 데이터와의 불일치 발생 가능

#### REQ-ING-014: 하드코딩된 경로 금지
**시스템은** 파일 경로를 코드에 하드코딩**하지 않아야 한다**.
CLI 인자 또는 환경변수로 설정 가능**해야 한다**.

**WHY**: 유연한 배포 환경 지원 및 테스트 용이성
**IMPACT**: 하드코딩 시 환경별 코드 수정 필요

---

### 5. Optional Requirements (선택 요구사항)

#### REQ-ING-015: 진행률 표시
**가능하면**, 시딩 진행 중 tqdm을 사용하여 진행률 바를 표시**할 수 있다**.

**WHY**: 대량 데이터 시딩 시 사용자 피드백 제공
**IMPACT**: 미지원 시에도 로그를 통해 진행 상태 확인 가능

#### REQ-ING-016: 병렬 처리
**가능하면**, 독립적인 테이블 시딩을 병렬로 처리하여 속도를 개선**할 수 있다**.

**WHY**: 시딩 시간 단축
**IMPACT**: 미지원 시에도 순차 처리로 정상 작동

---

## Specifications (세부 명세)

### JSON 스키마 정의 (Pydantic v2)

#### SetSchema
```python
class SetSchema(BaseModel):
    set_id: str
    title: str
    source: str
    version: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
```

#### ItemSchema
```python
class ItemSchema(BaseModel):
    item_id: str
    set_id: str  # FK to sets
    task_no: int
    task_type: Literal["independent", "integrated_read_listen", "integrated_listen_only"]
    prompt: str
    prep_seconds: int
    response_seconds: int
    language: str = "en"
    tags: list[str] = []
    difficulty: str | None = None
    scoring_focus: str | None = None

    model_config = ConfigDict(from_attributes=True)
```

#### StimulusSchema
```python
class StimulusSchema(BaseModel):
    stimulus_id: str
    item_id: str  # FK to items
    kind: Literal["reading", "direction", "listening"]
    title: str
    content_text: str | None = None
    asset_url: str | None = None
    duration_seconds: float | None = None
    order: int
    notes_allowed: bool = True

    model_config = ConfigDict(from_attributes=True)
```

#### AnswerKeySchema
```python
class AnswerKeySchema(BaseModel):
    answer_id: str
    item_id: str  # FK to items
    type: Literal["sample_response", "transcript", "blueprint"]
    level: Literal["basic", "advanced", "ultimate"] | None = None
    content: str
    source: str

    model_config = ConfigDict(from_attributes=True)
```

#### IndependentTopicSchema
```python
class IndependentTopicSchema(BaseModel):
    topic_id: str
    number: int
    prompt: str
    source: str

    model_config = ConfigDict(from_attributes=True)
```

### CLI 인터페이스 설계

```bash
# 사용법
python -m src.cli.seed [OPTIONS]

# 옵션
--file PATH           단일 파일 시딩 (예: external/sets.json)
--all                 모든 파일 순차 시딩
--validate-only       스키마 검증만 수행 (DB 쓰기 없음)
--dry-run             변환까지만 수행 (DB 쓰기 없음)
--upsert              기존 레코드 업데이트 허용
--batch-size INT      배치 크기 (기본값: 100)
--verbose             상세 로그 출력
--help                도움말 표시
```

### 에러 코드 정의

| 코드 | 설명 | 복구 방법 |
|------|------|----------|
| E001 | 파일 미존재 | 파일 경로 확인 |
| E002 | JSON 파싱 실패 | JSON 형식 검토 |
| E003 | 스키마 검증 실패 | 오류 상세 확인 후 데이터 수정 |
| E004 | FK 무결성 위반 | 참조 테이블 먼저 시딩 |
| E005 | 중복 PK | --upsert 옵션 사용 또는 데이터 확인 |
| E006 | DB 연결 실패 | 데이터베이스 연결 설정 확인 |

### 처리 성능 목표

| 지표 | 목표 값 |
|------|--------|
| 파싱 속도 | 1000 레코드/초 이상 |
| Insert 속도 | 500 레코드/초 이상 (Bulk) |
| 메모리 사용량 | 512MB 이하 (대용량 파일 포함) |
| 전체 시딩 시간 | 1분 이내 (예상 1200 레코드) |

---

## Traceability (추적성)

- **관련 SPEC**: SPEC-TOEFL-SCHEMA-001 (모델 정의 의존)
- **관련 SPEC**: SPEC-TOEFL-001 (전체 시스템 컨텍스트)
- **Epic**: TOEFL Speaking 데이터 관리
- **Labels**: `backend`, `data-pipeline`, `cli`, `database`

---

## 참고 문서

- **Pydantic v2 Documentation**: https://docs.pydantic.dev/latest/
- **SQLAlchemy 2.0 ORM**: https://docs.sqlalchemy.org/en/20/orm/
- **ijson Documentation**: https://github.com/ICRAR/ijson
- **Click CLI Framework**: https://click.palletsprojects.com/

---

**작성자**: workflow-spec
**검토자**: 수연
**버전**: 1.0.0
**최종 수정일**: 2026-01-25
