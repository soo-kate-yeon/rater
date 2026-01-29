"""ASR 및 Feature 추출 테스트 예제

Usage:
    python examples/test_asr_and_features.py /path/to/audio.mp3
"""

import asyncio
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

from src.schemas.scoring import ScoringFeatures
from src.services import get_asr_service, get_delivery_feature_extractor


async def test_asr_and_features(audio_path: str) -> None:
    """
    ASR 및 Delivery Feature 추출을 테스트합니다.

    Args:
        audio_path: 오디오 파일 경로
    """
    print(f"🎤 오디오 파일 처리 시작: {audio_path}\n")

    # 1. ASR 서비스 초기화
    asr_service = get_asr_service()
    print("✅ ASR 서비스 초기화 완료")

    # 2. Whisper 전사 실행
    print("\n📝 Whisper ASR 실행 중...")
    asr_result = await asr_service.transcribe(audio_path)

    print(f"  - Transcript: {asr_result.transcript[:100]}...")
    print(f"  - 세그먼트 수: {len(asr_result.segments)}")
    print(f"  - 감지된 언어: {asr_result.language}")
    print(f"  - 평균 로그 확률: {asr_result.avg_logprob:.3f}")
    print(f"  - 무음 확률: {asr_result.no_speech_prob:.3f}")
    print(f"  - 전체 길이: {asr_result.duration_sec:.2f}초")

    # 3. Delivery Feature 추출
    print("\n📊 Delivery Feature 추출 중...")
    extractor = get_delivery_feature_extractor()
    delivery_signals = extractor.extract(asr_result)

    print(f"  - 분당 단어 수 (WPM): {delivery_signals.wpm:.1f}")
    print(f"  - 무음 비율: {delivery_signals.silence_ratio:.1%}")
    print(f"  - 무음 횟수 (>500ms): {delivery_signals.pause_count}")
    print(f"  - 95th percentile 무음 길이: {delivery_signals.pause_p95_ms:.1f}ms")
    print(f"  - Filler 카운트: {delivery_signals.filler_count}")
    print(f"  - ASR 명료도 신호: {delivery_signals.asr_clarity_signal:.3f}")
    print(f"\n💬 해석: {delivery_signals.interpretation}")

    # 4. 전체 Feature 세트 생성
    scoring_features = ScoringFeatures(
        asr_result=asr_result,
        delivery_signals=delivery_signals,
        extracted_at=datetime.now(UTC).isoformat(),
    )

    # 5. JSON 출력 (job_artifacts.features_json에 저장될 형태)
    print("\n📦 최종 JSON 출력:")
    print("-" * 80)
    print(json.dumps(scoring_features.model_dump(), indent=2, ensure_ascii=False))

    print("\n✅ 처리 완료!")


def main() -> None:
    """메인 함수"""
    if len(sys.argv) < 2:
        print("Usage: python examples/test_asr_and_features.py /path/to/audio.mp3")
        sys.exit(1)

    audio_path = sys.argv[1]
    if not Path(audio_path).exists():
        print(f"❌ 오디오 파일을 찾을 수 없습니다: {audio_path}")
        sys.exit(1)

    asyncio.run(test_asr_and_features(audio_path))


if __name__ == "__main__":
    main()
