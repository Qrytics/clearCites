"""
OpenAlex-backed search and automatic graph ingestion for the web UI.
"""

from __future__ import annotations

import os

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

try:
    from scholargraph.data_pipeline.api_clients.openalex import OpenAlexClient
    from scholargraph.data_pipeline.openalex_subgraph import ingest_openalex_explore
except ImportError:  # Docker layout: /app/data_pipeline
    from data_pipeline.api_clients.openalex import OpenAlexClient
    from data_pipeline.openalex_subgraph import ingest_openalex_explore

router = APIRouter(prefix="/openalex", tags=["openalex"])


def _mailto() -> str:
    return (os.getenv("OPENALEX_MAILTO") or os.getenv("CROSSREF_MAILTO") or "").strip()


@router.get("/search")
async def openalex_search(
    q: str = Query(..., min_length=1, description="Plain-language or title query"),
    entity: str = Query(
        "works",
        description="OpenAlex catalog: works, authors, institutions, sources",
        pattern="^(works|authors|institutions|sources)$",
    ),
    per_page: int = Query(25, ge=1, le=100),
    page: int = Query(1, ge=1, le=500),
    year_from: str | None = Query(None, description="YYYY — works only"),
    year_to: str | None = Query(None, description="YYYY — works only"),
    work_type: str | None = Query(None, description="OpenAlex type filter — works only"),
    min_citations: int | None = Query(None, ge=0, description="Minimum cited_by_count — works only"),
    is_oa: bool = Query(False, description="Open access only — works only"),
    has_abstract: bool = Query(False, description="Has abstract — works only"),
    sort_field: str = Query("relevance_score"),
    sort_dir: str = Query("desc", pattern="^(asc|desc)$"),
):
    """
    Proxy search to OpenAlex (works with optional filters, or other entities).
    Returns raw ``results`` objects so the ARXTERM-style UI can render rich cards.
    """
    client = OpenAlexClient(mailto=_mailto())

    sort_param: str | None = None
    if entity == "works":
        if sort_field == "relevance_score" and q.strip():
            sort_param = f"relevance_score:{sort_dir}"
        elif sort_field != "relevance_score":
            sort_param = f"{sort_field}:{sort_dir}"
        try:
            raw = await client.search_works_filtered(
                q,
                per_page=per_page,
                page=page,
                year_from=year_from,
                year_to=year_to,
                work_type=work_type,
                min_citations=min_citations,
                is_oa=is_oa if is_oa else None,
                has_abstract=has_abstract if has_abstract else None,
                sort=sort_param,
            )
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(status_code=502, detail=f"OpenAlex error: {exc}") from exc
    else:
        if sort_field != "relevance_score":
            sort_param = f"{sort_field}:{sort_dir}"
        try:
            raw = await client.search_catalog(
                entity, q, per_page=per_page, page=page, sort=sort_param
            )
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(status_code=502, detail=f"OpenAlex error: {exc}") from exc

    meta = raw.get("meta") or {}
    return {
        "entity": entity,
        "results": raw.get("results") or [],
        "meta": {
            "count": meta.get("count"),
            "page": meta.get("page", page),
            "per_page": meta.get("per_page", per_page),
        },
    }


class ExploreRequest(BaseModel):
    seed_work_id: str = Field(
        ...,
        description="OpenAlex work id (W…), full URL, or DOI string",
    )
    modes: list[str] = Field(
        default_factory=lambda: ["citations_out", "citations_in", "coauthors"],
        description="Any of: citations_in, citations_out, coauthors, concepts, related",
    )
    limit_per_mode: int = Field(25, ge=1, le=100)


@router.post("/explore")
async def openalex_explore(body: ExploreRequest):
    """
    Fetch related works from OpenAlex for the selected modes and upsert all into Neo4j.

    Returns ``seed_canonical_id`` — pass this as ``doi`` to ``GET /graph`` or the /explore UI.
    """
    try:
        summary = await ingest_openalex_explore(
            seed_work_id=body.seed_work_id.strip(),
            modes=body.modes,
            limit_per_mode=body.limit_per_mode,
            mailto=_mailto(),
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"Ingest failed: {exc}") from exc

    return summary
