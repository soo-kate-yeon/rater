"""로컬 파일 스토리지 서비스

오디오 파일의 저장, 조회, 삭제를 담당하는 서비스 레이어
"""

import uuid
from pathlib import Path
from typing import Set

import aiofiles
from fastapi import HTTPException, UploadFile, status

from src.core.config import settings

# 허용된 파일 확장자
ALLOWED_EXTENSIONS: Set[str] = {".mp3", ".wav", ".m4a"}

# 최대 파일 크기 (10MB)
MAX_FILE_SIZE: int = 10 * 1024 * 1024


class StorageService:
    """파일 스토리지 관리 서비스"""

    def __init__(self) -> None:
        """스토리지 서비스 초기화"""
        self.storage_root = Path(settings.storage_path)
        self.audio_dir = self.storage_root / "audio"
        self.temp_dir = self.storage_root / "temp"

        # 디렉토리 생성
        self._ensure_directories()

    def _ensure_directories(self) -> None:
        """필요한 디렉토리 생성"""
        self.audio_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    async def validate_audio(self, file: UploadFile) -> bool:
        """
        오디오 파일 검증

        Args:
            file: 업로드된 파일

        Returns:
            검증 성공 여부

        Raises:
            HTTPException: 검증 실패 시
        """
        # 파일명 확인
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="파일명이 없습니다",
            )

        # 파일 확장자 확인
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"지원하지 않는 파일 형식입니다. 허용된 형식: {', '.join(ALLOWED_EXTENSIONS)}",
            )

        # 파일 크기 확인
        if file.size and file.size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"파일 크기가 최대 제한({MAX_FILE_SIZE / (1024 * 1024)}MB)을 초과했습니다",
            )

        return True

    async def save_audio(self, file: UploadFile) -> str:
        """
        오디오 파일 저장

        Args:
            file: 업로드된 오디오 파일

        Returns:
            audio_key (저장된 파일의 고유 키)

        Raises:
            HTTPException: 파일 저장 실패 시
        """
        # 파일 검증
        await self.validate_audio(file)

        # 고유 파일명 생성 (UUID + 원본 확장자)
        file_ext = Path(file.filename or "").suffix.lower()
        unique_filename = f"{uuid.uuid4()}{file_ext}"
        file_path = self.audio_dir / unique_filename

        try:
            # 비동기 파일 저장
            contents = await file.read()
            async with aiofiles.open(file_path, "wb") as f:
                await f.write(contents)

            # audio_key 생성 (audio/ 디렉토리 내 상대 경로)
            audio_key = f"audio/{unique_filename}"
            return audio_key

        except Exception as e:
            # 저장 실패 시 파일 삭제
            if file_path.exists():
                file_path.unlink()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"파일 저장에 실패했습니다: {str(e)}",
            ) from e

    async def get_audio_path(self, audio_key: str) -> Path:
        """
        audio_key로 파일 경로 조회

        Args:
            audio_key: 파일 고유 키 (예: "audio/uuid.mp3")

        Returns:
            파일의 절대 경로

        Raises:
            HTTPException: 파일이 존재하지 않을 때
        """
        # 경로 탐색 공격 방지
        file_path = (self.storage_root / audio_key).resolve()

        # storage_root 외부 접근 차단
        if not str(file_path).startswith(str(self.storage_root.resolve())):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="잘못된 파일 경로입니다",
            )

        # 파일 존재 여부 확인
        if not file_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"파일을 찾을 수 없습니다: {audio_key}",
            )

        return file_path

    async def delete_audio(self, audio_key: str) -> bool:
        """
        오디오 파일 삭제

        Args:
            audio_key: 파일 고유 키

        Returns:
            삭제 성공 여부

        Raises:
            HTTPException: 파일 삭제 실패 시
        """
        try:
            file_path = await self.get_audio_path(audio_key)

            # 파일 삭제
            if file_path.exists():
                file_path.unlink()
                return True

            return False

        except HTTPException:
            # 파일이 이미 없는 경우 성공으로 간주
            return False
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"파일 삭제에 실패했습니다: {str(e)}",
            ) from e

    async def save_temp_file(self, file: UploadFile) -> str:
        """
        임시 파일 저장 (ASR 처리용)

        Args:
            file: 업로드된 오디오 파일

        Returns:
            temp_key (임시 파일의 고유 키)

        Raises:
            HTTPException: 파일 저장 실패 시
        """
        await self.validate_audio(file)

        # 고유 파일명 생성
        file_ext = Path(file.filename or "").suffix.lower()
        unique_filename = f"{uuid.uuid4()}{file_ext}"
        file_path = self.temp_dir / unique_filename

        try:
            contents = await file.read()
            async with aiofiles.open(file_path, "wb") as f:
                await f.write(contents)

            temp_key = f"temp/{unique_filename}"
            return temp_key

        except Exception as e:
            if file_path.exists():
                file_path.unlink()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"임시 파일 저장에 실패했습니다: {str(e)}",
            ) from e

    async def cleanup_temp_files(self) -> int:
        """
        임시 파일 정리

        Returns:
            삭제된 파일 수
        """
        deleted_count = 0

        if not self.temp_dir.exists():
            return deleted_count

        for file_path in self.temp_dir.iterdir():
            if file_path.is_file():
                try:
                    file_path.unlink()
                    deleted_count += 1
                except Exception:
                    # 삭제 실패 시 무시하고 계속 진행
                    continue

        return deleted_count


# 싱글톤 인스턴스
_storage_service: StorageService | None = None


def get_storage_service() -> StorageService:
    """스토리지 서비스 싱글톤 인스턴스 반환"""
    global _storage_service
    if _storage_service is None:
        _storage_service = StorageService()
    return _storage_service
