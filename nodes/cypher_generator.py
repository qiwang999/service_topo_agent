from langchain_openai import ChatOpenAI

from agent_state import GraphState
from prompts.prompt_manager import PromptManager

class CypherGeneratorNode:
    """
    A node that generates a Cypher query based on the current state.
    """
    def __init__(self, llm: ChatOpenAI, prompt_manager: PromptManager):
        self.llm = llm
        self.prompt_manager = prompt_manager
        self.chain = self.prompt_manager.get_prompt_template() | self.llm

    def generate(self, state: GraphState, schema: str) -> dict:
        """
        Generates a Cypher query from the user's natural language question.

        Args:
            state (GraphState): The current state of the graph.
            schema (str): The Neo4j database schema.

        Returns:
            dict: A dictionary containing the generated query and updated retry count.
        """
        print("--- 1. GENERATING CYPHER QUERY ---")
        last_user_message = state["messages"][-1]
        
        # Invoke the chain with all required inputs for the prompt
        response = self.chain.invoke({
            "schema": schema,
            "question": last_user_message.content,
            "examples": self.prompt_manager.get_formatted_examples()
        })
        
        # Clean up the generated query
        cypher_query = response.content.strip().replace("```cypher", "").replace("```", "").strip()
        print(f"   - Generated Cypher: {cypher_query}")
        
        # Increment retries and update state
        retries = state.get("retries", 0) + 1
        return {"generation": cypher_query, "retries": retries} 