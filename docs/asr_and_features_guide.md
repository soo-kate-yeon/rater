# ASR 및 Delivery Features 가이드

TOEFL Speaking Rater의 Whisper ASR 및 Delivery Feature 추출 서비스 구현 가이드입니다.

## 📁 파일 구조

```
src/
├── schemas/
│   └── scoring.py          # ASR 및 Feature 관련 Pydantic 스키마
├── services/
│   ├── asr_service.py      # Whisper ASR 서비스
│   └── delivery_features.py # Delivery Feature 추출 서비스
└── core/
    └── config.py           # Whisper 모델 설정

examples/
└── test_asr_and_features.py # 사용 예제
```

## 🎯 구현 내용

### 1. ASR 서비스 (`asr_service.py`)

**기능:**
- Whisper 모델 Lazy Loading (메모리 효율성)
- 오디오 파일 전사 (영어 전용)
- 타임스탬프 포함 세그먼트 추출
- 명료도 신호 계산 (avg_logprob, no_speech_prob)

**주요 메서드:**
- `transcribe(audio_path)`: 오디오 파일 전사
- `unload_model()`: 모델 메모리 해제

**반환 데이터:**
```python
ASRResult(
    transcript="I think online classes are more effective...",
    segments=[...],  # WhisperSegment 리스트
    language="en",
    avg_logprob=-0.22,
    no_speech_prob=0.02,
    duration_sec=48.5
)
```

### 2. Delivery Feature 추출 서비스 (`delivery_features.py`)

**추출 신호:**
- `duration_sec`: 전체 녹음 길이
- `wpm`: Words Per Minute (분당 단어 수)
- `silence_ratio`: 무음 비율 (침묵>500ms 누적 / 전체 길이)
- `pause_count`: 무음 횟수 (>500ms)
- `pause_p95_ms`: 95th percentile 무음 길이
- `filler_count`: Filler 단어 카운트 (uh, um, like, you know 등)
- `asr_clarity_signal`: ASR 명료도 신호 (avg_logprob 기반)

**해석 규칙:**
- `wpm < 90`: 속도 느림
- `wpm > 180`: 속도 과속
- `silence_ratio > 0.22`: 침묵 많음 (끊김)
- `asr_clarity_signal < -0.5`: 발음 개선 필요

## 🚀 사용법

### 기본 사용 예제

```python
import asyncio
from src.services import get_asr_service, get_delivery_feature_extractor
from src.schemas.scoring import ScoringFeatures
from datetime import datetime, timezone

async def process_audio(audio_path: str):
    # 1. ASR 실행
    asr_service = get_asr_service()
    asr_result = await asr_service.transcribe(audio_path)
    
    # 2. Delivery Feature 추출
    extractor = get_delivery_feature_extractor()
    delivery_signals = extractor.extract(asr_result)
    
    # 3. 통합 Feature 세트 생성
    features = ScoringFeatures(
        asr_result=asr_result,
        delivery_signals=delivery_signals,
        extracted_at=datetime.now(timezone.utc).isoformat()
    )
    
    return features
```

### 테스트 스크립트 실행

```bash
python examples/test_asr_and_features.py /path/to/audio.mp3
```

## ⚙️ 설정

`.env` 파일에서 Whisper 모델 설정:

```bash
WHISPER_MODEL=base          # tiny, base, small, medium, large
WHISPER_DEVICE=cpu          # cpu 또는 cuda
USE_LOCAL_WHISPER=true      # 로컬 Whisper 사용 여부
```

**권장 설정:**
- 개발 환경: `base` (빠른 테스트용)
- 프로덕션: `small` 또는 `medium` (정확도와 속도 균형)

## 📚 참고 문서

- [OpenAI Whisper GitHub](https://github.com/openai/whisper)
- [SPEC-TOEFL-001](../.moai/specs/SPEC-TOEFL-001/spec.md)

---

**작성자**: Alfred (MoAI-ADK)  
**최종 수정일**: 2026-01-24
