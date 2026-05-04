"""Shared pytest fixtures for clearCites API tests."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def mock_neo4j(monkeypatch):
    """Replace neo4j.AsyncGraphDatabase.driver with a lightweight mock."""
    mock_driver = MagicMock()

    mock_session = AsyncMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)

    mock_result = AsyncMock()
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
