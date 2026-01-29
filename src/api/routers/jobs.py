"""채점 Job 라우터"""

import uuid
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.models.job import Job
from src.models.job import JobStatus as JobStatusEnum
from src.models.report import Report
from src.schemas.jobs import (
    FeedbackReport,
    JobCreate,
    JobResponse,
    JobStatus,
    JobStatusResponse,
    ReportResponse,
)
from src.services.storage_service import StorageService, get_storage_service
from src.workers.tasks import process_scoring_job

router = APIRouter()


@router.post("", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
async def create_job(
    job_data: JobCreate,
    db: AsyncSession = Depends(get_db),
    storage: StorageService = Depends(get_storage_service),
) -> JobResponse:
    """
    채점 Job 생성 엔드포인트

    Args:
        job_data: Job 생성 정보 (audio_key, task_id, task_type, prompt 등)
        db: 데이터베이스 세션
        storage: 스토리지 서비스

    Returns:
        생성된 Job 정보 (job_id, status)

    Raises:
        HTTPException: audio_key 검증 실패 또는 Job 생성 실패 시
    """
    # 1. audio_key 검증 (파일 존재 여부 확인)
    try:
        await storage.get_audio_path(job_data.audio_key)
    except HTTPException as e:
        # 파일이 존재하지 않으면 404 반환
        if e.status_code == status.HTTP_404_NOT_FOUND:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Audio file not found: {job_data.audio_key}",
            ) from e
        raise

    # 2. Job 레코드 생성
    new_job = Job(
        id=uuid.uuid4(),
        user_id=uuid.UUID("00000000-0000-0000-0000-000000000001"),  # TODO: JWT에서 추출
        task_id=uuid.UUID(job_data.task_id),
        status=JobStatusEnum.QUEUED,
        progress=0,
        audio_key=job_data.audio_key,
    )
    db.add(new_job)
    await db.commit()
    await db.refresh(new_job)

    # 3. Celery 태스크 생성 (비동기 채점 시작)
    process_scoring_job.delay(str(new_job.id), job_data.model_dump())

    return JobResponse(
        job_id=str(new_job.id),
        status=JobStatus(new_job.status.value),
    )


@router.get("/{job_id}", response_model=JobStatusResponse)
async def get_job_status(
    job_id: str,
    db: AsyncSession = Depends(get_db),
) -> JobStatusResponse:
    """
    Job 상태 조회 엔드포인트

    Args:
        job_id: Job UUID
        db: 데이터베이스 세션

    Returns:
        Job 상태 정보 (status, progress, created_at, updated_at)

    Raises:
        HTTPException: Job을 찾을 수 없는 경우 (404)
    """
    try:
        job_uuid = UUID(job_id)
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid job_id format",
        ) from err

    result = await db.execute(select(Job).where(Job.id == job_uuid))
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )

    return JobStatusResponse.model_validate(job)


@router.get("/{job_id}/report", response_model=ReportResponse)
async def get_job_report(
    job_id: str,
    db: AsyncSession = Depends(get_db),
) -> ReportResponse:
    """
    Job 최종 리포트 조회 엔드포인트

    Args:
        job_id: Job UUID
        db: 데이터베이스 세션

    Returns:
        최종 피드백 리포트

    Raises:
        HTTPException: Job 또는 리포트를 찾을 수 없는 경우 (404)
        HTTPException: Job이 아직 완료되지 않은 경우 (400)
    """
    # Job ID 검증
    try:
        job_uuid = UUID(job_id)
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid job_id format",
        ) from err

    # Job 조회
    result = await db.execute(select(Job).where(Job.id == job_uuid))
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )

    # Job 완료 여부 확인
    if job.status != JobStatusEnum.DONE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Job is not completed yet. Current status: {job.status.value}",
        )

    # 리포트 조회
    result = await db.execute(select(Report).where(Report.job_id == job_uuid))
    report = result.scalar_one_or_none()

    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found",
        )

    # FeedbackReport 스키마로 변환
    feedback_report = FeedbackReport.model_validate(report.report_json)

    return ReportResponse(
        job_id=str(job.id),
        report=feedback_report,
        created_at=report.created_at,
    )
