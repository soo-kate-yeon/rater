"""파일 업로드 API 테스트"""

import io

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_upload_audio_success(test_client: AsyncClient, sample_audio_file: bytes, cleanup_storage):
    """오디오 파일 업로드 성공 테스트"""
    # MP3 파일 업로드
    files = {"file": ("test_audio.mp3", io.BytesIO(sample_audio_file), "audio/mpeg")}

    response = await test_client.post("/api/v1/uploads/presign", files=files)

    # 검증
    assert response.status_code == 201
    data = response.json()
    assert "audio_key" in data
    assert data["audio_key"].startswith("audio/")
    assert data["audio_key"].endswith(".mp3")
    assert "uploaded_at" in data


@pytest.mark.asyncio
async def test_upload_audio_wav_format(test_client: AsyncClient, cleanup_storage):
    """WAV 형식 파일 업로드 테스트"""
    # WAV 파일 헤더를 포함한 가짜 데이터
    wav_data = b"RIFF" + b"\x00" * 1000

    files = {"file": ("test_audio.wav", io.BytesIO(wav_data), "audio/wav")}

    response = await test_client.post("/api/v1/uploads/presign", files=files)

    # 검증
    assert response.status_code == 201
    data = response.json()
    assert data["audio_key"].endswith(".wav")


@pytest.mark.asyncio
async def test_upload_audio_m4a_format(test_client: AsyncClient, cleanup_storage):
    """M4A 형식 파일 업로드 테스트"""
    # M4A 파일 가짜 데이터
    m4a_data = b"\x00\x00\x00\x20ftyp" + b"\x00" * 1000

    files = {"file": ("test_audio.m4a", io.BytesIO(m4a_data), "audio/mp4")}

    response = await test_client.post("/api/v1/uploads/presign", files=files)

    # 검증
    assert response.status_code == 201
    data = response.json()
    assert data["audio_key"].endswith(".m4a")


@pytest.mark.asyncio
async def test_upload_audio_invalid_format(test_client: AsyncClient):
    """지원하지 않는 파일 형식 업로드 실패 테스트"""
    # 텍스트 파일 업로드 시도
    files = {"file": ("test.txt", io.BytesIO(b"This is not an audio file"), "text/plain")}

    response = await test_client.post("/api/v1/uploads/presign", files=files)

    # 검증
    assert response.status_code == 400
    assert "지원하지 않는 파일 형식" in response.json()["detail"]


@pytest.mark.asyncio
async def test_upload_audio_no_filename(test_client: AsyncClient):
    """파일명 없는 파일 업로드 실패 테스트"""
    files = {"file": ("", io.BytesIO(b"audio data"), "audio/mpeg")}

    response = await test_client.post("/api/v1/uploads/presign", files=files)

    # 검증
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_upload_audio_too_large(test_client: AsyncClient):
    """최대 크기를 초과하는 파일 업로드 실패 테스트"""
    # 11MB 크기의 파일 (최대 10MB 초과)
    large_data = b"\xff\xfb\x90\x00" + b"\x00" * (11 * 1024 * 1024)

    files = {"file": ("large_audio.mp3", io.BytesIO(large_data), "audio/mpeg")}

    response = await test_client.post("/api/v1/uploads/presign", files=files)

    # 검증
    assert response.status_code == 413
    assert "최대 제한" in response.json()["detail"]


@pytest.mark.asyncio
async def test_upload_audio_no_file(test_client: AsyncClient):
    """파일 없이 업로드 요청 시 실패 테스트"""
    response = await test_client.post("/api/v1/uploads/presign")

    # 검증 (FastAPI 422 Unprocessable Entity)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_upload_audio_response_format(test_client: AsyncClient, sample_audio_file: bytes, cleanup_storage):
    """업로드 응답 포맷 검증"""
    files = {"file": ("test.mp3", io.BytesIO(sample_audio_file), "audio/mpeg")}

    response = await test_client.post("/api/v1/uploads/presign", files=files)

    # 검증
    assert response.status_code == 201
    data = response.json()

    # 응답 필드 확인
    assert isinstance(data["audio_key"], str)
    assert isinstance(data["uploaded_at"], str)

    # audio_key 형식 확인 (UUID 포함)
    import re

    uuid_pattern = r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"
    assert re.search(uuid_pattern, data["audio_key"])
