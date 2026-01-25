"""FastAPI 애플리케이션 엔트리포인트"""

from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.api.routers import auth, jobs, tasks, uploads
from src.core.config import settings
from src.core.database import close_db, init_db


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
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": exc.errors(),
            "body": exc.body,
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
app.include_router(auth.router, prefix="/v1/auth", tags=["auth"])
app.include_router(tasks.router, prefix="/v1/tasks", tags=["tasks"])
app.include_router(jobs.router, prefix="/v1/jobs", tags=["jobs"])
app.include_router(uploads.router, prefix="/v1/uploads", tags=["uploads"])
