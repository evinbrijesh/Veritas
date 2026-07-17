# CLAUDE.md — VERITAS

This is the document every agent/prompt should read first. Keep it current as the project evolves — ADRs, stats, and detailed style guides get added here once the project has enough shape to make them concrete.

## Overview

VERITAS (Verified Evidence Reasoning & Intelligence Triage Agentic System) is a multi-agent AI pipeline for digital forensic evidence analysis in child protection investigations, built for the HAC'KP hackathon (Kerala Police Cyberdome, ACPIA problem statement).

Users are law enforcement investigators across roles (analyst/supervisor/auditor/admin), often at different physical locations. The system must run on-premises, air-gapped-capable, with an explainable, chain-of-custody-preserving pipeline. See `PRD.md` for full scope.

## Stack

See `STACK.md` for the full decision record. Summary:

- Python 3.11+, FastAPI, Celery + Redis
- LangGraph for the 9-agent pipeline
- Ollama + Qwen2.5 7B (local LLM, no cloud calls)
- EfficientNet-B4 (synthetic image detection)
- Neo4j (case graph), Postgres (auth + audit log)
- Cytoscape.js (frontend graph rendering)
- Docker Compose, six services, bind-mount volumes only

## Conventions

### Code
- Python: type-hinted, `black`-formatted, one agent = one module under `agents/`
- Agent I/O contracts are explicit — every LangGraph node takes and returns a typed state object, never a loose dict
- No agent calls an external network service. All inference is local (Ollama, local EfficientNet weights).

### Data & persistence
- Docker bind-mounts only, never named volumes — evidence and case data must survive `docker compose down` and manual folder inspection
- Neo4j is local-only by design — never point it at a cloud instance
- Nightly backup script for Neo4j is mandatory in any deployment, not optional tooling

### Auth & chain of custody
- Every write to evidence or case data must go through the audit log — no silent writes
- Audit log table is append-only: no UPDATE/DELETE paths, enforced at the DB layer, not just app layer
- Roles (`analyst`/`supervisor`/`auditor`/`admin`) gate access at the route level in FastAPI, not just the UI

### Explainability
- Every agent must attach a reasoning trace to its output — this is a required field, not optional metadata
- Confidence scores must be calibrated, and agents must support an explicit **abstain** state rather than forcing a low-confidence guess
- Human-in-the-loop review gate is a hard pipeline checkpoint, not a UI suggestion — pipeline execution actually pauses

### Known gaps / active work
- Auth layer needs hardening — see `STACK.md` known gaps section. Treat any auth-related PR/prompt as touching a sensitive, unfinished area.

## What's NOT here yet (add as the project grows)
- ADRs (architecture decision records) for major agent-design tradeoffs
- Out-of-scope list beyond the MVP cut in `PRD.md`
- Detailed style guide (naming, error handling patterns, logging conventions)
- Test outline / coverage expectations

Hand these off to be fleshed out once the current scaffold has stabilized.
