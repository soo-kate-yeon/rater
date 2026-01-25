"""Celery Task 등록 파일

순환 참조를 방지하기 위해 Task 등록과 구현 로직을 분리합니다.
- Task 등록: 이 파일 (tasks.py)
- 구현 로직: scoring_worker.py
"""

from typing import Any

from celery import Task

from src.core.celery import celery_app
from src.workers.scoring_worker import ScoringTask, process_scoring_impl


@celery_app.task(
    bind=True,
    base=ScoringTask,
    name="src.workers.scoring_worker.process_scoring_job",
)
def process_scoring_job(self: Task, job_id: str, job_data: dict[str, Any]) -> dict[str, Any]:
    """
    비동기 채점 작업 Task

    Args:
        job_id: Job UUID 문자열
        job_data: Job 생성 데이터 (audio_key, task_id, prompt 등)

    Returns:
        처리 결과 딕셔너리

    Note:
        실제 구현은 src.workers.scoring_worker.process_scoring_impl에서 처리됩니다.
    """
    return process_scoring_impl(job_id, job_data)
