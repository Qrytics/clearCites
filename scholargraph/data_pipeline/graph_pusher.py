"""
data_pipeline/graph_pusher.py
Converts PaperObject instances into Neo4j Nodes and Edges using the
official neo4j Python driver.
"""

from __future__ import annotations

import os
from typing import Any

from neo4j import AsyncDriver, AsyncGraphDatabase

from .parser import PaperObject


def _get_driver() -> AsyncDriver:
    uri = os.environ["NEO4J_URI"]
    user = os.environ["NEO4J_USER"]
    password = os.environ["NEO4J_PASSWORD"]
    return AsyncGraphDatabase.driver(uri, auth=(user, password))


# ---------------------------------------------------------------------------
# Cypher helpers
# ---------------------------------------------------------------------------

_MERGE_PAPER = """
MERGE (p:Paper {doi: $doi})
ON CREATE SET
    p.title          = $title,
    p.year           = $year,
    p.abstract       = $abstract,
    p.funding_source = $funding_source,
    p.cited_by_count = $cited_by_count,
    p.impact_score   = 0.0,
    p.created_at     = datetime()
ON MATCH SET
    p.cited_by_count = $cited_by_count
"""

_MERGE_AUTHOR = """
MERGE (a:Author {name: $name})
ON CREATE SET a.created_at = datetime()
"""

_MERGE_WROTE = """
MATCH (a:Author {name: $author_name}), (p:Paper {doi: $doi})
MERGE (a)-[:WROTE]->(p)
"""

_MERGE_KEYWORD = """
MERGE (k:Keyword {text: $text})
"""

_MERGE_HAS_KEYWORD = """
MATCH (p:Paper {doi: $doi}), (k:Keyword {text: $keyword})
MERGE (p)-[:HAS_KEYWORD]->(k)
"""

_MERGE_FUNDER = """
MERGE (f:Funder {name: $name})
"""

_MERGE_FUNDED_BY = """
MATCH (p:Paper {doi: $doi}), (f:Funder {name: $funder})
MERGE (p)-[:FUNDED_BY]->(f)
"""

_MERGE_CITES = """
MERGE (ref:Paper {doi: $ref_doi})
ON CREATE SET ref.title = '', ref.created_at = datetime()
WITH ref
MATCH (src:Paper {doi: $src_doi})
MERGE (src)-[:CITES]->(ref)
"""


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def push_paper(paper: PaperObject, driver: AsyncDriver | None = None) -> None:
    """Write a single :class:`PaperObject` into the Neo4j graph."""
    close_driver = driver is None
    if driver is None:
        driver = _get_driver()

    try:
        async with driver.session() as session:
            # Upsert Paper node
            funding_source = (
                ", ".join(paper.funding_sources) if paper.funding_sources else ""
            )
            await session.run(
                _MERGE_PAPER,
                doi=paper.doi,
                title=paper.title,
                year=paper.year,
                abstract=paper.abstract,
                funding_source=funding_source,
                cited_by_count=paper.cited_by_count,
            )

            # Authors
            for author_name in paper.authors:
                await session.run(_MERGE_AUTHOR, name=author_name)
                await session.run(
                    _MERGE_WROTE, author_name=author_name, doi=paper.doi
                )

            # Keywords
            for kw in paper.keywords:
                await session.run(_MERGE_KEYWORD, text=kw)
                await session.run(
                    _MERGE_HAS_KEYWORD, doi=paper.doi, keyword=kw
                )

            # Funders
            for funder_name in paper.funding_sources:
                await session.run(_MERGE_FUNDER, name=funder_name)
                await session.run(
                    _MERGE_FUNDED_BY, doi=paper.doi, funder=funder_name
                )

            # Citation edges (stub target nodes if unknown)
            for ref_doi in paper.references:
                await session.run(
                    _MERGE_CITES, src_doi=paper.doi, ref_doi=ref_doi
                )
    finally:
        if close_driver:
            await driver.close()


async def update_impact_score(doi: str, score: float, driver: AsyncDriver | None = None) -> None:
    """Persist an AI-generated impact / correlation score on a Paper node."""
    close_driver = driver is None
    if driver is None:
        driver = _get_driver()

    try:
        async with driver.session() as session:
            await session.run(
                "MATCH (p:Paper {doi: $doi}) SET p.impact_score = $score",
                doi=doi,
                score=score,
            )
    finally:
        if close_driver:
            await driver.close()


_REL_QUERIES: dict[str, str] = {
    "VALIDATES": (
        "MATCH (src:Paper {doi: $src_doi}), (tgt:Paper {doi: $tgt_doi}) "
        "MERGE (src)-[r:VALIDATES]->(tgt) "
        "ON CREATE SET r.correlation_value = $correlation_value, r.evaluated_by = $evaluated_by"
    ),
    "BUILDS_ON": (
        "MATCH (src:Paper {doi: $src_doi}), (tgt:Paper {doi: $tgt_doi}) "
        "MERGE (src)-[r:BUILDS_ON]->(tgt)"
    ),
    "CHALLENGES": (
        "MATCH (src:Paper {doi: $src_doi}), (tgt:Paper {doi: $tgt_doi}) "
        "MERGE (src)-[r:CHALLENGES]->(tgt)"
    ),
}


async def set_relationship(
    src_doi: str,
    tgt_doi: str,
    rel_type: str,
    properties: dict[str, Any] | None = None,
    driver: AsyncDriver | None = None,
) -> None:
    """Create or update a typed relationship between two papers.

    *rel_type* must be one of: VALIDATES, BUILDS_ON, CHALLENGES.
    Uses a pre-defined query map to avoid Cypher injection via string interpolation.
    """
    if rel_type not in _REL_QUERIES:
        raise ValueError(f"rel_type must be one of {set(_REL_QUERIES)}, got {rel_type!r}")

    cypher = _REL_QUERIES[rel_type]
    props = properties or {}

    close_driver = driver is None
    if driver is None:
        driver = _get_driver()

    try:
        async with driver.session() as session:
            await session.run(cypher, src_doi=src_doi, tgt_doi=tgt_doi, **props)
    finally:
        if close_driver:
            await driver.close()
