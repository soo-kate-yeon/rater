# SPEC-TOEFL-SCHEMA-001: TOEFL Speaking 정규화 데이터 스키마 확장

---
spec_id: SPEC-TOEFL-SCHEMA-001
title: TOEFL Speaking 정규화 데이터 스키마 확장
created: 2026-01-25
status: completed
priority: High
assigned: manager-spec
depends_on:
  - SPEC-TOEFL-001
lifecycle: spec-anchored
---

## HISTORY

| 버전 | 날짜 | 작성자 | 변경 내용 |
|------|------|--------|-----------|
| 1.0.0 | 2026-01-25 | manager-spec | 초기 SPEC 작성 |

---

## 개요

TOEFL Speaking 작업 지시서 v2.2에 따른 정규화된 데이터 스키마를 구현합니다. 기존 `Task` 모델을 확장하여 문제 세트(Set), 개별 문항(Item), 자극자료(Stimulus), 모범답안(AnswerKey) 구조를 도입하고, Blueprint JSON 스키마를 Pydantic v2 모델로 정의합니다.

### 핵심 가치

- **정규화된 데이터 구조**: 중복 제거 및 데이터 일관성 보장
- **확장 가능한 스키마**: Independent/Integrated 문제 유형별 특화 필드 지원
- **타입 안전성**: Pydantic v2 모델을 통한 엄격한 데이터 검증
- **추적 가능성**: Set-Item-Stimulus-AnswerKey 관계를 통한 완전한 문제 추적

---

## Environment (환경)

### 기술 스택

#### Backend
- **Python**: 3.11+
- **FastAPI**: 0.115+
- **SQLAlchemy**: 2.0+ (async 지원)
- **Pydantic**: v2.9+
- **Alembic**: 1.13+ (마이그레이션)
- **PostgreSQL**: 15+

#### 데이터베이스
- **UUID 기반 PK**: 모든 테이블에 UUID 기본 키 사용
- **JSONB 필드**: Blueprint, tags 등 복잡한 데이터 저장
- **Foreign Key with CASCADE**: 참조 무결성 및 연쇄 삭제 지원
- **Index 전략**: 자주 조회되는 필드에 인덱스 적용

### 운영 환경

- **Database**: PostgreSQL 15+ (Supabase 또는 RDS)
- **Migration Tool**: Alembic (async 지원)
- **File Storage**: AWS S3 (audio/image assets)

---

## Assumptions (가정사항)

### 기술 가정

1. **SQLAlchemy 2.0 async 패턴**이 안정적으로 작동하며, relationship loading 시 N+1 문제가 발생하지 않도록 적절한 lazy loading 전략을 적용한다고 가정합니다.

2. **Pydantic v2의 model_validate**가 ORM 객체에서 효율적으로 변환되며, nested 모델 직렬화 시 성능 저하가 없다고 가정합니다.

3. **Alembic autogenerate**가 SQLAlchemy 2.0 모델 변경을 정확히 감지하며, UUID 및 JSONB 타입을 올바르게 처리한다고 가정합니다.

4. **PostgreSQL JSONB 인덱싱**이 Blueprint 필드 쿼리에 충분한 성능을 제공한다고 가정합니다.

### 비즈니스 가정

1. **Set-Item 관계**가 1:N으로 설계되며, 하나의 Item은 반드시 하나의 Set에 속한다고 가정합니다.

2. **Stimulus 순서(order 필드)**가 문제 제시 순서를 결정하며, reading -> audio -> image 순서가 일반적이라고 가정합니다.

3. **AnswerKey의 level 필드**가 high/mid/low 3단계로 충분하다고 가정합니다.

### 리스크 분석

| 가정사항 | 신뢰도 | 근거 | 틀렸을 경우 리스크 | 검증 방법 |
|---------|--------|------|-------------------|----------|
| SQLAlchemy async 안정성 | High | 공식 문서 및 프로덕션 사례 | 쿼리 실패 및 데이터 불일치 | 통합 테스트 |
| Pydantic ORM 변환 성능 | High | Pydantic v2 벤치마크 | 응답 지연 | 성능 테스트 |
| JSONB 인덱싱 성능 | Medium | PostgreSQL 문서 | 쿼리 속도 저하 | 쿼리 성능 측정 |

---

## Requirements (요구사항)

### 1. Ubiquitous Requirements (시스템 전체 필수 요구사항)

#### REQ-SCHEMA-001: UUID 기반 Primary Key
**시스템은 항상** 모든 새로운 모델(Set, Item, Stimulus, AnswerKey)에 UUID 타입의 primary key를 사용**해야 한다**.

**WHY**: 분산 시스템에서 ID 충돌 방지 및 보안 강화
**IMPACT**: 순차 ID 사용 시 데이터 노출 위험 및 ID 예측 공격 가능

#### REQ-SCHEMA-002: Foreign Key Cascade Delete
**시스템은 항상** 부모 레코드 삭제 시 관련 자식 레코드를 연쇄 삭제**해야 한다**:
- Set 삭제 시 → 연결된 Item 삭제
- Item 삭제 시 → 연결된 Stimulus, AnswerKey 삭제

**WHY**: 고아 레코드 방지 및 데이터 일관성 유지
**IMPACT**: CASCADE 미적용 시 참조 무결성 위반 및 저장소 낭비

#### REQ-SCHEMA-003: Timestamp 자동 관리
**시스템은 항상** created_at 및 updated_at 필드를 자동으로 관리**해야 한다**:
- created_at: 레코드 생성 시 자동 설정
- updated_at: 레코드 수정 시 자동 갱신

**WHY**: 데이터 변경 이력 추적 및 캐시 무효화 지원
**IMPACT**: 타임스탬프 누락 시 디버깅 및 감사 불가능

---

### 2. Event-Driven Requirements (이벤트 기반 요구사항)

#### REQ-SCHEMA-004: Set 생성 시 버전 검증
**WHEN** 새로운 Set을 생성하면,
**THEN** 시스템은 동일 source에서 더 높은 version이 존재하는지 검증하고, 존재할 경우 경고 로그를 기록**해야 한다**.

**WHY**: 버전 관리 일관성 및 중복 Set 방지
**IMPACT**: 검증 누락 시 동일 문제 세트의 여러 버전이 혼재될 수 있음

#### REQ-SCHEMA-005: Item 생성 시 task_no 자동 할당
**WHEN** Set에 새로운 Item을 추가하면,
**THEN** 시스템은 해당 Set 내에서 task_no를 자동으로 1씩 증가시켜 할당**해야 한다**.

**WHY**: 수동 번호 할당 오류 방지 및 일관성 보장
**IMPACT**: 자동 할당 미적용 시 중복 또는 누락된 task_no 발생 가능

#### REQ-SCHEMA-006: Stimulus 생성 시 kind별 필수 필드 검증
**WHEN** Stimulus를 생성하면,
**THEN** 시스템은 kind에 따라 필수 필드를 검증**해야 한다**:
- `reading`: content_text 필수
- `audio`: asset_url 및 duration_seconds 필수
- `image`: asset_url 필수
- `direction`: content_text 필수

**WHY**: 자극자료 타입별 데이터 무결성 보장
**IMPACT**: 검증 누락 시 불완전한 Stimulus 데이터로 인한 문제 표시 오류

---

### 3. State-Driven Requirements (상태 기반 요구사항)

#### REQ-SCHEMA-007: Independent Item 전용 필드 조건부 필수
**IF** Item의 task_type이 INDEPENDENT**이면**,
**THEN** 시스템은 topic_type 및 topic_category 필드가 설정되도록 강제**해야 한다**.

**WHY**: Independent 문제 유형의 특성 반영
**IMPACT**: 필드 누락 시 문제 분류 및 분석 불가능

#### REQ-SCHEMA-008: Integrated Item Blueprint 스키마 적용
**IF** Item의 task_type이 INTEGRATED**이면**,
**THEN** 해당 Item의 AnswerKey 중 type='blueprint'인 레코드는 IntegratedBlueprint JSON 스키마를 준수**해야 한다**.

**WHY**: 통합형 문제의 구조화된 모범답안 제공
**IMPACT**: 스키마 미준수 시 LLM 프롬프트 생성 실패

---

### 4. Unwanted Requirements (금지 요구사항)

#### REQ-SCHEMA-009: 순환 참조 금지
**시스템은** Set-Item-Stimulus-AnswerKey 관계에서 순환 참조가 발생**하지 않아야 한다**.

**WHY**: 무한 루프 및 메모리 오버플로우 방지
**IMPACT**: 순환 참조 시 ORM 직렬화 실패 및 API 응답 무한 대기

#### REQ-SCHEMA-010: 빈 Set 저장 금지
**시스템은** Item이 하나도 없는 Set을 저장**하지 않아야 한다**. 최소 1개 이상의 Item이 필요하다.

**WHY**: 의미 없는 데이터 저장 방지
**IMPACT**: 빈 Set 허용 시 데이터 정리 비용 증가

---

### 5. Optional Requirements (선택 요구사항)

#### REQ-SCHEMA-011: Blueprint 버전 관리
**가능하면**, Blueprint 스키마에 schema_version 필드를 추가하여 향후 스키마 변경 시 하위 호환성을 유지**할 수 있다**.

**WHY**: 장기적인 스키마 진화 지원
**IMPACT**: 미구현 시에도 현재 버전 내에서 정상 작동

#### REQ-SCHEMA-012: Full-text 검색 인덱스
**가능하면**, Item.prompt 및 Stimulus.content_text 필드에 PostgreSQL full-text 검색 인덱스를 추가**할 수 있다**.

**WHY**: 문제 검색 기능 성능 향상
**IMPACT**: 미구현 시 LIKE 쿼리로 대체 가능

---

## Specifications (세부 명세)

### 1. Set 모델 (문제 세트)

```sql
CREATE TABLE sets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(200) NOT NULL,
    source VARCHAR(100) NOT NULL,  -- "ETS Official", "Kaplan", "Custom"
    version VARCHAR(20) NOT NULL,  -- "v1.0", "v2.2"
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_sets_source ON sets(source);
CREATE INDEX idx_sets_version ON sets(version);
CREATE UNIQUE INDEX idx_sets_source_version ON sets(source, version);
```

### 2. Item 모델 (개별 문항)

```sql
CREATE TABLE items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    set_id UUID NOT NULL REFERENCES sets(id) ON DELETE CASCADE,
    task_no INTEGER NOT NULL,  -- 1, 2, 3, 4
    task_type VARCHAR(20) NOT NULL,  -- "INDEPENDENT", "INTEGRATED"
    prompt TEXT NOT NULL,
    prep_seconds INTEGER NOT NULL DEFAULT 15,  -- 준비 시간
    response_seconds INTEGER NOT NULL DEFAULT 45,  -- 응답 시간

    -- Independent 전용 필드
    topic_type VARCHAR(30),  -- "preference", "agree_disagree", "description", "opinion", "hypothetical"
    topic_category VARCHAR(30),  -- "education", "technology", "lifestyle", "work", "relationships", "society"
    question_pattern VARCHAR(100),  -- "Do you agree or disagree...", "Some people prefer..."

    -- 공통 필드
    tags JSONB DEFAULT '[]',
    difficulty VARCHAR(10),  -- "easy", "medium", "hard"
    scoring_focus JSONB DEFAULT '{}',  -- {"structure": 0.3, "language": 0.4, "delivery": 0.3}

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_items_set_id ON items(set_id);
CREATE INDEX idx_items_task_type ON items(task_type);
CREATE INDEX idx_items_topic_type ON items(topic_type);
CREATE INDEX idx_items_difficulty ON items(difficulty);
CREATE UNIQUE INDEX idx_items_set_task_no ON items(set_id, task_no);
```

### 3. Stimulus 모델 (자극자료)

```sql
CREATE TABLE stimuli (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    item_id UUID NOT NULL REFERENCES items(id) ON DELETE CASCADE,
    kind VARCHAR(20) NOT NULL,  -- "reading", "audio", "image", "direction"
    title VARCHAR(200),
    content_text TEXT,  -- reading, direction용 텍스트
    asset_url VARCHAR(500),  -- audio, image용 S3 URL
    duration_seconds INTEGER,  -- audio 길이
    display_order INTEGER NOT NULL DEFAULT 0,
    notes_allowed BOOLEAN DEFAULT false,  -- 노트 필기 허용 여부

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_stimuli_item_id ON stimuli(item_id);
CREATE INDEX idx_stimuli_kind ON stimuli(kind);
CREATE INDEX idx_stimuli_order ON stimuli(item_id, display_order);
```

### 4. AnswerKey 모델 (모범답안/구조)

```sql
CREATE TABLE answer_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    item_id UUID NOT NULL REFERENCES items(id) ON DELETE CASCADE,
    answer_type VARCHAR(30) NOT NULL,  -- "sample_response", "transcript", "outline", "points", "blueprint"
    level VARCHAR(10),  -- "high", "mid", "low"
    content JSONB NOT NULL,  -- 모범답안 내용 또는 Blueprint JSON
    source VARCHAR(100),  -- "ETS Official", "Expert Review"

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_answer_keys_item_id ON answer_keys(item_id);
CREATE INDEX idx_answer_keys_type ON answer_keys(answer_type);
CREATE INDEX idx_answer_keys_level ON answer_keys(level);
```

### 5. Enum 타입 정의

#### TopicType Enum
```python
class TopicType(str, enum.Enum):
    PREFERENCE = "preference"           # "Do you prefer A or B?"
    AGREE_DISAGREE = "agree_disagree"   # "Do you agree or disagree..."
    DESCRIPTION = "description"         # "Describe a..."
    OPINION = "opinion"                 # "What is your opinion..."
    HYPOTHETICAL = "hypothetical"       # "If you could..."
```

#### TopicCategory Enum
```python
class TopicCategory(str, enum.Enum):
    EDUCATION = "education"
    TECHNOLOGY = "technology"
    LIFESTYLE = "lifestyle"
    WORK = "work"
    RELATIONSHIPS = "relationships"
    SOCIETY = "society"
```

#### StimulusKind Enum
```python
class StimulusKind(str, enum.Enum):
    READING = "reading"
    AUDIO = "audio"
    IMAGE = "image"
    DIRECTION = "direction"
```

#### AnswerKeyType Enum
```python
class AnswerKeyType(str, enum.Enum):
    SAMPLE_RESPONSE = "sample_response"
    TRANSCRIPT = "transcript"
    OUTLINE = "outline"
    POINTS = "points"
    BLUEPRINT = "blueprint"
```

#### AnswerKeyLevel Enum
```python
class AnswerKeyLevel(str, enum.Enum):
    HIGH = "high"
    MID = "mid"
    LOW = "low"
```

### 6. Blueprint Pydantic 모델

#### IntegratedBlueprint Schema

```python
from pydantic import BaseModel, Field
from typing import Literal

class InfoUnit(BaseModel):
    """정보 단위"""
    source: Literal["reading", "listening"]
    label: str  # "Main Point", "Example 1", "Reason"
    content: str
    importance: Literal["essential", "supporting", "optional"] = "supporting"

class LinkingMove(BaseModel):
    """연결 표현"""
    position: str  # "transition_to_listening", "contrast", "conclusion"
    phrases: list[str]

class TimeBudget(BaseModel):
    """시간 배분"""
    intro_seconds: int = Field(ge=5, le=15)
    reading_summary_seconds: int = Field(ge=10, le=20)
    listening_summary_seconds: int = Field(ge=15, le=30)
    conclusion_seconds: int = Field(ge=5, le=10)

class IntegratedBlueprint(BaseModel):
    """통합형 문제 Blueprint"""
    schema_version: str = "1.0"
    info_units: list[InfoUnit]
    recommended_order: list[str]  # ["reading_main", "listening_example_1", ...]
    linking_moves: list[LinkingMove]
    coverage_expectations: dict[str, float]  # {"reading": 0.3, "listening": 0.7}
    time_budget: TimeBudget
```

#### IndependentBlueprint Schema

```python
class ScoreExpectation(BaseModel):
    """점수 기대치"""
    structure_weight: float = Field(ge=0, le=1)
    language_weight: float = Field(ge=0, le=1)
    delivery_weight: float = Field(ge=0, le=1)

class IndependentBlueprint(BaseModel):
    """독립형 문제 Blueprint"""
    schema_version: str = "1.0"
    topic_type: TopicType
    recommended_structure: list[str]  # ["intro", "reason_1", "example_1", "reason_2", "example_2", "conclusion"]
    linking_moves: list[LinkingMove]
    score_expectations: ScoreExpectation
    topic_specific_vocabulary: list[str]
    time_budget: TimeBudget
```

### 7. 기존 Task 모델과의 관계

기존 `Task` 모델은 **하위 호환성**을 위해 유지하되, 새로운 `Item` 모델과 연결됩니다:

```python
class Task(Base, UUIDMixin):
    """기존 Task 모델 (Deprecated - Item으로 마이그레이션 예정)"""
    __tablename__ = "tasks"

    # 기존 필드 유지
    task_type: Mapped[TaskType]
    prompt: Mapped[str]
    source_reading: Mapped[str | None]
    source_listening: Mapped[str | None]
    tags: Mapped[dict]
    created_at: Mapped[datetime]

    # 새 필드: Item 참조
    item_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("items.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
```

---

## Traceability (추적성)

- **관련 SPEC**: SPEC-TOEFL-001 (기존 DB 인프라 및 User/Job 모델)
- **Epic**: Data Schema Normalization
- **Labels**: `database`, `schema`, `migration`, `backend`
- **영향 범위**:
  - src/models/ (신규 모델 추가)
  - src/schemas/ (Pydantic 스키마 추가)
  - alembic/versions/ (마이그레이션 스크립트)

---

## 참고 문서

- **SQLAlchemy 2.0 Documentation**: https://docs.sqlalchemy.org/en/20/
- **Pydantic v2 Documentation**: https://docs.pydantic.dev/latest/
- **Alembic Documentation**: https://alembic.sqlalchemy.org/
- **TOEFL Speaking Rubric**: ETS Official Guidelines

---

**작성자**: manager-spec
**검토자**: 수연
**버전**: 1.0.0
**최종 수정일**: 2026-01-25
