"""Delivery Feature 추출 서비스"""

import logging
import re
from typing import Optional

import numpy as np

from src.schemas.scoring import ASRResult, DeliverySignals, WhisperSegment

logger = logging.getLogger(__name__)

# Filler 단어 목록 (소문자)
FILLER_WORDS = {"uh", "um", "like", "you know", "well", "so", "actually", "basically"}

# 무음 기준 (밀리초)
SILENCE_THRESHOLD_MS = 500


class DeliveryFeatureExtractor:
    """Delivery 신호 추출기"""

    def __init__(self) -> None:
        """추출기 초기화"""
        pass

    def extract(self, asr_result: ASRResult) -> DeliverySignals:
        """
        ASR 결과에서 Delivery 신호를 추출합니다.

        Args:
            asr_result: Whisper ASR 결과

        Returns:
            DeliverySignals: 추출된 Delivery 신호

        Raises:
            ValueError: ASR 결과가 유효하지 않을 때
        """
        if not asr_result.segments:
            raise ValueError("ASR 결과에 세그먼트가 없습니다")

        logger.info(f"Extracting delivery features from {len(asr_result.segments)} segments")

        # 1. duration_sec: 전체 녹음 길이
        duration_sec = asr_result.duration_sec

        # 2. wpm: Words Per Minute
        word_count = self._count_words(asr_result.transcript)
        wpm = (word_count / duration_sec) * 60 if duration_sec > 0 else 0.0

        # 3. silence_ratio, pause_count, pause_p95_ms: 무음 분석
        pauses_ms = self._extract_pauses(asr_result.segments)
        silence_ratio = self._calculate_silence_ratio(pauses_ms, duration_sec)
        pause_count = len(pauses_ms)
        pause_p95_ms = float(np.percentile(pauses_ms, 95)) if pauses_ms else 0.0

        # 4. filler_count: Filler 단어 카운트
        filler_count = self._count_fillers(asr_result.transcript)

        # 5. asr_clarity_signal: ASR 명료도 신호 (avg_logprob)
        asr_clarity_signal = asr_result.avg_logprob

        # 6. interpretation: 해석 생성
        interpretation = self._generate_interpretation(
            wpm=wpm,
            silence_ratio=silence_ratio,
            asr_clarity_signal=asr_clarity_signal,
        )

        delivery_signals = DeliverySignals(
            duration_sec=duration_sec,
            wpm=round(wpm, 1),
            silence_ratio=round(silence_ratio, 3),
            pause_count=pause_count,
            pause_p95_ms=round(pause_p95_ms, 1),
            filler_count=filler_count,
            asr_clarity_signal=round(asr_clarity_signal, 3),
            interpretation=interpretation,
        )

        logger.info(
            f"Delivery features extracted: wpm={wpm:.1f}, "
            f"silence_ratio={silence_ratio:.3f}, "
            f"pause_count={pause_count}, "
            f"filler_count={filler_count}"
        )
        return delivery_signals

    def _count_words(self, text: str) -> int:
        """
        텍스트에서 단어 개수를 카운트합니다.

        Args:
            text: 전사된 텍스트

        Returns:
            int: 단어 개수
        """
        # 알파벳 단어만 카운트 (구두점 제거)
        words = re.findall(r"\b[a-zA-Z]+\b", text.lower())
        return len(words)

    def _extract_pauses(self, segments: list[WhisperSegment]) -> list[float]:
        """
        세그먼트 간 무음 구간을 추출합니다.

        Args:
            segments: Whisper 세그먼트 리스트

        Returns:
            List[float]: 무음 구간 길이 목록 (밀리초, >500ms만)
        """
        pauses_ms: list[float] = []

        for i in range(len(segments) - 1):
            current_end = segments[i].end
            next_start = segments[i + 1].start
            pause_sec = next_start - current_end

            # 무음 기준 (500ms) 이상인 경우만 포함
            if pause_sec > (SILENCE_THRESHOLD_MS / 1000):
                pauses_ms.append(pause_sec * 1000)  # 초 → 밀리초 변환

        return pauses_ms

    def _calculate_silence_ratio(self, pauses_ms: list[float], duration_sec: float) -> float:
        """
        무음 비율을 계산합니다.

        Args:
            pauses_ms: 무음 구간 목록 (밀리초)
            duration_sec: 전체 오디오 길이 (초)

        Returns:
            float: 무음 비율 (0.0 ~ 1.0)
        """
        if duration_sec <= 0:
            return 0.0

        total_silence_ms = sum(pauses_ms)
        total_silence_sec = total_silence_ms / 1000
        silence_ratio = total_silence_sec / duration_sec

        return min(silence_ratio, 1.0)  # 최대 1.0으로 제한

    def _count_fillers(self, text: str) -> int:
        """
        Filler 단어를 카운트합니다.

        Args:
            text: 전사된 텍스트

        Returns:
            int: Filler 카운트
        """
        text_lower = text.lower()
        filler_count = 0

        # 단순 단어 매칭 (정규식 사용)
        for filler in FILLER_WORDS:
            # 단어 경계를 고려한 매칭
            pattern = r"\b" + re.escape(filler) + r"\b"
            matches = re.findall(pattern, text_lower)
            filler_count += len(matches)

        return filler_count

    def _generate_interpretation(
        self,
        wpm: float,
        silence_ratio: float,
        asr_clarity_signal: float,
    ) -> str:
        """
        해석 규칙을 적용하여 해석 문자열을 생성합니다.

        해석 규칙:
        - wpm < 90: 느림
        - wpm > 180: 과속
        - silence_ratio > 0.22: 끊김
        - asr_clarity_signal < -0.5: 발음 개선 필요

        Args:
            wpm: 분당 단어 수
            silence_ratio: 무음 비율
            asr_clarity_signal: ASR 명료도 신호

        Returns:
            str: 해석 결과
        """
        parts: list[str] = []

        # 속도 평가
        if wpm < 90:
            parts.append(f"속도 느림 ({wpm:.0f} WPM)")
        elif wpm > 180:
            parts.append(f"속도 과속 ({wpm:.0f} WPM)")
        else:
            parts.append(f"속도 적절 ({wpm:.0f} WPM)")

        # 침묵 평가
        silence_percent = silence_ratio * 100
        if silence_ratio > 0.22:
            parts.append(f"침묵 많음 ({silence_percent:.0f}% 끊김)")
        else:
            parts.append(f"침묵 비율 보통 ({silence_percent:.0f}%)")

        # 명료도 평가
        if asr_clarity_signal < -0.5:
            parts.append("발음 개선 필요 (ASR 인식 어려움)")
        else:
            parts.append("명료도 양호")

        return ", ".join(parts)


# 싱글톤 인스턴스
_extractor: Optional[DeliveryFeatureExtractor] = None


def get_delivery_feature_extractor() -> DeliveryFeatureExtractor:
    """Delivery Feature Extractor 싱글톤 인스턴스 반환"""
    global _extractor
    if _extractor is None:
        _extractor = DeliveryFeatureExtractor()
    return _extractor
