"""
Thin async client for the OpenAlex API (https://api.openalex.org).

Polite use: pass mailto= on every request (see https://docs.openalex.org/how-to-use/api).

Retries (429 / 502 / 503) and backoff are handled in :mod:`openalex_http` (see ``OPENALEX_*`` env vars there).
"""

from __future__ import annotations

import asyncio
import os
import re
from typing import Any
from urllib.parse import quote

import httpx

from .openalex_http import openalex_get_json

_BASE = "https://api.openalex.org"


def openalex_short_id_from_url(url: str) -> str:
    """Extract W123… or A123… from an OpenAlex URL."""
    if not url:
        return ""
    url = url.rstrip("/")
    return url.split("/")[-1]


def normalize_work_selector(selector: str) -> str:
    """
    Turn user / UI input into an OpenAlex *works* path segment.
    Accepts: W2741809807, https://openalex.org/W2741809807, DOI string 10.1038/…
    """
    s = selector.strip()
    if not s:
        return s
    if s.startswith("http"):
        return openalex_short_id_from_url(s)
    m = re.fullmatch(r"(W)(\d+)", s, re.I)
    if m:
        return "W" + m.group(2)
    if s.lower().startswith("doi:"):
        s = s[4:].strip()
    if re.match(r"10\.\d+", s):
        return f"https://doi.org/{s}"
    return s


class OpenAlexClient:
    def __init__(self, mailto: str | None = None, timeout: float = 60.0) -> None:
        self._mailto = (mailto or os.getenv("OPENALEX_MAILTO") or "").strip()
        self._timeout = timeout

    def _params(self, extra: dict[str, Any] | None = None) -> dict[str, Any]:
        p: dict[str, Any] = {}
        if self._mailto:
            p["mailto"] = self._mailto
        if extra:
            p.update(extra)
        return p

    async def search_works(
        self,
        query: str,
        *,
        per_page: int = 15,
        page: int = 1,
    ) -> dict[str, Any]:
        return await self.search_works_filtered(
            query,
            per_page=per_page,
            page=page,
        )

    async def search_works_filtered(
        self,
        query: str,
        *,
        per_page: int = 25,
        page: int = 1,
        year_from: str | None = None,
        year_to: str | None = None,
        work_type: str | None = None,
        min_citations: int | None = None,
        is_oa: bool | None = None,
        has_abstract: bool | None = None,
        sort: str | None = None,
    ) -> dict[str, Any]:
        filters: list[str] = []
        if year_from:
            filters.append(f"from_publication_date:{year_from}-01-01")
        if year_to:
            filters.append(f"to_publication_date:{year_to}-12-31")
        if work_type:
            filters.append(f"type:{work_type}")
        if min_citations is not None and min_citations > 0:
            filters.append(f"cited_by_count:>{min_citations - 1}")
        if is_oa:
            filters.append("is_oa:true")
        if has_abstract:
            filters.append("has_abstract:true")

        params: dict[str, Any] = {
            "search": query,
            "per_page": per_page,
            "page": page,
        }
        if filters:
            params["filter"] = ",".join(filters)
        if sort:
            params["sort"] = sort

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            raw = await openalex_get_json(client, f"{_BASE}/works", self._params(params))
            return raw or {}

    async def search_catalog(
        self,
        catalog: str,
        query: str,
        *,
        per_page: int = 25,
        page: int = 1,
        sort: str | None = None,
    ) -> dict[str, Any]:
        """Search authors, institutions, or sources (OpenAlex entity name)."""
        allowed = ("works", "authors", "institutions", "sources")
        if catalog not in allowed:
            catalog = "works"
        params: dict[str, Any] = {
            "search": query,
            "per_page": per_page,
            "page": page,
        }
        if sort:
            params["sort"] = sort
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            raw = await openalex_get_json(client, f"{_BASE}/{catalog}", self._params(params))
            return raw or {}

    async def get_work(self, work_selector: str) -> dict[str, Any] | None:
        """GET /works/{id} — id can be W…, https://doi.org/…, or raw DOI."""
        wid = normalize_work_selector(work_selector)
        path = quote(wid, safe="") if wid.startswith("http") else wid
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            return await openalex_get_json(
                client,
                f"{_BASE}/works/{path}",
                self._params(),
                allow_not_found=True,
            )

    async def get_work_safe(self, work_selector: str) -> dict[str, Any] | None:
        try:
            return await self.get_work(work_selector)
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 404:
                return None
            raise

    async def list_works(
        self,
        *,
        filter_expr: str,
        per_page: int = 50,
        cursor: str | None = None,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {"filter": filter_expr, "per_page": per_page}
        if cursor:
            params["cursor"] = cursor
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            raw = await openalex_get_json(client, f"{_BASE}/works", self._params(params))
            return raw or {}

    async def get_works_by_openalex_ids(self, short_ids: list[str]) -> list[dict[str, Any]]:
        """Batch-fetch full work objects (max ~50 ids per OpenAlex filter)."""
        clean: list[str] = []
        for x in short_ids:
            if not x:
                continue
            sid = x if x.startswith("W") else openalex_short_id_from_url(x)
            m = re.fullmatch(r"(W)(\d+)", sid or "", re.I)
            if m:
                clean.append("W" + m.group(2))
        if not clean:
            return []
        out: list[dict[str, Any]] = []
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            for i in range(0, len(clean), 45):
                if i:
                    await asyncio.sleep(0.12)
                chunk = clean[i : i + 45]
                filt = "openalex:" + "|".join(chunk)
                blob = await openalex_get_json(
                    client,
                    f"{_BASE}/works",
                    self._params({"filter": filt, "per_page": 50}),
                )
                data = (blob or {}).get("results") or []
                out.extend(data)
        return out
