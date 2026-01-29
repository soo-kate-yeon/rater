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


# ============================================================================
# 추가 테스트 (커버리지 향상)
# ============================================================================


@pytest.mark.asyncio
async def test_create_job_with_minimal_fields(
    test_client: AsyncClient,
    test_task,
    sample_audio_file: bytes,
    cleanup_storage,
):
    """최소 필수 필드만으로 Job 생성"""
    # 파일 업로드
    files = {"file": ("minimal.mp3", io.BytesIO(sample_audio_file), "audio/mpeg")}
    upload_response = await test_client.post("/api/v1/uploads/presign", files=files)
    audio_key = upload_response.json()["audio_key"]

    # Job 생성
    with patch("src.api.routers.jobs.process_scoring_job.delay") as mock_celery:
        response = await test_client.post(
            "/api/v1/jobs",
            json={
                "audio_key": audio_key,
                "task_id": str(test_task.id),
                "task_type": "independent",
                "prompt": "Minimal prompt",
            },
        )

    assert response.status_code == 201
    assert mock_celery.called


@pytest.mark.asyncio
async def test_create_job_with_task_data(
    test_client: AsyncClient,
    test_task,
    sample_audio_file: bytes,
    cleanup_storage,
):
    """task_type과 prompt가 포함된 Job 생성"""
    # 파일 업로드
    files = {"file": ("test.mp3", io.BytesIO(sample_audio_file), "audio/mpeg")}
    upload_response = await test_client.post("/api/v1/uploads/presign", files=files)
    audio_key = upload_response.json()["audio_key"]

    # Job 생성 (모든 필드 포함)
    with patch("src.api.routers.jobs.process_scoring_job.delay") as mock_celery:
        response = await test_client.post(
            "/api/v1/jobs",
            json={
                "audio_key": audio_key,
                "task_id": str(test_task.id),
                "task_type": "integrated",
                "prompt": "Integrated task prompt",
                "tier": "premium",
            },
        )

    assert response.status_code == 201
    data = response.json()
    assert "job_id" in data
    assert data["status"] == "QUEUED"

    # Celery 태스크 인자 확인
    call_args = mock_celery.call_args[0]
    job_data = call_args[1]
    assert job_data["task_type"] == "integrated"
    assert job_data["prompt"] == "Integrated task prompt"


@pytest.mark.asyncio
async def test_get_job_status_with_error(test_client: AsyncClient, test_db: AsyncSession, test_task, test_user):
    """실패한 Job의 상태 조회 (error_code와 error_message 포함)"""
    # 실패한 Job 생성
    job = Job(
        id=uuid.uuid4(),
        user_id=test_user.id,
        task_id=test_task.id,
        status=JobStatus.FAILED,
        progress=50,
        audio_key="audio/test.mp3",
        error_code="ASR_ERROR",
        error_message="ASR processing failed",
    )
    test_db.add(job)
    await test_db.commit()
    await test_db.refresh(job)

    # Job 상태 조회
    response = await test_client.get(f"/api/v1/jobs/{job.id}")

    # 검증
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "FAILED"
    assert data["error_code"] == "ASR_ERROR"
    assert data["error_message"] == "ASR processing failed"


@pytest.mark.asyncio
async def test_get_job_report_report_not_found(
    test_client: AsyncClient, test_db: AsyncSession, test_task, test_user
):
    """완료된 Job이지만 Report가 없는 경우 404"""
    # 완료된 Job 생성 (Report 없음)
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

    # Report 조회 시도
    response = await test_client.get(f"/api/v1/jobs/{job.id}/report")

    # 검증
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_get_job_report_invalid_uuid(test_client: AsyncClient):
    """잘못된 UUID 형식으로 Report 조회 시 400"""
    response = await test_client.get("/api/v1/jobs/invalid-uuid/report")

    assert response.status_code == 400
    assert "invalid" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_job_status_all_transitions(
    test_client: AsyncClient, test_db: AsyncSession, test_task, test_user
):
    """모든 Job 상태 전이 테스트"""
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

    # 상태 전이 시퀀스
    transitions = [
        (JobStatus.FETCHING_AUDIO, 10),
        (JobStatus.ASR_RUNNING, 30),
        (JobStatus.FEATURE_EXTRACTING, 50),
        (JobStatus.LLM_ANALYZING, 70),
        (JobStatus.SCORING, 90),
        (JobStatus.DONE, 100),
    ]

    for status, progress in transitions:
        job.status = status
        job.progress = progress
        await test_db.commit()

        response = await test_client.get(f"/api/v1/jobs/{job.id}")
        data = response.json()
        assert data["status"] == status.value
        assert data["progress"] == progress


@pytest.mark.asyncio
async def test_create_job_storage_service_error(test_client: AsyncClient, test_task):
    """StorageService 에러 발생 시 처리"""
    with patch("src.api.routers.jobs.get_storage_service") as mock_storage_service:
        from fastapi import HTTPException, status

        mock_storage = MagicMock()
        mock_storage.get_audio_path = AsyncMock(
            side_effect=HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Storage error",
            )
        )
        mock_storage_service.return_value = mock_storage

        response = await test_client.post(
            "/api/v1/jobs",
            json={
                "audio_key": "audio/test.mp3",
                "task_id": str(test_task.id),
                "task_type": "independent",
                "prompt": "Test prompt",
            },
        )

        # StorageService 에러는 500으로 전파됨
        assert response.status_code == 500


@pytest.mark.asyncio
async def test_get_job_report_with_complex_feedback(
    test_client: AsyncClient, test_db: AsyncSession, test_task, test_user
):
    """복잡한 피드백 구조를 포함한 Report 조회"""
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

    # 복잡한 Report 생성
    complex_report = {
        "summary_3lines": ["Line 1", "Line 2", "Line 3"],
        "bottleneck": {
            "title": "Grammar Issues",
            "explanation": "Verb tense inconsistency",
            "evidence_quote": "I was go to school",
        },
        "action_items": [
            {
                "action": "Practice verb tenses",
                "why": "Improve grammar",
                "how_to": "Write 10 sentences",
                "example_sentence": "I went to school.",
            }
        ],
        "structure": {
            "checklist": {
                "Intro": True,
                "Reason1": True,
                "Example1": False,
                "Reason2": False,
                "Example2": False,
                "Wrap-up": True,
            },
            "missing": ["Example1", "Reason2", "Example2"],
            "suggested_template": "Intro → Reason1 → Example1 → Wrap-up",
        },
        "language": {
            "top_errors": ["Verb tense (5)", "Article (3)"],
            "improved_sentences": ["I was go → I went"],
        },
        "delivery": {
            "speed_comment": "Good pace",
            "pause_comment": "Some hesitation",
            "clarity_comment": "Clear",
        },
        "score_band": {"min": 20, "max": 23, "rationale": "Good with minor issues"},
        "disclaimer": "This is a learning tool.",
    }

    report = Report(
        id=uuid.uuid4(),
        job_id=job.id,
        report_json=complex_report,
        score_band_min=20,
        score_band_max=23,
    )
    test_db.add(report)
    await test_db.commit()

    # Report 조회
    response = await test_client.get(f"/api/v1/jobs/{job.id}/report")

    # 검증
    assert response.status_code == 200
    data = response.json()
    assert data["report"]["bottleneck"]["title"] == "Grammar Issues"
    assert len(data["report"]["action_items"]) == 1
    assert data["report"]["structure"]["checklist"]["Intro"] is True
    assert "Verb tense" in data["report"]["language"]["top_errors"][0]


@pytest.mark.asyncio
async def test_create_job_celery_task_parameters(
    test_client: AsyncClient,
    test_task,
    sample_audio_file: bytes,
    cleanup_storage,
):
    """Celery 태스크에 전달되는 파라미터 검증"""
    # 파일 업로드
    files = {"file": ("test.mp3", io.BytesIO(sample_audio_file), "audio/mpeg")}
    upload_response = await test_client.post("/api/v1/uploads/presign", files=files)
    audio_key = upload_response.json()["audio_key"]

    # Job 생성
    with patch("src.api.routers.jobs.process_scoring_job.delay") as mock_celery:
        response = await test_client.post(
            "/api/v1/jobs",
            json={
                "audio_key": audio_key,
                "task_id": str(test_task.id),
                "task_type": "independent",
                "prompt": "Test prompt",
                "tier": "premium",
            },
        )

    # Celery 태스크 호출 검증
    assert response.status_code == 201
    job_id = response.json()["job_id"]

    # delay 메서드가 올바른 인자로 호출되었는지 확인
    mock_celery.assert_called_once()
    call_args = mock_celery.call_args[0]
    assert call_args[0] == job_id  # job_id
    assert call_args[1]["audio_key"] == audio_key
    assert call_args[1]["task_type"] == "independent"
    assert call_args[1]["tier"] == "premium"
