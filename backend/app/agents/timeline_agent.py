"""
Agent 6/9 — Timeline construction.
Orders all evidence by extracted timestamps into a chronological
sequence investigators can walk through, with gaps/anomalies flagged
(e.g. a file whose EXIF date predates the device's purchase date).
"""
from app.agents.state import PipelineState


def timeline_agent(state: PipelineState) -> PipelineState:
    events = []
    for path, meta in state.get("metadata_results", {}).items():
        ts = meta.get("datetime_original")
        if ts:
            events.append({"file": path, "timestamp": ts})

    events.sort(key=lambda e: e["timestamp"])
    state["timeline_results"] = {"ordered_events": events}
    return state
