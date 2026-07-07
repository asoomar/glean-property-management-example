"""Glean Search API — retrieve relevant snippets for a question."""

from __future__ import annotations

import logging

from glean.api_client import Glean
from glean.api_client.models.searchrequestoptions import SearchRequestOptions

from config import get_settings

logger = logging.getLogger(__name__)


def search(query: str, *, datasource: str | None = None, top_k: int | None = None) -> list[dict]:
    """Search the Glean index for relevant document snippets."""
    settings = get_settings()
    datasource = datasource or settings.glean_datasource
    top_k = top_k or settings.glean_default_top_k

    with Glean(
        api_token=settings.glean_search_api_token,
        server_url=settings.glean_server_url,
        timeout_ms=settings.glean_http_timeout_ms,
    ) as client:
        response = client.client.search.query(
            query=query,
            page_size=top_k,
            max_snippet_size=400,
            request_options=SearchRequestOptions(
                facet_bucket_size=20,
                datasource_filter=datasource,
            ),
            timeout_ms=settings.glean_http_timeout_ms,
        )

    hits = []
    for result in response.results or []:
        document = getattr(result, "document", None)
        snippet_text = getattr(result, "snippet", None)
        snippets = getattr(result, "snippets", None) or []
        if not snippet_text and snippets:
            parts = [getattr(s, "text", None) or getattr(s, "snippet", None) for s in snippets]
            snippet_text = " ".join(p for p in parts if p) or None

        hits.append(
            {
                "document_id": getattr(document, "id", None) if document else None,
                "title": getattr(result, "title", None),
                "url": getattr(result, "url", None) or getattr(result, "view_url", None),
                "snippet": snippet_text,
            }
        )

    logger.info("Search returned %d hit(s) for %r", len(hits), query)
    return hits
