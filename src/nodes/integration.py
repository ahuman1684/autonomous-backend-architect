"""Integration node: parses generated code blocks and writes files to disk."""

import os
from src.state import GraphState
from src.utils.code_parser import parse_code_blocks

ENV_EXAMPLE_CONTENT = "DATABASE_URL=postgresql://user:password@localhost:5432/dbname\n"


def integration_node(state: GraphState) -> dict:
    """Parse server_code markdown, extract files, and write them to output_dir.

    Also writes schema.sql from db_schema and a .env.example file.

    Args:
        state: The current graph state.

    Returns:
        Partial state update with ``output_dir`` and ``final_status``.
    """
    output_dir: str = state.get("output_dir") or "./output"
    server_code: str = state.get("server_code", "")
    db_schema: str = state.get("db_schema", "")

    os.makedirs(output_dir, exist_ok=True)

    files_written: list[tuple[str, int]] = []

    # --- Parse and write generated source files ---
    parsed = parse_code_blocks(server_code)
    for relative_path, content in parsed.items():
        dest = os.path.join(output_dir, relative_path)
        parent = os.path.dirname(dest)
        if parent:
            os.makedirs(parent, exist_ok=True)
        with open(dest, "w", encoding="utf-8") as fh:
            fh.write(content)
        files_written.append((relative_path, len(content)))

    # --- Write schema.sql ---
    if db_schema:
        schema_path = os.path.join(output_dir, "schema.sql")
        with open(schema_path, "w", encoding="utf-8") as fh:
            fh.write(db_schema)
        files_written.append(("schema.sql", len(db_schema)))

    # --- Write .env.example ---
    env_path = os.path.join(output_dir, ".env.example")
    with open(env_path, "w", encoding="utf-8") as fh:
        fh.write(ENV_EXAMPLE_CONTENT)
    files_written.append((".env.example", len(ENV_EXAMPLE_CONTENT)))

    # --- Print summary ---
    print(f"\n📂 Integration complete — files written to '{output_dir}/':")
    for path, size in files_written:
        print(f"   ✅ {path}  ({size} bytes)")

    return {
        "output_dir": output_dir,
        "final_status": state.get("final_status", ""),
    }
