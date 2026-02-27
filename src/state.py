"""Shared state object for the LangGraph workflow."""

from typing import TypedDict, Annotated
from operator import add


class GraphState(TypedDict):
    """The shared memory object passed between all nodes in the graph.
    
    Attributes:
        requirements: The user's high-level prompt describing the backend to build.
        db_schema: The generated PostgreSQL schema (CREATE TABLE statements).
        server_code: The generated Node.js/Express backend code.
        review_feedback: A list of critiques/errors found by the reviewer.
        iterations: Counter to prevent infinite correction loops.
        final_status: Whether the code was 'approved' or 'max_iterations_reached'.
    """
    requirements: str
    db_schema: str
    server_code: str
    review_feedback: Annotated[list[str], add]
    iterations: int
    final_status: str
    output_dir: str  # Path to the directory where generated files are written
