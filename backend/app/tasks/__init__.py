"""Celery task wrappers — the queue glue between HTTP routes and the pipeline.

Routes call tasks with .delay(...) so the pipeline runs inside a worker,
never inside an HTTP request.
"""
