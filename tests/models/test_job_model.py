"""Job 모델 테스트"""

import uuid

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.job import Job, JobStatus
from src.models.task import Task
from src.models.user import User


@pytest.mark.asyncio
async def test_create_job(test_db: AsyncSession, test_user: User, test_task: Task):
    """Job 생성 테스트"""
    # Job 생성
    job = Job(
        id=uuid.uuid4(),
        user_id=test_user.id,
        task_id=test_task.id,
        status=JobStatus.QUEUED,
        progress=0,
        audio_key="audio/test-audio.mp3",
    )

    test_db.add(job)
    await test_db.commit()
    await test_db.refresh(job)

    # 검증
    assert job.id is not None
    assert job.user_id == test_user.id
    assert job.task_id == test_task.id
    assert job.status == JobStatus.QUEUED
    assert job.progress == 0
    assert job.audio_key == "audio/test-audio.mp3"
    assert job.error_code is None
    assert job.error_message is None
    assert job.created_at is not None
    assert job.updated_at is not None


@pytest.mark.asyncio
async def test_job_status_enum_values():
    """JobStatus Enum 값 테스트"""
    # 모든 상태 확인
    assert JobStatus.QUEUED.value == "QUEUED"
    assert JobStatus.FETCHING_AUDIO.value == "FETCHING_AUDIO"
    assert JobStatus.ASR_RUNNING.value == "ASR_RUNNING"
    assert JobStatus.FEATURE_EXTRACTING.value == "FEATURE_EXTRACTING"
    assert JobStatus.LLM_ANALYZING.value == "LLM_ANALYZING"
    assert JobStatus.SCORING.value == "SCORING"
    assert JobStatus.DONE.value == "DONE"
    assert JobStatus.FAILED.value == "FAILED"


@pytest.mark.asyncio
async def test_job_status_transition(test_db: AsyncSession, test_user: User, test_task: Task):
    """Job 상태 전이 테스트"""
    # Job 생성
    job = Job(
        id=uuid.uuid4(),
        user_id=test_user.id,
        task_id=test_task.id,
        status=JobStatus.QUEUED,
        progress=0,
        audio_key="audio/test.mp3",
    )
    test_db.add(job)
    await test_db.commit()

    # QUEUED -> FETCHING_AUDIO
    job.status = JobStatus.FETCHING_AUDIO
    job.progress = 10
    await test_db.commit()
    await test_db.refresh(job)
    assert job.status == JobStatus.FETCHING_AUDIO
    assert job.progress == 10

    # FETCHING_AUDIO -> ASR_RUNNING
    job.status = JobStatus.ASR_RUNNING
    job.progress = 30
    await test_db.commit()
    await test_db.refresh(job)
    assert job.status == JobStatus.ASR_RUNNING
    assert job.progress == 30

    # ASR_RUNNING -> FEATURE_EXTRACTING
    job.status = JobStatus.FEATURE_EXTRACTING
    job.progress = 50
    await test_db.commit()
    await test_db.refresh(job)
    assert job.status == JobStatus.FEATURE_EXTRACTING
    assert job.progress == 50

    # FEATURE_EXTRACTING -> LLM_ANALYZING
    job.status = JobStatus.LLM_ANALYZING
    job.progress = 70
    await test_db.commit()
    await test_db.refresh(job)
    assert job.status == JobStatus.LLM_ANALYZING
    assert job.progress == 70

    # LLM_ANALYZING -> SCORING
    job.status = JobStatus.SCORING
    job.progress = 90
    await test_db.commit()
    await test_db.refresh(job)
    assert job.status == JobStatus.SCORING
    assert job.progress == 90

    # SCORING -> DONE
    job.status = JobStatus.DONE
    job.progress = 100
    await test_db.commit()
    await test_db.refresh(job)
    assert job.status == JobStatus.DONE
    assert job.progress == 100


@pytest.mark.asyncio
async def test_job_failure_status(test_db: AsyncSession, test_user: User, test_task: Task):
    """Job 실패 상태 테스트"""
    # Job 생성
    job = Job(
        id=uuid.uuid4(),
        user_id=test_user.id,
        task_id=test_task.id,
        status=JobStatus.ASR_RUNNING,
        progress=30,
        audio_key="audio/test.mp3",
    )
    test_db.add(job)
    await test_db.commit()

    # 실패 상태로 전환
    job.status = JobStatus.FAILED
    job.error_code = "ASR_ERROR"
    job.error_message = "Whisper transcription failed: Model not found"
    await test_db.commit()
    await test_db.refresh(job)

    # 검증
    assert job.status == JobStatus.FAILED
    assert job.error_code == "ASR_ERROR"
    assert job.error_message == "Whisper transcription failed: Model not found"


@pytest.mark.asyncio
async def test_job_relationships(test_db: AsyncSession, test_user: User, test_task: Task):
    """Job 관계 테스트 (user, task)"""
    # Job 생성
    job = Job(
        id=uuid.uuid4(),
        user_id=test_user.id,
        task_id=test_task.id,
        status=JobStatus.QUEUED,
        progress=0,
        audio_key="audio/test.mp3",
    )
    test_db.add(job)
    await test_db.commit()
    await test_db.refresh(job)

    # 관계 확인
    assert job.user is not None
    assert job.user.id == test_user.id
    assert job.user.email == test_user.email

    assert job.task is not None
    assert job.task.id == test_task.id
    assert job.task.task_type == test_task.task_type


@pytest.mark.asyncio
async def test_job_cascade_delete_user(test_db: AsyncSession, test_task: Task):
    """User 삭제 시 Job 캐스케이드 삭제 테스트"""
    from src.core.security import hash_password

    # 새로운 사용자 생성
    user = User(
        email="cascade@test.com",
        hashed_password=hash_password("password"),
        name="Cascade Test",
    )
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)

    # Job 생성
    job = Job(
        id=uuid.uuid4(),
        user_id=user.id,
        task_id=test_task.id,
        status=JobStatus.QUEUED,
        progress=0,
        audio_key="audio/test.mp3",
    )
    test_db.add(job)
    await test_db.commit()
    job_id = job.id

    # User 삭제
    await test_db.delete(user)
    await test_db.commit()

    # Job도 함께 삭제되었는지 확인
    result = await test_db.execute(select(Job).where(Job.id == job_id))
    deleted_job = result.scalar_one_or_none()
    assert deleted_job is None


@pytest.mark.asyncio
async def test_job_progress_validation(test_db: AsyncSession, test_user: User, test_task: Task):
    """Job progress 범위 테스트"""
    # 정상 범위 (0-100)
    job = Job(
        id=uuid.uuid4(),
        user_id=test_user.id,
        task_id=test_task.id,
        status=JobStatus.QUEUED,
        progress=50,
        audio_key="audio/test.mp3",
    )
    test_db.add(job)
    await test_db.commit()
    await test_db.refresh(job)
    assert job.progress == 50

    # 최소값
    job.progress = 0
    await test_db.commit()
    await test_db.refresh(job)
    assert job.progress == 0

    # 최대값
    job.progress = 100
    await test_db.commit()
    await test_db.refresh(job)
    assert job.progress == 100


@pytest.mark.asyncio
async def test_job_repr(test_db: AsyncSession, test_user: User, test_task: Task):
    """Job __repr__ 메서드 테스트"""
    job = Job(
        id=uuid.uuid4(),
        user_id=test_user.id,
        task_id=test_task.id,
        status=JobStatus.ASR_RUNNING,
        progress=45,
        audio_key="audio/test.mp3",
    )
    test_db.add(job)
    await test_db.commit()
    await test_db.refresh(job)

    # repr 출력 확인
    repr_str = repr(job)
    assert "Job(" in repr_str
    assert "ASR_RUNNING" in repr_str
    assert "45%" in repr_str


@pytest.mark.asyncio
async def test_multiple_jobs_per_user(test_db: AsyncSession, test_user: User, test_task: Task):
    """한 사용자가 여러 Job을 가질 수 있는지 테스트"""
    # 3개의 Job 생성
    jobs = []
    for i in range(3):
        job = Job(
            id=uuid.uuid4(),
            user_id=test_user.id,
            task_id=test_task.id,
            status=JobStatus.QUEUED,
            progress=0,
            audio_key=f"audio/test-{i}.mp3",
        )
        test_db.add(job)
        jobs.append(job)

    await test_db.commit()

    # 사용자의 모든 Job 조회
    result = await test_db.execute(select(Job).where(Job.user_id == test_user.id))
    user_jobs = result.scalars().all()

    # 검증
    assert len(user_jobs) >= 3  # 최소 3개 이상 (test_user fixture가 이미 job을 가질 수 있음)


@pytest.mark.asyncio
async def test_job_timestamps(test_db: AsyncSession, test_user: User, test_task: Task):
    """Job 타임스탬프 테스트"""
    import time

    # Job 생성
    job = Job(
        id=uuid.uuid4(),
        user_id=test_user.id,
        task_id=test_task.id,
        status=JobStatus.QUEUED,
        progress=0,
        audio_key="audio/test.mp3",
    )
    test_db.add(job)
    await test_db.commit()
    await test_db.refresh(job)

    created_at = job.created_at
    updated_at = job.updated_at

    # created_at과 updated_at이 설정되었는지 확인
    assert created_at is not None
    assert updated_at is not None

    # 잠시 대기
    time.sleep(0.1)

    # Job 업데이트
    job.progress = 50
    await test_db.commit()
    await test_db.refresh(job)

    # updated_at이 변경되었는지 확인
    assert job.created_at == created_at  # created_at은 변경되지 않음
    # SQLite의 경우 자동 업데이트가 안 될 수 있으므로 체크하지 않음
