# Day 3 — App Entrypoint + Config

**Date:** 2026-08-03
**Week:** Week 1 — Project Skeleton & Infra
**Roadmap reference:** Week 1, Day 3

---

## What we did

### 1. Created `backend/app/` — the first real Python code

Three files, all under the new `backend/app/` package:

| File | Purpose |
|---|---|
| `backend/app/__init__.py` | Marks `app` as a Python package so `app.main:app` resolves |
| `backend/app/config.py` | `Settings(BaseSettings)` — every env var the app uses, typed |
| `backend/app/main.py` | FastAPI instance + `/health` endpoint |

### 2. Verified the installed pydantic version before writing config

Ran `pip show` inside the Day 2 image — **pydantic-settings 2.14.2 / pydantic 2.13.4**.
The roadmap skeleton's `class Config: env_file = ...` is pydantic **v1** syntax;
with v2 we write plain typed fields. Also: compose injects all env vars (via
`env_file: .env` + the `environment:` block), so no `env_file` directive is
needed in Settings at all — the container environment is the source of truth.

### 3. Config design decisions

- **11 typed fields**, matching the real env vars: `JWT_*`, `DATABASE_URL`,
  `NEO4J_URI`, `NEO4J_PASSWORD`, `REDIS_URL`, `OLLAMA_HOST`,
  `SYNTHETIC_DETECTOR_MODEL_PATH`, `LLM_MODEL_NAME`, `DEPLOYMENT_NAME`.
- **No defaults anywhere** — a missing variable must fail the boot. Rationale:
  `deployment_name` gets stamped into audit logs/reports; a silent default
  could mislabel evidence in a forensic system. Fail loudly.
- **`settings = Settings()` at module level** — crashes at import time,
  not at first request. Fail-fast is the contract.
- Field names match env vars case-insensitively (`jwt_secret_key` ←
  `JWT_SECRET_KEY`).

### 4. Health endpoint double-duties as a config test

```python
@app.get("/health")
def health() -> dict:
    return {"status": "ok", "deployment": settings.deployment_name}
```

The response includes `settings.deployment_name` **on purpose** — if config
loading breaks, the health check fails at boot instead of lying.

### 5. Checkpoint — FIRST REAL BOOT of the stack

```bash
docker compose up -d api
```

Result: ✅ postgres/redis/neo4j healthy, api running:

```text
GET /health -> {"status":"ok","deployment":"cybercell_ernakulam"}
GET /docs    -> HTTP 200
```

This is the first time `docker compose up` has ever completed end-to-end.

---

## Two real bugs caught by the first boot (teaching gold)

### Bug 1 — `.gitkeep` blocked postgres init

`initdb: error: directory "/var/lib/postgresql/data" exists but is not empty`
— the culprit was a `.gitkeep` file in `data/postgres/` (from the initial
scaffold). The postgres image refuses to initialize into a non-empty
directory unless it contains a real `PG_VERSION`.

Root cause: `data/` is fully gitignored, so `.gitkeep` files were **never
tracked by git** — they served zero purpose and one of them broke postgres.

**Fix:** deleted all `.gitkeep` files under `data/` (via a root container,
since postgres had chowned `data/postgres` to its internal user, uid 70).

**Lesson:** if a directory is gitignored wholesale, don't plant `.gitkeep`
files in it. They can't be committed and they corrupt strict bootstrappers
like postgres.

### Bug 2 — Neo4j rejects the dev password

`InvalidPasswordException: A password must be at least 8 characters` —
the Day 1 dev value `dev123` was 6 characters. Neo4j 5.x enforces a minimum
of 8.

**Fix:** `NEO4J_PASSWORD=dev12345` in `.env`.

**Decision:** did **not** set
`NEO4J_dbms_security_auth__minimum__password__length=4` to override — even
in dev, a forensic tool shouldn't weaken its own security boundary.

**Lesson:** Day 1 validated compose with `docker compose config` (syntax
only). Real boot-time validation only happens when you actually run it.

---

## State of the project at end of Day 3

```
backend/
├── Dockerfile
├── requirements.txt
└── app/                    ← NEW — first application code
    ├── __init__.py
    ├── config.py           ← 11 typed settings, fail-fast, no defaults
    └── main.py             ← FastAPI + /health (returns deployment name)
```

Running stack: postgres, redis, neo4j, api — all healthy. `/docs` and
`/health` live on `http://localhost:8000`.

## Next up — Day 4

Week 1, Day 4 tasks from roadmap:
- `backend/app/celery_app.py` — Celery instance wired to Redis
- `backend/app/tasks/__init__.py` (empty)
- `backend/app/tasks/celery_tasks.py` — `run_pipeline_task` wrapper
- Checkpoint: Flower dashboard loads at `localhost:5555` with worker online
