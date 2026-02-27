"""Architect Node: Generates the PostgreSQL database schema."""

import os

from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage

from src.prompts.architect_prompt import (
    ARCHITECT_SYSTEM_PROMPT,
    ARCHITECT_USER_PROMPT,
)
from src.state import GraphState
from src.tools import lookup_postgres_best_practices, search_postgres_docs
from src.utils.llm import get_llm, get_llm_with_tools

MAX_TOOL_ITERATIONS = 5


def _get_available_tools() -> list:
    """Return the list of tools available to the architect agent.

    lookup_postgres_best_practices is always included.
    search_postgres_docs is included only when a search API key is configured.
    """
    tools = [lookup_postgres_best_practices]
    if os.environ.get("TAVILY_API_KEY") or os.environ.get("SERPAPI_API_KEY"):
        tools.append(search_postgres_docs)
    return tools


def _run_tool_agent(llm_with_tools, messages: list, tools: list) -> str:
    """Run a tool-calling agentic loop and return the final text content.

    Args:
        llm_with_tools: LLM with tools bound.
        messages: Initial message list (SystemMessage + HumanMessage).
        tools: List of available tool objects.

    Returns:
        The final assistant response content as a string.
    """
    tool_map = {t.name: t for t in tools}
    current_messages = list(messages)

    for _ in range(MAX_TOOL_ITERATIONS):
        response = llm_with_tools.invoke(current_messages)
        current_messages.append(response)

        if not response.tool_calls:
            return response.content

        for tc in response.tool_calls:
            name = tc["name"]
            args = tc["args"]
            try:
                result = tool_map[name].invoke(args)
            except KeyError:
                result = f"Unknown tool: {name}"
            except Exception as exc:  # noqa: BLE001
                result = f"Tool error: {exc}"
            current_messages.append(
                ToolMessage(content=str(result), tool_call_id=tc["id"])
            )

    # Max iterations reached — ask plain LLM for final answer
    final_response = get_llm(temperature=0.2).invoke(current_messages)
    return final_response.content


def architect_node(state: GraphState) -> dict:
    """Takes user requirements and produces a PostgreSQL schema.
    
    Args:
        state: The current graph state with 'requirements' populated.
    
    Returns:
        A dict updating 'db_schema' in the state.
    """
    tools = _get_available_tools()

    messages = [
        SystemMessage(content=ARCHITECT_SYSTEM_PROMPT),
        HumanMessage(
            content=ARCHITECT_USER_PROMPT.format(requirements=state["requirements"])
        ),
    ]

    if tools:
        llm_with_tools = get_llm_with_tools(tools, temperature=0.2)
        raw_content = _run_tool_agent(llm_with_tools, messages, tools)
    else:
        response = get_llm(temperature=0.2).invoke(messages)
        raw_content = response.content

    # Extract the SQL from the response (strip markdown fences if present)
    schema = raw_content.strip()
    if schema.startswith("```sql"):
        schema = schema[6:]
    if schema.startswith("```"):
        schema = schema[3:]
    if schema.endswith("```"):
        schema = schema[:-3]

    print("\n" + "=" * 60)
    print("🏗️  ARCHITECT NODE — Schema Generated")
    print("=" * 60)
    print(schema[:500] + "..." if len(schema) > 500 else schema)

    return {"db_schema": schema.strip()}
