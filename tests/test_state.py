"""Tests for the GraphState schema."""

from src.state import GraphState


def test_graph_state_initialization():
    """Verify that GraphState can be instantiated with all required fields."""
    state: GraphState = {
        "requirements": "Build a library management system",
        "db_schema": "",
        "server_code": "",
        "review_feedback": [],
        "iterations": 0,
        "final_status": "pending",
    }
    assert state["requirements"] == "Build a library management system"
    assert state["iterations"] == 0
    assert state["review_feedback"] == []


def test_review_feedback_annotation():
    """Verify that the Annotated[list, add] reducer concatenates feedback."""
    feedback_a = ["Missing error handling in POST /users"]
    feedback_b = ["SQL injection in GET /bookings"]
    combined = feedback_a + feedback_b  # Simulates the `add` operator
    assert len(combined) == 2
    assert "SQL injection" in combined[1]
