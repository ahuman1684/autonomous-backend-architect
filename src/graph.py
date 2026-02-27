"""LangGraph StateGraph assembly — wires together all nodes and edges."""

from langgraph.graph import StateGraph, START, END
from src.state import GraphState
from src.nodes.architect import architect_node
from src.nodes.developer import developer_node
from src.nodes.reviewer import reviewer_node
from src.nodes.integration import integration_node
from src.nodes.tdd_test import tdd_test_node

MAX_ITERATIONS = 3


def should_continue(state: GraphState) -> str:
    """Conditional edge: decides whether to loop back or finish.
    
    Returns:
        'developer_node' if there are unresolved issues and iterations remain.
        'integration_node' if code is approved or max iterations reached.
    """
    # Code approved — no feedback
    if not state.get("review_feedback"):
        return "integration_node"

    # Max iterations reached — fail gracefully
    if state.get("iterations", 0) >= MAX_ITERATIONS:
        print(f"\n🛑 Max iterations ({MAX_ITERATIONS}) reached. Stopping.")
        return "integration_node"

    # Still have feedback to address
    print(f"\n🔄 Looping back to developer (iteration {state['iterations']}/{MAX_ITERATIONS})")
    return "developer_node"


def should_continue_after_tests(state: GraphState) -> str:
    """Conditional edge after TDD node: route to END or loop back to developer.

    Returns:
        'end' if tests passed, were skipped, or max iterations reached.
        'developer_node' if tests failed and iterations remain.
    """
    test_status = state.get("test_status", "")

    if test_status in ("passed", "skipped"):
        return "end"

    # Tests failed
    if state.get("iterations", 0) >= MAX_ITERATIONS:
        print(f"\n🛑 Max iterations ({MAX_ITERATIONS}) reached after test failure. Stopping.")
        return "end"

    print(f"\n🔄 Tests failed — looping back to developer (iteration {state.get('iterations', 0)}/{MAX_ITERATIONS})")
    return "developer_node"


def build_graph() -> StateGraph:
    """Constructs and compiles the LangGraph workflow.
    
    Returns:
        A compiled LangGraph StateGraph ready for invocation.
    """
    workflow = StateGraph(GraphState)

    # --- Add Nodes ---
    workflow.add_node("architect_node", architect_node)
    workflow.add_node("developer_node", developer_node)
    workflow.add_node("reviewer_node", reviewer_node)
    workflow.add_node("integration_node", integration_node)
    workflow.add_node("tdd_test_node", tdd_test_node)

    # --- Add Edges ---
    # START → Architect → Developer → Reviewer
    workflow.add_edge(START, "architect_node")
    workflow.add_edge("architect_node", "developer_node")
    workflow.add_edge("developer_node", "reviewer_node")

    # Conditional: Reviewer → Developer (loop) OR → Integration
    workflow.add_conditional_edges(
        "reviewer_node",
        should_continue,
        {
            "developer_node": "developer_node",
            "integration_node": "integration_node",
        },
    )

    # Integration → TDD → END or back to Developer
    workflow.add_edge("integration_node", "tdd_test_node")
    workflow.add_conditional_edges(
        "tdd_test_node",
        should_continue_after_tests,
        {"developer_node": "developer_node", "end": END},
    )

    return workflow.compile()
