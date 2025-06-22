import json
from dotenv import load_dotenv
from langchain_core.messages import ToolMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph, END

from typing import List, Dict

# Local imports
from agent_state import GraphState
from tools.llm_client import setup_llm
from tools.neo4j_client import Neo4jClient
from database.vector_db_manager import VectorDBManager
from prompts.enhanced_prompt_manager import EnhancedPromptManager
from nodes.enhanced_cypher_generator import EnhancedCypherGeneratorNode
from nodes.cypher_validator import CypherValidatorNode
from nodes.query_executor import QueryExecutorNode
from nodes.summarizer_node import SummarizerNode
from nodes.manual_summarizer_node import ManualSummarizerNode

# Load environment variables from .env file
load_dotenv()


class EnhancedText2CypherAgent:
    """
    Enhanced agent with embedding-based features including semantic search, caching, and dynamic example selection.
    """

    def __init__(self, feedback_examples: List[Dict], model_name="gpt-4o",
                 prompt_template: str = None, examples_file_path: str = "examples.json",
                 summarizer_type: str = "llm", run_mode: str = "standard",
                 enable_cache: bool = True, enable_embeddings: bool = True):

        self.llm = setup_llm(model_name)
        self.neo4j_client = Neo4jClient()
        self.db_schema = self.neo4j_client.get_schema()
        self.run_mode = run_mode
        self.enable_cache = enable_cache
        self.enable_embeddings = enable_embeddings

        # Initialize vector database manager
        self.vector_db_manager = VectorDBManager()

        # Initialize enhanced prompt manager
        self.enhanced_prompt_manager = EnhancedPromptManager(
            vector_db_manager=self.vector_db_manager,
            base_prompt_template=prompt_template,
            examples_file_path=examples_file_path
        )

        # Initialize nodes
        self.enhanced_cypher_generator_node = EnhancedCypherGeneratorNode(
            self.llm, self.enhanced_prompt_manager, self.vector_db_manager, enable_cache
        )
        self.cypher_validator_node = CypherValidatorNode(
            self.llm, self.db_schema)
        self.query_executor_node = QueryExecutorNode(self.neo4j_client)

        if summarizer_type == "llm":
            self.summarizer_node = SummarizerNode(self.llm)
            print("--- Using LLM-based summarizer ---")
        elif summarizer_type == "manual":
            self.summarizer_node = ManualSummarizerNode()
            print("--- Using manual logic-based summarizer ---")
        else:
            raise ValueError(
                f"Invalid summarizer_type: '{summarizer_type}'. Must be 'llm' or 'manual'.")

        print(f"--- Enhanced Agent Initialized ---")
        print(f"   Run mode: {run_mode}")
        print(f"   Cache enabled: {enable_cache}")
        print(f"   Embeddings enabled: {enable_embeddings}")

        # Initialize vector database if embeddings are enabled
        if self.enable_embeddings:
            self._initialize_vector_database()

        self.app = self._build_graph()

    def _initialize_vector_database(self):
        """Initialize the vector database with existing data."""
        try:
            self.vector_db_manager.initialize_vector_database()
            print("--- Vector database initialized successfully ---")
        except Exception as e:
            print(f"Warning: Failed to initialize vector database: {e}")

    def _build_graph(self):
        """Builds and compiles the LangGraph agent."""
        workflow = StateGraph(GraphState)

        # The node functions are methods of our node classes
        workflow.add_node("generator", self.generator_node_wrapper)
        workflow.add_node("executor", self.query_executor_node.execute)
        workflow.add_node("summarizer", self.summarizer_node.summarize)

        workflow.set_entry_point("generator")

        if self.run_mode == "fast":
            # Fast mode: skip validation, go directly from generator to executor
            workflow.add_edge("generator", "executor")
            print("   - Fast mode: Skipping validation for faster execution")
        else:
            # Standard mode: include validation
            workflow.add_node("validator", self.cypher_validator_node.validate)
            workflow.add_edge("generator", "validator")
            workflow.add_conditional_edges(
                "validator",
                self.decide_after_validation,
                {
                    "regenerate": "generator",
                    "execute": "executor"
                }
            )
            print("   - Standard mode: Including validation step")

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
        return self.enhanced_cypher_generator_node.generate(state, self.db_schema)

    def decide_after_validation(self, state: GraphState) -> str:
        """
        After syntax validation, decides whether to proceed to execution or regenerate the query.
        """
        validation_result = state.get("validation_result")
        if validation_result == "invalid":
            print("   - Syntax validation failed. Regenerating query.")
            state["messages"].append(AIMessage(
                content="The previously generated query has invalid syntax. Please generate a new, syntactically correct query."))
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
                state["messages"].append(AIMessage(
                    content=f"The query execution failed. Please fix it. Error: {last_message.content}"))
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

        initial_state = {"messages": messages, "retries": 0}

        final_state = self.app.invoke(initial_state, {"recursion_limit": 10})

        # Prepare response for the web service
        summary = final_state.get(
            "summary", "I'm sorry, I couldn't process that.")

        # Update history for client
        updated_history = conversation_history + [
            {"role": "user", "content": new_query},
            {"role": "agent", "content": summary}
        ]

        # Prepare enhanced response with metadata
        response = {
            "summary": summary,
            "generated_cypher": final_state.get("generation"),
            "updated_history": updated_history,
        }

        # Add cache information if available
        if final_state.get("cache_hit"):
            response["cache_hit"] = True
            response["cache_similarity"] = final_state.get("cache_similarity")

        # Add prompt metadata if available
        if final_state.get("prompt_metadata"):
            response["prompt_metadata"] = final_state.get("prompt_metadata")

        return response

    def get_cache_stats(self) -> Dict:
        """Get cache statistics."""
        return self.vector_db_manager.get_cache_stats()

    def find_similar_examples(self, question: str, top_k: int = 5) -> List[Dict]:
        """Find similar examples for a question."""
        return self.vector_db_manager.find_similar_examples(question, top_k)

    def find_similar_feedback(self, question: str, top_k: int = 3) -> List[Dict]:
        """Find similar feedback for a question."""
        return self.vector_db_manager.find_similar_feedback(question, top_k)
