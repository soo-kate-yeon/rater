# TOEFL Speaking Rater 구현 현황 및 인수인계 문서

**작성일**: 2026-01-25
**SPEC**: SPEC-TOEFL-001
**상태**: 85% 완료 (API 서버 정상, Worker 통합 필요)

---

## 📊 전체 진행 상황 요약

### ✅ 완료된 항목 (85%)

#### 1. 프로젝트 구조 및 환경 설정
- ✅ pyproject.toml 설정 완료
- ✅ 디렉토리 구조 생성 (src/api, src/models, src/services, src/workers)
- ✅ .env 파일 설정 (SQLite 로컬 개발 환경)
- ✅ Git 저장소 초기화 및 커밋 완료

#### 2. 데이터베이스 레이어
- ✅ SQLAlchemy 2.0 async 모델 구현
  - User, Task, Job, JobArtifact, Report 모델
  - UUID 기반 Primary Key
  - 관계 설정 (Foreign Key, Cascade)
- ✅ Alembic 마이그레이션 설정
  - async 지원 env.py 작성
  - 초기 마이그레이션 생성 및 적용
  - SQLite 데이터베이스 생성 완료 (`toefl_rater.db`)
- ✅ Database URL 유연성 (PostgreSQL/SQLite 모두 지원)

**파일 위치**:
- 모델: `src/models/*.py`
- 마이그레이션: `alembic/versions/5ac6e5d77682_*.py`
- 데이터베이스: `./toefl_rater.db`

#### 3. API 서버 (FastAPI)
- ✅ FastAPI 애플리케이션 구조
- ✅ CORS 미들웨어 설정
- ✅ 인증 라우터 (`/v1/auth`)
  - POST /v1/auth/register (회원가입)
  - POST /v1/auth/login (JWT 토큰 발급)
- ✅ Task 라우터 (`/v1/tasks`)
  - GET /v1/tasks (목록 조회)
  - POST /v1/tasks (생성)
  - GET /v1/tasks/{task_id} (조회)
- ✅ Job 라우터 (`/v1/jobs`)
  - POST /v1/jobs (생성)
  - GET /v1/jobs/{job_id} (상태 조회)
  - GET /v1/jobs/{job_id}/report (리포트 조회)
- ✅ Upload 라우터 (`/v1/uploads`)
  - POST /v1/uploads/audio (오디오 파일 업로드)

**테스트 결과**:
```
[1/6] Health Check ✅
[2/6] 사용자 등록 ✅ (201 Created)
[3/6] 로그인 ✅ (JWT 토큰 발급)
[4/6] Task 조회 ✅ (4개 Task 확인)
[5/6] Task 생성 ✅ (201 Created)
[6/6] Job 생성 ⚠️ (Worker 통합 필요)
```

**실행 명령**:
```bash
uv run uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
```

#### 4. 보안 및 인증
- ✅ bcrypt 비밀번호 해싱 (72바이트 제한 처리)
- ✅ JWT 토큰 생성 및 검증
- ✅ OAuth2 Bearer 인증 스키마

**주요 수정 사항**:
- `src/core/security.py`: passlib 대신 bcrypt 직접 사용
- TaskType Enum: 문자열 Enum으로 변경 (INDEPENDENT/INTEGRATED)
- UserResponse: UUID 타입으로 수정

#### 5. 서비스 레이어
- ✅ ASR Service (Whisper 통합) - `src/services/asr_service.py`
- ✅ Delivery Features Extractor - `src/services/delivery_features.py`
- ✅ Feedback Service (LLM 통합) - `src/services/feedback_service.py`
- ✅ Storage Service (로컬 파일) - `src/services/storage_service.py`
- ✅ Language Features - `src/services/language_features.py`
- ✅ Structure Features - `src/services/structure_features.py`

**참고**: 모든 서비스는 구현되었으나 Worker에서 아직 실제 연동하지 않음 (더미 데이터 반환 중)

#### 6. 비동기 처리 (Celery + Redis)
- ✅ Celery 애플리케이션 설정 (`src/core/celery.py`)
- ✅ Redis 설치 및 실행
- ✅ Celery Worker 등록 (`process_scoring_job` 태스크)
- ⚠️ Worker 내부 서비스 통합 미완료

**실행 명령**:
```bash
# Redis 서버
redis-server --daemonize yes

# Celery Worker
uv run celery -A src.core.celery:celery_app worker --loglevel=info --pool=solo
```

**등록된 태스크**:
```
src.workers.scoring_worker.process_scoring_job
```

#### 7. 테스트 코드
- ✅ 67개 테스트 케이스 작성
- ✅ 51% 코드 커버리지
- ✅ 시스템 통합 테스트 스크립트 (`test_system.py`)
- ✅ End-to-End 테스트 스크립트 (`test_end_to_end.py`)

**실행 명령**:
```bash
uv run pytest tests/ -v --cov=src --cov-report=term-missing
```

---

## ⚠️ 부분 완료 / 이슈 항목 (10%)

### 1. Circular Import 문제 ❗CRITICAL

**문제**:
```
src/core/celery.py → src/workers/scoring_worker.py (import)
src/workers/scoring_worker.py → src/core/celery.py (import)
```

**증상**:
- API 서버 재시작 시 ImportError 발생
- `cannot import name 'process_scoring_job' from partially initialized module`

**임시 조치**:
- `src/core/celery.py`에서 수동 import 제거
- autodiscover_tasks만 사용

**근본 해결 방안**:
1. **옵션 A**: Worker를 별도 파일로 분리
   - `src/workers/__init__.py`에서 celery_app import 제거
   - Worker 파일에서 lazy import 사용

2. **옵션 B**: Celery 앱을 독립적으로 분리
   - `celery_app.py`를 최상위로 이동
   - Worker와 API 서버에서 독립적으로 import

**우선순위**: HIGH

### 2. Worker 실제 서비스 통합 미완료

**현재 상태**:
Worker(`src/workers/scoring_worker.py`)가 더미 데이터를 반환합니다.

```python
# 현재 (더미 구현)
async def _run_asr(audio_path: str) -> dict:
    return {
        "transcript": "I prefer working in teams...",
        "segments": [...],
        "avg_logprob": -0.2
    }
```

**필요 작업**:
각 단계를 실제 서비스로 교체:

1. **_fetch_audio()** (lines 161-181)
   ```python
   # 교체 대상
   from src.services.storage_service import get_storage_service
   storage = get_storage_service()
   audio_path = await storage.get_audio_path(audio_key)
   ```

2. **_run_asr()** (lines 184-203)
   ```python
   # 교체 대상
   from src.services.asr_service import get_asr_service
   asr_service = get_asr_service()
   asr_result = await asr_service.transcribe(str(audio_path))
   ```

3. **_extract_features()** (lines 206-230)
   ```python
   # 교체 대상
   from src.services.delivery_features import get_delivery_feature_extractor
   extractor = get_delivery_feature_extractor()
   delivery_signals = extractor.extract(asr_result)
   ```

4. **_analyze_with_llm()** (lines 233-293)
   ```python
   # 교체 대상
   from src.services.feedback_service import generate_full_feedback
   feedback_report = await generate_full_feedback(
       task_type=job.task.task_type.value,
       prompt=job.task.prompt,
       transcript=transcript,
       delivery_features_dict=delivery_features.model_dump(),
       source_reading=job.task.source_reading,
       source_listening=job.task.source_listening,
   )
   ```

5. **JobArtifact 저장 추가**
   ```python
   # _save_report() 전에 추가
   artifact = JobArtifact(
       job_id=job.id,
       asr_json=asr_result.model_dump(),
       features_json=delivery_features.model_dump(),
       llm_json=feedback_report.model_dump(),
       rubric_version="v1.0",
       pipeline_version="v1.0"
   )
   db.add(artifact)
   await db.commit()
   ```

**우선순위**: HIGH

---

## ❌ 미완료 항목 (5%)

### 1. End-to-End 테스트 완료
- 테스트 스크립트 작성 완료
- API 서버 circular import 문제로 실행 불가
- Worker 서비스 통합 후 재테스트 필요

### 2. 테스트 커버리지 향상
- 현재: 51%
- 목표: 80%+
- 필요: API 엔드포인트 테스트 추가

### 3. 프로덕션 준비
- [ ] 환경 변수 검증
- [ ] 에러 핸들링 강화
- [ ] 로깅 개선
- [ ] 성능 모니터링 설정

---

## 🔧 알려진 이슈 및 해결 방법

### Issue #1: bcrypt 72바이트 제한
**문제**: `password cannot be longer than 72 bytes`
**해결**: `src/core/security.py`에서 bcrypt 직접 사용 및 바이트 truncation

### Issue #2: TaskType Enum 값 불일치
**문제**: `'INDEPENDENT' is not a valid TaskType`
**해결**: TaskType을 `str, enum.Enum`으로 변경, 값을 대문자로 통일

### Issue #3: SQLite에서 JSONB 타입 사용
**문제**: Alembic 마이그레이션에서 PostgreSQL JSONB 타입 참조
**해결**: 마이그레이션 파일에서 JSONB → Text로 수정

### Issue #4: torch CUDA 모듈 누락
**문제**: `ModuleNotFoundError: No module named 'torch.cuda._memory_viz'`
**해결**: `src/services/__init__.py`에서 lazy import로 변경 (heavy dependency 회피)

---

## 📁 주요 파일 및 디렉토리 구조

```
rater/
├── .env                              # 환경 변수 (SQLite 설정)
├── pyproject.toml                    # 프로젝트 의존성
├── alembic/
│   ├── env.py                        # Async SQLAlchemy 지원
│   └── versions/
│       └── 5ac6e5d77682_*.py         # 초기 마이그레이션
├── src/
│   ├── api/
│   │   ├── main.py                   # FastAPI 앱
│   │   └── routers/
│   │       ├── auth.py               # 인증 라우터
│   │       ├── tasks.py              # Task 라우터
│   │       ├── jobs.py               # Job 라우터
│   │       └── uploads.py            # Upload 라우터
│   ├── core/
│   │   ├── config.py                 # 설정 관리
│   │   ├── database.py               # DB 연결
│   │   ├── security.py               # 인증/보안
│   │   └── celery.py                 # Celery 앱 ⚠️ Circular import
│   ├── models/
│   │   ├── base.py                   # Base 모델
│   │   ├── user.py                   # User 모델
│   │   ├── task.py                   # Task 모델
│   │   ├── job.py                    # Job 모델
│   │   ├── job_artifact.py           # JobArtifact 모델
│   │   └── report.py                 # Report 모델
│   ├── schemas/
│   │   ├── auth.py                   # 인증 스키마
│   │   ├── tasks.py                  # Task 스키마
│   │   ├── jobs.py                   # Job 스키마
│   │   └── scoring.py                # 채점 스키마
│   ├── services/
│   │   ├── asr_service.py            # Whisper ASR
│   │   ├── delivery_features.py      # Delivery 특징 추출
│   │   ├── feedback_service.py       # LLM 피드백 생성
│   │   ├── storage_service.py        # 파일 스토리지
│   │   ├── language_features.py      # 언어 특징 추출
│   │   └── structure_features.py     # 구조 특징 추출
│   └── workers/
│       └── scoring_worker.py         # Celery Worker ⚠️ 서비스 통합 필요
├── tests/                            # 테스트 (67 test cases, 51% coverage)
├── test_system.py                    # 시스템 통합 테스트
├── test_end_to_end.py                # E2E 테스트
└── toefl_rater.db                    # SQLite 데이터베이스
```

---

## 🚀 다음 단계 작업 가이드

### Step 1: Circular Import 해결 (30분)

**방법 A - Worker 파일 분리 (권장)**:
```python
# src/workers/tasks.py (신규 파일)
from src.core.celery import celery_app
from src.workers.scoring_worker import ScoringTask, process_scoring_impl

@celery_app.task(base=ScoringTask, name="process_scoring_job")
def process_scoring_job(job_id: str, job_data: dict):
    return process_scoring_impl(job_id, job_data)
```

```python
# src/workers/scoring_worker.py (수정)
# celery_app import 제거
def process_scoring_impl(job_id: str, job_data: dict):
    # 기존 로직
    pass
```

**방법 B - Lazy Import**:
```python
# src/core/celery.py
# autodiscover만 사용, 수동 import 제거 (현재 상태 유지)
```

### Step 2: Worker 실제 서비스 통합 (1-2시간)

`src/workers/scoring_worker.py` 파일 수정:

1. **Import 추가** (파일 상단):
```python
from src.services.storage_service import get_storage_service
from src.services.asr_service import get_asr_service
from src.services.delivery_features import get_delivery_feature_extractor
from src.services.feedback_service import generate_full_feedback
from src.models.job_artifact import JobArtifact
```

2. **각 함수 교체** (상세 내용은 "Worker 실제 서비스 통합 미완료" 섹션 참조)

3. **JobArtifact 저장 추가** (_save_report 전):
```python
artifact = JobArtifact(
    job_id=job.id,
    asr_json=asr_result.model_dump(),
    features_json=delivery_features.model_dump(),
    llm_json=feedback_report.model_dump(),
    rubric_version="v1.0",
    pipeline_version="v1.0"
)
db.add(artifact)
await db.commit()
```

### Step 3: 전체 시스템 테스트 (30분)

1. **서비스 시작**:
```bash
# Terminal 1: Redis
redis-server --daemonize yes

# Terminal 2: API Server
uv run uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 3: Celery Worker
uv run celery -A src.core.celery:celery_app worker --loglevel=info --pool=solo
```

2. **테스트 실행**:
```bash
# 시스템 통합 테스트
uv run python test_system.py

# End-to-End 테스트 (전체 파이프라인)
uv run python test_end_to_end.py
```

3. **예상 결과**:
```
[1/7] 사용자 등록 ✅
[2/7] 로그인 ✅
[3/7] Task 생성 ✅
[4/7] 오디오 업로드 ✅
[5/7] Job 생성 ✅
[6/7] 채점 진행 ✅ (QUEUED → FETCHING_AUDIO → ASR_RUNNING → ... → DONE)
[7/7] 리포트 조회 ✅ (점수대, 피드백 확인)
```

### Step 4: 커버리지 향상 (선택사항, 1-2시간)

추가 테스트 작성:
- API 엔드포인트 예외 케이스
- Worker 실패 시나리오
- 동시성 테스트

---

## 📞 주요 의존성 및 환경

### Python 패키지 (pyproject.toml)
```toml
python = "^3.13"
fastapi = "^0.115.6"
uvicorn = "^0.34.0"
sqlalchemy = "^2.0.36"
alembic = "^1.14.0"
pydantic = "^2.10.5"
pydantic-settings = "^2.7.1"
celery = "^5.6.2"
redis = "^5.2.1"
openai-whisper = "^20240930"
openai = "^1.59.7"
anthropic = "^0.42.0"
bcrypt = "^4.2.1"
python-jose = "^3.3.0"
aiosqlite = "^0.21.0"
httpx = "^0.28.1"
```

### 시스템 요구사항
- Python 3.13+
- Redis 8.4.0+
- SQLite (또는 PostgreSQL)
- 최소 2GB RAM (Whisper 모델 로드 시)

### 환경 변수 (.env)
```bash
# Database
DATABASE_URL=sqlite+aiosqlite:///./toefl_rater.db

# Redis
REDIS_URL=redis://localhost:6379/0

# OpenAI
OPENAI_API_KEY=sk-proj-...

# Storage
STORAGE_PATH=./storage

# JWT
SECRET_KEY=your-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Whisper
WHISPER_MODEL=base
WHISPER_DEVICE=cpu
USE_LOCAL_WHISPER=true
```

---

## 🎯 성공 기준

### 최소 요구사항 (MVP)
- [x] 사용자 등록/로그인
- [x] Task CRUD
- [x] 오디오 파일 업로드
- [ ] Job 생성 및 비동기 채점 ← **현재 작업 중**
- [ ] 최종 리포트 조회

### 전체 요구사항
- [ ] 85%+ 테스트 커버리지
- [ ] End-to-End 테스트 통과
- [ ] 프로덕션 준비 (에러 핸들링, 로깅)

---

## 📝 참고 자료

### 관련 문서
- SPEC 문서: `.moai/specs/SPEC-TOEFL-001/spec.md`
- API 스키마: Swagger UI (http://localhost:8000/docs)
- 테스트 리포트: `pytest --cov-report=html`

### 주요 커밋
- `d385100` - 초기 프로젝트 설정 및 SPEC 추가
- 이후 모든 구현 작업 (63 files, 11,355 insertions)

---

## ⚡ Quick Start (컨텍스트 복구용)

```bash
# 1. 환경 확인
cat .env  # DATABASE_URL, REDIS_URL 확인

# 2. 데이터베이스 확인
ls -lh toefl_rater.db  # SQLite 파일 존재 확인

# 3. 서비스 시작
redis-server --daemonize yes
uv run uvicorn src.api.main:app --reload &
uv run celery -A src.core.celery:celery_app worker --pool=solo &

# 4. 테스트
uv run python test_system.py

# 5. 현재 이슈 확인
# - API 서버 circular import 문제 해결 필요
# - Worker 서비스 통합 필요 (src/workers/scoring_worker.py)
```

---

**마지막 업데이트**: 2026-01-25 12:30 KST
**작업자**: Claude (Sonnet 4.5)
**다음 작업자에게**: Circular import 해결 → Worker 서비스 통합 → E2E 테스트 순서로 진행 권장
