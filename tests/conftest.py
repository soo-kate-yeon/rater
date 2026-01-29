"""공통 테스트 픽스처 및 설정"""

import asyncio
import os
from collections.abc import AsyncGenerator
from pathlib import Path
from typing import Any

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.api.main import app
from src.core.database import get_db
from src.models.base import Base  # Use the correct Base that models inherit from
from src.models.task import Task
from src.models.user import User
from src.schemas.scoring import ASRResult

# 테스트용 환경 변수 설정
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["SECRET_KEY"] = "test-secret-key-for-testing-only"
os.environ["STORAGE_PATH"] = "/tmp/toefl-rater-test-storage"


@pytest.fixture(scope="session")
def event_loop():
    """이벤트 루프 픽스처 (세션 스코프)"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def test_engine() -> AsyncGenerator[AsyncEngine, None]:
    """테스트용 SQLite in-memory 엔진"""
    # 모든 모델을 명시적으로 import하여 Base.metadata에 등록

    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        pool_pre_ping=True,
        connect_args={"check_same_thread": False},
    )

    # SQLite에서 외래 키 활성화
    from sqlalchemy import event

    @event.listens_for(engine.sync_engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    # 테이블 생성
    async with engine.begin() as conn:

        def create_tables(connection):
            Base.metadata.create_all(connection)
            # 디버그: 생성된 테이블 확인
            print(f"Created tables: {list(Base.metadata.tables.keys())}")

        await conn.run_sync(create_tables)

    yield engine

    # 정리
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def test_db(test_engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    """테스트용 데이터베이스 세션"""
    import uuid

    from src.core.security import hash_password

    async_session = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session() as session:
        # 기본 테스트 사용자 생성 (하드코딩된 user_id를 위해)
        default_user = User(
            id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
            email="default@test.com",
            hashed_password=hash_password("defaultpassword"),
        )
        session.add(default_user)
        await (
            session.flush()
        )  # commit 대신 flush를 사용하여 동일한 트랜잭션 내에서 사용 가능하게 함

        yield session
        # rollback 제거: test_engine이 각 테스트마다 새로 생성되므로 rollback 불필요
        # await session.rollback()


@pytest_asyncio.fixture(scope="function")
async def test_client(test_db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """FastAPI 테스트 클라이언트"""

    # 데이터베이스 의존성 오버라이드
    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield test_db

    app.dependency_overrides[get_db] = override_get_db

    # 비동기 클라이언트 생성
    async with AsyncClient(
        transport=ASGITransport(app=app),  # type: ignore
        base_url="http://test",
    ) as client:
        yield client

    # 의존성 오버라이드 정리
    app.dependency_overrides.clear()


@pytest.fixture
def mock_asr_result() -> dict[str, Any]:
    """모킹된 ASR 결과"""
    return {
        "transcript": "I think education is very important for everyone. It helps people develop critical thinking skills and prepare for their future careers.",
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
                "end": 12.0,
                "text": " It helps people develop critical thinking skills and prepare for their future careers.",
                "tokens": [
                    467,
                    3665,
                    561,
                    1499,
                    4924,
                    1953,
                    3942,
                    293,
                    5940,
                    337,
                    641,
                    2027,
                    16409,
                    13,
                ],
                "temperature": 0.0,
                "avg_logprob": -0.22,
                "compression_ratio": 1.3,
                "no_speech_prob": 0.02,
            },
        ],
        "language": "en",
        "avg_logprob": -0.235,
        "no_speech_prob": 0.015,
        "duration_sec": 12.0,
    }


@pytest.fixture
def mock_asr_result_model(mock_asr_result: dict[str, Any]) -> ASRResult:
    """모킹된 ASR 결과 (Pydantic 모델)"""
    return ASRResult.model_validate(mock_asr_result)


@pytest_asyncio.fixture
async def test_user(test_db: AsyncSession) -> User:
    """테스트용 사용자"""
    from src.core.security import hash_password

    user = User(
        email="test@example.com",
        hashed_password=hash_password("testpassword123"),
    )
    test_db.add(user)
    await test_db.flush()  # commit 대신 flush 사용
    await test_db.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_task(test_db: AsyncSession) -> Task:
    """테스트용 태스크"""
    from src.models.task import TaskType

    task = Task(
        task_type=TaskType.INDEPENDENT,
        prompt="Do you agree or disagree with the following statement? It is better to work in a team than to work alone.",
        source_reading=None,
        source_listening=None,
        tags={},
    )
    test_db.add(task)
    await test_db.flush()  # commit 대신 flush 사용
    await test_db.refresh(task)
    return task


@pytest.fixture
def sample_audio_file():
    """샘플 오디오 파일 (바이트)"""
    # MP3 파일 헤더를 포함한 가짜 오디오 데이터
    # 실제로는 작동하지 않지만 파일 타입 검증에는 충분
    return b"\xff\xfb\x90\x00" + b"\x00" * 1000


@pytest.fixture
def cleanup_storage():
    """스토리지 정리 픽스처"""
    storage_path = Path(os.environ.get("STORAGE_PATH", "/tmp/toefl-rater-test-storage"))

    # 테스트 전 정리
    if storage_path.exists():
        import shutil

        shutil.rmtree(storage_path)
    storage_path.mkdir(parents=True, exist_ok=True)

    yield

    # 테스트 후 정리
    if storage_path.exists():
        import shutil

        shutil.rmtree(storage_path)
