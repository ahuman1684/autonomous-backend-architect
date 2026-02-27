"""Reviewer Node: Inspects the generated code for bugs and vulnerabilities."""

from src.state import GraphState
from src.utils.llm import get_llm
from src.prompts.reviewer_prompt import (
    REVIEWER_SYSTEM_PROMPT,
    REVIEWER_USER_PROMPT,
)


def reviewer_node(state: GraphState) -> dict:
    """Reviews the server code against the schema and returns feedback.
    
    Args:
        state: The current graph state with 'db_schema' and 'server_code'.
    
    Returns:
        A dict updating 'review_feedback' and optionally 'final_status'.
    """
    llm = get_llm(temperature=0.1)  # Lower temp for more consistent reviews

    messages = [
        {"role": "system", "content": REVIEWER_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": REVIEWER_USER_PROMPT.format(
                db_schema=state["db_schema"],
                server_code=state["server_code"],
            ),
        },
    ]

    response = llm.invoke(messages)
    review = response.content.strip()

    print("\n" + "=" * 60)
    print("🔍 REVIEWER NODE — Review Complete")
    print("=" * 60)
    print(review)

    # Parse the review: check if code was approved
    if review.strip().upper() == "APPROVED":
        print("\n✅ Code APPROVED by reviewer!")
        return {
            "review_feedback": [],
            "final_status": "approved",
        }

    # Parse numbered feedback items
    feedback_items = []
    for line in review.split("\n"):
        line = line.strip()
        if line and (line[0].isdigit() or line.startswith("-")):
            # Remove leading number/bullet
            cleaned = line.lstrip("0123456789.-) ").strip()
            if cleaned:
                feedback_items.append(cleaned)

    # If parsing found no items but it's not APPROVED, use the whole response
    if not feedback_items:
        feedback_items = [review]

    print(f"\n⚠️  Found {len(feedback_items)} issue(s) to fix.")

    return {"review_feedback": feedback_items}
