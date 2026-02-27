"""Tests for src/nodes/integration.py"""

import os
import pytest
from src.nodes.integration import integration_node

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

SERVER_CODE = """\
```javascript
// server.js
const express = require('express');
const app = express();
app.listen(3000);
```

```javascript
// db/pool.js
const { Pool } = require('pg');
module.exports = new Pool();
```

```javascript
// routes/user.routes.js
const router = require('express').Router();
module.exports = router;
```
"""

DB_SCHEMA = "CREATE TABLE users (id SERIAL PRIMARY KEY, name TEXT NOT NULL);\n"


def _make_state(tmp_path, server_code=SERVER_CODE, db_schema=DB_SCHEMA):
    return {
        "requirements": "test",
        "server_code": server_code,
        "db_schema": db_schema,
        "review_feedback": [],
        "iterations": 1,
        "final_status": "approved",
        "output_dir": str(tmp_path),
    }


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_files_written_to_output_dir(tmp_path):
    """Extracted source files must be written under output_dir."""
    integration_node(_make_state(tmp_path))

    assert (tmp_path / "server.js").exists()
    assert (tmp_path / "db" / "pool.js").exists()
    assert (tmp_path / "routes" / "user.routes.js").exists()


def test_subdirectories_created_automatically(tmp_path):
    """Subdirectories like routes/ and db/ are created as needed."""
    integration_node(_make_state(tmp_path))

    assert (tmp_path / "db").is_dir()
    assert (tmp_path / "routes").is_dir()


def test_schema_sql_written(tmp_path):
    """schema.sql is written from db_schema."""
    integration_node(_make_state(tmp_path))

    schema_file = tmp_path / "schema.sql"
    assert schema_file.exists()
    assert "CREATE TABLE" in schema_file.read_text()


def test_env_example_created(tmp_path):
    """A .env.example file is created with the expected DATABASE_URL placeholder."""
    from src.nodes.integration import ENV_EXAMPLE_CONTENT

    integration_node(_make_state(tmp_path))

    env_file = tmp_path / ".env.example"
    assert env_file.exists()
    assert env_file.read_text() == ENV_EXAMPLE_CONTENT


def test_state_updated_with_output_dir(tmp_path):
    """The node returns output_dir in its state update."""
    result = integration_node(_make_state(tmp_path))

    assert result["output_dir"] == str(tmp_path)


def test_final_status_preserved(tmp_path):
    """final_status from the incoming state is preserved in the update."""
    result = integration_node(_make_state(tmp_path))

    assert result["final_status"] == "approved"


def test_empty_server_code_no_crash(tmp_path):
    """An empty server_code does not crash — only schema.sql and .env.example are written."""
    state = _make_state(tmp_path, server_code="", db_schema=DB_SCHEMA)
    integration_node(state)

    assert (tmp_path / "schema.sql").exists()
    assert (tmp_path / ".env.example").exists()


def test_empty_db_schema_no_schema_file(tmp_path):
    """When db_schema is empty, schema.sql is not written."""
    state = _make_state(tmp_path, db_schema="")
    integration_node(state)

    assert not (tmp_path / "schema.sql").exists()


def test_file_content_correct(tmp_path):
    """Written files must contain the expected content."""
    integration_node(_make_state(tmp_path))

    server_js = (tmp_path / "server.js").read_text()
    assert "express" in server_js
    # The comment line should be stripped by the parser
    assert "// server.js" not in server_js
