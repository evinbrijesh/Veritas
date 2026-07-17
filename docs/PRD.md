# VERITAS — Product Brief

**Verified Evidence Reasoning & Intelligence Triage Agentic System**

## What it is
A multi-agent AI pipeline that ingests digital forensic evidence and produces structured, explainable, chain-of-custody-preserving analysis to accelerate child protection investigations. Built for the HAC'KP hackathon (Kerala Police Cyberdome), targeting the ACPIA problem statement.

## Who it's for
Law enforcement investigators (analysts, supervisors, auditors, admins) working forensic evidence cases, often across different physical locations within a department. Deployment must work in sensitive, low-connectivity, potentially air-gapped environments — this is not a cloud SaaS tool.

## The problem
Existing forensic tools (Cellebrite, Magnet AXIOM, Griffeye, ADF Solutions) do bulk classification but lack:
- Adversarial-perturbation-aware synthetic media detection
- Human-in-the-loop explainability at the pipeline/reasoning level
- A unified, queryable graph of evidence relationships across a case
- Reasoning traces investigators (and courts) can audit

## Core features (MVP scope)
1. **Ingestion** of evidence (images, metadata, associated files) into a case
2. **Nine-stage agent pipeline**: ingestion → metadata → synthetic detection → correlation → pattern analysis → timeline → risk scoring → report generation → retrieval
3. **Synthetic/manipulated media detection** via a two-stage EfficientNet-B4 classifier
4. **Human-in-the-loop review gate** — pipeline pauses for investigator sign-off at defined checkpoints, not fully autonomous
5. **Explainability** — every agent decision has a reasoning trace, replayable, with calibrated confidence and an explicit abstention state (no forced high-confidence guesses)
6. **Case graph** — entities/evidence/relationships stored in Neo4j, queryable and visualized (Cytoscape.js)
7. **Natural-language retrieval** over case evidence and graph
8. **Chain of custody** — immutable audit log of every action taken on evidence, tied to authenticated users with role-based access (analyst/supervisor/auditor/admin)
9. **Reporting** — generated case reports summarizing findings, evidence, and reasoning

## Explicitly out of scope for MVP
- Kubernetes / multi-department scaling (future path, not a starting point)
- Full auth hardening (flagged as a known gap — analyst-set role flows work, but is not yet audit-hardened)
- Cross-department federation or cloud sync

## Success looks like
A working, demoable, explainable pipeline that:
- Runs fully on-premises via Docker Compose, no external calls required for core inference
- Preserves an auditable chain of custody end-to-end
- Lets an investigator ask a natural-language question and get a traceable answer grounded in the evidence graph
- Clearly outperforms existing tools on the "why did it flag this" question, not just raw detection accuracy

## Constraints
- On-premises, air-gapped-capable — no dependency on external APIs for core pipeline execution
- Local LLM only (Ollama/Qwen2.5 7B), no cloud model calls for evidence reasoning
- Data persistence via Docker bind-mounts is non-negotiable — evidence data must survive container teardown
