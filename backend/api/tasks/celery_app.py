from celery import Celery
from celery.schedules import crontab

from core.config import settings

celery_app = Celery(
    "rec_engine",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["tasks.retrain_task", "tasks.cache_refresh_task", "tasks.ltr_retrain_task", "tasks.dna_snapshot_task"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=60 * 60,
    beat_schedule={
        "refresh-rec-cache-hourly": {
            "task": "tasks.cache_refresh_task.refresh_top_users",
            "schedule": crontab(minute=0),
        },
        "retrain-nightly": {
            "task": "tasks.retrain_task.retrain_all",
            "schedule": crontab(hour=3, minute=0),
        },
        "ltr-retrain-nightly": {
            "task": "tasks.ltr_retrain_task.retrain_ltr_from_feedback",
            "schedule": crontab(hour=3, minute=30),
        },
        "dna-snapshot-daily": {
            "task": "tasks.dna_snapshot_task.snapshot_all_users",
            "schedule": crontab(hour=2, minute=0),
        },
    },
)
