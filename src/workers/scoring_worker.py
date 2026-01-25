"""채점 파이프라인 Celery Worker

Job 상태 전이:
QUEUED → FETCHING_AUDIO → ASR_RUNNING → FEATURE_EXTRACTING
→ LLM_ANALYZING → SCORING → DONE (또는 FAILED)
"""

import logging
from typing import Any

from celery import Task
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.core.config import settings
from src.models.job import Job, JobStatus
from src.models.job_artifact import JobArtifact
from src.models.report import Report
from src.schemas.jobs import FeedbackReport
from src.schemas.scoring import ASRResult, DeliverySignals
from src.services.asr_service import get_asr_service
from src.services.delivery_features import get_delivery_feature_extractor
from src.services.feedback_service import generate_full_feedback
from src.services.storage_service import get_storage_service

# 로거 설정
logger = logging.getLogger(__name__)

# 비동기 데이터베이스 엔진 (Worker용)
async_engine = create_async_engine(
    settings.database_url_str,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

async_session_maker = sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class ScoringTask(Task):
    """채점 작업 기본 클래스"""

    autoretry_for = (Exception,)
    retry_kwargs = {"max_retries": 3}
    retry_backoff = True
    retry_backoff_max = 600
    retry_jitter = True


def process_scoring_impl(job_id: str, job_data: dict[str, Any]) -> dict[str, Any]:
    """
    채점 Job 처리 구현 함수 (동기 래퍼)

    Args:
        job_id: Job UUID 문자열
        job_data: Job 생성 데이터 (audio_key, task_id, prompt 등)

    Returns:
        처리 결과 딕셔너리

    Note:
        이 함수는 src.workers.tasks.process_scoring_job Celery task에서 호출됩니다.
        순환 참조를 방지하기 위해 Task 등록과 구현을 분리했습니다.
    """
    import asyncio

    # 이벤트 루프가 없으면 새로 생성
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    # 비동기 함수 실행
    return loop.run_until_complete(_process_scoring_job_async(job_id, job_data))


async def _process_scoring_job_async(job_id: str, job_data: dict[str, Any]) -> dict[str, Any]:
    """
    채점 Job 처리 비동기 함수

    파이프라인 단계:
    1. FETCHING_AUDIO: 오디오 파일 다운로드 및 검증
    2. ASR_RUNNING: Whisper ASR 실행
    3. FEATURE_EXTRACTING: Delivery/Language/Structure 신호 추출
    4. LLM_ANALYZING: LLM 분석 및 피드백 생성
    5. SCORING: 최종 점수 계산 및 리포트 저장
    6. DONE: 완료
    """
    async with async_session_maker() as db:
        try:
            # Job 조회
            result = await db.execute(
                select(Job).where(Job.id == job_id)
            )
            job = result.scalar_one_or_none()

            if not job:
                logger.error(f"Job {job_id} not found")
                return {"status": "error", "message": "Job not found"}

            logger.info(f"Starting scoring job {job_id}")

            # Phase 1: FETCHING_AUDIO
            await _update_job_status(db, job, JobStatus.FETCHING_AUDIO, 10)
            audio_path = await _fetch_audio(job.audio_key)
            logger.info(f"Audio fetched: {audio_path}")

            # Phase 2: ASR_RUNNING
            await _update_job_status(db, job, JobStatus.ASR_RUNNING, 30)
            asr_result = await _run_asr(audio_path)
            logger.info(f"ASR completed: {len(asr_result.segments)} segments")

            # Phase 3: FEATURE_EXTRACTING
            await _update_job_status(db, job, JobStatus.FEATURE_EXTRACTING, 50)
            delivery_features = await _extract_features(asr_result)
            logger.info(f"Features extracted: WPM={delivery_features.wpm}")

            # Phase 4: LLM_ANALYZING
            await _update_job_status(db, job, JobStatus.LLM_ANALYZING, 70)
            feedback_report = await _analyze_with_llm(
                job=job,
                transcript=asr_result.transcript,
                delivery_features=delivery_features,
            )
            logger.info(f"LLM analysis completed: score_band={feedback_report.score_band.min}-{feedback_report.score_band.max}")

            # Phase 4.5: Save JobArtifact
            await _save_job_artifact(
                db=db,
                job=job,
                asr_result=asr_result,
                delivery_features=delivery_features,
                feedback_report=feedback_report,
            )
            logger.info(f"Job artifacts saved for job {job_id}")

            # Phase 5: SCORING & Report 저장
            await _update_job_status(db, job, JobStatus.SCORING, 90)
            await _save_report(db, job, feedback_report)
            logger.info(f"Report saved for job {job_id}")

            # Phase 6: DONE
            await _update_job_status(db, job, JobStatus.DONE, 100)

            logger.info(f"Job {job_id} completed successfully")
            return {"status": "success", "job_id": job_id}

        except Exception as e:
            logger.exception(f"Job {job_id} failed: {str(e)}")

            # 실패 상태 업데이트
            if job:
                job.status = JobStatus.FAILED
                job.error_code = "PROCESSING_ERROR"
                job.error_message = str(e)
                await db.commit()

            return {"status": "error", "message": str(e)}


async def _update_job_status(
    db: AsyncSession,
    job: Job,
    status: JobStatus,
    progress: int,
) -> None:
    """Job 상태 및 진행률 업데이트"""
    job.status = status
    job.progress = progress
    await db.commit()
    await db.refresh(job)
    logger.info(f"Job {job.id} status updated: {status.value} ({progress}%)")


async def _fetch_audio(audio_key: str) -> str:
    """
    오디오 파일 가져오기 (StorageService 통합)

    Args:
        audio_key: 오디오 파일 키 (예: "audio/uuid.mp3")

    Returns:
        오디오 파일의 절대 경로 문자열

    Raises:
        RuntimeError: 파일을 찾을 수 없거나 접근할 수 없을 때
    """
    logger.info(f"Fetching audio: {audio_key}")

    try:
        storage = get_storage_service()
        audio_path = await storage.get_audio_path(audio_key)
        return str(audio_path)
    except HTTPException as e:
        logger.error(f"Failed to fetch audio {audio_key}: {e.detail}")
        raise RuntimeError(f"Audio file not found or inaccessible: {audio_key}") from e
    except Exception as e:
        logger.error(f"Unexpected error fetching audio {audio_key}: {str(e)}")
        raise RuntimeError(f"Failed to fetch audio: {str(e)}") from e


async def _run_asr(audio_path: str) -> ASRResult:
    """
    Whisper ASR 실행 (ASRService 통합)

    Args:
        audio_path: 오디오 파일 경로

    Returns:
        ASRResult: Whisper 전사 결과

    Raises:
        RuntimeError: ASR 실행 실패 시
    """
    logger.info(f"Running ASR on: {audio_path}")

    try:
        asr_service = get_asr_service()
        asr_result = await asr_service.transcribe(audio_path)
        return asr_result
    except FileNotFoundError as e:
        logger.error(f"Audio file not found: {audio_path}")
        raise RuntimeError(f"Audio file not found: {audio_path}") from e
    except Exception as e:
        logger.error(f"ASR failed for {audio_path}: {str(e)}")
        raise RuntimeError(f"ASR execution failed: {str(e)}") from e


async def _extract_features(asr_result: ASRResult) -> DeliverySignals:
    """
    Delivery 신호 추출 (DeliveryFeatureExtractor 통합)

    Args:
        asr_result: Whisper ASR 결과

    Returns:
        DeliverySignals: 추출된 Delivery 신호

    Raises:
        RuntimeError: Feature 추출 실패 시
    """
    logger.info("Extracting delivery features from ASR result")

    try:
        extractor = get_delivery_feature_extractor()
        # extract()는 동기 메서드이므로 직접 호출
        delivery_signals = extractor.extract(asr_result)
        return delivery_signals
    except ValueError as e:
        logger.error(f"Invalid ASR result for feature extraction: {str(e)}")
        raise RuntimeError(f"Feature extraction failed: {str(e)}") from e
    except Exception as e:
        logger.error(f"Feature extraction failed: {str(e)}")
        raise RuntimeError(f"Feature extraction failed: {str(e)}") from e


async def _analyze_with_llm(
    job: Job,
    transcript: str,
    delivery_features: DeliverySignals,
) -> FeedbackReport:
    """
    LLM 분석 및 피드백 생성 (FeedbackService 통합)

    Args:
        job: Job 모델 (task 정보 포함)
        transcript: Whisper 전사 텍스트
        delivery_features: Delivery 신호

    Returns:
        FeedbackReport: 최종 피드백 리포트

    Raises:
        RuntimeError: LLM 분석 실패 시
    """
    logger.info("Analyzing with LLM")

    try:
        feedback_report = await generate_full_feedback(
            task_type=job.task.task_type.value,
            prompt=job.task.prompt,
            transcript=transcript,
            delivery_features_dict=delivery_features.model_dump(),
            source_reading=job.task.source_reading,
            source_listening=job.task.source_listening,
        )
        return feedback_report
    except Exception as e:
        logger.error(f"LLM analysis failed: {str(e)}")
        raise RuntimeError(f"LLM analysis failed: {str(e)}") from e


async def _save_job_artifact(
    db: AsyncSession,
    job: Job,
    asr_result: ASRResult,
    delivery_features: DeliverySignals,
    feedback_report: FeedbackReport,
) -> None:
    """
    JobArtifact 저장 (중간 결과 저장)

    Args:
        db: 데이터베이스 세션
        job: Job 모델
        asr_result: ASR 결과
        delivery_features: Delivery 신호
        feedback_report: 피드백 리포트

    Raises:
        RuntimeError: Artifact 저장 실패 시
    """
    logger.info(f"Saving job artifacts for job {job.id}")

    try:
        artifact = JobArtifact(
            job_id=job.id,
            asr_json=asr_result.model_dump(),
            features_json=delivery_features.model_dump(),
            llm_json=feedback_report.model_dump(),
            rubric_version="toefl_speaking_2026_v1",
            pipeline_version="1.0.0",
        )

        db.add(artifact)
        await db.commit()
        await db.refresh(artifact)

        logger.info(f"Job artifact saved: {artifact.id}")
    except Exception as e:
        logger.error(f"Failed to save job artifact: {str(e)}")
        raise RuntimeError(f"Failed to save job artifact: {str(e)}") from e


async def _save_report(
    db: AsyncSession,
    job: Job,
    feedback_report: FeedbackReport,
) -> None:
    """
    최종 리포트 저장

    Args:
        db: 데이터베이스 세션
        job: Job 모델
        feedback_report: 피드백 리포트

    Raises:
        RuntimeError: Report 저장 실패 시
    """
    logger.info(f"Saving report for job {job.id}")

    try:
        # Report 레코드 생성
        report = Report(
            job_id=job.id,
            report_json=feedback_report.model_dump(),
            score_band_min=feedback_report.score_band.min,
            score_band_max=feedback_report.score_band.max,
        )

        db.add(report)
        await db.commit()
        await db.refresh(report)

        logger.info(f"Report saved: {report.id}")
    except Exception as e:
        logger.error(f"Failed to save report: {str(e)}")
        raise RuntimeError(f"Failed to save report: {str(e)}") from e
