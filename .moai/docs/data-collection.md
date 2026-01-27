# 데이터 수집 파이프라인 가이드

## 개요

TOEFL Speaking 문제 데이터를 `external/` 디렉토리에서 PostgreSQL 데이터베이스로 수집하는 파이프라인입니다.

### 핵심 특징

- **데이터 무결성**: Pydantic v2 기반 스키마 검증으로 잘못된 데이터 유입 방지
- **효율적 수집**: Bulk Insert 및 Upsert로 대량 데이터 빠른 처리
- **유연한 CLI**: 파일별 또는 전체 시딩, 검증 전용 모드, Dry-run 지원
- **트랜잭션 안정성**: 오류 발생 시 전체 롤백으로 데이터 일관성 보장

---

## 데이터 파일 구조

### 입력 데이터 소스

| 파일명 | 설명 | 대상 테이블 | 예상 레코드 수 |
|--------|------|-------------|----------------|
| `external/sets.json` | 문제 세트 목록 | `sets` | ~40개 |
| `external/items.json` | 개별 문항 정보 (Q1-Q6) | `items` | ~240개 |
| `external/stimuli.json` | Reading/Listening 자극자료 | `stimuli` | ~300개 |
| `external/answer_keys.json` | 모범답안 및 Blueprint | `answer_keys` | ~500개 |
| `external/independent_topics.json` | Independent Speaking 토픽 | `independent_topics` | ~100개 |

### 시딩 순서

외래 키 의존성을 고려하여 다음 순서로 시딩이 진행됩니다:

1. **sets** → 문제 세트 정보
2. **items** → 개별 문항 (FK: `set_id`)
3. **stimuli** → 자극자료 (FK: `item_id`)
4. **answer_keys** → 모범답안 (FK: `item_id`)
5. **independent_topics** → 독립적인 토픽 뱅크

---

## CLI 사용법

### 기본 명령어

```bash
# 전체 데이터 시딩 (권장)
python -m src.cli.seed --all

# 단일 파일 시딩
python -m src.cli.seed --file external/sets.json

# 도움말 확인
python -m src.cli.seed --help
```

### 검증 및 테스트

```bash
# 스키마 검증만 수행 (DB에 쓰지 않음)
python -m src.cli.seed --validate-only

# Dry-run (변환 결과만 확인)
python -m src.cli.seed --dry-run

# 상세 로그 출력
python -m src.cli.seed --all --verbose
```

### 업데이트 및 성능 조정

```bash
# 기존 데이터 업데이트 (Upsert)
python -m src.cli.seed --file external/items.json --upsert

# 배치 크기 지정 (기본값: 100)
python -m src.cli.seed --all --batch-size 50

# 특정 파일 Upsert + 상세 로그
python -m src.cli.seed --file external/answer_keys.json --upsert --verbose
```

---

## 데이터 처리 플로우

### 1. JSON 파일 로드
- UTF-8 인코딩으로 파일 읽기
- 5MB 이상 파일은 스트리밍 파서(ijson) 사용

### 2. 스키마 검증
- Pydantic v2 모델로 데이터 타입 검증
- 필수 필드 누락 확인
- 데이터 형식 유효성 검사

### 3. SQLAlchemy 변환
- Pydantic 모델 → SQLAlchemy ORM 모델 변환
- FK 참조 무결성 사전 검증

### 4. Bulk Insert
- 배치 단위(기본 100개)로 데이터베이스 삽입
- Upsert 모드: 기존 레코드 UPDATE, 신규 레코드 INSERT

### 5. 트랜잭션 관리
- 각 파일은 단일 트랜잭션 내에서 처리
- 오류 발생 시 전체 롤백으로 데이터 일관성 보장

---

## JSON 스키마 예제

### sets.json

```json
[
  {
    "set_id": "TPO-01",
    "title": "TPO 1 Speaking Set",
    "source": "Official TPO",
    "version": "1.0",
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
  }
]
```

### items.json

```json
[
  {
    "item_id": "TPO-01-Q1",
    "set_id": "TPO-01",
    "task_no": 1,
    "task_type": "independent",
    "prompt": "Talk about a book you have read...",
    "prep_seconds": 15,
    "response_seconds": 45,
    "language": "en",
    "tags": ["personal_preference", "reading"],
    "difficulty": "medium",
    "scoring_focus": "general_description"
  }
]
```

### independent_topics.json

```json
[
  {
    "topic_id": "IND-001",
    "number": 1,
    "prompt": "Some people prefer to work independently. Others prefer to work in teams...",
    "source": "Official Guide"
  }
]
```

---

## 에러 처리

### 에러 코드 및 해결 방법

| 코드 | 설명 | 복구 방법 |
|------|------|----------|
| **E001** | 파일 미존재 | 파일 경로 확인 및 `external/` 디렉토리 확인 |
| **E002** | JSON 파싱 실패 | JSON 형식 검토 (쉼표, 중괄호 등) |
| **E003** | 스키마 검증 실패 | 오류 상세 확인 후 데이터 필드 수정 |
| **E004** | FK 무결성 위반 | 참조 테이블 먼저 시딩 (sets → items 순서) |
| **E005** | 중복 PK | `--upsert` 옵션 사용 또는 중복 데이터 제거 |
| **E006** | DB 연결 실패 | `.env` 파일의 데이터베이스 연결 설정 확인 |

### 로깅 및 디버깅

```bash
# 상세 로그 활성화
python -m src.cli.seed --all --verbose

# 로그 파일 확인
tail -f logs/seed.log
```

---

## 성능 최적화

### 권장 설정

| 상황 | 권장 배치 크기 | 예상 처리 시간 |
|------|---------------|----------------|
| 소규모 데이터 (<100개) | 기본값 (100) | ~5초 |
| 중규모 데이터 (100-1000개) | 100-200 | ~30초 |
| 대규모 데이터 (>1000개) | 50-100 | ~2분 |

### 메모리 최적화

- 5MB 이상 파일은 자동으로 스트리밍 모드 사용
- 배치 크기를 줄여 메모리 사용량 조절
- `--batch-size 50` 권장 (메모리 제한 환경)

---

## 트러블슈팅

### Q1. "FK 무결성 위반" 오류가 발생합니다

**A:** 시딩 순서가 잘못되었을 수 있습니다. `--all` 옵션을 사용하여 자동 순서로 시딩하세요.

```bash
python -m src.cli.seed --all
```

### Q2. 일부 레코드만 업데이트하고 싶습니다

**A:** `--upsert` 옵션을 사용하여 기존 레코드를 업데이트하세요.

```bash
python -m src.cli.seed --file external/items.json --upsert
```

### Q3. 시딩 전에 데이터를 검증하고 싶습니다

**A:** `--validate-only` 또는 `--dry-run` 옵션을 사용하세요.

```bash
# 스키마 검증만
python -m src.cli.seed --validate-only

# 변환 결과 미리보기
python -m src.cli.seed --dry-run
```

---

## 참고 자료

- **SPEC 문서**: [SPEC-TOEFL-INGEST-001](../.moai/specs/SPEC-TOEFL-INGEST-001/spec.md)
- **데이터베이스 스키마**: [database-schema.md](./database-schema.md)
- **API 엔드포인트**: [api-endpoints.md](./api-endpoints.md)
- **Pydantic v2 문서**: https://docs.pydantic.dev/latest/
- **SQLAlchemy 2.0 문서**: https://docs.sqlalchemy.org/en/20/

---

**작성일**: 2026-01-27
**버전**: 1.0.0
**관련 SPEC**: SPEC-TOEFL-INGEST-001
