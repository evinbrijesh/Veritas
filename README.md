# VERITAS
**V**erified **E**vidence **R**easoning & **I**ntelligence **T**riage **A**gentic **S**ystem

A multi-agent AI pipeline for digital forensic evidence analysis in child
protection investigations, built for HAC'KP (Kerala Police Cyberdome) —
ACPIA problem statement.

## Architecture at a glance

```
Investigator (browser)
        │
        ▼
   FastAPI (auth, case mgmt, evidence endpoints)
        │
        ├──► Postgres        (investigators, roles, audit log, cases)
        │
        ├──► Redis  ◄──►  Celery workers  (9-agent pipeline, parallelized)
        │                        │
        │                        ▼
        │                 LangGraph orchestrator
        │           ┌─────────────────────────────┐
        │           │ 1. Ingestion                │
        │           │ 2. Metadata extraction       │
        │           │ 3. Synthetic detection (CV)  │──► EfficientNet-B4
        │           │ 4. Correlation                │──► Neo4j
        │           │ 5. Pattern analysis            │
        │           │ 6. Timeline construction        │
        │           │ 7. Risk scoring                  │
        │           │ 8. Report generation              │──► Ollama (host, qwen3.5)
        │           │ 9. Retrieval (on-demand Q&A)        │
        │           └─────────────────────────────┘
        │
        └──► Neo4j          (evidence knowledge graph)
                    │
                    ▼
             Cytoscape.js (frontend graph rendering — not scaffolded here)
```

## Quick start (single-machine / department deployment)

```bash
cp .env.example .env
# edit .env: set NEO4J_PASSWORD, POSTGRES_PASSWORD, JWT_SECRET_KEY, LLM_MODEL_NAME

docker compose up -d

# LLM: this deployment uses a HOST ollama (not a container) — see
# "LLM runtime" below. Ensure the model named in LLM_MODEL_NAME is
# already pulled on the host:  ollama pull <LLM_MODEL_NAME>

# API docs available at:
# http://localhost:8000/docs

# Neo4j browser (inspect the knowledge graph directly):
# http://localhost:7474

# Celery task monitor:
# http://localhost:5555
```

All state — Neo4j graph, Postgres tables, Redis queue, raw evidence
files — persists under `./data/` via bind-mounted Docker volumes.
`docker compose down` (without `-v`) is always safe.

## LLM runtime

VERITAS talks to a **host-installed Ollama** at `host.docker.internal:11434`
(see `OLLAMA_HOST` in docker-compose.yml), not an in-compose container.
This lets the deployment reuse models already present on the machine —
no model downloads into Docker. The model named by `LLM_MODEL_NAME` in
`.env` must exist on the host (`ollama list`).

## Scaling

Evidence-heavy days (e.g. a large raid) need more parallel processing,
not a bigger API server:

```bash
docker compose up -d --scale worker=6
```

## Backups

Evidence data needs to survive more than just container restarts —
run `backend/scripts/backup_neo4j.sh` on a nightly cron for a
recoverable, timestamped dump under `./data/backups/`.

## Security notes for real deployment

- This scaffold's CORS, JWT secret, and DB passwords are dev defaults —
  replace all of them before anything resembling real evidence touches it.
- Intended to run fully air-gapped: no component in `docker-compose.yml`
  calls out to the public internet at runtime. The LLM is a host-installed
  Ollama (see "LLM runtime" above) — model downloads happen on the host,
  once, during setup.
- Every sensitive action (login, pipeline run, review approval) writes
  an `AuditLog` row in Postgres — don't delete from that table.
- The synthetic-detection model weights (`SYNTHETIC_DETECTOR_MODEL_PATH`)
  are **not included** — this scaffold ships an untrained model
  architecture only. Fine-tuned weights must be added before real use.

## Project layout

```
veritas/
├── docker-compose.yml       # all services + volume mounts
├── .env.example
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── scripts/backup_neo4j.sh
│   └── app/
│       ├── main.py           # FastAPI entrypoint
│       ├── config.py         # env-driven settings
│       ├── celery_app.py     # Celery instance
│       ├── agents/           # all 9 pipeline agents + LangGraph orchestrator
│       ├── tasks/            # Celery task wrappers around the pipeline
│       ├── db/                # Neo4j client + Postgres models/session
│       ├── ml/                 # EfficientNet-B4 detector + Ollama LLM client
│       ├── api/                 # evidence, case, graph REST routes
│       ├── auth/                 # JWT login, role-based access
│       └── schemas/               # Pydantic request/response models
└── data/                             # persisted volumes (gitignored)
```
