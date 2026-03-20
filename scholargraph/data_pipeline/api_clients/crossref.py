"""
data_pipeline/api_clients/crossref.py
Connector for the CrossRef REST API (metadata & funding info).
"""

from __future__ import annotations

from typing import Any

import httpx

_BASE_URL = "https://api.crossref.org/works"


class CrossRefClient:
    """Thin async wrapper around the CrossRef API."""

    def __init__(self, mailto: str = "", timeout: float = 30.0) -> None:
        # CrossRef Polite Pool: supply a mailto address so they can contact you.
        self._mailto = mailto
        self._timeout = timeout

    def _params(self, extra: dict[str, Any] | None = None) -> dict[str, Any]:
        params: dict[str, Any] = {}
        if self._mailto:
            params["mailto"] = self._mailto
        if extra:
            params.update(extra)
        return params

    async def get_paper(self, doi: str) -> dict[str, Any]:
        """Fetch CrossRef metadata for a paper identified by *doi*."""
        url = f"{_BASE_URL}/{doi}"
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.get(url, params=self._params())
            response.raise_for_status()
            return response.json().get("message", {})

    async def search_papers(self, query: str, rows: int = 20) -> list[dict[str, Any]]:
        """Bibliographic search against CrossRef."""
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.get(
                _BASE_URL,
                params=self._params({"query.bibliographic": query, "rows": rows}),
            )
            response.raise_for_status()
            return response.json().get("message", {}).get("items", [])
