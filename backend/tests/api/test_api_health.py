"""
API Contract Tests — Service Health Probes.

Tests `/health`:
- Verifies service metadata, environment binding, and database connectivity.
- Verifies degraded response when database probe experiences failure.
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check_healthy(async_client: AsyncClient):
    """Verifies GET /health returns online status and healthy database probe."""
    response = await async_client.get("/health")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "online"
    assert data["database"] == "healthy"
    assert "app_name" in data
    assert "environment" in data
    assert "base_url" in data


@pytest.mark.asyncio
async def test_health_check_degraded_on_db_failure(async_client: AsyncClient, monkeypatch):
    """Verifies GET /health returns degraded status when database is unreachable."""
    from backend.database.session import AsyncSessionLocal

    class FailingSession:
        async def __aenter__(self):
            raise ConnectionRefusedError("Simulated PostgreSQL connection drop")

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

    monkeypatch.setattr("backend.main.AsyncSessionLocal", lambda: FailingSession())

    response = await async_client.get("/health")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "degraded"
    assert data["database"] == "unhealthy"
