# SPEC-TOEFL-INGEST-001 수락 기준 (Acceptance Criteria)

## TAG BLOCK

```
SPEC-ID: SPEC-TOEFL-INGEST-001
제목: TOEFL Speaking 데이터 수집 파이프라인 수락 기준
생성일: 2026-01-25
상태: draft
우선순위: High
```

---

## HISTORY

| 버전 | 날짜 | 작성자 | 변경 내용 |
|------|------|--------|-----------|
| 1.0.0 | 2026-01-25 | workflow-spec | 초기 수락 기준 작성 |

---

## 수락 기준 개요

이 문서는 SPEC-TOEFL-INGEST-001의 각 기능이 완료되었다고 간주되기 위한 구체적인 검증 기준을 정의합니다. 모든 시나리오는 Given-When-Then 형식으로 작성되며, 자동화된 테스트 또는 수동 테스트를 통해 검증됩니다.

---

## 테스트 시나리오 (Given-When-Then Format)

### 시나리오 1: JSON 파싱 및 스키마 검증

#### AC-ING-001: 유효한 sets.json 파싱 성공
**Given**: `external/sets.json` 파일이 올바른 JSON 형식으로 존재하는 상태
**When**: 파서가 파일을 로드하고 SetSchema로 검증을 시도한다
**Then**:
  - 모든 레코드가 성공적으로 파싱된다
  - 각 레코드가 SetSchema 인스턴스로 변환된다
  - 필수 필드(set_id, title, source, version, created_at, updated_at)가 모두 존재한다

**검증 방법**:
```python
# pytest 테스트 예시
def test_parse_sets_json():
    data = load_json_file("external/sets.json")
    schemas = [SetSchema.model_validate(item) for item in data]
    assert len(schemas) > 0
    assert all(s.set_id is not None for s in schemas)
    assert all(s.title is not None for s in schemas)
```

---

#### AC-ING-002: 유효한 items.json 파싱 성공
**Given**: `external/items.json` 파일이 존재하는 상태
**When**: 파서가 파일을 로드하고 ItemSchema로 검증을 시도한다
**Then**:
  - 모든 레코드가 성공적으로 파싱된다
  - task_type 필드가 허용된 값 중 하나이다 ("independent", "integrated_read_listen", "integrated_listen_only")
  - set_id 필드가 존재한다

**검증 방법**:
```python
def test_parse_items_json():
    data = load_json_file("external/items.json")
    schemas = [ItemSchema.model_validate(item) for item in data]
    assert len(schemas) > 0
    valid_types = {"independent", "integrated_read_listen", "integrated_listen_only"}
    assert all(s.task_type in valid_types for s in schemas)
    assert all(s.set_id is not None for s in schemas)
```

---

#### AC-ING-003: 유효한 stimuli.json 파싱 성공
**Given**: `external/stimuli.json` 파일이 존재하는 상태
**When**: 파서가 파일을 로드하고 StimulusSchema로 검증을 시도한다
**Then**:
  - 모든 레코드가 성공적으로 파싱된다
  - kind 필드가 허용된 값 중 하나이다 ("reading", "direction", "listening")
  - item_id FK 참조가 존재한다

**검증 방법**:
```python
def test_parse_stimuli_json():
    data = load_json_file("external/stimuli.json")
    schemas = [StimulusSchema.model_validate(item) for item in data]
    assert len(schemas) > 0
    valid_kinds = {"reading", "direction", "listening"}
    assert all(s.kind in valid_kinds for s in schemas)
```

---

#### AC-ING-004: 유효한 answer_keys.json 파싱 성공
**Given**: `external/answer_keys.json` 파일이 존재하는 상태
**When**: 파서가 파일을 로드하고 AnswerKeySchema로 검증을 시도한다
**Then**:
  - 모든 레코드가 성공적으로 파싱된다
  - type 필드가 허용된 값 중 하나이다 ("sample_response", "transcript", "blueprint")
  - level 필드가 null이거나 허용된 값 중 하나이다

**검증 방법**:
```python
def test_parse_answer_keys_json():
    data = load_json_file("external/answer_keys.json")
    schemas = [AnswerKeySchema.model_validate(item) for item in data]
    assert len(schemas) > 0
    valid_types = {"sample_response", "transcript", "blueprint"}
    valid_levels = {"basic", "advanced", "ultimate", None}
    assert all(s.type in valid_types for s in schemas)
    assert all(s.level in valid_levels for s in schemas)
```

---

#### AC-ING-005: 유효한 independent_topics.json 파싱 성공
**Given**: `external/independent_topics.json` 파일이 존재하는 상태
**When**: 파서가 파일을 로드하고 IndependentTopicSchema로 검증을 시도한다
**Then**:
  - 모든 레코드가 성공적으로 파싱된다
  - topic_id, number, prompt 필드가 모두 존재한다

**검증 방법**:
```python
def test_parse_independent_topics_json():
    data = load_json_file("external/independent_topics.json")
    schemas = [IndependentTopicSchema.model_validate(item) for item in data]
    assert len(schemas) > 0
    assert all(s.topic_id is not None for s in schemas)
    assert all(s.number > 0 for s in schemas)
```

---

#### AC-ING-006: 잘못된 JSON 형식 처리
**Given**: 손상된 JSON 파일이 존재하는 상태 (예: 닫히지 않은 괄호)
**When**: 파서가 파일을 로드하려고 시도한다
**Then**:
  - JSONDecodeError 예외가 발생한다
  - 에러 코드 E002가 로그에 기록된다
  - 친화적인 에러 메시지가 출력된다

**검증 방법**:
```python
def test_parse_invalid_json():
    with pytest.raises(IngestError) as exc_info:
        load_json_file("tests/fixtures/invalid.json")
    assert exc_info.value.code == "E002"
    assert "JSON 파싱 실패" in str(exc_info.value)
```

---

#### AC-ING-007: 스키마 검증 실패 처리
**Given**: 필수 필드가 누락된 레코드가 포함된 JSON 파일
**When**: 파서가 스키마 검증을 시도한다
**Then**:
  - ValidationError 예외가 발생한다
  - 에러 코드 E003이 로그에 기록된다
  - 누락된 필드명과 레코드 인덱스가 에러 메시지에 포함된다

**검증 방법**:
```python
def test_schema_validation_failure():
    invalid_data = [{"set_id": "TEST_01"}]  # title 누락
    with pytest.raises(ValidationError) as exc_info:
        SetSchema.model_validate(invalid_data[0])
    assert "title" in str(exc_info.value)
```

---

### 시나리오 2: 단일 파일 시딩

#### AC-ING-008: 단일 파일 시딩 성공
**Given**: 데이터베이스가 비어있고 `external/sets.json`에 10개 레코드가 있는 상태
**When**: `python -m src.cli.seed --file=external/sets.json` 명령을 실행한다
**Then**:
  - sets 테이블에 10개 레코드가 삽입된다
  - 콘솔에 "10개 레코드 시딩 완료" 메시지가 출력된다
  - 에러 없이 프로세스가 종료된다 (exit code 0)

**검증 방법**:
```python
async def test_seed_single_file_success(db_session):
    result = subprocess.run(
        ["python", "-m", "src.cli.seed", "--file=external/sets.json"],
        capture_output=True, text=True
    )
    assert result.returncode == 0
    assert "시딩 완료" in result.stdout

    count = await db_session.scalar(select(func.count(Set.set_id)))
    assert count == 10
```

---

#### AC-ING-009: 존재하지 않는 파일 처리
**Given**: `external/nonexistent.json` 파일이 존재하지 않는 상태
**When**: `python -m src.cli.seed --file=external/nonexistent.json` 명령을 실행한다
**Then**:
  - 에러 코드 E001이 출력된다
  - "파일을 찾을 수 없습니다" 메시지가 출력된다
  - exit code 1로 종료된다

**검증 방법**:
```python
def test_seed_nonexistent_file():
    result = subprocess.run(
        ["python", "-m", "src.cli.seed", "--file=external/nonexistent.json"],
        capture_output=True, text=True
    )
    assert result.returncode == 1
    assert "E001" in result.stderr or "파일을 찾을 수 없습니다" in result.stderr
```

---

### 시나리오 3: 전체 시딩

#### AC-ING-010: 전체 시딩 성공 (올바른 순서)
**Given**: 데이터베이스가 비어있고 모든 external/*.json 파일이 존재하는 상태
**When**: `python -m src.cli.seed --all` 명령을 실행한다
**Then**:
  - 다음 순서로 테이블에 데이터가 삽입된다:
    1. sets (먼저)
    2. items (set_id FK 참조)
    3. stimuli (item_id FK 참조)
    4. answer_keys (item_id FK 참조)
    5. independent_topics (독립)
  - FK 무결성 오류가 발생하지 않는다
  - 모든 테이블에 예상 레코드 수가 삽입된다

**검증 방법**:
```python
async def test_seed_all_success(db_session):
    result = subprocess.run(
        ["python", "-m", "src.cli.seed", "--all"],
        capture_output=True, text=True
    )
    assert result.returncode == 0

    # 각 테이블 레코드 수 확인
    sets_count = await db_session.scalar(select(func.count(Set.set_id)))
    items_count = await db_session.scalar(select(func.count(Item.item_id)))
    stimuli_count = await db_session.scalar(select(func.count(Stimulus.stimulus_id)))

    assert sets_count > 0
    assert items_count > 0
    assert stimuli_count > 0
```

---

#### AC-ING-011: 전체 시딩 중 오류 발생 시 롤백
**Given**: items.json에 존재하지 않는 set_id를 참조하는 레코드가 있는 상태
**When**: `python -m src.cli.seed --all` 명령을 실행한다
**Then**:
  - FK 무결성 오류가 감지된다
  - 전체 트랜잭션이 롤백된다
  - 에러 코드 E004가 출력된다
  - 어떤 테이블에도 부분 데이터가 남지 않는다

**검증 방법**:
```python
async def test_seed_all_rollback_on_error(db_session, corrupted_items_json):
    result = subprocess.run(
        ["python", "-m", "src.cli.seed", "--all"],
        capture_output=True, text=True
    )
    assert result.returncode != 0
    assert "E004" in result.stderr or "FK 무결성" in result.stderr

    # 롤백 확인
    sets_count = await db_session.scalar(select(func.count(Set.set_id)))
    assert sets_count == 0  # 롤백되어 비어있어야 함
```

---

### 시나리오 4: 검증 모드

#### AC-ING-012: 검증 전용 모드 성공
**Given**: 모든 external/*.json 파일이 유효한 상태
**When**: `python -m src.cli.seed --validate-only` 명령을 실행한다
**Then**:
  - 모든 파일에 대해 "검증 성공" 메시지가 출력된다
  - 데이터베이스에 아무런 변경이 발생하지 않는다
  - exit code 0으로 종료된다

**검증 방법**:
```python
async def test_validate_only_mode(db_session):
    # 초기 상태 저장
    initial_count = await db_session.scalar(select(func.count(Set.set_id)))

    result = subprocess.run(
        ["python", "-m", "src.cli.seed", "--validate-only"],
        capture_output=True, text=True
    )
    assert result.returncode == 0
    assert "검증 성공" in result.stdout

    # DB 변경 없음 확인
    final_count = await db_session.scalar(select(func.count(Set.set_id)))
    assert initial_count == final_count
```

---

#### AC-ING-013: 검증 모드에서 오류 감지
**Given**: items.json에 잘못된 task_type 값이 있는 상태
**When**: `python -m src.cli.seed --validate-only` 명령을 실행한다
**Then**:
  - 스키마 검증 오류가 출력된다
  - 오류가 발생한 파일명과 필드명이 표시된다
  - exit code 1로 종료된다
  - 데이터베이스에 변경 없음

**검증 방법**:
```python
def test_validate_only_with_errors(corrupted_items_json):
    result = subprocess.run(
        ["python", "-m", "src.cli.seed", "--validate-only"],
        capture_output=True, text=True
    )
    assert result.returncode == 1
    assert "items.json" in result.stderr
    assert "task_type" in result.stderr
```

---

### 시나리오 5: Dry-run 모드

#### AC-ING-014: Dry-run 모드 성공
**Given**: 모든 external/*.json 파일이 유효한 상태
**When**: `python -m src.cli.seed --dry-run` 명령을 실행한다
**Then**:
  - 각 파일의 예상 레코드 수가 출력된다
  - 샘플 레코드(첫 2개)가 표시된다
  - 데이터베이스에 아무런 변경이 발생하지 않는다
  - exit code 0으로 종료된다

**검증 방법**:
```python
async def test_dry_run_mode(db_session):
    result = subprocess.run(
        ["python", "-m", "src.cli.seed", "--dry-run"],
        capture_output=True, text=True
    )
    assert result.returncode == 0
    assert "예상 레코드 수" in result.stdout

    # DB 변경 없음 확인
    count = await db_session.scalar(select(func.count(Set.set_id)))
    assert count == 0
```

---

### 시나리오 6: Upsert 기능

#### AC-ING-015: Upsert - 새 레코드 INSERT
**Given**: sets 테이블이 비어있는 상태
**When**: `python -m src.cli.seed --file=external/sets.json --upsert` 명령을 실행한다
**Then**:
  - 모든 레코드가 INSERT 된다
  - "INSERT: 10건, UPDATE: 0건" 형태로 결과가 출력된다

**검증 방법**:
```python
async def test_upsert_insert_new(db_session):
    result = subprocess.run(
        ["python", "-m", "src.cli.seed", "--file=external/sets.json", "--upsert"],
        capture_output=True, text=True
    )
    assert result.returncode == 0
    assert "INSERT:" in result.stdout
    assert "UPDATE: 0" in result.stdout
```

---

#### AC-ING-016: Upsert - 기존 레코드 UPDATE
**Given**: sets 테이블에 이미 동일한 set_id를 가진 레코드가 존재하는 상태
**When**: `python -m src.cli.seed --file=external/sets.json --upsert` 명령을 실행한다
**Then**:
  - 기존 레코드가 UPDATE 된다
  - 새 레코드는 INSERT 된다
  - "INSERT: 2건, UPDATE: 8건" 형태로 결과가 출력된다

**검증 방법**:
```python
async def test_upsert_update_existing(db_session, existing_sets):
    result = subprocess.run(
        ["python", "-m", "src.cli.seed", "--file=external/sets.json", "--upsert"],
        capture_output=True, text=True
    )
    assert result.returncode == 0
    assert "UPDATE:" in result.stdout
```

---

#### AC-ING-017: Upsert 없이 중복 PK 오류
**Given**: sets 테이블에 이미 동일한 set_id를 가진 레코드가 존재하는 상태
**When**: `python -m src.cli.seed --file=external/sets.json` 명령을 실행한다 (--upsert 없음)
**Then**:
  - 중복 PK 오류가 발생한다
  - 에러 코드 E005가 출력된다
  - 트랜잭션이 롤백된다

**검증 방법**:
```python
async def test_duplicate_pk_without_upsert(db_session, existing_sets):
    result = subprocess.run(
        ["python", "-m", "src.cli.seed", "--file=external/sets.json"],
        capture_output=True, text=True
    )
    assert result.returncode != 0
    assert "E005" in result.stderr or "중복" in result.stderr
```

---

### 시나리오 7: 배치 처리

#### AC-ING-018: 배치 크기 조절
**Given**: items.json에 200개 레코드가 있는 상태
**When**: `python -m src.cli.seed --file=external/items.json --batch-size=50` 명령을 실행한다
**Then**:
  - 50개씩 4번의 배치로 처리된다
  - 각 배치마다 진행 로그가 출력된다
  - 총 200개 레코드가 성공적으로 삽입된다

**검증 방법**:
```python
async def test_batch_size_option(db_session):
    result = subprocess.run(
        ["python", "-m", "src.cli.seed", "--file=external/items.json",
         "--batch-size=50", "--verbose"],
        capture_output=True, text=True
    )
    assert result.returncode == 0
    assert result.stdout.count("배치") >= 4  # 최소 4번 배치 로그
```

---

### 시나리오 8: 진행률 표시

#### AC-ING-019: 진행률 바 표시
**Given**: 대량의 레코드가 포함된 JSON 파일
**When**: `python -m src.cli.seed --all --verbose` 명령을 실행한다
**Then**:
  - tqdm 진행률 바가 표시된다
  - 예상 완료 시간(ETA)이 표시된다
  - 처리 속도(records/sec)가 표시된다

**검증 방법**: 수동 테스트
- [ ] 진행률 바가 터미널에 표시되는지 확인
- [ ] 진행률이 0%에서 100%까지 증가하는지 확인
- [ ] 완료 시 최종 통계가 출력되는지 확인

---

## Quality Gate (품질 게이트)

### 코드 품질
- [ ] **테스트 커버리지 >= 85%** (pytest-cov)
- [ ] **Ruff 린터 경고 0건**
- [ ] **Pyright 타입 체크 통과**
- [ ] **모든 함수에 docstring 존재**

### 성능 기준
- [ ] **파싱 속도**: 1000 레코드/초 이상
- [ ] **Insert 속도**: 500 레코드/초 이상
- [ ] **전체 시딩 시간**: 1분 이내 (약 1200 레코드)
- [ ] **메모리 사용량**: 512MB 이하

### 기능 완성도
- [ ] **모든 AC 시나리오 통과** (AC-ING-001 ~ AC-ING-019)
- [ ] **5개 JSON 소스 파일 지원**
- [ ] **CLI 옵션 모두 동작** (--file, --all, --validate-only, --dry-run, --upsert, --batch-size, --verbose)
- [ ] **에러 코드 E001-E006 모두 처리**

---

## Definition of Done (완료 정의)

다음 조건이 **모두** 충족되어야 SPEC-TOEFL-INGEST-001이 완료된 것으로 간주됩니다:

### 기능 완료
- [ ] 모든 Primary Goal Milestone (1.1 ~ 1.5) 완료
- [ ] 모든 AC 시나리오 (AC-ING-001 ~ AC-ING-019) 통과
- [ ] CLI 명령이 정상적으로 실행됨

### 품질 완료
- [ ] Quality Gate 모든 항목 Pass
- [ ] 테스트 커버리지 >= 85%
- [ ] 린터/타입 체커 경고 0건

### 문서 완료
- [ ] CLI `--help` 메시지 완성
- [ ] README에 시딩 가이드 추가
- [ ] 에러 코드 레퍼런스 문서 작성

### 통합 완료
- [ ] SPEC-TOEFL-SCHEMA-001 모델과 정상 연동
- [ ] 실제 external/*.json 파일로 시딩 성공

---

## 테스트 도구 및 프레임워크

### 단위 테스트
- **pytest**: 기본 테스트 프레임워크
- **pytest-asyncio**: 비동기 함수 테스트
- **pytest-cov**: 코드 커버리지 측정

### 통합 테스트
- **subprocess**: CLI 엔드투엔드 테스트
- **testcontainers**: PostgreSQL 컨테이너 (선택)

### Mock 데이터
- **tests/fixtures/**: 테스트용 JSON 파일
  - `valid_sets.json`: 유효한 sets 데이터
  - `invalid_json.json`: 손상된 JSON
  - `missing_fields.json`: 필수 필드 누락
  - `invalid_fk.json`: 존재하지 않는 FK

---

## 테스트 실행 계획

### Phase 1: 단위 테스트 (개발 중)
- **빈도**: 매 커밋마다
- **범위**: 파서, 검증기, 매퍼 개별 함수
- **도구**: pytest

### Phase 2: 통합 테스트 (기능 완료 시)
- **빈도**: PR 머지 전
- **범위**: CLI 명령 전체 플로우
- **도구**: pytest + subprocess

### Phase 3: 성능 테스트 (최적화 시)
- **빈도**: Milestone 완료 시
- **범위**: 대용량 파일 처리, 메모리 사용량
- **도구**: memory_profiler, timeit

---

**작성자**: workflow-spec
**검토자**: 수연
**버전**: 1.0.0
**최종 수정일**: 2026-01-25
