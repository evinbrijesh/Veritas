# Day 4 — Celery Wiring

**Date:** 2026-08-03
**Week:** Week 1 — Project Skeleton & Infra
**Roadmap reference:** Week 1, Day 4

---

## What we did

### 1. Created `backend/app/celery_app.py`

The Celery application object — shared by the API (producer) and workers
(consumer). Loaded as `app.celery_app` by the compose `worker` and `flower`
commands.

Key config decisions:

| Setting | Value | Why |
|---|---|---|
| `broker` | `settings.redis_url` | Single source of truth (Day 3). Not the roadmap's hardcoded `redis://redis:6379/0`. |
| `backend` | `settings.redis_url` | Roadmap sketched DB 1 for results; we share DB 0. Fine at this scale — splitting later is a one-line change. |
| `include` | `["app.tasks.celery_tasks"]` | **The footgun.** `celery -A app.celery_app` only imports `app.celery_app`; without this, the task module is never imported and no tasks register. |
| `broker_connection_retry_on_startup` | `True` | Don't crash at boot if Redis is still warming up (compose has no healthcheck gate on worker → redis). Explicit even though modern Celery defaults to True — protects against downgrades. |

Verified: Celery 5.6.3 in the image.

### 2. Created `backend/app/tasks/`

- `__init__.py` — package marker
- `celery_tasks.py` — `run_pipeline_task(case_id, evidence_path)`, `bind=True`,
  stub raising `NotImplementedError` until Week 3 (nothing calls it until
  Week 5 routes exist).

### 3. Worker checkpoint — booted WITHOUT a rebuild

`docker compose up -d worker` — the image already had celery, and the
`./backend/app` bind-mount made the new files visible immediately.

Worker log confirmed the whole point of Day 4:

```text
[tasks]
  . app.tasks.celery_tasks.run_pipeline_task
Connected to redis://redis:6379/0
celery@cc94ab46867d ready.
```

### 4. Flower — caught a real config bug, then fixed it

**Found:** `flower` was **never added to requirements.txt** (Day 2 gap) —
the compose service existed but the dependency didn't. Added it, rebuilt
the image (~2.5 min; changing requirements.txt invalidates the pip layer,
so everything reinstalls — the flip side of the Day 2 caching decision).

**Then Flower crashed at boot** with:

```text
pydantic_core.ValidationError: 3 validation errors for Settings
database_url  Field required
neo4j_uri     Field required
ollama_host   Field required
```

**Root cause:** Flower's command `celery -A app.celery_app flower` imports
`app.celery_app` → `app.config` → `settings = Settings()`, which requires
ALL 11 fields. But Flower's compose `environment:` block only set
`REDIS_URL` — the other three URLs were defined only on `api` and `worker`.

**This is Day 3's fail-fast design paying off**: without it, Flower would
have booted into a silently half-broken dashboard.

**Fix:** added `NEO4J_URI`, `DATABASE_URL`, `OLLAMA_HOST` to Flower's
environment block (same values as the other services). Decision: keep the
shared config import and make the dependency honest, rather than passing
`--broker` to Flower standalone (which would hardcode the broker URL and
create a second source of truth).

### 5. Final checkpoint — PASSED

```text
GET / -> HTTP 200   (Flower dashboard at localhost:5555)
```

Stack now running: postgres/redis/neo4j (healthy), api, worker, flower.

---

## State of the project at end of Day 4

```
backend/
├── Dockerfile
├── requirements.txt     ← +flower
└── app/
    ├── __init__.py
    ├── config.py
    ├── main.py
    ├── celery_app.py    ← NEW — broker/backend from settings.redis_url
    └── tasks/           ← NEW
        ├── __init__.py
        └── celery_tasks.py   ← run_pipeline_task stub (Week 3)
```

## Next up — Day 5

Week 1, Day 5 tasks from roadmap:
- `backend/app/db/__init__.py` (empty)
- `backend/app/db/session.py` — SQLAlchemy engine + `get_db` dependency
- `backend/scripts/backup_neo4j.sh` — real dump logic (not a TODO stub)
- Checkpoint: full `docker compose up -d` boots clean; manual backup script
  produces a file
