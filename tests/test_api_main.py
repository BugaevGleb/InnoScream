from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.main import app, lifespan
from app.core.config import settings


@pytest.fixture
def client():
    """Fixture for FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def mock_db():
    """Fixture for mocking database creation."""
    with patch("app.api.main.create_db_and_tables", new=AsyncMock()) as mock:
        yield mock


@pytest.mark.asyncio
async def test_lifespan(mock_db):
    """Test application lifespan events."""
    async with lifespan(FastAPI()):
        pass
    mock_db.assert_awaited_once()


def test_app_configuration():
    """Test FastAPI application configuration."""
    assert app.title == settings.PROJECT_NAME
    assert app.description == settings.PROJECT_DESCRIPTION
    assert app.version == settings.PROJECT_VERSION


def test_router_inclusion(client):
    """Test main router inclusion in application."""
    response = client.get("/openapi.json")
    assert "/user_messages" in response.json()["paths"]
