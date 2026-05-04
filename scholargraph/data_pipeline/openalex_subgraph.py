"""
Fetch a neighborhood of works from OpenAlex and persist them via :func:`graph_pusher.push_paper`.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from .api_clients.openalex import OpenAlexClient, openalex_short_id_from_url
from .graph_pusher import push_paper
from .parser import (
    canonical_paper_key_from_work,
    openalex_short_id_from_work,
    parse_openalex_work,
)

logger = logging.getLogger(__name__)

_VALID_MODES = frozenset(
    {"citations_in", "citations_out", "coauthors", "concepts", "related"}
)


async def ingest_openalex_explore(
    *,
    seed_work_id: str,
    modes: list[str],
    limit_per_mode: int,
    mailto: str = "",
) -> dict[str, Any]:
    """
    Pull works from OpenAlex according to *modes*, upsert into Neo4j, return the seed graph key.

    *modes* may include: citations_in, citations_out, coauthors, concepts, related.
    """
    cleaned = [m.strip().lower() for m in modes if m.strip().lower() in _VALID_MODES]
    if not cleaned:
        cleaned = ["citations_out", "citations_in"]

    client = OpenAlexClient(mailto=mailto)
    seed_work = await client.get_work(seed_work_id)
    if not seed_work:
        raise ValueError(f"OpenAlex work not found for selector: {seed_work_id!r}")

    seed_key = canonical_paper_key_from_work(seed_work)
    seed_w = openalex_short_id_from_work(seed_work)

    collected: dict[str, dict[str, Any]] = {}
    citation_targets: list[str] | None = None

    def add_work(w: dict[str, Any]) -> None:
        k = canonical_paper_key_from_work(w)
        collected[k] = w

    add_work(seed_work)

    if "citations_out" in cleaned:
        urls = (seed_work.get("referenced_works") or [])[:limit_per_mode]
        ids = [openalex_short_id_from_url(str(u)) for u in urls]
        ids = [i for i in ids if i]
        if ids:
            refs = await client.get_works_by_openalex_ids(ids)
            await asyncio.sleep(0.1)
            targets: list[str] = []
            for w in refs:
                add_work(w)
                targets.append(canonical_paper_key_from_work(w))
            citation_targets = targets

    if "citations_in" in cleaned:
        filt = f"cites:{seed_w}"
        data = await client.list_works(filter_expr=filt, per_page=limit_per_mode)
        await asyncio.sleep(0.1)
        for w in data.get("results") or []:
            add_work(w)

    if "coauthors" in cleaned:
        author_ids: list[str] = []
        for authorship in (seed_work.get("authorships") or [])[:10]:
            aid = (authorship.get("author") or {}).get("id")
            if not aid:
                continue
            short = str(aid).rstrip("/").split("/")[-1]
            if short.startswith("A"):
                author_ids.append(short)
        author_ids = list(dict.fromkeys(author_ids))[:5]
        if author_ids:
            filt = "author.id:" + "|".join(author_ids)
            data = await client.list_works(
                filter_expr=filt, per_page=min(limit_per_mode * 4, 100)
            )
            await asyncio.sleep(0.1)
            for w in data.get("results") or []:
                if canonical_paper_key_from_work(w) != seed_key:
                    add_work(w)

    if "concepts" in cleaned:
        concept_id: str | None = None
        for c in sorted(
            (seed_work.get("concepts") or []),
            key=lambda x: (int(x.get("level") or 9), -float(x.get("score") or 0.0)),
        ):
            cid = str(c.get("id") or "").rstrip("/").split("/")[-1]
            if cid.startswith("C"):
                concept_id = cid
                break
        if concept_id:
            data = await client.list_works(
                filter_expr=f"concepts.id:{concept_id}",
                per_page=limit_per_mode,
            )
            await asyncio.sleep(0.1)
            for w in data.get("results") or []:
                if canonical_paper_key_from_work(w) != seed_key:
                    add_work(w)

    if "related" in cleaned:
        urls = (seed_work.get("related_works") or [])[:limit_per_mode]
        ids = [openalex_short_id_from_url(str(u)) for u in urls]
        ids = [i for i in ids if i]
        if ids:
            rel = await client.get_works_by_openalex_ids(ids)
            await asyncio.sleep(0.1)
            for w in rel:
                add_work(w)

    keys = sorted(collected.keys(), key=lambda k: (0 if k != seed_key else 1, k))
    n = 0
    for k in keys:
        w = collected[k]
        if k == seed_key:
            paper = parse_openalex_work(w, citation_targets=citation_targets)
        else:
            paper = parse_openalex_work(w)
        await push_paper(paper)
        n += 1

    logger.info("OpenAlex explore ingested %s works (seed=%s)", n, seed_key)
    return {
        "seed_canonical_id": seed_key,
        "ingested_works": n,
        "modes": cleaned,
    }
