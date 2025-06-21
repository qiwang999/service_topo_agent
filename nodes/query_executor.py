import json
from langchain_core.messages import ToolMessage

from agent_state import GraphState
from tools.neo4j_client import Neo4jClient

class QueryExecutorNode:
    """
    A node that executes the generated Cypher query.
    """
    def __init__(self, neo4j_client: Neo4jClient):
        self.neo4j_client = neo4j_client

    def execute(self, state: GraphState) -> dict:
        """
        Executes the Cypher query and returns the result or an error message.

        Args:
            state (GraphState): The current state of the graph.

        Returns:
            dict: A dictionary containing a ToolMessage with the query result or error.
        """
        print("--- 2. EXECUTING CYPHER QUERY ---")
        query = state["generation"]
        
        try:
            query_result = self.neo4j_client.query(query)
            print(f"   - Query Result: {query_result}")
            # Return the result as a ToolMessage
            return {"messages": [ToolMessage(content=json.dumps(query_result), tool_call_id="executor")]}
        except Exception as e:
            print(f"   - Execution Failed: {e}")
            # If the query fails, return the error message as a ToolMessage
            error_message = f"Query execution failed with error: {str(e)}"
            return {"messages": [ToolMessage(content=error_message, tool_call_id="executor")]} 