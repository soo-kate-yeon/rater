"""Whisper ASR 서비스"""

import logging
from pathlib import Path
from typing import Any

import whisper
from whisper import Whisper

from src.core.config import settings
from src.schemas.scoring import ASRResult, WhisperSegment

logger = logging.getLogger(__name__)


class ASRService:
    """Whisper 기반 음성 인식 서비스"""

    def __init__(self) -> None:
        """서비스 초기화"""
        self._model: Whisper | None = None
        self._model_name = settings.whisper_model
        self._device = settings.whisper_device

    def _load_model(self) -> Whisper:
        """Whisper 모델 로딩 (Lazy Loading)"""
        if self._model is None:
            logger.info(
                f"Loading Whisper model: {self._model_name} on device: {self._device}"
            )
            try:
                self._model = whisper.load_model(self._model_name, device=self._device)
                logger.info(f"Whisper model '{self._model_name}' loaded successfully")
            except Exception as e:
                logger.error(f"Failed to load Whisper model: {e}")
                raise RuntimeError(f"Whisper 모델 로딩 실패: {e}") from e
        return self._model

    async def transcribe(self, audio_path: str | Path) -> ASRResult:
        """
        오디오 파일을 전사합니다.

        Args:
            audio_path: 오디오 파일 경로

        Returns:
            ASRResult: 전사 결과 (transcript, segments, language, avg_logprob, no_speech_prob)

        Raises:
            FileNotFoundError: 오디오 파일이 존재하지 않을 때
            RuntimeError: Whisper 실행 중 오류 발생 시
        """
        audio_path = Path(audio_path)
        if not audio_path.exists():
            raise FileNotFoundError(f"오디오 파일을 찾을 수 없습니다: {audio_path}")

        logger.info(f"Transcribing audio file: {audio_path}")

        try:
            model = self._load_model()

            # Whisper transcribe 실행
            result: dict[str, Any] = model.transcribe(
                str(audio_path),
                language="en",  # TOEFL Speaking은 영어만 처리
                word_timestamps=False,  # 단어 단위 타임스탬프는 불필요 (세그먼트 단위로 충분)
                verbose=False,
            )

            # 전체 평균 로그 확률 계산
            segments_data = result.get("segments", [])
            if segments_data:
                avg_logprob = sum(seg.get("avg_logprob", 0.0) for seg in segments_data) / len(
                    segments_data
                )
            else:
                avg_logprob = 0.0

            # 무음 확률 계산 (세그먼트별 no_speech_prob 평균)
            if segments_data:
                no_speech_prob = sum(
                    seg.get("no_speech_prob", 0.0) for seg in segments_data
                ) / len(segments_data)
            else:
                no_speech_prob = 0.0

            # 전체 길이 계산 (마지막 세그먼트의 end 시간)
            duration_sec = segments_data[-1]["end"] if segments_data else 0.0

            # Pydantic 모델로 변환
            segments = [
                WhisperSegment(
                    id=seg["id"],
                    start=seg["start"],
                    end=seg["end"],
                    text=seg["text"],
                    tokens=seg.get("tokens", []),
                    temperature=seg.get("temperature", 0.0),
                    avg_logprob=seg.get("avg_logprob", 0.0),
                    compression_ratio=seg.get("compression_ratio", 1.0),
                    no_speech_prob=seg.get("no_speech_prob", 0.0),
                )
                for seg in segments_data
            ]

            asr_result = ASRResult(
                transcript=result["text"].strip(),
                segments=segments,
                language=result.get("language", "en"),
                avg_logprob=avg_logprob,
                no_speech_prob=no_speech_prob,
                duration_sec=duration_sec,
            )

            logger.info(
                f"Transcription completed: {len(segments)} segments, "
                f"duration={duration_sec:.2f}s, avg_logprob={avg_logprob:.3f}"
            )
            return asr_result

        except Exception as e:
            logger.error(f"Whisper transcription failed: {e}")
            raise RuntimeError(f"음성 인식 실패: {e}") from e

    def unload_model(self) -> None:
        """메모리 절약을 위해 모델 언로드"""
        if self._model is not None:
            logger.info("Unloading Whisper model")
            del self._model
            self._model = None


# 싱글톤 인스턴스
_asr_service: ASRService | None = None


def get_asr_service() -> ASRService:
    """ASR 서비스 싱글톤 인스턴스 반환"""
    global _asr_service
    if _asr_service is None:
        _asr_service = ASRService()
    return _asr_service
