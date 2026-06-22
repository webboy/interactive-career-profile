from celery import Celery

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "interactive_career_profile",
    broker=settings.celery_broker_url,
    include=["app.worker.tasks"],
)

celery_app.conf.update(
    task_always_eager=settings.celery_task_always_eager,
    task_ignore_result=True,
    task_track_started=True,
    task_serializer="json",
    accept_content=["json"],
    timezone="UTC",
)
