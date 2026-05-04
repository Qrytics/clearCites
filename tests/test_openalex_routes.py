"""Contract-style tests for OpenAlex proxy routes (client mocked; no live HTTP)."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest


@pytest.fixture()
def mock_openalex_client():
    """Patch OpenAlexClient in the router module where endpoints resolve it."""
    with patch("scholargraph.services.graph_api.openalex_routes.OpenAlexClient") as cls:
        inst = cls.return_value
        inst.search_works_filtered = AsyncMock(
            return_value={
                "results": [{"id": "https://openalex.org/W1", "title": "T"}],
                "meta": {"count": 1, "page": 1, "per_page": 25},
            }
        )
        inst.search_catalog = AsyncMock(
            return_value={
                "results": [{"id": "https://openalex.org/A1", "display_name": "Alice"}],
                "meta": {"count": 2, "page": 1, "per_page": 25},
            }
        )
        yield inst


def test_openalex_search_works(client, mock_openalex_client):
    resp = client.get("/openalex/search?q=attention&entity=works&sort_field=cited_by_count")
    assert resp.status_code == 200
    data = resp.json()
    assert data["entity"] == "works"
    assert len(data["results"]) == 1
    mock_openalex_client.search_works_filtered.assert_awaited_once()
    call_kw = mock_openalex_client.search_works_filtered.await_args.kwargs
    assert call_kw.get("sort") == "cited_by_count:desc"


def test_openalex_search_authors(client, mock_openalex_client):
    resp = client.get("/openalex/search?q=smith&entity=authors&sort_field=works_count&sort_dir=asc")
    assert resp.status_code == 200
    data = resp.json()
    assert data["entity"] == "authors"
    mock_openalex_client.search_catalog.assert_awaited_once()
    kw = mock_openalex_client.search_catalog.await_args.kwargs
    assert kw.get("sort") == "works_count:asc"


@pytest.fixture()
def mock_ingest():
    with patch(
        "scholargraph.services.graph_api.openalex_routes.ingest_openalex_explore",
        new_callable=AsyncMock,
    ) as fn:
        fn.return_value = {
            "seed_canonical_id": "10.1000/xyz",
            "ingested_works": 4,
            "modes": ["citations_out", "citations_in"],
        }
        yield fn


def test_openalex_explore_ok(client, mock_ingest):
    resp = client.post(
        "/openalex/explore",
        json={"seed_work_id": "W2741809807", "modes": ["citations_out"], "limit_per_mode": 10},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["seed_canonical_id"] == "10.1000/xyz"
    assert body["ingested_works"] == 4
    mock_ingest.assert_awaited_once()


def test_openalex_explore_404(client):
    async def boom(**_kwargs):
        raise ValueError("OpenAlex work not found for selector: 'W0'")

    with patch(
        "scholargraph.services.graph_api.openalex_routes.ingest_openalex_explore",
        new_callable=AsyncMock,
        side_effect=boom,
    ):
        resp = client.post("/openalex/explore", json={"seed_work_id": "W0", "modes": ["citations_out"]})
    assert resp.status_code == 404
    assert "not found" in resp.json()["detail"].lower()
