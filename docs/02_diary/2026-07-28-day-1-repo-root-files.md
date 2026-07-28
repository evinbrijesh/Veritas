# Day 1 — Repo Root Files & Infra Validation

**Date:** 2026-07-28
**Week:** Week 1 — Project Skeleton & Infra
**Roadmap reference:** Week 1, Day 1

---

## What we did

### 1. Audited existing Day 1 deliverables

All four Day 1 files from the roadmap were already in place:

| File | Status | Notes |
|---|---|---|
| `docker-compose.yml` | ✅ Existed | Actually more detailed than the roadmap — healthchecks, container names, GPU deploy block, dedicated network |
| `.env.example` | ✅ Existed | Had extra fields beyond roadmap (JWT_ALGORITHM, JWT_EXPIRE_MINUTES, LLM_MODEL_NAME, DEPLOYMENT_NAME) |
| `.gitignore` | ✅ Existed | Comprehensive — covered env, data, Python, ML weights, Celery, testing, IDE, OS |
| `README.md` | ✅ Existed | Full architecture diagram, quickstart, scaling, security notes |
| `data/` folder | ✅ Existed | 5 subdirs: postgres/, redis/, neo4j/, evidence_storage/, backups/ |

### 2. `.gitignore` — added `*.dump` rule

Discovered a gap: Neo4j backup dump files (`.dump`) weren't excluded. If someone runs the backup script and accidentally stages files, dumps could leak into git. Added:

```
# Neo4j backup dumps
*.dump
```

Also confirmed the three critical exclusion rules are present:
- `.env` — prevents secret leakage
- `data/` — prevents committing evidence/database contents
- `backend/app/ml/weights/` — model weights too large for git

### 3. Discovered duplicate `env.example` files

Found **two** env.example files at different locations:

| File | Purpose |
|---|---|
| `veritas/.env.example` (root) | Real one — used by Docker Compose and app code. Concise, only truly configurable values. |
| `veritas/docs/env.example` | Leftover/earlier draft — verbose, listed values already hardcoded in compose file (e.g., `POSTGRES_HOST=postgres`, `REDIS_PORT=6379`). Would cause confusion if someone copied it. |

**Decision:** Delete `docs/env.example`. One source of truth. The root `.env.example` is the single template everyone copies from.

### 4. Enhanced `.env.example` with rich comments

Added detailed explanations for every variable — what it does, how to generate it, when it's used:

```
# --- Database credentials ---
# Used by Docker Compose to init Postgres and Neo4j on first run.
# POSTGRES_USER and POSTGRES_DB are hardcoded as 'veritas' in docker-compose.yml.
NEO4J_PASSWORD=<fill_in>
POSTGRES_PASSWORD=<fill_in>

# --- Auth / JWT ---
# JWT_SECRET_KEY: run `openssl rand -hex 32` to generate one.
JWT_SECRET_KEY=<generate_me>

# --- ML model paths ---
# SYNTHETIC_DETECTOR_MODEL_PATH: inside-container path.
# Weights are NOT shipped in repo — add them to backend/app/ml/weights/.
# LLM_MODEL_NAME: pull once with: docker exec -it veritas-ollama ollama pull qwen2.5:7b
...
```

### 5. Created `.env` and validated with `docker compose config`

**Step 1:** Copied `.env.example` → `.env`, filled in dev values:
- `NEO4J_PASSWORD=dev123`
- `POSTGRES_PASSWORD=dev123`
- `JWT_SECRET_KEY=0c9b0c9bde5848243c6ca18efb8faf04cfc805007dc5bb729c72839306860873` (generated via `openssl rand -hex 32`)

**Step 2:** Ran `docker compose config` to validate the compose file resolves correctly.

Result: ✅ Full 7-service config printed cleanly. All environment variables resolved, all bind-mounts pointed to absolute paths.

One warning surfaced: `the attribute 'version' is obsolete, it will be ignored, please remove it`. The compose file had `version: "3.9"` at the top — this is deprecated in Docker Compose v2.

### 6. Removed `version: "3.9"` from `docker-compose.yml`

Modern Docker Compose (v2+) ignores this field. Removed it to silence the warning and align with current syntax.

### 7. Normalized `docker-compose` → `docker compose` across all files

Docker Compose v1 used the hyphenated command (`docker-compose`). Docker Compose v2 uses a space (`docker compose`). Updated all **command references** (not filenames) across:

| File | Changes |
|---|---|
| `README.md` | Quickstart and scaling sections |
| `docker-compose.yml` | 3 inline comments |
| `.env.example` | 2 inline comments |

Filenames like `docker-compose.yml` and `docker-compose.override.yml` were left as-is — they are the actual file names.

### 8. Created this diary entry

---

## Key decisions made today

| Decision | Rationale |
|---|---|
| Delete `docs/env.example` | Duplicate source of truth causes confusion. Root `.env.example` is canonical. |
| Remove `version: "3.9"` from compose file | Deprecated in Docker Compose v2, generates warning, adds no value. |
| `docker compose` (space) everywhere | We're on Docker Compose v2. Hyphenated form is v1 legacy. |
| Comments in `.env.example`, not a separate doc | Keeps documentation next to the values it describes. One less file to maintain. |

## State of the project at end of Day 1

```
veritas/
├── .editorconfig
├── .gitignore          ← updated (+*.dump rule)
├── .env                ← created from .env.example (gitignored)
├── .env.example        ← enriched with comments
├── README.md           ← updated (docker compose syntax)
├── docker-compose.yml  ← cleaned (removed version, docker compose syntax)
├── data/               ← 5 subdirs, bind-mount ready
│   ├── backups/
│   ├── evidence_storage/
│   ├── neo4j/
│   ├── postgres/
│   └── redis/
├── backend/            ← created Day 2+
└── docs/
    ├── 01_roadmap/
    ├── 02_diary/       ← this file lives here
    ├── DATA_MODEL.md
    ├── PRD.md
    └── STACK.md
```

## Next up — Day 2

Week 1, Day 2 tasks from roadmap:
- `backend/Dockerfile` — base Python 3.11-slim image, install dependencies
- `backend/requirements.txt` — all Python packages (FastAPI, LangGraph, Celery, Neo4j driver, PyTorch, etc.)
- Checkpoint: `docker compose build backend` completes with no dependency errors
