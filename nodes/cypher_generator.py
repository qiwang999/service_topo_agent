from langchain_openai import ChatOpenAI
import json
from typing import List
from langchain_core.prompts import ChatPromptTemplate
from agent_state import GraphState
from prompts.prompt_manager import PromptManager
from langchain_core.messages import HumanMessage

GENERATION_PROMPT_TEMPLATE = """
# Instructions:
You are an expert in service topology and a Neo4j Cypher query developer.
Your task is to convert a natural language query about service dependencies, instances, and infrastructure into a Cypher query.
The query will be run against a Neo4j database with a service topology graph schema.
The Cypher query must be syntactically correct and execute against the database.
Only return the Cypher query, without any explanations or enclosing it in ```cypher ... ```.

# Neo4j Schema:
{schema}

# Examples:
{examples}

# Task:
Convert the following natural language query into a Cypher query.

Natural Language Query: {question}
"""

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
        Generates a Cypher query from the user's natural language question,
        considering the conversation history.

        Args:
            state (GraphState): The current state of the graph.
            schema (str): The Neo4j database schema.

        Returns:
            dict: A dictionary containing the generated query and updated retry count.
        """
        print("--- 1. GENERATING CYPHER QUERY (WITH CONTEXT) ---")
        
        # The history is all messages EXCEPT the last one
        history_messages = state["messages"][:-1]
        # The current question is the last message
        current_question_message = state["messages"][-1]

        # We need to extract the content and role for formatting
        # We also need to handle the different message types from LangGraph
        history_for_prompt = []
        for msg in history_messages:
            if isinstance(msg, tuple): # Standard ('user', 'content') format
                history_for_prompt.append(msg)
            elif hasattr(msg, 'role') and hasattr(msg, 'content'): # LangChain message objects
                history_for_prompt.append((msg.role, msg.content))


        # Format the history for the prompt
        chat_history_str = self.prompt_manager.format_chat_history(history_for_prompt)

        # Invoke the chain with all required inputs for the prompt
        response = self.chain.invoke({
            "schema": schema,
            "question": current_question_message.content,
            "chat_history": chat_history_str,
            "examples": self.prompt_manager.get_formatted_examples(),
            "feedback_examples": self.prompt_manager.get_formatted_feedback()
        })
        
        # Clean up the generated query
        cypher_query = response.content.strip().replace("```cypher", "").replace("```", "").strip()
        print(f"   - Generated Cypher: {cypher_query}")
        
        # Increment retries and update state
        retries = state.get("retries", 0) + 1
        return {"generation": cypher_query, "retries": retries}
