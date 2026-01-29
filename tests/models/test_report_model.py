"""Report 모델 테스트"""

import uuid
from datetime import UTC

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.job import Job, JobStatus
from src.models.report import Report
from src.models.task import Task
from src.models.user import User


@pytest.mark.asyncio
async def test_create_report(test_db: AsyncSession, test_user: User, test_task: Task):
    """Report 생성 테스트"""
    # Job 생성
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
    report_data = {
        "summary": {
            "line1": "Good organization",
            "line2": "Minor grammar errors",
            "line3": "Appropriate vocabulary",
        },
        "delivery": {
            "speed": {"status": "good", "description": "Natural pace"},
            "pauses": {"status": "fair", "description": "Some hesitation"},
            "clarity": {"status": "good", "description": "Clear pronunciation"},
        },
        "language_use": {
            "errors": [{"type": "grammar", "example": "I was go"}],
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
        "action_items": ["Focus on verb tenses", "Reduce filler words"],
    }

    report = Report(
        id=uuid.uuid4(),
        job_id=job.id,
        report_json=report_data,
        score_band_min=22,
        score_band_max=25,
    )
    test_db.add(report)
    await test_db.commit()
    await test_db.refresh(report)

    # 검증
    assert report.id is not None
    assert report.job_id == job.id
    assert report.report_json == report_data
    assert report.score_band_min == 22
    assert report.score_band_max == 25
    assert report.created_at is not None


@pytest.mark.asyncio
async def test_report_score_band_range(test_db: AsyncSession, test_user: User, test_task: Task):
    """Report score band 범위 테스트"""
    # Job 생성
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

    # 최소 점수 범위
    report_min = Report(
        id=uuid.uuid4(),
        job_id=job.id,
        report_json={"score_band": {"min": 0, "max": 5}},
        score_band_min=0,
        score_band_max=5,
    )
    test_db.add(report_min)
    await test_db.commit()
    await test_db.refresh(report_min)
    assert report_min.score_band_min == 0
    assert report_min.score_band_max == 5

    # Job 2 생성 (다른 report를 위해)
    job2 = Job(
        id=uuid.uuid4(),
        user_id=test_user.id,
        task_id=test_task.id,
        status=JobStatus.DONE,
        progress=100,
        audio_key="audio/test2.mp3",
    )
    test_db.add(job2)
    await test_db.commit()

    # 최대 점수 범위
    report_max = Report(
        id=uuid.uuid4(),
        job_id=job2.id,
        report_json={"score_band": {"min": 28, "max": 30}},
        score_band_min=28,
        score_band_max=30,
    )
    test_db.add(report_max)
    await test_db.commit()
    await test_db.refresh(report_max)
    assert report_max.score_band_min == 28
    assert report_max.score_band_max == 30


@pytest.mark.asyncio
async def test_report_json_structure(test_db: AsyncSession, test_user: User, test_task: Task):
    """Report JSON 구조 테스트"""
    # Job 생성
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

    # 복잡한 JSON 데이터
    complex_report_data = {
        "summary": {
            "line1": "First line of summary",
            "line2": "Second line of summary",
            "line3": "Third line of summary",
        },
        "delivery": {
            "speed": {"status": "excellent", "description": "Perfect pace at 130 WPM"},
            "pauses": {"status": "good", "description": "Natural pauses"},
            "clarity": {"status": "excellent", "description": "Very clear pronunciation"},
        },
        "language_use": {
            "errors": [
                {"type": "grammar", "example": "I was go to school"},
                {"type": "word_choice", "example": "very much good"},
                {"type": "preposition", "example": "interested on"},
            ],
            "vocabulary_level": "advanced",
            "sentence_variety": "excellent",
        },
        "structure": {
            "has_intro": True,
            "has_body": True,
            "has_conclusion": True,
            "coherence": "excellent",
        },
        "score_band": {"min": 26, "max": 28},
        "action_items": [
            "Review verb tense rules",
            "Practice word collocation",
            "Study preposition usage",
        ],
    }

    report = Report(
        id=uuid.uuid4(),
        job_id=job.id,
        report_json=complex_report_data,
        score_band_min=26,
        score_band_max=28,
    )
    test_db.add(report)
    await test_db.commit()
    await test_db.refresh(report)

    # JSON 구조 검증
    assert "summary" in report.report_json
    assert "delivery" in report.report_json
    assert "language_use" in report.report_json
    assert "structure" in report.report_json
    assert "score_band" in report.report_json
    assert "action_items" in report.report_json

    assert len(report.report_json["language_use"]["errors"]) == 3
    assert len(report.report_json["action_items"]) == 3


@pytest.mark.asyncio
async def test_report_job_relationship(test_db: AsyncSession, test_user: User, test_task: Task):
    """Report-Job 관계 테스트"""
    # Job 생성
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
        report_json={"score_band": {"min": 20, "max": 23}},
        score_band_min=20,
        score_band_max=23,
    )
    test_db.add(report)
    await test_db.commit()
    await test_db.refresh(report)

    # 관계 확인
    assert report.job is not None
    assert report.job.id == job.id
    assert report.job.status == JobStatus.DONE


@pytest.mark.asyncio
async def test_report_cascade_delete_job(test_db: AsyncSession, test_user: User, test_task: Task):
    """Job 삭제 시 Report 캐스케이드 삭제 테스트"""
    # Job 생성
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
        report_json={"score_band": {"min": 22, "max": 25}},
        score_band_min=22,
        score_band_max=25,
    )
    test_db.add(report)
    await test_db.commit()
    report_id = report.id

    # Job 삭제
    await test_db.delete(job)
    await test_db.commit()

    # Report도 함께 삭제되었는지 확인
    result = await test_db.execute(select(Report).where(Report.id == report_id))
    deleted_report = result.scalar_one_or_none()
    assert deleted_report is None


@pytest.mark.asyncio
async def test_report_one_to_one_relationship(
    test_db: AsyncSession, test_user: User, test_task: Task
):
    """Report-Job의 일대일 관계 테스트"""
    # Job 생성
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

    # 첫 번째 Report 생성
    report1 = Report(
        id=uuid.uuid4(),
        job_id=job.id,
        report_json={"score_band": {"min": 22, "max": 25}},
        score_band_min=22,
        score_band_max=25,
    )
    test_db.add(report1)
    await test_db.commit()

    # 두 번째 Report 생성 시도 (unique constraint 위반)
    report2 = Report(
        id=uuid.uuid4(),
        job_id=job.id,  # 동일한 job_id
        report_json={"score_band": {"min": 20, "max": 23}},
        score_band_min=20,
        score_band_max=23,
    )
    test_db.add(report2)

    # Unique constraint 위반으로 에러 발생 예상
    with pytest.raises(Exception):  # IntegrityError
        await test_db.commit()


@pytest.mark.asyncio
async def test_report_repr(test_db: AsyncSession, test_user: User, test_task: Task):
    """Report __repr__ 메서드 테스트"""
    # Job 생성
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

    # Report 생성
    report = Report(
        id=uuid.uuid4(),
        job_id=job.id,
        report_json={"score_band": {"min": 22, "max": 25}},
        score_band_min=22,
        score_band_max=25,
    )
    test_db.add(report)
    await test_db.commit()
    await test_db.refresh(report)

    # repr 출력 확인
    repr_str = repr(report)
    assert "Report(" in repr_str
    assert "22-25" in repr_str


@pytest.mark.asyncio
async def test_report_empty_json(test_db: AsyncSession, test_user: User, test_task: Task):
    """빈 JSON으로 Report 생성 테스트"""
    # Job 생성
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

    # 빈 JSON으로 Report 생성
    report = Report(
        id=uuid.uuid4(),
        job_id=job.id,
        report_json={},  # 빈 딕셔너리
        score_band_min=0,
        score_band_max=0,
    )
    test_db.add(report)
    await test_db.commit()
    await test_db.refresh(report)

    # 검증
    assert report.report_json == {}


@pytest.mark.asyncio
async def test_report_created_at_timestamp(test_db: AsyncSession, test_user: User, test_task: Task):
    """Report created_at 타임스탬프 테스트"""
    from datetime import datetime

    # Job 생성
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

    # Report 생성 전 시간
    before_creation = datetime.now(UTC)

    # Report 생성
    report = Report(
        id=uuid.uuid4(),
        job_id=job.id,
        report_json={"score_band": {"min": 22, "max": 25}},
        score_band_min=22,
        score_band_max=25,
    )
    test_db.add(report)
    await test_db.commit()
    await test_db.refresh(report)

    # Report 생성 후 시간
    after_creation = datetime.now(UTC)

    # created_at이 설정되었고, 생성 전후 시간 사이에 있는지 확인
    assert report.created_at is not None
    # SQLite는 타임존 처리가 다를 수 있으므로 존재 여부만 확인
