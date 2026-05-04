"""
tests/test_graph_api.py
Integration-light tests for the FastAPI graph_api using httpx TestClient.
Neo4j calls are mocked in ``conftest.py`` so no running database is needed.
"""

from __future__ import annotations

from unittest.mock import AsyncMock


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
        mock_neo4j.run.return_value.data = AsyncMock(
            return_value=[{"doi": "10.1/a", "title": "Alpha", "year": 2021, "impact_score": 0.5}]
        )
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


class TestAiMounted:
    def test_ai_summary_accepts_json(self, client):
        resp = client.post(
            "/ai/summary",
            json={"title": "Example", "abstract": "First sentence. Second sentence. Third sentence here."},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "summary" in data
        assert isinstance(data["summary"], str)

    def test_ai_relationship_accepts_json(self, client):
        resp = client.post(
            "/ai/relationship",
            json={
                "abstract_a": "Neural networks learn representations from labeled data.",
                "abstract_b": "Deep learning models optimize loss on training examples.",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "relationship" in data
        assert "correlation_value" in data
