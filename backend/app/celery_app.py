"""Celery application — the task queue that runs the 9-agent pipeline.

Both the API (producer, via .delay()) and the workers (consumer) share this
one object, loaded as `app.celery_app` (see docker-compose.yml `worker` and
`flower` services).

Broker and result backend both use settings.redis_url (Redis DB 0). The
roadmap sketched a separate DB 1 for results; we use one URL from config
and accept the shared keyspace — splitting later is a one-line change.
"""

from celery import Celery

from app.config import settings

celery_app = Celery(
    "veritas",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery_app.conf.update(
    # CRITICAL: `celery -A app.celery_app` only imports app.celery_app.
    # Without this include, tasks in app.tasks.celery_tasks are never
    # registered and .delay() calls fail with "unregistered task".
    include=["app.tasks.celery_tasks"],
    # Don't crash at boot if Redis is still warming up (compose has no
    # healthcheck gate on worker -> redis).
    broker_connection_retry_on_startup=True,
)
