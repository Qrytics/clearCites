"""Fetch metadata for a DOI and upsert it into Neo4j (Semantic Scholar or CrossRef)."""

from __future__ import annotations

import argparse
import asyncio
import os
import sys

from scholargraph.data_pipeline.api_clients.crossref import CrossRefClient
from scholargraph.data_pipeline.api_clients.semantic_scholar import SemanticScholarClient
from scholargraph.data_pipeline.graph_pusher import push_paper
from scholargraph.data_pipeline.parser import parse_crossref, parse_semantic_scholar


def _env_defaults() -> None:
    os.environ.setdefault("NEO4J_URI", "bolt://localhost:7687")
    os.environ.setdefault("NEO4J_USER", "neo4j")


async def _ingest_semantic_scholar(doi: str) -> str:
    raw = await SemanticScholarClient().get_paper(doi)
    ext = raw.get("externalIds") or {}
    canonical = ext.get("DOI") or ext.get("doi") or doi
    paper = parse_semantic_scholar(raw, doi=str(canonical))
    await push_paper(paper)
    return str(canonical)


async def _ingest_crossref(doi: str, mailto: str) -> str:
    raw = await CrossRefClient(mailto=mailto or "").get_paper(doi)
    paper = parse_crossref(raw)
    await push_paper(paper)
    return paper.doi


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Ingest one paper into Neo4j by DOI (writes Paper, authors, keywords, CITES stubs)."
    )
    parser.add_argument(
        "doi",
        help='DOI string, e.g. "10.1038/nature14539" (no "doi:" prefix).',
    )
    parser.add_argument(
        "--source",
        choices=("semantic_scholar", "crossref"),
        default="semantic_scholar",
        help="Metadata provider (default: semantic_scholar).",
    )
    parser.add_argument(
        "--mailto",
        default="",
        help="Email for CrossRef polite pool (optional; reads CROSSREF_MAILTO from env if unset).",
    )
    args = parser.parse_args()

    _env_defaults()
    if not os.environ.get("NEO4J_PASSWORD"):
        print("NEO4J_PASSWORD is not set; use the same value as in scholargraph/.env", file=sys.stderr)
        sys.exit(1)

    doi = args.doi.strip().removeprefix("doi:").removeprefix("DOI:").strip()

    async def run() -> str:
        if args.source == "crossref":
            mailto = args.mailto or os.environ.get("CROSSREF_MAILTO", "")
            return await _ingest_crossref(doi, mailto)
        return await _ingest_semantic_scholar(doi)

    try:
        used = asyncio.run(run())
    except Exception as exc:  # noqa: BLE001 — CLI surface
        print(f"Ingest failed: {exc}", file=sys.stderr)
        sys.exit(1)

    print(f"Upserted paper DOI: {used}")


if __name__ == "__main__":
    main()
