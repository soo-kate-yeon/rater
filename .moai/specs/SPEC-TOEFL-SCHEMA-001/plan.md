# SPEC-TOEFL-SCHEMA-001: 구현 계획

---
spec_id: SPEC-TOEFL-SCHEMA-001
title: TOEFL Speaking 정규화 데이터 스키마 확장 - 구현 계획
created: 2026-01-25
status: draft
priority: High
assigned: manager-spec
---

## HISTORY

| 버전 | 날짜 | 작성자 | 변경 내용 |
|------|------|--------|-----------|
| 1.0.0 | 2026-01-25 | manager-spec | 초기 계획 작성 |

---

## 구현 개요

TOEFL Speaking 정규화 데이터 스키마를 구현하기 위한 단계별 계획입니다. 기존 시스템과의 하위 호환성을 유지하면서 새로운 정규화 구조를 도입합니다.

---

## 마일스톤

### Primary Goal: 핵심 모델 및 마이그레이션

**목표**: Set, Item, Stimulus, AnswerKey 모델 생성 및 DB 마이그레이션

**산출물**:
- [ ] `src/models/set.py` - Set 모델
- [ ] `src/models/item.py` - Item 모델 (기존 Task 확장)
- [ ] `src/models/stimulus.py` - Stimulus 모델
- [ ] `src/models/answer_key.py` - AnswerKey 모델
- [ ] `src/models/__init__.py` 업데이트
- [ ] `alembic/versions/xxx_add_normalized_schema.py` - 마이그레이션 스크립트

**기술 접근**:
1. BaseModel(UUIDMixin, TimestampMixin) 상속 패턴 사용
2. SQLAlchemy 2.0 Mapped 타입 힌트 적용
3. relationship 설정 시 back_populates 명시
4. lazy="selectin" 또는 "joined" 전략 선택

---

### Secondary Goal: Enum 및 Pydantic 스키마

**목표**: 타입 정의 및 데이터 검증 스키마 구현

**산출물**:
- [ ] `src/models/enums.py` - TopicType, TopicCategory, StimulusKind, AnswerKeyType, AnswerKeyLevel
- [ ] `src/schemas/set.py` - SetCreate, SetRead, SetUpdate
- [ ] `src/schemas/item.py` - ItemCreate, ItemRead, ItemUpdate
- [ ] `src/schemas/stimulus.py` - StimulusCreate, StimulusRead
- [ ] `src/schemas/answer_key.py` - AnswerKeyCreate, AnswerKeyRead
- [ ] `src/schemas/blueprint.py` - IntegratedBlueprint, IndependentBlueprint

**기술 접근**:
1. str Enum 상속으로 JSON 직렬화 호환성 보장
2. Pydantic ConfigDict(from_attributes=True) 적용
3. Field(ge=, le=) 등 제약 조건 명시
4. Optional 필드와 Required 필드 명확히 구분

---

### Tertiary Goal: API 엔드포인트

**목표**: CRUD API 구현

**산출물**:
- [ ] `src/api/routers/sets.py` - Set CRUD
- [ ] `src/api/routers/items.py` - Item CRUD
- [ ] `src/api/routers/stimuli.py` - Stimulus CRUD
- [ ] `src/api/routers/answer_keys.py` - AnswerKey CRUD
- [ ] `src/api/main.py` 라우터 등록

**기술 접근**:
1. FastAPI Depends를 통한 DB 세션 주입
2. async def로 비동기 핸들러 구현
3. HTTPException으로 에러 응답 표준화
4. Pagination 지원 (offset, limit)

---

### Final Goal: 테스트 및 문서화

**목표**: 테스트 커버리지 85% 이상 및 API 문서 완성

**산출물**:
- [ ] `tests/models/test_set.py`
- [ ] `tests/models/test_item.py`
- [ ] `tests/models/test_stimulus.py`
- [ ] `tests/models/test_answer_key.py`
- [ ] `tests/schemas/test_blueprint.py`
- [ ] `tests/api/test_sets_router.py`
- [ ] OpenAPI 스키마 검증

**기술 접근**:
1. pytest-asyncio로 비동기 테스트
2. Factory Boy 또는 fixture factory 패턴
3. 유닛 테스트 + 통합 테스트 분리
4. FastAPI TestClient 사용

---

### Optional Goal: 기존 Task 마이그레이션

**목표**: 기존 Task 데이터를 새 Item 구조로 마이그레이션

**산출물**:
- [ ] `scripts/migrate_tasks_to_items.py` - 데이터 마이그레이션 스크립트
- [ ] `alembic/versions/xxx_link_task_to_item.py` - Task.item_id FK 추가

**기술 접근**:
1. 점진적 마이그레이션 (dual-write 패턴)
2. 롤백 가능한 스크립트 설계
3. 기존 API 엔드포인트 하위 호환성 유지

---

## 기술 접근 방법

### 1. 모델 설계 원칙

```python
# 기본 패턴: BaseModel 상속
class Set(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "sets"

    title: Mapped[str] = mapped_column(String(200), nullable=False)
    source: Mapped[str] = mapped_column(String(100), nullable=False)
    version: Mapped[str] = mapped_column(String(20), nullable=False)

    # 관계 정의
    items: Mapped[list["Item"]] = relationship(
        "Item",
        back_populates="set",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
```

### 2. Pydantic 스키마 패턴

```python
# ORM 변환 지원
class SetRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    source: str
    version: str
    created_at: datetime
    updated_at: datetime
    items: list["ItemRead"] = []

# 생성 스키마
class SetCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    source: str = Field(min_length=1, max_length=100)
    version: str = Field(pattern=r"^v\d+\.\d+$")
```

### 3. 마이그레이션 전략

```python
# Alembic 마이그레이션
def upgrade() -> None:
    # 1. Enum 타입 생성
    topic_type_enum = sa.Enum('preference', 'agree_disagree', 'description', 'opinion', 'hypothetical', name='topic_type_enum')
    topic_type_enum.create(op.get_bind())

    # 2. 테이블 생성
    op.create_table(
        'sets',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('title', sa.String(200), nullable=False),
        # ...
    )

    # 3. 인덱스 생성
    op.create_index('idx_sets_source', 'sets', ['source'])

def downgrade() -> None:
    op.drop_table('sets')
    # Enum 삭제
    sa.Enum(name='topic_type_enum').drop(op.get_bind())
```

### 4. API 라우터 패턴

```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/v1/sets", tags=["sets"])

@router.post("/", response_model=SetRead, status_code=status.HTTP_201_CREATED)
async def create_set(
    set_data: SetCreate,
    db: AsyncSession = Depends(get_db),
) -> Set:
    """문제 세트 생성"""
    new_set = Set(**set_data.model_dump())
    db.add(new_set)
    await db.commit()
    await db.refresh(new_set)
    return new_set
```

---

## 아키텍처 설계

### 데이터 흐름

```
[Client] → [FastAPI Router] → [Pydantic Validation] → [SQLAlchemy Model] → [PostgreSQL]
                                      ↓
                              [Blueprint Schema]
                                      ↓
                              [JSONB Storage]
```

### 모델 관계도

```
┌─────────┐
│   Set   │
│─────────│
│ id (PK) │
│ title   │
│ source  │
│ version │
└────┬────┘
     │ 1:N
     ▼
┌─────────────┐
│    Item     │
│─────────────│
│ id (PK)     │
│ set_id (FK) │◄── CASCADE DELETE
│ task_no     │
│ task_type   │
│ prompt      │
│ topic_type  │  (Independent only)
│ topic_cat   │  (Independent only)
└──────┬──────┘
       │ 1:N
       ├───────────────┐
       ▼               ▼
┌───────────┐   ┌────────────┐
│ Stimulus  │   │ AnswerKey  │
│───────────│   │────────────│
│ id (PK)   │   │ id (PK)    │
│ item_id   │   │ item_id    │
│ kind      │   │ type       │
│ content   │   │ level      │
│ asset_url │   │ content    │
│ order     │   │ (JSONB)    │
└───────────┘   └────────────┘
```

---

## 리스크 및 대응 계획

### 리스크 1: 마이그레이션 중 데이터 손실

**대응**:
- 마이그레이션 전 전체 DB 백업
- 개발/스테이징 환경에서 먼저 테스트
- 롤백 스크립트(downgrade) 철저히 검증

### 리스크 2: N+1 쿼리 문제

**대응**:
- `selectinload` 또는 `joinedload` 적용
- 필요 시 쿼리별 eager loading 명시
- SQL 로깅으로 실제 쿼리 모니터링

### 리스크 3: Blueprint JSON 스키마 변경

**대응**:
- `schema_version` 필드로 버전 관리
- 하위 호환 파서 구현
- Optional 필드 활용으로 유연성 확보

---

## 의존성

### 내부 의존성

- SPEC-TOEFL-001의 기존 DB 인프라 (User, Job, JobArtifact, Report)
- 기존 Task 모델과의 하위 호환성

### 외부 의존성

- PostgreSQL 15+ (UUID, JSONB 지원)
- SQLAlchemy 2.0+ (async, Mapped 타입)
- Pydantic v2.9+ (ConfigDict, Field)
- Alembic 1.13+ (async 지원)

---

## 체크리스트

### 구현 전

- [ ] 기존 Task 테이블 데이터 백업
- [ ] 개발 환경 PostgreSQL 버전 확인
- [ ] SQLAlchemy/Pydantic 버전 확인

### 구현 중

- [ ] 각 모델별 단위 테스트 작성
- [ ] 마이그레이션 스크립트 로컬 테스트
- [ ] API 엔드포인트 OpenAPI 문서 확인

### 구현 후

- [ ] 전체 테스트 커버리지 85% 이상
- [ ] 성능 테스트 (1000개 Item 조회)
- [ ] 코드 리뷰 및 머지

---

## 다음 단계

1. `/moai:2-run SPEC-TOEFL-SCHEMA-001` 실행하여 구현 시작
2. Primary Goal 완료 후 마이그레이션 적용
3. API 엔드포인트 구현 및 테스트
4. 기존 Task 데이터 마이그레이션 검토

---

**작성자**: manager-spec
**검토자**: 수연
**버전**: 1.0.0
**최종 수정일**: 2026-01-25
