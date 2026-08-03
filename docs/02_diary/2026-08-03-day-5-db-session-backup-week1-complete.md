# Day 5 — DB Session + Backup Script (Week 1 Complete)

**Date:** 2026-08-03
**Week:** Week 1 — Project Skeleton & Infra
**Roadmap reference:** Week 1, Day 5

---

## What we did

### 1. Created `backend/app/db/` — Postgres access layer

- `__init__.py` — package marker
- `session.py` — SQLAlchemy engine + `SessionLocal` + `get_db` dependency

Design decisions:

| Decision | Why |
|---|---|
| `engine = create_engine(settings.database_url, pool_pre_ping=True)` | URL comes whole from config (Day 3 payoff — no string composition). `pool_pre_ping` verifies stale connections before use; Postgres silently closes idle ones and a long-running API would otherwise throw cryptic errors. |
| Lazy engine | Importing `session.py` doesn't touch Postgres — the API boots even if the DB is down. First query opens the pool. |
| `get_db()` yields one session per request, `finally: db.close()` | The canonical FastAPI pattern — leak-proof per-request sessions. |
| `autoflush=False` | Explicit control over when writes hit the DB — matters later for intentional audit-log writes. |

### 2. Created `backend/scripts/backup_neo4j.sh` — real dump logic

CLAUDE.md: the nightly backup is **mandatory, not optional tooling** — so this
got real logic, not a TODO stub. Three live iterations to get it right:

**Iteration 1 — failed:** `--to-path` requires the target directory to
already exist. Fixed with `mkdir -p`.

**Iteration 2 — failed:** `The database is in use. Stop database 'neo4j' and
try again.` — **Neo4j community has no online backup.** `database backup` is
Enterprise-only; community's `database dump` needs a stopped database.

**Iteration 3 — works.** Final pattern:

```bash
docker stop --time=90 veritas-neo4j          # graceful shutdown
trap restart_neo4j EXIT                       # graph ALWAYS comes back
docker run --rm -v .../data/neo4j/data:/data \
  -v .../data/backups:/backups neo4j:5-community \
  sh -c "neo4j-admin database dump neo4j --to-path=/backups && mv ..."
```

Verified live: `Dump completed successfully` — 36 files, 257.8 MiB processed,
timestamped `.dump` in `./data/backups/`, neo4j restarted by the trap.

**Tradeoff recorded:** ~1 minute of graph downtime per nightly backup
(community edition limitation). Acceptable for a 2am maintenance window;
Enterprise's online backup would remove it.

### 3. Architecture decision — host Ollama instead of a container

The compose file had an `ollama` service, but the host already runs a
systemd `ollama serve` (PID 985) with models including **qwen3.5** — and
the user explicitly wanted to reuse existing models, not download new ones.

The container couldn't bind port 11434 (host ollama owns it), and stopping
the host service would need sudo. Decision: **remove the ollama container
entirely; point the app at the host ollama.**

Changes:
- Removed `ollama` service from docker-compose.yml (and its GPU deploy block)
- `OLLAMA_HOST: http://host.docker.internal:11434` on api/worker/flower
- `extra_hosts: ["host.docker.internal:host-gateway"]` on all three (Linux
  needs the host-gateway mapping; Docker Desktop does this automatically)
- `.env`: `LLM_MODEL_NAME=qwen3.5` (was qwen2.5:7b)
- README updated: quickstart, new "LLM runtime" section, security notes

Verified live: api container reaches `host.docker.internal:11434` and sees
qwen3.5 in the model list.

**Tradeoff recorded:** deviates from "everything in compose" — but the
air-gapped story holds (host ollama is local), and it reuses existing
models with zero downloads. A fresh deployment on a machine without host
ollama would re-add the container service.

### 4. Week 1 final checkpoint — PASSED

```text
docker compose up -d        # 6 services, all clean
GET /health                 # {"status":"ok","deployment":"cybercell_ernakulam"}
backup_neo4j.sh             # produced neo4j_20260803_234515.dump
api -> host ollama          # qwen3.5 present
```

---

## State of the project at end of Week 1

```
backend/
├── Dockerfile
├── requirements.txt
├── scripts/
│   └── backup_neo4j.sh     ← NEW — real dump, trap-guaranteed restart
└── app/
    ├── __init__.py
    ├── config.py           ← 11 typed settings, fail-fast
    ├── main.py             ← FastAPI + /health
    ├── celery_app.py       ← Celery, broker/backend from settings
    ├── db/
    │   ├── __init__.py     ← NEW
    │   └── session.py      ← NEW — engine + get_db
    └── tasks/
        ├── __init__.py
        └── celery_tasks.py ← run_pipeline_task stub
```

Running stack (6 services): postgres, redis, neo4j (healthy), api, worker,
flower. LLM served by host ollama (qwen3.5).

## Next up — Week 2: Auth & Data Models

Week 2, Day 1: `backend/app/db/postgres_models.py` — Investigator, Case,
AuditLog tables. The audit log is append-only by design (CLAUDE.md) —
enforced at the DB layer, not just the app layer.
