"""
tests/test_graph_api.py
Integration-light tests for the FastAPI graph_api using httpx TestClient.
Neo4j calls are mocked so no running database is needed.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Patch neo4j before importing the app
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def mock_neo4j(monkeypatch):
    """Replace neo4j.AsyncGraphDatabase.driver with a lightweight mock."""
    mock_driver = MagicMock()

    mock_session = AsyncMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)

    mock_result = AsyncMock()

    # Default behaviours – individual tests override as needed
    mock_result.single = AsyncMock(return_value=None)
    mock_result.data = AsyncMock(return_value=[])
    mock_session.run = AsyncMock(return_value=mock_result)
    mock_driver.session = MagicMock(return_value=mock_session)

    monkeypatch.setenv("NEO4J_URI", "bolt://localhost:7687")
    monkeypatch.setenv("NEO4J_USER", "neo4j")
    monkeypatch.setenv("NEO4J_PASSWORD", "test")

    with patch("neo4j.AsyncGraphDatabase.driver", return_value=mock_driver):
        yield mock_session


@pytest.fixture()
def client():
    from scholargraph.services.graph_api.main import app
    return TestClient(app)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestGetPaper:
    def test_404_when_paper_not_found(self, client, mock_neo4j):
        mock_neo4j.run.return_value.single = AsyncMock(return_value=None)
        resp = client.get("/papers/10.9999/does-not-exist")
        assert resp.status_code == 404

    def test_returns_paper_data(self, client, mock_neo4j):
        fake_record = {
            "p": {
                "doi": "10.1038/test",
                "title": "Test Paper",
                "year": 2020,
                "impact_score": 0.7,
            },
            "authors": ["Alice Smith"],
            "keywords": ["ML"],
            "funders": ["NSF"],
        }
        mock_neo4j.run.return_value.single = AsyncMock(return_value=fake_record)
        resp = client.get("/papers/10.1038/test")
        assert resp.status_code == 200
        data = resp.json()
        assert data["doi"] == "10.1038/test"
        assert data["authors"] == ["Alice Smith"]


class TestSearch:
    def test_search_returns_list(self, client, mock_neo4j):
        mock_neo4j.run.return_value.data = AsyncMock(return_value=[
            {"doi": "10.1/a", "title": "Alpha", "year": 2021, "impact_score": 0.5}
        ])
        resp = client.get("/search?q=alpha")
        assert resp.status_code == 200
        results = resp.json()
        assert isinstance(results, list)

    def test_search_requires_query(self, client):
        resp = client.get("/search")
        assert resp.status_code == 422  # FastAPI validation error

    def test_search_by_keyword(self, client, mock_neo4j):
        mock_neo4j.run.return_value.data = AsyncMock(return_value=[])
        resp = client.get("/search/by-keyword?keyword=machine+learning")
        assert resp.status_code == 200


class TestGraph:
    def test_graph_returns_nodes_edges(self, client, mock_neo4j):
        fake_record = {"nodes": [], "edges": []}
        mock_neo4j.run.return_value.single = AsyncMock(return_value=fake_record)
        resp = client.get("/graph?doi=10.1038/test")
        assert resp.status_code == 200
        data = resp.json()
        assert "nodes" in data
        assert "edges" in data

    def test_graph_requires_doi(self, client):
        resp = client.get("/graph")
        assert resp.status_code == 422

    def test_graph_empty_when_not_found(self, client, mock_neo4j):
        mock_neo4j.run.return_value.single = AsyncMock(return_value=None)
        resp = client.get("/graph?doi=10.9999/missing")
        assert resp.status_code == 200
        data = resp.json()
        assert data == {"nodes": [], "edges": []}
