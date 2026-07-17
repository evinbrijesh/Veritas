"""
Celery application instance. Workers import this to register tasks.
Redis is used as both broker (task queue) and result backend.
"""
from celery import Celery
from app.config import settings

celery_app = Celery(
    "veritas",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.tasks.celery_tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    # Evidence processing tasks can be slow (ML inference) — don't let
    # one hung worker silently swallow a task forever.
    task_time_limit=60 * 30,       # hard kill after 30 min
    task_soft_time_limit=60 * 25,  # warn at 25 min
    worker_prefetch_multiplier=1,  # fair scheduling across large batches
    task_acks_late=True,           # re-queue task if worker crashes mid-run
)
