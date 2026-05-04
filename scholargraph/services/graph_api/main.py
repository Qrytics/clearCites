"""
services/graph_api/main.py
FastAPI application – exposes graph traversal and paper endpoints.
"""

from __future__ import annotations

import hashlib
import os

from fastapi import FastAPI, HTTPException, Query
from neo4j import AsyncGraphDatabase

app = FastAPI(
    title="clearCites API",
    description="Graph traversal API for the clearCites research visualization tool.",
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


def _parse_expand(expand: str) -> set[str]:
    parts = {p.strip().lower() for p in expand.split(",") if p.strip()}
    if not parts:
        parts.add("citations")
    return parts


def _author_node_id(name: str) -> str:
    return "a_" + hashlib.sha256(name.encode("utf-8")).hexdigest()[:24]


def _keyword_node_id(text: str) -> str:
    return "k_" + hashlib.sha256(text.encode("utf-8")).hexdigest()[:24]


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
    expand: str = Query(
        default="citations,authors,coauthors",
        description=(
            "Comma-separated facets: citations (paper neighborhood via CITES), "
            "authors (WROTE), coauthors (other papers sharing an author with the seed), "
            "keywords (HAS_KEYWORD)."
        ),
    ),
):
    """
    Return a node/edge JSON structure suitable for React Flow or D3.
    Nodes have id, label, data (include data.kind: paper | author | keyword).
    CITES edges: source cites target (see data.connection: cites | cited_by).
    """
    modes = _parse_expand(expand)
    use_citations = "citations" in modes

    async with _driver().session() as session:
        nodes: list[dict] = []
        edges: list[dict] = []

        if use_citations:
            result = await session.run(_GRAPH_QUERIES[depth], doi=doi)
            record = await result.single()
            if record is None:
                return {"nodes": [], "edges": []}
            nodes = list(record["nodes"] or [])
            edges = list(record["edges"] or [])
        else:
            res = await session.run(
                """
                MATCH (p:Paper {doi: $doi})
                RETURN [{
                    id: p.doi,
                    label: p.title,
                    data: {
                        doi: p.doi,
                        year: p.year,
                        cited_by_count: p.cited_by_count,
                        impact_score: p.impact_score,
                        funding_source: p.funding_source
                    }
                }] AS nodes
                """,
                doi=doi,
            )
            rec = await res.single()
            if rec is None:
                return {"nodes": [], "edges": []}
            nodes = list(rec["nodes"] or [])

        for n in nodes:
            n.setdefault("data", {})
            n["data"]["kind"] = "paper"
            n["data"].setdefault("doi", n["id"])

        paper_dois = {str(n["id"]) for n in nodes}

        edge_keys: set[tuple[str, str, str]] = set()
        eid = 0

        def add_edge(source: str, target: str, label: str, **extra: object) -> None:
            nonlocal eid
            key = (source, target, label)
            if key in edge_keys:
                return
            edge_keys.add(key)
            row: dict = {
                "id": f"e_{eid}",
                "source": source,
                "target": target,
                "label": label,
            }
            row.update({k: v for k, v in extra.items() if v is not None})
            edges.append(row)
            eid += 1

        for e in edges:
            edge_keys.add((e["source"], e["target"], e.get("label", "CITES")))

        for e in edges:
            e.setdefault("data", {})
            e["data"]["connection"] = "cites"
            e["label"] = "cites"

        if "coauthors" in modes:
            r2 = await session.run(
                """
                MATCH (seed:Paper {doi: $doi})<-[:WROTE]-(a:Author)-[:WROTE]->(p:Paper)
                WHERE p <> seed
                WITH DISTINCT p LIMIT 40
                RETURN p.doi AS doi, p.title AS title, p.year AS year,
                       p.cited_by_count AS cited_by_count,
                       p.impact_score AS impact_score,
                       p.funding_source AS funding_source
                """,
                doi=doi,
            )
            for row in await r2.data():
                pid = row["doi"]
                if not pid or pid in paper_dois:
                    continue
                paper_dois.add(pid)
                nodes.append(
                    {
                        "id": pid,
                        "label": row.get("title") or pid,
                        "data": {
                            "kind": "paper",
                            "doi": pid,
                            "title": row.get("title"),
                            "year": row.get("year"),
                            "cited_by_count": row.get("cited_by_count"),
                            "impact_score": row.get("impact_score"),
                            "funding_source": row.get("funding_source"),
                        },
                    }
                )

        dois_list = list(paper_dois)

        if "authors" in modes and dois_list:
            r3 = await session.run(
                """
                UNWIND $dois AS d
                MATCH (p:Paper {doi: d})<-[:WROTE]-(a:Author)
                RETURN DISTINCT a.name AS author_name, p.doi AS paper_doi
                """,
                dois=dois_list,
            )
            authors_seen: set[str] = set()
            for row in await r3.data():
                aname, pd = row.get("author_name"), row.get("paper_doi")
                if not aname or not pd:
                    continue
                aid = _author_node_id(aname)
                if aid not in authors_seen:
                    authors_seen.add(aid)
                    nodes.append(
                        {
                            "id": aid,
                            "label": aname,
                            "data": {"kind": "author", "name": aname},
                        }
                    )
                add_edge(aid, pd, "wrote")

        if "keywords" in modes and dois_list:
            r4 = await session.run(
                """
                UNWIND $dois AS d
                MATCH (p:Paper {doi: d})-[:HAS_KEYWORD]->(k:Keyword)
                RETURN DISTINCT k.text AS keyword_text, p.doi AS paper_doi
                LIMIT 200
                """,
                dois=dois_list,
            )
            kw_seen: set[str] = set()
            for row in await r4.data():
                kw, pd = row.get("keyword_text"), row.get("paper_doi")
                if not kw or not pd:
                    continue
                kid = _keyword_node_id(kw)
                if kid not in kw_seen:
                    kw_seen.add(kid)
                    nodes.append(
                        {
                            "id": kid,
                            "label": kw,
                            "data": {"kind": "keyword", "text": kw},
                        }
                    )
                add_edge(pd, kid, "has_keyword")

        return {"nodes": nodes, "edges": edges}
