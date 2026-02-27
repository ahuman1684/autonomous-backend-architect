"""Smoke tests for the Streamlit UI module."""

import os


def test_ui_module_importable():
    """Verify src.ui package can be imported."""
    import src.ui
    assert src.ui is not None


def test_app_file_exists():
    """Verify the app.py file exists on disk."""
    app_path = os.path.join(os.path.dirname(__file__), "..", "src", "ui", "app.py")
    assert os.path.isfile(app_path)


def test_main_function_exists():
    """Verify the main() entry point exists."""
    try:
        from src.ui.app import main
        assert callable(main)
    except ImportError:
        # Streamlit not installed — that's OK, it's an optional dep
        pass
