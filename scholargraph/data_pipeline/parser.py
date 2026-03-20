"""
data_pipeline/parser.py
Extracts structured "Paper Object" data from raw API payloads.
Supports both Semantic Scholar and CrossRef response shapes.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any


@dataclass
class PaperObject:
    """Canonical representation of a research paper used throughout the pipeline."""

    doi: str
    title: str
    year: int | None
    abstract: str
    authors: list[str]
    keywords: list[str]
    cited_by_count: int
    references: list[str]          # list of DOIs
    funding_sources: list[str]     # e.g. ["NIH", "NSF"]
    external_ids: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "doi": self.doi,
            "title": self.title,
            "year": self.year,
            "abstract": self.abstract,
            "authors": self.authors,
            "keywords": self.keywords,
            "cited_by_count": self.cited_by_count,
            "references": self.references,
            "funding_sources": self.funding_sources,
            "external_ids": self.external_ids,
        }


# ---------------------------------------------------------------------------
# Semantic Scholar parser
# ---------------------------------------------------------------------------

def parse_semantic_scholar(raw: dict[str, Any], doi: str) -> PaperObject:
    """Convert a raw Semantic Scholar API response into a :class:`PaperObject`."""
    authors = [
        a.get("name", "")
        for a in raw.get("authors", [])
        if a.get("name")
    ]
    keywords = list(raw.get("fieldsOfStudy", []) or [])

    # References: grab DOIs where available
    references: list[str] = []
    for ref in raw.get("references", []):
        ext_ids = ref.get("externalIds") or {}
        ref_doi = ext_ids.get("DOI") or ext_ids.get("doi")
        if ref_doi:
            references.append(ref_doi)

    external_ids: dict[str, str] = {}
    for key, val in (raw.get("externalIds") or {}).items():
        if val:
            external_ids[str(key)] = str(val)

    return PaperObject(
        doi=doi,
        title=raw.get("title") or "",
        year=raw.get("year"),
        abstract=raw.get("abstract") or "",
        authors=authors,
        keywords=keywords,
        cited_by_count=raw.get("citationCount", 0) or 0,
        references=references,
        funding_sources=[],          # Semantic Scholar doesn't expose funding
        external_ids=external_ids,
    )


# ---------------------------------------------------------------------------
# CrossRef parser
# ---------------------------------------------------------------------------

_FUNDER_NORMALIZATIONS: dict[str, str] = {
    "national institutes of health": "NIH",
    "national science foundation": "NSF",
    "european research council": "ERC",
    "wellcome trust": "Wellcome Trust",
    "bill and melinda gates foundation": "Gates Foundation",
}


def _normalize_funder(name: str) -> str:
    lower = name.lower().strip()
    return _FUNDER_NORMALIZATIONS.get(lower, name.strip())


def _extract_doi_from_crossref(item: dict[str, Any]) -> str:
    return (item.get("DOI") or "").strip()


def parse_crossref(raw: dict[str, Any]) -> PaperObject:
    """Convert a raw CrossRef API item into a :class:`PaperObject`."""
    doi = _extract_doi_from_crossref(raw)

    # Title
    titles = raw.get("title", [])
    title = titles[0] if titles else ""

    # Year
    year: int | None = None
    date_parts = (raw.get("published", {}) or {}).get("date-parts", [])
    if date_parts and date_parts[0]:
        try:
            year = int(date_parts[0][0])
        except (ValueError, IndexError):
            pass

    # Abstract – CrossRef returns JATS XML; strip tags
    raw_abstract = raw.get("abstract", "")
    abstract = re.sub(r"<[^>]+>", "", raw_abstract).strip()

    # Authors
    authors: list[str] = []
    for author in raw.get("author", []):
        given = author.get("given", "")
        family = author.get("family", "")
        name = f"{given} {family}".strip()
        if name:
            authors.append(name)

    # Keywords (CrossRef "subject" field)
    keywords: list[str] = list(raw.get("subject", []) or [])

    # References
    references: list[str] = []
    for ref in raw.get("reference", []):
        ref_doi = (ref.get("DOI") or "").strip()
        if ref_doi:
            references.append(ref_doi)

    # Funding sources
    funding_sources: list[str] = []
    for funder in raw.get("funder", []):
        fname = funder.get("name", "").strip()
        if fname:
            funding_sources.append(_normalize_funder(fname))

    cited_by_count = raw.get("is-referenced-by-count", 0) or 0

    return PaperObject(
        doi=doi,
        title=title,
        year=year,
        abstract=abstract,
        authors=authors,
        keywords=keywords,
        cited_by_count=cited_by_count,
        references=references,
        funding_sources=funding_sources,
        external_ids={},
    )
