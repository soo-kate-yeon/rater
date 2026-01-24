# TOEFL Speaking Rater 테스트 가이드

## 테스트 구조

```
tests/
├── conftest.py              # 공통 픽스처 및 설정
├── api/                     # API 엔드포인트 테스트
│   ├── test_auth.py        # 회원가입, 로그인
│   ├── test_uploads.py     # 파일 업로드
│   └── test_jobs.py        # Job 생성, 조회, 리포트
├── services/                # 서비스 레이어 테스트
│   ├── test_storage_service.py   # 스토리지 서비스
│   ├── test_asr_service.py       # Whisper ASR (모킹)
│   └── test_feedback_service.py  # 피드백 생성 (모킹)
└── models/                  # 모델 테스트
    ├── test_job_model.py    # Job 모델, 상태 전이
    └── test_report_model.py # Report 모델
```

## 테스트 실행

### 전체 테스트 실행

```bash
pytest tests/
```

### 특정 디렉토리 테스트

```bash
pytest tests/api/           # API 테스트만
pytest tests/services/      # 서비스 테스트만
pytest tests/models/        # 모델 테스트만
```

### 특정 파일 테스트

```bash
pytest tests/api/test_auth.py
pytest tests/services/test_asr_service.py
```

### 커버리지 리포트

```bash
# 터미널에 커버리지 출력
pytest tests/ --cov=src --cov-report=term-missing

# HTML 리포트 생성
pytest tests/ --cov=src --cov-report=html
open htmlcov/index.html
```

### 상세 출력 모드

```bash
pytest tests/ -v           # verbose
pytest tests/ -vv          # more verbose
pytest tests/ -s           # print 출력 표시
```

## 주요 픽스처

### 데이터베이스 픽스처

- `test_engine`: SQLite in-memory 엔진
- `test_db`: 테스트용 데이터베이스 세션
- `test_user`: 테스트용 사용자 (`test@example.com`)
- `test_task`: 테스트용 태스크

### API 테스트 픽스처

- `test_client`: FastAPI 테스트 클라이언트 (httpx.AsyncClient)

### 모킹 픽스처

- `mock_asr_result`: 모킹된 Whisper ASR 결과
- `sample_audio_file`: 샘플 오디오 파일 바이트

### 스토리지 픽스처

- `cleanup_storage`: 테스트 전후 스토리지 정리

## 테스트 커버리지 목표

- **최소 목표**: 60% 전체 커버리지
- **API 엔드포인트**: 100% 커버
- **핵심 서비스**: 80% 커버

### 현재 커버리지

```bash
# 커버리지 확인
pytest tests/ --cov=src --cov-report=term-missing
```

## 테스트 작성 가이드

### API 테스트

```python
@pytest.mark.asyncio
async def test_endpoint_success(test_client: AsyncClient):
    response = await test_client.post(
        "/api/v1/endpoint",
        json={"key": "value"}
    )

    assert response.status_code == 200
    data = response.json()
    assert "expected_field" in data
```

### 서비스 테스트 (모킹)

```python
@pytest.mark.asyncio
async def test_service_method(service_fixture):
    with patch('module.dependency') as mock_dep:
        mock_dep.return_value = expected_value

        result = await service_fixture.method()

        assert result == expected_value
        assert mock_dep.called
```

### 모델 테스트

```python
@pytest.mark.asyncio
async def test_model_creation(test_db: AsyncSession):
    model = ModelClass(field1="value1", field2="value2")
    test_db.add(model)
    await test_db.commit()
    await test_db.refresh(model)

    assert model.id is not None
    assert model.field1 == "value1"
```

## 모킹 전략

### Whisper ASR 모킹

실제 Whisper 모델을 로딩하지 않고 모킹된 결과 사용:

```python
with patch.object(asr_service, '_load_model', return_value=mock_model):
    result = await asr_service.transcribe(audio_file)
```

### LLM API 모킹

실제 OpenAI/Anthropic API를 호출하지 않고 모킹:

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

## CI/CD 통합

### GitHub Actions

```yaml
- name: Run tests
  run: |
    pytest tests/ --cov=src --cov-report=xml

- name: Upload coverage
  uses: codecov/codecov-action@v3
```

## 트러블슈팅

### 테스트 데이터베이스 이슈

SQLite in-memory 사용으로 PostgreSQL 특정 기능 테스트 불가:
- JSONB 쿼리
- 고급 인덱싱

해결: 실제 PostgreSQL 테스트 DB 사용 또는 기능 단위 테스트로 검증

### 비동기 테스트 오류

`pytest-asyncio` 설정 확인:

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
```

### 픽스처 스코프 이슈

- `function`: 각 테스트마다 새로운 인스턴스
- `session`: 전체 세션에서 하나의 인스턴스

## 다음 단계

### 추가 테스트 작성

1. **Integration Tests**: 전체 워크플로우 테스트
2. **Performance Tests**: 대량 데이터 처리 테스트
3. **Security Tests**: 인증/인가, 입력 검증 테스트

### E2E 테스트

Playwright를 사용한 브라우저 테스트 추가 고려

### Load Testing

k6 또는 Locust를 사용한 부하 테스트 추가
