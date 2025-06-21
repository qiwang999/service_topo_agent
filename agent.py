import json
from dotenv import load_dotenv
from langchain_core.messages import ToolMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph, END

from typing import List, Dict

# Local imports
from agent_state import GraphState
from tools.llm_client import setup_llm
from tools.neo4j_client import Neo4jClient
from nodes.cypher_generator import CypherGeneratorNode
from nodes.cypher_validator import CypherValidatorNode
from nodes.query_executor import QueryExecutorNode
from nodes.summarizer_node import SummarizerNode
from nodes.manual_summarizer_node import ManualSummarizerNode
from prompts.prompt_manager import PromptManager

# Load environment variables from .env file
load_dotenv()


class Text2CypherAgent:
    """
    The main agent class that orchestrates the entire process.
    It initializes all components, builds the graph, and provides a run method.
    """

    def __init__(self, feedback_examples: List[Dict], model_name="gpt-4o", prompt_template: str = None, examples_file_path: str = "examples.json", summarizer_type: str = "llm"):
        self.llm = setup_llm(model_name)
        self.neo4j_client = Neo4jClient()
        self.db_schema = self.neo4j_client.get_schema()

        # The prompt manager now receives the feedback examples directly
        self.prompt_manager = PromptManager(feedback_examples, prompt_template, examples_file_path)

        self.cypher_generator_node = CypherGeneratorNode(self.llm, self.prompt_manager)
        self.cypher_validator_node = CypherValidatorNode(self.llm, self.db_schema)
        self.query_executor_node = QueryExecutorNode(self.neo4j_client)
        
        if summarizer_type == "llm":
            self.summarizer_node = SummarizerNode(self.llm)
            print("--- Using LLM-based summarizer ---")
        elif summarizer_type == "manual":
            self.summarizer_node = ManualSummarizerNode()
            print("--- Using manual logic-based summarizer ---")
        else:
            raise ValueError(f"Invalid summarizer_type: '{summarizer_type}'. Must be 'llm' or 'manual'.")
        
        self.app = self._build_graph()

    def _build_graph(self):
        """Builds and compiles the LangGraph agent."""
        workflow = StateGraph(GraphState)

        # The node functions are methods of our node classes
        workflow.add_node("generator", self.generator_node_wrapper)
        workflow.add_node("validator", self.cypher_validator_node.validate)
        workflow.add_node("executor", self.query_executor_node.execute)
        workflow.add_node("summarizer", self.summarizer_node.summarize)

        workflow.set_entry_point("generator")

        workflow.add_edge("generator", "validator")
        workflow.add_conditional_edges(
            "validator",
            self.decide_after_validation,
            {
                "regenerate": "generator",
                "execute": "executor"
            }
        )
        workflow.add_conditional_edges(
            "executor",
            self.decide_after_execution,
            {
                "regenerate": "generator",
                "summarize": "summarizer",
                "end": END
            }
        )
        workflow.add_edge("summarizer", END)
        return workflow.compile()

    def generator_node_wrapper(self, state: GraphState):
        """A wrapper to pass the dynamic DB schema to the generator node."""
        return self.cypher_generator_node.generate(state, self.db_schema)

    def decide_after_validation(self, state: GraphState) -> str:
        """
        After syntax validation, decides whether to proceed to execution or regenerate the query.
        """
        validation_result = state.get("validation_result")
        if validation_result == "invalid":
            print("   - Syntax validation failed. Regenerating query.")
            state["messages"].append(AIMessage(content="The previously generated query has invalid syntax. Please generate a new, syntactically correct query."))
            return "regenerate"
        else:
            print("   - Syntax validation successful. Proceeding to execution.")
            return "execute"

    def decide_after_execution(self, state: GraphState) -> str:
        """
        After execution, decides whether to summarize, regenerate, or end the process.
        """
        print("--- 5. POST-EXECUTION CHECK ---")
        last_message = state["messages"][-1]

        if isinstance(last_message, ToolMessage) and "Query execution failed" in last_message.content:
            # Execution failed path
            if state["retries"] >= 3:
                print("   - Max retries reached. Ending.")
                return "end"
            else:
                print("   - Execution failed. Regenerating query.")
                state["messages"].append(AIMessage(content=f"The query execution failed. Please fix it. Error: {last_message.content}"))
                return "regenerate"
        else:
            # Execution successful path
            print("   - Execution successful. Proceeding to summarize.")
            return "summarize"

    def run(self, conversation_history: list, new_query: str) -> dict:
        """
        Executes the agent for a single turn of a conversation.
        """
        # Convert simple dict history to LangChain message objects
        messages = []
        for msg in conversation_history:
            if msg.get("role") == "user":
                messages.append(HumanMessage(content=msg.get("content")))
            elif msg.get("role") == "agent":
                messages.append(AIMessage(content=msg.get("content")))
        
        # Append the new user query
        messages.append(HumanMessage(content=new_query))
        
        initial_state = { "messages": messages, "retries": 0 }
        
        final_state = self.app.invoke(initial_state, {"recursion_limit": 10})
        
        # Prepare response for the web service
        summary = final_state.get("summary", "I'm sorry, I couldn't process that.")
        
        # Update history for client
        updated_history = conversation_history + [
            {"role": "user", "content": new_query},
            {"role": "agent", "content": summary}
        ]

        return {
            "summary": summary,
            "generated_cypher": final_state.get("generation"),
            "updated_history": updated_history,
        }
