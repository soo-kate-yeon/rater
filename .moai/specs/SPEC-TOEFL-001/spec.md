# SPEC-TOEFL-001: TOEFL Speaking Training 모바일 앱

## 📌 TAG BLOCK

```
SPEC-ID: SPEC-TOEFL-001
제목: TOEFL Speaking Response 모의고사 훈련 앱
생성일: 2026-01-24
상태: Planned
우선순위: High
담당: workflow-spec
```

---

## 🎯 개요

TOEFL Speaking Response(SR) 모의고사 훈련을 위한 모바일 앱을 개발합니다. 사용자는 앱 내에서 모의고사를 수행하고, 녹음된 응답에 대해 자동 채점 및 피드백을 받을 수 있습니다.

### 핵심 가치

- **실행 가능한 피드백**: Whisper ASR + LLM 기반 구조적 분석으로 구체적 개선 방향 제시
- **약점 병목 분석**: 가장 큰 감점 요인 1가지 집중 제시로 효율적 학습 지원
- **점수 범위 제공**: 단일 점수 대신 점수 범위(예: 22-25)와 근거로 현실적 기대치 설정
- **구조 시각화**: 답변 구조 체크리스트로 TOEFL 템플릿 준수 여부 즉시 확인

---

## 🌍 Environment (환경)

### 기술 스택

#### Frontend (모바일 앱)
- **React Native**: 최신 안정 버전 (0.73+)
- **React Navigation**: 페이지 라우팅 (v6)
- **React Native Voice**: 음성 녹음 (v3.2+)
- **Expo Audio**: 오디오 재생 및 녹음 관리
- **Axios**: HTTP 클라이언트
- **AsyncStorage**: 로컬 데이터 저장

#### Backend (API 서버)
- **FastAPI**: 최신 안정 버전 (0.115+)
- **PostgreSQL**: 데이터베이스 (v15+)
- **SQLAlchemy 2.0**: ORM (async 지원)
- **Pydantic v2.9**: 데이터 검증
- **Celery**: 비동기 작업 큐
- **Redis**: Celery 브로커 및 캐싱

#### Audio Processing
- **ffmpeg**: 오디오 정규화 (normalization)
- **webrtcvad**: Voice Activity Detection (음성 구간 탐지)
- **pydub**: Python 오디오 처리

#### Scoring Integration
- **Whisper ASR**: OpenAI Whisper 또는 로컬 배포 (음성 → 텍스트 변환 + 타임스탬프 + 신뢰도 지표)
- **OpenAI GPT-4** 또는 **Anthropic Claude**: 구조 분석, 언어 사용 평가, 피드백 생성, 점수 범위 추정
- **Feature Extraction**: Delivery 신호(WPM, 침묵 비율, filler 카운트), Language 신호(문법 오류, 어휘 다양성), Structure 신호(EARS 체크리스트)

### 운영 환경
- **Platform**: iOS 14+ / Android 8+
- **Database**: PostgreSQL 15+ (RDS 또는 Cloud SQL)
- **File Storage**: AWS S3 또는 Google Cloud Storage (녹음 파일 저장)
- **Queue**: Redis (Celery 브로커)

---

## 🔧 Assumptions (가정사항)

### 비즈니스 가정
1. **사용자는 TOEFL Speaking 시험 준비 경험이 있으며**, Q1-Q4 문제 유형을 이해하고 있다고 가정합니다.
2. **사용자는 안정적인 인터넷 연결 환경**에서 모의고사를 수행한다고 가정합니다.
3. **Speechace API와 LLM API는 99% 이상의 가용성**을 제공한다고 가정합니다.

### 기술 가정
1. **React Native는 iOS와 Android 플랫폼 모두에서 안정적으로 작동**하며, 네이티브 모듈 통합(음성 녹음)이 원활하다고 가정합니다.
2. **FastAPI는 비동기 요청 처리를 통해 초당 100건 이상의 동시 요청을 처리**할 수 있다고 가정합니다.
3. **ffmpeg와 webrtcvad는 45-60초 길이의 오디오 파일을 3초 이내에 전처리**할 수 있다고 가정합니다.
4. **Speechace API는 60초 오디오 분석을 10초 이내에 완료**한다고 가정합니다.
5. **LLM API는 응답 평가 프롬프트를 5초 이내에 처리**한다고 가정합니다.

### 팀 가정
1. **개발자는 React Native, FastAPI, PostgreSQL에 대한 중급 이상의 경험**을 보유하고 있다고 가정합니다.
2. **Speechace API와 LLM API 문서는 충분히 상세하며**, 통합에 필요한 모든 정보를 제공한다고 가정합니다.

### 리스크 분석
| 가정사항 | 신뢰도 | 근거 | 틀렸을 경우 리스크 | 검증 방법 |
|---------|--------|------|-------------------|----------|
| Speechace API 가용성 99% | Medium | 공식 문서 SLA 미확인 | 채점 서비스 중단 | 초기 POC에서 API 안정성 테스트 |
| 오디오 전처리 3초 이내 | High | ffmpeg 벤치마크 데이터 | 사용자 대기 시간 증가 | 로컬 환경에서 성능 테스트 |
| React Native 네이티브 모듈 안정성 | Medium | 커뮤니티 리포트 | 녹음 기능 불안정 | iOS/Android 실기기 테스트 |

---

## 📋 Requirements (요구사항)

### 1. Ubiquitous Requirements (시스템 전체 필수 요구사항)

#### REQ-001: 사용자 인증 및 세션 관리
**시스템은 항상** 사용자 인증 토큰(JWT)을 검증하고, 유효하지 않은 토큰에 대해 401 Unauthorized 응답을 반환**해야 한다**.

**WHY**: 사용자 데이터 보호 및 개인화된 학습 히스토리 관리를 위해 필수
**IMPACT**: 인증 없이는 모의고사 결과 및 학습 진척도 추적 불가능

#### REQ-002: 오디오 파일 검증
**시스템은 항상** 업로드된 오디오 파일이 다음 조건을 만족하는지 검증**해야 한다**:
- 파일 형식: MP3, WAV, M4A
- 파일 크기: 최대 10MB
- 길이: 45초 이상 60초 이하

**WHY**: 잘못된 파일 형식 또는 크기로 인한 처리 실패 방지
**IMPACT**: 검증 없이는 백엔드 오류 및 사용자 혼란 발생

#### REQ-003: 에러 로깅 및 모니터링
**시스템은 항상** 모든 API 요청 실패, 채점 오류, 오디오 처리 실패를 로그에 기록**해야 한다**.

**WHY**: 운영 중 문제 추적 및 신속한 장애 대응
**IMPACT**: 로깅 없이는 문제 원인 분석 불가능

---

### 2. Event-Driven Requirements (이벤트 기반 요구사항)

#### REQ-004: 모의고사 시작
**WHEN** 사용자가 Exam 페이지에서 특정 모의고사(예: "Seoul Test")를 선택하면,
**THEN** 앱은 해당 모의고사의 Q1-Q4 문제를 순서대로 로드하고, 첫 번째 문제 화면을 표시**해야 한다**.

**WHY**: 사용자가 원하는 모의고사를 즉시 시작할 수 있도록 보장
**IMPACT**: 문제 로드 실패 시 사용자는 모의고사를 시작할 수 없음

#### REQ-005: 녹음 시작 및 종료
**WHEN** 사용자가 Practice 페이지에서 "Record" 버튼을 누르면,
**THEN** 앱은 즉시 음성 녹음을 시작하고, 녹음 중임을 나타내는 시각적 피드백(예: 빨간색 버튼, 타이머)을 표시**해야 한다**.

**WHEN** 사용자가 "Stop" 버튼을 누르거나 60초가 경과하면,
**THEN** 앱은 녹음을 종료하고, 녹음된 파일을 로컬에 저장한 후 업로드 준비 상태로 전환**해야 한다**.

**WHY**: 사용자가 녹음 프로세스를 명확하게 제어할 수 있도록 보장
**IMPACT**: 녹음 실패 시 사용자는 응답을 제출할 수 없음

#### REQ-006: 오디오 업로드 및 채점 요청
**WHEN** 사용자가 녹음 완료 후 "Submit" 버튼을 누르면,
**THEN** 앱은 다음 작업을 순서대로 수행**해야 한다**:
1. 녹음 파일을 백엔드 API(`POST /api/recordings`)로 업로드
2. 업로드 성공 시 채점 요청을 백엔드에 전송(`POST /api/scoring/submit`)
3. 채점 진행 중임을 나타내는 로딩 화면 표시
4. 채점 완료 시 결과 화면으로 자동 이동

**WHY**: 사용자가 녹음 후 즉시 피드백을 받을 수 있도록 보장
**IMPACT**: 업로드 또는 채점 요청 실패 시 사용자는 결과를 받을 수 없음

#### REQ-007: 채점 결과 표시
**WHEN** 채점이 완료되고 백엔드에서 결과가 반환되면,
**THEN** 앱은 다음 정보를 포함한 결과 화면을 표시**해야 한다**:
- **요약 진단 (3줄)**: 현재 레벨 포지션 + 가장 큰 감점 요인 + 전체적 평가
- **가장 큰 병목 1가지**: 제목 + 설명 + 증거 문장 인용
- **행동 아이템 (1-2개)**: 다음 답변에서 즉시 바꿀 구체적 행동 + 이유 + 방법 + 예시 문장
- **답변 구조 시각화**: Intro/Reason1/Example1/Reason2/Example2/Wrap-up 체크리스트
- **언어 사용 분석**: 반복 오류 TOP 2 + 개선 문장 예시
- **Delivery 분석**: 속도 코멘트 + 침묵 코멘트 + 명료도 코멘트
- **점수 범위**: 최소-최대 (예: 22-25) + 근거 설명
- **면책 고지**: 실제 TOEFL 점수와 다를 수 있음 명시

**WHY**: 사용자가 무엇을 바꿔야 할지 명확히 알고 즉시 행동할 수 있도록 지원
**IMPACT**: 결과 표시 실패 시 사용자는 구체적 개선 방향을 파악할 수 없음

#### REQ-008: Type Analysis 업데이트
**WHEN** 사용자가 새로운 모의고사를 완료하면,
**THEN** 백엔드는 해당 사용자의 Q1, Q2, Q3, Q4 평균 점수를 재계산하고, Type Analysis 페이지에 반영**해야 한다**.

**WHY**: 사용자가 유형별 약점을 실시간으로 파악할 수 있도록 보장
**IMPACT**: 분석 업데이트 실패 시 사용자는 잘못된 정보를 기반으로 학습 전략 수립

---

### 3. State-Driven Requirements (상태 기반 요구사항)

#### REQ-009: 인터넷 연결 상태 확인
**IF** 사용자가 오프라인 상태**이면**,
**THEN** 앱은 다음 기능을 제한**해야 한다**:
- 모의고사 시작 불가 (문제 로드 실패)
- 녹음 파일 업로드 불가 (재시도 옵션 제공)
- Type Analysis 페이지 데이터 갱신 불가 (캐시된 데이터 표시)

**WHY**: 네트워크 의존적 기능에 대한 명확한 사용자 피드백 제공
**IMPACT**: 오프라인 처리 없이는 사용자가 앱 작동 실패 원인을 이해할 수 없음

#### REQ-010: 채점 진행 중 상태
**IF** 채점이 현재 진행 중**이면**,
**THEN** 앱은 다음 동작을 수행**해야 한다**:
- 사용자가 다른 페이지로 이동 가능하지만, 채점 진행 중임을 상태바에 표시
- 채점 완료 시 알림(Notification)을 통해 사용자에게 결과 확인 유도

**WHY**: 사용자가 채점 대기 시간 동안 다른 활동을 할 수 있도록 유연성 제공
**IMPACT**: 상태 관리 없이는 사용자가 채점 완료 여부를 알 수 없음

---

### 4. Unwanted Requirements (금지 요구사항)

#### REQ-011: 개인정보 노출 금지
**시스템은** 로그 파일, 에러 메시지, API 응답에 사용자 이메일, 비밀번호, 개인 식별 정보(PII)를 포함**하지 않아야 한다**.

**WHY**: GDPR, CCPA 등 개인정보 보호 규정 준수
**IMPACT**: PII 노출 시 법적 책임 및 사용자 신뢰 손실

#### REQ-012: 미검증 파일 저장 금지
**시스템은** 오디오 파일 검증(REQ-002) 없이 파일을 S3 또는 데이터베이스에 저장**하지 않아야 한다**.

**WHY**: 악성 파일 또는 비정상 파일로 인한 저장소 낭비 및 보안 위험 방지
**IMPACT**: 미검증 저장 시 스토리지 비용 증가 및 보안 취약점 발생

#### REQ-013: 동기 채점 요청 금지
**시스템은** 채점 요청을 동기(synchronous) 방식으로 처리**하지 않아야 한다**.
모든 채점 작업은 비동기 큐(Celery)를 통해 처리**해야 한다**.

**WHY**: 채점 시간(Speechace + LLM 총 15초 이상)으로 인한 HTTP 타임아웃 방지
**IMPACT**: 동기 처리 시 사용자 대기 시간 증가 및 서버 리소스 블로킹

---

### 5. Optional Requirements (선택 요구사항)

#### REQ-014: ELSA API 통합
**가능하면**, 향후 단계에서 ELSA API를 통합하여 다음 분석을 제공**할 수 있다**:
- **Pronunciation**: 발음 정확도
- **Intonation**: 억양 자연스러움
- **Fluency**: 유창성 (말하기 속도, 쉼 빈도)

**WHY**: 사용자에게 더 세밀한 발음 및 억양 피드백 제공
**IMPACT**: ELSA 미통합 시에도 Speechace + LLM으로 기본 채점 가능

#### REQ-015: 오프라인 녹음 지원
**가능하면**, 사용자가 오프라인 상태에서도 녹음을 저장하고, 온라인 복귀 시 자동 업로드하는 기능을 제공**할 수 있다**.

**WHY**: 네트워크가 불안정한 환경에서도 학습 연속성 보장
**IMPACT**: 미지원 시에도 온라인 환경에서는 정상 작동

---

## 🛠️ Specifications (세부 명세)

### API Endpoints

#### 1. 사용자 인증
- `POST /api/auth/register`: 회원가입
- `POST /api/auth/login`: 로그인 (JWT 토큰 발급)
- `POST /api/auth/refresh`: 토큰 갱신

#### 2. 모의고사 관리
- `GET /api/exams`: 모의고사 목록 조회 (Seoul, Milan, Tokyo 등)
- `GET /api/exams/{exam_id}`: 특정 모의고사 상세 조회 (Q1-Q4 문제)
- `GET /api/exams/{exam_id}/results`: 모의고사 결과 리포트 조회

#### 3. 녹음 업로드 및 Job 관리
- `POST /v1/uploads/presign`: 업로드 세션 생성 (presigned URL 발급)
  - Request: `{"content_type": "audio/mpeg", "size_bytes": 1024000}`
  - Response: `{"upload_url": "https://...", "audio_key": "user123/rec456.mp3", "expires_at": "2026-01-24T12:00:00Z"}`
- `POST /v1/jobs`: 채점 Job 생성
  - Request: `{"audio_key": "user123/rec456.mp3", "task_id": 1, "task_type": "independent", "prompt": "질문 텍스트"}`
  - Response: `{"job_id": "abc123", "status": "QUEUED"}`
- `GET /v1/jobs/{job_id}`: Job 상태 조회 (폴링 또는 SSE)
  - Response: `{"status": "QUEUED|FETCHING_AUDIO|ASR_RUNNING|FEATURE_EXTRACTING|LLM_ANALYZING|SCORING|DONE|FAILED", "progress": 65, "created_at": "...", "updated_at": "..."}`
- `GET /v1/jobs/{job_id}/report`: 최종 피드백 리포트 조회
  - Response: FeedbackReport JSON (summary_3lines, bottleneck, action_items, structure, language, delivery, score_band, disclaimer)

#### 4. Type Analysis
- `GET /api/analysis/user/{user_id}`: 사용자의 Q1-Q4 평균 점수 조회
  - Response: `{ q1_avg: 3.2, q2_avg: 2.8, q3_avg: 3.5, q4_avg: 3.0 }`

#### 5. Practice History
- `GET /api/practice/history`: 사용자의 연습 히스토리 조회
  - Response: 녹음 목록 (날짜, 점수, transcript)
- `GET /api/practice/{recording_id}/transcript`: 특정 녹음의 텍스트 변환 결과 조회

### Database Schema

#### Users 테이블
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    name VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### Exams 테이블
```sql
CREATE TABLE exams (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,  -- "Seoul Test", "Milan Test"
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### Tasks 테이블 (문제 정보)
```sql
CREATE TABLE tasks (
    id SERIAL PRIMARY KEY,
    exam_id INTEGER REFERENCES exams(id) ON DELETE CASCADE,
    type VARCHAR(20) NOT NULL,  -- "independent", "integrated"
    question_type VARCHAR(10) NOT NULL,  -- "Q1", "Q2", "Q3", "Q4"
    prompt TEXT NOT NULL,
    source_reading TEXT,  -- 통합형 문제용 (선택)
    source_listening TEXT,  -- 통합형 문제용 (선택)
    tags VARCHAR(100)[],  -- 문제 태그
    preparation_time INTEGER DEFAULT 15,
    response_time INTEGER DEFAULT 45,
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### Jobs 테이블 (채점 작업 상태)
```sql
CREATE TABLE jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    task_id INTEGER REFERENCES tasks(id) ON DELETE CASCADE,
    status VARCHAR(30) NOT NULL,  -- QUEUED, FETCHING_AUDIO, ASR_RUNNING, FEATURE_EXTRACTING, LLM_ANALYZING, SCORING, DONE, FAILED
    progress INTEGER DEFAULT 0,  -- 0-100
    audio_key VARCHAR(500) NOT NULL,  -- S3 key
    error_code VARCHAR(50),  -- 실패 시 에러 코드
    error_message TEXT,  -- 실패 시 에러 메시지
    retryable BOOLEAN DEFAULT true,  -- 재시도 가능 여부
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_jobs_user_id ON jobs(user_id);
CREATE INDEX idx_jobs_status ON jobs(status);
```

#### Job_Artifacts 테이블 (중간 산출물)
```sql
CREATE TABLE job_artifacts (
    id SERIAL PRIMARY KEY,
    job_id UUID REFERENCES jobs(id) ON DELETE CASCADE,
    asr_json JSONB,  -- Whisper 결과 (transcript, segments, avg_logprob, no_speech_prob)
    features_json JSONB,  -- Feature 추출 결과 (delivery, language, structure 신호)
    llm_json JSONB,  -- LLM 원본 응답
    pipeline_version VARCHAR(50) DEFAULT 'v1',  -- 파이프라인 버전
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_artifacts_job_id ON job_artifacts(job_id);
```

#### Reports 테이블 (최종 피드백)
```sql
CREATE TABLE reports (
    id SERIAL PRIMARY KEY,
    job_id UUID REFERENCES jobs(id) ON DELETE CASCADE,
    report_json JSONB NOT NULL,  -- FeedbackReport 전체 (summary_3lines, bottleneck, action_items, structure, language, delivery, score_band, disclaimer)
    score_band_min INTEGER,  -- 점수 범위 최소값 (예: 22)
    score_band_max INTEGER,  -- 점수 범위 최대값 (예: 25)
    rubric_version VARCHAR(50) DEFAULT 'toefl_speaking_2026_v1',
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_reports_job_id ON reports(job_id);
CREATE INDEX idx_reports_score_band ON reports(score_band_min, score_band_max);
```

### 채점 파이프라인 상세 (Job State Machine)

#### Job 상태 전이
`QUEUED` → `FETCHING_AUDIO` → `ASR_RUNNING` → `FEATURE_EXTRACTING` → `LLM_ANALYZING` → `SCORING` → `DONE`

실패 시: `FAILED` (error_code + error_message + retryable)

**재시도 정책**:
- 스토리지 fetch 실패: 최대 3회 (지수 백오프)
- ASR/LLM 일시 실패: 최대 2회
- 입력 검증 실패 (오디오 길이 0 등): 재시도 없음

---

#### Phase 1: 오디오 업로드 및 Job 생성
1. **클라이언트**: `POST /v1/uploads/presign` 호출 → presigned URL 수신
2. **클라이언트**: S3로 직접 업로드 (서버 부하 감소)
3. **클라이언트**: `POST /v1/jobs` 호출 (audio_key, task_id, prompt 전달)
4. **백엔드**: Job 레코드 생성 (상태: QUEUED), Celery Task 생성

---

#### Phase 2: Whisper ASR 실행 (FETCHING_AUDIO → ASR_RUNNING)
1. **Celery Worker**: S3에서 오디오 파일 다운로드
2. **AudioMeta 추출**: duration_ms, sample_rate, codec, size_bytes
3. **Whisper 실행**:
   - OpenAI Whisper API 또는 로컬 Whisper 모델 (faster-whisper 권장)
   - Output: `transcript`, `segments` (타임스탬프), `avg_logprob`, `no_speech_prob`
4. **job_artifacts 테이블 저장**: asr_json 필드 업데이트

---

#### Phase 3: Feature 추출 (FEATURE_EXTRACTING)
**Delivery 신호 추출** (Whisper segments 기반):
- `duration_sec`: 전체 녹음 길이
- `wpm`: words per minute
- `silence_ratio`: (침묵>500ms 누적) / 전체 길이
- `pause_count`: 침묵>500ms 횟수
- `pause_p95_ms`: 95th percentile pause 길이
- `filler_count`: {uh, um, like, you know} 카운트
- `asr_clarity_signal`: avg_logprob, no_speech_prob

**Language 신호 추출** (Transcript + 규칙 기반):
- `error_types`: 시제/수일치/관사/전치사 오류 TOP N
- `error_density`: 오류 수 / 100단어
- `lexical_diversity`: TTR (Type-Token Ratio)
- `complexity`: 평균 문장 길이, 종속절 사용
- `repetition`: 동일 표현 반복률

**job_artifacts 테이블 저장**: features_json 필드 업데이트

---

#### Phase 4: LLM 분석 및 리포트 생성 (LLM_ANALYZING → SCORING)
**LLM 프롬프트 컨텍스트**:
- task_type: independent/integrated
- prompt: 질문 텍스트
- transcript: Whisper 결과
- segments: 타임스탬프 요약
- features: Phase 3에서 추출한 신호 (JSON)
- (선택) source_reading, source_listening

**LLM 출력 JSON Schema** (강제):
```json
{
  "summary_3lines": ["현재 레벨 포지션", "가장 큰 감점 요인", "전체 평가"],
  "bottleneck": {
    "title": "구조 부재",
    "explanation": "서론과 결론이 명확하지 않음",
    "evidence_quote": "I think... and that's it."
  },
  "action_items": [
    {
      "action": "서론에 명확한 입장 표명",
      "why": "채점자가 답변 방향을 즉시 파악",
      "how_to": "In my opinion, ... for two reasons.",
      "example_sentence": "In my opinion, online classes are more effective for two reasons."
    }
  ],
  "structure": {
    "checklist": {"Intro": false, "Reason1": true, "Example1": false, "Reason2": false, "Example2": false, "Wrap-up": false},
    "missing": ["Intro", "Example1", "Reason2", "Example2", "Wrap-up"],
    "suggested_template": "Intro → Reason1 → Example1 → Reason2 → Example2 → Wrap-up"
  },
  "language": {
    "top_errors": ["시제 불일치 3회", "관사 누락 2회"],
    "improved_sentences": ["I go → I went", "I have experience → I have an experience"]
  },
  "delivery": {
    "speed_comment": "속도는 적절 (140 WPM)",
    "pause_comment": "중간 침묵이 많아 전달력 저하 (15% 침묵 비율)",
    "clarity_comment": "일부 구간 ASR 인식 어려움 → 또박또박 발음 필요"
  },
  "score_band": {
    "min": 22,
    "max": 25,
    "rationale": "구조 점수 낮음 (Intro/Conclusion 부재), 언어 사용 양호, Delivery 보통"
  },
  "disclaimer": "본 평가는 학습 도구이며 실제 TOEFL 점수와 다를 수 있습니다."
}
```

**job_artifacts 저장**: llm_json 필드 업데이트

---

#### Phase 5: 최종 리포트 저장 (DONE)
1. **reports 테이블 생성**: LLM JSON을 report_json에 저장
2. **score_band_min/max 인덱스 저장**: 쿼리 최적화용
3. **Job 상태 업데이트**: status = DONE
4. **Type Analysis 업데이트**: Q1-Q4 평균 점수 재계산 (score_band의 중간값 사용)
5. **알림 전송**: Push Notification 또는 WebSocket

---

## 🔗 Traceability (추적성)

- **관련 SPEC**: 없음 (최초 SPEC)
- **Epic**: MVP Launch
- **예상 노력**: High (8-12주 개발 + 2주 테스트)
- **Labels**: `mobile`, `backend`, `scoring`, `mvp`

---

## 📚 참고 문서

- **Speechace API Documentation**: https://www.speechace.com/api/
- **OpenAI API Documentation**: https://platform.openai.com/docs/
- **React Native Voice**: https://github.com/react-native-voice/voice
- **FastAPI Documentation**: https://fastapi.tiangolo.com/
- **Celery Documentation**: https://docs.celeryproject.org/

---

**작성자**: workflow-spec
**검토자**: 수연
**버전**: 1.0.0
**최종 수정일**: 2026-01-24
