"""ASR 서비스 테스트 (모킹)"""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio

from src.schemas.scoring import ASRResult
from src.services.asr_service import ASRService


@pytest_asyncio.fixture
def asr_service():
    """ASR 서비스 픽스처"""
    return ASRService()


@pytest_asyncio.fixture
def mock_whisper_model():
    """모킹된 Whisper 모델"""
    mock_model = MagicMock()
    mock_model.transcribe.return_value = {
        "text": " I think education is very important for everyone. It helps people develop critical thinking skills.",
        "segments": [
            {
                "id": 0,
                "start": 0.0,
                "end": 5.5,
                "text": " I think education is very important for everyone.",
                "tokens": [1, 519, 519, 3775, 307, 588, 1021, 337, 1518, 13],
                "temperature": 0.0,
                "avg_logprob": -0.25,
                "compression_ratio": 1.2,
                "no_speech_prob": 0.01,
            },
            {
                "id": 1,
                "start": 5.5,
                "end": 10.0,
                "text": " It helps people develop critical thinking skills.",
                "tokens": [467, 3665, 561, 1499, 4924, 1953, 3942, 13],
                "temperature": 0.0,
                "avg_logprob": -0.22,
                "compression_ratio": 1.3,
                "no_speech_prob": 0.02,
            },
        ],
        "language": "en",
    }
    return mock_model


@pytest.mark.asyncio
async def test_transcribe_success(asr_service: ASRService, mock_whisper_model, tmp_path: Path):
    """음성 인식 성공 테스트"""
    # 임시 오디오 파일 생성
    audio_file = tmp_path / "test_audio.mp3"
    audio_file.write_bytes(b"\xff\xfb\x90\x00" + b"\x00" * 1000)

    # Whisper 모델 모킹
    with patch.object(asr_service, "_load_model", return_value=mock_whisper_model):
        result = await asr_service.transcribe(audio_file)

    # 검증
    assert isinstance(result, ASRResult)
    assert len(result.transcript) > 0
    assert result.language == "en"
    assert len(result.segments) == 2
    assert result.duration_sec == 10.0
    assert -1.0 <= result.avg_logprob <= 0.0
    assert 0.0 <= result.no_speech_prob <= 1.0


@pytest.mark.asyncio
async def test_transcribe_file_not_found(asr_service: ASRService):
    """존재하지 않는 파일로 음성 인식 실패 테스트"""
    with pytest.raises(FileNotFoundError, match="오디오 파일을 찾을 수 없습니다"):
        await asr_service.transcribe("/nonexistent/path/to/audio.mp3")


@pytest.mark.asyncio
async def test_transcribe_whisper_error(asr_service: ASRService, tmp_path: Path):
    """Whisper 실행 중 오류 발생 테스트"""
    # 임시 오디오 파일 생성
    audio_file = tmp_path / "test_audio.mp3"
    audio_file.write_bytes(b"\xff\xfb\x90\x00" + b"\x00" * 1000)

    # Whisper 모델이 예외를 발생시키도록 모킹
    mock_model = MagicMock()
    mock_model.transcribe.side_effect = RuntimeError("Whisper processing failed")

    with patch.object(asr_service, "_load_model", return_value=mock_model):
        with pytest.raises(RuntimeError, match="음성 인식 실패"):
            await asr_service.transcribe(audio_file)


@pytest.mark.asyncio
async def test_transcribe_empty_segments(asr_service: ASRService, tmp_path: Path):
    """세그먼트가 없는 경우 처리 테스트"""
    # 임시 오디오 파일 생성
    audio_file = tmp_path / "test_audio.mp3"
    audio_file.write_bytes(b"\xff\xfb\x90\x00" + b"\x00" * 1000)

    # 세그먼트가 없는 결과 모킹
    mock_model = MagicMock()
    mock_model.transcribe.return_value = {
        "text": "",
        "segments": [],
        "language": "en",
    }

    with patch.object(asr_service, "_load_model", return_value=mock_model):
        result = await asr_service.transcribe(audio_file)

    # 검증
    assert result.transcript == ""
    assert len(result.segments) == 0
    assert result.duration_sec == 0.0
    assert result.avg_logprob == 0.0
    assert result.no_speech_prob == 0.0


@pytest.mark.asyncio
async def test_asr_result_validation(mock_whisper_model, asr_service: ASRService, tmp_path: Path):
    """ASR 결과 Pydantic 검증 테스트"""
    # 임시 오디오 파일 생성
    audio_file = tmp_path / "test_audio.mp3"
    audio_file.write_bytes(b"\xff\xfb\x90\x00" + b"\x00" * 1000)

    with patch.object(asr_service, "_load_model", return_value=mock_whisper_model):
        result = await asr_service.transcribe(audio_file)

    # 스키마 검증
    assert isinstance(result.transcript, str)
    assert isinstance(result.segments, list)
    assert isinstance(result.language, str)
    assert isinstance(result.avg_logprob, float)
    assert isinstance(result.no_speech_prob, float)
    assert isinstance(result.duration_sec, float)

    # 세그먼트 검증
    for segment in result.segments:
        assert segment.id >= 0
        assert segment.start >= 0.0
        assert segment.end > segment.start
        assert isinstance(segment.text, str)
        assert isinstance(segment.tokens, list)


def test_unload_model(asr_service: ASRService):
    """모델 언로드 테스트"""
    # 모델 로드
    with patch("whisper.load_model") as mock_load:
        mock_load.return_value = MagicMock()
        asr_service._load_model()
        assert asr_service._model is not None

    # 모델 언로드
    asr_service.unload_model()
    assert asr_service._model is None


@pytest.mark.asyncio
async def test_transcribe_with_high_no_speech_prob(asr_service: ASRService, tmp_path: Path):
    """무음 확률이 높은 오디오 처리 테스트"""
    # 임시 오디오 파일 생성
    audio_file = tmp_path / "silent_audio.mp3"
    audio_file.write_bytes(b"\xff\xfb\x90\x00" + b"\x00" * 1000)

    # 높은 무음 확률로 모킹
    mock_model = MagicMock()
    mock_model.transcribe.return_value = {
        "text": "",
        "segments": [
            {
                "id": 0,
                "start": 0.0,
                "end": 3.0,
                "text": "",
                "tokens": [],
                "temperature": 0.0,
                "avg_logprob": -1.5,
                "compression_ratio": 1.0,
                "no_speech_prob": 0.95,  # 매우 높은 무음 확률
            }
        ],
        "language": "en",
    }

    with patch.object(asr_service, "_load_model", return_value=mock_model):
        result = await asr_service.transcribe(audio_file)

    # 검증
    assert result.no_speech_prob > 0.9
    assert result.transcript == ""


@pytest.mark.asyncio
async def test_lazy_loading(asr_service: ASRService, tmp_path: Path):
    """Lazy loading 동작 테스트"""
    # 초기에는 모델이 None
    assert asr_service._model is None

    # 임시 오디오 파일 생성
    audio_file = tmp_path / "test_audio.mp3"
    audio_file.write_bytes(b"\xff\xfb\x90\x00" + b"\x00" * 1000)

    mock_model = MagicMock()
    mock_model.transcribe.return_value = {
        "text": "Test",
        "segments": [
            {
                "id": 0,
                "start": 0.0,
                "end": 1.0,
                "text": "Test",
                "tokens": [1, 2, 3],
                "temperature": 0.0,
                "avg_logprob": -0.3,
                "compression_ratio": 1.1,
                "no_speech_prob": 0.05,
            }
        ],
        "language": "en",
    }

    # 첫 번째 호출 시 모델 로딩
    with patch("whisper.load_model", return_value=mock_model) as mock_load:
        await asr_service.transcribe(audio_file)
        assert mock_load.called
        assert asr_service._model is not None

    # 두 번째 호출 시 기존 모델 재사용
    with patch("whisper.load_model", return_value=mock_model) as mock_load:
        await asr_service.transcribe(audio_file)
        assert not mock_load.called  # 다시 로딩하지 않음
