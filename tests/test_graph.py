"""Tests for graph construction and conditional routing."""

from unittest.mock import patch
from src.graph import build_graph, should_continue, should_continue_after_tests


def _base_state(**overrides):
    """Return a minimal valid GraphState dict with optional overrides."""
    state = {
        "requirements": "test",
        "db_schema": "test",
        "server_code": "test",
        "review_feedback": [],
        "iterations": 1,
        "final_status": "approved",
        "output_dir": "./output",
        "test_results": "",
        "test_status": "",
    }
    state.update(overrides)
    return state


def test_should_continue_approved():
    """When no feedback exists, the graph should route to integration_node."""
    assert should_continue(_base_state()) == "integration_node"


def test_should_continue_with_feedback():
    """When feedback exists and iterations < max, loop back to developer."""
    state = _base_state(
        review_feedback=["Fix SQL injection"],
        iterations=1,
        final_status="",
    )
    assert should_continue(state) == "developer_node"


def test_should_continue_max_iterations():
    """When max iterations reached, route to integration_node regardless of feedback."""
    state = _base_state(
        review_feedback=["Still broken"],
        iterations=3,
        final_status="",
    )
    assert should_continue(state) == "integration_node"


def test_should_continue_after_tests_passed():
    """When test_status is 'passed', route to end."""
    assert should_continue_after_tests(_base_state(test_status="passed")) == "end"


def test_should_continue_after_tests_skipped():
    """When test_status is 'skipped', route to end."""
    assert should_continue_after_tests(_base_state(test_status="skipped")) == "end"


def test_should_continue_after_tests_failed():
    """When tests failed and iterations < max, loop back to developer."""
    state = _base_state(test_status="failed", iterations=1)
    assert should_continue_after_tests(state) == "developer_node"


def test_should_continue_after_tests_failed_max_iterations():
    """When tests failed and max iterations reached, route to end."""
    state = _base_state(test_status="failed", iterations=3)
    assert should_continue_after_tests(state) == "end"


def test_graph_compiles():
    """Verify the graph (now with 5 nodes) compiles without errors."""
    graph = build_graph()
    assert graph is not None
