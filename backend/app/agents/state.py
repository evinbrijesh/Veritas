"""
Shared state object passed between agents in the LangGraph pipeline.
Each agent reads what it needs and writes its own findings back —
LangGraph handles the sequencing and lets us branch (e.g. skip
pattern-analysis if correlation found nothing) or loop back for
human-in-the-loop approval gates.
"""
from typing import TypedDict, Any


class PipelineState(TypedDict, total=False):
    case_id: str
    evidence_file_paths: list[str]

    # populated progressively by each agent
    ingestion_results: dict[str, Any]
    metadata_results: dict[str, Any]
    synthetic_detection_results: dict[str, Any]
    correlation_results: dict[str, Any]
    pattern_analysis_results: dict[str, Any]
    timeline_results: dict[str, Any]
    risk_score: dict[str, Any]
    report: dict[str, Any]

    # human-in-the-loop gate
    requires_human_review: bool
    human_review_notes: str | None

    # explainability
    reasoning_trace: list[dict]
