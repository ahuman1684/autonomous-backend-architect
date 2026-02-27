"""Tests for src/utils/code_parser.py"""

import pytest
from src.utils.code_parser import parse_code_blocks

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

TYPICAL_SERVER_CODE = """\
```javascript
// package.json
{
  "name": "my-backend",
  "version": "1.0.0"
}
```

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

```javascript
// controllers/booking.controller.js
const pool = require('../db/pool');
module.exports = { list: async (req, res) => {} };
```
"""

# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_parse_typical_multi_file():
    """Parses a realistic multi-file LLM output into the correct file map."""
    result = parse_code_blocks(TYPICAL_SERVER_CODE)

    assert "package.json" in result
    assert "server.js" in result
    assert "db/pool.js" in result
    assert "routes/user.routes.js" in result
    assert "controllers/booking.controller.js" in result
    assert len(result) == 5


def test_comment_line_stripped():
    """The // filename comment must NOT appear in the extracted content."""
    result = parse_code_blocks(TYPICAL_SERVER_CODE)
    for filename, content in result.items():
        assert f"// {filename}" not in content, f"Comment line found in {filename}"


def test_nested_paths_preserved():
    """Nested paths like db/pool.js must be kept intact."""
    result = parse_code_blocks(TYPICAL_SERVER_CODE)
    assert "db/pool.js" in result
    assert "routes/user.routes.js" in result
    assert "controllers/booking.controller.js" in result


def test_package_json_content():
    """package.json content is parsed and contains expected JSON text."""
    result = parse_code_blocks(TYPICAL_SERVER_CODE)
    content = result["package.json"]
    assert '"name"' in content
    assert "// package.json" not in content


def test_filename_on_fence_tag():
    """Filename can appear in the fence tag instead of the first comment line."""
    code = """\
```javascript // utils.js
function helper() {}
module.exports = helper;
```
"""
    result = parse_code_blocks(code)
    assert "utils.js" in result
    assert "helper" in result["utils.js"]


def test_fallback_no_parseable_blocks():
    """When no filenames are found, fall back to server_code.md."""
    code = """\
```javascript
const x = 1;
```
```python
def foo(): pass
```
"""
    result = parse_code_blocks(code)
    assert "server_code.md" in result
    assert len(result) == 1
    assert "const x = 1;" in result["server_code.md"]


def test_empty_input():
    """Empty string returns an empty dict (no fallback needed)."""
    assert parse_code_blocks("") == {}


def test_whitespace_only_input():
    """Whitespace-only string returns an empty dict."""
    assert parse_code_blocks("   \n\t\n  ") == {}


def test_block_without_filename_skipped():
    """A code block with no filename comment is skipped."""
    code = """\
```javascript
const a = 1;
```

```javascript
// server.js
const app = require('express')();
```
"""
    result = parse_code_blocks(code)
    assert list(result.keys()) == ["server.js"]


def test_json_language_tag_with_comment():
    """package.json declared in a ```json block with a comment is parsed."""
    code = """\
```json
// package.json
{
  "name": "app",
  "version": "1.0.0"
}
```
"""
    result = parse_code_blocks(code)
    assert "package.json" in result
    assert '"name"' in result["package.json"]
