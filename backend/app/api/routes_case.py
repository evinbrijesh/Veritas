"""
Basic case CRUD — creating a case is the first step before evidence
can be attached and the pipeline run against it.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.db.session import get_db
from app.db.postgres_models import Case, AuditLog, Investigator
from app.auth.routes import get_current_investigator

router = APIRouter(prefix="/cases", tags=["cases"])


class CaseCreateRequest(BaseModel):
    case_number: str
    title: str
    description: str | None = None


@router.post("/")
def create_case(
    request: CaseCreateRequest,
    investigator: Investigator = Depends(get_current_investigator),
    db: Session = Depends(get_db),
):
    case = Case(
        case_number=request.case_number,
        title=request.title,
        description=request.description,
        created_by=investigator.id,
    )
    db.add(case)
    db.add(AuditLog(
        investigator_id=investigator.id,
        action="CREATED_CASE",
        target_reference=request.case_number,
    ))
    db.commit()
    db.refresh(case)
    return case


@router.get("/")
def list_cases(investigator: Investigator = Depends(get_current_investigator), db: Session = Depends(get_db)):
    return db.query(Case).all()
