# VERITAS — Stack Decision

Locked in before further code generation. Changing any of these later means throwing away generated files, so this is the reference point for every agent/prompt going forward.

## Languages
- **Python 3.11+** — backend, agent pipeline, ML inference
- **JavaScript** — frontend graph visualization only (Cytoscape.js)

## Orchestration
- **LangGraph** — the nine-agent pipeline (ingestion → metadata → synthetic detection → correlation → pattern analysis → timeline → risk scoring → report generation → retrieval), wired into a single orchestrator with a conditional human-in-the-loop review gate

## API / async processing
- **FastAPI** — REST routes for cases, evidence, graph queries, and NL retrieval
- **Celery + Redis** — async task execution for long-running pipeline stages
- **Flower** — Celery task monitoring

## LLM
- **Ollama**, running **Qwen2.5 7B** locally — no external API calls for evidence reasoning. Client wraps reasoning-trace capture for explainability.

## Image classification
- **EfficientNet-B4** — two-stage synthetic/manipulated image detector

## Databases
- **Neo4j** — case/evidence relationship graph (local-only by design, no cloud Aura)
- **Postgres** — auth (users, roles), case metadata, immutable audit log

## Auth
- **JWT + bcrypt**, Postgres-backed
- Roles: `analyst`, `supervisor`, `auditor`, `admin`
- Immutable audit log table for chain-of-custody (append-only, no update/delete path)

## Frontend
- **Cytoscape.js** — graph rendering for case/evidence relationships

## Containerization
- **Docker Compose** — six services: Neo4j, Postgres, Redis, Ollama, FastAPI, Celery/Flower
- **Bind-mount volumes** (not named volumes) for all persistent data — required so data survives folder deletion/container teardown
- Kubernetes is a *future* scaling path, not a starting point — do not introduce k8s manifests into MVP scope

## Explicit non-choices (and why)
| Considered | Rejected because |
|---|---|
| Cloud LLM API (OpenAI/Anthropic/etc.) | Violates air-gapped/on-prem constraint for evidence reasoning |
| Managed Neo4j Aura | Same — evidence data must stay local |
| Kubernetes for MVP | Overkill for single-department deployment target; adds ops burden hackathon/MVP doesn't need |
| Named Docker volumes | Bind mounts make backup/restore and manual inspection simpler for forensic auditability |

## Known gaps to track
- Auth layer is functionally wired (JWT/bcrypt/RBAC/audit log) but **not yet hardened** — flagged as the top priority before this stack decision is considered "done" for production use.
