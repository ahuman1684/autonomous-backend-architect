"""Web search tool for the latest PostgreSQL documentation."""

import os

from langchain_core.tools import tool


@tool
def search_postgres_docs(query: str) -> str:
    """Search the web for the latest PostgreSQL documentation and best practices.

    Tries Tavily first (if TAVILY_API_KEY is set), then falls back to SerpAPI
    (if SERPAPI_API_KEY is set). If neither key is available, returns a graceful
    message so the agent can proceed with internal knowledge.

    Args:
        query: The search query, e.g. 'PostgreSQL UUID primary key best practices'.

    Returns:
        Formatted search results as a string, or a graceful fallback message.
    """
    tavily_key = os.environ.get("TAVILY_API_KEY")
    serpapi_key = os.environ.get("SERPAPI_API_KEY")

    if tavily_key:
        try:
            from langchain_community.tools.tavily_search import TavilySearchResults

            search = TavilySearchResults(max_results=5, tavily_api_key=tavily_key)
            results = search.invoke(query)
            if isinstance(results, list):
                return "\n\n".join(
                    f"[{r.get('url', '')}]\n{r.get('content', '')}" for r in results
                )
            return str(results)
        except Exception:  # noqa: BLE001
            pass  # fall through to SerpAPI

    if serpapi_key:
        try:
            from langchain_community.utilities import SerpAPIWrapper

            search = SerpAPIWrapper(serpapi_api_key=serpapi_key)
            return search.run(query)
        except Exception:  # noqa: BLE001
            pass  # fall through to graceful message

    return (
        "No search API key configured (TAVILY_API_KEY or SERPAPI_API_KEY). "
        "Proceeding with internal knowledge only."
    )
