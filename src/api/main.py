"""FastAPI 애플리케이션 엔트리포인트"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.api.routers import answer_keys, auth, items, jobs, sets, stimuli, tasks, uploads
from src.core.config import settings
from src.core.database import close_db, init_db


def make_json_serializable(obj: Any) -> Any:
    """객체를 JSON 직렬화 가능하도록 재귀적으로 변환"""
    if isinstance(obj, dict):
        return {k: make_json_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [make_json_serializable(item) for item in obj]
    elif isinstance(obj, str | int | float | bool | type(None)):
        return obj
    else:
        # 직렬화 불가능한 객체는 문자열로 변환
        return str(obj)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """애플리케이션 생명주기 관리"""
    # 시작 시
    if settings.debug:
        await init_db()
    yield
    # 종료 시
    await close_db()


# FastAPI 앱 생성
app = FastAPI(
    title="TOEFL Speaking Rater API",
    description="TOEFL Speaking 자동 채점 및 피드백 시스템",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS 미들웨어 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프로덕션에서는 특정 도메인만 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 예외 핸들러
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """입력 검증 오류 핸들러"""
    # errors()의 결과를 JSON 직렬화 가능하도록 변환
    errors = make_json_serializable(exc.errors())

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": errors,
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """일반 예외 핸들러"""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error",
            "message": str(exc) if settings.debug else "An unexpected error occurred",
        },
    )


# 기본 엔드포인트
@app.get("/")
async def root() -> dict[str, str]:
    """루트 엔드포인트"""
    return {"message": "TOEFL Speaking Rater API", "version": "0.1.0"}


@app.get("/health")
async def health() -> dict[str, str]:
    """헬스 체크 엔드포인트"""
    return {"status": "healthy"}


# 라우터 등록
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(tasks.router, prefix="/api/v1/tasks", tags=["tasks"])
app.include_router(jobs.router, prefix="/api/v1/jobs", tags=["jobs"])
app.include_router(uploads.router, prefix="/api/v1/uploads", tags=["uploads"])

# 정규화 스키마 라우터 (SPEC-TOEFL-SCHEMA-001)
app.include_router(sets.router, prefix="/api/v1/sets", tags=["sets"])
app.include_router(items.router, prefix="/api/v1/items", tags=["items"])
app.include_router(stimuli.router, prefix="/api/v1/stimuli", tags=["stimuli"])
app.include_router(answer_keys.router, prefix="/api/v1/answer-keys", tags=["answer-keys"])
