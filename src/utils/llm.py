"""LLM client configuration."""

import os
from typing import Any

from langchain_openai import ChatOpenAI

_GROQ_BASE_URL = "https://api.groq.com/openai/v1"
_DEFAULT_MODEL = "llama-3.3-70b-versatile"


def get_llm(
    temperature: float = 0.2,
    model: str | None = None,
) -> ChatOpenAI:
    """Returns a configured ChatOpenAI instance pointed at Groq's API.

    Args:
        temperature: Controls randomness. Lower = more deterministic.
        model: The Groq model to use. Defaults to the LLM_MODEL env var or
               ``llama-3.3-70b-versatile``.

    Returns:
        A ChatOpenAI instance ready for invocation.
    """
    resolved_model = model or os.environ.get("LLM_MODEL", _DEFAULT_MODEL)
    return ChatOpenAI(
        model=resolved_model,
        temperature=temperature,
        api_key=os.environ.get("GROQ_API_KEY"),
        base_url=_GROQ_BASE_URL,
    )


def get_llm_with_tools(
    tools: list[Any],
    temperature: float = 0.2,
    model: str | None = None,
) -> ChatOpenAI:
    """Returns a ChatOpenAI instance (via Groq) with tools bound if any are provided.

    Args:
        tools: List of LangChain tool objects to bind to the LLM.
        temperature: Controls randomness. Lower = more deterministic.
        model: The Groq model to use. Defaults to the LLM_MODEL env var or
               ``llama-3.3-70b-versatile``.

    Returns:
        A ChatOpenAI instance with tools bound (or plain if tools is empty).
    """
    llm = get_llm(temperature=temperature, model=model)
    if tools:
        return llm.bind_tools(tools)
    return llm
