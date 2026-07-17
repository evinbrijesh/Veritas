"""
Endpoints for querying the case knowledge graph — both raw (for the
Cytoscape.js frontend to render) and natural-language (via the
retrieval agent).
"""
from fastapi import APIRouter, Depends

from app.schemas.evidence import RetrievalQuery
from app.agents.retrieval_agent import retrieval_agent
from app.db.neo4j_client import neo4j_client
from app.auth.routes import get_current_investigator
from app.db.postgres_models import Investigator

router = APIRouter(prefix="/graph", tags=["graph"])


@router.get("/case/{case_id}/subgraph")
def get_subgraph(case_id: str, investigator: Investigator = Depends(get_current_investigator)):
    """Raw graph data for the Cytoscape.js frontend to render."""
    return neo4j_client.get_case_subgraph(case_id)


@router.post("/ask")
def ask_question(query: RetrievalQuery, investigator: Investigator = Depends(get_current_investigator)):
    """Natural-language Q&A over an already-processed case's graph."""
    return retrieval_agent(query.case_id, query.question)
