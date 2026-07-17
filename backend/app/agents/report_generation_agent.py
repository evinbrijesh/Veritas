"""
Agent 8/9 — Report generation.
Uses the local Qwen2.5 7B model to draft a structured investigator
report summarizing findings from every prior agent. Uses the
reasoning-trace method so the report is explainable, not a black box —
investigators can see WHY the model concluded what it concluded.

If requires_human_review is True, the report is explicitly marked
DRAFT — PENDING REVIEW and cannot be exported as final without a
supervisor sign-off (enforced at the API layer via require_role()).
"""
from app.agents.state import PipelineState
from app.ml.llm_client import llm_client


REPORT_SYSTEM_PROMPT = """You are assisting a licensed investigator by drafting a factual,
neutral summary of automated evidence analysis. Do not speculate beyond
the provided data. Do not make legal conclusions. Flag uncertainty
explicitly wherever it exists."""


def report_generation_agent(state: PipelineState) -> PipelineState:
    summary_input = {
        "case_id": state["case_id"],
        "synthetic_detection": state.get("synthetic_detection_results", {}),
        "correlations": state.get("correlation_results", {}),
        "patterns": state.get("pattern_analysis_results", {}),
        "timeline": state.get("timeline_results", {}),
        "risk_score": state.get("risk_score", {}),
    }

    prompt = f"Summarize the following evidence analysis for an investigator report:\n{summary_input}"
    llm_output = llm_client.generate_with_reasoning_trace(prompt, system=REPORT_SYSTEM_PROMPT)

    status = "DRAFT — PENDING SUPERVISOR REVIEW" if state.get("requires_human_review") else "FINALIZED"

    state["report"] = {
        "status": status,
        "summary": llm_output["conclusion"],
        "reasoning_trace": llm_output["reasoning"],
    }
    state.setdefault("reasoning_trace", []).append(llm_output)
    return state
