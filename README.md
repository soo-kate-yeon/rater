# TOEFL Speaking Rater

TOEFL Speaking Response 자동 채점 및 피드백 시스템

## 프로젝트 개요

이 프로젝트는 TOEFL Speaking 시험 준비를 위한 AI 기반 자동 채점 시스템입니다.

### 핵심 기능

- **자동 채점**: Whisper ASR + LLM 기반 구조적 분석
- **구체적 피드백**: 답변 구조, 언어 사용, 전달력 분석
- **약점 분석**: 가장 큰 감점 요인 집중 제시
- **점수 범위 제공**: 신뢰 구간을 포함한 점수 범위 (예: 22-25점)

## 기술 스택

- **FastAPI 0.115+**: 비동기 웹 프레임워크
- **PostgreSQL 15+**: 관계형 데이터베이스
- **SQLAlchemy 2.0**: 비동기 ORM
- **Celery + Redis**: 비동기 작업 큐
- **Whisper**: 음성 인식 (ASR)
- **GPT-4 / Claude**: LLM 분석

## 설치 방법

### 1. 의존성 설치

```bash
# Poetry 사용 (권장)
poetry install

# pip 사용
pip install -e ".[dev]"
```

### 2. 환경 변수 설정

```bash
cp .env.example .env
# .env 파일을 편집하여 API 키 및 데이터베이스 정보 입력
```

### 3. 데이터베이스 마이그레이션

```bash
alembic upgrade head
```

## 실행 방법

### API 서버

```bash
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

### Celery Worker

```bash
celery -A src.workers.celery_app worker --loglevel=info
```

## API 문서

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 프로젝트 구조

```
rater/
├── src/
│   ├── api/              # FastAPI 라우터
│   ├── models/           # SQLAlchemy 모델
│   ├── services/         # 비즈니스 로직
│   ├── workers/          # Celery Workers
│   ├── schemas/          # Pydantic 스키마
│   ├── cli/              # CLI 명령어 (데이터 수집)
│   └── core/             # 핵심 설정
├── tests/                # 테스트
├── alembic/              # DB 마이그레이션
├── external/             # 외부 데이터 파일 (JSON)
└── storage/              # 로컬 파일 저장소
```

## 데이터 수집

TOEFL Speaking 문제 데이터를 PostgreSQL 데이터베이스로 수집하는 파이프라인을 제공합니다.

### 지원하는 데이터 파일

`external/` 디렉토리에 다음 JSON 파일들을 배치합니다:

- **sets.json**: 문제 세트 목록 (테스트 세트 정보)
- **items.json**: 개별 문항 정보 (Q1-Q6 문제)
- **stimuli.json**: Reading/Listening 자극자료
- **answer_keys.json**: 모범답안 및 Blueprint
- **independent_topics.json**: Independent Speaking 토픽 뱅크

### CLI 사용법

```bash
# 전체 데이터 시딩 (순차적으로 모든 파일 처리)
python -m src.cli.seed --all

# 단일 파일 시딩
python -m src.cli.seed --file external/sets.json

# 검증만 수행 (DB에 쓰지 않음)
python -m src.cli.seed --validate-only

# Dry-run (변환 확인만)
python -m src.cli.seed --dry-run

# 기존 데이터 업데이트 (Upsert)
python -m src.cli.seed --file external/items.json --upsert

# 배치 크기 지정
python -m src.cli.seed --all --batch-size 50 --verbose
```

### IndependentTopic 모델

Independent Speaking 문제의 토픽 뱅크를 관리하는 모델입니다:

- **topic_id**: 고유 식별자
- **number**: 토픽 번호 (1-100)
- **prompt**: 문제 프롬프트
- **source**: 출처 (예: TPO, Official Guide)

### 데이터 처리 플로우

1. **JSON 파일 로드**: UTF-8 인코딩으로 파일 읽기
2. **스키마 검증**: Pydantic v2 모델로 데이터 검증
3. **SQLAlchemy 변환**: ORM 모델로 변환
4. **Bulk Insert**: 배치 단위로 데이터베이스 삽입
5. **트랜잭션 관리**: 오류 발생 시 전체 롤백

상세한 내용은 [SPEC-TOEFL-INGEST-001](.moai/specs/SPEC-TOEFL-INGEST-001/spec.md)을 참조하세요.

## 라이선스

MIT License
