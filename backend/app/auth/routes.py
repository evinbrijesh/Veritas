"""
Login endpoint + FastAPI dependencies for protecting other routes.
Every protected route uses `get_current_investigator`, and sensitive
routes additionally use `require_role([...])`.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.auth.utils import verify_password, create_access_token, decode_access_token
from app.db.postgres_models import Investigator, AuditLog
from app.db.session import get_db  # see db/session.py

router = APIRouter(prefix="/auth", tags=["auth"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    investigator = db.query(Investigator).filter(
        Investigator.email == form_data.username
    ).first()

    if not investigator or not verify_password(form_data.password, investigator.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    token = create_access_token(subject=str(investigator.id), role=investigator.role.value)

    db.add(AuditLog(
        investigator_id=investigator.id,
        action="LOGIN",
        detail=f"{investigator.full_name} logged in",
    ))
    db.commit()

    return {"access_token": token, "token_type": "bearer", "role": investigator.role.value}


def get_current_investigator(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> Investigator:
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    investigator = db.query(Investigator).filter(Investigator.id == payload["sub"]).first()
    if investigator is None:
        raise HTTPException(status_code=401, detail="Investigator not found")
    return investigator


def require_role(allowed_roles: list[str]):
    """Usage: @router.get(...); def route(user = Depends(require_role(["supervisor", "admin"])))"""
    def role_checker(investigator: Investigator = Depends(get_current_investigator)):
        if investigator.role.value not in allowed_roles:
            raise HTTPException(status_code=403, detail="Insufficient permissions for this action")
        return investigator
    return role_checker
