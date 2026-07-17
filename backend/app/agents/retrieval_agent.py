"""
Agent 9/9 — Retrieval.
Answers investigator follow-up questions against the already-built
case knowledge graph + report (e.g. "which files were linked to this
device?"), without re-running the full pipeline. Combines a Neo4j
Cypher query with an LLM pass to phrase the answer naturally.
"""
from app.db.neo4j_client import neo4j_client
from app.ml.llm_client import llm_client


def retrieval_agent(case_id: str, question: str) -> dict:
    subgraph = neo4j_client.get_case_subgraph(case_id)

    prompt = (
        f"Case knowledge graph data:\n{subgraph}\n\n"
        f"Investigator question: {question}\n\n"
        f"Answer using ONLY the data provided above. If the answer isn't "
        f"present in the data, say so explicitly rather than guessing."
    )
    result = llm_client.generate_with_reasoning_trace(prompt)
    return {"answer": result["conclusion"], "reasoning": result["reasoning"]}
