"""Tests for graph construction and conditional routing."""

from unittest.mock import patch
from src.graph import build_graph, should_continue


def test_should_continue_approved():
    """When no feedback exists, the graph should route to END."""
    state = {
        "requirements": "test",
        "db_schema": "test",
        "server_code": "test",
        "review_feedback": [],
        "iterations": 1,
        "final_status": "approved",
    }
    assert should_continue(state) == "end"


def test_should_continue_with_feedback():
    """When feedback exists and iterations < max, loop back to developer."""
    state = {
        "requirements": "test",
        "db_schema": "test",
        "server_code": "test",
        "review_feedback": ["Fix SQL injection"],
        "iterations": 1,
        "final_status": "",
    }
    assert should_continue(state) == "developer_node"


def test_should_continue_max_iterations():
    """When max iterations reached, route to END regardless of feedback."""
    state = {
        "requirements": "test",
        "db_schema": "test",
        "server_code": "test",
        "review_feedback": ["Still broken"],
        "iterations": 3,
        "final_status": "",
    }
    assert should_continue(state) == "end"


def test_graph_compiles():
    """Verify the graph compiles without errors."""
    graph = build_graph()
    assert graph is not None
