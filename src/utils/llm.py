"""LLM client configuration."""

import os
from typing import Any

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


def get_llm_with_tools(
    tools: list[Any],
    temperature: float = 0.2,
    model: str = "gpt-4o",
) -> ChatOpenAI:
    """Returns a ChatOpenAI instance with tools bound if any are provided.
    
    Args:
        tools: List of LangChain tool objects to bind to the LLM.
        temperature: Controls randomness. Lower = more deterministic.
        model: The OpenAI model to use.
    
    Returns:
        A ChatOpenAI instance with tools bound (or plain if tools is empty).
    """
    llm = get_llm(temperature=temperature, model=model)
    if tools:
        return llm.bind_tools(tools)
    return llm
