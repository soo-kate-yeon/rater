# TOEFL Speaking Rater - 서비스 사용 가이드

## 개요

TOEFL Speaking 응답에 대한 자동 피드백 생성 시스템의 서비스 레이어 구조입니다.

## 서비스 구조

```
src/services/
├── llm_service.py           # LLM API 통합 (OpenAI GPT-4, Anthropic Claude)
├── language_features.py     # 언어 사용 신호 추출
├── structure_features.py    # 답변 구조 신호 추출
├── feedback_service.py      # 통합 피드백 생성
├── delivery_features.py     # Delivery 신호 추출 (기존)
└── asr_service.py          # Whisper ASR 통합 (기존)
```

## 파이프라인 플로우

```mermaid
graph LR
    A[오디오 파일] --> B[ASR Service]
    B --> C[Transcript + Segments]
    C --> D[Delivery Features]
    C --> E[Language Features]
    C --> F[Structure Features]
    D --> G[Feedback Service]
    E --> G
    F --> G
    G --> H[LLM Service]
    H --> I[FeedbackReport]
```

## 사용 예시

### 1. 전체 피드백 생성 (헬퍼 함수 사용)

```python
from src.services.feedback_service import generate_full_feedback, LLMProvider

# Whisper ASR 결과 (예시)
transcript = "I think online classes are better. Because I can study at home..."

# Delivery features (Whisper segments 기반으로 이미 추출됨)
delivery_features = {
    "duration_sec": 52.5,
    "wpm": 140.0,
    "silence_ratio": 0.15,
    "pause_count": 8,
    "pause_p95_ms": 800,
    "filler_count": 3,
    "asr_clarity_signal": {
        "avg_logprob": -0.25,
        "no_speech_prob": 0.02,
    },
}

# 피드백 생성
feedback_report = await generate_full_feedback(
    task_type="independent",
    prompt="Do you prefer online or in-person classes? Why?",
    transcript=transcript,
    delivery_features_dict=delivery_features,
    llm_provider=LLMProvider.OPENAI,
)

# 결과 사용
print(f"점수 범위: {feedback_report.score_band.min}-{feedback_report.score_band.max}")
print(f"가장 큰 병목: {feedback_report.bottleneck.title}")
```

### 2. 개별 Feature 추출

#### Language Features

```python
from src.services.language_features import extract_language_features

transcript = "I go to school yesterday. He are my friend."

language_features = extract_language_features(transcript)

print(language_features)
# {
#   "error_types": ["시제 불일치", "수일치 오류"],
#   "error_density": 20.0,  # 2 errors / 10 words * 100
#   "lexical_diversity": 0.9,  # TTR
#   "avg_sentence_length": 5.0,
#   "repetition_ratio": 0.2
# }
```

#### Structure Features

```python
from src.services.structure_features import extract_structure_features

transcript = "In my opinion, online classes are better for two reasons. First, they save time..."
prompt = "Do you prefer online or in-person classes?"

structure_features = extract_structure_features(transcript, prompt)

print(structure_features)
# {
#   "prompt_coverage": True,
#   "structure_checklist": {
#     "Intro": True,
#     "Reason1": True,
#     "Example1": False,
#     ...
#   },
#   "coherence_score": 0.67,
#   "specificity_score": 0.5
# }
```

### 3. LLM 서비스 직접 사용

```python
from src.services.llm_service import LLMService, LLMConfig, LLMProvider

# LLM 설정
config = LLMConfig(
    provider=LLMProvider.ANTHROPIC,
    model="claude-3-5-sonnet-20241022",
    temperature=0.3,
    max_retries=3,
)

llm_service = LLMService(config=config)

# 피드백 생성
all_features = {
    "delivery": delivery_features,
    "language": language_features,
    "structure": structure_features,
}

feedback = await llm_service.generate_feedback(
    task_type="independent",
    prompt="Do you prefer online or in-person classes?",
    transcript=transcript,
    features=all_features,
)
```

### 4. Celery Worker에서 사용 (비동기 작업)

```python
from celery import Celery
from src.services.feedback_service import generate_full_feedback

app = Celery("worker", broker="redis://localhost:6379/0")

@app.task
async def generate_feedback_task(job_id: str, task_data: dict):
    """비동기 피드백 생성 작업"""
    
    # Job 상태 업데이트: FEATURE_EXTRACTING
    await update_job_status(job_id, "FEATURE_EXTRACTING")
    
    # 피드백 생성
    feedback_report = await generate_full_feedback(
        task_type=task_data["task_type"],
        prompt=task_data["prompt"],
        transcript=task_data["transcript"],
        delivery_features_dict=task_data["delivery_features"],
    )
    
    # Job 상태 업데이트: DONE
    await update_job_status(job_id, "DONE")
    
    # Report 저장
    await save_report(job_id, feedback_report)
    
    return {"job_id": job_id, "status": "DONE"}
```

## 환경 변수 설정

`.env` 파일에 다음 API 키를 설정하세요:

```bash
# OpenAI API 키 (GPT-4 + Whisper)
OPENAI_API_KEY=sk-...

# Anthropic API 키 (Claude) - 선택사항
ANTHROPIC_API_KEY=sk-ant-...

# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/toefl_rater

# Redis
REDIS_URL=redis://localhost:6379/0
```

## 에러 처리

### 1. API 키 미설정

```python
try:
    feedback = await generate_full_feedback(...)
except ValueError as e:
    print(f"API 키 미설정: {e}")
    # OPENAI_API_KEY 또는 ANTHROPIC_API_KEY 확인
```

### 2. JSON 파싱 실패 (최대 재시도 초과)

```python
try:
    feedback = await llm_service.generate_feedback(...)
except RuntimeError as e:
    print(f"피드백 생성 실패 (재시도 초과): {e}")
    # LLM 응답이 JSON 형식이 아니거나, Pydantic 검증 실패
```

### 3. Pydantic 검증 실패

```python
from pydantic import ValidationError

try:
    delivery_features = DeliveryFeatures(**invalid_data)
except ValidationError as e:
    print(f"Delivery features 검증 실패: {e}")
```

## 테스트

```bash
# pytest로 서비스 테스트
pytest tests/services/test_language_features.py -v
pytest tests/services/test_structure_features.py -v
pytest tests/services/test_llm_service.py -v
pytest tests/services/test_feedback_service.py -v
```

## 참고사항

- **Language Features**: 규칙 기반 오류 감지는 단순화된 버전입니다. 실제로는 NLP 라이브러리 (spaCy, NLTK) 사용 권장
- **Structure Features**: TOEFL 템플릿 감지도 단순화된 패턴 매칭입니다. 실제로는 더 정교한 NLP 모델 필요
- **LLM 서비스**: JSON 모드 강제 출력은 OpenAI만 지원하므로, Anthropic 사용 시 프롬프트에 명시
- **재시도 로직**: 파싱 실패 시 최대 3회 재시도 (기본값)

## 다음 단계

1. Celery Worker에 피드백 생성 작업 통합
2. Job 상태 업데이트 (FEATURE_EXTRACTING → LLM_ANALYZING → SCORING → DONE)
3. Report 테이블에 결과 저장
4. Type Analysis 업데이트 (Q1-Q4 평균 점수)

---

**작성자**: expert-backend  
**생성일**: 2026-01-24  
**버전**: 1.0.0
