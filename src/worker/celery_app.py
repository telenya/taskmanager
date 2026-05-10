from celery import Celery

from src.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "task_manager",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["src.worker.tasks"],
)

celery_app.conf.update(
    timezone=settings.timezone,
    enable_utc=True,
    task_track_started=True,
    beat_schedule={
        "send-deadline-reminders-every-minute": {
            "task": "src.worker.tasks.send_deadline_reminders",
            "schedule": 60.0,
        },
    },
)
