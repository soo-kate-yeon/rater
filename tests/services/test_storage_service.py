"""스토리지 서비스 테스트"""

import io
from pathlib import Path

import pytest
import pytest_asyncio
from fastapi import UploadFile

from src.services.storage_service import StorageService


@pytest_asyncio.fixture
def storage_service():
    """스토리지 서비스 픽스처"""
    return StorageService()


@pytest_asyncio.fixture
def mock_audio_file():
    """Mock 오디오 파일 픽스처"""
    return UploadFile(
        filename="test.mp3",
        file=io.BytesIO(b"fake audio content for testing"),
    )


@pytest.mark.asyncio
async def test_save_audio(storage_service: StorageService, mock_audio_file: UploadFile):
    """오디오 파일 저장 테스트"""
    # 파일 저장
    audio_key = await storage_service.save_audio(mock_audio_file)

    # 검증
    assert audio_key is not None
    assert audio_key.startswith("audio/")
    assert audio_key.endswith(".mp3")

    # 정리
    await storage_service.delete_audio(audio_key)


@pytest.mark.asyncio
async def test_get_audio_path(storage_service: StorageService, mock_audio_file: UploadFile):
    """파일 경로 조회 테스트"""
    # 파일 저장
    audio_key = await storage_service.save_audio(mock_audio_file)

    # 파일 경로 조회
    file_path = await storage_service.get_audio_path(audio_key)

    # 검증
    assert file_path.exists()
    assert file_path.is_file()
    assert file_path.suffix == ".mp3"

    # 정리
    await storage_service.delete_audio(audio_key)


@pytest.mark.asyncio
async def test_delete_audio(storage_service: StorageService, mock_audio_file: UploadFile):
    """파일 삭제 테스트"""
    # 파일 저장
    audio_key = await storage_service.save_audio(mock_audio_file)

    # 파일 삭제
    success = await storage_service.delete_audio(audio_key)

    # 검증
    assert success is True

    # 파일이 실제로 삭제되었는지 확인
    file_path = storage_service.storage_root / audio_key
    assert not file_path.exists()


@pytest.mark.asyncio
async def test_validate_audio_invalid_extension(storage_service: StorageService):
    """잘못된 파일 확장자 검증 테스트"""
    from fastapi import HTTPException

    # 잘못된 확장자 파일
    invalid_file = UploadFile(
        filename="test.txt",
        file=io.BytesIO(b"not an audio file"),
    )

    # 예외 발생 확인
    with pytest.raises(HTTPException) as exc_info:
        await storage_service.validate_audio(invalid_file)

    assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_save_temp_file(storage_service: StorageService, mock_audio_file: UploadFile):
    """임시 파일 저장 테스트"""
    # 임시 파일 저장
    temp_key = await storage_service.save_temp_file(mock_audio_file)

    # 검증
    assert temp_key is not None
    assert temp_key.startswith("temp/")
    assert temp_key.endswith(".mp3")

    # 파일 존재 확인
    temp_path = await storage_service.get_audio_path(temp_key)
    assert temp_path.exists()

    # 정리
    await storage_service.delete_audio(temp_key)


@pytest.mark.asyncio
async def test_cleanup_temp_files(storage_service: StorageService):
    """임시 파일 정리 테스트"""
    # 여러 임시 파일 생성
    temp_keys = []
    for i in range(3):
        mock_file = UploadFile(
            filename=f"test_{i}.mp3",
            file=io.BytesIO(b"fake audio content"),
        )
        temp_key = await storage_service.save_temp_file(mock_file)
        temp_keys.append(temp_key)

    # 임시 파일 정리
    deleted_count = await storage_service.cleanup_temp_files()

    # 검증
    assert deleted_count == 3

    # 파일들이 실제로 삭제되었는지 확인
    for temp_key in temp_keys:
        temp_path = storage_service.storage_root / temp_key
        assert not temp_path.exists()
