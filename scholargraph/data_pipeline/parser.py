"""
data_pipeline/parser.py
Extracts structured "Paper Object" data from raw API payloads.
Supports both Semantic Scholar and CrossRef response shapes.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from .api_clients.openalex import openalex_short_id_from_url as _oa_url_id


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


# ---------------------------------------------------------------------------
# OpenAlex
# ---------------------------------------------------------------------------


def openalex_short_id_from_work(work: dict[str, Any]) -> str:
    ids = work.get("ids") or {}
    for key in ("openalex", "pmid", "mag"):
        val = ids.get(key)
        if val:
            return _oa_url_id(str(val))
    return _oa_url_id(str(work.get("id") or ""))


def canonical_paper_key_from_work(work: dict[str, Any]) -> str:
    """Primary key for :Paper nodes — DOI when present, else openalex:W…."""
    doi_url = work.get("doi")
    if doi_url:
        return str(doi_url).replace("https://doi.org/", "").strip().lower()
    wid = openalex_short_id_from_work(work)
    return f"openalex:{wid}" if wid else "openalex:unknown"


def _decode_openalex_abstract(inv: dict[str, Any] | None) -> str:
    if not inv:
        return ""
    parts: list[tuple[int, str]] = []
    for word, positions in inv.items():
        if not isinstance(positions, list):
            continue
        for pos in positions:
            if isinstance(pos, int):
                parts.append((pos, str(word)))
    parts.sort(key=lambda t: t[0])
    return " ".join(w for _, w in parts)


def parse_openalex_work(
    work: dict[str, Any],
    *,
    citation_targets: list[str] | None = None,
) -> PaperObject:
    """Map an OpenAlex *work* JSON object into a :class:`PaperObject`."""
    key = canonical_paper_key_from_work(work)
    title = (work.get("title") or "").strip() or "Untitled"
    year_raw = work.get("publication_year")
    year: int | None = int(year_raw) if year_raw is not None else None

    abstract = _decode_openalex_abstract(work.get("abstract_inverted_index"))

    authors: list[str] = []
    for authorship in work.get("authorships") or []:
        name = (authorship.get("author") or {}).get("display_name")
        if name:
            authors.append(str(name))

    concepts = sorted(
        (work.get("concepts") or []),
        key=lambda c: float(c.get("score") or 0.0),
        reverse=True,
    )
    keywords = [str(c.get("display_name") or "").strip() for c in concepts[:12]]
    keywords = [k for k in keywords if k]

    references: list[str]
    if citation_targets is not None:
        references = list(citation_targets)
    else:
        references = []
        for url in (work.get("referenced_works") or [])[:200]:
            wid = _oa_url_id(str(url))
            if wid:
                references.append(f"openalex:{wid}")

    cited_by_count = int(work.get("cited_by_count") or 0)

    funding_sources: list[str] = []
    for grant in work.get("grants") or []:
        name = (grant.get("funder") or {}).get("display_name")
        if name:
            funding_sources.append(str(name))

    ext: dict[str, str] = {"openalex": openalex_short_id_from_work(work)}
    if work.get("doi"):
        ext["doi_url"] = str(work["doi"])

    return PaperObject(
        doi=key,
        title=title,
        year=year,
        abstract=abstract,
        authors=authors,
        keywords=keywords,
        cited_by_count=cited_by_count,
        references=references,
        funding_sources=funding_sources,
        external_ids=ext,
    )
