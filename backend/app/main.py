"""
VERITAS API entrypoint. Wires together auth, case management, evidence
pipeline, and graph query routers.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.auth.routes import router as auth_router
from app.api.routes_case import router as case_router
from app.api.routes_evidence import router as evidence_router
from app.api.routes_graph import router as graph_router
from app.db.session import engine
from app.db.postgres_models import Base

app = FastAPI(
    title="VERITAS",
    description="Verified Evidence Reasoning & Intelligence Triage Agentic System",
    version="0.1.0",
)

# Restrict this properly in production — investigator terminals only,
# never open to the public internet.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(case_router)
app.include_router(evidence_router)
app.include_router(graph_router)


@app.on_event("startup")
def on_startup():
    # Creates Postgres tables if they don't exist. In a real deployment,
    # use Alembic migrations instead of create_all — this is scaffold-only.
    Base.metadata.create_all(bind=engine)


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "VERITAS API"}
