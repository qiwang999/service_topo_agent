from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import ToolMessage

from agent_state import GraphState

SUMMARIZER_PROMPT_TEMPLATE = """
# Task
You are an expert data analyst. Your goal is to provide a clear, concise, and friendly summary of the data returned from a database query.
The user asked a question, and a query was run against a database, which returned the following JSON data.
Synthesize this information into a natural language response that directly answers the user's original question.
Do not just restate the data; interpret it and present it in a helpful way. If the data is empty, inform the user that no results were found.

# User's Original Question:
{question}

# JSON Query Result:
{query_result}

# Your Summary:
"""


class SummarizerNode:
    """
    A node that summarizes the query result into natural language.
    """

    def __init__(self, llm: ChatOpenAI):
        self.llm = llm
        self.prompt_template = ChatPromptTemplate.from_template(
            SUMMARIZER_PROMPT_TEMPLATE)
        self.chain = self.prompt_template | self.llm

    def summarize(self, state: GraphState) -> dict:
        """
        Generates a natural language summary of the query result.

        Args:
            state (GraphState): The current state of the graph.

        Returns:
            dict: A dictionary containing the summary.
        """
        print("--- 6. SUMMARIZING RESULT ---")

        # The original question is the first user message
        original_question = state["messages"][0].content
        # The query result is in the last ToolMessage
        query_result = ""
        for msg in reversed(state["messages"]):
            if isinstance(msg, ToolMessage):
                query_result = msg.content
                break

        response = self.chain.invoke({
            "question": original_question,
            "query_result": query_result
        })

        summary = response.content.strip()
        print(f"   - Generated Summary: {summary}")

        return {"summary": summary}
