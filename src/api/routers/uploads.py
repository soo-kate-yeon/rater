"""파일 업로드 라우터"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, UploadFile, status

from src.schemas.uploads import UploadResponse
from src.services.storage_service import StorageService, get_storage_service

router = APIRouter()


@router.post("/presign", response_model=UploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_audio(
    file: UploadFile = File(..., description="오디오 파일 (MP3, WAV, M4A)"),
    storage: StorageService = Depends(get_storage_service),
) -> UploadResponse:
    """
    오디오 파일 직접 업로드 엔드포인트 (로컬 환경용)

    Args:
        file: 업로드할 오디오 파일
        storage: 스토리지 서비스 (의존성 주입)

    Returns:
        업로드된 파일 정보 (audio_key, uploaded_at)

    Raises:
        HTTPException: 파일 검증 실패 또는 저장 실패 시
    """
    # 파일 저장
    audio_key = await storage.save_audio(file)

    # 응답 생성
    uploaded_at = datetime.now(timezone.utc)

    return UploadResponse(
        audio_key=audio_key,
        uploaded_at=uploaded_at,
    )
