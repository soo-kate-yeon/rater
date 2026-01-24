"""Job API 테스트"""

import io
import uuid
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.job import Job, JobStatus
from src.models.report import Report


@pytest.mark.asyncio
async def test_create_job_success(
    test_client: AsyncClient,
    test_db: AsyncSession,
    test_task,
    sample_audio_file: bytes,
    cleanup_storage,
):
    """Job 생성 성공 테스트"""
    # 1. 파일 업로드
    files = {"file": ("test.mp3", io.BytesIO(sample_audio_file), "audio/mpeg")}
    upload_response = await test_client.post("/api/v1/uploads/presign", files=files)
    audio_key = upload_response.json()["audio_key"]

    # 2. Job 생성
    with patch("src.api.routers.jobs.process_scoring_job.delay") as mock_celery:
        response = await test_client.post(
            "/api/v1/jobs",
            json={
                "audio_key": audio_key,
                "task_id": str(test_task.id),
                "task_type": "independent",
                "prompt": "Test prompt",
            },
        )

    # 검증
    assert response.status_code == 201
    data = response.json()
    assert "job_id" in data
    assert data["status"] == "QUEUED"

    # Celery 태스크가 호출되었는지 확인
    assert mock_celery.called


@pytest.mark.asyncio
async def test_create_job_invalid_audio_key(test_client: AsyncClient, test_task):
    """존재하지 않는 audio_key로 Job 생성 실패 테스트"""
    response = await test_client.post(
        "/api/v1/jobs",
        json={
            "audio_key": "audio/nonexistent.mp3",
            "task_id": str(test_task.id),
            "task_type": "independent",
            "prompt": "Test prompt",
        },
    )

    # 검증
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_create_job_missing_fields(test_client: AsyncClient):
    """필수 필드 누락 시 Job 생성 실패 테스트"""
    response = await test_client.post(
        "/api/v1/jobs",
        json={
            "audio_key": "audio/test.mp3",
            # task_id, task_type, prompt 누락
        },
    )

    # 검증
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_job_status_success(test_client: AsyncClient, test_db: AsyncSession, test_task, test_user):
    """Job 상태 조회 성공 테스트"""
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
    await test_db.refresh(job)

    # Job 상태 조회
    response = await test_client.get(f"/api/v1/jobs/{job.id}")

    # 검증
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ASR_RUNNING"
    assert data["progress"] == 30
    assert "created_at" in data
    assert "updated_at" in data


@pytest.mark.asyncio
async def test_get_job_status_not_found(test_client: AsyncClient):
    """존재하지 않는 Job 조회 실패 테스트"""
    fake_job_id = str(uuid.uuid4())
    response = await test_client.get(f"/api/v1/jobs/{fake_job_id}")

    # 검증
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_get_job_status_invalid_uuid(test_client: AsyncClient):
    """잘못된 UUID 형식으로 Job 조회 실패 테스트"""
    response = await test_client.get("/api/v1/jobs/invalid-uuid")

    # 검증
    assert response.status_code == 400
    assert "invalid" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_get_job_report_success(test_client: AsyncClient, test_db: AsyncSession, test_task, test_user):
    """Job 리포트 조회 성공 테스트"""
    # 완료된 Job 생성
    job = Job(
        id=uuid.uuid4(),
        user_id=test_user.id,
        task_id=test_task.id,
        status=JobStatus.DONE,
        progress=100,
        audio_key="audio/test.mp3",
    )
    test_db.add(job)
    await test_db.commit()
    await test_db.refresh(job)

    # Report 생성
    report = Report(
        id=uuid.uuid4(),
        job_id=job.id,
        report_json={
            "summary": {
                "line1": "Your response demonstrates good organization.",
                "line2": "There are some minor grammar errors.",
                "line3": "Vocabulary usage is appropriate for the task.",
            },
            "delivery": {
                "speed": {"status": "good", "description": "Natural speaking pace"},
                "pauses": {"status": "fair", "description": "Some hesitation noted"},
                "clarity": {"status": "good", "description": "Clear pronunciation"},
            },
            "language_use": {
                "errors": [{"type": "grammar", "example": "I was go to school"}],
                "vocabulary_level": "intermediate",
                "sentence_variety": "good",
            },
            "structure": {
                "has_intro": True,
                "has_body": True,
                "has_conclusion": True,
                "coherence": "good",
            },
            "score_band": {"min": 22, "max": 25},
            "action_items": [
                "Focus on verb tenses",
                "Practice reducing hesitation",
            ],
        },
        score_band_min=22,
        score_band_max=25,
    )
    test_db.add(report)
    await test_db.commit()

    # Report 조회
    response = await test_client.get(f"/api/v1/jobs/{job.id}/report")

    # 검증
    assert response.status_code == 200
    data = response.json()
    assert data["job_id"] == str(job.id)
    assert "report" in data
    assert data["report"]["score_band"]["min"] == 22
    assert data["report"]["score_band"]["max"] == 25
    assert "created_at" in data


@pytest.mark.asyncio
async def test_get_job_report_not_completed(test_client: AsyncClient, test_db: AsyncSession, test_task, test_user):
    """완료되지 않은 Job의 리포트 조회 실패 테스트"""
    # 진행 중인 Job 생성
    job = Job(
        id=uuid.uuid4(),
        user_id=test_user.id,
        task_id=test_task.id,
        status=JobStatus.ASR_RUNNING,
        progress=50,
        audio_key="audio/test.mp3",
    )
    test_db.add(job)
    await test_db.commit()

    # Report 조회 시도
    response = await test_client.get(f"/api/v1/jobs/{job.id}/report")

    # 검증
    assert response.status_code == 400
    assert "not completed" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_get_job_report_not_found(test_client: AsyncClient):
    """존재하지 않는 Job의 리포트 조회 실패 테스트"""
    fake_job_id = str(uuid.uuid4())
    response = await test_client.get(f"/api/v1/jobs/{fake_job_id}/report")

    # 검증
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_job_status_progression(test_client: AsyncClient, test_db: AsyncSession, test_task, test_user):
    """Job 상태 진행 테스트"""
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

    # 초기 상태 확인
    response = await test_client.get(f"/api/v1/jobs/{job.id}")
    assert response.json()["status"] == "QUEUED"

    # 상태 업데이트
    job.status = JobStatus.ASR_RUNNING
    job.progress = 30
    await test_db.commit()

    # 업데이트된 상태 확인
    response = await test_client.get(f"/api/v1/jobs/{job.id}")
    data = response.json()
    assert data["status"] == "ASR_RUNNING"
    assert data["progress"] == 30
