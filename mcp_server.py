"""MCP server — exposes ask_glean as a single tool."""

from __future__ import annotations

from fastmcp import FastMCP
from httpx import ReadTimeout

from chat import ask

mcp = FastMCP("Northstar Property Management Chatbot")


def _format_response(result: dict) -> str:
    """Format answer and sources as plain text so clients surface citations."""
    if result.get("error"):
        return f"Error: {result['error']}"

    lines = [result.get("answer") or "(no answer)", "", "Sources:"]
    sources = result.get("sources") or result.get("search_hits") or []

    if not sources:
        lines.append("(none)")
    else:
        for i, source in enumerate(sources, 1):
            title = source.get("title") or "Unknown document"
            url = source.get("url") or ""
            snippet = source.get("snippet")
            lines.append(f"{i}. {title}")
            if url:
                lines.append(f"   {url}")
            if snippet:
                lines.append(f"   {snippet}")

    return "\n".join(lines)


@mcp.tool(name="ask_glean")
def ask_glean(question: str) -> str:
    """Ask a question about Northstar Property Management policy documents.

    Returns the grounded answer and a Sources section with document titles and URLs.
    Always present both the answer and every listed source to the user.
    """
    try:
        return _format_response(ask(question))
    except ReadTimeout:
        return _format_response(
            {
                "error": "Glean API timed out. Try a simpler question.",
                "answer": "",
                "sources": [],
            }
        )


if __name__ == "__main__":
    mcp.run(transport="stdio")
