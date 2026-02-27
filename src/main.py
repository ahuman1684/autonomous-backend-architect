"""Entry point for the Autonomous Backend Architect."""

import sys
from dotenv import load_dotenv
from src.graph import build_graph


def run(prompt: str) -> dict:
    """Runs the full architect pipeline for a given prompt.
    
    Args:
        prompt: High-level description of the backend to build.
    
    Returns:
        The final graph state containing schema, code, and status.
    """
    load_dotenv()

    print("🚀 Autonomous Backend Architect")
    print("=" * 60)
    print(f"📋 Prompt: {prompt}")
    print("=" * 60)

    graph = build_graph()

    initial_state = {
        "requirements": prompt,
        "db_schema": "",
        "server_code": "",
        "review_feedback": [],
        "iterations": 0,
        "final_status": "pending",
    }

    # Stream events for visibility
    final_state = None
    for event in graph.stream(initial_state, {"recursion_limit": 25}):
        # Each event is a dict with the node name as key
        for node_name, node_output in event.items():
            final_state = {**initial_state, **node_output} if final_state is None else {**final_state, **node_output}

    # Final summary
    print("\n" + "=" * 60)
    print("📦 FINAL OUTPUT SUMMARY")
    print("=" * 60)
    status = final_state.get("final_status", "unknown")
    iterations = final_state.get("iterations", 0)
    print(f"   Status:     {status}")
    print(f"   Iterations: {iterations}")
    print(f"   Schema:     {len(final_state.get('db_schema', ''))} chars")
    print(f"   Code:       {len(final_state.get('server_code', ''))} chars")

    if status == "approved":
        print("\n✅ Backend generated and approved!")
    else:
        remaining = final_state.get("review_feedback", [])
        print(f"\n⚠️  Completed with {len(remaining)} unresolved issue(s).")

    return final_state


def main():
    """CLI entry point."""
    if len(sys.argv) > 1:
        prompt = " ".join(sys.argv[1:])
    else:
        prompt = input("Enter your backend requirements: ")

    result = run(prompt)

    # Write output files
    with open("output_schema.sql", "w") as f:
        f.write(result.get("db_schema", ""))
    with open("output_server_code.md", "w") as f:
        f.write(result.get("server_code", ""))

    print("\n📁 Files written: output_schema.sql, output_server_code.md")


if __name__ == "__main__":
    main()
