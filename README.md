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
│   └── core/             # 핵심 설정
├── tests/                # 테스트
├── alembic/              # DB 마이그레이션
└── storage/              # 로컬 파일 저장소
```

## 라이선스

MIT License
