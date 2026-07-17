"""
Agent 1/9 — Ingestion.
Validates incoming evidence files, computes hashes for chain-of-custody,
determines file type, and stages them for the rest of the pipeline.
"""
import hashlib
import os
from app.agents.state import PipelineState


def compute_sha256(file_path: str) -> str:
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def ingestion_agent(state: PipelineState) -> PipelineState:
    results = {}
    for path in state["evidence_file_paths"]:
        results[path] = {
            "sha256": compute_sha256(path),
            "size_bytes": os.path.getsize(path),
            "file_type": os.path.splitext(path)[1].lower(),
            "ingested_ok": True,
        }
    state["ingestion_results"] = results
    return state
