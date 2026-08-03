"""Task wrappers for the VERITAS analysis pipeline."""

from app.celery_app import celery_app


@celery_app.task(bind=True)
def run_pipeline_task(self, case_id: str, evidence_path: str):
    """Run the full 9-agent LangGraph pipeline for one evidence file.

    `bind=True` gives the task access to `self` (task id, retry helpers) —
    needed later for retries and audit trail entries.

    Stub until Week 3: the LangGraph orchestrator does not exist yet, and
    nothing calls this task until the evidence routes land in Week 5.
    """
    raise NotImplementedError("wired to the LangGraph orchestrator in Week 3")
