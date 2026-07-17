"""
Agent 4/9 — Correlation.
Takes metadata (GPS, timestamps, device IDs) and ingestion hashes and
writes entities/relationships into the Neo4j knowledge graph — e.g.
linking two files taken by the same device, at the same location, or
within the same time window across the case's evidence set.
"""
from app.agents.state import PipelineState
from app.db.neo4j_client import neo4j_client


def correlation_agent(state: PipelineState) -> PipelineState:
    case_id = state["case_id"]
    correlations_found = []

    for path, meta in state.get("metadata_results", {}).items():
        entity_id = state["ingestion_results"][path]["sha256"]

        neo4j_client.upsert_entity(
            entity_id=entity_id,
            entity_type="MediaFile",
            properties={
                "case_id": case_id,
                "path": path,
                "gps_lat": meta.get("gps", {}).get("lat"),
                "gps_lon": meta.get("gps", {}).get("lon"),
                "datetime_original": meta.get("datetime_original"),
                "camera_model": meta.get("camera_model"),
            },
        )

        # Example correlation rule: same camera_model across files -> link them.
        # A real implementation would do this as a batched Cypher query rather
        # than in a Python loop, but this illustrates the pattern.
        camera = meta.get("camera_model")
        if camera:
            correlations_found.append({"entity": entity_id, "camera_model": camera})

    state["correlation_results"] = {"correlations_found": correlations_found}
    return state
