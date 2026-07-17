"""
LangGraph orchestration graph — wires all 9 agents into the VERITAS
pipeline. Ingestion -> Metadata -> Synthetic Detection -> Correlation
-> Pattern Analysis -> Timeline -> Risk Scoring -> Report Generation.
(Retrieval is invoked separately, on-demand, after the pipeline runs —
see api/routes_graph.py.)

The graph includes a conditional human-in-the-loop gate: if any agent
sets requires_human_review=True, the graph routes to an `awaiting_review`
node instead of finalizing, and a supervisor must approve via the API
before the report is marked FINALIZED (see auth/routes.py require_role).
"""
from langgraph.graph import StateGraph, END
from app.agents.state import PipelineState

from app.agents.ingestion_agent import ingestion_agent
from app.agents.metadata_agent import metadata_agent
from app.agents.synthetic_detection_agent import synthetic_detection_agent
from app.agents.correlation_agent import correlation_agent
from app.agents.pattern_analysis_agent import pattern_analysis_agent
from app.agents.timeline_agent import timeline_agent
from app.agents.risk_scoring_agent import risk_scoring_agent
from app.agents.report_generation_agent import report_generation_agent


def awaiting_review_node(state: PipelineState) -> PipelineState:
    """
    Terminal node when human review is required. The report agent still
    runs (to give the supervisor something to review) but the API layer
    will not allow export/finalization until a supervisor approves.
    """
    state["human_review_notes"] = state.get(
        "human_review_notes",
        "Automatically routed for human review due to low-confidence or abstained findings.",
    )
    return state


def route_after_synthetic_detection(state: PipelineState) -> str:
    return "correlation_agent"  # always continue; review flag is checked at report stage


def build_pipeline_graph():
    graph = StateGraph(PipelineState)

    graph.add_node("ingestion_agent", ingestion_agent)
    graph.add_node("metadata_agent", metadata_agent)
    graph.add_node("synthetic_detection_agent", synthetic_detection_agent)
    graph.add_node("correlation_agent", correlation_agent)
    graph.add_node("pattern_analysis_agent", pattern_analysis_agent)
    graph.add_node("timeline_agent", timeline_agent)
    graph.add_node("risk_scoring_agent", risk_scoring_agent)
    graph.add_node("report_generation_agent", report_generation_agent)
    graph.add_node("awaiting_review_node", awaiting_review_node)

    graph.set_entry_point("ingestion_agent")
    graph.add_edge("ingestion_agent", "metadata_agent")
    graph.add_edge("metadata_agent", "synthetic_detection_agent")
    graph.add_conditional_edges(
        "synthetic_detection_agent",
        route_after_synthetic_detection,
        {"correlation_agent": "correlation_agent"},
    )
    graph.add_edge("correlation_agent", "pattern_analysis_agent")
    graph.add_edge("pattern_analysis_agent", "timeline_agent")
    graph.add_edge("timeline_agent", "risk_scoring_agent")
    graph.add_edge("risk_scoring_agent", "report_generation_agent")

    graph.add_conditional_edges(
        "report_generation_agent",
        lambda state: "awaiting_review_node" if state.get("requires_human_review") else END,
        {"awaiting_review_node": "awaiting_review_node", END: END},
    )
    graph.add_edge("awaiting_review_node", END)

    return graph.compile()


pipeline_graph = build_pipeline_graph()


def run_pipeline(case_id: str, evidence_file_paths: list[str]) -> PipelineState:
    initial_state: PipelineState = {
        "case_id": case_id,
        "evidence_file_paths": evidence_file_paths,
        "requires_human_review": False,
    }
    return pipeline_graph.invoke(initial_state)
