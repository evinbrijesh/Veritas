# VERITAS — Data Model & API Shape

Rough schema and endpoint list, kept here so every generated file agrees on the same shapes. Update this doc first when a shape needs to change — don't let it drift silently across files.

## Postgres (auth, cases metadata, audit log)

### `users`
| field | type | notes |
|---|---|---|
| id | uuid, pk | |
| email | text, unique | |
| password_hash | text | bcrypt |
| role | enum | analyst \| supervisor \| auditor \| admin |
| created_at | timestamptz | |

### `cases`
| field | type | notes |
|---|---|---|
| id | uuid, pk | |
| title | text | |
| status | enum | open \| under_review \| closed |
| created_by | uuid, fk → users.id | |
| created_at | timestamptz | |
| updated_at | timestamptz | |

### `evidence`
| field | type | notes |
|---|---|---|
| id | uuid, pk | |
| case_id | uuid, fk → cases.id | |
| type | enum | image \| document \| metadata_bundle \| other |
| storage_path | text | bind-mounted path, not cloud URL |
| ingested_by | uuid, fk → users.id | |
| ingested_at | timestamptz | |

### `audit_log` (append-only, no update/delete)
| field | type | notes |
|---|---|---|
| id | uuid, pk | |
| user_id | uuid, fk → users.id | |
| action | text | e.g. `evidence.viewed`, `evidence.flagged`, `case.status_changed` |
| target_type | text | e.g. `evidence`, `case` |
| target_id | uuid | |
| detail | jsonb | free-form, action-specific |
| created_at | timestamptz | |

## Neo4j (case graph)

### Node labels
- `:Case {id, title}`
- `:Evidence {id, type, storage_path}`
- `:Entity {id, name, kind}` — people/accounts/devices surfaced by correlation agent
- `:Pattern {id, description, confidence}` — output of pattern analysis agent
- `:RiskAssessment {id, score, rationale, confidence, abstained}`

### Relationship types
- `(:Case)-[:CONTAINS]->(:Evidence)`
- `(:Evidence)-[:REFERENCES]->(:Entity)`
- `(:Entity)-[:LINKED_TO {weight, basis}]->(:Entity)` — output of correlation agent
- `(:Evidence)-[:MATCHES_PATTERN]->(:Pattern)`
- `(:Case)-[:HAS_RISK]->(:RiskAssessment)`
- `(:Evidence)-[:PRECEDES {timestamp}]->(:Evidence)` — timeline agent output

## Agent pipeline state shape (LangGraph)

Every node reads/writes a shared typed state object. Rough shape:

```python
class PipelineState(TypedDict):
    case_id: str
    evidence_ids: list[str]
    metadata: dict            # populated by metadata agent
    synthetic_flags: dict      # evidence_id -> {is_synthetic, confidence, abstained}
    correlations: list[dict]   # entity links found
    patterns: list[dict]
    timeline: list[dict]
    risk_score: dict           # {score, rationale, confidence, abstained}
    reasoning_trace: list[dict]  # appended to by every agent, never overwritten
    review_required: bool       # set True to trigger human-in-the-loop gate
    review_decision: str | None # supervisor's decision once gate is passed
```

## FastAPI routes (rough)

### Cases
- `POST /cases` — create case
- `GET /cases/{case_id}` — case detail
- `GET /cases` — list cases (filtered by role)
- `PATCH /cases/{case_id}/status` — update status (audit-logged)

### Evidence
- `POST /cases/{case_id}/evidence` — ingest evidence (triggers pipeline via Celery)
- `GET /evidence/{evidence_id}` — evidence detail + reasoning trace
- `GET /cases/{case_id}/evidence` — list evidence for a case

### Pipeline / review
- `GET /cases/{case_id}/pipeline-status` — current agent stage, review gate status
- `POST /cases/{case_id}/review-decision` — supervisor submits human-in-the-loop decision

### Graph
- `GET /cases/{case_id}/graph` — full case graph (nodes + edges) for Cytoscape.js
- `POST /cases/{case_id}/graph/query` — Cypher-backed structured query

### Retrieval
- `POST /cases/{case_id}/ask` — natural-language question over case evidence/graph

### Audit
- `GET /audit-log?case_id=...` — auditor/admin-only, read-only

## Notes
- Every route that touches `cases` or `evidence` must write to `audit_log` — enforce this in a shared dependency/middleware, not per-route.
- `reasoning_trace` in `PipelineState` is append-only across the whole pipeline run — it's the artifact that gets persisted for explainability replay, not just intermediate scratch state.
