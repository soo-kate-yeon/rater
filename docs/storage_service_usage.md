# Storage Service 사용 가이드

## 개요

`storage_service.py`는 TOEFL Speaking Rater의 로컬 파일 스토리지를 관리하는 서비스 레이어입니다.

## 주요 기능

### 1. 파일 저장

```python
from src.services.storage_service import get_storage_service

storage = get_storage_service()

# 오디오 파일 저장
audio_key = await storage.save_audio(file)
# 반환값: "audio/{uuid}.mp3"
```

### 2. 파일 조회

```python
# audio_key로 파일 경로 조회
file_path = await storage.get_audio_path(audio_key)
# 반환값: Path("/path/to/storage/audio/uuid.mp3")
```

### 3. 파일 삭제

```python
# 파일 삭제
success = await storage.delete_audio(audio_key)
# 반환값: True (삭제 성공) or False (파일 없음)
```

### 4. 임시 파일 관리

```python
# 임시 파일 저장 (ASR 처리용)
temp_key = await storage.save_temp_file(file)

# 임시 파일 정리
deleted_count = await storage.cleanup_temp_files()
```

## 디렉토리 구조

```
storage/
├── audio/           # 오디오 원본 파일
│   ├── {uuid}.mp3
│   ├── {uuid}.wav
│   └── {uuid}.m4a
└── temp/            # 임시 파일 (ASR 처리 중)
    └── {uuid}.mp3
```

## API 라우터 사용 예제

### Before (기존 코드)

```python
# src/api/routers/uploads.py
@router.post("/presign")
async def upload_audio(file: UploadFile = File(...)):
    # 검증 로직
    validate_audio_file(file)
    
    # 파일 저장 로직
    storage_path = Path(settings.storage_path)
    storage_path.mkdir(parents=True, exist_ok=True)
    
    file_ext = Path(file.filename).suffix.lower()
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = storage_path / unique_filename
    
    contents = await file.read()
    with open(file_path, "wb") as f:
        f.write(contents)
    
    return {"audio_key": str(file_path)}
```

### After (리팩토링 후)

```python
# src/api/routers/uploads.py
from src.services.storage_service import StorageService, get_storage_service

@router.post("/presign")
async def upload_audio(
    file: UploadFile = File(...),
    storage: StorageService = Depends(get_storage_service),
):
    # 서비스 레이어로 위임
    audio_key = await storage.save_audio(file)
    
    return UploadResponse(
        audio_key=audio_key,
        uploaded_at=datetime.now(timezone.utc),
    )
```

## 보안 기능

### 1. 파일 형식 검증

- 허용된 확장자: `.mp3`, `.wav`, `.m4a`
- 검증 실패 시 `HTTP 400` 에러 발생

### 2. 파일 크기 검증

- 최대 크기: 10MB
- 초과 시 `HTTP 413` 에러 발생

### 3. 경로 탐색 공격 방지

```python
# storage_root 외부 접근 차단
if not str(file_path).startswith(str(self.storage_root.resolve())):
    raise HTTPException(status_code=403, detail="잘못된 파일 경로입니다")
```

## 의존성 주입 패턴

FastAPI의 `Depends`를 사용하여 스토리지 서비스를 주입합니다:

```python
from fastapi import Depends
from src.services.storage_service import StorageService, get_storage_service

@router.post("/example")
async def example_endpoint(
    storage: StorageService = Depends(get_storage_service),
):
    # storage 인스턴스 사용
    audio_key = await storage.save_audio(file)
```

## 에러 처리

모든 메서드는 적절한 HTTP 예외를 발생시킵니다:

- `400 Bad Request`: 잘못된 파일 형식
- `403 Forbidden`: 잘못된 파일 경로
- `404 Not Found`: 파일을 찾을 수 없음
- `413 Request Entity Too Large`: 파일 크기 초과
- `500 Internal Server Error`: 서버 오류

## 테스트 예제

```python
import pytest
from fastapi import UploadFile
from src.services.storage_service import StorageService

@pytest.mark.asyncio
async def test_save_audio():
    storage = StorageService()
    
    # Mock 파일 생성
    file = UploadFile(
        filename="test.mp3",
        file=io.BytesIO(b"fake audio content"),
    )
    
    # 파일 저장
    audio_key = await storage.save_audio(file)
    
    # 검증
    assert audio_key.startswith("audio/")
    assert audio_key.endswith(".mp3")
    
    # 파일 조회
    file_path = await storage.get_audio_path(audio_key)
    assert file_path.exists()
    
    # 파일 삭제
    success = await storage.delete_audio(audio_key)
    assert success is True
```

## 환경 설정

`.env` 파일에서 스토리지 경로를 설정합니다:

```bash
STORAGE_PATH=./storage
```

`src/core/config.py`에서 자동으로 로드됩니다:

```python
storage_path: str = Field(
    default="./storage",
    description="로컬 파일 저장소 경로",
)
```

## 향후 개선 사항

1. **S3 통합**: AWS S3 스토리지 옵션 추가
2. **파일 압축**: 저장 전 자동 압축
3. **메타데이터 저장**: 파일 정보를 데이터베이스에 저장
4. **임시 파일 자동 정리**: 일정 시간 후 자동 삭제
