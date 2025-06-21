from typing import TypedDict, Annotated
from langgraph.graph.message import add_messages

class GraphState(TypedDict):
    """
    Represents the state of our graph.

    Attributes:
        messages: The history of messages in the conversation.
        generation: The last generated Cypher query.
        retries: The number of times the agent has tried to generate a valid query.
        validation_result: The result from the syntax validation node.
        summary: The final natural language summary of the result.
    """
    messages: Annotated[list, add_messages]
    generation: str
    retries: int
    validation_result: str
    summary: str 