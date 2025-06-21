import os
from langchain_community.graphs import Neo4jGraph

class Neo4jClient:
    """
    A client to interact with a Neo4j database.
    It handles connection, schema retrieval, and querying.
    """
    def __init__(self):
        uri = os.getenv("NEO4J_URI")
        username = os.getenv("NEO4J_USERNAME")
        password = os.getenv("NEO4J_PASSWORD")
        if not all([uri, username, password]):
            raise ValueError("FATAL: Neo4j connection details not found in .env file.")
        
        try:
            self.db = Neo4jGraph(url=uri, username=username, password=password)
        except Exception as e:
            raise ConnectionError(f"Failed to connect to Neo4j. Error: {e}")

    def get_schema(self) -> str:
        """
        Retrieves the database schema.
        Returns a dummy schema if the connection fails.
        """
        try:
            return self.db.schema
        except Exception as e:
            print(f"Warning: Could not connect to Neo4j to get schema. Using a dummy schema. Error: {e}")
            return """Node properties are the following:
Service {name: STRING, version: STRING, status: STRING},
Instance {id: STRING, ip_address: STRING, status: STRING},
Region {name: STRING},
Namespace {name: STRING}

Relationship properties are the following:

The relationships are the following:
(:Instance)-[:INSTANCE_OF]->(:Service),
(:Service)-[:DEPENDS_ON]->(:Service),
(:Service)-[:LOCATED_IN]->(:Region),
(:Service)-[:PART_OF]->(:Namespace)
"""

    def query(self, query: str, params: dict = None):
        """
        Executes a Cypher query against the database.
        """
        return self.db.query(query, params) 