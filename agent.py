import json
from dotenv import load_dotenv
from langchain_core.messages import ToolMessage
from langgraph.graph import StateGraph, END

# Local imports
from agent_state import GraphState
from tools.llm_client import setup_llm
from tools.neo4j_client import Neo4jClient
from nodes.cypher_generator import CypherGeneratorNode, PromptManager
from nodes.cypher_validator import CypherValidatorNode
from nodes.query_executor import QueryExecutorNode
from nodes.summarizer_node import SummarizerNode
from nodes.manual_summarizer_node import ManualSummarizerNode

# Load environment variables from .env file
load_dotenv()


class Text2CypherAgent:
    """
    The main agent class that orchestrates the entire process.
    It initializes all components, builds the graph, and provides a run method.
    """

    def __init__(self, model_name="gpt-4o", prompt_template: str = None, examples_file_path: str = "examples.json", summarizer_type: str = "llm"):
        # Setup tools and clients
        self.llm = setup_llm(model_name)
        self.neo4j_client = Neo4jClient()
        self.db_schema = self.neo4j_client.get_schema()

        # Setup prompt manager
        self.prompt_manager = PromptManager(
            prompt_template, examples_file_path)

        # Setup graph nodes
        self.cypher_generator_node = CypherGeneratorNode(
            self.llm, self.prompt_manager)
        self.cypher_validator_node = CypherValidatorNode(
            self.llm, self.db_schema)
        self.query_executor_node = QueryExecutorNode(self.neo4j_client)

        # Initialize the selected summarizer node based on the chosen type
        if summarizer_type == "llm":
            self.summarizer_node = SummarizerNode(self.llm)
            print("--- Using LLM-based summarizer ---")
        elif summarizer_type == "manual":
            self.summarizer_node = ManualSummarizerNode()
            print("--- Using manual logic-based summarizer ---")
        else:
            raise ValueError(
                f"Invalid summarizer_type: '{summarizer_type}'. Must be 'llm' or 'manual'.")

        # Build and compile the graph
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
            error_message = "The previously generated query has invalid syntax. Please generate a new, syntactically correct query."
            state["messages"].append(("user", error_message))
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
                error_message = f"The query execution failed. Please fix it. Error: {last_message.content}"
                state["messages"].append(("user", error_message))
                return "regenerate"
        else:
            # Execution successful path
            print("   - Execution successful. Proceeding to summarize.")
            return "summarize"

    def run(self, query: str) -> dict:
        """
        Executes the agent with a given natural language query.
        """
        initial_state = {"messages": [("user", query)], "retries": 0}
        # Set a recursion limit to prevent infinite loops
        final_state = self.app.invoke(initial_state, {"recursion_limit": 10})

        # Format the final output
        final_result_message = final_state['messages'][-1]
        if isinstance(final_result_message, ToolMessage):
            try:
                result_data = json.loads(final_result_message.content)
            except json.JSONDecodeError:
                result_data = {"error": "Could not parse the final result.",
                               "raw_content": final_result_message.content}
        else:
            # This might happen if the graph ends on a failure note without a ToolMessage
            result_data = {"final_message": str(final_result_message)}

        return {
            "raw_json_result": result_data,
            "generated_cypher": final_state.get("generation"),
            "summary": final_state.get("summary"),
            "retries": final_state.get("retries")
        }
