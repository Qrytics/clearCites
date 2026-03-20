"""
data_pipeline/api_clients/semantic_scholar.py
Connector for the Semantic Scholar Academic Graph API.
"""

from __future__ import annotations

import os
from typing import Any

import httpx

_BASE_URL = "https://api.semanticscholar.org/graph/v1"
_DEFAULT_FIELDS = (
    "title,abstract,year,authors,citationCount,"
    "references,externalIds,fieldsOfStudy,publicationTypes"
)


class SemanticScholarClient:
    """Thin async wrapper around the Semantic Scholar API."""

    def __init__(self, api_key: str | None = None, timeout: float = 30.0) -> None:
        self._api_key = api_key or os.getenv("SEMANTIC_SCHOLAR_API_KEY", "")
        self._timeout = timeout

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _headers(self) -> dict[str, str]:
        headers: dict[str, str] = {"Accept": "application/json"}
        if self._api_key:
            headers["x-api-key"] = self._api_key
        return headers

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    async def get_paper(self, doi: str, fields: str = _DEFAULT_FIELDS) -> dict[str, Any]:
        """Fetch a single paper by DOI and return the raw API response."""
        url = f"{_BASE_URL}/paper/DOI:{doi}"
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.get(url, params={"fields": fields}, headers=self._headers())
            response.raise_for_status()
            return response.json()

    async def search_papers(
        self, query: str, limit: int = 20, fields: str = _DEFAULT_FIELDS
    ) -> list[dict[str, Any]]:
        """Full-text search for papers matching *query*."""
        url = f"{_BASE_URL}/paper/search"
        params = {"query": query, "limit": limit, "fields": fields}
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.get(url, params=params, headers=self._headers())
            response.raise_for_status()
            return response.json().get("data", [])
