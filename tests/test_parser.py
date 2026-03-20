"""
tests/test_parser.py
Unit tests for data_pipeline/parser.py – no external services required.
"""

import pytest

from scholargraph.data_pipeline.parser import (
    PaperObject,
    parse_crossref,
    parse_semantic_scholar,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

SEMANTIC_SCHOLAR_FIXTURE = {
    "title": "Attention Is All You Need",
    "year": 2017,
    "abstract": "We propose a new simple network architecture, the Transformer ...",
    "citationCount": 80000,
    "authors": [
        {"name": "Ashish Vaswani"},
        {"name": "Noam Shazeer"},
    ],
    "fieldsOfStudy": ["Computer Science", "Machine Learning"],
    "references": [
        {"externalIds": {"DOI": "10.1162/neco.1997.9.8.1735"}},
        {"externalIds": {}},  # No DOI – should be skipped
    ],
    "externalIds": {"ArXiv": "1706.03762", "DOI": "10.48550/arxiv.1706.03762"},
}

CROSSREF_FIXTURE = {
    "DOI": "10.1038/nature12373",
    "title": ["Playing Atari with Deep Reinforcement Learning"],
    "published": {"date-parts": [[2013]]},
    "abstract": "<jats:p>We present the first deep learning model to <jats:italic>successfully</jats:italic> learn.</jats:p>",
    "author": [
        {"given": "Volodymyr", "family": "Mnih"},
        {"given": "Koray", "family": "Kavukcuoglu"},
    ],
    "subject": ["Multidisciplinary"],
    "reference": [
        {"DOI": "10.1162/neco.1997.9.8.1735"},
        {"key": "ref2"},  # No DOI
    ],
    "funder": [
        {"name": "Google DeepMind"},
        {"name": "National Science Foundation"},
    ],
    "is-referenced-by-count": 15000,
}


# ---------------------------------------------------------------------------
# Semantic Scholar parser tests
# ---------------------------------------------------------------------------

class TestParseSemanticScholar:
    def test_returns_paper_object(self):
        paper = parse_semantic_scholar(SEMANTIC_SCHOLAR_FIXTURE, doi="10.48550/arxiv.1706.03762")
        assert isinstance(paper, PaperObject)

    def test_doi_set_correctly(self):
        paper = parse_semantic_scholar(SEMANTIC_SCHOLAR_FIXTURE, doi="10.48550/arxiv.1706.03762")
        assert paper.doi == "10.48550/arxiv.1706.03762"

    def test_title_extracted(self):
        paper = parse_semantic_scholar(SEMANTIC_SCHOLAR_FIXTURE, doi="10.48550/arxiv.1706.03762")
        assert paper.title == "Attention Is All You Need"

    def test_year_extracted(self):
        paper = parse_semantic_scholar(SEMANTIC_SCHOLAR_FIXTURE, doi="10.48550/arxiv.1706.03762")
        assert paper.year == 2017

    def test_authors_extracted(self):
        paper = parse_semantic_scholar(SEMANTIC_SCHOLAR_FIXTURE, doi="10.48550/arxiv.1706.03762")
        assert "Ashish Vaswani" in paper.authors
        assert "Noam Shazeer" in paper.authors

    def test_keywords_from_fields_of_study(self):
        paper = parse_semantic_scholar(SEMANTIC_SCHOLAR_FIXTURE, doi="10.48550/arxiv.1706.03762")
        assert "Computer Science" in paper.keywords

    def test_cited_by_count(self):
        paper = parse_semantic_scholar(SEMANTIC_SCHOLAR_FIXTURE, doi="10.48550/arxiv.1706.03762")
        assert paper.cited_by_count == 80000

    def test_references_only_include_dois(self):
        paper = parse_semantic_scholar(SEMANTIC_SCHOLAR_FIXTURE, doi="10.48550/arxiv.1706.03762")
        assert "10.1162/neco.1997.9.8.1735" in paper.references
        assert len(paper.references) == 1  # Second ref has no DOI

    def test_external_ids_extracted(self):
        paper = parse_semantic_scholar(SEMANTIC_SCHOLAR_FIXTURE, doi="10.48550/arxiv.1706.03762")
        assert paper.external_ids.get("ArXiv") == "1706.03762"

    def test_empty_abstract_handled(self):
        raw = {**SEMANTIC_SCHOLAR_FIXTURE, "abstract": None}
        paper = parse_semantic_scholar(raw, doi="test")
        assert paper.abstract == ""

    def test_missing_citation_count_defaults_to_zero(self):
        raw = {**SEMANTIC_SCHOLAR_FIXTURE, "citationCount": None}
        paper = parse_semantic_scholar(raw, doi="test")
        assert paper.cited_by_count == 0

    def test_to_dict_is_serialisable(self):
        paper = parse_semantic_scholar(SEMANTIC_SCHOLAR_FIXTURE, doi="10.48550/arxiv.1706.03762")
        d = paper.to_dict()
        assert d["doi"] == "10.48550/arxiv.1706.03762"
        assert isinstance(d["authors"], list)


# ---------------------------------------------------------------------------
# CrossRef parser tests
# ---------------------------------------------------------------------------

class TestParseCrossRef:
    def test_returns_paper_object(self):
        paper = parse_crossref(CROSSREF_FIXTURE)
        assert isinstance(paper, PaperObject)

    def test_doi_extracted(self):
        paper = parse_crossref(CROSSREF_FIXTURE)
        assert paper.doi == "10.1038/nature12373"

    def test_title_extracted(self):
        paper = parse_crossref(CROSSREF_FIXTURE)
        assert paper.title == "Playing Atari with Deep Reinforcement Learning"

    def test_year_extracted(self):
        paper = parse_crossref(CROSSREF_FIXTURE)
        assert paper.year == 2013

    def test_abstract_strips_jats_tags(self):
        paper = parse_crossref(CROSSREF_FIXTURE)
        assert "<jats:" not in paper.abstract
        assert "We present" in paper.abstract

    def test_authors_full_names(self):
        paper = parse_crossref(CROSSREF_FIXTURE)
        assert "Volodymyr Mnih" in paper.authors

    def test_keywords_from_subject(self):
        paper = parse_crossref(CROSSREF_FIXTURE)
        assert "Multidisciplinary" in paper.keywords

    def test_references_only_include_dois(self):
        paper = parse_crossref(CROSSREF_FIXTURE)
        assert "10.1162/neco.1997.9.8.1735" in paper.references
        assert len(paper.references) == 1

    def test_funding_sources_extracted_and_normalised(self):
        paper = parse_crossref(CROSSREF_FIXTURE)
        assert "NSF" in paper.funding_sources
        assert "Google DeepMind" in paper.funding_sources

    def test_cited_by_count(self):
        paper = parse_crossref(CROSSREF_FIXTURE)
        assert paper.cited_by_count == 15000

    def test_empty_author_list(self):
        raw = {**CROSSREF_FIXTURE, "author": []}
        paper = parse_crossref(raw)
        assert paper.authors == []

    def test_missing_year_returns_none(self):
        raw = {**CROSSREF_FIXTURE, "published": {}}
        paper = parse_crossref(raw)
        assert paper.year is None

    def test_to_dict_contains_funding(self):
        paper = parse_crossref(CROSSREF_FIXTURE)
        d = paper.to_dict()
        assert "NSF" in d["funding_sources"]
