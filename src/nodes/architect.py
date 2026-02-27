"""Architect Node: Generates the PostgreSQL database schema."""

from src.state import GraphState
from src.utils.llm import get_llm
from src.prompts.architect_prompt import (
    ARCHITECT_SYSTEM_PROMPT,
    ARCHITECT_USER_PROMPT,
)


def architect_node(state: GraphState) -> dict:
    """Takes user requirements and produces a PostgreSQL schema.
    
    Args:
        state: The current graph state with 'requirements' populated.
    
    Returns:
        A dict updating 'db_schema' in the state.
    """
    llm = get_llm(temperature=0.2)

    messages = [
        {"role": "system", "content": ARCHITECT_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": ARCHITECT_USER_PROMPT.format(
                requirements=state["requirements"]
            ),
        },
    ]

    response = llm.invoke(messages)

    # Extract the SQL from the response (strip markdown fences if present)
    schema = response.content.strip()
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
