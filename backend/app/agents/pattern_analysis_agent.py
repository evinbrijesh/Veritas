"""
Agent 5/9 — Pattern analysis.
Runs over the correlation graph to surface higher-order patterns:
recurring contact clusters, repeated file-sharing paths, grooming-
pattern indicators in associated chat logs (if provided), etc.
This scaffold implements the graph query scaffolding; the actual
pattern rules are a case-classification research task in themselves.
"""
from app.agents.state import PipelineState
from app.db.neo4j_client import neo4j_client


def pattern_analysis_agent(state: PipelineState) -> PipelineState:
    case_id = state["case_id"]
    subgraph = neo4j_client.get_case_subgraph(case_id)

    # Placeholder pattern rule: flag if more than N entities share
    # the same camera_model (possible single-source distribution point)
    patterns = []
    camera_groups: dict[str, int] = {}
    for row in subgraph:
        cam = row.get("e", {}).get("camera_model")
        if cam:
            camera_groups[cam] = camera_groups.get(cam, 0) + 1

    for cam, count in camera_groups.items():
        if count >= 3:
            patterns.append({
                "pattern_type": "shared_device_cluster",
                "camera_model": cam,
                "file_count": count,
            })

    state["pattern_analysis_results"] = {"patterns": patterns}
    return state
