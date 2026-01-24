# TOEFL Speaking Rater MVP SPEC (2026)

## 1. 목적과 철학
본 문서는 2026년 기준 TOEFL iBT Speaking(이하 TOEFL SR) 공식 루브릭을 토대로, **Whisper ASR + LLM**만으로 *현실적으로 탐지·분석 가능한 영역*을 선별하고, **채점 정확도보다 유저 가치(설명력 있는 피드백)**에 초점을 맞춘 MVP 사양(SPEC)을 정의한다.

핵심 원칙:
- 정밀 채점 ≠ 초기 유저 가치
- 점수는 *추정치*, 피드백은 *구체적·행동 가능*
- ‘왜 부족한지’를 설명하지 못하는 평가는 실패

---

## 2. 2026 TOEFL Speaking 공식 루브릭 요약
TOEFL SR은 여전히 4개 축을 중심으로 평가된다.

1. **Delivery**
   - 발음 명료도
   - 유창성(속도, 끊김)
   - 억양/강세의 자연스러움

2. **Language Use**
   - 문법 정확성
   - 어휘 다양성/정확성
   - 표현의 적절성

3. **Topic Development**
   - 질문 충실도
   - 아이디어 전개
   - 예시/근거의 명확성

4. **Task Fulfillment (Integrated)**
   - Reading/Listening 핵심 반영
   - 정보 왜곡 여부

본 SPEC은 이 중 **기계적으로 신뢰 가능한 하위 요소만 채택**한다.

---

## 3. Whisper + LLM으로 Detect 가능한 영역 매핑

### 3.1 Delivery (부분 적용)

#### Detect 가능
- 총 발화 시간
- 분당 단어 수(WPM)
- 무음 구간 비율 (예: >500ms 침묵)
- 반복/망설임 표현 (uh, um, you know 등)
- ASR 인식 신뢰도 지표 (avg logprob)

#### Detect 불가 / 제외
- 원어민 기준 발음 정확도
- 음소(phoneme) 단위 오류
- 억양/강세의 미묘한 자연스러움

➡ **해석 전략**
> “발음 점수”가 아니라 **‘명료도 신호’**로 재정의

출력 예:
- 발화는 빠르나(160 WPM) 중간 침묵이 많아 전달력이 끊김
- 특정 구간에서 ASR 인식률 급락 → 또박또박 발음 필요

---

### 3.2 Language Use (강력 적용 가능 영역)

#### Detect 가능
- 문법 오류 유형 분류 (시제, 수일치, 관사 등)
- 문장 길이 분포 (단문/복문 비율)
- 어휘 다양성 지표 (TTR, 고빈도 단어 비율)
- 반복 표현 감지
- LLM 기반 자연성 평가

#### 출력 피드백 포인트
- "의미 전달은 가능하나, 단순 문장 반복으로 고득점 제한"
- "과거 시제 일관성 오류가 빈번"

---

### 3.3 Topic Development (핵심 가치 영역)

#### Detect 가능 (LLM 기반)
- 질문 프롬프트 대응 여부
- 서론 존재 여부
- 이유/근거 구조 (Reason–Example 패턴)
- 논리적 연결어 사용
- 결론 또는 마무리 문장 존재

#### 구조 분석 예시
- Intro: ❌ 없음
- Reason 1: ⭕ 있음
- Example: ❌ 추상적
- Reason 2: ❌ 누락

➡ 이 영역이 **Speechace 대비 핵심 차별점**

---

### 3.4 Integrated Task Fulfillment (조건부 적용)

#### Detect 가능
- Reading 핵심 문장 요약 여부
- Listening 내용 언급 여부
- 동의/대조 관계 인식

#### Detect 한계
- 세부 사실 정확도 100% 검증 불가

➡ 전략:
- “정확성 판단”이 아닌 **‘반영 여부’ 체크리스트화**

---

## 4. 점수 정책 (UX 설계)

### 4.1 점수 표현 방식
- 단일 점수 ❌
- 점수 구간 ⭕

예:
- 추정 점수 범위: **22–25**
- 근거: 구조 점수 높음 / Delivery 불안정

### 4.2 점수보다 앞서는 피드백 구조
1. 이번 답변의 **가장 큰 병목 1가지**
2. 고득점 답변과의 **구조적 차이**
3. 다음 답변에서 **즉시 바꿀 행동 1–2개**

---

## 5. 사용자에게 제공되는 핵심 리포트 구성

1. **요약 진단 (3줄)**
   - 현재 레벨 포지션
   - 가장 큰 감점 요인

2. **Delivery 분석**
   - 속도 / 침묵 / 명료도 신호

3. **Language Use 분석**
   - 반복 오류 TOP 2
   - 어휘/문법 개선 포인트

4. **답변 구조 시각화**
   - 포함 요소 체크리스트

5. **점수 범위 + 이유 설명**

---

## 5A. 개발 관점 워크플로우(End-to-End)

### 5A-1. 전체 시스템 구성(권장)
- **Mobile App**: 녹음, 파일 업로드, 결과 조회, 리포트 렌더링
- **API Server (FastAPI)**: 인증, 업로드 세션 생성, Job 생성/조회, 결과 제공
- **Object Storage (S3/GCS)**: 오디오 원본 저장 (서버 디스크 저장 금지)
- **Queue + Worker**: 비동기 파이프라인 실행(Whisper/Feature/LLM)
- **DB (Postgres)**: Job/결과/피드백/메타데이터
- **Cache (Redis 선택)**: 폴링 최적화, 임시 상태, rate limit

### 5A-2. 사용자 플로우(클라이언트 관점)
1) 유저가 문제(Task) 선택 → 녹음 시작/종료
2) 앱이 `업로드 세션 생성` 요청 → presigned URL 수신
3) 앱이 스토리지로 직접 업로드
4) 앱이 `Job 생성`(audio_key, task_id, prompt, source_text 등) → job_id 수신
5) 앱이 `Job 상태 조회` 폴링(또는 SSE) → 완료 시 결과 다운로드/렌더

### 5A-3. 서버 플로우(시스템 관점)
- API는 **job 생성까지만 동기 처리**
- Whisper/LLM은 **워커에서 비동기 처리**
- 결과는 DB에 저장하고, 앱은 조회로만 접근

---

## 5B. Job 파이프라인 단계 정의(Worker)

### 5B-1. Job 상태 머신
- `QUEUED` → `FETCHING_AUDIO` → `ASR_RUNNING` → `FEATURE_EXTRACTING` → `LLM_ANALYZING` → `SCORING` → `DONE`
- 실패 시: `FAILED` (error_code + error_message + retryable)

권장 재시도 정책:
- 스토리지 fetch 실패: 최대 3회(지수 백오프)
- ASR/LLM 일시 실패: 최대 2회
- 입력 검증 실패(오디오 길이 0 등): 재시도 없음

### 5B-2. 단계별 산출물(Artifacts)
1) **AudioMeta**: duration_ms, sample_rate, codec, size_bytes
2) **ASRResult**: transcript, segments(timestamps), avg_logprob(or confidence), no_speech_prob
3) **AcousticSignals**: silence_ratio, pause_stats, speech_rate_wpm, filler_counts
4) **TextSignals**: grammar_issues, vocab_diversity, repetition, connector_usage
5) **StructureAnalysis**: intro/reasons/examples/conclusion 체크리스트 + 근거 문장 인용
6) **FeedbackReport**: 3줄 요약 + 병목 1개 + 행동 1–2개 + 점수 구간

---

## 5C. Feature 추출 상세(신호 정의)

### 5C-1. Delivery 신호(Whisper/타임스탬프 기반)
- `duration_sec`: 전체 녹음 길이
- `wpm`: 단어수/분
- `silence_ratio`: (무음>500ms 누적) / 전체 길이
- `pause_count`: 무음>500ms 횟수
- `pause_p95_ms`: 상위 95% pause 길이
- `filler_count`: {uh, um, like, you know} 등 카운트
- `asr_clarity_signal`: avg_logprob, no_speech_prob, segment-level drop

해석 규칙(예시):
- wpm < 90: 느림(정보량 부족 위험)
- wpm > 180: 과속(명료도/문법 붕괴 위험)
- silence_ratio > 0.22: 끊김(전달력 저하)
- asr_clarity_signal 낮음: 또박또박/발음 명료도 개선 권고

### 5C-2. Language Use 신호(LLM + 규칙 혼합)
- `error_types`: 시제/수일치/관사/전치사/어순 등 TOP N
- `error_density`: 오류 수 / 100단어
- `lexical_diversity`: TTR(간단), 고빈도 단어 비율
- `complexity`: 평균 문장 길이, 종속절/접속사 사용
- `repetition`: 동일 표현 반복률

### 5C-3. Topic/Structure 신호(LLM)
- `prompt_coverage`: 질문 요구사항 충족 여부(예/아니오 + 근거)
- `structure_checklist`:
  - Intro(요지 한 문장)
  - Reason1
  - Example1
  - Reason2
  - Example2
  - Wrap-up
- `coherence`: 연결어 사용, 논리 점프 탐지
- `specificity`: 추상 표현 비율 vs 구체 사례

### 5C-4. Integrated(통합형) 신호(조건부)
입력으로 source 제공 시(Reading/Listening 텍스트 또는 요약):
- `reading_keypoint_covered` (bool + 인용)
- `listening_keypoint_covered` (bool + 인용)
- `relationship`: agree/disagree/contrast 등
- `distortion_flags`: 명백한 왜곡 가능성(확률적 경고로만)

---

## 5D. LLM 프롬프트/출력 규격(개발용)

### 5D-1. 입력 컨텍스트
- task_type: independent/integrated
- prompt: 문제 텍스트
- transcript: Whisper 결과(원문)
- segments: 타임스탬프 요약(필요 시)
- features: 5C 신호(숫자)
- (optional) source_reading/source_listening: 통합형 자료

### 5D-2. 출력 JSON 스키마(고정)
- `summary_3lines`: [str, str, str]
- `bottleneck`: {title, explanation, evidence_quote}
- `action_items`: [{action, why, how_to, example_sentence?}]
- `structure`: {checklist, missing, suggested_template}
- `language`: {top_errors, improved_sentences}
- `delivery`: {speed_comment, pause_comment, clarity_comment}
- `score_band`: {min, max, rationale}
- `disclaimer`: str

**중요:** LLM 출력은 반드시 JSON-only 모드로 강제(파싱 실패 시 재시도)

---

## 5E. API 설계(초안)

### 5E-1. 업로드/Job
- `POST /v1/uploads/presign`
  - req: {content_type, size_bytes}
  - res: {upload_url, audio_key, expires_at}

- `POST /v1/jobs`
  - req: {audio_key, task_id, task_type, prompt, (optional)source_reading, source_listening}
  - res: {job_id, status}

- `GET /v1/jobs/{job_id}`
  - res: {status, progress(0-100), eta_hint?, created_at, updated_at}

- `GET /v1/jobs/{job_id}/report`
  - res: FeedbackReport(JSON) + 메타

### 5E-2. 운영/디버그(내부)
- `GET /v1/jobs/{job_id}/artifacts` (admin)
- `POST /v1/jobs/{job_id}/retry` (admin)

---

## 5F. 데이터 모델(요약)

### 5F-1. 테이블
- `users` (id, created_at, ...)
- `tasks` (id, type, prompt, source_reading/listening, tags)
- `jobs` (id, user_id, task_id, status, progress, audio_key, error_code, created_at, updated_at)
- `job_artifacts` (job_id, asr_json, features_json, llm_json, version, created_at)
- `reports` (job_id, report_json, score_band_min/max, created_at)

### 5F-2. 버전 관리
- `rubric_version`: 예) "toefl_speaking_2026_v1"
- `pipeline_version`: ASR 모델/프롬프트 변경 시 increment

---

## 5G. 관측성/품질(필수 최소)
- Job 단계별 latency/실패율
- ASR 품질 지표 분포(avg_logprob, no_speech_prob)
- LLM JSON 파싱 실패율
- 유저 리포트 조회률, 재시도율

---

## 5H. MVP 범위(엄격)

포함:
- 녹음 업로드, job 생성/조회
- Whisper 전사 + 기본 Delivery 신호
- LLM 구조/언어 분석 + 행동 아이템 1–2개
- 점수 구간 + 이유

제외:
- 음소 단위 발음 진단
- 실시간 스트리밍 피드백
- 문제은행/학습 콘텐츠 대량

---



## 6. 명시적 한계 고지 (신뢰 설계)

반드시 UI/문구로 고지:
- 본 평가는 실제 TOEFL 점수와 다를 수 있음
- 발음 점수는 원어민 청취 기반이 아님
- 구조/전개 중심의 학습용 분석 도구임

➡ 오히려 신뢰 상승 효과

---

## 7. 향후 확장 포인트 (Speechace 연동 시)

- 발음 세부 점수 보강
- phoneme 기반 훈련 추천
- Delivery 점수 세분화

이 SPEC은 Speechace **대체가 아니라 기반층**으로 설계됨.

---

## 8. 한 줄 결론
> 이 MVP의 목표는 “점수를 맞히는 AI”가 아니라,
> **“유저가 다음 답변에서 무엇을 바꿔야 할지 알게 만드는 AI”다.

