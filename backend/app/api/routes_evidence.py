"""
Evidence pipeline endpoints. Every action here writes an AuditLog row —
this is the legal chain-of-custody trail.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from celery.result import AsyncResult

from app.schemas.evidence import PipelineRunRequest, PipelineRunResponse
from app.tasks.celery_tasks import run_case_pipeline_task
from app.auth.routes import get_current_investigator
from app.db.postgres_models import Investigator, AuditLog
from app.db.session import get_db

router = APIRouter(prefix="/evidence", tags=["evidence"])


@router.post("/run-pipeline", response_model=PipelineRunResponse)
def run_pipeline_endpoint(
    request: PipelineRunRequest,
    investigator: Investigator = Depends(get_current_investigator),
    db: Session = Depends(get_db),
):
    task = run_case_pipeline_task.delay(request.case_id, request.evidence_file_paths)

    db.add(AuditLog(
        investigator_id=investigator.id,
        action="RAN_PIPELINE",
        target_reference=request.case_id,
        detail=f"Queued {len(request.evidence_file_paths)} file(s) for processing. task_id={task.id}",
    ))
    db.commit()

    return PipelineRunResponse(task_id=task.id, status="queued")


@router.get("/pipeline-status/{task_id}")
def get_pipeline_status(task_id: str, investigator: Investigator = Depends(get_current_investigator)):
    result = AsyncResult(task_id)
    return {
        "task_id": task_id,
        "status": result.status,       # PENDING, STARTED, SUCCESS, FAILURE
        "result": result.result if result.ready() else None,
    }


@router.post("/approve-review/{case_id}")
def approve_human_review(
    case_id: str,
    investigator: Investigator = Depends(get_current_investigator),
    db: Session = Depends(get_db),
):
    """
    Supervisor-only sign-off for reports flagged requires_human_review.
    Role enforcement happens via require_role in a real deployment —
    wire this the same way as the auth.routes examples.
    """
    db.add(AuditLog(
        investigator_id=investigator.id,
        action="APPROVED_REVIEW",
        target_reference=case_id,
        detail="Supervisor approved report for finalization.",
    ))
    db.commit()
    return {"status": "approved", "case_id": case_id}
