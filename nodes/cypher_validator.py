from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from agent_state import GraphState

VALIDATION_PROMPT_TEMPLATE = """
# Task
You are an expert Neo4j syntax validator. Your task is to determine if the following Cypher query is syntactically correct based on the provided Neo4j database schema. Do not execute the query or check if the data exists in the database. You must focus exclusively on the syntax.

- Check for correct Cypher keywords (e.g., MATCH, WHERE, RETURN).
- Check for balanced parentheses (), brackets [], and curly braces {}.
- Check for typos in relationship types, labels, and properties based on the schema.

Respond with a single word: 'valid' if the query is syntactically correct, or 'invalid' if it is not.

# Neo4j Schema:
{schema}

# Cypher Query to Validate:
{query}
"""

class CypherValidatorNode:
    """
    A node that validates the syntax of a generated Cypher query using an LLM.
    """
    def __init__(self, llm: ChatOpenAI, schema: str):
        self.llm = llm
        self.schema = schema
        self.prompt_template = ChatPromptTemplate.from_template(VALIDATION_PROMPT_TEMPLATE)
        self.chain = self.prompt_template | self.llm

    def validate(self, state: GraphState) -> dict:
        """
        Validates the Cypher query present in the state.

        Args:
            state (GraphState): The current state of the graph.

        Returns:
            dict: A dictionary with the validation result ('valid' or 'invalid').
        """
        print("--- 4. VALIDATING CYPHER SYNTAX ---")
        query_to_validate = state["generation"]
        
        response = self.chain.invoke({
            "schema": self.schema,
            "query": query_to_validate
        })
        
        validation_result = response.content.strip().lower()
        print(f"   - Validation Result: {validation_result}")
        
        if "invalid" in validation_result:
            return {"validation_result": "invalid"}
        else:
            return {"validation_result": "valid"} 