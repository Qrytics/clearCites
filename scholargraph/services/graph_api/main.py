"""
services/graph_api/main.py
FastAPI application – exposes graph traversal and paper endpoints.
"""

from __future__ import annotations

import os

from fastapi import FastAPI, HTTPException, Query
from neo4j import AsyncGraphDatabase

app = FastAPI(
    title="ScholarGraph API",
    description="Graph traversal API for the ScholarGraph research visualization tool.",
    version="0.1.0",
)


def _driver():
    return AsyncGraphDatabase.driver(
        os.environ["NEO4J_URI"],
        auth=(os.environ["NEO4J_USER"], os.environ["NEO4J_PASSWORD"]),
    )


# Pre-built Cypher queries for each allowed depth value (1-3).
# Cypher does not support parameterized variable-length path bounds,
# so we use a static lookup table to avoid f-string interpolation.
_CITATION_QUERIES: dict[int, str] = {
    d: (
        f"MATCH path = (src:Paper {{doi: $doi}})-[:CITES*1..{d}]->(ref:Paper) "
        "RETURN DISTINCT ref.doi AS doi, ref.title AS title, "
        "ref.year AS year, ref.cited_by_count AS cited_by_count, "
        "ref.impact_score AS impact_score"
    )
    for d in (1, 2, 3)
}

_GRAPH_QUERIES: dict[int, str] = {
    d: (
        f"MATCH path = (seed:Paper {{doi: $doi}})-[:CITES*0..{d}]-(p:Paper) "
        "WITH collect(DISTINCT p) AS papers, collect(DISTINCT relationships(path)) AS rel_lists "
        "UNWIND papers AS p "
        "WITH collect(DISTINCT { "
        "    id: p.doi, label: p.title, "
        "    data: { doi: p.doi, year: p.year, cited_by_count: p.cited_by_count, "
        "            impact_score: p.impact_score, funding_source: p.funding_source } "
        "}) AS nodes, rel_lists "
        "UNWIND rel_lists AS rels "
        "UNWIND rels AS rel "
        "WITH nodes, collect(DISTINCT { "
        "    id: toString(id(rel)), source: startNode(rel).doi, "
        "    target: endNode(rel).doi, label: type(rel) "
        "}) AS edges "
        "RETURN nodes, edges"
    )
    for d in (1, 2, 3)
}


# ---------------------------------------------------------------------------
# Paper endpoints
# ---------------------------------------------------------------------------

@app.get("/papers/{doi:path}")
async def get_paper(doi: str):
    """Return the full Paper node and its direct relationships."""
    async with _driver().session() as session:
        result = await session.run(
            """
            MATCH (p:Paper {doi: $doi})
            OPTIONAL MATCH (p)<-[:WROTE]-(a:Author)
            OPTIONAL MATCH (p)-[:HAS_KEYWORD]->(k:Keyword)
            OPTIONAL MATCH (p)-[:FUNDED_BY]->(f:Funder)
            RETURN p,
                   collect(DISTINCT a.name)  AS authors,
                   collect(DISTINCT k.text)  AS keywords,
                   collect(DISTINCT f.name)  AS funders
            """,
            doi=doi,
        )
        record = await result.single()
        if record is None:
            raise HTTPException(status_code=404, detail="Paper not found")

        paper_node = dict(record["p"])
        paper_node["authors"] = record["authors"]
        paper_node["keywords"] = record["keywords"]
        paper_node["funders"] = record["funders"]
        return paper_node


@app.get("/papers/{doi:path}/citations")
async def get_citations(doi: str, depth: int = Query(default=1, ge=1, le=3)):
    """Return all papers that *doi* cites, up to *depth* hops."""
    async with _driver().session() as session:
        result = await session.run(_CITATION_QUERIES[depth], doi=doi)
        records = await result.data()
        return records


@app.get("/papers/{doi:path}/cited-by")
async def get_cited_by(doi: str):
    """Return all papers that cite *doi*."""
    async with _driver().session() as session:
        result = await session.run(
            """
            MATCH (src:Paper)-[:CITES]->(p:Paper {doi: $doi})
            RETURN src.doi AS doi, src.title AS title,
                   src.year AS year, src.impact_score AS impact_score
            """,
            doi=doi,
        )
        return await result.data()


@app.get("/papers/{doi:path}/pedigree")
async def get_pedigree(doi: str):
    """Return the full citation lineage (ancestor chain) of a paper."""
    async with _driver().session() as session:
        result = await session.run(
            """
            MATCH path = (p:Paper {doi: $doi})-[:CITES*]->(ancestor:Paper)
            WITH ancestor, length(path) AS hops
            RETURN ancestor.doi AS doi, ancestor.title AS title,
                   ancestor.year AS year, hops
            ORDER BY hops ASC
            """,
            doi=doi,
        )
        return await result.data()


# ---------------------------------------------------------------------------
# Search endpoints
# ---------------------------------------------------------------------------

@app.get("/search")
async def search_papers(
    q: str = Query(..., description="Keyword or phrase to search"),
    limit: int = Query(default=20, ge=1, le=100),
):
    """Full-text search over paper titles and abstracts stored in Neo4j."""
    async with _driver().session() as session:
        result = await session.run(
            """
            MATCH (p:Paper)
            WHERE toLower(p.title)    CONTAINS toLower($q)
               OR toLower(p.abstract) CONTAINS toLower($q)
            RETURN p.doi AS doi, p.title AS title,
                   p.year AS year, p.impact_score AS impact_score
            LIMIT $limit
            """,
            q=q,
            limit=limit,
        )
        return await result.data()


@app.get("/search/by-keyword")
async def search_by_keyword(
    keyword: str = Query(..., description="Keyword node text to match"),
    limit: int = Query(default=20, ge=1, le=100),
):
    """Return papers linked to a specific :class:`Keyword` node."""
    async with _driver().session() as session:
        result = await session.run(
            """
            MATCH (p:Paper)-[:HAS_KEYWORD]->(k:Keyword)
            WHERE toLower(k.text) CONTAINS toLower($keyword)
            RETURN p.doi AS doi, p.title AS title,
                   p.year AS year, p.impact_score AS impact_score
            LIMIT $limit
            """,
            keyword=keyword,
            limit=limit,
        )
        return await result.data()


# ---------------------------------------------------------------------------
# Author endpoints
# ---------------------------------------------------------------------------

@app.get("/authors/{name}/papers")
async def get_author_papers(name: str):
    """Return all papers written by an author."""
    async with _driver().session() as session:
        result = await session.run(
            """
            MATCH (a:Author)-[:WROTE]->(p:Paper)
            WHERE toLower(a.name) CONTAINS toLower($name)
            RETURN p.doi AS doi, p.title AS title,
                   p.year AS year, a.name AS author
            """,
            name=name,
        )
        return await result.data()


# ---------------------------------------------------------------------------
# Graph export endpoint (for the frontend canvas)
# ---------------------------------------------------------------------------

@app.get("/graph")
async def get_graph(
    doi: str = Query(..., description="Seed DOI to build the graph around"),
    depth: int = Query(default=2, ge=1, le=3),
):
    """
    Return a node/edge JSON structure suitable for React Flow or D3.
    Nodes have id, label, data.  Edges have id, source, target, label.
    """
    async with _driver().session() as session:
        result = await session.run(_GRAPH_QUERIES[depth], doi=doi)
        record = await result.single()
        if record is None:
            return {"nodes": [], "edges": []}
        return {"nodes": record["nodes"], "edges": record["edges"]}
