# SPEC-TOEFL-001 구현 계획

## 📌 TAG BLOCK

```
SPEC-ID: SPEC-TOEFL-001
제목: TOEFL Speaking Training 구현 계획
생성일: 2026-01-24
상태: Planned
우선순위: High
```

---

## 🎯 구현 우선순위 및 마일스톤

### Primary Goal (1순위 핵심 기능)

**목표**: 사용자가 모의고사를 수행하고 기본 채점 결과를 받을 수 있는 MVP 완성

#### Milestone 1.1: 백엔드 기반 구조 구축
- ✅ **완료 조건**: FastAPI 서버 실행, PostgreSQL 연결, JWT 인증 작동
- **작업 내용**:
  - FastAPI 프로젝트 초기화 (pyproject.toml, poetry 설정)
  - PostgreSQL 데이터베이스 생성 및 연결 (SQLAlchemy async)
  - Users, Exams, Questions, Recordings, Scoring_Results 테이블 생성
  - JWT 기반 인증 API (`/api/auth/register`, `/api/auth/login`) 구현
  - Pydantic 스키마 정의 (UserCreate, UserLogin, Token)

#### Milestone 1.2: React Native 앱 초기화 및 기본 화면 구성
- ✅ **완료 조건**: 3개 메인 페이지 네비게이션 작동, 로그인 화면 기능 구현
- **작업 내용**:
  - React Native 프로젝트 생성 (`npx create-react-native-app`)
  - React Navigation 설정 (Bottom Tab Navigator)
  - 3개 메인 페이지 스켈레톤 생성:
    - `ExamListScreen`: 모의고사 목록
    - `TypeAnalysisScreen`: Q1-Q4 평균 점수 차트
    - `PracticeScreen`: 녹음 버튼 및 히스토리 탭
  - 로그인/회원가입 화면 구현 (AsyncStorage로 JWT 저장)
  - Axios 설정 (Base URL, JWT 인터셉터)

#### Milestone 1.3: 녹음 기능 및 파일 업로드
- ✅ **완료 조건**: 사용자가 45-60초 녹음 후 백엔드에 업로드 성공
- **작업 내용**:
  - React Native Voice 또는 Expo Audio 통합
  - 녹음 UI 구현 (Record/Stop 버튼, 타이머, 시각적 피드백)
  - 녹음 파일 로컬 저장 (캐시 디렉토리)
  - `POST /api/recordings` 엔드포인트 구현 (multipart/form-data)
  - S3 또는 GCS에 파일 업로드 (boto3 또는 google-cloud-storage)
  - 파일 검증 로직 (형식, 크기, 길이) 추가

#### Milestone 1.4: 오디오 전처리 파이프라인
- ✅ **완료 조건**: 업로드된 오디오가 ffmpeg로 정규화되고 VAD 처리 완료
- **작업 내용**:
  - Celery + Redis 설정 (docker-compose.yml)
  - `process_audio` Celery Task 생성
  - ffmpeg 명령어 실행 (Python subprocess 또는 pydub)
  - webrtcvad를 통한 음성 구간 탐지 및 무음 제거
  - 전처리된 파일을 S3에 저장 (원본과 별도 경로)

#### Milestone 1.5: Whisper ASR 통합
- ✅ **완료 조건**: Whisper ASR이 transcript + timestamps + 신뢰도 지표를 반환하고 job_artifacts에 저장
- **작업 내용**:
  - OpenAI Whisper API 또는 로컬 Whisper 모델 (faster-whisper) 선택 및 설정
  - `run_whisper_asr` 함수 구현:
    - 입력: S3 오디오 파일 경로
    - 출력: transcript, segments (타임스탬프), avg_logprob, no_speech_prob
  - ASR 결과를 job_artifacts.asr_json에 저장
  - ASR 품질 신호 계산:
    - avg_logprob: 평균 로그 확률 (인식 신뢰도)
    - no_speech_prob: 무음 구간 확률
    - segment-level drop: 신뢰도 급락 구간 탐지
  - 오류 처리 (API 타임아웃, 인증 실패, 오디오 형식 불일치)
  - Job 상태 업데이트: FETCHING_AUDIO → ASR_RUNNING → FEATURE_EXTRACTING

#### Milestone 1.6: Feature 추출 파이프라인
- ✅ **완료 조건**: Delivery/Language/Structure 신호가 추출되어 job_artifacts.features_json에 저장
- **작업 내용**:
  - **Delivery 신호 추출** (`extract_delivery_features` 함수):
    - duration_sec: Whisper segments 기반 계산
    - wpm (words per minute): transcript 단어 수 / 시간
    - silence_ratio: segments 간 gap >500ms 누적 / 전체 시간
    - pause_count: >500ms gap 횟수
    - pause_p95_ms: 95th percentile pause 길이
    - filler_count: {uh, um, like, you know} 정규표현식 카운트
    - asr_clarity_signal: avg_logprob, no_speech_prob 통합
  - **Language 신호 추출** (`extract_language_features` 함수):
    - error_types: LanguageTool 또는 규칙 기반 문법 검사 (시제, 수일치, 관사, 전치사)
    - error_density: 오류 수 / 100단어
    - lexical_diversity: TTR (unique words / total words)
    - complexity: 평균 문장 길이, 종속절 탐지 (spaCy)
    - repetition: n-gram 반복 비율
  - **Structure 신호 추출** (`extract_structure_features` 함수):
    - prompt_coverage: 질문 키워드 매칭 (boolean + 근거 문장)
    - coherence: 연결어 사용 빈도 (however, therefore, for example)
    - specificity: 추상 표현 vs 구체 표현 비율
  - features_json 저장 및 Job 상태 업데이트: FEATURE_EXTRACTING → LLM_ANALYZING

#### Milestone 1.7: LLM 분석 및 리포트 생성
- ✅ **완료 조건**: LLM이 FeedbackReport JSON을 반환하고 reports 테이블에 저장
- **작업 내용**:
  - **LLM 프롬프트 설계**:
    - 입력 컨텍스트: task_type, prompt, transcript, segments, features (Milestone 1.6 결과)
    - 출력 스키마: summary_3lines, bottleneck, action_items, structure, language, delivery, score_band, disclaimer
    - JSON 모드 강제 (OpenAI `response_format={"type": "json_object"}` 또는 Anthropic function calling)
  - `analyze_with_llm` 함수 구현:
    - OpenAI GPT-4 또는 Anthropic Claude 3.5 Sonnet 호출
    - JSON 파싱 실패 시 최대 2회 재시도
    - Timeout 30초 설정
  - **리포트 생성 및 저장**:
    - LLM 응답을 job_artifacts.llm_json에 저장
    - reports 테이블에 report_json, score_band_min/max 저장
    - Job 상태 업데이트: LLM_ANALYZING → SCORING → DONE
  - **API 엔드포인트 구현**:
    - `GET /v1/jobs/{job_id}`: 상태 조회 (progress 포함)
    - `GET /v1/jobs/{job_id}/report`: FeedbackReport 조회
  - **React Native 결과 화면 구현**:
    - 요약 진단 (3줄)
    - 가장 큰 병목 1가지 (제목 + 설명 + 증거)
    - 행동 아이템 (1-2개, 구체적 예시 포함)
    - 구조 체크리스트 시각화
    - 언어 사용 분석 (TOP 2 오류 + 개선 문장)
    - Delivery 분석 (속도/침묵/명료도)
    - 점수 범위 (min-max + 근거)
    - 면책 고지

---

### Secondary Goal (2순위 확장 기능)

**목표**: 사용자 경험 개선 및 학습 히스토리 관리

#### Milestone 2.1: Practice History 기능
- ✅ **완료 조건**: 사용자가 과거 녹음 목록 조회, 재생, transcript 확인 가능
- **작업 내용**:
  - `GET /api/practice/history` 엔드포인트 구현 (페이지네이션)
  - `GET /api/practice/{recording_id}/transcript` 엔드포인트 구현
  - Practice History 탭 UI 구현 (FlatList, 날짜별 그룹화)
  - 오디오 재생 기능 (Expo Audio `Sound.createAsync`)
  - Transcript 표시 화면

#### Milestone 2.2: 모의고사 상세 리포트
- ✅ **완료 조건**: Exam 페이지에서 특정 모의고사 클릭 시 Q1-Q4 결과 요약 표시
- **작업 내용**:
  - `GET /api/exams/{exam_id}/results` 엔드포인트 구현
  - 상세 리포트 화면 구성:
    - 각 문제별 점수
    - 전체 평균 점수
    - 약점 문제 하이라이트
  - 진행률 표시 (예: 4문제 중 3문제 완료)

#### Milestone 2.3: 알림 및 실시간 상태 업데이트
- ✅ **완료 조건**: 채점 완료 시 Push Notification 전송, 앱 내 실시간 상태 업데이트
- **작업 내용**:
  - Firebase Cloud Messaging (FCM) 또는 Expo Push Notifications 설정
  - Celery Task 완료 시 알림 전송
  - 앱 내 WebSocket 연결 (선택사항, FastAPI WebSocket)
  - 상태바에 채점 진행 중 표시

---

### Final Goal (3순위 최적화 및 안정성)

**목표**: 프로덕션 배포 준비 및 성능 최적화

#### Milestone 3.1: 에러 처리 및 로깅
- ✅ **완료 조건**: 모든 주요 에러 케이스에 대한 사용자 친화적 메시지 표시, 로그 수집
- **작업 내용**:
  - FastAPI 전역 예외 핸들러 추가
  - 구조화된 로깅 (structlog 또는 Python logging)
  - Sentry 또는 LogRocket 통합 (에러 트래킹)
  - React Native 에러 바운더리 (Error Boundary Component)

#### Milestone 3.2: 성능 최적화
- ✅ **완료 조건**: API 응답 시간 P95 < 500ms, 앱 로딩 시간 < 2초
- **작업 내용**:
  - PostgreSQL 인덱스 추가 (user_id, exam_id, recording_id)
  - Redis 캐싱 (Type Analysis 평균 점수)
  - React Native 이미지 최적화 및 코드 스플리팅
  - Celery Worker 수 조정 (동시 처리 작업 수)

#### Milestone 3.3: 보안 강화
- ✅ **완료 조건**: OWASP Top 10 체크리스트 통과, 보안 테스트 완료
- **작업 내용**:
  - JWT 토큰 만료 시간 설정 (Access: 15분, Refresh: 7일)
  - HTTPS 강제 (프로덕션 환경)
  - S3 버킷 접근 권한 최소화 (IAM Policy)
  - SQL Injection 방지 (SQLAlchemy parameterized query)
  - API Rate Limiting (slowapi)

#### Milestone 3.4: 테스트 작성
- ✅ **완료 조건**: 백엔드 테스트 커버리지 > 85%, 주요 React Native 컴포넌트 단위 테스트
- **작업 내용**:
  - pytest + pytest-asyncio 설정
  - FastAPI 엔드포인트 통합 테스트 (TestClient)
  - Celery Task 단위 테스트 (Mock Speechace/LLM API)
  - React Native Jest + React Testing Library 설정
  - 주요 화면 스냅샷 테스트

---

## 🛠️ 기술 스택 명세

### Frontend (React Native)

| 라이브러리 | 버전 | 용도 |
|-----------|------|------|
| **React Native** | 0.73+ (최신 안정) | 크로스 플랫폼 모바일 앱 프레임워크 |
| **React Navigation** | v6 | 페이지 라우팅 및 네비게이션 |
| **React Native Voice** | v3.2+ | 음성 녹음 (iOS/Android) |
| **Expo Audio** | latest | 오디오 재생 및 녹음 관리 |
| **Axios** | latest | HTTP 클라이언트 (API 호출) |
| **AsyncStorage** | latest | 로컬 데이터 저장 (JWT 토큰) |
| **react-native-chart-kit** | latest | 차트 시각화 (Type Analysis) |
| **React Native Paper** | latest (선택) | Material Design 컴포넌트 |

**설치 명령어**:
```bash
npx create-react-native-app rater-mobile
cd rater-mobile
npm install @react-navigation/native @react-navigation/bottom-tabs
npm install @react-native-voice/voice expo-av axios @react-native-async-storage/async-storage
npm install react-native-chart-kit react-native-paper
```

---

### Backend (FastAPI)

| 라이브러리 | 버전 | 용도 |
|-----------|------|------|
| **FastAPI** | 0.115+ | 비동기 웹 프레임워크 |
| **Uvicorn** | latest | ASGI 서버 |
| **SQLAlchemy** | 2.0+ | ORM (async 지원) |
| **asyncpg** | latest | PostgreSQL async 드라이버 |
| **Pydantic** | v2.9+ | 데이터 검증 및 스키마 |
| **PyJWT** | latest | JWT 토큰 생성 및 검증 |
| **Celery** | latest | 비동기 작업 큐 |
| **Redis** | latest | Celery 브로커 및 캐싱 |
| **boto3** | latest | AWS S3 연동 (파일 저장) |
| **httpx** | latest | 비동기 HTTP 클라이언트 (Speechace/LLM API) |
| **python-multipart** | latest | 파일 업로드 지원 |
| **pydub** | latest | 오디오 처리 (ffmpeg wrapper) |
| **webrtcvad** | latest | Voice Activity Detection |
| **pytest** | latest | 테스트 프레임워크 |
| **pytest-asyncio** | latest | 비동기 테스트 지원 |

**pyproject.toml**:
```toml
[tool.poetry]
name = "rater-backend"
version = "0.1.0"
description = "TOEFL Speaking Training Backend"
python = "^3.11"

[tool.poetry.dependencies]
fastapi = "^0.115.0"
uvicorn = {extras = ["standard"], version = "^0.30.0"}
sqlalchemy = "^2.0.0"
asyncpg = "^0.29.0"
pydantic = "^2.9.0"
pyjwt = "^2.9.0"
celery = "^5.4.0"
redis = "^5.0.0"
boto3 = "^1.35.0"  # AWS S3 (또는 google-cloud-storage for GCS)
httpx = "^0.27.0"
python-multipart = "^0.0.9"

# Whisper ASR
openai = "^1.12.0"  # OpenAI Whisper API 사용 시
faster-whisper = "^1.0.0"  # 로컬 Whisper 사용 시 (GPU 권장)

# Feature 추출
language-tool-python = "^2.8.0"  # 문법 검사
spacy = "^3.7.0"  # 문장 파싱, 품사 태깅
nltk = "^3.8.0"  # TTR, n-gram 분석
numpy = "^1.26.0"
pandas = "^2.2.0"

# LLM API
anthropic = "^0.18.0"  # Anthropic Claude API (선택)

[tool.poetry.group.dev.dependencies]
pytest = "^8.3.0"
pytest-asyncio = "^0.24.0"
pytest-mock = "^3.12.0"
ruff = "^0.6.0"
black = "^24.0.0"
```

**설치 명령어**:
```bash
poetry init
poetry add fastapi uvicorn[standard] sqlalchemy asyncpg pydantic pyjwt celery redis boto3 httpx python-multipart
poetry add openai faster-whisper language-tool-python spacy nltk numpy pandas anthropic
poetry add --group dev pytest pytest-asyncio pytest-mock ruff black

# spaCy 모델 다운로드
python -m spacy download en_core_web_sm

# NLTK 데이터 다운로드
python -m nltk.downloader punkt averaged_perceptron_tagger
```

---

### Database (PostgreSQL)

| 항목 | 명세 |
|------|------|
| **버전** | PostgreSQL 15+ |
| **호스팅** | AWS RDS, Google Cloud SQL, 또는 로컬 Docker |
| **Extensions** | `uuid-ossp` (UUID 생성) |
| **Connection Pool** | SQLAlchemy `create_async_engine` (pool_size=20, max_overflow=10) |

**Docker Compose 설정**:
```yaml
version: '3.8'
services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: rater
      POSTGRES_USER: rater_user
      POSTGRES_PASSWORD: secure_password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7
    ports:
      - "6379:6379"

volumes:
  postgres_data:
```

---

### Audio Processing

| 도구 | 버전 | 용도 |
|------|------|------|
| **ffmpeg** | 4.4+ | 오디오 정규화 (샘플링 레이트, 비트레이트 조정) |
| **webrtcvad** | 2.0+ | 음성 구간 탐지 (Voice Activity Detection) |

**ffmpeg 명령어 예시**:
```bash
ffmpeg -i input.mp3 -ar 16000 -ac 1 -b:a 128k output.mp3
```

---

### Scoring Integration

#### Whisper ASR
- **Option 1: OpenAI Whisper API**
  - Endpoint: `https://api.openai.com/v1/audio/transcriptions`
  - Model: `whisper-1`
  - Input: 오디오 파일 (multipart/form-data)
  - Output: JSON with `text`, `segments` (타임스탬프)
  - 비용: $0.006/분

- **Option 2: 로컬 Whisper (faster-whisper 권장)**
  - Library: `faster-whisper` (CTranslate2 기반, 4배 빠름)
  - Model: `whisper-large-v3` 또는 `whisper-medium`
  - GPU 권장: NVIDIA GPU (CUDA 지원)
  - 장점: API 비용 없음, 데이터 프라이버시
  - 단점: GPU 인프라 필요

- **Output Format** (공통):
  ```json
  {
    "text": "I think the best way to...",
    "segments": [
      {"start": 0.0, "end": 2.5, "text": "I think", "avg_logprob": -0.3, "no_speech_prob": 0.01},
      {"start": 2.5, "end": 5.0, "text": "the best way to", "avg_logprob": -0.25, "no_speech_prob": 0.02}
    ],
    "language": "en"
  }
  ```

#### Feature 추출 라이브러리
- **LanguageTool**: 문법 검사 (시제, 수일치, 관사 오류)
  - Python wrapper: `language-tool-python`
- **spaCy**: 문장 파싱, 종속절 탐지, 품사 태깅
  - Model: `en_core_web_sm`
- **NLTK**: TTR 계산, n-gram 반복 분석
- **NumPy/Pandas**: 통계 계산 (pause percentile, silence ratio)

#### LLM API
- **Option 1: OpenAI GPT-4**
  - Endpoint: `https://api.openai.com/v1/chat/completions`
  - Model: `gpt-4-turbo` 또는 `gpt-4o`
  - JSON 모드: `response_format={"type": "json_object"}`
  - 비용: ~$0.03/1K tokens (input), ~$0.06/1K tokens (output)

- **Option 2: Anthropic Claude**
  - Endpoint: `https://api.anthropic.com/v1/messages`
  - Model: `claude-3-5-sonnet-20241022`
  - JSON 강제: Tool use (function calling)
  - 장점: 더 긴 컨텍스트 (200K 토큰), 안정적 JSON 출력
  - 비용: ~$0.003/1K tokens (input), ~$0.015/1K tokens (output)

**권장 구성**: Whisper (로컬) + Claude 3.5 Sonnet (비용 효율적)

---

## 🏗️ 아키텍처 설계

### 시스템 아키텍처 다이어그램

```
[React Native App]
       |
       | 1. POST /v1/uploads/presign (presigned URL 요청)
       v
[FastAPI Backend] -----> [PostgreSQL]
       |                      |
       | 2. presigned URL     v
       v                  [Users, Exams, Tasks,
[React Native App]       Jobs, Job_Artifacts, Reports]
       |
       | 3. 직접 업로드 (presigned URL 사용)
       v
[S3/GCS Storage] <------ [Audio Files]
       |
       | 4. POST /v1/jobs (Job 생성 요청)
       v
[FastAPI Backend] -----> [Celery Queue (Redis)]
       |                      |
       | 5. Job 생성          v
       v              [Celery Workers]
[PostgreSQL Jobs]              |
       ^                       |
       |                       v
       +---------- 6. Job 상태 업데이트 (QUEUED → DONE)
                               |
                               v
                    [파이프라인 단계 실행]
                               |
                               +-----> FETCHING_AUDIO: S3에서 다운로드
                               |
                               +-----> ASR_RUNNING: Whisper ASR 실행
                               |          └─> job_artifacts.asr_json 저장
                               |
                               +-----> FEATURE_EXTRACTING:
                               |          └─> Delivery/Language/Structure 신호 추출
                               |          └─> job_artifacts.features_json 저장
                               |
                               +-----> LLM_ANALYZING:
                               |          └─> LLM API 호출 (GPT-4/Claude)
                               |          └─> job_artifacts.llm_json 저장
                               |
                               +-----> SCORING:
                               |          └─> reports 테이블에 리포트 저장
                               |
                               +-----> DONE
                                      └─> Push Notification 전송

[React Native App] <---- 7. GET /v1/jobs/{job_id} (폴링으로 상태 조회)
                    └─> 8. GET /v1/jobs/{job_id}/report (결과 다운로드)
```

### 채점 워크플로우 상세 (클라이언트 → 서버)

**클라이언트 플로우**:
1. **업로드 세션 생성**: `POST /v1/uploads/presign` → presigned URL 수신
2. **S3 직접 업로드**: presigned URL로 오디오 파일 업로드 (서버 부하 감소)
3. **Job 생성**: `POST /v1/jobs` (audio_key, task_id, prompt 전달) → job_id 수신
4. **상태 폴링**: `GET /v1/jobs/{job_id}` 2초마다 호출 (또는 SSE)
5. **결과 조회**: status = DONE 확인 후 `GET /v1/jobs/{job_id}/report`

**서버 플로우** (Celery Worker):
1. **QUEUED**: Job 레코드 생성, Celery Task 등록
2. **FETCHING_AUDIO**: S3에서 오디오 다운로드, AudioMeta 추출
3. **ASR_RUNNING**: Whisper 실행 (transcript + segments + 신뢰도 지표)
4. **FEATURE_EXTRACTING**:
   - Delivery 신호: wpm, silence_ratio, pause_count, filler_count, asr_clarity_signal
   - Language 신호: error_types, error_density, lexical_diversity, complexity, repetition
   - Structure 신호: prompt_coverage, coherence, specificity
5. **LLM_ANALYZING**:
   - LLM 프롬프트 생성 (task_type, prompt, transcript, features)
   - LLM API 호출 (JSON 모드 강제)
   - FeedbackReport 파싱 (summary_3lines, bottleneck, action_items, structure, language, delivery, score_band)
6. **SCORING**: reports 테이블에 리포트 저장, score_band_min/max 인덱싱
7. **DONE**: Type Analysis 업데이트, Push Notification 전송

---

## 📦 리소스 요구사항

### 개발 환경
- **개발자 수**: 1-2명 (풀스택 또는 프론트엔드 1명 + 백엔드 1명)
- **개발 머신**: macOS (React Native iOS 빌드) 또는 Windows/Linux (Android 빌드)
- **필수 도구**:
  - Node.js 18+
  - Python 3.11+
  - Docker Desktop
  - Xcode (iOS 개발 시)
  - Android Studio (Android 개발 시)

### 클라우드 리소스 (프로덕션)
- **FastAPI 서버**: AWS EC2 t3.medium (2 vCPU, 4GB RAM) 또는 Google Cloud Run
- **PostgreSQL**: AWS RDS db.t3.small (2 vCPU, 2GB RAM)
- **Redis**: AWS ElastiCache t3.micro (1 vCPU, 0.5GB RAM)
- **S3 Storage**: 100GB (예상 사용자 1000명 × 100 녹음 × 1MB/파일)
- **Celery Worker**: AWS EC2 t3.small × 2대 (동시 채점 처리)

### API 비용 (월간 예상, 사용자 1000명 기준)
- **Speechace API**: $0.02/request × 10,000 requests = $200
- **OpenAI GPT-4**: $0.03/1K tokens × 500 tokens × 10,000 requests = $150
- **Total API Cost**: ~$350/월

---

## ⚠️ 리스크 분석 및 대응 전략

### 리스크 1: Whisper ASR 응답 지연 또는 실패
- **확률**: Low (로컬 배포 시), Medium (OpenAI API 시)
- **영향도**: High (채점 불가)
- **대응**:
  - **로컬 Whisper 사용 시**: GPU 메모리 부족 모니터링, 동시 처리 제한
  - **OpenAI API 사용 시**: Timeout 설정 (60초), Retry 로직 (최대 2회)
  - ASR 실패 시 사용자에게 "음성 인식 실패, 다시 시도해주세요" 메시지
  - **대안**: 로컬 Whisper + OpenAI API 하이브리드 (로컬 실패 시 API fallback)

### 리스크 2: LLM API 비용 초과
- **확률**: Medium
- **영향도**: Medium (예산 초과)
- **대응**:
  - 프롬프트 토큰 수 최적화 (500 토큰 이하로 유지)
  - GPT-3.5-turbo로 다운그레이드 (비용 70% 절감)
  - 월간 API 사용량 모니터링 (CloudWatch Alarm)
  - **대안**: Claude 3 Haiku (더 저렴한 모델)

### 리스크 3: React Native 네이티브 모듈 호환성 문제
- **확률**: Medium
- **영향도**: High (녹음 기능 불안정)
- **대응**:
  - 초기 단계에서 iOS/Android 실기기 테스트
  - React Native Voice 대신 Expo Audio 사용 (더 안정적)
  - 커뮤니티 이슈 트래커 모니터링
  - **대안**: 녹음 기능을 웹뷰로 구현 (MediaRecorder API)

### 리스크 4: PostgreSQL 쿼리 성능 저하
- **확률**: Low
- **영향도**: Medium (Type Analysis 로딩 지연)
- **대응**:
  - 초기 설계 단계에서 인덱스 추가 (`user_id`, `question_id`)
  - 복잡한 집계 쿼리는 Redis 캐싱 (TTL 1시간)
  - `EXPLAIN ANALYZE`로 쿼리 최적화
  - **대안**: 집계 결과를 별도 테이블에 미리 계산 (Materialized View)

### 리스크 5: 오디오 전처리 시간 초과
- **확률**: Low
- **영향도**: Medium (사용자 대기 시간 증가)
- **대응**:
  - ffmpeg 명령어 최적화 (불필요한 옵션 제거)
  - Celery Worker 수 증가 (2대 → 4대)
  - 전처리 진행 상태를 사용자에게 표시 ("처리 중... 예상 시간 10초")
  - **대안**: 전처리를 클라이언트에서 수행 (React Native ffmpeg 라이브러리)

---

## 📊 성공 지표 (KPI)

### 기술 지표
- **API 응답 시간**: P95 < 500ms, P99 < 1000ms
- **채점 완료 시간**: 업로드부터 결과 표시까지 < 20초
- **앱 크래시율**: < 1%
- **백엔드 테스트 커버리지**: > 85%

### 사용자 지표
- **일일 활성 사용자(DAU)**: > 100명 (MVP 출시 1개월 후)
- **모의고사 완료율**: > 70% (시작한 사용자 중 4문제 모두 완료)
- **재방문율**: > 50% (주 2회 이상 앱 사용)

---

## 🚀 다음 단계

1. ✅ **SPEC-TOEFL-001 승인 대기**: 수연님의 검토 및 피드백
2. **기술 스택 확정**: 대안 기술 선택 (예: Anthropic Claude vs OpenAI GPT-4)
3. **개발 환경 설정**: Docker Compose, Poetry, React Native 프로젝트 초기화
4. **Milestone 1.1 시작**: FastAPI 백엔드 기반 구조 구축

---

**작성자**: workflow-spec
**검토자**: 수연
**버전**: 1.0.0
**최종 수정일**: 2026-01-24
