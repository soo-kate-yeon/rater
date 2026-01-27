# SPEC-TOEFL-INGEST-001 구현 상태

## 현재 상태: 🟡 부분 완료 (핵심 아키텍처 완성)

**마지막 업데이트**: 2026-01-27
**완료도**: 40% (핵심 아키텍처 100%, 서비스/CLI 0%)

---

## ✅ 완료된 작업

### 1. IndependentTopic 모델 ✅
**파일**: `src/models/independent_topic.py`

```python
class IndependentTopic(BaseModel):
    """Independent Speaking 토픽 모델"""
    __tablename__ = "independent_topics"

    number: Mapped[int]     # 토픽 번호 (unique)
    prompt: Mapped[str]     # 토픽 프롬프트
    source: Mapped[str]     # 출처
```

### 2. Ingest Pydantic 스키마 (5개) ✅
**디렉토리**: `src/schemas/ingest/`

| 스키마 | 파일 | 검증 상태 |
|--------|------|-----------|
| SetIngest | set.py | ✅ 10개 레코드 파싱 성공 |
| ItemIngest | item.py | ✅ 생성 완료 |
| StimulusIngest | stimulus.py | ✅ 생성 완료 |
| AnswerKeyIngest | answer_key.py | ✅ 생성 완료 |
| IndependentTopicIngest | topic.py | ✅ 294개 레코드 파싱 성공 |

### 3. ID 매핑 레이어 ✅
**파일**: `src/services/ingest/id_mapper.py`

**기능**:
- uuid.uuid5() 기반 deterministic 매핑
- 5개 엔티티 타입별 네임스페이스 분리
- 동일 string ID → 동일 UUID 보장

**검증**:
```
String ID: ACTUAL_TEST_01
UUID 1: 4fccfa9b-40ee-57f6-8e94-18569daec687
UUID 2: 4fccfa9b-40ee-57f6-8e94-18569daec687
Deterministic: ✅
```

---

## 🚧 보류된 작업

### 4. Parser 구현 (설계 완료)
**파일**: `src/services/ingest/parser.py` (미생성)

**필요 기능**:
- `load_json_file()`: JSON 파일 로드
- `parse_to_schema()`: dict → Pydantic 변환
- `stream_json_file()`: 대용량 파일 스트리밍

**예상 소요 시간**: 1h

### 5. Mapper 구현 (설계 완료)
**파일**: `src/services/ingest/mapper.py` (미생성)

**필요 기능**:
- `to_set_model()`: SetIngest → Set
- `to_item_model()`: ItemIngest → Item
- `to_stimulus_model()`: StimulusIngest → Stimulus
- `to_answer_key_model()`: AnswerKeyIngest → AnswerKey
- `to_topic_model()`: IndependentTopicIngest → IndependentTopic

**예상 소요 시간**: 1.5h

### 6. Seeder 구현 (설계 완료)
**파일**: `src/services/ingest/seeder.py` (미생성)

**필요 기능**:
- `bulk_insert()`: Bulk Insert 수행
- `upsert_batch()`: INSERT or UPDATE

**예상 소요 시간**: 1h

### 7. CLI 구현 (설계 완료)
**파일**: `src/cli/seed.py` (미생성)

**필요 옵션**:
- `--file`: 단일 파일 시딩
- `--all`: 전체 시딩
- `--validate-only`: 검증만
- `--dry-run`: Dry-run
- `--upsert`: Upsert 지원
- `--batch-size`: 배치 크기
- `--verbose`: 상세 로그

**예상 소요 시간**: 1.5h

### 8. 테스트 작성 (설계 완료)
**디렉토리**: `tests/services/ingest/`, `tests/cli/`

**필요 테스트**:
- AC-ING-001 ~ AC-ING-019 (19개 시나리오)
- 단위 테스트 (Parser, Mapper, Seeder, IDMapper)
- 통합 테스트 (CLI)

**목표 커버리지**: 85%+
**예상 소요 시간**: 1.5h

---

## 📋 즉시 실행 필요 작업

### 우선순위 1: Alembic 마이그레이션 ⚠️
**작업**: IndependentTopic 테이블 생성

```bash
# 마이그레이션 생성
alembic revision --autogenerate -m "Add independent_topics table"

# 마이그레이션 적용
alembic upgrade head
```

**이유**: 모델은 생성되었으나 DB 테이블이 없음

### 우선순위 2: Python 버전 이슈 해결 ⚠️
**문제**: Python 3.9에서 `Type | None` 문법 미지원

**해결 방법 (택1)**:
1. Python 3.11+ 업그레이드 (권장)
2. 모든 모델 파일에 `from __future__ import annotations` 추가

### 우선순위 3: 나머지 서비스 구현
**순서**:
1. Parser (1h)
2. Mapper (1.5h)
3. Seeder (1h)
4. CLI (1.5h)
5. 테스트 (1.5h)

**총 예상 소요 시간**: 6.5h

---

## 📊 구현 진행률

### Milestone 체크리스트
- [x] Milestone 1: IndependentTopic 모델 (1h)
- [x] Milestone 2: Ingest 스키마 (1.5h)
- [x] Milestone 3: ID 매핑 레이어 (2h)
- [ ] Milestone 4: Parser (1h)
- [ ] Milestone 5: Mapper (1.5h)
- [ ] Milestone 6: Seeder (1h)
- [ ] Milestone 7: CLI (1.5h)
- [ ] Milestone 8: 테스트 (1.5h)
- [ ] Milestone 9: Integration (0.5h)

**완료**: 3 / 9 (33%)
**소요 시간**: 4.5h / 11.5h (39%)

### AC 시나리오 체크리스트
- [ ] AC-ING-001: sets.json 파싱 (스키마 완료, 테스트 미작성)
- [ ] AC-ING-002: items.json 파싱 (스키마 완료, 테스트 미작성)
- [ ] AC-ING-003: stimuli.json 파싱 (스키마 완료, 테스트 미작성)
- [ ] AC-ING-004: answer_keys.json 파싱 (스키마 완료, 테스트 미작성)
- [ ] AC-ING-005: independent_topics.json 파싱 (스키마 완료, 테스트 미작성)
- [ ] AC-ING-006: 잘못된 JSON 처리 (Parser 미구현)
- [ ] AC-ING-007: 스키마 검증 실패 (스키마 완료, 테스트 미작성)
- [ ] AC-ING-008: 단일 파일 시딩 (CLI 미구현)
- [ ] AC-ING-009: 파일 미존재 처리 (CLI 미구현)
- [ ] AC-ING-010: 전체 시딩 (CLI 미구현)
- [ ] AC-ING-011: 전체 시딩 롤백 (Seeder 미구현)
- [ ] AC-ING-012: 검증 전용 모드 (CLI 미구현)
- [ ] AC-ING-013: 검증 오류 감지 (스키마 완료, CLI 미구현)
- [ ] AC-ING-014: Dry-run 모드 (CLI 미구현)
- [ ] AC-ING-015: Upsert INSERT (Seeder 미구현)
- [ ] AC-ING-016: Upsert UPDATE (Seeder 미구현)
- [ ] AC-ING-017: 중복 PK 오류 (Seeder 미구현)
- [ ] AC-ING-018: 배치 크기 조절 (Seeder 미구현)
- [ ] AC-ING-019: 진행률 표시 (CLI 미구현)

**통과**: 0 / 19 (0%)

---

## 🎯 다음 실행 단계

### Step 1: 환경 준비
```bash
# Python 버전 확인
python --version  # 3.11+ 권장

# Alembic 마이그레이션
alembic revision --autogenerate -m "Add independent_topics table"
alembic upgrade head

# 의존성 확인
pip install click ijson tqdm sqlalchemy asyncpg pydantic
```

### Step 2: Parser 구현
```bash
# 파일 생성
touch src/services/ingest/parser.py

# ddd-implementation-report.md의 설계 참고하여 구현
```

### Step 3: Mapper 구현
```bash
# 파일 생성
touch src/services/ingest/mapper.py

# ddd-implementation-report.md의 설계 참고하여 구현
```

### Step 4: Seeder 구현
```bash
# 파일 생성
touch src/services/ingest/seeder.py

# ddd-implementation-report.md의 설계 참고하여 구현
```

### Step 5: CLI 구현
```bash
# 디렉토리 및 파일 생성
mkdir -p src/cli
touch src/cli/__init__.py
touch src/cli/seed.py

# ddd-implementation-report.md의 설계 참고하여 구현
```

### Step 6: 테스트 작성
```bash
# 테스트 디렉토리 생성
mkdir -p tests/services/ingest
mkdir -p tests/cli
mkdir -p tests/fixtures/ingest

# 테스트 파일 생성 및 작성
touch tests/services/ingest/test_id_mapper.py
touch tests/services/ingest/test_parser.py
touch tests/services/ingest/test_mapper.py
touch tests/services/ingest/test_seeder.py
touch tests/cli/test_seed.py

# 테스트 실행
pytest tests/services/ingest/ -v
pytest tests/cli/ -v

# 커버리지 확인
pytest --cov=src --cov-report=html
```

---

## 📚 참고 문서

- **분석 보고서**: `.moai/specs/SPEC-TOEFL-INGEST-001/ddd-analysis.md`
- **구현 보고서**: `.moai/specs/SPEC-TOEFL-INGEST-001/ddd-implementation-report.md`
- **SPEC 문서**: `.moai/specs/SPEC-TOEFL-INGEST-001/spec.md`
- **구현 계획**: `.moai/specs/SPEC-TOEFL-INGEST-001/plan.md`
- **수락 기준**: `.moai/specs/SPEC-TOEFL-INGEST-001/acceptance.md`

---

**작성자**: manager-ddd
**검토자**: 수연
**다음 검토**: 구현 완료 후
