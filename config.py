"""Application configuration loaded from environment variables."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parent
load_dotenv(REPO_ROOT / ".env")


class Settings:
    glean_server_url: str = os.getenv("GLEAN_SERVER_URL", "https://support-lab-be.glean.com")
    glean_indexing_api_token: str = os.getenv("GLEAN_INDEXING_API_TOKEN", "")
    glean_search_api_token: str = os.getenv("GLEAN_SEARCH_API_TOKEN", "")
    glean_client_api_token: str = os.getenv("GLEAN_CLIENT_API_TOKEN", "")
    glean_datasource: str = os.getenv("GLEAN_DATASOURCE", "interviewds6")
    glean_object_type: str = os.getenv("GLEAN_OBJECT_TYPE", "Article")
    glean_view_url_base: str = os.getenv("GLEAN_VIEW_URL_BASE", "https://northstarpm.example.com/docs")
    glean_act_as: str | None = os.getenv("GLEAN_ACT_AS")
    glean_default_top_k: int = int(os.getenv("GLEAN_DEFAULT_TOP_K", "5"))
    glean_chat_timeout_ms: int = int(os.getenv("GLEAN_CHAT_TIMEOUT_MS", "120000"))
    glean_http_timeout_ms: int = int(os.getenv("GLEAN_HTTP_TIMEOUT_MS", "120000"))

    @property
    def documents_path(self) -> Path:
        return REPO_ROOT / "documents"


settings = Settings()


def get_settings() -> Settings:
    return settings
