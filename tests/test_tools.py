"""Tests for src/tools/postgres_reference.py and src/tools/search.py."""

import os
import pytest

from src.tools.postgres_reference import (
    POSTGRES_BEST_PRACTICES,
    lookup_postgres_best_practices,
)
from src.tools.search import search_postgres_docs


# ---------------------------------------------------------------------------
# postgres_reference tests
# ---------------------------------------------------------------------------

EXPECTED_TOPICS = ["uuid", "timestamps", "indexing", "constraints", "performance", "security", "naming"]


@pytest.mark.parametrize("topic", EXPECTED_TOPICS)
def test_direct_topic_match(topic):
    """Each of the 7 topics returns its dedicated entry."""
    result = lookup_postgres_best_practices.invoke({"topic": topic})
    assert result == POSTGRES_BEST_PRACTICES[topic]


@pytest.mark.parametrize("topic", EXPECTED_TOPICS)
def test_case_insensitivity(topic):
    """Topic lookup is case-insensitive."""
    result = lookup_postgres_best_practices.invoke({"topic": topic.upper()})
    assert result == POSTGRES_BEST_PRACTICES[topic]


def test_fuzzy_match_substring():
    """A topic containing a key as a substring returns the matching entry."""
    result = lookup_postgres_best_practices.invoke({"topic": "uuid primary keys"})
    assert result == POSTGRES_BEST_PRACTICES["uuid"]


def test_fuzzy_match_key_contains_topic():
    """A topic that is a substring of a key still matches."""
    result = lookup_postgres_best_practices.invoke({"topic": "index"})
    assert result == POSTGRES_BEST_PRACTICES["indexing"]


def test_unknown_topic_returns_all_practices():
    """An unknown topic returns all practices with 'No exact match' prefix."""
    result = lookup_postgres_best_practices.invoke({"topic": "zzzunknown"})
    assert result.startswith("No exact match")
    for topic in EXPECTED_TOPICS:
        assert topic.upper() in result


def test_all_expected_topics_in_dict():
    """POSTGRES_BEST_PRACTICES contains exactly the 7 required keys."""
    assert set(EXPECTED_TOPICS) == set(POSTGRES_BEST_PRACTICES.keys())


# ---------------------------------------------------------------------------
# search tool tests
# ---------------------------------------------------------------------------

def test_search_graceful_no_keys(monkeypatch):
    """When no API keys are set, search_postgres_docs returns a graceful message."""
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)
    monkeypatch.delenv("SERPAPI_API_KEY", raising=False)
    result = search_postgres_docs.invoke({"query": "PostgreSQL UUID"})
    assert "No search API key configured" in result
    assert "Proceeding with internal knowledge only" in result


# ---------------------------------------------------------------------------
# Tool name attribute tests
# ---------------------------------------------------------------------------

def test_lookup_tool_name():
    assert lookup_postgres_best_practices.name == "lookup_postgres_best_practices"


def test_search_tool_name():
    assert search_postgres_docs.name == "search_postgres_docs"
