"""Tests for the TDD Test Node."""

import json
import os
import subprocess
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from src.nodes.tdd_test import tdd_test_node, _patch_package_json


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_state(output_dir: str, **overrides) -> dict:
    state = {
        "requirements": "test",
        "db_schema": "CREATE TABLE users (id SERIAL PRIMARY KEY);",
        "server_code": "",
        "review_feedback": [],
        "iterations": 1,
        "final_status": "",
        "output_dir": output_dir,
        "test_results": "",
        "test_status": "",
    }
    state.update(overrides)
    return state


def _write_minimal_package_json(directory: str) -> str:
    pkg = {"name": "test-app", "scripts": {}, "dependencies": {}}
    path = os.path.join(directory, "package.json")
    with open(path, "w") as fh:
        json.dump(pkg, fh)
    return path


# ---------------------------------------------------------------------------
# Tests: edge cases that skip without calling LLM
# ---------------------------------------------------------------------------

def test_skipped_when_output_dir_missing():
    """Node should return test_status='skipped' when output_dir does not exist."""
    state = _make_state("/nonexistent/path/xyz123")
    result = tdd_test_node(state)
    assert result["test_status"] == "skipped"


def test_skipped_when_no_package_json(tmp_path):
    """Node should return test_status='skipped' when no package.json is found."""
    state = _make_state(str(tmp_path))
    result = tdd_test_node(state)
    assert result["test_status"] == "skipped"


# ---------------------------------------------------------------------------
# Tests: _patch_package_json utility
# ---------------------------------------------------------------------------

def test_patch_package_json_adds_test_script(tmp_path):
    pkg_path = str(tmp_path / "package.json")
    with open(pkg_path, "w") as fh:
        json.dump({"name": "app", "scripts": {}}, fh)

    _patch_package_json(pkg_path)

    with open(pkg_path) as fh:
        pkg = json.load(fh)

    assert pkg["scripts"]["test"] == "jest --forceExit --detectOpenHandles"


def test_patch_package_json_adds_dev_dependencies(tmp_path):
    pkg_path = str(tmp_path / "package.json")
    with open(pkg_path, "w") as fh:
        json.dump({"name": "app"}, fh)

    _patch_package_json(pkg_path)

    with open(pkg_path) as fh:
        pkg = json.load(fh)

    assert "jest" in pkg["devDependencies"]
    assert "supertest" in pkg["devDependencies"]


def test_patch_package_json_idempotent(tmp_path):
    pkg_path = str(tmp_path / "package.json")
    with open(pkg_path, "w") as fh:
        json.dump({
            "name": "app",
            "scripts": {"test": "jest --forceExit --detectOpenHandles"},
            "devDependencies": {"jest": "^29.0.0", "supertest": "^6.0.0"},
        }, fh)

    _patch_package_json(pkg_path)

    with open(pkg_path) as fh:
        pkg = json.load(fh)

    # Values must not be overridden
    assert pkg["devDependencies"]["jest"] == "^29.0.0"
    assert pkg["devDependencies"]["supertest"] == "^6.0.0"


# ---------------------------------------------------------------------------
# Tests: subprocess-level behaviour (LLM is mocked)
# ---------------------------------------------------------------------------

def _mock_llm_response(content: str = ""):
    """Return a mock LLM that produces *content* when invoked."""
    mock_llm = MagicMock()
    mock_response = MagicMock()
    mock_response.content = content
    mock_llm.invoke.return_value = mock_response
    return mock_llm


@patch("src.nodes.tdd_test.get_llm")
@patch("src.nodes.tdd_test.subprocess.run")
def test_passing_tests_return_passed_status(mock_run, mock_get_llm, tmp_path):
    """When npm test exits 0, node returns test_status='passed'."""
    _write_minimal_package_json(str(tmp_path))
    mock_get_llm.return_value = _mock_llm_response()

    # npm install succeeds, npm test succeeds
    mock_run.side_effect = [
        MagicMock(returncode=0, stdout="", stderr=""),       # npm install
        MagicMock(returncode=0, stdout="Tests: 3 passed", stderr=""),  # npm test
    ]

    result = tdd_test_node(_make_state(str(tmp_path)))
    assert result["test_status"] == "passed"
    assert result["final_status"] == "approved"


@patch("src.nodes.tdd_test.get_llm")
@patch("src.nodes.tdd_test.subprocess.run")
def test_failing_tests_return_failed_status_with_feedback(mock_run, mock_get_llm, tmp_path):
    """When npm test exits non-zero, node returns test_status='failed' with feedback."""
    _write_minimal_package_json(str(tmp_path))
    mock_get_llm.return_value = _mock_llm_response()

    mock_run.side_effect = [
        MagicMock(returncode=0, stdout="", stderr=""),          # npm install
        MagicMock(returncode=1, stdout="FAIL __tests__/users.test.js", stderr="Error"),
    ]

    result = tdd_test_node(_make_state(str(tmp_path)))
    assert result["test_status"] == "failed"
    assert len(result["review_feedback"]) > 0
    assert result["review_feedback"][0].startswith("[TEST FAILURE]")


@patch("src.nodes.tdd_test.get_llm")
@patch("src.nodes.tdd_test.subprocess.run")
def test_npm_not_found_returns_skipped(mock_run, mock_get_llm, tmp_path):
    """FileNotFoundError from subprocess (npm not installed) → test_status='skipped'."""
    _write_minimal_package_json(str(tmp_path))
    mock_get_llm.return_value = _mock_llm_response()

    mock_run.side_effect = FileNotFoundError("npm not found")

    result = tdd_test_node(_make_state(str(tmp_path)))
    assert result["test_status"] == "skipped"


@patch("src.nodes.tdd_test.get_llm")
@patch("src.nodes.tdd_test.subprocess.run")
def test_timeout_on_npm_test_returns_failed(mock_run, mock_get_llm, tmp_path):
    """TimeoutExpired on npm test → test_status='failed'."""
    _write_minimal_package_json(str(tmp_path))
    mock_get_llm.return_value = _mock_llm_response()

    # install succeeds, test times out
    mock_run.side_effect = [
        MagicMock(returncode=0, stdout="", stderr=""),
        subprocess.TimeoutExpired(cmd="npm test", timeout=120),
    ]

    result = tdd_test_node(_make_state(str(tmp_path)))
    assert result["test_status"] == "failed"


@patch("src.nodes.tdd_test.get_llm")
@patch("src.nodes.tdd_test.subprocess.run")
def test_npm_install_failure_returns_skipped(mock_run, mock_get_llm, tmp_path):
    """Non-zero returncode from npm install → test_status='skipped'."""
    _write_minimal_package_json(str(tmp_path))
    mock_get_llm.return_value = _mock_llm_response()

    mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="install error")

    result = tdd_test_node(_make_state(str(tmp_path)))
    assert result["test_status"] == "skipped"
