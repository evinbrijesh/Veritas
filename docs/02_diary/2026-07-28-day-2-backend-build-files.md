# Day 2 — Backend Build Files

**Date:** 2026-07-28
**Week:** Week 1 — Project Skeleton & Infra
**Roadmap reference:** Week 1, Day 2

---

## What we did

### 1. Created `backend/` directory

```bash
mkdir backend
```

New folder to hold the Dockerfile, requirements.txt, and all application code going forward.

### 2. Created `backend/requirements.txt`

Listed all Python dependencies, grouped by function:

| Group | Packages |
|---|---|
| Web framework | fastapi, uvicorn, python-multipart, pydantic-settings |
| Task queue | celery, redis |
| Orchestration | langgraph, langchain-core |
| Databases | neo4j, sqlalchemy, psycopg2-binary |
| Auth | passlib, pyjwt |
| ML / synthetic detection | torch, torchvision, timm, pillow |
| Metadata extraction | pymediainfo |
| LLM client | requests |
| Testing | pytest, httpx |

### 3. Created `backend/Dockerfile`

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Key decisions:
- **`python:3.11-slim`** — minimal base image, small footprint
- **COPY requirements.txt before COPY .** — leverages Docker layer caching. Dependencies don't reinstall unless requirements.txt changes.
- **CMD as uvicorn** — default command, overridden per-service in docker-compose.yml

### 4. Built and validated

```bash
docker compose build api
```

⚠️ Note: docker-compose.yml calls the service `api`, not `backend`. The `build: ./backend` directive in the compose file still points to the `backend/` folder, but the **service name** is `api`.

Result: ✅ Image `veritas-api` built successfully (5.74GB).

Checkpoint passed — all package names are real, no dependency conflicts.

### 5. Committed and pushed

```bash
git add backend/Dockerfile backend/requirements.txt
git commit -m "backend: Docker + requirements, verified with docker compose build"
git push
```

---

## Key decisions made today

| Decision | Rationale |
|---|---|
| `python:3.11-slim` over full image | Saves ~780MB per image, no docs/man pages needed |
| COPY requirements.txt before COPY . | Docker layer caching — faster rebuilds during dev |
| Service named `api` not `backend` | docker-compose.yml naming convention |
| Inline comments in requirements.txt | Self-documenting for anyone reading the file later |
| No pinned versions in requirements.txt | Hackathon pace — faster to iterate. Pin versions before production. |

## State of the project at end of Day 2

```
veritas/
├── backend/
│   ├── Dockerfile        ← NEW — Python 3.11-slim, pip install, uvicorn default
│   └── requirements.txt  ← NEW — 20 packages, grouped by function
├── docker-compose.yml
├── .env.example
├── .gitignore
├── README.md
├── data/                 ← bind-mount ready
└── docs/
    ├── 01_roadmap/
    ├── 02_diary/
    └── data_layout.md
```

## Next up — Day 3

Week 1, Day 3 tasks from roadmap:
- `backend/app/__init__.py` — empty, makes `app` a Python package
- `backend/app/config.py` — reads .env into typed Settings object via pydantic-settings
- `backend/app/main.py` — FastAPI entrypoint with `/health` endpoint
- Checkpoint: `localhost:8000/docs` loads and shows `/health`
