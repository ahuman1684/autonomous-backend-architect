"""Parses labeled fenced code blocks from LLM markdown output into file mappings."""

import re


def parse_code_blocks(server_code: str) -> dict[str, str]:
    """Extract filename → content pairs from labeled markdown code blocks.

    The developer node wraps each file like:
        ```javascript
        // server.js
        ...
        ```

    or with the filename on the fence tag:
        ```javascript // server.js
        ...
        ```

    Args:
        server_code: Raw markdown string produced by the developer node.

    Returns:
        A dict mapping relative file paths to their (stripped) content.
        Falls back to ``{"server_code.md": server_code}`` if nothing is parsed.
    """
    if not server_code or not server_code.strip():
        return {}

    files: dict[str, str] = {}

    # Match fenced code blocks: opening fence optionally has a language/filename tag
    block_pattern = re.compile(
        r"```(?P<tag>[^\n]*)\n(?P<body>.*?)```",
        re.DOTALL,
    )

    # Filename patterns inside block body (first line comment)
    comment_filename_re = re.compile(
        r"^[ \t]*(?://|#)\s*(?P<fname>\S+\.\S+)\s*\n",
    )

    for match in block_pattern.finditer(server_code):
        tag = match.group("tag").strip()
        body = match.group("body")

        filename = None

        # 1. Check if filename is embedded in the fence tag, e.g. "javascript // server.js"
        tag_inline_re = re.search(r"(?://|#)\s*(\S+\.\S+)", tag)
        if tag_inline_re:
            filename = tag_inline_re.group(1)

        # 2. Check first line of the body for a comment-style filename
        if filename is None:
            cm = comment_filename_re.match(body)
            if cm:
                filename = cm.group("fname")
                # Strip the comment line from the content
                body = body[cm.end():]

        if filename is None:
            # No filename found — skip this block
            continue

        # Strip leading/trailing blank lines from the content
        content = body.strip("\n")
        files[filename] = content

    if not files:
        # Fallback: preserve everything so nothing is lost
        return {"server_code.md": server_code}

    return files
