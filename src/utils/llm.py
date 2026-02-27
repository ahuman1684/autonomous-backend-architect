"""LLM client configuration."""

import os
from langchain_openai import ChatOpenAI


def get_llm(temperature: float = 0.2, model: str = "gpt-4o") -> ChatOpenAI:
    """Returns a configured ChatOpenAI instance.
    
    Args:
        temperature: Controls randomness. Lower = more deterministic.
        model: The OpenAI model to use.
    
    Returns:
        A ChatOpenAI instance ready for invocation.
    """
    return ChatOpenAI(
        model=model,
        temperature=temperature,
        api_key=os.environ.get("OPENAI_API_KEY"),
    )
