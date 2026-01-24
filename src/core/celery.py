"""Celery 애플리케이션 초기화 및 설정"""

from celery import Celery

from src.core.config import settings

# Celery 애플리케이션 인스턴스 생성
celery_app = Celery(
    "toefl_rater",
    broker=settings.redis_url_str,
    backend=settings.redis_url_str,
)

# Celery 설정
celery_app.conf.update(
    # 작업 결과 설정
    result_expires=3600,  # 1시간 후 결과 삭제
    result_backend_transport_options={"master_name": "mymaster"},
    # 작업 직렬화
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    # 타임존
    timezone="Asia/Seoul",
    enable_utc=True,
    # 재시도 설정
    task_acks_late=True,  # 작업 완료 후 ACK
    task_reject_on_worker_lost=True,  # Worker 손실 시 재시도
    # Worker 설정
    worker_prefetch_multiplier=1,  # 한 번에 하나의 작업만 가져옴
    worker_max_tasks_per_child=100,  # 메모리 누수 방지
    # 작업 라우팅
    task_routes={
        "src.workers.scoring_worker.*": {"queue": "scoring"},
    },
    # 작업 우선순위
    task_default_priority=5,
    task_queue_max_priority=10,
)

# 작업 자동 발견 설정
celery_app.autodiscover_tasks(["src.workers"])

# Celery Beat 스케줄 (선택사항 - 향후 주기적 작업용)
celery_app.conf.beat_schedule = {
    # 예: 매일 자정에 임시 파일 정리
    # "cleanup-temp-files": {
    #     "task": "src.workers.maintenance.cleanup_temp_files",
    #     "schedule": crontab(hour=0, minute=0),
    # },
}
