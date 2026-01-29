"""채점 워커 테스트

scoring_worker.py의 모든 함수와 파이프라인을 테스트합니다.
"""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.job import Job, JobStatus
from src.models.report import Report
from src.schemas.jobs import FeedbackReport
from src.schemas.scoring import ASRResult, WhisperSegment
from src.workers.scoring_worker import (
    _analyze_with_llm,
    _extract_all_features,
    _fetch_audio,
    _process_scoring_job_async,
    _run_asr,
    _save_job_artifact,
    _save_report,
    _update_job_status,
)

# ============================================================================
# 테스트 픽스처
# ============================================================================


@pytest_asyncio.fixture
def mock_job(test_task, test_user) -> Job:
    """모킹된 Job 객체"""
    job = Job(
        id=uuid.uuid4(),
        user_id=test_user.id,
        task_id=test_task.id,
        status=JobStatus.QUEUED,
        progress=0,
        audio_key="audio/test.mp3",
    )
    job.task = test_task
    return job


@pytest_asyncio.fixture
def mock_feedback_report() -> FeedbackReport:
    """모킹된 FeedbackReport"""
    return FeedbackReport(
        summary_3lines=[
            "Your response shows good organization.",
            "Main issue: Minor grammar errors.",
            "With practice, you can reach higher scores.",
        ],
        bottleneck={
            "title": "문법 오류",
            "explanation": "동사 시제 일관성이 부족합니다.",
            "evidence_quote": "I was go to school",
        },
        action_items=[
            {
                "action": "동사 시제 연습",
                "why": "시제 일관성이 중요합니다",
                "how_to": "과거 시제 문장 10개 작성",
                "example_sentence": "I went to school yesterday.",
            }
        ],
        structure={
            "checklist": {
                "Intro": True,
                "Reason1": True,
                "Example1": True,
                "Reason2": False,
                "Example2": False,
                "Wrap-up": True,
            },
            "missing": ["Reason2", "Example2"],
            "suggested_template": "Intro → Reason1 → Example1 → Reason2 → Example2 → Wrap-up",
        },
        language={
            "top_errors": ["Verb tense (3)", "Article usage (2)"],
            "improved_sentences": ["I was go → I went"],
        },
        delivery={
            "speed_comment": "Natural speaking pace",
            "pause_comment": "Some hesitation noted",
            "clarity_comment": "Clear pronunciation",
        },
        score_band={"min": 22, "max": 25, "rationale": "Good organization with minor errors"},
        disclaimer="본 평가는 학습 도구이며 실제 TOEFL 점수와 다를 수 있습니다.",
    )


# ============================================================================
# process_scoring_impl 테스트
# ============================================================================


@pytest.mark.asyncio
async def test_process_scoring_impl_success(test_db: AsyncSession, mock_job, mock_feedback_report):
    """process_scoring_impl 성공 테스트"""
    # Job 저장
    test_db.add(mock_job)
    await test_db.commit()
    await test_db.refresh(mock_job)

    job_data = {
        "audio_key": mock_job.audio_key,
        "task_id": str(mock_job.task_id),
        "task_type": "independent",
        "prompt": "Test prompt",
    }

    # Mock 설정
    with (
        patch("src.workers.scoring_worker._fetch_audio", new_callable=AsyncMock) as mock_fetch,
        patch("src.workers.scoring_worker._run_asr", new_callable=AsyncMock) as mock_asr,
        patch(
            "src.workers.scoring_worker._extract_all_features", new_callable=AsyncMock
        ) as mock_features,
        patch("src.workers.scoring_worker._analyze_with_llm", new_callable=AsyncMock) as mock_llm,
        patch(
            "src.workers.scoring_worker._save_job_artifact", new_callable=AsyncMock
        ) as mock_artifact,
        patch("src.workers.scoring_worker._save_report", new_callable=AsyncMock) as mock_report,
    ):
        # Mock 반환값 설정
        mock_fetch.return_value = "/tmp/test.mp3"
        mock_asr.return_value = ASRResult(
            transcript="Test transcript",
            segments=[
                WhisperSegment(
                    id=0,
                    start=0.0,
                    end=5.0,
                    text="Test transcript",
                    tokens=[1, 2, 3],
                    temperature=0.0,
                    avg_logprob=-0.2,
                    compression_ratio=1.0,
                    no_speech_prob=0.01,
                )
            ],
            language="en",
            avg_logprob=-0.2,
            no_speech_prob=0.01,
            duration_sec=5.0,
        )
        mock_features.return_value = {
            "delivery": {"wpm": 120},
            "grammar": {"spacy_available": True},
            "vocabulary": {"types": 50},
            "blueprint": None,
            "structure": None,
        }
        mock_llm.return_value = mock_feedback_report

        # 실행 - test_db 세션을 주입하여 async 함수 호출
        from src.workers.scoring_worker import _process_scoring_job_async

        result = await _process_scoring_job_async(str(mock_job.id), job_data, db=test_db)

        # 검증
        assert result["status"] == "success"
        assert result["job_id"] == str(mock_job.id)

        # 모든 함수가 호출되었는지 확인
        assert mock_fetch.called
        assert mock_asr.called
        assert mock_features.called
        assert mock_llm.called
        assert mock_artifact.called
        assert mock_report.called


@pytest.mark.asyncio
async def test_process_scoring_impl_job_not_found(test_db: AsyncSession):
    """Job을 찾을 수 없는 경우 테스트"""
    fake_job_id = str(uuid.uuid4())
    job_data = {
        "audio_key": "audio/test.mp3",
        "task_id": str(uuid.uuid4()),
        "task_type": "independent",
        "prompt": "Test prompt",
    }

    result = await _process_scoring_job_async(fake_job_id, job_data, db=test_db)

    assert result["status"] == "error"
    assert "not found" in result["message"].lower()


# ============================================================================
# _update_job_status 테스트
# ============================================================================


@pytest.mark.asyncio
async def test_update_job_status_success(test_db: AsyncSession, mock_job):
    """Job 상태 업데이트 성공 테스트"""
    test_db.add(mock_job)
    await test_db.commit()
    await test_db.refresh(mock_job)

    await _update_job_status(test_db, mock_job, JobStatus.ASR_RUNNING, 30)

    assert mock_job.status == JobStatus.ASR_RUNNING
    assert mock_job.progress == 30


# ============================================================================
# _fetch_audio 테스트
# ============================================================================


@pytest.mark.asyncio
async def test_fetch_audio_success():
    """오디오 파일 가져오기 성공 테스트"""
    with patch("src.workers.scoring_worker.get_storage_service") as mock_storage_service:
        mock_storage = MagicMock()
        mock_storage.get_audio_path = AsyncMock(return_value="/tmp/test.mp3")
        mock_storage_service.return_value = mock_storage

        result = await _fetch_audio("audio/test.mp3")

        assert result == "/tmp/test.mp3"
        mock_storage.get_audio_path.assert_called_once_with("audio/test.mp3")


@pytest.mark.asyncio
async def test_fetch_audio_not_found():
    """오디오 파일을 찾을 수 없는 경우 테스트"""
    from fastapi import HTTPException, status

    with patch("src.workers.scoring_worker.get_storage_service") as mock_storage_service:
        mock_storage = MagicMock()
        mock_storage.get_audio_path = AsyncMock(
            side_effect=HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found",
            )
        )
        mock_storage_service.return_value = mock_storage

        with pytest.raises(RuntimeError, match="not found or inaccessible"):
            await _fetch_audio("audio/nonexistent.mp3")


# ============================================================================
# _run_asr 테스트
# ============================================================================


@pytest.mark.asyncio
async def test_run_asr_success():
    """ASR 실행 성공 테스트"""
    mock_asr_result = ASRResult(
        transcript="Test transcript",
        segments=[
            WhisperSegment(
                id=0,
                start=0.0,
                end=5.0,
                text="Test transcript",
                tokens=[1, 2, 3],
                temperature=0.0,
                avg_logprob=-0.2,
                compression_ratio=1.0,
                no_speech_prob=0.01,
            )
        ],
        language="en",
        avg_logprob=-0.2,
        no_speech_prob=0.01,
        duration_sec=5.0,
    )

    with patch("src.workers.scoring_worker.get_asr_service") as mock_asr_service:
        mock_service = MagicMock()
        mock_service.transcribe = AsyncMock(return_value=mock_asr_result)
        mock_asr_service.return_value = mock_service

        result = await _run_asr("/tmp/test.mp3")

        assert result.transcript == "Test transcript"
        assert len(result.segments) == 1
        mock_service.transcribe.assert_called_once_with("/tmp/test.mp3")


@pytest.mark.asyncio
async def test_run_asr_file_not_found():
    """ASR 실행 시 파일을 찾을 수 없는 경우 테스트"""
    with patch("src.workers.scoring_worker.get_asr_service") as mock_asr_service:
        mock_service = MagicMock()
        mock_service.transcribe = AsyncMock(side_effect=FileNotFoundError("File not found"))
        mock_asr_service.return_value = mock_service

        with pytest.raises(RuntimeError, match="Audio file not found"):
            await _run_asr("/tmp/nonexistent.mp3")


# ============================================================================
# _extract_all_features 테스트
# ============================================================================


@pytest.mark.asyncio
async def test_extract_all_features_independent_task(mock_job, mock_asr_result_model):
    """Independent Task 피처 추출 테스트"""
    with (
        patch("src.workers.scoring_worker.get_delivery_feature_extractor") as mock_delivery,
        patch("src.workers.scoring_worker.get_grammar_feature_extractor") as mock_grammar,
        patch("src.workers.scoring_worker.get_vocabulary_feature_extractor") as mock_vocab,
        patch("src.workers.scoring_worker.get_structure_comparison_service") as mock_structure,
    ):
        # Mock 설정
        mock_delivery_extractor = MagicMock()
        mock_delivery_extractor.extract.return_value = MagicMock(
            model_dump=MagicMock(return_value={"wpm": 120})
        )
        mock_delivery.return_value = mock_delivery_extractor

        mock_grammar_extractor = MagicMock()
        mock_grammar_extractor.extract.return_value = MagicMock(
            model_dump=MagicMock(return_value={"spacy_available": True})
        )
        mock_grammar.return_value = mock_grammar_extractor

        mock_vocab_extractor = MagicMock()
        mock_vocab_extractor.extract.return_value = MagicMock(
            model_dump=MagicMock(return_value={"types": 50})
        )
        mock_vocab.return_value = mock_vocab_extractor

        mock_structure_service = MagicMock()
        mock_structure_service.analyze_structure.return_value = MagicMock(
            model_dump=MagicMock(return_value={"match_percentage": 75.0})
        )
        mock_structure.return_value = mock_structure_service

        # 실행
        result = await _extract_all_features(mock_job, mock_asr_result_model)

        # 검증
        assert "delivery" in result
        assert "grammar" in result
        assert "vocabulary" in result
        assert "structure" in result
        assert result["blueprint"] is None  # Independent Task는 blueprint이 없음


# ============================================================================
# _analyze_with_llm 테스트
# ============================================================================


@pytest.mark.asyncio
async def test_analyze_with_llm_success(mock_job, mock_feedback_report):
    """LLM 분석 성공 테스트"""
    features = {
        "delivery": {"wpm": 120},
        "grammar": {"spacy_available": True},
        "vocabulary": {"types": 50},
    }

    with patch(
        "src.workers.scoring_worker.generate_full_feedback", new_callable=AsyncMock
    ) as mock_feedback:
        mock_feedback.return_value = mock_feedback_report

        result = await _analyze_with_llm(
            job=mock_job,
            transcript="Test transcript",
            all_features=features,
            tier="basic",
        )

        assert result.score_band.min == 22
        assert result.score_band.max == 25
        mock_feedback.assert_called_once()


# ============================================================================
# _save_job_artifact 테스트
# ============================================================================


@pytest.mark.asyncio
async def test_save_job_artifact_success(
    test_db: AsyncSession, mock_job, mock_asr_result_model, mock_feedback_report
):
    """JobArtifact 저장 성공 테스트"""
    test_db.add(mock_job)
    await test_db.commit()
    await test_db.refresh(mock_job)

    features = {
        "delivery": {"wpm": 120},
        "grammar": {"spacy_available": True},
        "vocabulary": {"types": 50},
    }

    await _save_job_artifact(
        db=test_db,
        job=mock_job,
        asr_result=mock_asr_result_model,
        all_features=features,
        feedback_report=mock_feedback_report,
    )

    # JobArtifact가 저장되었는지 확인
    from sqlalchemy import select

    from src.models.job_artifact import JobArtifact

    result = await test_db.execute(select(JobArtifact).where(JobArtifact.job_id == mock_job.id))
    artifact = result.scalar_one_or_none()

    assert artifact is not None
    assert artifact.job_id == mock_job.id
    assert "asr_json" in artifact.__dict__
    assert "features_json" in artifact.__dict__


# ============================================================================
# _save_report 테스트
# ============================================================================


@pytest.mark.asyncio
async def test_save_report_success(test_db: AsyncSession, mock_job, mock_feedback_report):
    """Report 저장 성공 테스트"""
    test_db.add(mock_job)
    await test_db.commit()
    await test_db.refresh(mock_job)

    await _save_report(
        db=test_db,
        job=mock_job,
        feedback_report=mock_feedback_report,
    )

    # Report가 저장되었는지 확인
    from sqlalchemy import select

    result = await test_db.execute(select(Report).where(Report.job_id == mock_job.id))
    report = result.scalar_one_or_none()

    assert report is not None
    assert report.job_id == mock_job.id
    assert report.score_band_min == 22
    assert report.score_band_max == 25


# ============================================================================
# 에러 핸들링 테스트
# ============================================================================


@pytest.mark.asyncio
async def test_process_scoring_job_async_with_error(test_db: AsyncSession, mock_job):
    """파이프라인 중 오류 발생 시 FAILED 상태로 전환 테스트"""
    test_db.add(mock_job)
    await test_db.commit()
    await test_db.refresh(mock_job)

    job_data = {
        "audio_key": mock_job.audio_key,
        "task_id": str(mock_job.task_id),
        "task_type": "independent",
        "prompt": "Test prompt",
    }

    with patch("src.workers.scoring_worker._fetch_audio", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.side_effect = RuntimeError("Audio fetch failed")

        result = await _process_scoring_job_async(str(mock_job.id), job_data, db=test_db)

        assert result["status"] == "error"
        assert "Audio fetch failed" in result["message"]

        # Job 상태가 FAILED로 변경되었는지 확인
        await test_db.refresh(mock_job)
        assert mock_job.status == JobStatus.FAILED
        assert mock_job.error_code == "PROCESSING_ERROR"
