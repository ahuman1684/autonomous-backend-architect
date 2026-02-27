"""TDD Test Node: generates Jest tests, runs them, and feeds errors back."""

import json
import os
import subprocess

from src.state import GraphState
from src.utils.code_parser import parse_code_blocks
from src.utils.llm import get_llm
from src.prompts.tdd_prompt import TDD_SYSTEM_PROMPT, TDD_USER_PROMPT


def _list_files(directory: str) -> list[str]:
    """Return relative paths of all files under *directory*."""
    result = []
    for root, _, fnames in os.walk(directory):
        for fname in fnames:
            rel = os.path.relpath(os.path.join(root, fname), directory)
            result.append(rel)
    return sorted(result)


def _read_js_json_files(directory: str, file_list: list[str]) -> str:
    """Read and concatenate .js / .json files for the LLM prompt."""
    parts: list[str] = []
    for rel in file_list:
        if rel.endswith(".js") or rel.endswith(".json"):
            full = os.path.join(directory, rel)
            try:
                with open(full, encoding="utf-8") as fh:
                    content = fh.read()
                parts.append(f"// {rel}\n{content}")
            except OSError:
                pass
    return "\n\n".join(parts)


def _patch_package_json(pkg_path: str) -> None:
    """Ensure package.json has jest/supertest devDeps and a test script."""
    with open(pkg_path, encoding="utf-8") as fh:
        pkg = json.load(fh)

    changed = False

    scripts = pkg.setdefault("scripts", {})
    if scripts.get("test") != "jest --forceExit --detectOpenHandles":
        scripts["test"] = "jest --forceExit --detectOpenHandles"
        changed = True

    dev_deps = pkg.setdefault("devDependencies", {})
    for dep in ("jest", "supertest"):
        if dep not in dev_deps:
            dev_deps[dep] = "*"
            changed = True

    if changed:
        with open(pkg_path, "w", encoding="utf-8") as fh:
            json.dump(pkg, fh, indent=2)
            fh.write("\n")


def _npm_not_found_skip() -> dict:
    """Return a skipped result when npm is not available."""
    msg = "npm not found — skipping tests."
    print(f"\n⚠️  TDD node: {msg}")
    return {"test_status": "skipped", "test_results": msg}


def tdd_test_node(state: GraphState) -> dict:
    """Generate Jest tests, execute them, and return results or feedback."""
    output_dir: str = state.get("output_dir") or "./output"

    # --- Guard: output dir must exist ---
    if not os.path.isdir(output_dir):
        print("\n⚠️  TDD node: output_dir does not exist — skipping tests.")
        return {
            "test_status": "skipped",
            "test_results": "Output directory not found.",
            "final_status": state.get("final_status", ""),
        }

    file_list = _list_files(output_dir)

    # --- Guard: package.json must exist ---
    pkg_path = os.path.join(output_dir, "package.json")
    if "package.json" not in file_list:
        print("\n⚠️  TDD node: no package.json found — skipping tests.")
        return {
            "test_status": "skipped",
            "test_results": "No package.json found in output directory.",
            "final_status": state.get("final_status", ""),
        }

    # --- Generate test files via LLM ---
    server_code_content = _read_js_json_files(output_dir, file_list)
    file_listing_str = "\n".join(f"  - {f}" for f in file_list)

    llm = get_llm(temperature=0.1)
    messages = [
        {"role": "system", "content": TDD_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": TDD_USER_PROMPT.format(
                db_schema=state.get("db_schema", ""),
                server_code=server_code_content,
                file_listing=file_listing_str,
            ),
        },
    ]
    response = llm.invoke(messages)
    generated = response.content.strip()

    # Write test files to output_dir (parse_code_blocks handles subdirs)
    parsed = parse_code_blocks(generated)
    for relative_path, content in parsed.items():
        dest = os.path.join(output_dir, relative_path)
        parent = os.path.dirname(dest)
        if parent:
            os.makedirs(parent, exist_ok=True)
        with open(dest, "w", encoding="utf-8") as fh:
            fh.write(content)

    # Ensure package.json has jest + supertest + test script
    _patch_package_json(pkg_path)

    print(f"\n🧪 TDD node — test files written, running npm install + npm test …")

    # --- npm install ---
    try:
        install_result = subprocess.run(
            ["npm", "install"],
            capture_output=True,
            text=True,
            timeout=120,
            cwd=output_dir,
        )
    except FileNotFoundError:
        return {**_npm_not_found_skip(), "final_status": state.get("final_status", "")}
    except subprocess.TimeoutExpired:
        msg = "npm install timed out — skipping tests."
        print(f"\n⚠️  TDD node: {msg}")
        return {
            "test_status": "skipped",
            "test_results": msg,
            "final_status": state.get("final_status", ""),
        }

    if install_result.returncode != 0:
        msg = f"npm install failed:\n{install_result.stderr}"
        print(f"\n⚠️  TDD node: npm install failed — skipping tests.")
        return {
            "test_status": "skipped",
            "test_results": msg,
            "final_status": state.get("final_status", ""),
        }

    # --- npm test ---
    try:
        test_result = subprocess.run(
            ["npm", "test"],
            capture_output=True,
            text=True,
            timeout=120,
            cwd=output_dir,
        )
    except FileNotFoundError:
        return {**_npm_not_found_skip(), "final_status": state.get("final_status", "")}
    except subprocess.TimeoutExpired:
        msg = "npm test timed out after 120 seconds."
        print(f"\n⚠️  TDD node: {msg}")
        return {
            "test_status": "failed",
            "test_results": msg,
            "review_feedback": [f"[TEST FAILURE] {msg}"],
        }

    combined_output = (test_result.stdout or "") + (test_result.stderr or "")

    if test_result.returncode == 0:
        print("\n✅ TDD node — all tests passed!")
        return {
            "test_status": "passed",
            "test_results": test_result.stdout,
            "final_status": "approved",
        }

    # Tests failed — extract errors and feed back to developer
    print("\n❌ TDD node — tests failed. Feeding errors back to developer.")
    error_feedback = f"[TEST FAILURE] Jest test failures:\n{combined_output}"
    return {
        "test_status": "failed",
        "test_results": combined_output,
        "review_feedback": [error_feedback],
    }
