---
tags: [veritas, hackp, build-log, from-scratch]
status: in-progress
---

# VERITAS — From-Scratch Build Roadmap

> Each day: which file(s) to create, and the skeleton to put in them. You fill in the actual logic — this just gives you the structure, signatures, and TODOs so you're not staring at a blank file.
> Pace: ~3–4 hrs/day, 5 days/week, no fixed deadline.

---

## Week 1 — Project Skeleton & Infra

### Day 1 — Repo root files
**Create:**
- [x] `veritas/docker-compose.yml`
- [x] `veritas/.env.example`
- [x] `veritas/.gitignore`
- [x] `veritas/README.md`

```yaml
# docker-compose.yml
version: "3.9"
services:
  postgres:
    image: postgres:16
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
    volumes:
      - ./data/postgres:/var/lib/postgresql/data
    ports: ["5432:5432"]

  redis:
    image: redis:7
    volumes:
      - ./data/redis:/data
    ports: ["6379:6379"]

  neo4j:
    image: neo4j:5-community
    environment:
      NEO4J_AUTH: neo4j/${NEO4J_PASSWORD}
    volumes:
      - ./data/neo4j:/data
    ports: ["7474:7474", "7687:7687"]

  ollama:
    image: ollama/ollama
    volumes:
      - ./data/ollama:/root/.ollama
    ports: ["11434:11434"]

  backend:
    build: ./backend
    env_file: .env
    depends_on: [postgres, redis, neo4j, ollama]
    volumes:
      - ./data/evidence_storage:/evidence_storage
    ports: ["8000:8000"]
    # TODO: command to run uvicorn app.main:app

  celery:
    build: ./backend
    env_file: .env
    depends_on: [redis, backend]
    # TODO: command to run celery worker

  flower:
    build: ./backend
    env_file: .env
    depends_on: [redis, celery]
    ports: ["5555:5555"]
    # TODO: command to run flower
```

```bash
# .env.example
POSTGRES_USER=
POSTGRES_PASSWORD=
POSTGRES_DB=veritas
NEO4J_PASSWORD=
JWT_SECRET_KEY=
OLLAMA_HOST=http://ollama:11434
SYNTHETIC_DETECTOR_MODEL_PATH=/models/efficientnet_b4_synthetic.pt
```

---

### Day 2 — Backend build files
**Create:**
- [x] `veritas/backend/Dockerfile`
- [x] `veritas/backend/requirements.txt`

```dockerfile
# backend/Dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
# TODO: CMD to launch uvicorn (overridden per-service in compose)
```

```text
# backend/requirements.txt
fastapi
uvicorn[standard]
pydantic-settings
sqlalchemy
psycopg2-binary
neo4j
celery
redis
langgraph
langchain-core
passlib[bcrypt]
pyjwt
python-multipart
torch
torchvision
timm
pillow
requests
pymediainfo
pytest
httpx
```

> [!success] Checkpoint
> `docker compose build backend` completes with no dependency errors.

---

### Day 3 — App entrypoint + config
**Create:**
- [x] `veritas/backend/app/__init__.py` (empty)
- [x] `veritas/backend/app/config.py`
- [x] `veritas/backend/app/main.py`

```python
# app/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    postgres_user: str
    postgres_password: str
    postgres_db: str
    neo4j_password: str
    jwt_secret_key: str
    ollama_host: str
    synthetic_detector_model_path: str

    class Config:
        env_file = ".env"

settings = Settings()
```

```python
# app/main.py
from fastapi import FastAPI

app = FastAPI(title="VERITAS")

# TODO: import and include routers once they exist
# from app.auth.routes import router as auth_router
# from app.api.routes_case import router as case_router
# from app.api.routes_evidence import router as evidence_router
# from app.api.routes_graph import router as graph_router
# app.include_router(auth_router, prefix="/auth")
# app.include_router(case_router, prefix="/cases")
# app.include_router(evidence_router, prefix="/evidence")
# app.include_router(graph_router, prefix="/graph")

@app.get("/health")
def health():
    return {"status": "ok"}
```

> [!success] Checkpoint
> `localhost:8000/docs` loads and shows `/health`.

---

### Day 4 — Celery wiring
**Create:**
- [ ] `veritas/backend/app/celery_app.py`
- [ ] `veritas/backend/app/tasks/__init__.py` (empty)
- [ ] `veritas/backend/app/tasks/celery_tasks.py`

```python
# app/celery_app.py
from celery import Celery
from app.config import settings

celery_app = Celery(
    "veritas",
    broker="redis://redis:6379/0",
    backend="redis://redis:6379/1",
)
# TODO: celery_app.conf updates (task routes, serialization, etc.)
```

```python
# app/tasks/celery_tasks.py
from app.celery_app import celery_app

@celery_app.task(bind=True)
def run_pipeline_task(self, case_id: str, evidence_path: str):
    """Async wrapper that kicks off the LangGraph pipeline for one evidence file."""
    # TODO: import orchestrator once it exists, invoke with initial PipelineState
    raise NotImplementedError
```

> [!success] Checkpoint
> Flower dashboard loads at `localhost:5555` and shows the worker as online.

---

### Day 5 — DB session + backup script
**Create:**
- [ ] `veritas/backend/app/db/__init__.py` (empty)
- [ ] `veritas/backend/app/db/session.py`
- [ ] `veritas/backend/scripts/backup_neo4j.sh`

```python
# app/db/session.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config import settings

DATABASE_URL = f"postgresql://{settings.postgres_user}:{settings.postgres_password}@postgres:5432/{settings.postgres_db}"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

```bash
#!/bin/bash
# backend/scripts/backup_neo4j.sh
set -e
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/data/backups"
# TODO: neo4j-admin dump command targeting $BACKUP_DIR/neo4j_$TIMESTAMP.dump
echo "TODO: implement dump"
```

> [!success] Checkpoint — Week 1
> Full `docker compose up -d` boots all 7 services clean. `/health` responds. A manual backup script run produces a file (even if the dump command is still a TODO stub for now).

---

## Week 2 — Auth & Data Models

### Day 1 — Postgres models
**Create:**
- [ ] `veritas/backend/app/db/postgres_models.py`

```python
# app/db/postgres_models.py
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base
import uuid, datetime

Base = declarative_base()

class Investigator(Base):
    __tablename__ = "investigators"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, nullable=False)  # analyst | supervisor | auditor | admin

class Case(Base):
    __tablename__ = "cases"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String, nullable=False)
    created_by = Column(String, ForeignKey("investigators.id"))
    status = Column(String, default="open")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class AuditLog(Base):
    __tablename__ = "audit_log"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    investigator_id = Column(String, ForeignKey("investigators.id"))
    action = Column(String, nullable=False)
    target_reference = Column(String)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    # TODO: after table is created, revoke UPDATE/DELETE grants for the app DB role
```

---

### Day 2 — Auth utils
**Create:**
- [ ] `veritas/backend/app/auth/__init__.py` (empty)
- [ ] `veritas/backend/app/auth/utils.py`

```python
# app/auth/utils.py
from passlib.context import CryptContext
import jwt
from datetime import datetime, timedelta
from app.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)

def create_access_token(investigator_id: str, role: str, expires_minutes: int = 60) -> str:
    # TODO: payload with sub, role, exp — sign with settings.jwt_secret_key
    raise NotImplementedError

def decode_access_token(token: str) -> dict:
    # TODO: jwt.decode, handle ExpiredSignatureError / InvalidTokenError
    raise NotImplementedError
```

---

### Day 3 — Auth routes
**Create:**
- [ ] `veritas/backend/app/auth/routes.py`

```python
# app/auth/routes.py
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

@router.post("/login")
def login(username: str, password: str):
    # TODO: look up investigator, verify_password, create_access_token
    # TODO: write AuditLog row for "LOGIN"
    raise NotImplementedError

def get_current_investigator(token: str = Depends(oauth2_scheme)):
    # TODO: decode_access_token, fetch investigator, raise 401 if invalid
    raise NotImplementedError

def require_role(allowed_roles: list[str]):
    def checker(investigator=Depends(get_current_investigator)):
        # TODO: raise 403 if investigator.role not in allowed_roles
        return investigator
    return checker
```

> [!success] Checkpoint
> You can hit `/auth/login` in `/docs`, get a token back, and decode it manually to confirm the payload.

---

### Day 4 — Schemas
**Create:**
- [ ] `veritas/backend/app/schemas/__init__.py` (empty)
- [ ] `veritas/backend/app/schemas/evidence.py`

```python
# app/schemas/evidence.py
from pydantic import BaseModel
from typing import Optional

class CaseCreate(BaseModel):
    title: str

class CaseOut(BaseModel):
    id: str
    title: str
    status: str

class EvidenceUploadOut(BaseModel):
    evidence_id: str
    sha256: str
    file_type: str

class ReviewApprovalIn(BaseModel):
    case_id: str
    notes: Optional[str] = None
```

---

### Day 5 — Case routes + permission test script
**Create:**
- [ ] `veritas/backend/app/api/__init__.py` (empty)
- [ ] `veritas/backend/app/api/routes_case.py`
- [ ] `veritas/backend/tests/test_permissions.py`

```python
# app/api/routes_case.py
from fastapi import APIRouter, Depends
from app.auth.routes import get_current_investigator, require_role
from app.schemas.evidence import CaseCreate, CaseOut

router = APIRouter()

@router.post("/", response_model=CaseOut)
def create_case(payload: CaseCreate, investigator=Depends(require_role(["analyst","supervisor","admin"]))):
    # TODO: create Case row, write AuditLog "CASE_CREATED"
    raise NotImplementedError

@router.get("/{case_id}", response_model=CaseOut)
def get_case(case_id: str, investigator=Depends(get_current_investigator)):
    # TODO: fetch case, 404 if missing
    raise NotImplementedError
```

```python
# tests/test_permissions.py
import httpx

BASE_URL = "http://localhost:8000"

ROLE_TOKENS = {
    # TODO: populate with real tokens per role after logging in
}

ROUTE_MATRIX = [
    # (method, path, allowed_roles)
    ("POST", "/cases/", ["analyst", "supervisor", "admin"]),
    # TODO: add every route from routes_case.py, routes_evidence.py, routes_graph.py
]

def test_permission_matrix():
    for method, path, allowed in ROUTE_MATRIX:
        for role, token in ROLE_TOKENS.items():
            # TODO: httpx.request(method, BASE_URL+path, headers={"Authorization": f"Bearer {token}"})
            # TODO: assert 2xx if role in allowed else assert 403
            pass
```

> [!success] Checkpoint — Week 2
> Auth end to end works: login → token → role-gated route. Permission test script exists (logic can still be TODO, structure should be real).

---

## Week 3 — Pipeline Skeleton + Agents 1–3

### Day 1 — Pipeline state + orchestrator shell
**Create:**
- [ ] `veritas/backend/app/agents/__init__.py` (empty)
- [ ] `veritas/backend/app/agents/state.py`
- [ ] `veritas/backend/app/agents/orchestrator.py`

```python
# app/agents/state.py
from typing import TypedDict, Optional, List

class PipelineState(TypedDict, total=False):
    case_id: str
    evidence_path: str
    sha256: str
    file_type: str
    metadata: dict
    synthetic_verdict: Optional[str]      # "real" | "synthetic" | "abstain"
    synthetic_confidence: Optional[float]
    requires_human_review: bool
    correlations: List[dict]
    patterns: List[dict]
    timeline: List[dict]
    risk_score: Optional[float]
    report: Optional[str]
    status: str  # "processing" | "awaiting_review" | "complete" | "failed"
```

```python
# app/agents/orchestrator.py
from langgraph.graph import StateGraph, END
from app.agents.state import PipelineState

# TODO: import each agent function once written
# from app.agents.ingestion_agent import ingestion_node
# from app.agents.metadata_agent import metadata_node
# ...

def build_graph():
    graph = StateGraph(PipelineState)

    # TODO: graph.add_node("ingestion", ingestion_node) etc for all 9 agents
    # TODO: graph.add_edge(...) for the linear sequence
    # TODO: graph.add_conditional_edges("synthetic_detection", route_on_review,
    #         {"awaiting_review": "awaiting_review_node", "continue": "correlation"})

    graph.set_entry_point("ingestion")
    return graph.compile()

pipeline = None  # TODO: pipeline = build_graph() once nodes exist
```

---

### Day 2 — Ingestion agent
**Create:**
- [ ] `veritas/backend/app/agents/ingestion_agent.py`

```python
# app/agents/ingestion_agent.py
import hashlib
from app.agents.state import PipelineState

def ingestion_node(state: PipelineState) -> PipelineState:
    # TODO: read file at state["evidence_path"]
    # TODO: sha256 = hashlib.sha256(file_bytes).hexdigest()  -- do this FIRST, chain-of-custody anchor
    # TODO: detect file_type (mimetype)
    # TODO: on failure -> write AuditLog "INGESTION_FAILED", set state["status"]="failed"
    raise NotImplementedError
```

---

### Day 3 — Metadata agent
**Create:**
- [ ] `veritas/backend/app/agents/metadata_agent.py`

```python
# app/agents/metadata_agent.py
from app.agents.state import PipelineState

def metadata_node(state: PipelineState) -> PipelineState:
    file_type = state.get("file_type", "")
    if file_type.startswith("image"):
        # TODO: EXIF/GPS/timestamp extraction (PIL.ExifTags)
        pass
    elif file_type.startswith("video"):
        # TODO: Week 6 — pymediainfo/ffmpeg branch, stub for now
        pass
    else:
        # TODO: unsupported type handling
        pass
    raise NotImplementedError
```

---

### Day 4 — Synthetic detector (stage 1 shell)
**Create:**
- [ ] `veritas/backend/app/ml/__init__.py` (empty)
- [ ] `veritas/backend/app/ml/synthetic_detector.py`

```python
# app/ml/synthetic_detector.py
import timm
import torch
from app.config import settings

class SyntheticDetector:
    def __init__(self):
        self.model = timm.create_model("efficientnet_b4", pretrained=False, num_classes=2)
        # TODO: load state dict from settings.synthetic_detector_model_path
        self.model.eval()

    def _stage1_classify(self, image) -> tuple[str, float]:
        # TODO: preprocess image, run through self.model, softmax -> (verdict, confidence)
        raise NotImplementedError

    def _stage2_adversarial_check(self, image, stage1_confidence: float) -> bool:
        # TODO: Week 6 — transform-consistency check (JPEG recompress / blur / noise)
        raise NotImplementedError

    def predict(self, image_path: str) -> dict:
        # TODO: orchestrate stage1 -> stage2 -> return {"verdict":..., "confidence":..., "abstain": bool}
        raise NotImplementedError
```

---

### Day 5 — Synthetic detection agent
**Create:**
- [ ] `veritas/backend/app/agents/synthetic_detection_agent.py`

```python
# app/agents/synthetic_detection_agent.py
from app.agents.state import PipelineState
from app.ml.synthetic_detector import SyntheticDetector

detector = SyntheticDetector()

def synthetic_detection_node(state: PipelineState) -> PipelineState:
    # TODO: only run on image/video file types
    # TODO: result = detector.predict(state["evidence_path"])
    # TODO: state["synthetic_verdict"], state["synthetic_confidence"] = ...
    # TODO: if result["abstain"]: state["requires_human_review"] = True
    raise NotImplementedError
```

> [!success] Checkpoint — Week 3
> All 5 files exist and import without errors (even with `NotImplementedError` bodies). `orchestrator.py`'s graph structure is sketched even if not wired to real functions yet.

---

## Week 4 — Neo4j Client + Agents 4–7

### Day 1 — Neo4j client
**Create:**
- [ ] `veritas/backend/app/db/neo4j_client.py`

```python
# app/db/neo4j_client.py
from neo4j import GraphDatabase
from app.config import settings

class Neo4jClient:
    def __init__(self):
        self.driver = GraphDatabase.driver("bolt://neo4j:7687", auth=("neo4j", settings.neo4j_password))

    def upsert_media_file(self, case_id: str, sha256: str, metadata: dict):
        # TODO: MERGE (:MediaFile {sha256: $sha256}) SET properties, link to Case
        raise NotImplementedError

    def link_related(self, sha256_a: str, sha256_b: str, reason: str):
        # TODO: MERGE relationship between two MediaFile nodes
        raise NotImplementedError

    def query_subgraph(self, case_id: str) -> dict:
        # TODO: return nodes/edges for a case, shaped for Cytoscape.js
        raise NotImplementedError

neo4j_client = Neo4jClient()
```

---

### Day 2 — Correlation agent
**Create:**
- [ ] `veritas/backend/app/agents/correlation_agent.py`

```python
# app/agents/correlation_agent.py
from app.agents.state import PipelineState
from app.db.neo4j_client import neo4j_client

def correlation_node(state: PipelineState) -> PipelineState:
    # TODO: neo4j_client.upsert_media_file(...)
    # TODO: find other MediaFile nodes sharing device/location/time window, link_related(...)
    raise NotImplementedError
```

---

### Day 3 — Pattern analysis agent
**Create:**
- [ ] `veritas/backend/app/agents/pattern_analysis_agent.py`

```python
# app/agents/pattern_analysis_agent.py
from app.agents.state import PipelineState

def pattern_analysis_node(state: PipelineState) -> PipelineState:
    # TODO: query Neo4j for graph-level patterns (e.g. shared-device clusters)
    # TODO: state["patterns"] = [...]
    raise NotImplementedError
```

---

### Day 4 — Timeline agent
**Create:**
- [ ] `veritas/backend/app/agents/timeline_agent.py`

```python
# app/agents/timeline_agent.py
from app.agents.state import PipelineState

def timeline_node(state: PipelineState) -> PipelineState:
    # TODO: order state["metadata"] timestamps chronologically
    # TODO: flag anomalies (impossible ordering, missing timestamps)
    raise NotImplementedError
```

---

### Day 5 — Risk scoring agent
**Create:**
- [ ] `veritas/backend/app/agents/risk_scoring_agent.py`

```python
# app/agents/risk_scoring_agent.py
from app.agents.state import PipelineState

def risk_scoring_node(state: PipelineState) -> PipelineState:
    # TODO: weighted function of synthetic_confidence, patterns, timeline anomalies
    # TODO: low confidence -> requires_human_review = True instead of forcing a score
    raise NotImplementedError
```

> [!success] Checkpoint — Week 4
> `neo4j_client.py` and 4 agent files exist with real method/function signatures matching `PipelineState` fields.

---

## Week 5 — LLM Client + Agents 8–9 + Remaining API Routes

### Day 1 — LLM client
**Create:**
- [ ] `veritas/backend/app/ml/llm_client.py`

```python
# app/ml/llm_client.py
import requests
from app.config import settings

class OllamaClient:
    def __init__(self):
        self.host = settings.ollama_host

    def generate(self, prompt: str) -> str:
        # TODO: POST to {self.host}/api/generate with model="qwen2.5:7b"
        raise NotImplementedError

    def generate_with_trace(self, prompt: str) -> dict:
        # TODO: return {"answer": ..., "reasoning_trace": [...]} -- your explainability core
        raise NotImplementedError

llm_client = OllamaClient()
```

---

### Day 2–3 — Report generation agent
**Create:**
- [ ] `veritas/backend/app/agents/report_generation_agent.py`

```python
# app/agents/report_generation_agent.py
from app.agents.state import PipelineState
from app.ml.llm_client import llm_client

def report_generation_node(state: PipelineState) -> PipelineState:
    # TODO: build prompt from full pipeline state
    # TODO: result = llm_client.generate_with_trace(prompt)
    # TODO: prefix report with "DRAFT — PENDING REVIEW" if state["requires_human_review"]
    raise NotImplementedError
```

---

### Day 4 — Retrieval agent
**Create:**
- [ ] `veritas/backend/app/agents/retrieval_agent.py`

```python
# app/agents/retrieval_agent.py
from app.db.neo4j_client import neo4j_client
from app.ml.llm_client import llm_client

def answer_question(case_id: str, question: str) -> str:
    # TODO: pull relevant subgraph/context for case_id
    # TODO: prompt the LLM grounded ONLY in that context
    # TODO: if context doesn't cover the question, say so explicitly rather than guessing
    raise NotImplementedError
```

---

### Day 5 — Evidence + graph routes
**Create:**
- [ ] `veritas/backend/app/api/routes_evidence.py`
- [ ] `veritas/backend/app/api/routes_graph.py`

```python
# app/api/routes_evidence.py
from fastapi import APIRouter, Depends
from app.auth.routes import get_current_investigator, require_role
from app.tasks.celery_tasks import run_pipeline_task

router = APIRouter()

@router.post("/run")
def run_evidence(case_id: str, file_path: str, investigator=Depends(get_current_investigator)):
    # TODO: run_pipeline_task.delay(case_id, file_path), return task id
    raise NotImplementedError

@router.get("/status/{task_id}")
def get_status(task_id: str, investigator=Depends(get_current_investigator)):
    # TODO: check celery AsyncResult(task_id) state
    raise NotImplementedError

@router.post("/approve-review/{case_id}")
def approve_review(case_id: str, investigator=Depends(require_role(["supervisor","admin"]))):
    # TODO: finalize case, write AuditLog "REVIEW_APPROVED"
    raise NotImplementedError
```

```python
# app/api/routes_graph.py
from fastapi import APIRouter, Depends
from app.auth.routes import get_current_investigator
from app.db.neo4j_client import neo4j_client
from app.agents.retrieval_agent import answer_question

router = APIRouter()

@router.get("/subgraph/{case_id}")
def get_subgraph(case_id: str, investigator=Depends(get_current_investigator)):
    # TODO: return neo4j_client.query_subgraph(case_id)
    raise NotImplementedError

@router.post("/ask/{case_id}")
def ask(case_id: str, question: str, investigator=Depends(get_current_investigator)):
    # TODO: return answer_question(case_id, question)
    raise NotImplementedError
```

> [!success] Checkpoint — Week 5
> All 9 agent files and all 4 route files exist with matching signatures. `orchestrator.py` can now import every node function (bodies still TODO is fine).

---

## Week 6 — Fill In the Two Genuinely Open Items

*This is where you actually write real logic, not just skeletons — budget extra time.*

### Day 1–3 — `_stage2_adversarial_check()` in `synthetic_detector.py`
**Edit:**
- [ ] `veritas/backend/app/ml/synthetic_detector.py`

```python
# fleshing out _stage2_adversarial_check — structure to build against
def _stage2_adversarial_check(self, image, stage1_confidence: float) -> bool:
    transforms_to_try = [
        # TODO: jpeg_recompress(image, quality=70)
        # TODO: gaussian_blur(image, radius=2)
        # TODO: add_noise(image, sigma=0.05)
    ]
    confidence_deltas = []
    for transformed in transforms_to_try:
        # TODO: _, new_confidence = self._stage1_classify(transformed)
        # TODO: confidence_deltas.append(abs(stage1_confidence - new_confidence))
        pass
    # TODO: large average delta -> likely adversarially perturbed -> return True (flag/abstain)
    raise NotImplementedError
```

### Day 4–5 — Video metadata branch in `metadata_agent.py`
**Edit:**
- [ ] `veritas/backend/app/agents/metadata_agent.py`

```python
# fleshing out the video branch
from pymediainfo import MediaInfo

def _extract_video_metadata(path: str) -> dict:
    # TODO: MediaInfo.parse(path), pull codec, duration, creation timestamp
    raise NotImplementedError
```

> [!success] Checkpoint — Week 6
> Both methods have real (not stubbed) logic, tested against manually perturbed/sample files.

---

## Week 7 — Model Weights, Frontend, Backup Proof

### Day 1–3 — Training script
**Create:**
- [ ] `veritas/backend/scripts/train_synthetic_detector.py`

```python
# scripts/train_synthetic_detector.py
import timm, torch
from torch.utils.data import DataLoader

def build_model():
    return timm.create_model("efficientnet_b4", pretrained=True, num_classes=2)

def train(dataset_path: str, epochs: int = 10):
    # TODO: dataset loading (real vs AI-generated images, public research datasets only)
    # TODO: training loop, save checkpoint to SYNTHETIC_DETECTOR_MODEL_PATH
    raise NotImplementedError

if __name__ == "__main__":
    train(dataset_path="./data/training_set")
```

### Day 4 — Frontend graph view
**Create:**
- [ ] `veritas/frontend/index.html`
- [ ] `veritas/frontend/graph.js`

```html
<!-- frontend/index.html -->
<!DOCTYPE html>
<html>
<head><script src="https://cdnjs.cloudflare.com/ajax/libs/cytoscape/3.28.1/cytoscape.min.js"></script></head>
<body>
  <div id="cy" style="width:100%;height:100vh;"></div>
  <script src="graph.js"></script>
</body>
</html>
```

```javascript
// frontend/graph.js
// TODO: fetch(`/graph/subgraph/${caseId}`) with auth header
// TODO: cytoscape({ container: document.getElementById('cy'), elements: [...], style: [...] })
// TODO: style node color by type (person / evidence / case)
```

### Day 5 — Restore script
**Create:**
- [ ] `veritas/backend/scripts/restore_neo4j.sh`

```bash
#!/bin/bash
# backend/scripts/restore_neo4j.sh
set -e
DUMP_FILE=$1
# TODO: neo4j-admin load command targeting $DUMP_FILE
echo "TODO: implement restore, then verify against a known query"
```

> [!success] Checkpoint — Week 7
> Real checkpoint loads, real verdicts. Frontend renders a graph. You've deleted and restored Neo4j data successfully.

---

## Week 8 — Test Suite + Demo Prep

### Day 1–2 — Pipeline tests
**Create:**
- [ ] `veritas/backend/tests/conftest.py`
- [ ] `veritas/backend/tests/test_pipeline.py`

```python
# tests/conftest.py
import pytest
# TODO: fixtures for test DB session, test evidence files (clean/synthetic/ambiguous/corrupted)
```

```python
# tests/test_pipeline.py
def test_clean_case_completes():
    raise NotImplementedError

def test_synthetic_case_flags_review():
    raise NotImplementedError

def test_corrupted_file_fails_gracefully():
    raise NotImplementedError
```

### Day 3–5 — No new files
- [ ] Demo scenario selection + timing
- [ ] Adversarial Q&A written answers
- [ ] Full dry run with a test audience

> [!success] Checkpoint — Week 8
> Test suite runs (structure real, assertions filled in by you). Full dry run done.

---

## Reference: Day → File Map

| Week | Day | Files Created |
|---|---|---|
| 1 | 1 | `docker-compose.yml`, `.env.example`, `.gitignore`, `README.md` |
| 1 | 2 | `backend/Dockerfile`, `backend/requirements.txt` |
| 1 | 3 | `app/__init__.py`, `app/config.py`, `app/main.py` |
| 1 | 4 | `app/celery_app.py`, `app/tasks/celery_tasks.py` |
| 1 | 5 | `app/db/session.py`, `scripts/backup_neo4j.sh` |
| 2 | 1 | `app/db/postgres_models.py` |
| 2 | 2 | `app/auth/utils.py` |
| 2 | 3 | `app/auth/routes.py` |
| 2 | 4 | `app/schemas/evidence.py` |
| 2 | 5 | `app/api/routes_case.py`, `tests/test_permissions.py` |
| 3 | 1 | `app/agents/state.py`, `app/agents/orchestrator.py` |
| 3 | 2 | `app/agents/ingestion_agent.py` |
| 3 | 3 | `app/agents/metadata_agent.py` |
| 3 | 4 | `app/ml/synthetic_detector.py` |
| 3 | 5 | `app/agents/synthetic_detection_agent.py` |
| 4 | 1 | `app/db/neo4j_client.py` |
| 4 | 2 | `app/agents/correlation_agent.py` |
| 4 | 3 | `app/agents/pattern_analysis_agent.py` |
| 4 | 4 | `app/agents/timeline_agent.py` |
| 4 | 5 | `app/agents/risk_scoring_agent.py` |
| 5 | 1 | `app/ml/llm_client.py` |
| 5 | 2–3 | `app/agents/report_generation_agent.py` |
| 5 | 4 | `app/agents/retrieval_agent.py` |
| 5 | 5 | `app/api/routes_evidence.py`, `app/api/routes_graph.py` |
| 6 | 1–3 | Edit `synthetic_detector.py` (`_stage2_adversarial_check`) |
| 6 | 4–5 | Edit `metadata_agent.py` (video branch) |
| 7 | 1–3 | `scripts/train_synthetic_detector.py` |
| 7 | 4 | `frontend/index.html`, `frontend/graph.js` |
| 7 | 5 | `scripts/restore_neo4j.sh` |
| 8 | 1–2 | `tests/conftest.py`, `tests/test_pipeline.py` |
