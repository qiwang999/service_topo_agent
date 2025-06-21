import os
from langchain_openai import ChatOpenAI

def setup_llm(model_name: str = "gpt-4o") -> ChatOpenAI:
    """
    Initializes and returns the OpenAI LLM.
    
    Args:
        model_name (str): The name of the OpenAI model to use.

    Returns:
        ChatOpenAI: An instance of the ChatOpenAI client.
        
    Raises:
        ValueError: If the OPENAI_API_KEY environment variable is not set.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("FATAL: OPENAI_API_KEY environment variable not set.")
    return ChatOpenAI(model=model_name, openai_api_key=api_key, temperature=0) 