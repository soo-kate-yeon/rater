# SPEC-TOEFL-001 수락 기준 (Acceptance Criteria)

## 📌 TAG BLOCK

```
SPEC-ID: SPEC-TOEFL-001
제목: TOEFL Speaking Training 수락 기준
생성일: 2026-01-24
상태: Planned
우선순위: High
```

---

## 🎯 수락 기준 개요

이 문서는 SPEC-TOEFL-001의 각 기능이 완료되었다고 간주되기 위한 구체적인 검증 기준을 정의합니다. 모든 시나리오는 Given-When-Then 형식으로 작성되며, 자동화된 테스트 또는 수동 테스트를 통해 검증됩니다.

---

## 📋 테스트 시나리오 (Given-When-Then Format)

### 시나리오 1: 사용자 회원가입 및 로그인

#### AC-001: 신규 사용자 회원가입 성공
**Given**: 사용자가 앱을 처음 실행하고 회원가입 화면에 접근한 상태
**When**: 사용자가 다음 정보를 입력하고 "회원가입" 버튼을 누른다:
  - 이메일: `test@example.com`
  - 비밀번호: `SecurePass123!`
  - 이름: `홍길동`
**Then**:
  - 백엔드 `/api/auth/register` 엔드포인트가 호출된다
  - `users` 테이블에 새로운 레코드가 생성된다 (비밀번호는 해시 처리됨)
  - 사용자에게 "회원가입 성공" 메시지가 표시된다
  - 자동으로 로그인 화면으로 이동한다

**검증 방법**:
```python
# pytest 테스트 예시
async def test_user_registration_success(async_client):
    response = await async_client.post("/api/auth/register", json={
        "email": "test@example.com",
        "password": "SecurePass123!",
        "name": "홍길동"
    })
    assert response.status_code == 201
    assert "user_id" in response.json()
```

---

#### AC-002: 중복 이메일 회원가입 실패
**Given**: 데이터베이스에 `test@example.com` 이메일을 가진 사용자가 이미 존재하는 상태
**When**: 다른 사용자가 동일한 이메일로 회원가입을 시도한다
**Then**:
  - 백엔드가 `400 Bad Request` 응답을 반환한다
  - 에러 메시지: `"이미 등록된 이메일입니다"`
  - 사용자는 회원가입 화면에 남아있으며, 에러 메시지를 확인할 수 있다

**검증 방법**:
```python
async def test_user_registration_duplicate_email(async_client, existing_user):
    response = await async_client.post("/api/auth/register", json={
        "email": existing_user.email,
        "password": "AnotherPass123!",
        "name": "김철수"
    })
    assert response.status_code == 400
    assert "이미 등록된 이메일" in response.json()["detail"]
```

---

#### AC-003: 로그인 성공 및 JWT 토큰 발급
**Given**: 사용자가 회원가입을 완료한 상태
**When**: 사용자가 올바른 이메일과 비밀번호로 로그인을 시도한다
**Then**:
  - 백엔드가 `200 OK` 응답과 함께 JWT 토큰을 반환한다
  - 앱이 토큰을 AsyncStorage에 저장한다
  - 사용자가 자동으로 Exam 페이지(홈 화면)로 이동한다

**검증 방법**:
```python
async def test_user_login_success(async_client, existing_user):
    response = await async_client.post("/api/auth/login", json={
        "email": existing_user.email,
        "password": "correct_password"
    })
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert "token_type" in response.json()
    assert response.json()["token_type"] == "bearer"
```

---

### 시나리오 2: 모의고사 목록 조회 및 시작

#### AC-004: Exam 페이지에서 모의고사 목록 표시
**Given**: 사용자가 로그인한 상태에서 Exam 페이지에 접근한다
**When**: 앱이 `GET /api/exams` 엔드포인트를 호출한다
**Then**:
  - 백엔드가 모의고사 목록을 반환한다 (예: Seoul Test, Milan Test, Tokyo Test)
  - 각 모의고사는 다음 정보를 포함한다:
    - `exam_id`: 고유 ID
    - `name`: 모의고사 이름
    - `description`: 간단한 설명
  - 앱이 목록을 카드 형태로 표시한다

**검증 방법**:
```python
async def test_get_exam_list(async_client, auth_headers):
    response = await async_client.get("/api/exams", headers=auth_headers)
    assert response.status_code == 200
    exams = response.json()
    assert len(exams) > 0
    assert all("exam_id" in exam for exam in exams)
    assert any(exam["name"] == "Seoul Test" for exam in exams)
```

---

#### AC-005: 모의고사 선택 시 문제 로드
**Given**: 사용자가 Exam 페이지에서 "Seoul Test"를 선택한다
**When**: 앱이 `GET /api/exams/{exam_id}` 엔드포인트를 호출한다
**Then**:
  - 백엔드가 해당 모의고사의 Q1-Q4 문제를 반환한다
  - 각 문제는 다음 정보를 포함한다:
    - `question_id`: 문제 ID
    - `question_type`: "Q1", "Q2", "Q3", "Q4"
    - `prompt`: 문제 내용
    - `preparation_time`: 준비 시간 (초)
    - `response_time`: 응답 시간 (초)
  - 앱이 첫 번째 문제(Q1)를 표시한다

**검증 방법**:
```python
async def test_get_exam_questions(async_client, auth_headers, seoul_exam):
    response = await async_client.get(
        f"/api/exams/{seoul_exam.id}",
        headers=auth_headers
    )
    assert response.status_code == 200
    questions = response.json()["questions"]
    assert len(questions) == 4
    assert questions[0]["question_type"] == "Q1"
    assert "prompt" in questions[0]
```

---

### 시나리오 3: 녹음 기능

#### AC-006: Practice 페이지에서 녹음 시작
**Given**: 사용자가 Practice 페이지의 "Practice" 탭에 접근한 상태
**When**: 사용자가 "Record" 버튼을 누른다
**Then**:
  - 앱이 마이크 권한을 요청한다 (최초 1회)
  - 권한이 허용되면 녹음이 즉시 시작된다
  - 버튼이 "Stop"으로 변경되고, 빨간색으로 표시된다
  - 타이머가 0초부터 시작하여 60초까지 카운트된다
  - 시각적 피드백(예: 파형 애니메이션)이 표시된다

**검증 방법**: 수동 테스트 (React Native 녹음 기능은 실기기에서만 작동)
- [ ] iOS 실기기에서 녹음 시작 확인
- [ ] Android 실기기에서 녹음 시작 확인
- [ ] 타이머가 정확히 작동하는지 확인
- [ ] 60초 후 자동 종료 확인

---

#### AC-007: 녹음 종료 및 로컬 저장
**Given**: 사용자가 녹음을 시작한 상태 (예: 45초 경과)
**When**: 사용자가 "Stop" 버튼을 누른다
**Then**:
  - 녹음이 즉시 종료된다
  - 녹음 파일이 앱의 캐시 디렉토리에 저장된다 (형식: MP3 또는 M4A)
  - 파일 크기가 10MB 이하인지 확인한다
  - "Submit" 버튼이 활성화된다
  - 파일 정보(길이, 크기)가 화면에 표시된다

**검증 방법**: 수동 테스트
- [ ] 녹음 파일이 로컬에 저장되는지 확인
- [ ] 파일 형식과 크기가 요구사항을 충족하는지 확인
- [ ] "Submit" 버튼 활성화 확인

---

#### AC-008: Presigned URL 발급 및 S3 직접 업로드 성공
**Given**: 사용자가 녹음을 완료하고 "Submit" 버튼을 누른다
**When**: 앱이 `POST /v1/uploads/presign` 엔드포인트를 호출한다
**Then**:
  - 백엔드가 파일 메타데이터를 검증한다 (content_type, size_bytes)
  - S3 presigned URL을 생성한다 (유효 기간: 15분)
  - `200 OK` 응답과 함께 `upload_url`, `audio_key`, `expires_at`을 반환한다
  - 앱이 presigned URL로 S3에 직접 업로드한다
  - 업로드 성공 시, 앱이 `audio_key`를 저장하고 Job 생성 단계로 진행한다

**검증 방법**:
```python
async def test_presigned_url_generation(async_client, auth_headers):
    response = await async_client.post(
        "/v1/uploads/presign",
        headers=auth_headers,
        json={"content_type": "audio/mpeg", "size_bytes": 1024000}
    )
    assert response.status_code == 200
    data = response.json()
    assert "upload_url" in data
    assert "audio_key" in data
    assert "expires_at" in data
    assert data["upload_url"].startswith("https://")
```

---

#### AC-009: 파일 크기 초과 시 presigned URL 발급 실패
**Given**: 사용자가 10MB를 초과하는 오디오 파일을 업로드하려고 시도한다
**When**: 앱이 `POST /v1/uploads/presign` 엔드포인트를 호출한다 (size_bytes: 15000000)
**Then**:
  - 백엔드가 파일 크기를 검증한다
  - `400 Bad Request` 응답을 반환한다
  - 에러 메시지: `"파일 크기가 너무 큽니다. 최대 10MB까지 허용됩니다"`
  - 사용자에게 에러 메시지가 표시된다

**검증 방법**:
```python
async def test_presigned_url_file_too_large(async_client, auth_headers):
    response = await async_client.post(
        "/v1/uploads/presign",
        headers=auth_headers,
        json={"content_type": "audio/mpeg", "size_bytes": 15000000}
    )
    assert response.status_code == 400
    assert "파일 크기가 너무 큽니다" in response.json()["detail"]
```

---

### 시나리오 4: 채점 파이프라인 (Job 기반)

#### AC-010: Job 생성 및 비동기 처리
**Given**: 사용자가 S3 업로드를 완료한 상태 (`audio_key: user123/rec456.mp3`)
**When**: 앱이 `POST /v1/jobs` 엔드포인트를 호출한다
**Then**:
  - 백엔드가 Job 레코드를 생성한다 (상태: QUEUED)
  - Celery Task를 생성한다
  - `201 Created` 응답과 함께 `job_id`, `status`를 반환한다
  - 앱이 채점 진행 중 화면을 표시한다
  - 로딩 인디케이터가 표시된다

**검증 방법**:
```python
async def test_create_job(async_client, auth_headers, task):
    response = await async_client.post(
        "/v1/jobs",
        headers=auth_headers,
        json={
            "audio_key": "user123/rec456.mp3",
            "task_id": task.id,
            "task_type": "independent",
            "prompt": "Describe your favorite hobby."
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert "job_id" in data
    assert data["status"] == "QUEUED"
```

---

#### AC-011: Whisper ASR 실행 및 결과 저장
**Given**: Celery Worker가 Job을 수신하고 S3에서 오디오 다운로드 완료
**When**: Worker가 Whisper ASR을 실행한다 (상태: ASR_RUNNING)
**Then**:
  - Whisper가 다음 데이터를 반환한다:
    - `transcript`: 음성 텍스트
    - `segments`: 타임스탬프 배열 (start, end, text, avg_logprob, no_speech_prob)
    - `language`: 언어 코드 (en)
  - job_artifacts 테이블의 asr_json 필드에 저장된다
  - Job 상태가 FEATURE_EXTRACTING으로 업데이트된다
  - ASR 처리 시간이 30초 이내에 완료된다

**검증 방법**:
```python
async def test_whisper_asr_execution(celery_worker, job):
    task = run_whisper_asr.delay(job.id)
    result = task.get(timeout=40)
    assert result["status"] == "success"
    assert "transcript" in result["asr_json"]
    assert "segments" in result["asr_json"]
    assert len(result["asr_json"]["segments"]) > 0
    assert result["processing_time"] < 30.0
```

---

#### AC-012: Feature 추출 완료
**Given**: Whisper ASR 결과가 job_artifacts.asr_json에 저장된 상태
**When**: Worker가 Feature 추출 함수를 실행한다 (상태: FEATURE_EXTRACTING)
**Then**:
  - Delivery 신호가 추출된다:
    - duration_sec, wpm, silence_ratio, pause_count, pause_p95_ms, filler_count, asr_clarity_signal
  - Language 신호가 추출된다:
    - error_types, error_density, lexical_diversity, complexity, repetition
  - Structure 신호가 추출된다:
    - prompt_coverage, coherence, specificity
  - job_artifacts 테이블의 features_json 필드에 저장된다
  - Job 상태가 LLM_ANALYZING으로 업데이트된다
  - Feature 추출 시간이 10초 이내에 완료된다

**검증 방법**:
```python
async def test_feature_extraction(celery_worker, job_with_asr):
    task = extract_features.delay(job_with_asr.id)
    result = task.get(timeout=15)
    assert result["status"] == "success"
    features = result["features_json"]
    assert "delivery" in features
    assert "language" in features
    assert "structure" in features
    assert features["delivery"]["wpm"] > 0
    assert result["processing_time"] < 10.0
```

---

#### AC-013: LLM 분석 및 FeedbackReport 생성
**Given**: Feature 추출이 완료되고 features_json에 저장된 상태
**When**: Worker가 LLM API를 호출한다 (상태: LLM_ANALYZING)
**Then**:
  - LLM이 FeedbackReport JSON을 반환한다:
    - summary_3lines, bottleneck, action_items, structure, language, delivery, score_band, disclaimer
  - job_artifacts 테이블의 llm_json 필드에 저장된다
  - Job 상태가 SCORING으로 업데이트된다
  - LLM 호출 시간이 15초 이내에 완료된다

**검증 방법**:
```python
async def test_llm_analysis(celery_worker, job_with_features):
    task = analyze_with_llm.delay(job_with_features.id)
    result = task.get(timeout=20)
    assert result["status"] == "success"
    llm_response = result["llm_json"]
    assert "summary_3lines" in llm_response
    assert len(llm_response["summary_3lines"]) == 3
    assert "bottleneck" in llm_response
    assert "action_items" in llm_response
    assert len(llm_response["action_items"]) >= 1
    assert "score_band" in llm_response
    assert llm_response["score_band"]["min"] <= llm_response["score_band"]["max"]
    assert result["processing_time"] < 15.0
```

---

#### AC-014: 최종 리포트 저장 및 완료
**Given**: LLM 분석이 완료되고 llm_json에 저장된 상태
**When**: Worker가 리포트를 생성한다 (상태: SCORING → DONE)
**Then**:
  - reports 테이블에 레코드가 생성된다:
    - report_json: LLM 응답 전체
    - score_band_min: 점수 범위 최소값
    - score_band_max: 점수 범위 최대값
    - rubric_version: "toefl_speaking_2026_v1"
  - Job 상태가 DONE으로 업데이트된다
  - Type Analysis 평균 점수가 재계산된다
  - 사용자에게 Push Notification이 전송된다 (선택)

**검증 방법**:
```python
async def test_report_generation(db_session, job_id):
    report = await get_report_by_job_id(db_session, job_id)
    assert report is not None
    assert report.score_band_min is not None
    assert report.score_band_max is not None
    assert report.score_band_min <= report.score_band_max
    assert "summary_3lines" in report.report_json
    assert report.created_at <= datetime.now()

    # Job 상태 확인
    job = await get_job_by_id(db_session, job_id)
    assert job.status == "DONE"
    assert job.progress == 100
```

---

### 시나리오 5: 채점 결과 표시

#### AC-015: Job 상태 조회 (폴링)
**Given**: Job이 생성된 상태 (`job_id: abc123`)
**When**: 앱이 `GET /v1/jobs/{job_id}` 엔드포인트를 2초마다 폴링한다
**Then**:
  - 백엔드가 `200 OK` 응답과 함께 현재 상태를 반환한다:
    - status: QUEUED, FETCHING_AUDIO, ASR_RUNNING, FEATURE_EXTRACTING, LLM_ANALYZING, SCORING, DONE, FAILED
    - progress: 0-100 (진행률 퍼센트)
    - created_at, updated_at
  - 앱이 진행률 바를 업데이트한다
  - status가 DONE이 되면 폴링을 중단하고 리포트 조회 단계로 진행한다
  - status가 FAILED이면 에러 메시지를 표시한다

**검증 방법**:
```python
async def test_job_status_polling(async_client, auth_headers, job_in_progress):
    response = await async_client.get(
        f"/v1/jobs/{job_in_progress.id}",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] in ["QUEUED", "FETCHING_AUDIO", "ASR_RUNNING", "FEATURE_EXTRACTING", "LLM_ANALYZING", "SCORING", "DONE", "FAILED"]
    assert 0 <= data["progress"] <= 100
    assert "created_at" in data
    assert "updated_at" in data
```

---

#### AC-016: 최종 리포트 조회 및 표시
**Given**: Job 상태가 DONE인 상태 (`job_id: abc123`)
**When**: 앱이 `GET /v1/jobs/{job_id}/report` 엔드포인트를 호출한다
**Then**:
  - 백엔드가 `200 OK` 응답과 함께 FeedbackReport를 반환한다
  - 앱이 결과 화면을 표시한다:
    - **요약 진단 (3줄)**:
      - "현재 레벨: 중급 (22-25점 범위)"
      - "가장 큰 감점 요인: 답변 구조 부재 (Intro/Conclusion 누락)"
      - "언어 사용은 양호하나 구조 개선 시 고득점 가능"
    - **가장 큰 병목 1가지**:
      - 제목: "구조 부재"
      - 설명: "서론과 결론이 명확하지 않아 채점자가 답변 방향을 파악하기 어려움"
      - 증거: "I think... and that's it." (인용)
    - **행동 아이템 (1-2개)**:
      - 행동: "서론에 명확한 입장 표명"
      - 이유: "채점자가 답변 방향을 즉시 파악"
      - 방법: "In my opinion, ... for two reasons."
      - 예시 문장: "In my opinion, online classes are more effective for two reasons."
    - **답변 구조 시각화**:
      - ❌ Intro
      - ✅ Reason1
      - ❌ Example1
      - ❌ Reason2
      - ❌ Example2
      - ❌ Wrap-up
      - 누락: Intro, Example1, Reason2, Example2, Wrap-up
      - 권장 템플릿: "Intro → Reason1 → Example1 → Reason2 → Example2 → Wrap-up"
    - **언어 사용 분석**:
      - TOP 2 오류: "시제 불일치 3회", "관사 누락 2회"
      - 개선 문장: "I go → I went", "I have experience → I have an experience"
    - **Delivery 분석**:
      - 속도: "적절 (140 WPM)"
      - 침묵: "중간 침묵이 많아 전달력 저하 (15% 침묵 비율)"
      - 명료도: "일부 구간 ASR 인식 어려움 → 또박또박 발음 필요"
    - **점수 범위**: 22-25점
      - 근거: "구조 점수 낮음 (Intro/Conclusion 부재), 언어 사용 양호, Delivery 보통"
    - **면책 고지**: "본 평가는 학습 도구이며 실제 TOEFL 점수와 다를 수 있습니다."

**검증 방법**:
```python
async def test_get_feedback_report(async_client, auth_headers, completed_job):
    response = await async_client.get(
        f"/v1/jobs/{completed_job.id}/report",
        headers=auth_headers
    )
    assert response.status_code == 200
    report = response.json()

    # 필수 필드 검증
    assert "summary_3lines" in report
    assert len(report["summary_3lines"]) == 3

    assert "bottleneck" in report
    assert "title" in report["bottleneck"]
    assert "explanation" in report["bottleneck"]
    assert "evidence_quote" in report["bottleneck"]

    assert "action_items" in report
    assert len(report["action_items"]) >= 1
    for item in report["action_items"]:
        assert "action" in item
        assert "why" in item
        assert "how_to" in item

    assert "structure" in report
    assert "checklist" in report["structure"]
    assert "missing" in report["structure"]
    assert "suggested_template" in report["structure"]

    assert "language" in report
    assert "top_errors" in report["language"]
    assert "improved_sentences" in report["language"]

    assert "delivery" in report
    assert "speed_comment" in report["delivery"]
    assert "pause_comment" in report["delivery"]
    assert "clarity_comment" in report["delivery"]

    assert "score_band" in report
    assert "min" in report["score_band"]
    assert "max" in report["score_band"]
    assert "rationale" in report["score_band"]
    assert report["score_band"]["min"] <= report["score_band"]["max"]

    assert "disclaimer" in report
```

---

### 시나리오 6: Type Analysis

#### AC-017: Type Analysis 평균 점수 계산 (점수 범위 기반)
**Given**: 사용자가 여러 모의고사를 완료한 상태 (점수 범위의 중간값 사용)
  - Q1: [22-25] (중간값 23.5), [20-23] (중간값 21.5), [24-26] (중간값 25.0) → 평균 23.33
  - Q2: [18-21] (중간값 19.5), [20-22] (중간값 21.0), [19-21] (중간값 20.0) → 평균 20.17
  - Q3: [24-27] (중간값 25.5), [26-28] (중간값 27.0), [25-27] (중간값 26.0) → 평균 26.17
  - Q4: [22-24] (중간값 23.0), [23-25] (중간값 24.0), [22-25] (중간값 23.5) → 평균 23.50
**When**: 앱이 `GET /api/analysis/user/{user_id}` 엔드포인트를 호출한다
**Then**:
  - 백엔드가 PostgreSQL 집계 쿼리를 실행한다:
    - reports 테이블에서 score_band_min, score_band_max를 조회
    - 각 리포트의 중간값 계산: (min + max) / 2
    - question_type별 평균 계산
  - 결과를 반환한다:
    ```json
    {
      "q1_avg": 23.33,
      "q2_avg": 20.17,
      "q3_avg": 26.17,
      "q4_avg": 23.50,
      "weakest_type": "Q2",
      "strongest_type": "Q3"
    }
    ```
  - 앱이 차트로 시각화한다 (막대 그래프 또는 레이더 차트)

**검증 방법**:
```python
async def test_type_analysis_calculation(async_client, auth_headers, user_with_score_bands):
    response = await async_client.get(
        f"/api/analysis/user/{user_with_score_bands.id}",
        headers=auth_headers
    )
    assert response.status_code == 200
    analysis = response.json()
    assert abs(analysis["q1_avg"] - 23.33) < 0.1
    assert abs(analysis["q2_avg"] - 20.17) < 0.1
    assert abs(analysis["q3_avg"] - 26.17) < 0.1
    assert abs(analysis["q4_avg"] - 23.50) < 0.1
    assert analysis["weakest_type"] == "Q2"
    assert analysis["strongest_type"] == "Q3"
```

---

### 시나리오 7: Practice History

#### AC-017: Practice History 조회
**Given**: 사용자가 10개의 연습 녹음을 완료한 상태
**When**: 사용자가 Practice 페이지의 "History" 탭에 접근한다
**Then**:
  - 앱이 `GET /api/practice/history` 엔드포인트를 호출한다
  - 백엔드가 최신순으로 녹음 목록을 반환한다 (페이지네이션: 10개씩)
  - 각 녹음은 다음 정보를 포함한다:
    - 날짜 및 시간
    - 점수 (Overall Score)
    - 문제 유형 (Q1, Q2, Q3, Q4)
  - 앱이 FlatList로 목록을 표시한다

**검증 방법**:
```python
async def test_practice_history_list(async_client, auth_headers, user_with_recordings):
    response = await async_client.get(
        "/api/practice/history",
        headers=auth_headers,
        params={"page": 1, "size": 10}
    )
    assert response.status_code == 200
    history = response.json()
    assert len(history["items"]) <= 10
    assert history["total"] >= 10
```

---

#### AC-018: 특정 녹음 재생 및 Transcript 확인
**Given**: 사용자가 Practice History에서 특정 녹음을 선택한다
**When**: 사용자가 재생 버튼을 누른다
**Then**:
  - 앱이 S3에서 오디오 파일을 다운로드한다
  - Expo Audio를 사용하여 재생한다
  - 재생 중에는 일시정지/재생 컨트롤이 표시된다
  - "Show Transcript" 버튼을 누르면, `GET /api/practice/{recording_id}/transcript`를 호출한다
  - Transcript가 화면에 표시된다

**검증 방법**: 수동 테스트
- [ ] 오디오 재생 확인
- [ ] Transcript 표시 확인

---

## 🏁 Quality Gate (품질 게이트)

### 코드 품질
- [ ] **테스트 커버리지 ≥ 85%** (백엔드 pytest)
- [ ] **Ruff 린터 경고 0건** (FastAPI 코드)
- [ ] **TypeScript 타입 에러 0건** (선택, React Native에 TypeScript 사용 시)
- [ ] **React Native ESLint 경고 < 5건**

### 성능 기준
- [ ] **API 응답 시간**: P95 < 500ms, P99 < 1000ms (Job 생성, 상태 조회)
- [ ] **채점 완료 시간**: Job 생성부터 DONE 상태까지
  - Whisper ASR: < 30초
  - Feature 추출: < 10초
  - LLM 분석: < 15초
  - 전체 파이프라인: < 60초 (평균)
- [ ] **S3 업로드 시간**: presigned URL 사용 시 < 5초 (1MB 파일 기준)
- [ ] **앱 초기 로딩 시간**: < 3초 (iOS/Android)
- [ ] **메모리 사용량**: < 200MB (백그라운드 상태)

### 보안 기준
- [ ] **OWASP Top 10 체크리스트**: 모든 항목 Pass
- [ ] **JWT 토큰 만료 시간**: Access Token 15분, Refresh Token 7일
- [ ] **S3 버킷 공개 접근**: 차단 (IAM Policy 설정)
- [ ] **API Rate Limiting**: 사용자당 분당 60 요청 제한

### 사용자 경험
- [ ] **앱 크래시율**: < 1% (Firebase Crashlytics)
- [ ] **오디오 녹음 성공률**: > 95%
- [ ] **S3 업로드 성공률**: > 99% (presigned URL 방식)
- [ ] **채점 성공률**: > 95% (Whisper ASR + Feature 추출 + LLM API 합산)
  - Whisper ASR 성공률: > 98%
  - Feature 추출 성공률: > 99%
  - LLM JSON 파싱 성공률: > 97%
- [ ] **Job 상태 폴링 응답 시간**: < 200ms (평균)
- [ ] **iOS/Android 실기기 테스트**: 각 플랫폼 2대 이상

---

## ✅ Definition of Done (완료 정의)

다음 조건이 **모두** 충족되어야 SPEC-TOEFL-001이 완료된 것으로 간주됩니다:

### 기능 완료
- [x] 모든 Primary Goal (Milestone 1.1 ~ 1.7) 완료
  - Milestone 1.5: Whisper ASR 통합
  - Milestone 1.6: Feature 추출 파이프라인 (Delivery/Language/Structure 신호)
  - Milestone 1.7: LLM 분석 및 FeedbackReport 생성
- [x] 모든 AC 시나리오 (AC-001 ~ AC-018) 통과
  - Job 기반 비동기 파이프라인 검증
  - Whisper ASR 결과 검증
  - Feature 추출 결과 검증
  - LLM FeedbackReport JSON 스키마 검증
  - 점수 범위 기반 Type Analysis 검증
- [x] iOS 및 Android 실기기에서 정상 작동 확인
  - S3 직접 업로드 성공
  - Job 상태 폴링 정상 작동
  - FeedbackReport 시각화 정상 표시

### 품질 완료
- [x] Quality Gate 모든 항목 Pass
- [x] 백엔드 테스트 커버리지 ≥ 85%
- [x] 보안 취약점 0건 (Snyk 또는 Bandit 스캔)

### 문서 완료
- [x] API 문서 생성 (FastAPI `/docs` Swagger UI)
- [x] README.md 업데이트 (설치 방법, 실행 방법)
- [x] 배포 가이드 작성 (Docker Compose, 환경변수 설정)

### 배포 준비
- [x] Docker 이미지 빌드 성공
- [x] 프로덕션 환경에서 스모크 테스트 완료
- [x] 모니터링 및 알림 설정 (CloudWatch, Sentry)

---

## 🛠️ 테스트 도구 및 프레임워크

### 백엔드 테스트
- **pytest**: 단위 테스트 및 통합 테스트
- **pytest-asyncio**: 비동기 함수 테스트
- **httpx**: FastAPI TestClient (API 엔드포인트 테스트)
- **pytest-mock**: Speechace/LLM API 모킹
- **pytest-cov**: 코드 커버리지 측정

### 프론트엔드 테스트
- **Jest**: React Native 단위 테스트
- **React Testing Library**: 컴포넌트 테스트
- **Detox** (선택): E2E 테스트 (iOS/Android)

### 성능 테스트
- **Locust**: API 부하 테스트
- **React Native Performance Monitor**: 앱 성능 모니터링

### 보안 테스트
- **Bandit**: Python 코드 보안 스캔
- **Snyk**: 의존성 취약점 검사
- **OWASP ZAP**: API 보안 테스트

---

## 📊 테스트 실행 계획

### Phase 1: 단위 테스트 (개발 중)
- **빈도**: 매 커밋마다 실행
- **범위**: 개별 함수 및 클래스
- **도구**: pytest (백엔드), Jest (프론트엔드)

### Phase 2: 통합 테스트 (기능 완료 시)
- **빈도**: Pull Request 머지 전
- **범위**: API 엔드포인트, Celery Task, 데이터베이스 상호작용
- **도구**: pytest (FastAPI TestClient)

### Phase 3: E2E 테스트 (Milestone 완료 시)
- **빈도**: 주 1회 또는 주요 기능 완료 시
- **범위**: 사용자 시나리오 전체 플로우
- **도구**: Detox (선택) 또는 수동 테스트

### Phase 4: 성능 및 보안 테스트 (배포 전)
- **빈도**: 프로덕션 배포 전 1회
- **범위**: API 부하 테스트, 보안 취약점 스캔
- **도구**: Locust, Bandit, Snyk

---

## 🔄 회귀 테스트 (Regression Testing)

새로운 기능 추가 또는 버그 수정 후, 다음 시나리오를 재실행하여 기존 기능이 정상 작동하는지 확인합니다:

- [ ] AC-003: 로그인 성공
- [ ] AC-006: 녹음 시작
- [ ] AC-010: 채점 요청
- [ ] AC-015: 채점 결과 표시
- [ ] AC-016: Type Analysis 계산

---

**작성자**: workflow-spec
**검토자**: 수연
**버전**: 1.0.0
**최종 수정일**: 2026-01-24
