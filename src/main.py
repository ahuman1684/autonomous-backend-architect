"""Entry point for the Autonomous Backend Architect."""

import argparse
import os
from dotenv import load_dotenv
from src.graph import build_graph


def run(prompt: str, output_dir: str = "./output") -> dict:
    """Runs the full architect pipeline for a given prompt.
    
    Args:
        prompt: High-level description of the backend to build.
        output_dir: Directory where generated files will be written.
    
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
        "output_dir": output_dir,
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
    out_dir = final_state.get("output_dir", output_dir)
    print(f"   Status:     {status}")
    print(f"   Iterations: {iterations}")
    print(f"   Output dir: {os.path.abspath(out_dir)}")

    generated_files = []
    if os.path.isdir(out_dir):
        for root, _, fnames in os.walk(out_dir):
            for fname in fnames:
                rel = os.path.relpath(os.path.join(root, fname), out_dir)
                generated_files.append(rel)

    if generated_files:
        print("\n📁 Generated files:")
        for f in sorted(generated_files):
            print(f"   • {f}")

    if status == "approved":
        print("\n✅ Backend generated and approved!")
    else:
        remaining = final_state.get("review_feedback", [])
        print(f"\n⚠️  Completed with {len(remaining)} unresolved issue(s).")

    return final_state


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Autonomous Backend Architect")
    parser.add_argument(
        "prompt",
        nargs="*",
        help="High-level description of the backend to build",
    )
    parser.add_argument(
        "--output-dir",
        default="./output",
        help="Directory to write generated files (default: ./output)",
    )
    args = parser.parse_args()

    if args.prompt:
        prompt = " ".join(args.prompt)
    else:
        prompt = input("Enter your backend requirements: ")

    run(prompt, output_dir=args.output_dir)


if __name__ == "__main__":
    main()
