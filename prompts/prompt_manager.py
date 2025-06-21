import json
from typing import List, Tuple
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import AIMessage, HumanMessage

DEFAULT_PROMPT_TEMPLATE = """
# Instructions:
You are an expert in service topology and a Neo4j Cypher query developer.
Your task is to convert a natural language query about service dependencies, instances, and infrastructure into a Cypher query.
You must use the provided conversation history to understand the context of the user's current question.
The Cypher query must be syntactically correct and execute against the database.
Only return the Cypher query, without any explanations or enclosing it in ```cypher ... ```.

# Neo4j Schema:
{schema}

# Few-Shot Examples:
{examples}

---
# Conversation History:
{chat_history}
---

# Task:
Based on the conversation history and the user's question below, generate the appropriate Cypher query.

Natural Language Query: {question}
"""

class PromptManager:
    """
    Manages loading and formatting of prompt templates and few-shot examples.
    """
    def __init__(self, prompt_template_str: str = None, examples_file_path: str = "examples.json"):
        self.template_str = prompt_template_str if prompt_template_str is not None else DEFAULT_PROMPT_TEMPLATE
        self.examples = self._load_examples(examples_file_path)
        self.formatted_examples = self._format_examples_for_prompt(self.examples)
        self.prompt_template = ChatPromptTemplate.from_template(self.template_str)

    def _load_examples(self, file_path: str) -> List[dict]:
        """Loads few-shot examples from a JSON file."""
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Warning: Could not load examples from {file_path}. Proceeding without examples. Error: {e}")
            return []

    def _format_examples_for_prompt(self, examples: List[dict]) -> str:
        """Formats the examples list into a string for the prompt."""
        if not examples:
            return "No examples provided."
        
        return "\n\n".join(
            [f"# Natural Language: {ex['natural_language']}\n# Cypher: {ex['cypher']}" for ex in examples]
        )
    
    @staticmethod
    def format_chat_history(messages: List[Tuple[str, str]]) -> str:
        """Formats the chat history into a readable string for the prompt."""
        if not messages:
            return "No previous conversation."
        
        history_str = ""
        for role, content in messages:
            # We only care about user questions and agent's summaries for history
            if role == "user":
                history_str += f"User: {content}\n"
            elif isinstance(content, str) and content.startswith('{"type":'): # Heuristic for manual summary
                 # Try to parse the manual summary for a more readable history
                try:
                    summary_data = json.loads(content)
                    history_str += f"Agent: (Responded with structured data of type: {summary_data.get('type')})\n"
                except:
                     history_str += f"Agent: (Responded with structured data)\n"
            elif isinstance(content, str): # Assumes LLM summary
                 history_str += f"Agent: {content}\n"
        
        return history_str


    def get_prompt_template(self) -> ChatPromptTemplate:
        return self.prompt_template

    def get_formatted_examples(self) -> str:
        return self.formatted_examples 