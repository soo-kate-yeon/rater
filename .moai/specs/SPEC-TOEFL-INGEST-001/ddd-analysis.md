# SPEC-TOEFL-INGEST-001 DDD 분석 보고서

## 생성 정보
- **SPEC ID**: SPEC-TOEFL-INGEST-001
- **분석 일시**: 2026-01-27
- **분석자**: manager-ddd
- **DDD 사이클**: ANALYZE-PRESERVE-IMPROVE

---

## Phase 1: ANALYZE - 현재 상태 분석

### 1.1 코드베이스 구조

#### 기존 모델 (src/models/)
✅ **존재하는 모델:**
- `Set` (set.py) - UUID PK, title, source, version, description
- `Item` (item.py) - UUID PK, set_id FK, task_no, task_type, prompt, etc.
- `Stimulus` (stimulus.py) - UUID PK, item_id FK, kind, content_text, asset_url
- `AnswerKey` (answer_key.py) - UUID PK, item_id FK, answer_type, level, content (JSONB)

❌ **누락된 모델:**
- `IndependentTopic` - independent_topics.json 데이터를 저장할 모델 필요

#### 기존 스키마 (src/schemas/)
✅ **API용 스키마 존재:**
- SetBase, SetCreate, SetUpdate, SetResponse
- ItemBase, ItemCreate, ItemUpdate, ItemResponse
- (Stimulus, AnswerKey도 유사 패턴)

❌ **Ingest용 스키마 누락:**
- JSON 파일 파싱을 위한 별도 Pydantic 스키마 필요
- API 스키마와 Ingest 스키마는 구조가 다름 (UUID vs string ID)

#### 서비스 레이어
❌ **Ingest 서비스 미존재:**
- src/services/ingest/ 디렉토리 필요
- Parser, Mapper, Seeder 구현 필요

#### CLI
❌ **CLI 미존재:**
- src/cli/ 디렉토리 필요
- seed.py 명령 구현 필요

### 1.2 JSON 데이터 구조 분석

#### external/sets.json
```json
{
  "set_id": "ACTUAL_TEST_01",  // String ID
  "title": "Speaking Actual Test 1",
  "source": "internal_pdf",
  "version": "1.0.0",
  "created_at": "2026-01-25T07:12:33.227399",
  "updated_at": "2026-01-25T07:12:33.227408"
}
```

**분석:**
- ✅ 기본 필드 일치 (title, source, version)
- ⚠️ **ID 불일치**: JSON은 string ID, 모델은 UUID PK
- ⚠️ **timestamp**: JSON에 있지만 모델은 자동 생성

#### external/independent_topics.json
```json
{
  "topic_id": "INDEPENDENT_TOPIC_001",
  "number": 1,
  "prompt": "In work, do you prefer...",
  "source": "Independent_Topics.pdf"
}
```

**분석:**
- ❌ 모델 자체가 존재하지 않음
- 필드: topic_id (string), number (int), prompt (str), source (str)

### 1.3 아키텍처 갭 분석

#### 주요 불일치 사항

| 항목 | JSON 구조 | 현재 모델 | 해결 방법 |
|------|-----------|-----------|----------|
| **Primary Key** | string ID | UUID | uuid.uuid5() 매핑 |
| **Timestamps** | JSON에 포함 | 자동 생성 | JSON 무시, DB 자동 생성 사용 |
| **Stimulus.kind** | "reading", "listening", "direction" | READING, AUDIO, IMAGE, DIRECTION | Enum 매핑 필요 |
| **AnswerKey.content** | string | JSONB | JSON 래핑 필요 |
| **IndependentTopic** | 존재 | 미존재 | 신규 모델 생성 |

#### 승인된 전략: UUID.uuid5() 매핑 레이어

```python
# 네임스페이스 정의
NAMESPACE_SET = uuid.uuid5(uuid.NAMESPACE_DNS, "toefl.speaking.set")
NAMESPACE_ITEM = uuid.uuid5(uuid.NAMESPACE_DNS, "toefl.speaking.item")
NAMESPACE_STIMULUS = uuid.uuid5(uuid.NAMESPACE_DNS, "toefl.speaking.stimulus")
NAMESPACE_ANSWER_KEY = uuid.uuid5(uuid.NAMESPACE_DNS, "toefl.speaking.answer_key")
NAMESPACE_TOPIC = uuid.uuid5(uuid.NAMESPACE_DNS, "toefl.speaking.topic")

# 매핑 함수
def map_set_id(set_id: str) -> UUID:
    return uuid.uuid5(NAMESPACE_SET, set_id)
```

**장점:**
- 기존 UUID 모델 변경 불필요
- Deterministic 매핑 (같은 string ID → 항상 같은 UUID)
- 데이터 재시딩 시 Idempotency 보장

**단점:**
- 양방향 매핑 불가 (UUID → string ID 복구 불가)
- 별도 매핑 레이어 관리 필요

### 1.4 의존성 분석

#### 시딩 순서 (FK 관계)
```
1. sets.json        → sets 테이블 (독립)
2. items.json       → items 테이블 (FK: set_id)
3. stimuli.json     → stimuli 테이블 (FK: item_id)
4. answer_keys.json → answer_keys 테이블 (FK: item_id)
5. independent_topics.json → independent_topics 테이블 (독립)
```

**FK 무결성 보장 전략:**
- sets → items 시딩 전에 set_id 존재 여부 검증
- items → stimuli/answer_keys 시딩 전에 item_id 검증
- FK 오류 발생 시 전체 트랜잭션 롤백

### 1.5 테스트 커버리지 분석

#### 현재 테스트 상태
```bash
tests/models/test_schema_models.py  # 기존 모델 테스트
tests/api/test_sets.py              # API 테스트
tests/api/test_items.py
```

**분석:**
- ✅ 기존 모델 단위 테스트 존재
- ❌ Ingest 관련 테스트 전무
- 목표: 85%+ 커버리지

---

## Phase 2: 구현 계획

### 2.1 구현 순서 (Milestone 기반)

#### Milestone 1: IndependentTopic 모델 생성 (1h)
**작업:**
1. `src/models/independent_topic.py` 생성
2. BaseModel 상속, UUIDMixin + TimestampMixin 사용
3. 필드: topic_id (UUID PK), number, prompt, source
4. `src/models/__init__.py`에 등록

**검증:**
- 모델 import 성공
- Alembic 마이그레이션 생성 가능

#### Milestone 2: Ingest Pydantic 스키마 정의 (1.5h)
**작업:**
1. `src/schemas/ingest/` 디렉토리 생성
2. 5개 스키마 파일 작성:
   - `set.py` → SetIngest (set_id: str, title, source, version, created_at?, updated_at?)
   - `item.py` → ItemIngest (item_id: str, set_id: str, task_no, task_type, ...)
   - `stimulus.py` → StimulusIngest (stimulus_id: str, item_id: str, kind, ...)
   - `answer_key.py` → AnswerKeyIngest (answer_id: str, item_id: str, type, level?, content: str, source)
   - `topic.py` → IndependentTopicIngest (topic_id: str, number, prompt, source)

**검증:**
- 각 스키마로 external/*.json 파싱 성공
- 스키마 검증 통과 (필수 필드, 타입 검증)

#### Milestone 3: ID 매핑 레이어 구현 (2h) ⭐ **핵심**
**작업:**
1. `src/services/ingest/id_mapper.py` 생성
2. 네임스페이스 상수 정의
3. 매핑 함수 구현:
   ```python
   class IDMapper:
       @staticmethod
       def to_set_uuid(set_id: str) -> UUID
       @staticmethod
       def to_item_uuid(item_id: str) -> UUID
       @staticmethod
       def to_stimulus_uuid(stimulus_id: str) -> UUID
       @staticmethod
       def to_answer_key_uuid(answer_id: str) -> UUID
       @staticmethod
       def to_topic_uuid(topic_id: str) -> UUID
   ```

**검증:**
- 동일 string ID → 동일 UUID 매핑 (Deterministic)
- 다른 string ID → 다른 UUID

#### Milestone 4: Parser 구현 (1h)
**작업:**
1. `src/services/ingest/parser.py` 생성
2. 함수 구현:
   ```python
   def load_json_file(path: Path) -> list[dict]  # UTF-8 강제
   def parse_to_schema(data: list[dict], schema: type[BaseModel]) -> list[BaseModel]
   def stream_json_file(path: Path) -> Generator[dict, None, None]  # 대용량 파일용
   ```

**검증:**
- UTF-8 인코딩 테스트
- 파싱 오류 처리 (JSONDecodeError)
- 스키마 검증 실패 처리 (ValidationError)

#### Milestone 5: Mapper 구현 (1.5h)
**작업:**
1. `src/services/ingest/mapper.py` 생성
2. Ingest 스키마 → ORM 모델 변환:
   ```python
   class ModelMapper:
       def __init__(self, id_mapper: IDMapper)

       def to_set_model(schema: SetIngest) -> Set
       def to_item_model(schema: ItemIngest) -> Item
       def to_stimulus_model(schema: StimulusIngest) -> Stimulus
       def to_answer_key_model(schema: AnswerKeyIngest) -> AnswerKey
       def to_topic_model(schema: IndependentTopicIngest) -> IndependentTopic
   ```

**핵심 로직:**
- string ID → UUID 변환 (IDMapper 사용)
- Enum 매핑 (kind: str → StimulusKind enum)
- JSONB 래핑 (AnswerKey.content: str → {"text": content})
- created_at/updated_at 무시 (DB 자동 생성)

**검증:**
- 매핑 결과가 ORM 모델 인스턴스
- FK 관계 유지 (set_id, item_id 일관성)

#### Milestone 6: Seeder 구현 (1h)
**작업:**
1. `src/services/ingest/seeder.py` 생성
2. 함수 구현:
   ```python
   async def bulk_insert(
       session: AsyncSession,
       models: list[Base],
       batch_size: int = 100
   ) -> dict[str, int]  # {"inserted": 100}

   async def upsert_batch(
       session: AsyncSession,
       models: list[Base],
       pk_field: str = "id"
   ) -> dict[str, int]  # {"inserted": 20, "updated": 80}
   ```

**검증:**
- 트랜잭션 관리 (오류 시 롤백)
- 배치 크기 조절
- 진행률 로깅

#### Milestone 7: CLI 구현 (1.5h)
**작업:**
1. `src/cli/seed.py` 생성 (Click 프레임워크)
2. 명령 및 옵션:
   ```bash
   python -m src.cli.seed --file=external/sets.json
   python -m src.cli.seed --all
   python -m src.cli.seed --validate-only
   python -m src.cli.seed --dry-run
   python -m src.cli.seed --upsert
   python -m src.cli.seed --batch-size=50
   python -m src.cli.seed --verbose
   ```

**검증:**
- 각 옵션 정상 작동
- 에러 코드 E001-E006 처리
- 친화적 오류 메시지

#### Milestone 8: 테스트 작성 (1.5h)
**작업:**
1. 단위 테스트:
   - `tests/services/ingest/test_parser.py`
   - `tests/services/ingest/test_mapper.py`
   - `tests/services/ingest/test_id_mapper.py`
2. 통합 테스트:
   - `tests/cli/test_seed.py`
3. Fixtures:
   - `tests/fixtures/ingest/` (테스트용 JSON 파일)

**AC 시나리오 매핑:**
- AC-ING-001 ~ AC-ING-005: 파싱 테스트
- AC-ING-006 ~ AC-ING-007: 에러 처리 테스트
- AC-ING-008 ~ AC-ING-019: CLI 통합 테스트

**검증:**
- pytest 커버리지 85% 이상
- 모든 AC 시나리오 통과

#### Milestone 9: Integration & Validation (0.5h)
**작업:**
1. 실제 데이터로 전체 시딩 테스트
2. 성능 측정 (파싱 속도, Insert 속도)
3. 문서 업데이트

**검증:**
- 전체 시딩 1분 이내
- 메모리 사용량 512MB 이하

### 2.2 파일 생성 계획

```
src/
├── models/
│   └── independent_topic.py      # 신규
├── schemas/
│   └── ingest/                   # 신규 디렉토리
│       ├── __init__.py
│       ├── set.py
│       ├── item.py
│       ├── stimulus.py
│       ├── answer_key.py
│       └── topic.py
├── services/
│   └── ingest/                   # 신규 디렉토리
│       ├── __init__.py
│       ├── parser.py
│       ├── mapper.py
│       ├── id_mapper.py
│       ├── seeder.py
│       └── validator.py
└── cli/
    ├── __init__.py
    └── seed.py                   # 신규

tests/
├── models/
│   └── test_independent_topic.py # 신규
├── services/
│   └── ingest/                   # 신규 디렉토리
│       ├── test_parser.py
│       ├── test_mapper.py
│       ├── test_id_mapper.py
│       └── test_seeder.py
├── cli/
│   └── test_seed.py              # 신규
└── fixtures/
    └── ingest/                   # 신규 디렉토리
        ├── valid_sets.json
        ├── invalid_json.json
        └── missing_fields.json
```

### 2.3 리스크 및 대응

| 리스크 | 확률 | 영향 | 대응 전략 |
|--------|------|------|----------|
| FK 무결성 오류 | Medium | High | 시딩 전 FK 검증 + 의존성 순서 엄격 적용 |
| ID 매핑 충돌 | Low | High | uuid.uuid5() 사용으로 충돌 방지 (Deterministic) |
| 스키마 불일치 | Medium | Medium | Pydantic extra="ignore" + 버전 관리 |
| 성능 저하 | Low | Medium | 배치 크기 조절 + ijson 스트리밍 |
| 테스트 커버리지 부족 | Medium | High | AC 시나리오 기반 체계적 테스트 작성 |

---

## Phase 3: PRESERVE - 안전망 구축

### 3.1 기존 테스트 검증
- 기존 모델 테스트 실행 (`tests/models/`)
- API 테스트 실행 (`tests/api/`)
- 모든 테스트 통과 확인

### 3.2 Characterization 테스트
- 기존 Set, Item, Stimulus, AnswerKey 모델 동작 스냅샷
- ORM 관계 (back_populates) 정상 작동 확인
- Enum 매핑 정확성 검증

### 3.3 Regression 방지
- Ingest 구현이 기존 API에 영향 없음 확인
- 모델 변경 없음 (IndependentTopic만 추가)
- 스키마 네임스페이스 분리 (ingest/ 별도)

---

## Phase 4: IMPROVE - 점진적 구현

### 4.1 구현 진행 상황 추적
```
[ ] Milestone 1: IndependentTopic 모델 (1h)
[ ] Milestone 2: Ingest 스키마 (1.5h)
[ ] Milestone 3: ID 매핑 레이어 (2h)
[ ] Milestone 4: Parser (1h)
[ ] Milestone 5: Mapper (1.5h)
[ ] Milestone 6: Seeder (1h)
[ ] Milestone 7: CLI (1.5h)
[ ] Milestone 8: 테스트 (1.5h)
[ ] Milestone 9: Integration (0.5h)
```

**예상 총 소요 시간**: 11.5시간

### 4.2 DDD 검증 포인트
각 Milestone 완료 후:
1. 관련 단위 테스트 실행
2. 기존 테스트 여전히 통과 확인
3. 커밋 생성 (atomic change)

---

## 성공 지표

### 기능 완료
- [ ] 5개 JSON 파일 모두 파싱 가능
- [ ] CLI 7개 옵션 모두 작동
- [ ] 전체 시딩 정상 완료 (1200+ 레코드)

### 품질 완료
- [ ] 테스트 커버리지 >= 85%
- [ ] 모든 AC 시나리오 (19개) 통과
- [ ] Ruff/Pyright 경고 0건

### 성능 완료
- [ ] 파싱 속도 >= 1000 레코드/초
- [ ] Insert 속도 >= 500 레코드/초
- [ ] 전체 시딩 <= 1분
- [ ] 메모리 <= 512MB

---

**분석 완료일**: 2026-01-27
**다음 단계**: Milestone 1 구현 시작 (IndependentTopic 모델)
