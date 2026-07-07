"""Glean Indexing API — ingest documents from documents/ into Glean."""

from __future__ import annotations

import json
import logging
import re
import sys
from pathlib import Path

from glean.api_client import Glean
from glean.api_client.models.contentdefinition import ContentDefinition
from glean.api_client.models.documentdefinition import DocumentDefinition
from glean.api_client.models.documentpermissionsdefinition import DocumentPermissionsDefinition

from config import get_settings

logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = {".txt", ".md", ".markdown"}
MANIFEST_FILE = "glean_index_manifest.json"


def to_glean_id(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]+", "", value) or "document"


def load_documents() -> list[dict]:
    """Load documents from glean_index_manifest.json (or scan documents/)."""
    settings = get_settings()
    docs_dir = settings.documents_path
    if not docs_dir.exists():
        return []

    manifest_path = docs_dir / MANIFEST_FILE
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text())
        datasource = manifest.get("datasource", settings.glean_datasource)
        object_type = manifest.get("object_type", settings.glean_object_type)
        documents = []
        for entry in manifest.get("documents", []):
            path = docs_dir / Path(entry["filename"]).name
            if not path.exists():
                continue
            body = path.read_text(encoding="utf-8").strip()
            if not body:
                continue
            documents.append(
                {
                    "id": to_glean_id(entry["id"]),
                    "title": entry["title"],
                    "body": body,
                    "view_url": entry["view_url"],
                    "datasource": datasource,
                    "object_type": object_type,
                    "mime_type": "text/markdown",
                }
            )
        return documents

    documents = []
    for path in sorted(docs_dir.iterdir()):
        if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue
        body = path.read_text(encoding="utf-8").strip()
        if body:
            documents.append(
                {
                    "id": to_glean_id(path.stem),
                    "title": path.stem.replace("_", " ").title(),
                    "body": body,
                    "view_url": f"{settings.glean_view_url_base.rstrip('/')}/{path.stem}",
                    "datasource": settings.glean_datasource,
                    "object_type": settings.glean_object_type,
                    "mime_type": "text/markdown",
                }
            )
    return documents


def index_documents() -> list[dict]:
    """Index all local documents via the Glean Indexing API."""
    settings = get_settings()
    documents = load_documents()
    if not documents:
        return []

    results = []
    with Glean(
        api_token=settings.glean_indexing_api_token,
        server_url=settings.glean_server_url,
        timeout_ms=settings.glean_http_timeout_ms,
    ) as client:
        for doc in documents:
            client.indexing.documents.add_or_update(
                document=DocumentDefinition(
                    datasource=doc["datasource"],
                    object_type=doc["object_type"],
                    id=doc["id"],
                    title=doc["title"],
                    view_url=doc["view_url"],
                    body=ContentDefinition(mime_type=doc["mime_type"], text_content=doc["body"]),
                    permissions=DocumentPermissionsDefinition(allow_anonymous_access=True),
                ),
                timeout_ms=settings.glean_http_timeout_ms,
            )
            results.append({"id": doc["id"], "title": doc["title"], "view_url": doc["view_url"], "status": "indexed"})
            logger.info("Indexed %s", doc["title"])

    return results


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    results = index_documents()
    if not results:
        logger.error("No documents to index. Add files to %s", get_settings().documents_path)
        return 1

    print(json.dumps(results, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
