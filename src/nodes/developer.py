"""Developer Node: Generates the Node.js/Express backend code."""

from src.state import GraphState
from src.utils.llm import get_llm
from src.prompts.developer_prompt import (
    DEVELOPER_SYSTEM_PROMPT,
    DEVELOPER_USER_PROMPT,
    FEEDBACK_SECTION_TEMPLATE,
)


def developer_node(state: GraphState) -> dict:
    """Takes the schema (and optional feedback) and produces backend code.
    
    Args:
        state: The current graph state with 'db_schema' and optionally 
               'review_feedback' populated.
    
    Returns:
        A dict updating 'server_code' and incrementing 'iterations'.
    """
    llm = get_llm(temperature=0.2)

    # Build the feedback section if there's prior review feedback
    feedback_section = ""
    if state.get("review_feedback"):
        feedback_items = "\n".join(
            f"- {item}" for item in state["review_feedback"]
        )
        feedback_section = FEEDBACK_SECTION_TEMPLATE.format(
            feedback=feedback_items
        )

    messages = [
        {"role": "system", "content": DEVELOPER_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": DEVELOPER_USER_PROMPT.format(
                requirements=state["requirements"],
                db_schema=state["db_schema"],
                feedback_section=feedback_section,
            ),
        },
    ]

    response = llm.invoke(messages)
    code = response.content.strip()

    iteration = state.get("iterations", 0) + 1

    print("\n" + "=" * 60)
    print(f"💻 DEVELOPER NODE — Code Generated (Iteration {iteration})")
    print("=" * 60)
    print(code[:500] + "..." if len(code) > 500 else code)

    return {
        "server_code": code,
        "iterations": iteration,
        # Clear previous feedback so it doesn't accumulate across iterations
        "review_feedback": [],
    }
