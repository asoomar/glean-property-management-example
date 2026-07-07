"""Glean Chat API — generate grounded answers using search results."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from typing import Any

from glean.api_client import Glean, models
from glean.api_client.models.chatrestrictionfilters import ChatRestrictionFilters

from config import get_settings
from search import search

logger = logging.getLogger(__name__)


def _extract_answer(response: Any) -> str:
    texts = []
    for message in getattr(response, "messages", None) or []:
        for fragment in getattr(message, "fragments", None) or []:
            if text := getattr(fragment, "text", None):
                texts.append(text)
    return "\n".join(texts).strip() if texts else (getattr(response, "text", None) or "").strip()


def _extract_sources(response: Any) -> list[dict]:
    sources = []
    seen: set[tuple[str | None, str | None]] = set()

    def add(doc: Any) -> None:
        if not doc:
            return
        key = (getattr(doc, "id", None), getattr(doc, "url", None))
        if key in seen:
            return
        seen.add(key)
        sources.append(
            {
                "document_id": getattr(doc, "id", None),
                "title": getattr(doc, "title", None),
                "url": getattr(doc, "url", None),
                "snippet": getattr(doc, "snippet", None),
            }
        )

    for message in getattr(response, "messages", None) or []:
        for fragment in getattr(message, "fragments", None) or []:
            citation = getattr(fragment, "citation", None)
            if citation:
                add(getattr(citation, "source_document", None) or getattr(citation, "sourceDocument", None))

    for citation in getattr(response, "citations", None) or []:
        add(getattr(citation, "source_document", None) or getattr(citation, "sourceDocument", None))

    return sources


def ask(question: str) -> dict:
    """Search → Chat → return answer with sources."""
    settings = get_settings()
    datasource = settings.glean_datasource
    hits = search(question)

    context = "No retrieved documents were found."
    if hits:
        parts = []
        for i, hit in enumerate(hits, 1):
            parts.append(
                f"[{i}] Title: {hit.get('title') or 'Unknown'}\n"
                f"URL: {hit.get('url') or 'N/A'}\n"
                f"Snippet: {hit.get('snippet') or 'N/A'}"
            )
        context = "\n\n".join(parts)

    prompt = (
        "You are an internal assistant for Northstar Residential Management.\n"
        "Answer using ONLY the retrieved documents below. Cite sources.\n\n"
        f"Retrieved documents (datasource: {datasource}):\n{context}\n\n"
        f"Question: {question}"
    )

    headers = {"X-Glean-ActAs": settings.glean_act_as} if settings.glean_act_as else None

    with Glean(
        api_token=settings.glean_client_api_token,
        server_url=settings.glean_server_url,
        timeout_ms=settings.glean_http_timeout_ms,
    ) as client:
        response = client.client.chat.create(
            messages=[{"fragments": [models.ChatMessageFragment(text=prompt)]}],
            inclusions=ChatRestrictionFilters(datasource_instances=[datasource]),
            timeout_millis=settings.glean_chat_timeout_ms,
            timeout_ms=settings.glean_http_timeout_ms,
            http_headers=headers,
        )

    answer = _extract_answer(response)
    sources = _extract_sources(response)
    if not sources:
        sources = hits

    return {
        "question": question,
        "answer": answer,
        "sources": sources,
        "search_hits": hits,
        "chat_id": getattr(response, "chat_id", None) or getattr(response, "chatId", None),
    }


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    parser = argparse.ArgumentParser(description="Ask a question via Glean Search + Chat.")
    parser.add_argument("question")
    args = parser.parse_args(argv)

    print(json.dumps(ask(args.question), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
