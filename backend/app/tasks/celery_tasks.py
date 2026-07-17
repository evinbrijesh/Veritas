"""
Celery task definitions. The FastAPI layer enqueues these instead of
running the pipeline inline, so a big evidence batch (e.g. 10 seized
phones) doesn't block the API or get lost if a single file's
processing crashes.
"""
from app.celery_app import celery_app
from app.agents.orchestrator import run_pipeline


@celery_app.task(bind=True, name="run_case_pipeline")
def run_case_pipeline_task(self, case_id: str, evidence_file_paths: list[str]) -> dict:
    """
    Runs the full 9-agent pipeline for a case. Returns the final
    PipelineState as a plain dict (Celery/Redis need JSON-serializable
    results).
    """
    result_state = run_pipeline(case_id, evidence_file_paths)
    return dict(result_state)


@celery_app.task(name="process_single_file")
def process_single_file_task(case_id: str, file_path: str) -> dict:
    """
    Fine-grained variant — useful when you want per-file progress
    tracking in the UI rather than waiting on the whole batch.
    """
    result_state = run_pipeline(case_id, [file_path])
    return dict(result_state)
