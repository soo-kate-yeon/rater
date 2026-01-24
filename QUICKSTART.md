# Job API 통합 - 빠른 시작 가이드

## ✅ 구현 완료 사항

### 1. Celery 앱 설정
- **파일**: `src/core/celery.py`
- **기능**: Redis 브로커, 재시도 정책, 작업 라우팅

### 2. 채점 Worker
- **파일**: `src/workers/scoring_worker.py`
- **기능**: 6단계 채점 파이프라인 (QUEUED → DONE)

### 3. Job API 엔드포인트
- **파일**: `src/api/routers/jobs.py`
- **구현된 엔드포인트**:
  - ✅ `POST /v1/jobs` - audio_key 검증 + Celery 작업 전송
  - ✅ `GET /v1/jobs/{job_id}` - Job 상태 조회
  - ✅ `GET /v1/jobs/{job_id}/report` - Report 조회

## 🚀 실행 순서

```bash
# 1. Redis 시작
docker run -d --name redis -p 6379:6379 redis:7

# 2. Celery Worker 시작
celery -A src.core.celery:celery_app worker --loglevel=info --queues=scoring

# 3. FastAPI 서버 시작
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# 4. API 테스트
curl -X POST "http://localhost:8000/v1/jobs" \
  -H "Content-Type: application/json" \
  -d '{
    "audio_key": "audio/test.mp3",
    "task_id": 1,
    "task_type": "independent",
    "prompt": "Test prompt"
  }'
```

## 📋 향후 작업 (TODO)

1. **ASR 통합**: `_run_asr()` - Whisper API/로컬 모델
2. **Feature 추출**: `_extract_features()` - WPM, 침묵 비율 등
3. **LLM 통합**: `_analyze_with_llm()` - GPT-4/Claude
4. **JWT 인증**: `user_id` 추출 로직
5. **스키마 수정**: `task_id` 타입 통일 (int → UUID)
6. **S3 통합**: `_fetch_audio()` - AWS S3 다운로드

## 📖 상세 문서

전체 구현 내용은 `IMPLEMENTATION_NOTES.md` 참조
