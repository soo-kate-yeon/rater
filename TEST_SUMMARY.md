# TOEFL Speaking Rater 테스트 요약

## 📊 테스트 통계

- **총 테스트 파일**: 8개
- **총 테스트 케이스**: 67개
- **총 코드 라인**: ~1,919줄
- **초기 커버리지**: 51%

## ✅ 생성된 테스트 파일

### 1. API 테스트 (test_api/)

#### test_auth.py (9개 테스트)
- ✅ 회원가입 성공
- ✅ 중복 이메일 회원가입 실패
- ✅ 잘못된 이메일 형식 검증
- ✅ 로그인 성공
- ✅ 잘못된 비밀번호 로그인 실패
- ✅ 존재하지 않는 사용자 로그인 실패
- ✅ 필수 필드 누락 검증 (회원가입)
- ✅ 필수 필드 누락 검증 (로그인)

#### test_uploads.py (9개 테스트)
- ✅ 오디오 파일 업로드 성공 (MP3)
- ✅ WAV 형식 파일 업로드
- ✅ M4A 형식 파일 업로드
- ✅ 지원하지 않는 파일 형식 업로드 실패
- ✅ 파일명 없는 파일 업로드 실패
- ✅ 최대 크기 초과 파일 업로드 실패
- ✅ 파일 없이 업로드 요청 실패
- ✅ 업로드 응답 포맷 검증

#### test_jobs.py (10개 테스트)
- ✅ Job 생성 성공
- ✅ 존재하지 않는 audio_key로 Job 생성 실패
- ✅ 필수 필드 누락 시 Job 생성 실패
- ✅ Job 상태 조회 성공
- ✅ 존재하지 않는 Job 조회 실패
- ✅ 잘못된 UUID 형식 조회 실패
- ✅ Job 리포트 조회 성공
- ✅ 완료되지 않은 Job 리포트 조회 실패
- ✅ 존재하지 않는 Job 리포트 조회 실패
- ✅ Job 상태 진행 테스트

### 2. 서비스 테스트 (test_services/)

#### test_storage_service.py (7개 테스트 - 기존)
- ✅ 오디오 파일 저장
- ✅ 파일 경로 조회
- ✅ 파일 삭제
- ✅ 잘못된 파일 확장자 검증
- ✅ 임시 파일 저장
- ✅ 임시 파일 정리

#### test_asr_service.py (9개 테스트)
- ✅ 음성 인식 성공 (Whisper 모킹)
- ✅ 존재하지 않는 파일 처리
- ✅ Whisper 실행 중 오류 처리
- ✅ 빈 세그먼트 처리
- ✅ ASR 결과 Pydantic 검증
- ✅ 모델 언로드
- ✅ 높은 무음 확률 오디오 처리
- ✅ Lazy loading 동작 확인

#### test_feedback_service.py (8개 테스트)
- ✅ 독립형 문제 피드백 생성
- ✅ 통합형 문제 피드백 생성
- ✅ Language features 추출 확인
- ✅ Structure features 추출 확인
- ✅ 피드백 서비스 설정
- ✅ 피드백 생성 중 오류 처리
- ✅ DeliveryFeatures 검증
- ✅ Features 요약 메서드 테스트

### 3. 모델 테스트 (test_models/)

#### test_job_model.py (11개 테스트)
- ✅ Job 생성
- ✅ JobStatus Enum 값 확인
- ✅ Job 상태 전이 (QUEUED → DONE)
- ✅ Job 실패 상태 처리
- ✅ Job 관계 확인 (user, task)
- ✅ User 삭제 시 캐스케이드 삭제
- ✅ Job progress 범위 검증
- ✅ Job __repr__ 메서드
- ✅ 한 사용자의 여러 Job
- ✅ Job 타임스탬프

#### test_report_model.py (10개 테스트)
- ✅ Report 생성
- ✅ Score band 범위 테스트
- ✅ Report JSON 구조 검증
- ✅ Report-Job 관계
- ✅ Job 삭제 시 캐스케이드 삭제
- ✅ 일대일 관계 제약
- ✅ Report __repr__ 메서드
- ✅ 빈 JSON 처리
- ✅ created_at 타임스탬프

## 📁 테스트 구조

```
tests/
├── conftest.py                      # 공통 픽스처 (test_db, test_client, mock_asr_result 등)
├── README.md                        # 테스트 가이드 문서
│
├── api/                             # API 엔드포인트 테스트
│   ├── __init__.py
│   ├── test_auth.py                # 9개 테스트
│   ├── test_uploads.py             # 9개 테스트
│   └── test_jobs.py                # 10개 테스트
│
├── services/                        # 서비스 레이어 테스트
│   ├── __init__.py
│   ├── test_storage_service.py     # 7개 테스트
│   ├── test_asr_service.py         # 9개 테스트 (모킹)
│   └── test_feedback_service.py    # 8개 테스트 (모킹)
│
└── models/                          # 모델 테스트
    ├── __init__.py
    ├── test_job_model.py           # 11개 테스트
    └── test_report_model.py        # 10개 테스트
```

## 🎯 커버리지 현황

### 전체 커버리지: 51%

#### 높은 커버리지 (80% 이상)
- ✅ `src/models/` - 90-100% (모델 정의)
- ✅ `src/schemas/` - 100% (Pydantic 스키마)
- ✅ `src/core/config.py` - 100% (설정)

#### 중간 커버리지 (40-80%)
- 🟨 `src/api/routers/` - 60-80% (API 라우터)
- 🟨 `src/core/security.py` - 42% (보안 함수)
- 🟨 `src/services/feedback_service.py` - 51%

#### 낮은 커버리지 (40% 미만)
- 🟥 `src/services/asr_service.py` - 27% (Whisper 통합 - 모킹 필요)
- 🟥 `src/services/storage_service.py` - 21% (파일 저장 로직)
- 🟥 `src/services/llm_service.py` - 35% (LLM API 통합 - 모킹 필요)
- 🟥 `src/workers/scoring_worker.py` - 26% (Celery 워커 - 통합 테스트 필요)

## 🔧 주요 픽스처

### 데이터베이스 픽스처
- `test_engine`: SQLite in-memory 엔진
- `test_db`: 테스트용 데이터베이스 세션
- `test_user`: 테스트용 사용자 (test@example.com)
- `test_task`: 테스트용 태스크

### API 테스트 픽스처
- `test_client`: FastAPI AsyncClient (httpx)

### 모킹 픽스처
- `mock_asr_result`: 모킹된 Whisper ASR 결과
- `mock_asr_result_model`: ASRResult Pydantic 모델
- `mock_feedback_report`: 모킹된 피드백 리포트

### 유틸리티 픽스처
- `sample_audio_file`: 샘플 오디오 파일 바이트
- `cleanup_storage`: 스토리지 정리

## 🚀 테스트 실행 방법

### 1. 전체 테스트 실행

```bash
pytest tests/
```

### 2. 커버리지 리포트

```bash
# 터미널 출력
pytest tests/ --cov=src --cov-report=term-missing

# HTML 리포트 (브라우저에서 확인)
pytest tests/ --cov=src --cov-report=html
open htmlcov/index.html
```

### 3. 특정 디렉토리/파일만 테스트

```bash
pytest tests/api/                    # API 테스트만
pytest tests/services/               # 서비스 테스트만
pytest tests/models/                 # 모델 테스트만
pytest tests/api/test_auth.py       # 특정 파일만
```

### 4. 상세 출력

```bash
pytest tests/ -v                     # verbose
pytest tests/ -vv                    # more verbose
pytest tests/ -s                     # print 출력 표시
pytest tests/ -k "auth"              # 이름에 auth가 포함된 테스트만
```

## 🎭 모킹 전략

### Whisper ASR 모킹
실제 Whisper 모델을 로딩하지 않고 테스트:

```python
with patch.object(asr_service, '_load_model', return_value=mock_model):
    result = await asr_service.transcribe(audio_file)
```

### LLM API 모킹
실제 OpenAI/Anthropic API 호출 없이 테스트:

```python
with patch.object(llm_service, 'generate_feedback') as mock_generate:
    mock_generate.return_value = mock_feedback_report
    result = await feedback_service.generate_feedback(...)
```

### Celery 태스크 모킹
```python
with patch('src.api.routers.jobs.process_scoring_job.delay') as mock_celery:
    response = await test_client.post("/api/v1/jobs", json=data)
    assert mock_celery.called
```

## 📈 다음 단계

### 1. 커버리지 향상 (60% → 80%)
- [ ] `src/services/storage_service.py` 테스트 강화
- [ ] `src/services/llm_service.py` 모킹 테스트 추가
- [ ] `src/workers/scoring_worker.py` 통합 테스트

### 2. 통합 테스트 추가
- [ ] 전체 워크플로우 테스트 (업로드 → Job 생성 → 처리 → 리포트)
- [ ] 에러 시나리오 테스트 (ASR 실패, LLM API 실패 등)

### 3. 성능 테스트
- [ ] 대량 파일 업로드 테스트
- [ ] 동시 요청 처리 테스트

### 4. 보안 테스트
- [ ] JWT 토큰 검증 테스트
- [ ] 파일 업로드 보안 테스트 (경로 탐색 공격 등)
- [ ] API 속도 제한 테스트

## 💡 참고 사항

### SQLite vs PostgreSQL
- 테스트는 SQLite in-memory 사용
- PostgreSQL 특정 기능 (JSONB 쿼리 등)은 단위 테스트로 검증
- 실제 운영 환경과 차이가 있을 수 있음

### 비동기 테스트
- `pytest-asyncio` 사용
- `asyncio_mode = "auto"` 설정으로 자동 처리

### 픽스처 스코프
- 대부분 `function` 스코프 (각 테스트마다 독립적)
- 필요 시 `session` 스코프로 최적화 가능

## 📝 테스트 작성 가이드

자세한 테스트 작성 가이드는 `tests/README.md` 참조

---

**생성일**: 2026-01-25
**테스트 프레임워크**: pytest 9.0.2, pytest-asyncio 1.3.0
**초기 커버리지**: 51% (67개 테스트)
**목표 커버리지**: 80%+
