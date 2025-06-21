import json
from langchain_core.messages import ToolMessage
from agent_state import GraphState

class ManualSummarizerNode:
    """
    A node that processes query results with predefined logic,
    formatting it for frontend consumption without using an LLM.
    """
    def summarize(self, state: GraphState) -> dict:
        """
        Processes the query result based on its structure and returns a structured JSON.

        Args:
            state (GraphState): The current state of the graph.

        Returns:
            dict: A dictionary containing the structured summary as a JSON string.
        """
        print("--- 6. SUMMARIZING RESULT (MANUAL LOGIC) ---")
        
        query_result_str = ""
        for msg in reversed(state["messages"]):
            if isinstance(msg, ToolMessage):
                query_result_str = msg.content
                break
        
        try:
            query_result = json.loads(query_result_str)
        except json.JSONDecodeError:
            structured_summary = {
                "type": "error",
                "content": "Failed to parse query result."
            }
            print(f"   - Structured Summary: {json.dumps(structured_summary, indent=2)}")
            return {"summary": json.dumps(structured_summary)}

        # Apply simple logic: check if the result is a list of objects (table)
        if isinstance(query_result, list) and query_result and all(isinstance(i, dict) for i in query_result):
            structured_summary = {
                "type": "table",
                "headers": list(query_result[0].keys()),
                "data": query_result
            }
        # Check if the result is empty
        elif not query_result:
             structured_summary = {
                "type": "message",
                "content": "No results found."
            }
        # Otherwise, treat it as a generic key-value display
        else:
            structured_summary = {
                "type": "key_value",
                "data": query_result
            }
            
        print(f"   - Structured Summary: {json.dumps(structured_summary, indent=2)}")
        
        return {"summary": json.dumps(structured_summary)} 