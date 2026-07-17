"""
Thin wrapper around the Neo4j driver. This is where the evidence
knowledge graph lives: entities (people, devices, accounts, files),
relationships (CONTACTED, APPEARED_WITH, SENT_TO, CO_LOCATED),
discovered by the correlation and pattern-analysis agents.
"""
from neo4j import GraphDatabase
from app.config import settings


class Neo4jClient:
    def __init__(self):
        self._driver = GraphDatabase.driver(
            settings.NEO4J_URI,
            auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
        )

    def close(self):
        self._driver.close()

    def run(self, query: str, params: dict | None = None) -> list[dict]:
        with self._driver.session() as session:
            result = session.run(query, params or {})
            return [record.data() for record in result]

    # --- Example domain methods the agents will call into ---

    def upsert_entity(self, entity_id: str, entity_type: str, properties: dict):
        query = """
        MERGE (e:Entity {id: $entity_id})
        SET e.type = $entity_type, e += $properties
        RETURN e
        """
        return self.run(query, {
            "entity_id": entity_id,
            "entity_type": entity_type,
            "properties": properties,
        })

    def link_entities(self, from_id: str, to_id: str, relationship: str, properties: dict | None = None):
        query = f"""
        MATCH (a:Entity {{id: $from_id}}), (b:Entity {{id: $to_id}})
        MERGE (a)-[r:{relationship}]->(b)
        SET r += $properties
        RETURN r
        """
        return self.run(query, {
            "from_id": from_id,
            "to_id": to_id,
            "properties": properties or {},
        })

    def get_case_subgraph(self, case_id: str) -> list[dict]:
        query = """
        MATCH (e:Entity {case_id: $case_id})-[r]-(other:Entity {case_id: $case_id})
        RETURN e, r, other
        """
        return self.run(query, {"case_id": case_id})


neo4j_client = Neo4jClient()
