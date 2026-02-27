"""Streamlit web application for the Autonomous Backend Architect."""

import io
import os
import zipfile

from dotenv import load_dotenv


def _display_node_output(node_name: str, node_output: dict) -> None:
    """Render a single node's output using appropriate Streamlit widgets."""
    import streamlit as st

    if node_name == "architect_node":
        with st.status("🏗️ Architect — Designing Schema...", expanded=True):
            schema = node_output.get("db_schema", "")
            if schema:
                st.code(schema, language="sql")

    elif node_name == "developer_node":
        with st.status("💻 Developer — Generating Code...", expanded=True):
            iteration = node_output.get("iterations", 0)
            st.caption(f"Iteration: {iteration}")
            server_code = node_output.get("server_code", "")
            if server_code:
                from src.utils.code_parser import parse_code_blocks
                files = parse_code_blocks(server_code)
                for fname, content in files.items():
                    st.subheader(fname)
                    st.code(content, language="javascript")

    elif node_name == "reviewer_node":
        with st.status("🔍 Reviewer — Analyzing Code...", expanded=True):
            feedback = node_output.get("review_feedback", [])
            if not feedback:
                st.success("✅ Code Approved!")
            else:
                st.warning("⚠️ Issues Found")
                for i, item in enumerate(feedback, 1):
                    st.write(f"{i}. {item}")

    elif node_name == "integration_node":
        with st.status("📂 Integration — Writing Files...", expanded=True):
            out_dir = node_output.get("output_dir", "")
            st.write(f"Output directory: `{out_dir}`")
            if out_dir and os.path.isdir(out_dir):
                for root, _, fnames in os.walk(out_dir):
                    for fname in fnames:
                        fpath = os.path.join(root, fname)
                        rel = os.path.relpath(fpath, out_dir)
                        size = os.path.getsize(fpath)
                        st.write(f"• `{rel}` ({size} bytes)")

    elif node_name == "tdd_test_node":
        with st.status("🧪 TDD Tests — Running...", expanded=True):
            test_status = node_output.get("test_status", "")
            if test_status == "passed":
                st.write(f"✅ {test_status}")
            elif test_status == "failed":
                st.write(f"❌ {test_status}")
            else:
                st.write(f"⏭️ {test_status}" if test_status else "⏭️ skipped")
            test_results = node_output.get("test_results", "")
            if test_results:
                st.code(test_results, language="text")


def _show_final_summary(final_state: dict, output_dir: str) -> None:
    """Render the final summary and downloads sections."""
    import streamlit as st

    st.divider()
    st.subheader("📊 Final Summary")

    status = final_state.get("final_status", "unknown")
    iterations = final_state.get("iterations", 0)
    out_dir = final_state.get("output_dir", output_dir)
    test_status = final_state.get("test_status", "")

    if status == "approved":
        st.success(f"✅ Status: {status}")
    elif status == "pending":
        st.warning(f"⚠️ Status: {status}")
    else:
        st.error(f"❌ Status: {status}")

    st.write(f"**Total Iterations:** {iterations}")
    st.write(f"**Output Directory:** `{os.path.abspath(out_dir)}`")
    if test_status:
        st.write(f"**Test Status:** {test_status}")

    # Downloads section
    if out_dir and os.path.isdir(out_dir):
        st.divider()
        st.subheader("📥 Downloads")

        all_files = []
        for root, _, fnames in os.walk(out_dir):
            for fname in fnames:
                fpath = os.path.join(root, fname)
                rel = os.path.relpath(fpath, out_dir)
                all_files.append((rel, fpath))

        for rel, fpath in sorted(all_files):
            with open(fpath, "rb") as fh:
                file_bytes = fh.read()
            st.download_button(
                label=f"⬇️ {rel}",
                data=file_bytes,
                file_name=os.path.basename(fpath),
                key=f"dl_{rel}",
            )

        if all_files:
            zip_buf = io.BytesIO()
            with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED) as zf:
                for rel, fpath in all_files:
                    zf.write(fpath, rel)
            zip_buf.seek(0)
            st.download_button(
                label="📦 Download All as ZIP",
                data=zip_buf,
                file_name="backend_output.zip",
                mime="application/zip",
                key="dl_zip",
            )


def main_app() -> None:
    """Main Streamlit application logic."""
    import streamlit as st

    st.set_page_config(page_title="🏗️ Autonomous Backend Architect", layout="wide")

    # --- Sidebar ---
    with st.sidebar:
        st.header("⚙️ Configuration")
        openai_key = st.text_input("OpenAI API Key", type="password")
        if openai_key:
            os.environ["OPENAI_API_KEY"] = openai_key

        tavily_key = st.text_input("Tavily API Key (optional)", type="password")
        if tavily_key:
            os.environ["TAVILY_API_KEY"] = tavily_key

        output_dir = st.text_input("Output Directory", value="./output")

        if st.button("🗑️ Clear History"):
            st.session_state.clear()
            st.rerun()

        with st.expander("ℹ️ How to use"):
            st.markdown(
                "1. Enter your **OpenAI API Key** above (or set it in a `.env` file).\n"
                "2. Optionally enter a **Tavily API Key** for web search.\n"
                "3. Type your backend requirements in the main area.\n"
                "4. Click **🚀 Generate Backend** to start the pipeline.\n"
                "5. Watch each agent work in real-time.\n"
                "6. Download the generated files when done."
            )

    # --- Main area ---
    st.title("🏗️ Autonomous Backend Architect")
    st.write("Generate a complete, production-ready backend from a plain-English description.")

    prompt = st.text_area(
        "Backend Requirements",
        placeholder=(
            "Build a REST API for a library management system with users, "
            "books, and borrowing records..."
        ),
        height=150,
    )

    generate_clicked = st.button("🚀 Generate Backend")

    if generate_clicked:
        if not os.environ.get("OPENAI_API_KEY"):
            load_dotenv()
        if not os.environ.get("OPENAI_API_KEY"):
            st.error("❌ OpenAI API Key is required. Enter it in the sidebar or set OPENAI_API_KEY in your environment.")
            return
        if not prompt.strip():
            st.error("❌ Please enter your backend requirements.")
            return

        from src.graph import build_graph
        graph = build_graph()

        initial_state = {
            "requirements": prompt,
            "db_schema": "",
            "server_code": "",
            "review_feedback": [],
            "iterations": 0,
            "final_status": "pending",
            "output_dir": output_dir,
            "test_results": "",
            "test_status": "",
        }

        events: list[tuple[str, dict]] = []
        final_state: dict = dict(initial_state)

        try:
            for event in graph.stream(initial_state, {"recursion_limit": 25}):
                for node_name, node_output in event.items():
                    events.append((node_name, node_output))
                    final_state = {**final_state, **node_output}
                    _display_node_output(node_name, node_output)
        except Exception as exc:
            st.error(f"❌ Pipeline error: {exc}")
            return

        st.session_state.final_state = final_state
        st.session_state.events = events

        _show_final_summary(final_state, output_dir)

    elif "final_state" in st.session_state:
        # Re-display results from previous run without re-running the pipeline
        events = st.session_state.get("events", [])
        for node_name, node_output in events:
            _display_node_output(node_name, node_output)

        _show_final_summary(
            st.session_state.final_state,
            st.session_state.final_state.get("output_dir", output_dir),
        )


def main() -> None:
    """Launch the Streamlit app programmatically."""
    import sys
    from streamlit.web.cli import main as st_main

    sys.argv = ["streamlit", "run", os.path.abspath(__file__), "--server.headless", "True"]
    st_main()


if __name__ == "__main__":
    main_app()
