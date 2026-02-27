"""Tests for architect node tool integration (_get_available_tools)."""

import pytest

from src.nodes.architect import _get_available_tools
from src.tools.postgres_reference import lookup_postgres_best_practices
from src.tools.search import search_postgres_docs


def test_always_includes_lookup_tool():
    """_get_available_tools always includes lookup_postgres_best_practices."""
    tools = _get_available_tools()
    names = [t.name for t in tools]
    assert "lookup_postgres_best_practices" in names


def test_includes_search_when_tavily_key_set(monkeypatch):
    """_get_available_tools includes search_postgres_docs when TAVILY_API_KEY is set."""
    monkeypatch.setenv("TAVILY_API_KEY", "tvly-test-key")
    monkeypatch.delenv("SERPAPI_API_KEY", raising=False)
    tools = _get_available_tools()
    names = [t.name for t in tools]
    assert "search_postgres_docs" in names


def test_includes_search_when_serpapi_key_set(monkeypatch):
    """_get_available_tools includes search_postgres_docs when SERPAPI_API_KEY is set."""
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)
    monkeypatch.setenv("SERPAPI_API_KEY", "serpapi-test-key")
    tools = _get_available_tools()
    names = [t.name for t in tools]
    assert "search_postgres_docs" in names


def test_excludes_search_when_no_keys_set(monkeypatch):
    """_get_available_tools excludes search_postgres_docs when no API keys are set."""
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)
    monkeypatch.delenv("SERPAPI_API_KEY", raising=False)
    tools = _get_available_tools()
    names = [t.name for t in tools]
    assert "search_postgres_docs" not in names
